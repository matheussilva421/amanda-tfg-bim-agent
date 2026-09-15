"""Shapely-backed block polygons derived from macrozone demands."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite, sqrt
from typing import Any

from shapely import affinity  # type: ignore[import-untyped]
from shapely.geometry import Polygon, box, shape  # type: ignore[import-untyped]

from .geometry import InvalidDesignGeometryError, validate_polygon


@dataclass(frozen=True)
class BlockViolation:
    code: str
    message: str
    sector_id: str | None = None
    actual: float | None = None
    expected: float | None = None


@dataclass(frozen=True)
class BlockGenerationResult:
    blocks: list[dict[str, Any]] = field(default_factory=list)
    violations: list[BlockViolation] = field(default_factory=list)
    area_tolerance_percent: float = 1.0

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


def _demand(item: Any) -> float:
    direct = _value(item, "demand_m2", _value(item, "capacity_m2"))
    if direct is not None:
        return float(direct)
    return sum(float(_value(space, "target_area_m2", 0) or 0) * int(_value(space, "quantity", 1) or 1) for space in (_value(item, "spaces", []) or []))


def _fit_rectangle(zone: Polygon, target_area: float, min_width_m: float) -> Polygon | None:
    min_x, min_y, max_x, max_y = zone.bounds
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0 or target_area <= 0:
        return None
    ratio = sqrt(target_area / (width * height))
    candidate = affinity.scale(box(min_x, min_y, max_x, max_y), xfact=ratio, yfact=ratio, origin="center")
    if candidate.bounds[2] - candidate.bounds[0] < min_width_m or candidate.bounds[3] - candidate.bounds[1] < min_width_m:
        return None
    if zone.covers(candidate):
        return candidate
    # A rotated or irregular zone gets a conservative Shapely shrink and is
    # accepted only if the resulting polygon still has the requested area.
    safe = zone.buffer(-min_width_m / 2)
    if safe.is_empty:
        return None
    bounds = safe.bounds
    safe_box = box(*bounds)
    scale = sqrt(target_area / safe_box.area)
    fallback = affinity.scale(safe_box, xfact=scale, yfact=scale, origin="center")
    return fallback if safe.covers(fallback) and zone.covers(fallback) else None


def _split_zones(zone: Polygon, count: int) -> list[Polygon]:
    min_x, min_y, max_x, max_y = zone.bounds
    if max_x - min_x >= max_y - min_y:
        candidates = [box(min_x + (max_x - min_x) * index / count, min_y, min_x + (max_x - min_x) * (index + 1) / count, max_y) for index in range(count)]
    else:
        candidates = [box(min_x, min_y + (max_y - min_y) * index / count, max_x, min_y + (max_y - min_y) * (index + 1) / count) for index in range(count)]
    return [zone.intersection(candidate) for candidate in candidates]


def generate_blocks(
    sectors: list[Any],
    *,
    area_tolerance_percent: float = 1.0,
    min_width_m: float = 1.0,
    allow_sector_splitting: bool = False,
    split_count: int | None = None,
) -> BlockGenerationResult:
    """Generate non-overlapping blocks, rejecting capacity and sliver errors."""

    if not isfinite(area_tolerance_percent) or area_tolerance_percent < 0:
        raise ValueError("area_tolerance_percent must be finite and non-negative")
    if not isfinite(min_width_m) or min_width_m <= 0:
        raise ValueError("min_width_m must be finite and positive")
    blocks: list[dict[str, Any]] = []
    violations: list[BlockViolation] = []
    for sector in sectors:
        sector_id = str(_value(sector, "logical_id", _value(sector, "id", "sector")))
        try:
            zone = _polygon(_value(sector, "geometry", _value(sector, "polygon", sector)))
        except (InvalidDesignGeometryError, TypeError, ValueError) as exc:
            violations.append(BlockViolation("invalid_geometry", str(exc), sector_id))
            continue
        demand = _demand(sector)
        if demand > zone.area + 1e-6:
            violations.append(BlockViolation("sector_capacity", f"{sector_id} demand exceeds macrozone area", sector_id, zone.area, demand))
            continue
        count = int(split_count or 1) if allow_sector_splitting else 1
        if count < 1:
            raise ValueError("split_count must be positive")
        zones = _split_zones(zone, count) if count > 1 else [zone]
        for index, subzone in enumerate(zones):
            target = demand / count
            geometry = _fit_rectangle(subzone, target, min_width_m)
            if geometry is None:
                violations.append(BlockViolation("sliver_polygon", f"{sector_id} cannot meet minimum block width", sector_id, target, min_width_m))
                break
            area_delta = abs(geometry.area - target) / target * 100
            if area_delta > area_tolerance_percent + 1e-9:
                violations.append(BlockViolation("area_mismatch", f"{sector_id} block area is outside tolerance", sector_id, geometry.area, target))
                break
            blocks.append({
                "logical_id": f"{sector_id}-block-{index + 1}",
                "sector_id": sector_id,
                "geometry": geometry,
                "area_m2": float(geometry.area),
                "demand_m2": target,
            })
    for index, first in enumerate(blocks):
        for second in blocks[index + 1 :]:
            if first["geometry"].intersection(second["geometry"]).area > 1e-6:
                violations.append(BlockViolation("geometry_overlap", f"{first['logical_id']} overlaps {second['logical_id']}"))
    return BlockGenerationResult(blocks=blocks, violations=violations, area_tolerance_percent=area_tolerance_percent)


generate_block_polygons = generate_blocks


__all__ = ["BlockGenerationResult", "BlockViolation", "generate_block_polygons", "generate_blocks"]
