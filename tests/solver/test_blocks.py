from __future__ import annotations

import pytest
from shapely.geometry import box

from amanda_agent.design.blocks import generate_blocks


def test_blocks_stay_inside_sectors_and_match_demand():
    result = generate_blocks(
        [
            {"logical_id": "public", "geometry": box(0, 0, 10, 10), "demand_m2": 60},
            {"logical_id": "residential", "geometry": box(10, 0, 20, 10), "demand_m2": 60},
        ],
        area_tolerance_percent=1,
        min_width_m=2,
    )

    assert result.ok is True
    assert len(result.blocks) == 2
    zones = {"public": box(0, 0, 10, 10), "residential": box(10, 0, 20, 10)}
    for block in result.blocks:
        assert block["geometry"].area == pytest.approx(60)
        assert block["sector_id"] in {"public", "residential"}
        assert zones[block["sector_id"]].covers(block["geometry"])
    assert not result.violations


def test_sector_splitting_requires_explicit_configuration():
    result = generate_blocks(
        [{"logical_id": "sector", "geometry": box(0, 0, 10, 10), "demand_m2": 140}],
        allow_sector_splitting=False,
    )

    assert result.ok is False
    assert any(item.code == "sector_capacity" for item in result.violations)


def test_sliver_polygon_is_rejected():
    result = generate_blocks(
        [{"logical_id": "sliver", "geometry": box(0, 0, 20, 1), "demand_m2": 10}],
        min_width_m=2,
    )

    assert result.ok is False
    assert any(item.code == "sliver_polygon" for item in result.violations)


def test_explicit_sector_split_creates_non_overlapping_blocks():
    result = generate_blocks(
        [{"logical_id": "sector", "geometry": box(0, 0, 20, 10), "demand_m2": 100}],
        allow_sector_splitting=True,
        split_count=2,
    )

    assert result.ok is True
    assert len(result.blocks) == 2
    assert result.blocks[0]["geometry"].intersection(result.blocks[1]["geometry"]).area == 0
