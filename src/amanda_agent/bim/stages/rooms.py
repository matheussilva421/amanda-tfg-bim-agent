"""Pure desired-state planning for canonical R08 room objects."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
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

ROOM_CAPABILITY = "revit.create_room"
DEFAULT_AREA_TOLERANCE_M2 = 1e-6
PROGRAM_INTERNAL_USEFUL_M2 = 626.0
PROGRAM_PERSON_CAPACITY = 20


class RoomsStagePlan(BaseModel):
    """R08 managed room desired state and independent program reconciliation."""

    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R08
    preflight: PreflightReport
    desired_state: DesiredState
    operations: list[StageOperation] = Field(default_factory=list)
    program_reconciliation: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    checkpoint_label: str = Field(default="R08_ROOMS", min_length=1)

    @property
    def desired_elements(self) -> list[DesiredElement]:
        return self.desired_state.elements


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def _identifier(item: Any, default: str = "") -> str:
    return str(_value(item, "logical_id", _value(item, "id", default)))


def _polygon(value: Any, identifier: str) -> Polygon:
    geometry = _value(value, "geometry", _value(value, "polygon", value))
    try:
        return validate_polygon(geometry)
    except (InvalidDesignGeometryError, ValueError, TypeError) as exc:
        raise StageError(f"room {identifier} is not enclosed: {exc}") from exc


def _polygon_geometry(polygon: Polygon) -> dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [[[float(x), float(y)] for x, y in polygon.exterior.coords]],
    }


def _sectors(program: Any) -> list[Any]:
    values = _value(program, "sectors")
    if values is None and isinstance(program, Mapping):
        values = (
            program.get("program", {}).get("sectors")
            if isinstance(program.get("program"), Mapping)
            else None
        )
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise StageError("R08 requires canonical program sectors")
    return list(values)


def _spaces(sector: Any) -> list[Any]:
    values = _value(sector, "spaces", ())
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise StageError("program sector spaces must be a sequence")
    return list(values)


def _room_instances(program: Any) -> tuple[list[dict[str, Any]], float, float]:
    instances: list[dict[str, Any]] = []
    computed_internal = 0.0
    computed_external = 0.0
    for sector in _sectors(program):
        sector_id = _identifier(sector)
        sector_name = str(_value(sector, "name", sector_id))
        area_kind = str(_value(sector, "area_kind", "INTERNAL")).upper()
        for space in _spaces(sector):
            space_id = _identifier(space)
            quantity = int(_value(space, "quantity", 1))
            if not space_id or quantity < 1:
                raise StageError(
                    "canonical program spaces require a positive quantity and logical_id"
                )
            target_area = float(
                _value(space, "target_area_m2", _value(space, "area_m2", 0.0))
            )
            if not math.isfinite(target_area) or target_area <= 0:
                raise StageError(
                    f"program room {space_id} target area must be positive"
                )
            total = target_area * quantity
            if area_kind == "INTERNAL":
                computed_internal += total
            else:
                computed_external += total
            for index in range(1, quantity + 1):
                room_id = space_id if quantity == 1 else f"{space_id}#{index}"
                instances.append(
                    {
                        "logical_id": room_id,
                        "requirement_id": space_id,
                        "name": str(_value(space, "name", space_id)),
                        "sector_id": sector_id,
                        "sector_name": sector_name,
                        "area_kind": area_kind,
                        "target_area_m2": target_area,
                        "quantity_index": index,
                        "quantity": quantity,
                        "accessible": _value(space, "accessible"),
                        "source_page": _value(space, "source_page"),
                        "privacy": _value(
                            space, "privacy", _value(space, "privacy_level")
                        ),
                    }
                )
    return instances, computed_internal, computed_external


def _program_value(program: Any, key: str, default: Any = None) -> Any:
    value = _value(program, key)
    if value is not None:
        return value
    baseline = _value(program, "baseline")
    if key == "person_capacity" and baseline is not None:
        return _value(baseline, key, default)
    totals = _value(program, "totals")
    if key == "internal_useful_m2" and totals is not None:
        return _value(totals, key, default)
    if key == "external_programmed_m2" and totals is not None:
        return _value(totals, key, default)
    return default


def _geometry_map(room_geometries: Any) -> dict[str, Any]:
    if isinstance(room_geometries, Mapping):
        return {str(key): value for key, value in room_geometries.items()}
    result: dict[str, Any] = {}
    for item in room_geometries or ():
        identifier = _identifier(item)
        if not identifier:
            raise StageError("room geometry entries require logical_id")
        if identifier in result:
            raise StageError(f"duplicate managed room geometry: {identifier}")
        result[identifier] = item
    return result


def _operation(element: DesiredElement, request: PreflightRequest) -> StageOperation:
    preferred, fallbacks = provider_chain(
        request.registry,
        ROOM_CAPABILITY,
        revit_build=request.revit_build,
        tool_schema_hash=request.tool_schema_hash,
        scope=request.evidence_scope,
    )
    return StageOperation(
        stage=BimStage.R08,
        logical_id=element.logical_id,
        semantic_capability=ROOM_CAPABILITY,
        payload=element.model_dump(mode="json"),
        verification_rules=[
            "independent_requery",
            "unique_id_present",
            "room_enclosed",
            "room_metadata_matches",
            "area_reconciled",
        ],
        preferred_provider=preferred,
        fallback_providers=fallbacks,
    )


def _preflight(request: PreflightRequest) -> tuple[PreflightRequest, PreflightReport]:
    effective = with_stage_requirements(request, extra=(ROOM_CAPABILITY,))
    if effective.stage is not BimStage.R08:
        raise StagePreflightError(
            f"R08 preflight refused: stage_identity: expected R08, got {effective.stage.name}"
        )
    report = run_preflight(effective)
    if not report.ok:
        raise StagePreflightError(
            "R08 preflight refused: " + "; ".join(report.problems)
        )
    return effective, report


def plan_rooms_stage(
    request: PreflightRequest,
    program: Any | None = None,
    room_geometries: Any | None = None,
    *,
    rooms: Any | None = None,
    privacy_by_room: Mapping[str, Any] | None = None,
    number_scheme: str = "{sector}-{index:03d}",
    design_option: str | None = None,
    area_tolerance_m2: float = DEFAULT_AREA_TOLERANCE_M2,
) -> RoomsStagePlan:
    """Associate one enclosed desired room with each internal canonical room ID.

    Area mismatches are carried as numeric divergence in the reconciliation
    report.  The planner never rounds geometry or changes it to hide a delta.
    """

    effective, report = _preflight(request)
    if area_tolerance_m2 < 0 or not math.isfinite(area_tolerance_m2):
        raise StageError("room area tolerance must be finite and non-negative")
    if program is None:
        raise StageError("R08 requires canonical program sectors")
    if room_geometries is None:
        room_geometries = rooms
    if room_geometries is None:
        raise StageError("R08 requires room geometry for canonical rooms")
    instances, computed_internal, computed_external = _room_instances(program)
    internal_instances = [
        instance for instance in instances if instance["area_kind"] == "INTERNAL"
    ]
    expected = {instance["logical_id"] for instance in internal_instances}
    geometries = _geometry_map(room_geometries)
    unknown = sorted(set(geometries) - expected)
    if unknown:
        raise StageError("redundant managed rooms supplied: " + ", ".join(unknown))

    selected_option = design_option or (
        effective.solution.solution_id
        if effective.solution is not None
        else "SELECTED_DESIGN"
    )
    elements: list[DesiredElement] = []
    actual_area = 0.0
    seen: set[str] = set()
    sector_counters: dict[str, int] = {}
    for instance in internal_instances:
        room_id = instance["logical_id"]
        if room_id in seen:
            raise StageError(f"duplicate canonical room logical_id: {room_id}")
        seen.add(room_id)
        if room_id not in geometries:
            raise StageError(f"room {room_id} is unplaced")
        raw_geometry = geometries[room_id]
        if _value(raw_geometry, "enclosed", True) is False:
            raise StageError(f"room {room_id} is not-enclosed")
        polygon = _polygon(raw_geometry, room_id)
        actual = float(polygon.area)
        actual_area += actual
        privacy = (privacy_by_room or {}).get(room_id, instance["privacy"])
        sector_id = instance["sector_id"]
        sector_index = sector_counters.get(sector_id, 0) + 1
        sector_counters[sector_id] = sector_index
        number = number_scheme.format(sector=sector_id, index=sector_index)
        properties = {
            "name": instance["name"],
            "number": number,
            "sector": instance["sector_id"],
            "sector_name": instance["sector_name"],
            "target_area_m2": instance["target_area_m2"],
            "actual_geometry_area_m2": actual,
            "privacy": privacy,
            "accessible": instance["accessible"],
            "source_page": instance["source_page"],
            "quantity_index": instance["quantity_index"],
            "requirement_id": instance["requirement_id"],
            "enclosed": True,
        }
        elements.append(
            DesiredElement(
                logical_id=room_id,
                category="ROOM",
                geometry=_polygon_geometry(polygon),
                properties=properties,
                requirement_id=instance["requirement_id"],
                design_option=selected_option,
                generation_run=effective.generation_run,
            )
        )

    source_internal = float(
        _program_value(program, "internal_useful_m2", computed_internal)
    )
    source_external = float(
        _program_value(program, "external_programmed_m2", computed_external)
    )
    person_capacity = int(
        _program_value(program, "person_capacity", PROGRAM_PERSON_CAPACITY)
    )
    area_delta = actual_area - source_internal
    capacity_ok = 0 < person_capacity <= PROGRAM_PERSON_CAPACITY
    divergence = abs(area_delta) > area_tolerance_m2
    reconciliation = {
        "target_internal_useful_m2": source_internal,
        "actual_geometry_area_m2": float(actual_area),
        "area_delta_m2": float(area_delta),
        "area_tolerance_m2": float(area_tolerance_m2),
        "divergence": divergence,
        "status": "DIVERGENCE" if divergence else "MATCH",
        "external_programmed_m2": source_external,
        "person_capacity": person_capacity,
        "capacity_limit": PROGRAM_PERSON_CAPACITY,
        "capacity_ok": capacity_ok,
        "room_count": len(elements),
        "internal_canonical_area_m2": float(computed_internal),
        "external_canonical_area_m2": float(computed_external),
        "program_baseline_matches_626_m2": math.isclose(
            source_internal, PROGRAM_INTERNAL_USEFUL_M2, abs_tol=area_tolerance_m2
        ),
        "program_baseline_matches_20_people": person_capacity
        == PROGRAM_PERSON_CAPACITY,
    }
    desired_state = DesiredState(
        stage=BimStage.R08,
        generation_run=effective.generation_run,
        model_id=effective.solution.solution_id
        if effective.solution is not None
        else "STUDY",
        elements=elements,
    )
    warnings = [
        "R08 uses independent geometry area for reconciliation; no target-area rounding or wall deformation is performed",
        "external programmed spaces remain in program accounting and are not emitted as enclosed Room objects",
    ]
    if not capacity_ok:
        warnings.append(
            f"program capacity divergence: {person_capacity} exceeds the 20-person baseline"
        )
    return RoomsStagePlan(
        preflight=report,
        desired_state=desired_state,
        operations=[_operation(element, effective) for element in elements],
        program_reconciliation=reconciliation,
        warnings=warnings,
        checkpoint_label=stage_checkpoint_label(BimStage.R08),
    )


def execute_rooms_stage(
    plan: RoomsStagePlan, *, invoker: StageToolInvoker
) -> list[StageExecutionRecord]:
    """Dispatch desired room operations through the injected adapter."""

    return dispatch_operations(plan.operations, invoker=invoker)


def verify_rooms_stage(
    plan: RoomsStagePlan,
    *,
    tool_reported_success: bool | Mapping[str, bool],
    query_results: Mapping[str, Mapping[str, Any] | None],
    geometry_tolerance: float = 1e-6,
) -> list[VerificationResult]:
    """Verify enclosed room objects and managed metadata independently."""

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


plan_room_stage = plan_rooms_stage
plan_rooms = plan_rooms_stage
execute_room_stage = execute_rooms_stage


__all__ = [
    "DEFAULT_AREA_TOLERANCE_M2",
    "PROGRAM_INTERNAL_USEFUL_M2",
    "PROGRAM_PERSON_CAPACITY",
    "ROOM_CAPABILITY",
    "RoomsStagePlan",
    "execute_room_stage",
    "execute_rooms_stage",
    "plan_room_stage",
    "plan_rooms",
    "plan_rooms_stage",
    "verify_rooms_stage",
]
