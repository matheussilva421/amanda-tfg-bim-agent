"""Validated Shapely/GeoJSON operations for site study geometry."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite, sqrt
from typing import Any

import shapely
from shapely.geometry import Polygon, mapping, shape
from shapely.validation import explain_validity

from .models import BoundaryKind, BoundaryPolygon

PINNED_SHAPELY_VERSION = "2.1.2"
if shapely.__version__ != PINNED_SHAPELY_VERSION:
    raise RuntimeError(
        "site geometry requires Shapely=="
        + PINNED_SHAPELY_VERSION
        + "; found "
        + shapely.__version__
    )


class InvalidBoundaryError(ValueError):
    """Raised when a site ring cannot be treated as a valid polygon."""


def _as_polygon(value: Any) -> Polygon:
    if isinstance(value, BoundaryPolygon):
        return Polygon(value.coordinates)
    if isinstance(value, Polygon):
        return value
    if isinstance(value, Mapping):
        try:
            geometry = shape(value)
        except Exception as exc:  # pragma: no cover - Shapely owns details
            raise InvalidBoundaryError("invalid GeoJSON boundary") from exc
        if not isinstance(geometry, Polygon):
            raise InvalidBoundaryError("site boundary must be a Polygon")
        return geometry
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        try:
            return Polygon(value)
        except Exception as exc:  # pragma: no cover - Shapely owns details
            raise InvalidBoundaryError("invalid boundary coordinate ring") from exc
    raise InvalidBoundaryError("boundary must be a ring, Polygon, or GeoJSON mapping")


def validate_boundary(value: Any) -> Polygon:
    """Return a valid polygon or refuse it with an explicit boundary error."""

    polygon = _as_polygon(value)
    if not polygon.is_valid:
        reason = explain_validity(polygon)
        if "Self-intersection" in reason:
            raise InvalidBoundaryError("boundary self-intersects: " + reason)
        raise InvalidBoundaryError("boundary is invalid: " + reason)
    if polygon.area <= 0:
        raise InvalidBoundaryError("boundary area must be positive")
    return polygon


def validate_self_intersection(value: Any) -> bool:
    """Validate a boundary ring and return ``True`` when it is safe."""

    validate_boundary(value)
    return True


def is_self_intersecting(value: Any) -> bool:
    """Report self-intersection without hiding other malformed boundaries."""

    polygon = _as_polygon(value)
    if polygon.is_valid:
        return False
    return "Self-intersection" in explain_validity(polygon)


def compute_area_m2(value: Any) -> float:
    """Compute area only after the complete polygon validity check."""

    return float(validate_boundary(value).area)


area_m2 = compute_area_m2


def build_area_preserving_rectangular_placeholder(
    area_m2: float,
    *,
    origin: tuple[float, float] = (0.0, 0.0),
    aspect_ratio: float = 1.0,
) -> BoundaryPolygon:
    """Build labelled study geometry from area only.

    The returned object is always ``STUDY_PLACEHOLDER``.  It intentionally has
    no cadastral source reference because an equal-area rectangle does not
    establish the real boundary.
    """

    if not isfinite(area_m2) or area_m2 <= 0:
        raise ValueError("area_m2 must be a finite positive number")
    if not isfinite(aspect_ratio) or aspect_ratio <= 0:
        raise ValueError("aspect_ratio must be a finite positive number")
    if len(origin) != 2 or not all(isfinite(value) for value in origin):
        raise ValueError("origin must contain two finite coordinates")

    width = sqrt(area_m2 * aspect_ratio)
    height = area_m2 / width
    x, y = origin
    ring = [
        (x, y),
        (x + width, y),
        (x + width, y + height),
        (x, y + height),
        (x, y),
    ]
    return BoundaryPolygon(
        coordinates=ring,
        kind=BoundaryKind.STUDY_PLACEHOLDER,
        placeholder_area_m2=area_m2,
    )


def polygon_to_geojson(value: Any) -> dict:
    """Serialize valid polygon geometry as a GeoJSON mapping."""

    return dict(mapping(validate_boundary(value)))


def polygon_from_geojson(payload: Mapping[str, Any]) -> list[tuple[float, float]]:
    """Read and validate a GeoJSON polygon, returning its exterior ring."""

    polygon = validate_boundary(payload)
    return [(float(x), float(y)) for x, y, *_ in polygon.exterior.coords]
