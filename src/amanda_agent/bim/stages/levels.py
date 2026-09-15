"""R03 desired levels, conceptual grids and project references.

The stage keeps metric design data in typed desired elements. Levels require
evidence for their elevation; a provisional grid is allowed as a design
concept but is explicitly marked as unverified structural work.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..desired_state import DesiredState
from ..models import BimStage, DesiredElement
from ..verification import VerificationResult, verify_write
from . import (
    PreflightReport,
    PreflightRequest,
    StageError,
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

LEVEL_CAPABILITY = "revit.create_level"
GRID_CAPABILITY = "revit.create_grid"
REFERENCE_CAPABILITY = "revit.create_reference"


class LevelReference(BaseModel):
    """A level whose elevation is bound to source evidence."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    elevation_m: float
    evidence: list[str] = Field(default_factory=list)
    is_provable: bool = True
    required: bool = True
    source_kind: Literal["VERIFIED_SOURCE", "DESIGN_ASSUMPTION"] = "VERIFIED_SOURCE"

    @model_validator(mode="before")
    @classmethod
    def accept_level_aliases(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if "logical_id" not in values and "level_id" in values:
            values["logical_id"] = values.pop("level_id")
        if "elevation_m" not in values and "elevation" in values:
            values["elevation_m"] = values.pop("elevation")
        if "evidence" not in values and "source_refs" in values:
            values["evidence"] = values.pop("source_refs")
        if "is_provable" not in values and "verified" in values:
            values["is_provable"] = values.pop("verified")
        return values


class GridAxis(BaseModel):
    """A project grid axis; structural certification is a separate concern."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    start: tuple[float, float]
    end: tuple[float, float]
    assumption: Literal["PROVISIONAL_ASSUMPTION"] | None = None
    engineering_verified: bool = False

    @model_validator(mode="before")
    @classmethod
    def accept_axis_aliases(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if "logical_id" not in values and "axis_id" in values:
            values["logical_id"] = values.pop("axis_id")
        return values


class ReferenceMarker(BaseModel):
    """A named project reference such as the origin or a survey datum."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    coordinate: tuple[float, float, float]
    evidence: list[str] = Field(default_factory=list)
    is_provisional: bool = False


class LevelsStagePlan(BaseModel):
    """The read-only R03 desired state and selected provider operations."""

    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R03
    preflight: PreflightReport
    levels: list[LevelReference] = Field(default_factory=list)
    grids: list[GridAxis] = Field(default_factory=list)
    references: list[ReferenceMarker] = Field(default_factory=list)
    desired_state: DesiredState
    operations: list[StageOperation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    checkpoint_label: str = Field(default="R03_LEVELS_AND_REFERENCES", min_length=1)


def _desired_level(level: LevelReference, generation_run: str) -> DesiredElement:
    return DesiredElement(
        logical_id=level.logical_id,
        category="Levels",
        geometry={"elevation_m": level.elevation_m},
        properties={
            "name": level.name,
            "source_kind": level.source_kind,
            "evidence": list(level.evidence),
        },
        requirement_id="P05-T11:LEVEL",
        design_option="SELECTED_SOLUTION",
        generation_run=generation_run,
    )


def _desired_grid(grid: GridAxis, generation_run: str) -> DesiredElement:
    return DesiredElement(
        logical_id=grid.logical_id,
        category="Grids",
        geometry={"start": list(grid.start), "end": list(grid.end)},
        properties={
            "name": grid.name,
            "assumption": grid.assumption,
            "engineering_verified": grid.engineering_verified,
        },
        requirement_id="P05-T11:GRID",
        design_option="PROVISIONAL_GRID_CONCEPT"
        if grid.assumption == "PROVISIONAL_ASSUMPTION"
        else "SELECTED_SOLUTION",
        generation_run=generation_run,
    )


def _desired_reference(reference: ReferenceMarker, generation_run: str) -> DesiredElement:
    return DesiredElement(
        logical_id=reference.logical_id,
        category="References",
        geometry={"coordinate": list(reference.coordinate)},
        properties={
            "name": reference.name,
            "kind": reference.kind,
            "evidence": list(reference.evidence),
            "is_provisional": reference.is_provisional,
        },
        requirement_id="P05-T11:REFERENCE",
        design_option="PROVISIONAL_REFERENCE"
        if reference.is_provisional
        else "SELECTED_SOLUTION",
        generation_run=generation_run,
    )


def _operation(
    *,
    element: DesiredElement,
    capability: str,
    preferred: str,
    fallbacks: Sequence[str],
) -> StageOperation:
    return StageOperation(
        stage=BimStage.R03,
        logical_id=element.logical_id,
        semantic_capability=capability,
        payload={
            "logical_id": element.logical_id,
            "category": element.category,
            "geometry": element.geometry,
            "properties": element.properties,
            "name": element.properties["name"],
            **(
                {"elevation_m": element.geometry["elevation_m"]}
                if element.category == "Levels"
                else {}
            ),
            "requirement_id": element.requirement_id,
            "design_option": element.design_option,
            "generation_run": element.generation_run,
        },
        verification_rules=[
            "independent_requery",
            "unique_id_present",
            "name_matches",
            "elevation_matches"
            if element.category == "Levels"
            else "geometry_matches",
        ],
        preferred_provider=preferred,
        fallback_providers=list(fallbacks),
    )


def _select(
    request: PreflightRequest,
    capability: str,
) -> tuple[str, list[str]]:
    preferred, rest = select_capability(
        request.registry,
        capability,
        revit_build=request.revit_build,
        tool_schema_hash=request.tool_schema_hash,
        scope=request.evidence_scope,
    )
    return preferred.provider, [entry.provider for entry in rest]


def plan_levels_stage(
    request: PreflightRequest,
    *,
    levels: Sequence[LevelReference | Mapping[str, Any]] = (),
    grids: Sequence[GridAxis | Mapping[str, Any]] = (),
    references: Sequence[ReferenceMarker | Mapping[str, Any]] = (),
) -> LevelsStagePlan:
    """Plan only evidenced required levels plus explicitly supplied references."""

    if request.stage is not BimStage.R03:
        raise StageError(f"R03 levels stage requires stage R03, got {request.stage.name}")
    selected_levels = [
        item if isinstance(item, LevelReference) else LevelReference.model_validate(item)
        for item in levels
    ]
    selected_levels = [item for item in selected_levels if item.required]
    selected_grids = [
        item if isinstance(item, GridAxis) else GridAxis.model_validate(item)
        for item in grids
    ]
    selected_references = [
        item
        if isinstance(item, ReferenceMarker)
        else ReferenceMarker.model_validate(item)
        for item in references
    ]
    missing_evidence = [
        item.logical_id
        for item in selected_levels
        if not item.evidence
        or not item.is_provable
        or item.source_kind != "VERIFIED_SOURCE"
    ]
    required_operations = tuple(
        capability
        for capability, items in (
            (LEVEL_CAPABILITY, selected_levels),
            (GRID_CAPABILITY, selected_grids),
            (REFERENCE_CAPABILITY, selected_references),
        )
        if items
    )
    effective = with_stage_requirements(request, extra=required_operations)
    report = run_preflight(effective)
    if missing_evidence:
        raise StagePreflightError(
            "R03 preflight refused: level_evidence: "
            + ", ".join(sorted(missing_evidence))
            + " lacks provable source elevation"
        )
    if not report.ok:
        raise StagePreflightError("R03 preflight refused: " + "; ".join(report.problems))

    desired_elements: list[DesiredElement] = []
    operations: list[StageOperation] = []
    for level in sorted(selected_levels, key=lambda item: item.logical_id):
        element = _desired_level(level, request.generation_run)
        preferred, fallbacks = _select(request, LEVEL_CAPABILITY)
        desired_elements.append(element)
        operations.append(
            _operation(
                element=element,
                capability=LEVEL_CAPABILITY,
                preferred=preferred,
                fallbacks=fallbacks,
            )
        )
    for grid in sorted(selected_grids, key=lambda item: item.logical_id):
        element = _desired_grid(grid, request.generation_run)
        preferred, fallbacks = _select(request, GRID_CAPABILITY)
        desired_elements.append(element)
        operations.append(
            _operation(
                element=element,
                capability=GRID_CAPABILITY,
                preferred=preferred,
                fallbacks=fallbacks,
            )
        )
    for reference in sorted(selected_references, key=lambda item: item.logical_id):
        element = _desired_reference(reference, request.generation_run)
        preferred, fallbacks = _select(request, REFERENCE_CAPABILITY)
        desired_elements.append(element)
        operations.append(
            _operation(
                element=element,
                capability=REFERENCE_CAPABILITY,
                preferred=preferred,
                fallbacks=fallbacks,
            )
        )
    return LevelsStagePlan(
        preflight=report,
        levels=selected_levels,
        grids=selected_grids,
        references=selected_references,
        desired_state=DesiredState(
            elements=desired_elements,
            stage=BimStage.R03,
            generation_run=request.generation_run,
        ),
        operations=operations,
        notes=[
            "structural grid assumptions remain provisional and require independent engineering verification"
            if any(grid.assumption for grid in selected_grids)
            else "no provisional structural grid assumption was supplied"
        ],
        checkpoint_label=stage_checkpoint_label(BimStage.R03),
    )


def execute_levels_stage(
    plan: LevelsStagePlan,
    *,
    invoker: StageToolInvoker,
) -> list[StageExecutionRecord]:
    """Dispatch R03 desired operations through the injected provider."""

    return dispatch_operations(plan.operations, invoker=invoker)


def verify_levels_stage(
    plan: LevelsStagePlan,
    *,
    tool_reported_success: bool | Mapping[str, bool],
    query_results: Mapping[str, Mapping[str, Any] | None],
    geometry_tolerance: float = 1e-6,
) -> list[VerificationResult]:
    """Verify names and metric geometry after an independent model re-query."""

    results: list[VerificationResult] = []
    for operation in plan.operations:
        success = (
            tool_reported_success.get(operation.logical_id, False)
            if isinstance(tool_reported_success, Mapping)
            else tool_reported_success
        )
        query = query_results.get(operation.logical_id)
        results.extend(
            verify_write(
                logical_id=operation.logical_id,
                tool_reported_success=success,
                query_result=query,
                expected_geometry=operation.payload["geometry"],
                expected_properties={"name": operation.payload["properties"]["name"]},
                geometry_tolerance=geometry_tolerance,
            )
        )
    return results


LevelSpec = LevelReference
DesiredLevel = LevelReference
ReferenceSpec = ReferenceMarker


__all__ = [
    "GRID_CAPABILITY",
    "LEVEL_CAPABILITY",
    "REFERENCE_CAPABILITY",
    "DesiredLevel",
    "GridAxis",
    "LevelReference",
    "LevelSpec",
    "LevelsStagePlan",
    "ReferenceMarker",
    "ReferenceSpec",
    "execute_levels_stage",
    "plan_levels_stage",
    "verify_levels_stage",
]
