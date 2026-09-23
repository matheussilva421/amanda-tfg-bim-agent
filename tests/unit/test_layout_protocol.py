from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from shapely.geometry import Point, box
from shapely.geometry.base import BaseGeometry

from amanda_agent.design.architectural_layout import build_courtyard_layout
from amanda_agent.design.layout_protocol import (
    ExternalSpace,
    LayoutProtocol,
)

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class MinimalLayout:
    rooms: tuple[Any, ...]
    footprint: BaseGeometry
    external_spaces: tuple[ExternalSpace, ...]
    content_hash: str
    accounting: dict[str, float]
    parameters: dict[str, float]
    service_access_point: Point


def test_minimal_structural_layout_satisfies_the_protocol():
    garden = ExternalSpace(
        logical_id="GARDEN",
        name="Central garden",
        polygon=box(2, 2, 6, 6),
        is_covered=False,
    )
    fake = MinimalLayout(
        rooms=(),
        footprint=box(0, 0, 1, 1),
        external_spaces=(garden,),
        content_hash="a" * 64,
        accounting={"net_internal_m2": 0.0},
        parameters={},
        service_access_point=Point(0, 0),
    )

    assert isinstance(fake, LayoutProtocol)
    assert fake.external_spaces[0].area_m2 == pytest.approx(16.0)


def test_legacy_courtyard_layout_satisfies_protocol_without_geometry_changes():
    program = json.loads(
        (ROOT / "project/requirements/program.json").read_text(encoding="utf-8")
    )
    layout = build_courtyard_layout(program)

    assert isinstance(layout, LayoutProtocol)
    assert {space.logical_id for space in layout.external_spaces} == {
        "PROTECTED_PATIO",
        "COVERED_VERANDA",
    }
    by_id = {space.logical_id: space for space in layout.external_spaces}
    assert by_id["PROTECTED_PATIO"].is_covered is False
    assert by_id["COVERED_VERANDA"].is_covered is True
    assert all(
        space.area_m2 == pytest.approx(space.polygon.area)
        for space in layout.external_spaces
    )
    assert layout.content_hash
    assert layout.accounting["net_internal_m2"] == pytest.approx(626.0)
