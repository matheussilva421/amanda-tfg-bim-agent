"""Fast project-labeled solar and ventilation heuristics."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, isfinite, radians
from typing import Any


def _circular_difference(first: float, second: float) -> float:
    return abs((first - second + 180.0) % 360.0 - 180.0)


@dataclass(frozen=True)
class EnvironmentalHeuristics:
    solar_score: float
    ventilation_score: float
    metrics: dict[str, float]
    labels: dict[str, str] = field(default_factory=lambda: {"solar": "HEURISTIC", "ventilation": "HEURISTIC"})
    evidence: list[str] = field(default_factory=list)


def evaluate_environmental_heuristics(
    geometry: Any,
    *,
    true_north_deg: float = 0.0,
    preferred_solar_orientation_deg: float = 0.0,
    wind_direction_deg: float = 90.0,
) -> EnvironmentalHeuristics:
    """Score orientation relative to true north and wind exposure in [0, 1]."""

    if not all(isfinite(float(value)) for value in (true_north_deg, preferred_solar_orientation_deg, wind_direction_deg)):
        raise ValueError("environmental directions must be finite")
    if isinstance(geometry, dict):
        orientation = float(geometry.get("facade_orientation_deg", geometry.get("orientation_deg", 0.0)) or 0.0)
        opening_ratio = float(geometry.get("opening_ratio", 0.5) or 0.0)
        exposure = float(geometry.get("wind_exposure", 1.0) or 0.0)
    else:
        orientation = float(getattr(geometry, "facade_orientation_deg", getattr(geometry, "orientation_deg", 0.0)))
        opening_ratio = float(getattr(geometry, "opening_ratio", 0.5))
        exposure = float(getattr(geometry, "wind_exposure", 1.0))
    if not 0 <= opening_ratio <= 1 or not 0 <= exposure <= 1:
        raise ValueError("opening_ratio and wind_exposure must be between 0 and 1")
    world_orientation = (orientation - true_north_deg) % 360.0
    solar_difference = _circular_difference(world_orientation, preferred_solar_orientation_deg)
    solar_score = max(0.0, 1.0 - solar_difference / 180.0)
    wind_difference = _circular_difference(world_orientation, wind_direction_deg)
    wind_alignment = (1.0 + cos(radians(wind_difference))) / 2.0
    ventilation_score = max(0.0, min(1.0, 0.55 * wind_alignment * exposure + 0.45 * opening_ratio))
    return EnvironmentalHeuristics(
        solar_score=float(solar_score),
        ventilation_score=float(ventilation_score),
        metrics={"solar_heuristic": float(solar_score), "ventilation_heuristic": float(ventilation_score)},
        evidence=[
            "true-north-aware facade orientation",
            "Amanda source orientation and wind findings are applied as project heuristics",
            "detailed environmental simulation was not run",
        ],
    )


evaluate_environment = evaluate_environmental_heuristics
fast_environmental_heuristics = evaluate_environmental_heuristics


__all__ = ["EnvironmentalHeuristics", "evaluate_environment", "evaluate_environmental_heuristics", "fast_environmental_heuristics"]
