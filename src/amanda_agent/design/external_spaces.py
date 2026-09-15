"""External program geometry with explicit privacy and relation checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite, sqrt
from typing import Any

from shapely.geometry import Polygon, box, shape  # type: ignore[import-untyped]

from .geometry import InvalidDesignGeometryError, validate_polygon


@dataclass(frozen=True)
class ExternalSpaceViolation:
    code: str
    message: str
    logical_id: str | None = None


@dataclass(frozen=True)
class ExternalSpaceValidation:
    violations: list[ExternalSpaceViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations


@dataclass(frozen=True)
class ExternalSpaceGenerationResult:
    spaces: list[dict[str, Any]] = field(default_factory=list)
    violations: list[ExternalSpaceViolation] = field(default_factory=list)
    used_leftover_as_garden: bool = False

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


def _rectangle(site: Polygon, target: float, x: float, y: float) -> Polygon | None:
    min_x, min_y, max_x, max_y = site.bounds
    site_width = max_x - min_x
    site_height = max_y - min_y
    if target <= 0 or target > site.area:
        return None
    width = min(site_width, sqrt(target))
    height = target / width
    if height > site_height:
        height = site_height
        width = target / height
    if x + width > max_x + 1e-9:
        return None
    candidate = box(x, y, x + width, y + height)
    return candidate if site.covers(candidate) else None


def validate_external_spaces(
    spaces: list[Any],
    site: Any,
    *,
    area_tolerance_percent: float = 1.0,
    privacy_policy: dict[str, Any] | None = None,
    related_geometries: dict[str, Any] | None = None,
) -> ExternalSpaceValidation:
    site_polygon = _polygon(site)
    policy = privacy_policy or {}
    related = related_geometries or {}
    violations: list[ExternalSpaceViolation] = []
    seen: set[str] = set()
    geometries: list[tuple[str, Polygon, Any]] = []
    for item in spaces:
        identifier = str(_value(item, "logical_id", _value(item, "id", "")))
        if identifier in seen:
            violations.append(ExternalSpaceViolation("duplicate_external_id", f"external space {identifier} appears more than once", identifier))
        seen.add(identifier)
        try:
            geometry = _polygon(_value(item, "geometry", item))
        except (InvalidDesignGeometryError, TypeError, ValueError) as exc:
            violations.append(ExternalSpaceViolation("invalid_geometry", str(exc), identifier))
            continue
        geometries.append((identifier, geometry, item))
        if not site_polygon.covers(geometry):
            violations.append(ExternalSpaceViolation("outside_site", f"external space {identifier} is outside site", identifier))
        target = _value(item, "target_area_m2")
        if target is not None and abs(geometry.area - float(target)) / float(target) * 100 > area_tolerance_percent + 1e-9:
            violations.append(ExternalSpaceViolation("area_mismatch", f"external space {identifier} misses its area target", identifier))
        kind = str(_value(item, "kind", ""))
        privacy = _value(item, "privacy_level")
        minimum = float(policy.get("protected_min_privacy_level", 0))
        if kind in {"therapeutic_garden", "protected_courtyard", "protected"} and privacy is not None and float(privacy) < minimum:
            violations.append(ExternalSpaceViolation("external_privacy", f"protected external space {identifier} is below privacy policy", identifier))
        relation_id = _value(item, "child_relation")
        if kind == "playground" and relation_id is not None and str(relation_id) in related:
            related_geometry = _polygon(related[str(relation_id)])
            if geometry.distance(related_geometry) > float(policy.get("child_relation_max_distance_m", 10.0)):
                violations.append(ExternalSpaceViolation("playground_child_relation", f"playground {identifier} is too far from {relation_id}", identifier))
    for index, (_, first, _) in enumerate(geometries):
        for second_id, second, _ in geometries[index + 1 :]:
            if first.intersection(second).area > 1e-6:
                violations.append(ExternalSpaceViolation("external_overlap", f"external spaces overlap {second_id}"))
    return ExternalSpaceValidation(violations=violations)


def generate_external_spaces(
    site: Any,
    requirements: list[Any],
    *,
    area_tolerance_percent: float = 1.0,
    privacy_policy: dict[str, Any] | None = None,
) -> ExternalSpaceGenerationResult:
    """Materialize each requested garden/play area; residual land is unnamed."""

    if not isfinite(area_tolerance_percent) or area_tolerance_percent < 0:
        raise ValueError("area_tolerance_percent must be finite and non-negative")
    site_polygon = _polygon(site)
    spaces: list[dict[str, Any]] = []
    violations: list[ExternalSpaceViolation] = []
    seen: set[str] = set()
    cursor_x, cursor_y, row_height = site_polygon.bounds[0], site_polygon.bounds[1], 0.0
    for index, requirement in enumerate(requirements):
        identifier = str(_value(requirement, "logical_id", _value(requirement, "id", "")))
        target = float(_value(requirement, "target_area_m2", _value(requirement, "area_m2", 0)))
        if identifier in seen:
            violations.append(ExternalSpaceViolation("duplicate_external_id", f"external space {identifier} appears more than once", identifier))
            continue
        seen.add(identifier)
        min_x, _, max_x, _ = site_polygon.bounds
        width = min(max_x - min_x, sqrt(target))
        height = target / width if width else 0.0
        if cursor_x + width > max_x + 1e-9:
            cursor_x = min_x
            cursor_y += row_height
            row_height = 0.0
        geometry = _rectangle(site_polygon, target, cursor_x, cursor_y)
        if geometry is None:
            violations.append(ExternalSpaceViolation("external_capacity", f"cannot place external space {identifier}", identifier))
            continue
        cursor_x += width
        row_height = max(row_height, height)
        spaces.append({
            "logical_id": identifier,
            "geometry": geometry,
            "target_area_m2": target,
            "kind": _value(requirement, "kind", "external_program"),
            "privacy_level": _value(requirement, "privacy_level"),
            "child_relation": _value(requirement, "child_relation"),
        })
    validation = validate_external_spaces(spaces, site_polygon, area_tolerance_percent=area_tolerance_percent, privacy_policy=privacy_policy)
    violations.extend(validation.violations)
    return ExternalSpaceGenerationResult(spaces=spaces, violations=violations)


generate_external_space_geometry = generate_external_spaces


__all__ = ["ExternalSpaceGenerationResult", "ExternalSpaceValidation", "ExternalSpaceViolation", "generate_external_space_geometry", "generate_external_spaces", "validate_external_spaces"]
