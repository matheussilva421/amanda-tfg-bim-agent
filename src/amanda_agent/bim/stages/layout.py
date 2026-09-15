"""Pure desired-state planning for the R06 internal layout."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from itertools import pairwise
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import Polygon  # type: ignore[import-untyped]

from amanda_agent.design.adjacency import AdjacencyResult, evaluate_adjacency
from amanda_agent.design.flows import FlowAnalysis, analyze_route, build_flow_graph
from amanda_agent.design.geometry import InvalidDesignGeometryError, validate_polygon
from amanda_agent.requirements.relations import FlowNetwork, RelationType

from ..models import BimStage, DesiredElement, DesiredState
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
    provider_chain,
    run_preflight,
    stage_checkpoint_label,
    with_stage_requirements,
)

LAYOUT_CAPABILITY = "revit.create_internal_wall"


class LayoutStagePlan(BaseModel):
    """R06 boundaries plus independent adjacency, flow and area evidence."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    stage: BimStage = BimStage.R06
    preflight: PreflightReport
    desired_state: DesiredState
    operations: list[StageOperation] = Field(default_factory=list)
    adjacency_results: list[AdjacencyResult] = Field(default_factory=list)
    flow_results: dict[FlowNetwork, FlowAnalysis] = Field(default_factory=dict)
    area_results: dict[str, dict[str, Any]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    checkpoint_label: str = Field(default="R06_INTERNAL_LAYOUT", min_length=1)

    @property
    def desired_elements(self) -> list[DesiredElement]:
        return self.desired_state.elements


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def _identifier(item: Any, default: str = "") -> str:
    return str(_value(item, "logical_id", _value(item, "id", default)))


def _polygon(item: Any) -> Polygon:
    geometry = _value(item, "geometry", _value(item, "polygon", item))
    try:
        return validate_polygon(geometry)
    except (InvalidDesignGeometryError, ValueError, TypeError) as exc:
        raise StageError(f"invalid layout geometry: {exc}") from exc


def _point_key(point: tuple[float, float]) -> tuple[float, float]:
    return round(float(point[0]), 6), round(float(point[1]), 6)


def _edge_key(
    first: tuple[float, float], second: tuple[float, float]
) -> tuple[tuple[float, float], tuple[float, float]]:
    left, right = _point_key(first), _point_key(second)
    return (left, right) if left <= right else (right, left)


def _edge_id(key: tuple[tuple[float, float], tuple[float, float]]) -> str:
    digest = hashlib.sha256(
        json.dumps(key, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]
    return f"LAYOUT-WALL-{digest}"


def _line_geometry(
    first: tuple[float, float], second: tuple[float, float]
) -> dict[str, Any]:
    return {
        "type": "LineString",
        "coordinates": [
            [float(first[0]), float(first[1])],
            [float(second[0]), float(second[1])],
        ],
    }


def _operation(element: DesiredElement, request: PreflightRequest) -> StageOperation:
    preferred, fallbacks = provider_chain(
        request.registry,
        LAYOUT_CAPABILITY,
        revit_build=request.revit_build,
        tool_schema_hash=request.tool_schema_hash,
        scope=request.evidence_scope,
    )
    return StageOperation(
        stage=BimStage.R06,
        logical_id=element.logical_id,
        semantic_capability=LAYOUT_CAPABILITY,
        payload=element.model_dump(mode="json"),
        verification_rules=[
            "independent_requery",
            "unique_id_present",
            "boundary_matches",
            "logical_id_persists",
        ],
        preferred_provider=preferred,
        fallback_providers=fallbacks,
    )


def _preflight(request: PreflightRequest) -> tuple[PreflightRequest, PreflightReport]:
    effective = with_stage_requirements(request, extra=(LAYOUT_CAPABILITY,))
    if effective.stage is not BimStage.R06:
        raise StagePreflightError(
            f"R06 preflight refused: stage_identity: expected R06, got {effective.stage.name}"
        )
    report = run_preflight(effective)
    if not report.ok:
        raise StagePreflightError(
            "R06 preflight refused: " + "; ".join(report.problems)
        )
    return effective, report


def _range_for(value: Any) -> tuple[float, float] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        low = value.get("min", value.get("minimum"))
        high = value.get("max", value.get("maximum"))
    else:
        try:
            low, high = value
        except (TypeError, ValueError) as exc:
            raise StageError("area range must contain minimum and maximum") from exc
    if low is None or high is None or float(low) > float(high):
        raise StageError("area range must have minimum <= maximum")
    return float(low), float(high)


def plan_layout_stage(
    request: PreflightRequest,
    rooms: Sequence[Any],
    *,
    adjacency_relations: Sequence[Any] = (),
    flow_candidate: Mapping[str, Any] | None = None,
    flow_routes: Mapping[FlowNetwork | str, Sequence[str] | Mapping[str, str]]
    | None = None,
    area_ranges: Mapping[str, Any] | None = None,
    wall_thickness_m: float = 0.12,
    design_option: str | None = None,
) -> LayoutStagePlan:
    """Convert the shared boundaries of room polygons into internal walls.

    The exact geometry is kept as supplied.  Area ranges are a gate for
    acceptance; the planner never changes a polygon to chase a target value.
    """

    effective, report = _preflight(request)
    if not rooms:
        raise StageError("R06 layout requires room polygons")
    if wall_thickness_m <= 0:
        raise StageError("layout wall thickness must be positive")

    selected_option = design_option or (
        effective.solution.solution_id
        if effective.solution is not None
        else "SELECTED_DESIGN"
    )
    room_data: list[tuple[str, Polygon, float | None]] = []
    seen: set[str] = set()
    for index, room in enumerate(rooms, start=1):
        identifier = _identifier(room, f"ROOM-{index:03d}")
        if not identifier:
            raise StageError("layout rooms require logical_id")
        if identifier in seen:
            raise StageError(f"duplicate layout room logical_id: {identifier}")
        seen.add(identifier)
        polygon = _polygon(room)
        target = _value(room, "target_area_m2", _value(room, "area_m2"))
        room_data.append(
            (identifier, polygon, None if target is None else float(target))
        )

    geometry_map = {identifier: polygon for identifier, polygon, _ in room_data}
    adjacency_results = evaluate_adjacency(adjacency_relations, geometry_map)
    for adjacency_result in adjacency_results:
        if (
            adjacency_result.relation
            in {RelationType.MUST_ADJOIN, RelationType.MUST_BE_SEPARATED}
            and not adjacency_result.passed
        ):
            raise StageError(
                f"layout adjacency violation: {adjacency_result.source_logical_id} -> {adjacency_result.target_logical_id} ({adjacency_result.status.value})"
            )

    edge_occurrences: dict[
        tuple[tuple[float, float], tuple[float, float]], list[str]
    ] = defaultdict(list)
    edge_points: dict[
        tuple[tuple[float, float], tuple[float, float]],
        tuple[tuple[float, float], tuple[float, float]],
    ] = {}
    for room_id, polygon, _ in room_data:
        coordinates = [(float(x), float(y)) for x, y in polygon.exterior.coords]
        for first, second in pairwise(coordinates):
            key = _edge_key(first, second)
            if room_id not in edge_occurrences[key]:
                edge_occurrences[key].append(room_id)
            edge_points.setdefault(key, (first, second))

    elements: list[DesiredElement] = []
    for key in sorted(edge_occurrences):
        host_rooms = sorted(set(edge_occurrences[key]))
        if len(host_rooms) < 2:
            continue
        first, second = edge_points[key]
        element = DesiredElement(
            logical_id=_edge_id(key),
            category="INTERNAL_WALL",
            geometry=_line_geometry(first, second),
            properties={
                "wall_type_id": "INT_WALL_01",
                "thickness_m": float(wall_thickness_m),
                "location_line": "CENTERLINE",
                "joins": "AUTOMATIC_CORNERS",
                "host_dependencies": host_rooms,
                "boundary_role": "shared_room_boundary",
            },
            requirement_id="R06-LAYOUT",
            design_option=selected_option,
            generation_run=effective.generation_run,
        )
        elements.append(element)

    area_results: dict[str, dict[str, Any]] = {}
    configured_ranges = area_ranges or {}
    for identifier, polygon, target in room_data:
        actual = float(polygon.area)
        configured = _range_for(configured_ranges.get(identifier))
        if configured is not None and not (configured[0] <= actual <= configured[1]):
            raise StageError(
                f"layout area range violation for {identifier}: {actual:g} m2 is outside {configured[0]:g}..{configured[1]:g}"
            )
        area_results[identifier] = {
            "target_area_m2": target,
            "actual_area_m2": actual,
            "area_delta_m2": None if target is None else actual - target,
            "geometry_unchanged": True,
            "finished_face_area_pending_r08": True,
        }

    flow_results: dict[FlowNetwork, FlowAnalysis] = {}
    for raw_flow, route in (flow_routes or {}).items():
        flow = FlowNetwork(raw_flow)
        if flow_candidate is None:
            raise StageError(
                f"layout flow {flow.value} requires a flow graph candidate"
            )
        graph = build_flow_graph(flow_candidate, flow)
        if isinstance(route, Mapping):
            start, goal = str(route["start"]), str(route["goal"])
        else:
            if len(route) != 2:
                raise StageError(
                    f"layout flow route for {flow.value} requires start and goal"
                )
            start, goal = str(route[0]), str(route[1])
        flow_result = analyze_route(graph, start, goal)
        flow_results[flow] = flow_result
        if not flow_result.ok:
            raise StageError(
                f"layout flow violation for {flow.value}: "
                + "; ".join(item.code for item in flow_result.hard_violations)
            )

    desired_state = DesiredState(
        stage=BimStage.R06,
        generation_run=effective.generation_run,
        model_id=effective.solution.solution_id
        if effective.solution is not None
        else "STUDY",
        elements=elements,
    )
    operations = [_operation(element, effective) for element in elements]
    warnings = [
        "R06 records boundary/centreline geometry; finished-face Room areas are queried at R08",
    ]
    return LayoutStagePlan(
        preflight=report,
        desired_state=desired_state,
        operations=operations,
        adjacency_results=adjacency_results,
        flow_results=flow_results,
        area_results=area_results,
        warnings=warnings,
        checkpoint_label=stage_checkpoint_label(BimStage.R06),
    )


def execute_layout_stage(
    plan: LayoutStagePlan, *, invoker: StageToolInvoker
) -> list[StageExecutionRecord]:
    """Dispatch desired layout operations through the injected adapter."""

    return dispatch_operations(plan.operations, invoker=invoker)


def verify_layout_stage(
    plan: LayoutStagePlan,
    *,
    tool_reported_success: bool | Mapping[str, bool],
    query_results: Mapping[str, Mapping[str, Any] | None],
    geometry_tolerance: float = 1e-6,
) -> list[VerificationResult]:
    """Verify internal boundary elements against independent query results."""

    results: list[VerificationResult] = []
    for element in plan.desired_state.elements:
        success = (
            tool_reported_success.get(element.logical_id, False)
            if isinstance(tool_reported_success, Mapping)
            else tool_reported_success
        )
        results.extend(
            verify_write(
                logical_id=element.logical_id,
                tool_reported_success=success,
                query_result=query_results.get(element.logical_id),
                expected_geometry=element.geometry,
                expected_properties=element.properties,
                geometry_tolerance=geometry_tolerance,
            )
        )
    return results


plan_internal_layout = plan_layout_stage
plan_internal_layout_stage = plan_layout_stage
execute_internal_layout = execute_layout_stage


__all__ = [
    "LAYOUT_CAPABILITY",
    "LayoutStagePlan",
    "execute_internal_layout",
    "execute_layout_stage",
    "plan_internal_layout",
    "plan_internal_layout_stage",
    "plan_layout_stage",
    "verify_layout_stage",
]
