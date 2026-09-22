"""Pure desired-state planning for the R05 architectural shell.

The module turns room and envelope geometry into stable managed elements.  It
does not know how Revit stores an element: a caller supplies the capability
registry and, only at execution time, an injected ``StageToolInvoker``.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from itertools import pairwise
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import Polygon  # type: ignore[import-untyped]

from amanda_agent.design.geometry import InvalidDesignGeometryError, validate_polygon

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

WALL_CAPABILITY = "revit.create_wall"
FLOOR_CAPABILITY = "revit.create_floor"
SLAB_CAPABILITY = "revit.create_slab"
ROOF_CAPABILITY = "revit.create_roof"
LINK_CAPABILITY = "revit.link_model"
SHELL_CAPABILITIES = (
    WALL_CAPABILITY,
    FLOOR_CAPABILITY,
    SLAB_CAPABILITY,
    ROOF_CAPABILITY,
)

DEFAULT_WALL_TYPES = {"external": "EXT_WALL_01", "internal": "INT_WALL_01"}
#: The placeholder names above are the compiler's own vocabulary.  A real model
#: carries whatever types its template ships, and a wall type that does not
#: exist is refused by the provider, so a caller that has read the template's
#: real types must be able to name them.  The catalog below is therefore the set
#: of REGISTRY-PLACEHOLDER names, not a whitelist of permitted real types.
_PLACEHOLDER_WALL_TYPES = frozenset(DEFAULT_WALL_TYPES.values())
_WALL_TYPE_KEYS = frozenset(DEFAULT_WALL_TYPES)
DEFAULT_WALL_THICKNESSES = {"external": 0.20, "internal": 0.12}
DEFAULT_WALL_MATERIALS = {
    "external": "EXT_WALL_MATERIAL",
    "internal": "INT_WALL_MATERIAL",
}


class ShellStagePlan(BaseModel):
    """R05 desired state, operations and auditable geometry accounting."""

    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R05
    preflight: PreflightReport
    desired_state: DesiredState
    operations: list[StageOperation] = Field(default_factory=list)
    area_reconciliation: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    checkpoint_label: str = Field(default="R05_ARCHITECTURAL_SHELL", min_length=1)

    @property
    def desired_elements(self) -> list[DesiredElement]:
        return self.desired_state.elements


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def _identifier(item: Any, default: str = "") -> str:
    return str(_value(item, "logical_id", _value(item, "id", default)))


def _as_polygon(item: Any) -> Polygon:
    geometry = _value(item, "geometry", _value(item, "polygon", item))
    try:
        return validate_polygon(geometry)
    except (InvalidDesignGeometryError, ValueError, TypeError) as exc:
        raise StageError(f"invalid shell geometry: {exc}") from exc


def _point_key(point: tuple[float, float]) -> tuple[float, float]:
    return (round(float(point[0]), 6), round(float(point[1]), 6))


def _edge_key(
    first: tuple[float, float], second: tuple[float, float]
) -> tuple[tuple[float, float], tuple[float, float]]:
    left, right = _point_key(first), _point_key(second)
    return (left, right) if left <= right else (right, left)


def _edge_id(key: tuple[tuple[float, float], tuple[float, float]]) -> str:
    digest = hashlib.sha256(
        json.dumps(key, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]
    return f"WALL-{digest}"


def _merge_collinear_edges(
    edge_occurrences: dict[tuple[tuple[float, float], tuple[float, float]], list[str]],
    edge_points: dict[
        tuple[tuple[float, float], tuple[float, float]],
        tuple[tuple[float, float], tuple[float, float]],
    ],
) -> dict[
    tuple[tuple[float, float], tuple[float, float]],
    tuple[tuple[str, ...], tuple[float, float], tuple[float, float], bool],
]:
    """Merge room edges that lie on one line and form one continuous run.

    Rooms whose faces step by a few centimetres leave two collinear walls, and
    Revit refuses the batch with "the highlighted walls overlap".  A person
    drawing the plan would run one wall along that line, and so does this: the
    merged run spans both, keeps every room that owned any part of it, and
    carries a deterministic identity of its own so the result stays reproducible.
    """

    def axis_of(first, second) -> int | None:
        if abs(first[0] - second[0]) < 1e-6:
            return 0
        if abs(first[1] - second[1]) < 1e-6:
            return 1
        return None

    buckets: dict[
        tuple[int, float, bool],
        list[
            tuple[
                float,
                float,
                tuple[tuple[float, float], tuple[float, float]],
            ]
        ],
    ] = defaultdict(list)
    merged: dict[
        tuple[tuple[float, float], tuple[float, float]],
        tuple[tuple[str, ...], tuple[float, float], tuple[float, float], bool],
    ] = {}
    for key, room_ids in edge_occurrences.items():
        first, second = edge_points[key]
        axis = axis_of(first, second)
        is_shared = len(room_ids) > 1
        if axis is None:
            # The architectural layout contains a few diagonal corners.  They
            # cannot be merged by an axis-aligned sweep, but they are still
            # valid shell edges and must remain part of the desired state.
            merged[key] = (tuple(sorted(set(room_ids))), first, second, is_shared)
            continue
        # ``axis`` is the coordinate that stays fixed along the segment.  The
        # interval therefore varies on the other coordinate: y for a vertical
        # run (axis 0) and x for a horizontal run (axis 1).
        fixed = round(first[axis], 6)
        varying_axis = 1 - axis
        low, high = sorted((first[varying_axis], second[varying_axis]))
        buckets[(axis, fixed, is_shared)].append((low, high, key))

    for (axis, fixed, _is_shared), spans in buckets.items():
        # Sort by interval start so each connected component can be emitted
        # independently.  Touching runs are joined because Revit's automatic
        # wall joins can report their bodies as overlapping when submitted as
        # separate walls.
        ordered = sorted(spans, key=lambda span: (span[0], span[1], span[2]))
        component: list[tuple[float, float, tuple[tuple[float, float], tuple[float, float]]]] = []

        def emit(items, *, axis=axis, fixed=fixed, is_shared=_is_shared):
            if not items:
                return
            low = min(item[0] for item in items)
            high = max(item[1] for item in items)
            start = (fixed, low) if axis == 0 else (low, fixed)
            end = (fixed, high) if axis == 0 else (high, fixed)
            output_key = _edge_key(start, end)
            owners = sorted(
                {
                    room_id
                    for item in items
                    for room_id in edge_occurrences[item[2]]
                }
            )
            if len(items) == 1:
                original_key = items[0][2]
                start, end = edge_points[original_key]
                output_key = original_key
            merged[output_key] = (
                tuple(owners),
                start,
                end,
                is_shared,
            )

        for span in ordered:
            if not component or span[0] <= max(item[1] for item in component) + 1e-6:
                component.append(span)
                continue
            emit(component)
            component = [span]
        emit(component)
    return merged


def _polygon_geometry(polygon: Polygon) -> dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [[[float(x), float(y)] for x, y in polygon.exterior.coords]],
    }


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


def _coerce_element(value: DesiredElement | Mapping[str, Any]) -> DesiredElement:
    return (
        value
        if isinstance(value, DesiredElement)
        else DesiredElement.model_validate(value)
    )


def _element_operation(
    element: DesiredElement,
    capability: str,
    request: PreflightRequest,
) -> StageOperation:
    preferred, fallbacks = provider_chain(
        request.registry,
        capability,
        revit_build=request.revit_build,
        tool_schema_hash=request.tool_schema_hash,
        scope=request.evidence_scope,
    )
    return StageOperation(
        stage=BimStage.R05,
        logical_id=element.logical_id,
        semantic_capability=capability,
        payload=element.model_dump(mode="json"),
        verification_rules=[
            "independent_requery",
            "unique_id_present",
            "geometry_matches",
            "properties_match",
            "duplicate_warnings_clear",
            "off_axis_warnings_clear",
            "unjoined_warnings_clear",
        ],
        preferred_provider=preferred,
        fallback_providers=fallbacks,
    )


def _preflight(
    request: PreflightRequest, *, include_link: bool
) -> tuple[PreflightRequest, PreflightReport]:
    extras = list(SHELL_CAPABILITIES)
    if include_link:
        extras.append(LINK_CAPABILITY)
    effective = with_stage_requirements(request, extra=extras)
    if effective.stage is not BimStage.R05:
        raise StagePreflightError(
            f"R05 preflight refused: stage_identity: expected R05, got {effective.stage.name}"
        )
    report = run_preflight(effective)
    if not report.ok:
        raise StagePreflightError(
            "R05 preflight refused: " + "; ".join(report.problems)
        )
    return effective, report


def plan_shell_stage(
    request: PreflightRequest,
    rooms: Sequence[Any],
    *,
    gross_shell: Any | None = None,
    floor_loops: Sequence[Any] | None = None,
    slab_loops: Sequence[Any] | None = None,
    roof: Mapping[str, Any] | None = None,
    openings: Sequence[Any] | None = None,
    wall_types: Mapping[str, str] | None = None,
    wall_type_source: str | None = None,
    wall_thicknesses_m: Mapping[str, float] | None = None,
    wall_materials: Mapping[str, str] | None = None,
    design_option: str | None = None,
    external_elements: Sequence[DesiredElement | Mapping[str, Any]] = (),
    external_planner: Callable[[], Sequence[DesiredElement | Mapping[str, Any]]]
    | None = None,
    link_model: Callable[..., DesiredElement] | None = None,
    model_path: str | None = None,
    link_name: str = "linked-model",
    link_insertion: Mapping[str, float] | Sequence[float] = (0.0, 0.0, 0.0),
) -> ShellStagePlan:
    """Describe walls, floors, slabs and a simple roof from closed geometry.

    Every room boundary is collected before elements are created.  Identical
    reversed segments therefore become one managed wall with both room IDs in
    ``host_dependencies``.
    """

    include_link = (
        link_model is not None
        or bool(external_elements)
        or external_planner is not None
    )
    effective, report = _preflight(request, include_link=include_link)
    if not rooms:
        raise StageError("R05 shell requires at least one room geometry")

    selected_option = design_option or (
        effective.solution.solution_id
        if effective.solution is not None
        else "SELECTED_DESIGN"
    )
    types = dict(DEFAULT_WALL_TYPES)
    types.update(wall_types or {})
    if set(types) - _WALL_TYPE_KEYS:
        raise StageError("wall type catalog accepts only external and internal entries")
    # A type is either the compiler's own placeholder or a real type the caller
    # READ OFF the target model.  The difference matters: a placeholder is the
    # stage's vocabulary, while a real type is a fact about a document, and a
    # name that exists in no document is refused by the provider after the
    # transaction has already begun.  A caller that supplies anything other than
    # the placeholders must therefore also say where those names came from, so
    # an invented type cannot pass as a verified one.
    observed = {str(value).strip() for value in (wall_types or {}).values()}
    if not observed <= _PLACEHOLDER_WALL_TYPES:
        if not str(wall_type_source or "").strip():
            raise StageError(
                "wall type catalog contains an uncontrolled type: a type other "
                "than the built-in placeholders requires wall_type_source naming "
                "the target document or catalog it was read from"
            )
    if any(not str(value).strip() for value in types.values()):
        raise StageError("wall type catalog contains an empty type name")
    thicknesses = dict(DEFAULT_WALL_THICKNESSES)
    thicknesses.update(wall_thicknesses_m or {})
    materials = dict(DEFAULT_WALL_MATERIALS)
    materials.update(wall_materials or {})
    if any(float(value) <= 0 for value in thicknesses.values()):
        raise StageError("wall thickness must be positive")

    room_polygons: list[tuple[str, Polygon]] = []
    for index, room in enumerate(rooms, start=1):
        identifier = _identifier(room, f"ROOM-{index:03d}")
        if not identifier:
            raise StageError("shell rooms require logical_id")
        room_polygons.append((identifier, _as_polygon(room)))

    edge_occurrences: dict[
        tuple[tuple[float, float], tuple[float, float]], list[str]
    ] = defaultdict(list)
    edge_points: dict[
        tuple[tuple[float, float], tuple[float, float]],
        tuple[tuple[float, float], tuple[float, float]],
    ] = {}
    for room_id, polygon in room_polygons:
        coordinates = [(float(x), float(y)) for x, y in polygon.exterior.coords]
        for first, second in pairwise(coordinates):
            key = _edge_key(first, second)
            if room_id not in edge_occurrences[key]:
                edge_occurrences[key].append(room_id)
            edge_points.setdefault(key, (first, second))

    opening_by_host: dict[str, list[str]] = defaultdict(list)
    for opening in openings or ():
        host_id = _value(opening, "host_logical_id", _value(opening, "host_id"))
        opening_id = _identifier(opening)
        if host_id and opening_id:
            opening_by_host[str(host_id)].append(opening_id)

    elements: list[DesiredElement] = []
    capabilities: dict[str, str] = {}
    # A room edge becomes one wall, but two rooms whose faces step by a few
    # centimetres put two walls on the same line.  Revit joins them into a T,
    # warns that the walls overlap, and refuses the batch, so runs that lie on
    # one line are merged into the single wall a person would draw.  The merge
    # happens before the desired state is built, which is why it can be
    # verified: every wall still corresponds to a boundary of the plan.
    merged_edges = _merge_collinear_edges(
        edge_occurrences, edge_points
    )
    for key in sorted(merged_edges):
        room_ids, first, second, is_shared = merged_edges[key]
        kind = "internal" if is_shared else "external"
        logical_id = _edge_id(key)
        opening_ids: set[str] = set(opening_by_host.get(logical_id, []))
        for room_id in room_ids:
            opening_ids.update(opening_by_host.get(room_id, []))
        properties = {
            "type_id": types[kind],
            "wall_kind": kind,
            "thickness_m": float(thicknesses[kind]),
            "material": materials[kind],
            "location_line": "CENTERLINE",
            "joins": "AUTOMATIC_CORNERS",
            "is_shared": is_shared,
            "host_dependencies": room_ids,
            "opening_logical_ids": sorted(opening_ids),
        }
        element = DesiredElement(
            logical_id=logical_id,
            category="WALL",
            geometry=_line_geometry(first, second),
            properties=properties,
            requirement_id="R05-SHELL",
            design_option=selected_option,
            generation_run=effective.generation_run,
        )
        elements.append(element)
        capabilities[logical_id] = WALL_CAPABILITY

    def add_loop_elements(
        loops: Sequence[Any], category: str, capability: str, prefix: str
    ) -> None:
        for index, loop in enumerate(loops, start=1):
            polygon = _as_polygon(loop)
            logical_id = f"{prefix}-{index:03d}"
            element = DesiredElement(
                logical_id=logical_id,
                category=category,
                geometry=_polygon_geometry(polygon),
                properties={"closed_loop": True, "loop_index": index},
                requirement_id="R05-SHELL",
                design_option=selected_option,
                generation_run=effective.generation_run,
            )
            elements.append(element)
            capabilities[logical_id] = capability

    shell_polygon = _as_polygon(gross_shell) if gross_shell is not None else None
    add_loop_elements(
        floor_loops or ([shell_polygon] if shell_polygon is not None else []),
        "FLOOR",
        FLOOR_CAPABILITY,
        "FLOOR",
    )
    add_loop_elements(slab_loops or [], "SLAB", SLAB_CAPABILITY, "SLAB")
    if roof is not None or shell_polygon is not None:
        roof_polygon = _as_polygon(
            roof.get("geometry", shell_polygon) if roof is not None else shell_polygon
        )
        roof_properties = dict(roof or {})
        roof_properties.pop("geometry", None)
        roof_properties.setdefault("type", "simple-approved")
        roof_properties.setdefault("elevation_m", 0.0)
        roof_properties["closed_loop"] = True
        element = DesiredElement(
            logical_id="ROOF-001",
            category="ROOF",
            geometry=_polygon_geometry(roof_polygon),
            properties=roof_properties,
            requirement_id="R05-SHELL",
            design_option=selected_option,
            generation_run=effective.generation_run,
        )
        elements.append(element)
        capabilities[element.logical_id] = ROOF_CAPABILITY

    planned_external: Sequence[DesiredElement | Mapping[str, Any]] = ()
    if external_planner is not None:
        planned = external_planner()
        if isinstance(planned, (DesiredElement, Mapping)):
            planned_external = (planned,)
        else:
            planned_external = planned
    for item in [*external_elements, *planned_external]:
        element = _coerce_element(item)
        elements.append(element)
        capabilities[element.logical_id] = LINK_CAPABILITY
    if link_model is not None:
        if model_path is None:
            raise StageError("a linked model planner requires model_path")
        linked = link_model(model_path, name=link_name, insertion=link_insertion)
        element = _coerce_element(linked)
        elements.append(element)
        capabilities[element.logical_id] = LINK_CAPABILITY

    desired_state = DesiredState(
        stage=BimStage.R05,
        generation_run=effective.generation_run,
        model_id=effective.solution.solution_id
        if effective.solution is not None
        else "STUDY",
        elements=elements,
    )
    operations = [
        _element_operation(element, capabilities[element.logical_id], effective)
        for element in elements
    ]
    net_room_area = sum(polygon.area for _, polygon in room_polygons)
    gross_shell_area = (
        shell_polygon.area if shell_polygon is not None else net_room_area
    )
    wall_count = sum(1 for element in elements if element.category == "WALL")
    reconciliation = {
        "net_room_area_m2": float(net_room_area),
        "gross_shell_area_m2": float(gross_shell_area),
        "area_delta_m2": float(gross_shell_area - net_room_area),
        "wall_count": float(wall_count),
        "shared_wall_count": float(
            sum(
                bool(element.properties["is_shared"])
                for element in elements
                if element.category == "WALL"
            )
        ),
    }
    warnings = [
        "R05 verifies shell boundary geometry; computed Revit Room areas belong to R08",
    ]
    if not shell_polygon:
        warnings.append(
            "gross shell geometry was not supplied; room envelope area is used for reconciliation"
        )
    return ShellStagePlan(
        preflight=report,
        desired_state=desired_state,
        operations=operations,
        area_reconciliation=reconciliation,
        warnings=warnings,
        checkpoint_label=stage_checkpoint_label(BimStage.R05),
    )


def execute_shell_stage(
    plan: ShellStagePlan, *, invoker: StageToolInvoker
) -> list[StageExecutionRecord]:
    """Dispatch desired shell operations through the injected adapter."""

    return dispatch_operations(plan.operations, invoker=invoker)


def _query_for(
    query_result: Mapping[str, Any] | None, logical_id: str
) -> Mapping[str, Any] | None:
    if query_result is None:
        return None
    if query_result.get("logical_id") == logical_id:
        return query_result
    candidate = query_result.get(logical_id)
    return candidate if isinstance(candidate, Mapping) else None


def verify_shell_stage(
    plan: ShellStagePlan,
    *,
    tool_reported_success: bool | Mapping[str, bool],
    query_results: Mapping[str, Mapping[str, Any] | None] | None = None,
    query_result: Mapping[str, Any] | None = None,
    geometry_tolerance: float = 1e-6,
) -> list[VerificationResult]:
    """Return independent verification records for every desired shell element."""

    results: list[VerificationResult] = []
    for element in plan.desired_state.elements:
        success = (
            tool_reported_success.get(element.logical_id, False)
            if isinstance(tool_reported_success, Mapping)
            else tool_reported_success
        )
        observed = (
            query_results.get(element.logical_id)
            if query_results is not None
            else _query_for(query_result, element.logical_id)
        )
        results.extend(
            verify_write(
                logical_id=element.logical_id,
                tool_reported_success=success,
                query_result=observed,
                expected_geometry=element.geometry,
                expected_properties=element.properties,
                geometry_tolerance=geometry_tolerance,
            )
        )
    return results


plan_architectural_shell = plan_shell_stage
plan_architectural_shell_stage = plan_shell_stage
execute_architectural_shell = execute_shell_stage


__all__ = [
    "DEFAULT_WALL_MATERIALS",
    "DEFAULT_WALL_THICKNESSES",
    "DEFAULT_WALL_TYPES",
    "FLOOR_CAPABILITY",
    "LINK_CAPABILITY",
    "ROOF_CAPABILITY",
    "SHELL_CAPABILITIES",
    "SLAB_CAPABILITY",
    "WALL_CAPABILITY",
    "ShellStagePlan",
    "execute_architectural_shell",
    "execute_shell_stage",
    "plan_architectural_shell",
    "plan_architectural_shell_stage",
    "plan_shell_stage",
    "verify_shell_stage",
]
