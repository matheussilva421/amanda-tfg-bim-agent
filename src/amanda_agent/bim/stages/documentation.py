"""R13 deterministic documentation desired-state planning (P05-T21)."""

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

DOCUMENTATION_CAPABILITY = "revit.create_documentation_element"
DOCUMENTATION_DESIGN_OPTION = "DELEGATED_DESIGN"
MINIMUM_TABLES: tuple[str, ...] = (
    "ROOM_SCHEDULE",
    "DOOR_SCHEDULE",
    "WINDOW_SCHEDULE",
    "AREA_SUMMARY",
)
DEFAULT_VIEW_NAMES: tuple[str, ...] = (
    "PLAN_SITE",
    "PLAN_GROUND",
    "PLAN_ROOF",
    "SECTION_COURTYARD",
    "SECTION_RESIDENTIAL",
    "SECTION_TRANSITIONS",
    "SECTION_ACCESS",
    "ELEVATION_NORTH",
    "ELEVATION_SOUTH",
    "ELEVATION_EAST",
    "ELEVATION_WEST",
)
DEFAULT_SHEET_REGISTRY: dict[str, list[str]] = {
    "SHEET-ARQ-01": ["PLAN_SITE", "PLAN_GROUND"],
    "SHEET-ARQ-02": ["PLAN_ROOF", "SECTION_COURTYARD"],
    "SHEET-ARQ-03": ["SECTION_RESIDENTIAL", "SECTION_TRANSITIONS", "SECTION_ACCESS"],
    "SHEET-ARQ-04": [
        "ELEVATION_NORTH",
        "ELEVATION_SOUTH",
        "ELEVATION_EAST",
        "ELEVATION_WEST",
    ],
    "SHEET-ARQ-05": list(MINIMUM_TABLES),
}


class DocumentationStagePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R13
    preflight: PreflightReport
    view_names: tuple[str, ...]
    table_names: tuple[str, ...]
    sheet_registry: dict[str, list[str]]
    desired_state: DesiredState
    operations: list[StageOperation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    checkpoint_label: str = "R13_DOCUMENTATION"

    @property
    def desired_elements(self) -> list[DesiredElement]:
        return self.desired_state.elements


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


def _element(
    *,
    logical_id: str,
    category: str,
    kind: str,
    properties: Mapping[str, Any],
    requirement_id: str,
    generation_run: str,
) -> DesiredElement:
    return DesiredElement(
        logical_id=logical_id,
        category=category,
        geometry={"documentation_kind": kind},
        properties={"documentation_kind": kind, **dict(properties)},
        requirement_id=requirement_id,
        design_option=DOCUMENTATION_DESIGN_OPTION,
        generation_run=generation_run,
        provenance=BimProvenance(
            requirement_id=requirement_id,
            design_option=DOCUMENTATION_DESIGN_OPTION,
            generation_run=generation_run,
            notes={"documentation_kind": kind},
        ),
    )


def plan_documentation_stage(
    request: PreflightRequest,
    *,
    view_names: Sequence[str] = DEFAULT_VIEW_NAMES,
    table_names: Sequence[str] = MINIMUM_TABLES,
    sheet_registry: Mapping[str, Sequence[str]] = DEFAULT_SHEET_REGISTRY,
    external_elements: Sequence[DesiredElement | Mapping[str, Any]] = (),
    external_planner: Callable[[], Sequence[DesiredElement | Mapping[str, Any]]]
    | None = None,
) -> DocumentationStagePlan:
    """Generate repeatable views, tables, sheets, placements and annotations."""

    views = tuple(view_names)
    tables = tuple(table_names)
    sheets = {str(sheet): list(placed) for sheet, placed in sheet_registry.items()}
    if not set(MINIMUM_TABLES).issubset(tables):
        missing = sorted(set(MINIMUM_TABLES) - set(tables))
        raise ValueError(
            f"documentation package is missing minimum tables: {', '.join(missing)}"
        )
    if not {"PLAN_SITE", "PLAN_ROOF"}.issubset(views):
        raise ValueError(
            "documentation package requires deterministic site and roof plans"
        )
    if not {
        "SECTION_COURTYARD",
        "SECTION_RESIDENTIAL",
        "SECTION_TRANSITIONS",
        "SECTION_ACCESS",
    }.issubset(views):
        raise ValueError(
            "documentation package requires the four architectural relationship sections"
        )
    sheet_ids = set(sheets)
    if not sheet_ids or any(not placements for placements in sheets.values()):
        raise ValueError("documentation sheet registry requires non-empty sheets")
    for placed in sheets.values():
        unknown = set(placed) - set(views) - set(tables)
        if unknown:
            raise ValueError(
                f"documentation registry references unknown views or tables: {sorted(unknown)}"
            )
    effective = with_stage_requirements(request, extra=(DOCUMENTATION_CAPABILITY,))
    report = run_preflight(effective)
    if not report.ok:
        raise StagePreflightError(
            "R13 preflight refused: " + "; ".join(report.problems)
        )
    owned: list[DesiredElement] = []
    for name in views:
        kind = (
            "section"
            if name.startswith("SECTION_")
            else "elevation"
            if name.startswith("ELEVATION_")
            else "plan"
        )
        owned.append(
            _element(
                logical_id=f"DOC-VIEW-{name}",
                category="view",
                kind=kind,
                properties={
                    "view_name": name,
                    "purpose": "architectural_relationship"
                    if kind == "section"
                    else "deterministic_documentation",
                },
                requirement_id="R13-VIEW",
                generation_run=effective.generation_run,
            )
        )
    for name in tables:
        owned.append(
            _element(
                logical_id=f"DOC-TABLE-{name}",
                category="table",
                kind="schedule",
                properties={
                    "table_name": name,
                    "minimum_package_table": name in MINIMUM_TABLES,
                },
                requirement_id="R13-TABLE",
                generation_run=effective.generation_run,
            )
        )
    for sheet_id, placed in sheets.items():
        owned.append(
            _element(
                logical_id=f"DOC-SHEET-{sheet_id}",
                category="sheet",
                kind="sheet",
                properties={"sheet_id": sheet_id, "placements": list(placed)},
                requirement_id="R13-SHEET",
                generation_run=effective.generation_run,
            )
        )
        for index, placed_id in enumerate(placed, start=1):
            category = "viewport" if placed_id in views else "table_viewport"
            owned.append(
                _element(
                    logical_id=f"DOC-VP-{sheet_id}-{index:02d}",
                    category="viewport",
                    kind=category,
                    properties={
                        "sheet_id": sheet_id,
                        "view_or_table_id": placed_id,
                        "placement_order": index,
                    },
                    requirement_id="R13-VIEWPORT",
                    generation_run=effective.generation_run,
                )
            )
    for index, name in enumerate(views, start=1):
        owned.append(
            _element(
                logical_id=f"DOC-DIM-{index:02d}",
                category="dimension",
                kind="dimension_plan",
                properties={
                    "view_name": name,
                    "dimension_plan": "primary_axes_and_clearances",
                },
                requirement_id="R13-DIMENSION",
                generation_run=effective.generation_run,
            )
        )
        owned.append(
            _element(
                logical_id=f"DOC-TAG-{index:02d}",
                category="tag",
                kind="tag_plan",
                properties={"view_name": name, "tag_plan": "rooms_doors_windows"},
                requirement_id="R13-TAG",
                generation_run=effective.generation_run,
            )
        )
    desired_state = DesiredState(
        stage=BimStage.R13,
        generation_run=effective.generation_run,
        elements=[*owned, *_external_elements(external_elements, external_planner)],
    )
    preferred, fallbacks = select_capability(
        effective.registry,
        DOCUMENTATION_CAPABILITY,
        revit_build=effective.revit_build,
        tool_schema_hash=effective.tool_schema_hash,
        scope=effective.evidence_scope,
    )
    operations = [
        StageOperation(
            stage=BimStage.R13,
            logical_id=element.logical_id,
            semantic_capability=DOCUMENTATION_CAPABILITY,
            payload=element.model_dump(mode="json"),
            verification_rules=[
                "independent_requery",
                "registry_relationships_preserved",
                "deterministic_name_preserved",
            ],
            preferred_provider=preferred.provider,
            fallback_providers=[entry.provider for entry in fallbacks],
        )
        for element in owned
    ]
    return DocumentationStagePlan(
        preflight=report,
        view_names=views,
        table_names=tables,
        sheet_registry=sheets,
        desired_state=desired_state,
        operations=operations,
        notes=[
            "documentation registry includes plans, meaningful relationship sections, elevations, minimum schedules, sheets, viewports, dimensions and tags"
        ],
        checkpoint_label=stage_checkpoint_label(BimStage.R13),
    )


def execute_documentation_stage(
    plan: DocumentationStagePlan, *, invoker: StageToolInvoker
) -> list[StageExecutionRecord]:
    return dispatch_operations(plan.operations, invoker=invoker)


def verify_documentation_stage(
    plan: DocumentationStagePlan,
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
    "DEFAULT_SHEET_REGISTRY",
    "DEFAULT_VIEW_NAMES",
    "DOCUMENTATION_CAPABILITY",
    "MINIMUM_TABLES",
    "DocumentationStagePlan",
    "execute_documentation_stage",
    "plan_documentation_stage",
    "verify_documentation_stage",
]
