"""Stable non-dominated filtering for multidimensional alternatives."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast


def _metrics(candidate: Any, dimensions: Sequence[str]) -> dict[str, float | None]:
    if hasattr(candidate, "normalized_metrics"):
        values = candidate.normalized_metrics
    elif isinstance(candidate, dict):
        values = candidate.get("metrics", candidate)
    else:
        values = getattr(candidate, "metrics", {})
    return {dimension: None if values.get(dimension) is None else float(values[dimension]) for dimension in dimensions}


def dominates(first: Any, second: Any, *, dimensions: Sequence[str], directions: dict[str, str] | None = None) -> bool:
    directions = directions or {}
    left = _metrics(first, dimensions)
    right = _metrics(second, dimensions)
    if any(left[name] is None or right[name] is None for name in dimensions):
        return False
    left_values = [cast(float, left[name]) for name in dimensions]
    right_values = [cast(float, right[name]) for name in dimensions]
    transformed_left = [value if directions.get(name, "higher") == "higher" else -value for name, value in zip(dimensions, left_values)]
    transformed_right = [value if directions.get(name, "higher") == "higher" else -value for name, value in zip(dimensions, right_values)]
    return all(a >= b for a, b in zip(transformed_left, transformed_right)) and any(a > b for a, b in zip(transformed_left, transformed_right))


def pareto_frontier(candidates: Sequence[Any], *, dimensions: Sequence[str] | None = None, directions: dict[str, str] | None = None) -> list[Any]:
    """Return input-order candidates that no other candidate strictly dominates."""

    if dimensions is None:
        if not candidates:
            return []
        first = candidates[0]
        if isinstance(first, dict):
            values = first.get("metrics", first)
        else:
            values = getattr(first, "normalized_metrics", getattr(first, "metrics", {}))
        dimensions = sorted(str(name) for name in values)
    usable = [dimension for dimension in dimensions if all(_metrics(candidate, [dimension])[dimension] is not None for candidate in candidates)]
    if not usable:
        return list(candidates)
    result: list[Any] = []
    for index, candidate in enumerate(candidates):
        if not any(dominates(other, candidate, dimensions=usable, directions=directions) for other_index, other in enumerate(candidates) if other_index != index):
            result.append(candidate)
    return result


filter_non_dominated = pareto_frontier
non_dominated = pareto_frontier


__all__ = ["dominates", "filter_non_dominated", "non_dominated", "pareto_frontier"]
