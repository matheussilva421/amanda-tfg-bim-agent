"""Pure desired-state builders for external Revit artifacts.

These builders do not open Revit or write a model.  They describe the
provider-facing geometry in feet while retaining the metric source values for
auditability.  Missing source evidence is represented explicitly rather than
being replaced with a guessed Revit level.
"""

from __future__ import annotations

import hashlib
import itertools
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .models import DesiredElement
from .provenance import BimProvenance
from .units import degrees_to_radians, meters_to_feet

_GENERATION_RUN = "EXTERNAL-ARTIFACTS-RUN"
_DESIGN_OPTION = "EXTERNAL_ARTIFACTS"


def _finite(value: Any, *, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric, not bool")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _non_empty_name(name: Any) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    return name.strip()


def _element(
    *,
    logical_id: str,
    category: str,
    geometry: dict[str, Any],
    properties: dict[str, Any],
    requirement_id: str,
    source_refs: list[str] | None = None,
    notes: dict[str, Any] | None = None,
) -> DesiredElement:
    return DesiredElement(
        logical_id=logical_id,
        category=category,
        geometry=geometry,
        properties=properties,
        requirement_id=requirement_id,
        design_option=_DESIGN_OPTION,
        generation_run=_GENERATION_RUN,
        provenance=BimProvenance(
            requirement_id=requirement_id,
            design_option=_DESIGN_OPTION,
            generation_run=_GENERATION_RUN,
            source_refs=source_refs or [],
            notes=notes or {},
        ),
    )


def _stable_id(prefix: str, *values: Any) -> str:
    raw = "\x1f".join(str(value) for value in values).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(raw).hexdigest()[:16]}"


def _xyz(value: Any, *, name: str) -> list[float]:
    if isinstance(value, Mapping):
        if set(value) != {"x", "y", "z"}:
            raise ValueError(f"{name} mapping must contain x, y and z")
        value = (value["x"], value["y"], value["z"])
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must contain three coordinates")
    if len(value) != 3:
        raise ValueError(f"{name} must contain three coordinates")
    return [_finite(item, name=f"{name}[{index}]") for index, item in enumerate(value)]


def _footprint(value: Any) -> list[list[float]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("footprint must contain points")
    points = []
    for index, point in enumerate(value):
        if isinstance(point, (str, bytes)) or not isinstance(point, Sequence):
            raise TypeError(f"footprint point {index} must contain x and y")
        if len(point) != 2:
            raise ValueError(f"footprint point {index} must contain x and y")
        points.append(
            [
                _finite(point[0], name=f"footprint[{index}].x"),
                _finite(point[1], name=f"footprint[{index}].y"),
            ]
        )
    if len(points) < 3:
        raise ValueError("footprint must contain at least three points")
    closed = points if points[0] == points[-1] else [*points, points[0]]
    area_twice = sum(
        first[0] * second[1] - second[0] * first[1]
        for first, second in itertools.pairwise(closed)
    )
    if math.isclose(area_twice, 0.0, abs_tol=1e-12):
        raise ValueError("footprint must enclose a non-zero area")
    return closed


def place_link(
    model_path: str | Path, *, name: str, insertion: Sequence[Any]
) -> DesiredElement:
    """Describe a linked model instance at a metric insertion point."""

    try:
        path = Path(model_path)
    except TypeError as exc:
        raise ValueError("model file path is invalid") from exc
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"model file does not exist or is mutable: {path}")
    display_name = _non_empty_name(name)
    insertion_m = _xyz(insertion, name="insertion")
    insertion_ft = [meters_to_feet(value) for value in insertion_m]
    resolved = path.resolve()
    return _element(
        logical_id=_stable_id("EXT-LINK", resolved, display_name),
        category="external_model_link",
        geometry={
            "model_path": str(resolved),
            "insertion_m": insertion_m,
            "insertion_ft": insertion_ft,
        },
        properties={
            "name": display_name,
            "unit_boundary": "meters_to_revit_feet",
        },
        requirement_id="BIM-EXTERNAL-LINK",
        source_refs=[str(resolved)],
        notes={"artifact_kind": "linked_model"},
    )


def place_toposolid(
    footprint: Sequence[Sequence[Any]], *, elevation: Any, name: str
) -> DesiredElement:
    """Describe a Toposolid footprint without asserting a reference level."""

    display_name = _non_empty_name(name)
    footprint_m = _footprint(footprint)
    elevation_m = _finite(elevation, name="elevation")
    footprint_ft = [
        [meters_to_feet(point[0]), meters_to_feet(point[1])] for point in footprint_m
    ]
    return _element(
        logical_id=_stable_id("EXT-TOPOSOLID", display_name, footprint_m, elevation_m),
        category="toposolid",
        geometry={
            "footprint_m": footprint_m,
            "footprint_ft": footprint_ft,
            "elevation_m": elevation_m,
            "elevation_ft": meters_to_feet(elevation_m),
        },
        properties={
            "name": display_name,
            "reference_level": None,
            "reference_level_status": "NOT_PROVEN",
            "unit_boundary": "meters_to_revit_feet",
        },
        requirement_id="BIM-EXTERNAL-TOPOSOLID",
        notes={
            "artifact_kind": "toposolid",
            "reference_level_proven": False,
        },
    )


def compute_true_north(azimuth_degrees: Any) -> DesiredElement:
    """Describe true north with a degree input and a provider-facing radian value."""

    azimuth = _finite(azimuth_degrees, name="azimuth_degrees")
    if not 0.0 <= azimuth <= 360.0:
        raise ValueError("azimuth_degrees must be between 0 and 360")
    return _element(
        logical_id="EXT-TRUE-NORTH",
        category="true_north",
        geometry={
            "azimuth_degrees": azimuth,
            "azimuth_radians": degrees_to_radians(azimuth),
        },
        properties={
            "angle_unit": "degrees_to_radians",
            "source_value_is_degrees": True,
        },
        requirement_id="BIM-EXTERNAL-TRUE-NORTH",
        notes={"artifact_kind": "true_north"},
    )


def compute_georeference(
    lat: Any, lon: Any, elevation: Any, *, epsg: int = 4674
) -> DesiredElement:
    """Describe a geographic reference and convert only elevation to feet."""

    latitude = _finite(lat, name="latitude")
    longitude = _finite(lon, name="longitude")
    elevation_m = _finite(elevation, name="elevation")
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("latitude must be between -90 and 90")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("longitude must be between -180 and 180")
    if isinstance(epsg, bool) or not isinstance(epsg, int) or epsg <= 0:
        raise ValueError("epsg must be a positive integer")
    return _element(
        logical_id="EXT-GEOREFERENCE",
        category="georeference",
        geometry={
            "latitude": latitude,
            "longitude": longitude,
            "elevation_m": elevation_m,
            "elevation_ft": meters_to_feet(elevation_m),
        },
        properties={
            "epsg": epsg,
            "coordinate_system": "geographic",
            "unit_boundary": "meters_to_revit_feet",
        },
        requirement_id="BIM-EXTERNAL-GEOREFERENCE",
        notes={"artifact_kind": "georeference"},
    )


__all__ = [
    "compute_georeference",
    "compute_true_north",
    "place_link",
    "place_toposolid",
]
