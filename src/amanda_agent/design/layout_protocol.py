"""Structural layout contracts shared by design, BIM, QA, and export code."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry


@dataclass(frozen=True)
class ExternalSpace:
    """A named, measurable exterior program space in a layout."""

    logical_id: str
    name: str
    polygon: BaseGeometry
    is_covered: bool = False

    @property
    def area_m2(self) -> float:
        return float(self.polygon.area)


@runtime_checkable
class ExternalSpaceProtocol(Protocol):
    """Minimum geometry and identity needed for an exterior program space."""

    logical_id: str
    name: str
    polygon: BaseGeometry
    is_covered: bool

    @property
    def area_m2(self) -> float: ...


@runtime_checkable
class LayoutProtocol(Protocol):
    """Stable interface consumed by active BIM, QA, and export workflows."""

    rooms: Sequence[Any]
    footprint: BaseGeometry
    external_spaces: Sequence[ExternalSpaceProtocol]
    content_hash: str
    accounting: Mapping[str, Any]
    parameters: Mapping[str, Any]
    service_access_point: Point


__all__ = ["ExternalSpace", "ExternalSpaceProtocol", "LayoutProtocol"]
