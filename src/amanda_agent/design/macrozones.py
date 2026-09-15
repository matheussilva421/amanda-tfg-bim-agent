"""Deterministic CP-SAT assignment of program sectors to site regions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from math import ceil, isfinite
from typing import Any

from ortools.sat.python import cp_model  # type: ignore[import-untyped]
from shapely.geometry import (  # type: ignore[import-untyped]
    Polygon,
    box,
    mapping,
    shape,
)

from amanda_agent.requirements.relations import RelationType

from .geometry import validate_polygon


@dataclass(frozen=True)
class MacrozoneResult:
    """Solver output with CP-SAT and Shapely evidence kept separate."""

    status: str
    assignment: dict[str, str] = field(default_factory=dict)
    assignment_order: list[str] = field(default_factory=list)
    sectors: list[dict[str, Any]] = field(default_factory=list)
    solver_status: str = "UNKNOWN"
    solver_seed: int = 0
    grid_scale_m: float = 1.0
    rounding_tolerance_m: float = 0.5
    grid_coordinates: dict[str, tuple[int, int]] = field(default_factory=dict)
    geometry_valid: bool | None = None
    geometry_hash: str | None = None
    infeasibility_evidence: list[str] = field(default_factory=list)
    solver_evidence: list[str] = field(default_factory=list)
    geometry_evidence: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status in {"OPTIMAL", "FEASIBLE"} and self.geometry_valid is True


def _polygon(value: Any) -> Polygon:
    if isinstance(value, Polygon):
        return validate_polygon(value)
    if isinstance(value, dict):
        return validate_polygon(shape(value))
    return validate_polygon(value)


def _site_polygon(site: Any) -> Polygon:
    if isinstance(site, dict):
        value = site.get("buildable_area", site.get("boundary", site))
        if isinstance(value, dict):
            value = value.get("geometry", value.get("polygon", value.get("coordinates", value)))
        return _polygon(value)
    return _polygon(site)


def _items(requirements: Any, key: str) -> list[Any]:
    if isinstance(requirements, dict):
        values = requirements.get(key, [])
    else:
        values = getattr(requirements, key, [])
    return list(values or [])


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _sector_demand(sector: Any) -> float:
    direct = _value(sector, "demand_m2", _value(sector, "capacity_m2"))
    if direct is not None:
        return float(direct)
    return sum(
        float(_value(space, "target_area_m2", 0) or 0)
        * int(_value(space, "quantity", 1) or 1)
        for space in (_value(sector, "spaces", []) or [])
    )


def _relation_value(relation: Any, key: str, default: Any = None) -> Any:
    if isinstance(relation, dict):
        return relation.get(key, default)
    return getattr(relation, key, default)


def _relations(requirements: Any) -> list[Any]:
    if isinstance(requirements, dict):
        return list(requirements.get("relations", []) or [])
    return list(getattr(requirements, "relations", []) or [])


def _make_regions(site: Polygon, count: int, *, axis: int) -> list[dict[str, Any]]:
    min_x, min_y, max_x, max_y = site.bounds
    regions: list[dict[str, Any]] = []
    for index in range(count):
        start = index / count
        end = (index + 1) / count
        if axis == 0:
            candidate = box(min_x + (max_x - min_x) * start, min_y, min_x + (max_x - min_x) * end, max_y)
        else:
            candidate = box(min_x, min_y + (max_y - min_y) * start, max_x, min_y + (max_y - min_y) * end)
        clipped = site.intersection(candidate)
        if clipped.geom_type == "MultiPolygon":
            clipped = max(clipped.geoms, key=lambda item: item.area)
        regions.append({"logical_id": f"region-{index + 1}", "geometry": validate_polygon(clipped)})
    return regions


def _normalise_regions(site: Polygon, regions: list[Any] | None, count: int, seed: int) -> list[dict[str, Any]]:
    if regions is None:
        return _make_regions(site, count, axis=seed % 2)
    result: list[dict[str, Any]] = []
    for index, item in enumerate(regions):
        geometry = _value(item, "geometry", _value(item, "polygon", item))
        result.append({
            "logical_id": str(_value(item, "logical_id", _value(item, "id", f"region-{index + 1}"))),
            "geometry": _polygon(geometry),
            "capacity_m2": float(_value(item, "capacity_m2", _polygon(geometry).area)),
        })
    return result


def _relation_allowed(left: Polygon, right: Polygon, relation: RelationType, tolerance_m: float) -> bool:
    if relation is RelationType.MUST_ADJOIN:
        return left.touches(right) and left.distance(right) <= tolerance_m
    if relation is RelationType.MUST_BE_SEPARATED:
        return not left.intersects(right) and left.distance(right) > tolerance_m
    return True


def _canonical_hash(sectors: list[dict[str, Any]]) -> str:
    def convert(value: Any) -> Any:
        if hasattr(value, "__geo_interface__"):
            return convert(mapping(value))
        if isinstance(value, dict):
            return {str(key): convert(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
        if isinstance(value, (list, tuple)):
            return [convert(item) for item in value]
        if isinstance(value, float):
            return round(value, 6)
        return value

    encoded = json.dumps(convert(sectors), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def solve_macrozones(
    requirements: Any,
    site: Any,
    *,
    seed: int,
    regions: list[Any] | None = None,
    region_count: int | None = None,
    separation_tolerance_m: float = 0.01,
    grid_resolution_m: float = 1.0,
    time_limit_s: float = 10.0,
) -> MacrozoneResult:
    """Assign each sector to one bounded region and revalidate its polygons."""

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("solver seed must be an integer")
    if not isfinite(time_limit_s) or time_limit_s <= 0:
        raise ValueError("time_limit_s must be finite and positive")
    if not isfinite(grid_resolution_m) or grid_resolution_m <= 0:
        raise ValueError("grid_resolution_m must be finite and positive")
    site_polygon = _site_polygon(site)
    sector_items = _items(requirements, "sectors")
    sector_items = sorted(sector_items, key=lambda item: str(_value(item, "logical_id", "")))
    if not sector_items:
        return MacrozoneResult(
            status="INFEASIBLE",
            solver_status="INFEASIBLE",
            solver_seed=seed,
            grid_scale_m=grid_resolution_m,
            rounding_tolerance_m=grid_resolution_m / 2,
            infeasibility_evidence=["no program sectors were supplied"],
        )
    count = len(regions) if regions is not None else int(region_count or len(sector_items))
    if count < len(sector_items):
        return MacrozoneResult(
            status="INFEASIBLE",
            solver_status="INFEASIBLE",
            solver_seed=seed,
            grid_scale_m=grid_resolution_m,
            rounding_tolerance_m=grid_resolution_m / 2,
            infeasibility_evidence=["fewer candidate regions than required sectors"],
        )
    region_items = _normalise_regions(site_polygon, regions, count, seed)
    model: Any = cp_model.CpModel()
    variables: dict[tuple[int, int], Any] = {}
    min_x, min_y, _, _ = site_polygon.bounds
    grid_width = max(1, ceil((site_polygon.bounds[2] - min_x) / grid_resolution_m))
    grid_height = max(1, ceil((site_polygon.bounds[3] - min_y) / grid_resolution_m))
    grid_x = {index: model.NewIntVar(0, grid_width, f"sector_{index}_grid_x") for index in range(len(sector_items))}
    grid_y = {index: model.NewIntVar(0, grid_height, f"sector_{index}_grid_y") for index in range(len(sector_items))}
    for sector_index, sector in enumerate(sector_items):
        demand = _sector_demand(sector)
        for region_index, region in enumerate(region_items):
            variable = model.NewBoolVar(f"sector_{sector_index}_region_{region_index}")
            variables[(sector_index, region_index)] = variable
            if demand > float(region.get("capacity_m2", region["geometry"].area)) + 1e-6:
                model.Add(variable == 0)
            centroid = region["geometry"].centroid
            model.Add(grid_x[sector_index] == round((centroid.x - min_x) / grid_resolution_m)).OnlyEnforceIf(variable)
            model.Add(grid_y[sector_index] == round((centroid.y - min_y) / grid_resolution_m)).OnlyEnforceIf(variable)
        model.Add(sum(variables[(sector_index, index)] for index in range(len(region_items))) == 1)
    for region_index in range(len(region_items)):
        model.Add(sum(variables[(sector_index, region_index)] for sector_index in range(len(sector_items))) <= 1)
    for relation in _relations(requirements):
        relation_type = RelationType(_relation_value(relation, "relation"))
        if relation_type not in {RelationType.MUST_ADJOIN, RelationType.MUST_BE_SEPARATED}:
            continue
        source = str(_relation_value(relation, "source_logical_id"))
        target = str(_relation_value(relation, "target_logical_id"))
        source_index = next((i for i, item in enumerate(sector_items) if str(_value(item, "logical_id")) == source), None)
        target_index = next((i for i, item in enumerate(sector_items) if str(_value(item, "logical_id")) == target), None)
        if source_index is None or target_index is None:
            continue
        for left_index, left in enumerate(region_items):
            for right_index, right in enumerate(region_items):
                if not _relation_allowed(left["geometry"], right["geometry"], relation_type, separation_tolerance_m):
                    model.AddBoolOr([variables[(source_index, left_index)].Not(), variables[(target_index, right_index)].Not()])
    solver: Any = cp_model.CpSolver()
    solver.parameters.random_seed = seed
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.search_branching = cp_model.FIXED_SEARCH
    outcome = solver.Solve(model)
    status_name = solver.StatusName(outcome)
    if outcome not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if outcome == cp_model.UNKNOWN:
            return MacrozoneResult(
                status="UNKNOWN",
                solver_status=status_name,
                solver_seed=seed,
                grid_scale_m=grid_resolution_m,
                rounding_tolerance_m=grid_resolution_m / 2,
                solver_evidence=["wall-clock search timeout is UNKNOWN, not proof of infeasibility"],
            )
        return MacrozoneResult(
            status="INFEASIBLE" if outcome == cp_model.INFEASIBLE else status_name,
            solver_status=status_name,
            solver_seed=seed,
            grid_scale_m=grid_resolution_m,
            rounding_tolerance_m=grid_resolution_m / 2,
            infeasibility_evidence=[
                f"CP-SAT status={status_name}",
                "capacity, assignment, and mandatory relation constraints had no accepted solution",
            ],
            solver_evidence=["infeasibility reported by CP-SAT witness"],
        )
    assignment: dict[str, str] = {}
    selected: list[dict[str, Any]] = []
    grid_coordinates: dict[str, tuple[int, int]] = {}
    for sector_index, sector in enumerate(sector_items):
        sector_id = str(_value(sector, "logical_id"))
        region_index = next(index for index in range(len(region_items)) if solver.BooleanValue(variables[(sector_index, index)]))
        region = region_items[region_index]
        assignment[sector_id] = str(region["logical_id"])
        grid_coordinates[sector_id] = (solver.Value(grid_x[sector_index]), solver.Value(grid_y[sector_index]))
        selected.append({
            "logical_id": sector_id,
            "region_id": str(region["logical_id"]),
            "geometry": region["geometry"],
            "demand_m2": _sector_demand(sector),
        })
    selected.sort(key=lambda item: item["logical_id"])
    valid = all(site_polygon.covers(item["geometry"]) for item in selected)
    geometry_evidence = ["assigned regions revalidated with Shapely"]
    if not valid:
        geometry_evidence.append("a CP-SAT-feasible assignment was outside the buildable polygon")
        return MacrozoneResult(
            status="INFEASIBLE",
            assignment=assignment,
            assignment_order=[item["logical_id"] for item in selected],
            sectors=selected,
            solver_status=status_name,
            solver_seed=seed,
            grid_scale_m=grid_resolution_m,
            rounding_tolerance_m=grid_resolution_m / 2,
            grid_coordinates=grid_coordinates,
            geometry_valid=False,
            geometry_hash=_canonical_hash(selected),
            geometry_evidence=geometry_evidence,
            infeasibility_evidence=["Shapely geometric revalidation rejected the grid assignment"],
        )
    return MacrozoneResult(
        status=status_name,
        assignment=assignment,
        assignment_order=[item["logical_id"] for item in selected],
        sectors=selected,
        solver_status=status_name,
        solver_seed=seed,
        grid_scale_m=grid_resolution_m,
        rounding_tolerance_m=grid_resolution_m / 2,
        grid_coordinates=grid_coordinates,
        geometry_valid=True,
        geometry_hash=_canonical_hash(selected),
        geometry_evidence=geometry_evidence,
    )


solve_macrozone = solve_macrozones
assign_macrozones = solve_macrozones


__all__ = ["MacrozoneResult", "assign_macrozones", "solve_macrozone", "solve_macrozones"]
