from __future__ import annotations

import pytest
from shapely.geometry import box

from amanda_agent.design.rooms import refine_rooms, validate_room_layout


def test_three_room_refinement_preserves_logical_ids_and_separates_net_from_gross():
    result = refine_rooms(
        {"logical_id": "block-1", "geometry": box(0, 0, 12, 10), "level": 0},
        [
            {"logical_id": "room-a", "target_area_m2": 30},
            {"logical_id": "room-b", "target_area_m2": 30},
            {"logical_id": "room-c", "target_area_m2": 30},
        ],
        wall_thickness_m=0.2,
        circulation_area_m2=18,
    )

    assert result.ok is True
    assert {room["logical_id"] for room in result.rooms} == {"room-a", "room-b", "room-c"}
    assert sum(room["net_area_m2"] for room in result.rooms) == 90
    assert result.accounting["net_area_m2"] == 90
    assert result.accounting["gross_footprint_m2"] > 90
    assert result.accounting["circulation_m2"] == 18
    assert result.net_to_gross_is_hypothesis is True


def test_quantity_expands_instances_without_changing_logical_base_id():
    result = refine_rooms(
        {"logical_id": "block-1", "geometry": box(0, 0, 10, 10)},
        [{"logical_id": "bedroom", "quantity": 2, "target_area_m2": 20}],
    )

    assert result.ok is True
    assert [room["logical_id"] for room in result.rooms] == ["bedroom#1", "bedroom#2"]
    assert {room["logical_id_base"] for room in result.rooms} == {"bedroom"}


def test_disconnected_rooms_are_rejected_as_orphans():
    result = validate_room_layout(
        [
            {"logical_id": "a", "geometry": box(0, 0, 3, 3)},
            {"logical_id": "b", "geometry": box(7, 7, 10, 10)},
        ],
        entry_id="a",
    )

    assert result.ok is False
    assert any(item.code == "unreachable_room" for item in result.violations)


def test_external_garden_is_not_counted_as_internal_area():
    result = refine_rooms(
        {"logical_id": "block-1", "geometry": box(0, 0, 10, 10)},
        [{"logical_id": "room", "target_area_m2": 20}],
        external_spaces=[{"logical_id": "garden", "geometry": box(20, 20, 25, 25)}],
    )

    assert result.accounting["internal_net_area_m2"] == 20
    assert result.accounting["external_area_m2"] == 0


def test_canonical_minimum_area_is_enforced_only_when_present():
    result = refine_rooms(
        {"logical_id": "block-1", "geometry": box(0, 0, 10, 10)},
        [{"logical_id": "room", "target_area_m2": 10, "min_area_m2": 12}],
    )

    assert result.ok is False
    assert any(item.code == "room_area_below_minimum" for item in result.violations)


def test_multi_storey_rooms_stack_with_unique_ids_and_doubled_net_area():
    requirements = [
        {"logical_id": "room-a", "target_area_m2": 30},
        {"logical_id": "room-b", "target_area_m2": 30},
        {"logical_id": "room-c", "target_area_m2": 30},
    ]

    single = refine_rooms({"logical_id": "block-1", "geometry": box(0, 0, 12, 10)}, requirements)
    doubled = refine_rooms({"logical_id": "block-1", "geometry": box(0, 0, 12, 10)}, requirements, storeys=2)

    assert single.ok is True and doubled.ok is True
    assert len(single.rooms) == 3
    assert len(doubled.rooms) == 6
    assert doubled.accounting["net_area_m2"] == pytest.approx(2 * single.accounting["net_area_m2"])
    assert {room["level"] for room in doubled.rooms} == {0, 1}
    assert len({room["logical_id"] for room in doubled.rooms}) == 6
    assert {room["logical_id_base"] for room in doubled.rooms} == {"room-a", "room-b", "room-c"}
