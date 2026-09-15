"""Metric-to-Revit unit conversions used at the BIM provider boundary.

Design data remains metric.  These functions are intentionally small and
side-effect free so a provider adapter can convert only when its capability
contract declares Revit's internal feet (or derived units).
"""

from __future__ import annotations

import math
from typing import SupportsFloat

METERS_PER_FOOT = 0.3048
FEET_PER_METER = 1.0 / METERS_PER_FOOT
SQUARE_METERS_PER_SQUARE_FOOT = METERS_PER_FOOT**2
CUBIC_METERS_PER_CUBIC_FOOT = METERS_PER_FOOT**3


def _finite(value: SupportsFloat, *, name: str = "value") -> float:
    """Return a finite numeric value, rejecting booleans and text."""

    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric, not bool")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def meters_to_feet(meters: SupportsFloat) -> float:
    """Convert metres to Revit's internal length unit, feet."""

    return _finite(meters, name="meters") * FEET_PER_METER


def feet_to_meters(feet: SupportsFloat) -> float:
    """Convert Revit's internal length unit, feet, to metres."""

    return _finite(feet, name="feet") * METERS_PER_FOOT


def sqm_to_sqft(square_meters: SupportsFloat) -> float:
    """Convert square metres to square feet."""

    return _finite(square_meters, name="square_meters") / SQUARE_METERS_PER_SQUARE_FOOT


def sqft_to_sqm(square_feet: SupportsFloat) -> float:
    """Convert square feet to square metres."""

    return _finite(square_feet, name="square_feet") * SQUARE_METERS_PER_SQUARE_FOOT


def cubic_meters_to_cubic_feet(cubic_meters: SupportsFloat) -> float:
    """Convert cubic metres to cubic feet."""

    return _finite(cubic_meters, name="cubic_meters") / CUBIC_METERS_PER_CUBIC_FOOT


def cubic_feet_to_cubic_meters(cubic_feet: SupportsFloat) -> float:
    """Convert cubic feet to cubic metres."""

    return _finite(cubic_feet, name="cubic_feet") * CUBIC_METERS_PER_CUBIC_FOOT


def degrees_to_radians(degrees: SupportsFloat) -> float:
    """Convert an angle in degrees to radians."""

    return math.radians(_finite(degrees, name="degrees"))


def radians_to_degrees(radians: SupportsFloat) -> float:
    """Convert an angle in radians to degrees."""

    return math.degrees(_finite(radians, name="radians"))


__all__ = [
    "CUBIC_METERS_PER_CUBIC_FOOT",
    "FEET_PER_METER",
    "METERS_PER_FOOT",
    "SQUARE_METERS_PER_SQUARE_FOOT",
    "cubic_feet_to_cubic_meters",
    "cubic_meters_to_cubic_feet",
    "degrees_to_radians",
    "feet_to_meters",
    "meters_to_feet",
    "radians_to_degrees",
    "sqft_to_sqm",
    "sqm_to_sqft",
]
