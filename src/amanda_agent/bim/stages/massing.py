"""R04 conceptual massing derived from the design engine's metric blocks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import Polygon, shape

from amanda_agent.design.geometry import centroid as polygon_centroid
from amanda_agent.design.geometry import contains, overlap_area_m2, validate_polygon

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

MASSING_CAPABILITY = "revit.create_mass"


def _coordinates(value: Any) -> list[tuple[float, float]]:
    if isinstance(value, Polygon):
        return [(float(x), float(y)) for x, y in value.exterior.coords]
    if isinstance(value, Mapping):
        return _coordinates(shape(value))
    if hasattr(value, "exterior"):
        return _coordinates(value.exterior)
    if hasattr(value, "coords"):
        return [(float(point[0]), float(point[1])) for point in value.coords]
    return [(float(point[0]), float(point[1])) for point in value]


class MassingBlock(BaseModel):
    """One design-engine block expressed in metres."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    name: str = Field(default="Mass", min_length=1)
    sector_id: str | None = Field(default=None, min_length=1)
    footprint: list[tuple[float, float]] = Field(min_length=4)
    base_elevation_m: float = 0.0
    height_m: float = Field(gt=0)
    rotation_degrees: float = 0.0
    source_area_m2: float | None = Field(default=None, gt=0)
    demand_m2: float | None = Field(default=None, gt=0)
    source_solution_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="before")
    @classmethod
    def accept_design_engine_block_shape(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if "footprint" not in values and "geometry" in values:
            values["footprint"] = _coordinates(values.pop("geometry"))
        if "height_m" not in values:
            for key in ("height", "height_meters"):
                if key in values:
                    values["height_m"] = values.pop(key)
                    break
        if "source_area_m2" not in values and "area_m2" in values:
            values["source_area_m2"] = values.pop("area_m2")
        return values

    @model_validator(mode="after")
    def validate_metric_geometry(self) -> MassingBlock:
        if not isfinite(self.base_elevation_m) or not isfinite(self.height_m):
            raise ValueError("massing elevations and height must be finite")
        if not isfinite(self.rotation_degrees):
            raise ValueError("massing rotation must be finite")
        validate_polygon(self.footprint)
        return self

    @property
    def area_projection_m2(self) -> float:
        return float(validate_polygon(self.footprint).area)

    @property
    def top_elevation_m(self) -> float:
        return self.base_elevation_m + self.height_m


class MassingStagePlan(BaseModel):
    """Read-only R04 plan with the metric desired state."""

    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R04
    preflight: PreflightReport
    blocks: list[MassingBlock] = Field(default_factory=list)
    desired_state: DesiredState
    operations: list[StageOperation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    checkpoint_label: str = Field(default="R04_MASSING", min_length=1)


def _desired_element(block: MassingBlock, generation_run: str) -> DesiredElement:
    return DesiredElement(
        logical_id=block.logical_id,
        category="Massing",
        geometry={
            "footprint": [list(point) for point in block.footprint],
            "centroid": list(polygon_centroid(block.footprint)),
            "dimensions_m": [
                max(point[0] for point in block.footprint)
                - min(point[0] for point in block.footprint),
                max(point[1] for point in block.footprint)
                - min(point[1] for point in block.footprint),
            ],
            "base_elevation_m": block.base_elevation_m,
            "height_m": block.height_m,
            "top_elevation_m": block.top_elevation_m,
            "rotation_degrees": block.rotation_degrees,
        },
        properties={
            "name": block.name,
            "area_projection_m2": block.area_projection_m2,
            "source_area_m2": block.source_area_m2,
            "source_solution_id": block.source_solution_id,
        },
        requirement_id="P05-T12:MASSING",
        design_option="SELECTED_SOLUTION",
        generation_run=generation_run,
    )


def _operation(block: MassingBlock, generation_run: str, provider: str, fallbacks: Sequence[str]) -> StageOperation:
    element = _desired_element(block, generation_run)
    return StageOperation(
        stage=BimStage.R04,
        logical_id=block.logical_id,
        semantic_capability=MASSING_CAPABILITY,
        payload={
            "logical_id": element.logical_id,
            "category": element.category,
            "geometry": element.geometry,
            "properties": element.properties,
            "footprint": element.geometry["footprint"],
            "base_elevation_m": block.base_elevation_m,
            "height_m": block.height_m,
            "area_m2": block.area_projection_m2,
            "rotation_degrees": block.rotation_degrees,
            "requirement_id": element.requirement_id,
            "design_option": element.design_option,
            "generation_run": element.generation_run,
        },
        verification_rules=[
            "independent_requery",
            "unique_id_present",
            "footprint_matches",
            "height_matches",
            "projection_area_matches",
        ],
        preferred_provider=provider,
        fallback_providers=list(fallbacks),
    )


def plan_massing_stage(
    request: PreflightRequest,
    *,
    blocks: Sequence[MassingBlock | Mapping[str, Any]] = (),
    site_boundary: Any | None = None,
    area_tolerance_m2: float = 1e-6,
) -> MassingStagePlan:
    """Convert design-engine blocks into guarded R04 surrogate operations."""

    if request.stage is not BimStage.R04:
        raise StageError(f"R04 massing stage requires stage R04, got {request.stage.name}")
    if area_tolerance_m2 < 0 or not isfinite(area_tolerance_m2):
        raise ValueError("area_tolerance_m2 must be finite and non-negative")
    selected = [
        item if isinstance(item, MassingBlock) else MassingBlock.model_validate(item)
        for item in blocks
    ]
    if not selected:
        solution_geometry = getattr(request.solution, "geometry", None)
        if isinstance(solution_geometry, Mapping):
            selected = [MassingBlock.model_validate(item) for item in solution_geometry.get("blocks", [])]
    if not selected:
        raise StagePreflightError("R04 preflight refused: massing_blocks: no design-engine blocks supplied")

    solution_id = getattr(request.solution, "solution_id", None)
    if solution_id:
        selected = [
            block
            if block.source_solution_id is not None
            else block.model_copy(update={"source_solution_id": solution_id})
            for block in selected
        ]

    if site_boundary is not None:
        site_boundary = getattr(site_boundary, "boundary", site_boundary)
        for block in selected:
            if not contains(site_boundary, block.footprint, tolerance_m=0.0):
                raise StagePreflightError(
                    f"R04 preflight refused: site_containment: {block.logical_id} is outside the site"
                )
    area_problems = [
        block.logical_id
        for block in selected
        if block.source_area_m2 is not None
        and abs(block.area_projection_m2 - block.source_area_m2) > area_tolerance_m2
    ]
    if area_problems:
        raise StagePreflightError(
            "R04 preflight refused: projection_area: " + ", ".join(sorted(area_problems))
        )

    for index, first in enumerate(selected):
        for second in selected[index + 1 :]:
            if overlap_area_m2(first.footprint, second.footprint) > 1e-6:
                raise StagePreflightError(
                    "R04 preflight refused: separation: "
                    f"{first.logical_id} overlaps {second.logical_id}"
                )

    effective = with_stage_requirements(request, extra=(MASSING_CAPABILITY,))
    report = run_preflight(effective)
    if not report.ok:
        raise StagePreflightError("R04 preflight refused: " + "; ".join(report.problems))
    try:
        preferred, rest = select_capability(
            effective.registry,
            MASSING_CAPABILITY,
            revit_build=effective.revit_build,
            tool_schema_hash=effective.tool_schema_hash,
            scope=effective.evidence_scope,
        )
    except Exception as exc:
        raise StagePreflightError(f"R04 preflight refused: {MASSING_CAPABILITY}: {exc}") from exc

    ordered = sorted(selected, key=lambda item: item.logical_id)
    elements = [_desired_element(block, request.generation_run) for block in ordered]
    operations = [
        _operation(
            block,
            request.generation_run,
            preferred.provider,
            [entry.provider for entry in rest],
        )
        for block in ordered
    ]
    return MassingStagePlan(
        preflight=report,
        blocks=ordered,
        desired_state=DesiredState(
            elements=elements,
            stage=BimStage.R04,
            generation_run=request.generation_run,
        ),
        operations=operations,
        notes=[
            "R04 is a simplified metric surrogate; detailed shell and structural verification remain later stages"
        ],
        checkpoint_label=stage_checkpoint_label(BimStage.R04),
    )


def execute_massing_stage(
    plan: MassingStagePlan,
    *,
    invoker: StageToolInvoker,
) -> list[StageExecutionRecord]:
    """Dispatch R04 operations through the injected provider."""

    return dispatch_operations(plan.operations, invoker=invoker)


def verify_massing_stage(
    plan: MassingStagePlan,
    *,
    tool_reported_success: bool | Mapping[str, bool],
    query_results: Mapping[str, Mapping[str, Any] | None],
    geometry_tolerance: float = 1e-6,
) -> list[VerificationResult]:
    """Verify the independent re-query against the metric massing payload."""

    results: list[VerificationResult] = []
    for operation in plan.operations:
        success = (
            tool_reported_success.get(operation.logical_id, False)
            if isinstance(tool_reported_success, Mapping)
            else tool_reported_success
        )
        results.extend(
            verify_write(
                logical_id=operation.logical_id,
                tool_reported_success=success,
                query_result=query_results.get(operation.logical_id),
                expected_geometry=operation.payload["geometry"],
                expected_properties={
                    "name": operation.payload["properties"]["name"],
                    "area_projection_m2": operation.payload["properties"][
                        "area_projection_m2"
                    ],
                },
                geometry_tolerance=geometry_tolerance,
            )
        )
    return results


MassingSpec = MassingBlock


__all__ = [
    "MASSING_CAPABILITY",
    "MassingBlock",
    "MassingSpec",
    "MassingStagePlan",
    "execute_massing_stage",
    "plan_massing_stage",
    "verify_massing_stage",
]
