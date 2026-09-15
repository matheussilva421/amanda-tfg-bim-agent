"""Configuration-driven archetypes that generate deterministic macro seeds."""

from __future__ import annotations

import random
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import box, mapping

from .geometry import InvalidDesignGeometryError, validate_polygon


class ArchetypeName(StrEnum):
    COURTYARD = "COURTYARD"
    LINEAR_SPINE = "LINEAR_SPINE"
    CLUSTER = "CLUSTER"
    PRIVACY_GRADIENT = "PRIVACY_GRADIENT"
    DOUBLE_COURTYARD = "DOUBLE_COURTYARD"
    COMB = "COMB"


class MacroSeed(BaseModel):
    """Serializable macro initialization, with no preselected winner."""

    model_config = ConfigDict(extra="forbid")

    archetype: ArchetypeName
    seed: int
    site: dict[str, Any]
    sectors: list[dict[str, Any]] = Field(min_length=1)
    courtyards: list[dict[str, Any]] = Field(default_factory=list)
    initialization: dict[str, Any]
    relationships: list[Any]
    exploration_tags: list[str]
    selected: str | None = None
    valid: bool = True


def _config_path(path: str | Path | None) -> Path:
    return (
        Path(path)
        if path is not None
        else Path(__file__).resolve().parents[3]
        / "design-engine"
        / "config"
        / "archetypes.yaml"
    )


def load_archetypes(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Load archetype rules as data, preserving strategy and relationships."""

    payload = yaml.safe_load(_config_path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TypeError("archetypes YAML must contain a mapping")
    configurations = payload.get("archetypes")
    if not isinstance(configurations, Mapping):
        raise TypeError("archetypes YAML must contain archetypes mapping")
    return {str(key): dict(value) for key, value in configurations.items()}


def get_archetype(name: ArchetypeName | str) -> dict[str, Any]:
    """Return one configured archetype by its stable name."""

    resolved = ArchetypeName(str(name))
    try:
        return load_archetypes()[resolved.value]
    except KeyError as exc:  # pragma: no cover - config is checked by tests
        raise KeyError(resolved.value) from exc


def list_archetypes() -> tuple[ArchetypeName, ...]:
    return tuple(ArchetypeName(name) for name in load_archetypes())


def exploration_archetypes() -> tuple[ArchetypeName, ...]:
    """Return Amanda's explicit exploration set without selecting a winner."""

    return (
        ArchetypeName.COURTYARD,
        ArchetypeName.CLUSTER,
        ArchetypeName.PRIVACY_GRADIENT,
    )


def _largest_polygon(geometry: Any) -> Any:
    if geometry.geom_type == "Polygon":
        return geometry
    if geometry.geom_type == "MultiPolygon":
        return max(geometry.geoms, key=lambda polygon: polygon.area)
    raise InvalidDesignGeometryError("macro sector intersection must be a polygon")


def _partition(site: Any, *, axis: int, first: float, second: float) -> list[Any]:
    min_x, min_y, max_x, max_y = site.bounds
    if axis == 0:
        boxes = [
            box(min_x, min_y, min_x + (max_x - min_x) * first, max_y),
            box(
                min_x + (max_x - min_x) * first,
                min_y,
                min_x + (max_x - min_x) * second,
                max_y,
            ),
            box(min_x + (max_x - min_x) * second, min_y, max_x, max_y),
        ]
    else:
        boxes = [
            box(min_x, min_y, max_x, min_y + (max_y - min_y) * first),
            box(
                min_x,
                min_y + (max_y - min_y) * first,
                max_x,
                min_y + (max_y - min_y) * second,
            ),
            box(min_x, min_y + (max_y - min_y) * second, max_x, max_y),
        ]
    return [_largest_polygon(site.intersection(item)) for item in boxes]


def _courtyard(site: Any, x_fraction: float, y_fraction: float, size_fraction: float) -> Any:
    min_x, min_y, max_x, max_y = site.bounds
    width = (max_x - min_x) * size_fraction
    height = (max_y - min_y) * size_fraction
    center_x = min_x + (max_x - min_x) * x_fraction
    center_y = min_y + (max_y - min_y) * y_fraction
    return _largest_polygon(
        site.intersection(
            box(
                center_x - width / 2,
                center_y - height / 2,
                center_x + width / 2,
                center_y + height / 2,
            )
        )
    )


def generate_macro_seed(
    archetype: ArchetypeName | str,
    site: Any,
    *,
    seed: int,
) -> MacroSeed:
    """Generate a valid, reproducible macro seed from rules and site bounds."""

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("macro generation requires an integer run seed")
    resolved = ArchetypeName(str(archetype))
    configuration = get_archetype(resolved)
    polygon = validate_polygon(site)
    rng = random.Random(seed)
    axis = rng.randrange(2)
    first = 0.25 + rng.random() * 0.12
    second = 0.58 + rng.random() * 0.12
    sectors_geometry = _partition(polygon, axis=axis, first=first, second=second)
    labels = ("public", "controlled", "residential")
    sectors = [
        {
            "logical_id": label,
            "privacy_level": level,
            "geometry": dict(mapping(sector)),
        }
        for label, level, sector in zip(labels, (0, 1, 5), sectors_geometry)
    ]
    courtyards: list[dict[str, Any]] = []
    if resolved in {ArchetypeName.COURTYARD, ArchetypeName.CLUSTER}:
        courtyard = _courtyard(polygon, 0.5, 0.5, 0.22)
        courtyards.append({"logical_id": "courtyard", "geometry": dict(mapping(courtyard))})
    elif resolved is ArchetypeName.DOUBLE_COURTYARD:
        for index, (x_fraction, y_fraction) in enumerate(((0.33, 0.5), (0.67, 0.5))):
            courtyard = _courtyard(polygon, x_fraction, y_fraction, 0.16)
            courtyards.append(
                {"logical_id": f"courtyard-{index + 1}", "geometry": dict(mapping(courtyard))}
            )
    return MacroSeed(
        archetype=resolved,
        seed=seed,
        site=dict(mapping(polygon)),
        sectors=sectors,
        courtyards=courtyards,
        initialization=dict(configuration["initialization"]),
        relationships=list(configuration["relationships"]),
        exploration_tags=list(configuration["exploration_tags"]),
    )


generate_macrozone_seed = generate_macro_seed
build_macro_seed = generate_macro_seed


__all__ = [
    "ArchetypeName",
    "MacroSeed",
    "build_macro_seed",
    "exploration_archetypes",
    "generate_macro_seed",
    "generate_macrozone_seed",
    "get_archetype",
    "list_archetypes",
    "load_archetypes",
]
