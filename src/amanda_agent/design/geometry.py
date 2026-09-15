"""Metric geometry primitives backed by the pinned Shapely implementation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from pathlib import Path
from typing import Any

import shapely
import yaml
from shapely.geometry import Polygon, shape
from shapely.validation import explain_validity

PINNED_SHAPELY_VERSION = "2.1.2"
if shapely.__version__ != PINNED_SHAPELY_VERSION:
    raise RuntimeError(
        "design geometry requires Shapely=="
        + PINNED_SHAPELY_VERSION
        + "; found "
        + shapely.__version__
    )


class InvalidDesignGeometryError(ValueError):
    """Raised when design geometry cannot be trusted for a metric operation."""


def _as_polygon(value: Any) -> Polygon:
    if isinstance(value, Polygon):
        return value
    if hasattr(value, "coordinates"):
        value = value.coordinates
    if isinstance(value, Mapping):
        try:
            geometry = shape(value)
        except Exception as exc:  # pragma: no cover - Shapely owns details
            raise InvalidDesignGeometryError("invalid GeoJSON polygon") from exc
        if not isinstance(geometry, Polygon):
            raise InvalidDesignGeometryError("design geometry must be a Polygon")
        return geometry
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        try:
            return Polygon(value)
        except Exception as exc:  # pragma: no cover - Shapely owns details
            raise InvalidDesignGeometryError("invalid polygon coordinate ring") from exc
    raise InvalidDesignGeometryError(
        "design geometry must be a polygon, coordinate ring, or GeoJSON mapping"
    )


def validate_polygon(value: Any) -> Polygon:
    """Return a valid polygon, rejecting self-intersections before measurement."""

    polygon = _as_polygon(value)
    if not polygon.is_valid:
        reason = explain_validity(polygon)
        if "Self-intersection" in reason:
            raise InvalidDesignGeometryError("polygon self-intersects: " + reason)
        raise InvalidDesignGeometryError("polygon is invalid: " + reason)
    if not isfinite(polygon.area) or polygon.area <= 0:
        raise InvalidDesignGeometryError("polygon area must be positive and finite")
    return polygon


def _finite_tolerance(value: float) -> float:
    if not isfinite(value) or value < 0:
        raise ValueError("tolerance must be a finite non-negative number in meters")
    return float(value)


def contains(container: Any, candidate: Any, *, tolerance_m: float = 0.0) -> bool:
    """Whether the candidate is covered by the container within metric tolerance."""

    tolerance = _finite_tolerance(tolerance_m)
    outer = validate_polygon(container)
    inner = validate_polygon(candidate)
    return outer.buffer(tolerance).covers(inner)


def overlaps(first: Any, second: Any, *, area_tolerance_m2: float = 0.000001) -> bool:
    """Whether two polygons have a positive physical intersection area."""

    tolerance = _finite_tolerance(area_tolerance_m2)
    left = validate_polygon(first)
    right = validate_polygon(second)
    return float(left.intersection(right).area) > tolerance


def overlap_area_m2(first: Any, second: Any) -> float:
    """Return the positive intersection area in square meters."""

    left = validate_polygon(first)
    right = validate_polygon(second)
    return float(left.intersection(right).area)


def minimum_distance(first: Any, second: Any) -> float:
    """Return the shortest boundary/interior distance in meters."""

    left = validate_polygon(first)
    right = validate_polygon(second)
    return float(left.distance(right))


def area_delta_percent(reference: Any, candidate: Any) -> float:
    """Return absolute area difference relative to reference, in percent."""

    reference_polygon = validate_polygon(reference)
    candidate_polygon = validate_polygon(candidate)
    reference_area = float(reference_polygon.area)
    return abs(float(candidate_polygon.area) - reference_area) / reference_area * 100


def centroid(value: Any) -> tuple[float, float]:
    """Return the Shapely centroid as a serializable ``(x, y)`` pair."""

    point = validate_polygon(value).centroid
    return (float(point.x), float(point.y))


def load_tolerances(path: str | Path | None = None) -> dict[str, Any]:
    """Load the metric tolerance registry without introducing unit conversion."""

    source = (
        Path(path)
        if path is not None
        else Path(__file__).resolve().parents[3]
        / "design-engine"
        / "config"
        / "tolerances.yaml"
    )
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("tolerances YAML must contain a mapping")
    for key in (
        "length_m",
        "distance_m",
        "area_m2",
        "area_delta_percent",
        "centroid_m",
    ):
        value = payload.get(key)
        if not isinstance(value, (int, float)) or not isfinite(float(value)):
            raise ValueError(f"tolerance {key} must be finite")
        if value < 0:
            raise ValueError(f"tolerance {key} must be non-negative")
    units = payload.get("units")
    if not isinstance(units, dict) or units.get("length") != "m":
        raise ValueError("tolerances must declare metric length units")
    return payload


polygon_contains = contains
is_within = contains
intersects = overlaps
distance_m = minimum_distance
area_delta = area_delta_percent


__all__ = [
    "PINNED_SHAPELY_VERSION",
    "InvalidDesignGeometryError",
    "area_delta",
    "area_delta_percent",
    "centroid",
    "contains",
    "distance_m",
    "intersects",
    "is_within",
    "load_tolerances",
    "minimum_distance",
    "overlap_area_m2",
    "overlaps",
    "polygon_contains",
    "validate_polygon",
]
