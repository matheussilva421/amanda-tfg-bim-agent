"""Hard and unavailable checks for the progressive design resolutions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from enum import StrEnum
from typing import Any

from amanda_agent.requirements.models import ProgramRequirementSet
from amanda_agent.requirements.relations import RelationType

from .geometry import (
    InvalidDesignGeometryError,
    contains,
    minimum_distance,
    overlaps,
    validate_polygon,
)
from .models import (
    ConstraintStatus,
    ConstraintViolation,
    ViolationSeverity,
)


class ConstraintResolution(StrEnum):
    """Resolution at which a candidate is currently being checked."""

    MACRO = "MACRO"
    BLOCK = "BLOCK"
    ROOM = "ROOM"


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        values = value.model_dump(mode="python")
        geometry = values.get("geometry")
        if isinstance(geometry, Mapping):
            values.update(
                {
                    key: item
                    for key, item in geometry.items()
                    if key not in values
                }
            )
        return values
    raise TypeError("candidate must be a mapping or Pydantic model")


def _item_geometry(item: Any) -> Any:
    if isinstance(item, Mapping):
        for key in ("geometry", "polygon", "coordinates"):
            if key in item:
                return item[key]
    if hasattr(item, "geometry"):
        return item.geometry
    return item


def _items(candidate: Mapping[str, Any], key: str) -> list[Any]:
    value = candidate.get(key, [])
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(f"candidate {key} must be a sequence")
    return list(value)


def _identifier(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("logical_id", item.get("id"))
    else:
        value = getattr(item, "logical_id", getattr(item, "id", None))
    return str(value) if value is not None else None


def _requirements_spaces(requirements: Any) -> list[Any]:
    if isinstance(requirements, ProgramRequirementSet):
        return [space for sector in requirements.sectors for space in sector.spaces]
    if hasattr(requirements, "sectors"):
        sectors = requirements.sectors
    elif isinstance(requirements, Mapping):
        sectors = requirements.get("sectors", [])
    else:
        return []
    spaces: list[Any] = []
    for sector in sectors or []:
        if isinstance(sector, Mapping):
            spaces.extend(sector.get("spaces", []))
        else:
            spaces.extend(getattr(sector, "spaces", []))
    return spaces


def _requirement_value(requirement: Any, key: str, default: Any = None) -> Any:
    if isinstance(requirement, Mapping):
        return requirement.get(key, default)
    return getattr(requirement, key, default)


def _relations(candidate: Mapping[str, Any], requirements: Any) -> list[Any]:
    values = candidate.get("relations")
    if values is None:
        values = getattr(requirements, "relations", None)
    if values is None and isinstance(requirements, Mapping):
        values = requirements.get("relations")
    return list(values or [])


def _relation_value(relation: Any, key: str) -> Any:
    if isinstance(relation, Mapping):
        return relation.get(key)
    return getattr(relation, key, None)


def _relation_type(relation: Any) -> RelationType | None:
    value = _relation_value(relation, "relation")
    try:
        return RelationType(value)
    except (TypeError, ValueError):
        return None


def _site_polygon(site: Any) -> Any:
    if isinstance(site, Mapping):
        buildable = site.get("buildable_area")
        if isinstance(buildable, Mapping):
            for key in ("geometry", "polygon", "coordinates"):
                if key in buildable:
                    return buildable[key]
        if buildable is not None and not isinstance(buildable, (int, float)):
            return buildable
        boundary = site.get("boundary")
        if isinstance(boundary, Mapping):
            return boundary.get("coordinates", boundary)
        return boundary or site
    boundary = getattr(site, "boundary", None)
    if boundary is not None:
        return getattr(boundary, "coordinates", boundary)
    return site


def _resolution(candidate: Mapping[str, Any]) -> ConstraintResolution:
    value = candidate.get("resolution")
    if value is not None:
        return ConstraintResolution(str(value))
    if candidate.get("rooms") is not None:
        return ConstraintResolution.ROOM
    if candidate.get("blocks") is not None:
        return ConstraintResolution.BLOCK
    return ConstraintResolution.MACRO


def _violation(
    code: str,
    message: str,
    resolution: ConstraintResolution,
    *,
    expected: Any = None,
    actual: Any = None,
    status: ConstraintStatus = ConstraintStatus.VIOLATION,
    severity: ViolationSeverity = ViolationSeverity.HARD,
) -> ConstraintViolation:
    return ConstraintViolation(
        code=code,
        message=message,
        resolution=resolution.value,
        expected=expected,
        actual=actual,
        status=status,
        severity=severity,
    )


def _not_evaluated(code: str, resolution: ConstraintResolution, message: str) -> ConstraintViolation:
    return _violation(
        code,
        message,
        resolution,
        status=ConstraintStatus.NOT_EVALUATED,
        severity=ViolationSeverity.INFO,
    )


def _geometry_map(items: Iterable[Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in items:
        identifier = _identifier(item)
        if identifier is not None:
            result[identifier] = _item_geometry(item)
    return result


def _check_boundary(
    items: list[Any], site_polygon: Any, resolution: ConstraintResolution
) -> list[ConstraintViolation]:
    results: list[ConstraintViolation] = []
    for item in items:
        identifier = _identifier(item) or "<anonymous>"
        try:
            if not contains(site_polygon, _item_geometry(item)):
                results.append(
                    _violation(
                        "outside_buildable_site",
                        f"{identifier} is outside the buildable site",
                        resolution,
                        expected="contained by site",
                        actual=identifier,
                    )
                )
        except InvalidDesignGeometryError as exc:
            results.append(
                _violation(
                    "invalid_geometry",
                    f"{identifier} has invalid geometry: {exc}",
                    resolution,
                )
            )
    return results


def _check_overlaps(
    items: list[Any], resolution: ConstraintResolution
) -> list[ConstraintViolation]:
    results: list[ConstraintViolation] = []
    for index, first in enumerate(items):
        for second in items[index + 1 :]:
            first_id = _identifier(first) or f"item-{index}"
            second_id = _identifier(second) or "item"
            try:
                has_overlap = overlaps(_item_geometry(first), _item_geometry(second))
            except InvalidDesignGeometryError:
                continue
            if has_overlap:
                results.append(
                    _violation(
                        "room_overlap" if resolution is ConstraintResolution.ROOM else "geometry_overlap",
                        f"{first_id} overlaps {second_id}",
                        resolution,
                        actual=(first_id, second_id),
                    )
                )
    return results


def _matches(identifier: str | None, required_id: str) -> bool:
    if identifier is None:
        return False
    return identifier == required_id or any(
        identifier.startswith(required_id + suffix)
        for suffix in ("#", "-", "__")
    )


def _check_required_rooms(
    rooms: list[Any], requirements: Any, resolution: ConstraintResolution
) -> list[ConstraintViolation]:
    if resolution is not ConstraintResolution.ROOM:
        return [
            _not_evaluated(
                "required_rooms",
                resolution,
                "expanded room instances are unavailable at this resolution",
            )
        ]
    results: list[ConstraintViolation] = []
    identifiers = [_identifier(room) for room in rooms]
    for requirement in _requirements_spaces(requirements):
        required_id = str(_requirement_value(requirement, "logical_id", ""))
        quantity = int(_requirement_value(requirement, "quantity", 1) or 1)
        count = sum(_matches(identifier, required_id) for identifier in identifiers)
        if count < quantity:
            results.append(
                _violation(
                    "required_room_missing",
                    f"required room {required_id} is missing",
                    resolution,
                    expected=quantity,
                    actual=count,
                )
            )
    return results


def _check_accessible_rooms(
    rooms: list[Any], requirements: Any, resolution: ConstraintResolution
) -> list[ConstraintViolation]:
    if resolution is not ConstraintResolution.ROOM:
        return [
            _not_evaluated(
                "accessible_rooms",
                resolution,
                "expanded accessible rooms are unavailable at this resolution",
            )
        ]
    results: list[ConstraintViolation] = []
    for requirement in _requirements_spaces(requirements):
        if _requirement_value(requirement, "accessible") is not True:
            continue
        required_id = str(_requirement_value(requirement, "logical_id", ""))
        matches = [
            room
            for room in rooms
            if _matches(_identifier(room), required_id)
        ]
        if not any(
            bool(room.get("accessible"))
            if isinstance(room, Mapping)
            else bool(getattr(room, "accessible", False))
            for room in matches
        ):
            results.append(
                _violation(
                    "accessible_room_missing",
                    f"required accessible room {required_id} is missing",
                    resolution,
                    actual=required_id,
                )
            )
    return results


def _check_area_ranges(
    rooms: list[Any], requirements: Any, resolution: ConstraintResolution
) -> list[ConstraintViolation]:
    results: list[ConstraintViolation] = []
    requirement_by_id = {
        str(_requirement_value(item, "logical_id", "")): item
        for item in _requirements_spaces(requirements)
    }
    for room in rooms:
        requirement = requirement_by_id.get(_identifier(room) or "")
        if requirement is None:
            continue
        minimum = _requirement_value(requirement, "min_area_m2")
        maximum = _requirement_value(requirement, "max_area_m2")
        if minimum is None and maximum is None:
            continue
        actual = (
            room.get("net_area_m2")
            if isinstance(room, Mapping)
            else getattr(room, "net_area_m2", None)
        )
        if actual is None:
            try:
                actual = validate_polygon(_item_geometry(room)).area
            except (AttributeError, InvalidDesignGeometryError):
                continue
        if minimum is not None and actual < minimum:
            results.append(
                _violation(
                    "room_area_below_minimum",
                    f"{_identifier(room)} is below its minimum net area",
                    resolution,
                    expected=minimum,
                    actual=actual,
                )
            )
        if maximum is not None and actual > maximum:
            results.append(
                _violation(
                    "room_area_above_maximum",
                    f"{_identifier(room)} exceeds its maximum net area",
                    resolution,
                    expected=maximum,
                    actual=actual,
                )
            )
    return results


def _check_separation(
    items: list[Any], relations: list[Any], resolution: ConstraintResolution
) -> list[ConstraintViolation]:
    geometries = _geometry_map(items)
    results: list[ConstraintViolation] = []
    for relation in relations:
        if _relation_type(relation) is not RelationType.MUST_BE_SEPARATED:
            continue
        source = str(_relation_value(relation, "source_logical_id"))
        target = str(_relation_value(relation, "target_logical_id"))
        if source not in geometries or target not in geometries:
            results.append(
                _not_evaluated(
                    "must_be_separated",
                    resolution,
                    f"separation geometry unavailable for {source} and {target}",
                )
            )
            continue
        if overlaps(geometries[source], geometries[target]) or minimum_distance(
            geometries[source], geometries[target]
        ) <= 0.01:
            results.append(
                _violation(
                    "must_be_separated",
                    f"{source} and {target} violate MUST_BE_SEPARATED",
                    resolution,
                    actual=(source, target),
                )
            )
    return results


def _check_sector_capacity(
    sectors: list[Any], requirements: Any, site: Any, resolution: ConstraintResolution
) -> list[ConstraintViolation]:
    del site
    required_by_id: dict[str, float] = {}
    requirement_sectors = (
        requirements.get("sectors", [])
        if isinstance(requirements, Mapping)
        else getattr(requirements, "sectors", [])
    )
    for requirement_sector in requirement_sectors or []:
        sector_id = str(_requirement_value(requirement_sector, "logical_id", ""))
        if not sector_id:
            continue
        required_by_id[sector_id] = sum(
            float(_requirement_value(space, "target_area_m2", 0) or 0)
            * int(_requirement_value(space, "quantity", 1) or 1)
            for space in (_requirement_value(requirement_sector, "spaces", []) or [])
        )
    results: list[ConstraintViolation] = []
    for sector_id, required_area in required_by_id.items():
        matches = [item for item in sectors if _identifier(item) == sector_id]
        if not matches:
            results.append(
                _violation(
                    "sector_missing",
                    f"required sector {sector_id} is missing",
                    resolution,
                    actual=0,
                    expected=required_area,
                )
            )
            continue
        actual_area = sum(
            float(validate_polygon(_item_geometry(item)).area) for item in matches
        )
        if actual_area + 0.000001 < required_area:
            results.append(
                _violation(
                    "sector_capacity",
                    f"sector {sector_id} is below its required capacity",
                    resolution,
                    expected=required_area,
                    actual=actual_area,
                )
            )
    return results


def _check_gross_area(
    blocks: list[Any], candidate: Mapping[str, Any], resolution: ConstraintResolution
) -> list[ConstraintViolation]:
    budget = candidate.get("gross_area_budget_m2", candidate.get("gross_area_budget"))
    if budget is None:
        return [
            _not_evaluated(
                "gross_area_budget",
                resolution,
                "gross-area budget is unavailable at this resolution",
            )
        ]
    actual = candidate.get("gross_area_m2")
    if actual is None:
        actual = sum(float(_item_geometry(item).area) for item in blocks)
    if float(actual) > float(budget) + 0.000001:
        return [
            _violation(
                "gross_area_budget",
                "block gross area exceeds the configured budget",
                resolution,
                expected=budget,
                actual=actual,
            )
        ]
    return []


def validate_candidate(
    candidate: Any, requirements: Any, site: Any
) -> list[ConstraintViolation]:
    """Validate only checks available at the candidate's progressive resolution."""

    values = _as_mapping(candidate)
    resolution = _resolution(values)
    if resolution is ConstraintResolution.MACRO:
        items = _items(values, "sectors") or _items(values, "macrozones")
    elif resolution is ConstraintResolution.BLOCK:
        items = _items(values, "blocks")
    else:
        items = _items(values, "rooms")
    try:
        site_polygon = _site_polygon(site)
        results = _check_boundary(items, site_polygon, resolution)
    except (InvalidDesignGeometryError, TypeError, ValueError) as exc:
        return [
            _violation(
                "invalid_site_geometry",
                f"site geometry cannot be evaluated: {exc}",
                resolution,
            )
        ]
    results.extend(_check_overlaps(items, resolution))
    relations = _relations(values, requirements)
    results.extend(_check_separation(items, relations, resolution))

    if resolution is ConstraintResolution.MACRO:
        results.extend(_check_sector_capacity(items, requirements, site, resolution))
        results.append(
            _not_evaluated(
                "required_rooms",
                resolution,
                "expanded room instances are unavailable at this resolution",
            )
        )
        results.append(
            _not_evaluated(
                "accessible_rooms",
                resolution,
                "expanded accessible rooms are unavailable at this resolution",
            )
        )
    elif resolution is ConstraintResolution.BLOCK:
        results.extend(_check_gross_area(items, values, resolution))
        results.extend(_check_required_rooms(items, requirements, resolution))
        results.extend(_check_accessible_rooms(items, requirements, resolution))
    else:
        results.extend(_check_required_rooms(items, requirements, resolution))
        results.extend(_check_accessible_rooms(items, requirements, resolution))
        results.extend(_check_area_ranges(items, requirements, resolution))
    return results


def hard_violations_only(
    violations: Iterable[ConstraintViolation],
) -> list[ConstraintViolation]:
    """Return actual hard failures, excluding unavailable checks."""

    return [violation for violation in violations if violation.is_hard_violation]


def soft_penalties_from_violations(
    violations: Iterable[ConstraintViolation],
) -> dict[str, float]:
    """Convert only explicit soft violations into numeric penalties."""

    penalties: dict[str, float] = {}
    for violation in violations:
        if violation.is_hard_violation:
            raise ValueError(
                "hard constraint violations cannot become a soft penalty"
            )
        if violation.status is ConstraintStatus.NOT_EVALUATED:
            continue
        if violation.severity is ViolationSeverity.SOFT:
            penalties[violation.code] = violation.as_soft_penalty()
    return penalties


__all__ = [
    "ConstraintResolution",
    "hard_violations_only",
    "soft_penalties_from_violations",
    "validate_candidate",
]
