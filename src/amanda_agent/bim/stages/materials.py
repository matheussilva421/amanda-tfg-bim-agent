"""R12 controlled material desired-state planning (P05-T20)."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..models import BimStage, DesiredElement, DesiredState
from ..provenance import BimProvenance
from ..verification import VerificationResult, verify_write
from . import (
    PreflightReport,
    PreflightRequest,
    StageExecutionRecord,
    StageOperation,
    StagePreflightError,
    StageToolInvoker,
    dispatch_operations,
    run_preflight,
    select_capability,
    stage_checkpoint_label,
    with_stage_requirements,
)

MATERIAL_CAPABILITY = "revit.assign_material"
MATERIAL_DESIGN_OPTION = "DELEGATED_DESIGN"


class MaterialCatalogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    material_name: str = Field(min_length=1)
    material_type: str = Field(min_length=1)
    source_ref: str | None = None
    justification: str | None = None


class MaterialAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    element_logical_id: str = Field(min_length=1)
    material_name: str = Field(min_length=1)
    material_type: str = Field(min_length=1)
    requirement_id: str = Field(min_length=1)
    design_intent: str = Field(min_length=1)
    source_ref: str | None = None
    justification: str | None = None


class MaterialsStagePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R12
    preflight: PreflightReport
    desired_state: DesiredState
    assignments: list[MaterialAssignment] = Field(default_factory=list)
    operations: list[StageOperation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    checkpoint_label: str = "R12_MATERIALS"

    @property
    def desired_elements(self) -> list[DesiredElement]:
        return self.desired_state.elements


def _as_assignment(value: MaterialAssignment | Mapping[str, Any]) -> MaterialAssignment:
    return (
        value
        if isinstance(value, MaterialAssignment)
        else MaterialAssignment.model_validate(value)
    )


def _as_catalog(
    value: MaterialCatalogEntry | Mapping[str, Any],
) -> MaterialCatalogEntry:
    return (
        value
        if isinstance(value, MaterialCatalogEntry)
        else MaterialCatalogEntry.model_validate(value)
    )


def _as_desired(value: DesiredElement | Mapping[str, Any]) -> DesiredElement:
    return (
        value
        if isinstance(value, DesiredElement)
        else DesiredElement.model_validate(value)
    )


def _external_elements(
    external_elements: Sequence[DesiredElement | Mapping[str, Any]],
    external_planner: Callable[[], Sequence[DesiredElement | Mapping[str, Any]]] | None,
) -> list[DesiredElement]:
    values = list(external_elements)
    if external_planner is not None:
        values.extend(external_planner())
    return [_as_desired(value) for value in values]


def plan_materials_stage(
    request: PreflightRequest,
    *,
    assignments: Sequence[MaterialAssignment | Mapping[str, Any]],
    catalog: Sequence[MaterialCatalogEntry | Mapping[str, Any]]
    | Mapping[str, MaterialCatalogEntry | Mapping[str, Any]],
    external_elements: Sequence[DesiredElement | Mapping[str, Any]] = (),
    external_planner: Callable[[], Sequence[DesiredElement | Mapping[str, Any]]]
    | None = None,
) -> MaterialsStagePlan:
    """Assign only materials whose source and justification are registered."""

    if isinstance(catalog, Mapping):
        entries = [
            _as_catalog(
                {
                    "material_name": name,
                    **(
                        entry.model_dump()
                        if isinstance(entry, MaterialCatalogEntry)
                        else entry
                    ),
                }
            )
            for name, entry in catalog.items()
        ]
    else:
        entries = [_as_catalog(entry) for entry in catalog]
    names: set[str] = set()
    types: set[tuple[str, str]] = set()
    by_name: dict[str, MaterialCatalogEntry] = {}
    for entry in entries:
        if (
            entry.material_name in names
            or (entry.material_name, entry.material_type) in types
        ):
            raise ValueError(
                f"duplicate material name/type in controlled catalog: {entry.material_name}/{entry.material_type}"
            )
        names.add(entry.material_name)
        types.add((entry.material_name, entry.material_type))
        by_name[entry.material_name] = entry
    normalized = [_as_assignment(assignment) for assignment in assignments]
    ids: set[str] = set()
    for assignment in normalized:
        if assignment.element_logical_id in ids:
            raise ValueError(
                f"duplicate material assignment element: {assignment.element_logical_id}"
            )
        ids.add(assignment.element_logical_id)
        catalog_entry = by_name.get(assignment.material_name)
        if catalog_entry is None:
            raise ValueError(
                f"material provenance is not registered for {assignment.material_name}"
            )
        if catalog_entry.material_type != assignment.material_type:
            raise ValueError(
                f"material type does not match controlled catalog for {assignment.material_name}"
            )
        if not (assignment.source_ref or catalog_entry.source_ref) or not (
            assignment.justification or catalog_entry.justification
        ):
            raise ValueError(
                f"material provenance requires source_ref and justification for {assignment.material_name}"
            )
    effective = with_stage_requirements(request, extra=(MATERIAL_CAPABILITY,))
    report = run_preflight(effective)
    if not report.ok:
        raise StagePreflightError(
            "R12 preflight refused: " + "; ".join(report.problems)
        )
    owned: list[DesiredElement] = []
    for assignment in normalized:
        catalog_entry = by_name[assignment.material_name]
        source_ref = assignment.source_ref or catalog_entry.source_ref
        justification = assignment.justification or catalog_entry.justification
        owned.append(
            DesiredElement(
                logical_id=assignment.element_logical_id,
                category="material_assignment",
                geometry={"host_element": assignment.element_logical_id},
                properties={
                    "material_name": assignment.material_name,
                    "material_type": assignment.material_type,
                    "source_ref": source_ref,
                    "justification": justification,
                    "design_intent": assignment.design_intent,
                },
                requirement_id=assignment.requirement_id,
                design_option=MATERIAL_DESIGN_OPTION,
                generation_run=effective.generation_run,
                provenance=BimProvenance(
                    requirement_id=assignment.requirement_id,
                    design_option=MATERIAL_DESIGN_OPTION,
                    generation_run=effective.generation_run,
                    source_refs=[source_ref] if source_ref else [],
                    notes={
                        "justification": justification,
                        "material_type": assignment.material_type,
                    },
                ),
            )
        )
    desired_state = DesiredState(
        stage=BimStage.R12,
        generation_run=effective.generation_run,
        elements=[*owned, *_external_elements(external_elements, external_planner)],
    )
    preferred, fallbacks = select_capability(
        effective.registry,
        MATERIAL_CAPABILITY,
        revit_build=effective.revit_build,
        tool_schema_hash=effective.tool_schema_hash,
        scope=effective.evidence_scope,
    )
    operations = [
        StageOperation(
            stage=BimStage.R12,
            logical_id=element.logical_id,
            semantic_capability=MATERIAL_CAPABILITY,
            payload=element.model_dump(mode="json"),
            verification_rules=[
                "independent_requery",
                "material_provenance_preserved",
                "design_intent_preserved",
            ],
            preferred_provider=preferred.provider,
            fallback_providers=[entry.provider for entry in fallbacks],
        )
        for element in owned
    ]
    return MaterialsStagePlan(
        preflight=report,
        desired_state=desired_state,
        assignments=normalized,
        operations=operations,
        notes=[
            "material names and types are controlled per run; assignments remain traceable to design intent"
        ],
        checkpoint_label=stage_checkpoint_label(BimStage.R12),
    )


def execute_materials_stage(
    plan: MaterialsStagePlan, *, invoker: StageToolInvoker
) -> list[StageExecutionRecord]:
    return dispatch_operations(plan.operations, invoker=invoker)


def verify_materials_stage(
    plan: MaterialsStagePlan,
    *,
    query_result: Mapping[str, Mapping[str, Any]],
    tool_reported_success: bool = True,
) -> list[VerificationResult]:
    results: list[VerificationResult] = []
    owned_ids = {operation.logical_id for operation in plan.operations}
    for element in plan.desired_state.elements:
        if element.logical_id not in owned_ids:
            continue
        results.extend(
            verify_write(
                logical_id=element.logical_id,
                tool_reported_success=tool_reported_success,
                query_result=query_result.get(element.logical_id),
                expected_geometry=element.geometry,
                expected_properties=element.properties,
            )
        )
    return results


__all__ = [
    "MATERIAL_CAPABILITY",
    "MaterialAssignment",
    "MaterialCatalogEntry",
    "MaterialsStagePlan",
    "execute_materials_stage",
    "plan_materials_stage",
    "verify_materials_stage",
]
