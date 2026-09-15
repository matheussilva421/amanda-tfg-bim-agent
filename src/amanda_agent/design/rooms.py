"""Deterministic room refinement with explicit internal area accounting."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from shapely.geometry import Polygon, box, shape  # type: ignore[import-untyped]

from .geometry import InvalidDesignGeometryError, validate_polygon


@dataclass(frozen=True)
class RoomViolation:
    code: str
    message: str
    logical_id: str | None = None


@dataclass(frozen=True)
class RoomLayoutValidation:
    violations: list[RoomViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations


@dataclass(frozen=True)
class RoomRefinementResult:
    rooms: list[dict[str, Any]] = field(default_factory=list)
    violations: list[RoomViolation] = field(default_factory=list)
    accounting: dict[str, float] = field(default_factory=dict)
    net_to_gross_is_hypothesis: bool = True

    @property
    def ok(self) -> bool:
        return not self.violations


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _polygon(value: Any) -> Polygon:
    if isinstance(value, Polygon):
        return validate_polygon(value)
    if isinstance(value, dict):
        return validate_polygon(shape(value))
    return validate_polygon(value)


def _room_instances(requirements: list[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for requirement in requirements:
        base = str(_value(requirement, "logical_id", _value(requirement, "id", "room")))
        quantity = int(_value(requirement, "quantity", 1) or 1)
        for index in range(quantity):
            result.append({
                "logical_id_base": base,
                "logical_id": base if quantity == 1 else f"{base}#{index + 1}",
                "target_area_m2": float(_value(requirement, "target_area_m2", _value(requirement, "area_m2", 0))),
                "requirement": requirement,
            })
    return result


def validate_room_layout(
    rooms: list[Any],
    *,
    entry_id: str | None = None,
    connections: list[Any] | None = None,
) -> RoomLayoutValidation:
    """Check overlap and reachability using room touching or actual connections."""

    violations: list[RoomViolation] = []
    identifiers = [str(_value(item, "logical_id", _value(item, "id", ""))) for item in rooms]
    geometries: dict[str, Polygon] = {}
    for item, identifier in zip(rooms, identifiers):
        try:
            geometries[identifier] = _polygon(_value(item, "geometry", item))
        except (InvalidDesignGeometryError, ValueError, TypeError) as exc:
            violations.append(RoomViolation("invalid_geometry", str(exc), identifier))
    for index, first_id in enumerate(identifiers):
        for second_id in identifiers[index + 1 :]:
            if first_id in geometries and second_id in geometries and geometries[first_id].intersection(geometries[second_id]).area > 1e-6:
                violations.append(RoomViolation("room_overlap", f"{first_id} overlaps {second_id}"))
    graph: dict[str, set[str]] = {identifier: set() for identifier in identifiers}
    if connections:
        for item in connections:
            source = str(_value(item, "from", _value(item, "source", "")))
            target = str(_value(item, "to", _value(item, "target", "")))
            if source in graph and target in graph:
                graph[source].add(target)
                graph[target].add(source)
    else:
        for index, first_id in enumerate(identifiers):
            for second_id in identifiers[index + 1 :]:
                if first_id in geometries and second_id in geometries and geometries[first_id].touches(geometries[second_id]):
                    graph[first_id].add(second_id)
                    graph[second_id].add(first_id)
    if identifiers:
        root = entry_id or identifiers[0]
        if root not in graph:
            violations.append(RoomViolation("entry_missing", f"entry room {root} is missing", root))
        else:
            reachable = {root}
            pending = [root]
            while pending:
                current = pending.pop(0)
                for neighbour in sorted(graph[current]):
                    if neighbour not in reachable:
                        reachable.add(neighbour)
                        pending.append(neighbour)
            for identifier in identifiers:
                if identifier not in reachable:
                    violations.append(RoomViolation("unreachable_room", f"room {identifier} is unreachable from {root}", identifier))
    return RoomLayoutValidation(violations=violations)


def refine_rooms(
    block: Any,
    requirements: list[Any],
    *,
    wall_thickness_m: float = 0.2,
    circulation_area_m2: float = 0.0,
    min_dimension_m: float | None = None,
    storeys: int = 1,
    external_spaces: list[Any] | None = None,
) -> RoomRefinementResult:
    """Place room net footprints in deterministic strips inside one block."""

    if not isfinite(wall_thickness_m) or wall_thickness_m < 0:
        raise ValueError("wall_thickness_m must be finite and non-negative")
    if not isfinite(circulation_area_m2) or circulation_area_m2 < 0:
        raise ValueError("circulation_area_m2 must be finite and non-negative")
    if storeys < 1:
        raise ValueError("storeys must be positive")
    del external_spaces  # External program geometry has its own accounting.
    try:
        polygon = _polygon(_value(block, "geometry", block))
    except (InvalidDesignGeometryError, ValueError, TypeError) as exc:
        return RoomRefinementResult(violations=[RoomViolation("invalid_geometry", str(exc))])
    instances = _room_instances(requirements)
    total_net = sum(item["target_area_m2"] for item in instances)
    if any(item["target_area_m2"] <= 0 for item in instances):
        return RoomRefinementResult(violations=[RoomViolation("invalid_area", "room target area must be positive")])
    if total_net + circulation_area_m2 > polygon.area + 1e-6:
        return RoomRefinementResult(violations=[RoomViolation("block_capacity", "rooms and circulation exceed block area")])
    min_x, min_y, max_x, max_y = polygon.bounds
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0:
        return RoomRefinementResult(violations=[RoomViolation("invalid_geometry", "block has no usable dimensions")])
    rooms: list[dict[str, Any]] = []
    y = min_y
    per_floor_rooms: list[list[dict[str, Any]]] = []
    net_per_floor = sum(item["target_area_m2"] for item in instances)
    for level_index in range(storeys):
        floor_rooms: list[dict[str, Any]] = []
        y = min_y
        for instance in instances:
            room_height = instance["target_area_m2"] / width
            if abs((y + room_height) - max_y) <= 1e-9:
                room_height = max_y - y
            geometry = box(min_x, y, max_x, y + room_height)
            if not polygon.covers(geometry):
                return RoomRefinementResult(violations=[RoomViolation("room_outside_block", f"room {instance['logical_id']} is outside block", instance["logical_id"])])
            actual_min_dimension = min(width, room_height)
            requirement = instance["requirement"]
            required_dimension = _value(requirement, "min_dimension_m", min_dimension_m)
            if required_dimension is not None and actual_min_dimension + 1e-9 < float(required_dimension):
                return RoomRefinementResult(violations=[RoomViolation("minimum_dimension", f"room {instance['logical_id']} is below its minimum dimension", instance["logical_id"])])
            net_area = float(geometry.area)
            minimum_area = _value(requirement, "min_area_m2")
            maximum_area = _value(requirement, "max_area_m2")
            if minimum_area is not None and net_area + 1e-9 < float(minimum_area):
                return RoomRefinementResult(violations=[RoomViolation("room_area_below_minimum", f"room {instance['logical_id']} is below its minimum net area", instance["logical_id"])])
            if maximum_area is not None and net_area - 1e-9 > float(maximum_area):
                return RoomRefinementResult(violations=[RoomViolation("room_area_above_maximum", f"room {instance['logical_id']} exceeds its maximum net area", instance["logical_id"])])
            wall_area = float(geometry.length * wall_thickness_m)
            room_id = instance["logical_id"] if storeys == 1 else f"{instance['logical_id']}@L{level_index + 1}"
            floor_rooms.append({
                "logical_id": room_id,
                "logical_id_base": instance["logical_id_base"],
                "geometry": geometry,
                "net_area_m2": net_area,
                "gross_footprint_m2": net_area + wall_area,
                "wall_thickness_m": wall_thickness_m,
                "shafts_m2": float(_value(requirement, "shafts_m2", 0.0) or 0.0),
                "circulation_m2": float(_value(requirement, "circulation_m2", 0.0) or 0.0),
                "level": int(_value(block, "level", _value(block, "storey", 0))) + level_index,
                "accessible": _value(requirement, "accessible", False),
            })
            y += room_height
        per_floor_rooms.append(floor_rooms)
        rooms.extend(floor_rooms)
    validation_violations: list[RoomViolation] = []
    for floor_rooms in per_floor_rooms:
        validation_violations.extend(validate_room_layout(floor_rooms).violations)
    validation = RoomLayoutValidation(violations=validation_violations)
    accounting = {
        "net_area_m2": sum(item["net_area_m2"] for item in rooms),
        "internal_net_area_m2": sum(item["net_area_m2"] for item in rooms),
        "gross_footprint_m2": sum(item["gross_footprint_m2"] for item in rooms),
        "wall_area_m2": sum(item["gross_footprint_m2"] - item["net_area_m2"] for item in rooms),
        "shafts_m2": sum(item["shafts_m2"] for item in rooms),
        "circulation_m2": float(circulation_area_m2) * storeys + sum(item["circulation_m2"] for item in rooms),
        "storeys": float(storeys),
        "external_area_m2": 0.0,
        "net_area_per_storey_m2": net_per_floor,
    }
    accounting["net_to_gross_factor"] = accounting["net_area_m2"] / max(accounting["gross_footprint_m2"] + circulation_area_m2, 1e-9)
    return RoomRefinementResult(rooms=rooms, violations=validation.violations, accounting=accounting)


refine_room_layout = refine_rooms


__all__ = ["RoomLayoutValidation", "RoomRefinementResult", "RoomViolation", "refine_room_layout", "refine_rooms", "validate_room_layout"]
