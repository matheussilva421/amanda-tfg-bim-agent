"""Behavioural contract of the delegated architectural layout generator.

The design engine stops at macrozone strips and does not produce a buildable
plan.  These tests fix the contract of the module that turns the canonical
program into a real single-storey plan: exact program areas, no overlap, one
traversable gallery reaching every room, a protected patio, and an enclosed
built area consistent with the program's own estimate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from shapely.geometry import Point

from amanda_agent.design.architectural_layout import (
    PATIO_MIN_M2,
    PROGRAM_COVERED_RANGE_M2,
    PROGRAM_ENCLOSED_RANGE_M2,
    ArchitecturalLayoutError,
    build_courtyard_layout,
)

ROOT = Path(__file__).resolve().parents[2]
PROGRAM_PATH = ROOT / "project" / "requirements" / "program.json"


@pytest.fixture(scope="module")
def program() -> dict:
    return json.loads(PROGRAM_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def layout(program: dict):
    return build_courtyard_layout(program)


def _instances(program: dict) -> list[tuple[str, float, str]]:
    rows: list[tuple[str, float, str]] = []
    for sector in program["sectors"]:
        if str(sector.get("area_kind", "")).upper() != "INTERNAL":
            continue
        for space in sector["spaces"]:
            quantity = int(space.get("quantity", 1))
            for index in range(1, quantity + 1):
                logical_id = (
                    space["logical_id"]
                    if quantity == 1
                    else f"{space['logical_id']}#{index}"
                )
                rows.append(
                    (logical_id, float(space["target_area_m2"]), sector["logical_id"])
                )
    return rows


def test_program_instances_are_all_placed_exactly_once(layout, program):
    placed = {room.logical_id: room for room in layout.rooms}
    expected = _instances(program)

    assert len(placed) == len(expected)
    for logical_id, area, sector_id in expected:
        assert logical_id in placed, logical_id
        room = placed[logical_id]
        assert room.sector_id == sector_id
        assert room.net_area_m2 == pytest.approx(area, abs=1e-9)
        assert room.polygon.area == pytest.approx(area, abs=1e-9)


def test_room_areas_are_never_stretched_to_reach_a_total(layout):
    assert layout.accounting["net_internal_m2"] == pytest.approx(626.0, abs=1e-6)
    for room in layout.rooms:
        assert room.polygon.is_valid
        assert room.depth_m <= layout.parameters["band_depth_m"] + 1e-9
        assert room.length_m * room.depth_m == pytest.approx(room.net_area_m2, abs=1e-9)


def test_rooms_do_not_overlap_each_other_or_the_gallery(layout):
    polygons = [room.polygon for room in layout.rooms]
    for index, first in enumerate(polygons):
        for second in polygons[index + 1 :]:
            assert first.intersection(second).area <= 1e-6
        assert first.intersection(layout.gallery).area <= 1e-6


def test_gallery_touches_both_faces_and_the_whole_plan(layout):
    gallery = layout.gallery
    street = layout.face_rooms("street")
    patio = layout.face_rooms("patio")
    assert street and patio
    for room in [*street, *patio]:
        assert room.polygon.distance(gallery) <= 1e-9, room.logical_id


def test_gallery_width_respects_the_accessibility_minimum(layout):
    assert layout.corridor_width_m >= 1.5
    min_x, min_y, max_x, max_y = layout.gallery.bounds
    assert min(max_x - min_x, max_y - min_y) == pytest.approx(
        layout.corridor_width_m, abs=1e-9
    )


def test_every_room_is_inside_the_built_plate(layout):
    assert layout.plate.is_valid
    assert layout.footprint.is_valid
    for room in layout.rooms:
        assert layout.plate.buffer(1e-6).covers(room.polygon)
    assert layout.footprint.covers(layout.gallery)


def test_rooms_keep_a_habitable_minimum_dimension(layout):
    for room in layout.rooms:
        assert room.min_dimension_m >= 1.0 - 1e-9, room.logical_id


def test_enclosed_area_is_accounted_and_inside_the_program_range(layout):
    low, high = PROGRAM_ENCLOSED_RANGE_M2
    accounting = layout.accounting
    gross = accounting["gross_enclosed_m2"]

    assert low - 1e-6 <= gross <= high + 1e-6
    assert accounting["within_program_enclosed_estimate"] is True
    assert accounting["gross_vs_program_m2"] == 0.0
    # Every square metre of the enclosed area is attributed to something.
    assert gross == pytest.approx(
        accounting["net_internal_m2"]
        + accounting["circulation_m2"]
        + accounting["partitions_m2"]
        + accounting["service_voids_m2"],
        abs=1e-6,
    )
    assert accounting["construction_footprint_m2"] > gross
    assert 0.7 <= accounting["net_to_gross_factor"] <= 0.9


def test_covered_total_reconciles_the_program_covered_estimate(layout):
    """The programme estimates a covered total; the plan must measure one."""

    low, high = PROGRAM_COVERED_RANGE_M2
    accounting = layout.accounting
    covered = accounting["covered_total_m2"]

    assert low - 1e-6 <= covered <= high + 1e-6
    assert accounting["within_program_covered_estimate"] is True
    assert accounting["covered_vs_program_m2"] == 0.0
    # Covered is enclosed plus the roofed veranda, and nothing else.
    assert covered == pytest.approx(
        accounting["gross_enclosed_m2"] + accounting["veranda_m2"], abs=1e-6
    )
    assert accounting["veranda_m2"] > 0.0
    assert layout.parameters["veranda_depth_m"] > 0.0


def test_patio_is_protected_open_ground_beside_the_residential_face(layout):
    patio = layout.patio
    assert patio.area >= PATIO_MIN_M2
    assert patio.intersection(layout.footprint).area <= 1e-6
    facing = [room for room in layout.rooms if room.faces_patio]
    assert facing
    assert all(room.face == "patio" for room in facing)
    # Facing the patio is the patio side of the gallery.  A room large enough to
    # span the whole band reaches the roofed veranda directly; a shallow room
    # such as a bathroom steps back and looks over its own external wall, so its
    # distance is larger.  Both are patio-facing, and neither claim is invented.
    veranda_depth = layout.parameters["veranda_depth_m"]
    distances = [room.polygon.distance(patio) for room in facing]
    assert min(distances) <= veranda_depth + 1e-6
    assert max(distances) < layout.parameters["band_depth_m"] + veranda_depth + 1e-6
    reaching = [room for room in facing if room.polygon.distance(layout.veranda) <= 1e-9]
    assert reaching, "some patio rooms must actually reach the veranda"
    # Residential looks into the patio; services never do.
    assert layout.rooms_of("SEC-02")
    assert all(room.face == "patio" for room in layout.rooms_of("SEC-02"))
    assert all(room.face == "street" for room in layout.rooms_of("SEC-06"))


def test_plan_is_deterministic_and_carries_a_content_hash(program):
    first = build_courtyard_layout(program)
    second = build_courtyard_layout(program)
    assert first.content_hash == second.content_hash
    assert len(first.content_hash) == 64
    assert first.parameters == second.parameters
    assert first.accounting == second.accounting


def test_privacy_gradient_orders_public_before_residential(layout):
    levels = layout.sector_privacy_level
    assert levels["SEC-01"] < levels["SEC-03"]
    assert levels["SEC-05"] < levels["SEC-02"]
    assert levels["SEC-06"] <= levels["SEC-02"]
    for room in layout.rooms:
        assert room.privacy_level == levels[room.sector_id]


def test_service_sector_has_its_own_external_access(layout):
    service = layout.rooms_of("SEC-06")
    assert service
    access = layout.service_access_point
    assert isinstance(access, Point)
    # The loading area opens onto the street face of the bar, not through the
    # gallery the residents use.
    loading = [room for room in service if room.polygon.distance(access) <= 1e-9]
    assert loading
    assert all(room.face == "street" for room in loading)
    assert access.y == pytest.approx(
        min(room.polygon.bounds[1] for room in loading), abs=1e-9
    )
    assert access.y < layout.gallery.bounds[1]


def test_external_programme_never_leaks_into_the_internal_plan(layout):
    assert all(room.sector_id != "SEC-07" for room in layout.rooms)


def test_layout_refuses_a_program_without_internal_spaces():
    empty = {"sectors": [{"logical_id": "SEC-09", "area_kind": "EXTERNAL", "spaces": []}]}
    with pytest.raises(ArchitecturalLayoutError):
        build_courtyard_layout(empty)


def test_layout_refuses_a_sector_with_no_declared_face():
    unknown = {
        "sectors": [
            {
                "logical_id": "SEC-99",
                "area_kind": "INTERNAL",
                "spaces": [
                    {
                        "logical_id": "REQ-99-01",
                        "name": "Sala desconhecida",
                        "quantity": 1,
                        "target_area_m2": 20.0,
                    }
                ],
            }
        ]
    }
    with pytest.raises(ArchitecturalLayoutError):
        build_courtyard_layout(unknown)
