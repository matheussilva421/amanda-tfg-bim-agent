from __future__ import annotations

import json
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

import pytest

from amanda_agent.design.canonical_pavilion_layout import (
    build_canonical_pavilion_layout,
)
from amanda_agent.design.canonical_reference import CanonicalReferenceProfile

ROOT = Path(__file__).resolve().parents[2]
PROGRAM_PATH = ROOT / "project/requirements/program.json"


def _profile() -> CanonicalReferenceProfile:
    cluster = {
        "required": True,
        "pavilion_count_target": 4,
        "sleeping_pavilions_target": 3,
        "communal_pavilions_target": 1,
        "central_garden_required": True,
    }
    parti = {
        "single_linear_bar_allowed": False,
        "admin_public_edge": True,
        "admin_storeys_target": 2,
        "residential_cluster": cluster,
        "child_sector_green_interface": True,
        "service_block_separate": True,
        "service_access_separate": True,
        "covered_external_paths_required": True,
        "landscape_is_program": True,
    }
    data = {
        "program": {
            "people": 20,
            "net_internal_m2": 626.0,
            "external_programmed_m2": 260.0,
            "enclosed_estimate_m2": [783.0, 814.0],
            "covered_estimate_m2": [850.0, 950.0],
        },
        "required_parti": parti,
    }
    return CanonicalReferenceProfile(
        status="CANONICAL_DESIGN_REFERENCE",
        supersedes=("AMANDA-RUN-001-S01", "COURTYARD_DOUBLE_LOADED_BAR"),
        canonical_images=(
            "canonical/01_implantacao_geral_canonica.png",
            "canonical/02_bloco_residencial_canonico.png",
            "canonical/03_bloco_administrativo_canonico.png",
        ),
        source_hashes=("a" * 64, "b" * 64, "c" * 64),
        data=data,
    )


def _expected_rooms(program: dict) -> dict[str, tuple[float, str]]:
    expected: dict[str, tuple[float, str]] = {}
    for sector in program["sectors"]:
        if sector["area_kind"] != "INTERNAL":
            continue
        for space in sector["spaces"]:
            quantity = int(space.get("quantity", 1))
            area = float(space["target_area_m2"])
            for index in range(1, quantity + 1):
                logical_id = (
                    space["logical_id"]
                    if quantity == 1
                    else f"{space['logical_id']}#{index}"
                )
                expected[logical_id] = (area, sector["logical_id"])
    return expected


@pytest.fixture(scope="module")
def program() -> dict:
    return json.loads(PROGRAM_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def layout(program: dict):
    return build_canonical_pavilion_layout(program, _profile())


def test_internal_program_is_assigned_once_at_exact_net_area(layout, program):
    expected = _expected_rooms(program)
    actual = Counter(room.logical_id for room in layout.rooms)

    assert actual == Counter({logical_id: 1 for logical_id in expected})
    assert sum(room.net_area_m2 for room in layout.rooms) == pytest.approx(626.0)
    assert layout.accounting["net_internal_m2"] == pytest.approx(626.0)
    for room in layout.rooms:
        area, sector_id = expected[room.logical_id]
        assert room.sector_id == sector_id
        assert room.net_area_m2 == pytest.approx(area)
        assert room.polygon.area == pytest.approx(area)


def test_residential_program_is_split_across_three_sleeping_and_one_communal_pavilion(
    layout,
):
    pavilions = layout.residential_pavilions
    by_component: dict[str, set[str]] = defaultdict(set)
    for room in layout.rooms:
        by_component[room.component_id].add(room.logical_id)

    assert len(pavilions) == 4
    assert {block.component_id for block in pavilions} == {
        "RES_PAV_A",
        "RES_PAV_B",
        "RES_PAV_C",
        "RES_PAV_D_COMMUNAL",
    }
    for pavilion_id in ("RES_PAV_A", "RES_PAV_B", "RES_PAV_C"):
        assert any(
            logical_id.startswith(
                ("REQ-02-01", "REQ-02-02", "REQ-02-03", "REQ-02-04", "REQ-02-05")
            )
            for logical_id in by_component[pavilion_id]
        )
    assert by_component["RES_PAV_D_COMMUNAL"] == {
        "REQ-02-08",
        "REQ-02-09",
        "REQ-02-10",
    }


def test_administration_has_two_levels_and_services_are_a_separate_block(layout):
    admin = layout.block("ADMIN_ACOLHIMENTO")
    service = layout.block("SERVICE_CAPACITATION")
    levels = {
        room.level for room in layout.rooms if room.component_id == admin.component_id
    }

    assert admin.storeys == 2
    assert levels == {1, 2}
    assert admin.footprint.disjoint(service.footprint)
    assert service.access_point.distance(layout.public_access_point) > 20.0
    assert layout.service_access_point == service.access_point


def test_buildings_remain_separate_volumes_in_normalized_reference_coordinates(layout):
    assert layout.coordinate_basis == "NORMALIZED_METRIC_REFERENCE_NOT_SURVEY"
    assert layout.site_fit_status == "UNVERIFIED"
    assert len(layout.blocks) == 7
    assert layout.footprint.geom_type == "MultiPolygon"
    assert len(layout.footprint.geoms) == 7
    for index, first in enumerate(layout.blocks):
        for second in layout.blocks[index + 1 :]:
            assert first.footprint.distance(second.footprint) > 0.0


def test_programmed_external_spaces_total_exactly_260_square_metres(layout):
    assert sum(space.area_m2 for space in layout.external_spaces) == pytest.approx(
        260.0
    )
    assert layout.accounting["external_programmed_m2"] == pytest.approx(260.0)
    assert {space.component_id for space in layout.external_spaces} == {
        "PROTECTED_PATIO",
        "THERAPEUTIC_GARDEN",
        "HORTA",
        "EXERCISE",
        "PLAYGROUND",
    }


def test_central_garden_connects_each_pavilion_without_overlapping_closed_footprints(
    layout,
):
    garden = layout.central_garden
    connectors = [
        path
        for path in layout.covered_connectors
        if path.to_component == "PROTECTED_PATIO"
    ]
    assert len(connectors) == 4
    assert garden.area_m2 == pytest.approx(80.0)
    for connector in connectors:
        assert connector.area_m2 > 0.0
        assert connector.footprint.distance(garden.polygon) <= 1e-6
        for block in layout.blocks:
            assert connector.footprint.intersection(block.footprint).area <= 1e-6
    assert all(garden.polygon.disjoint(block.footprint) for block in layout.blocks)


def test_residential_quadrants_match_the_canonical_board_around_the_garden(layout):
    garden_center = layout.central_garden.polygon.centroid
    expected_quadrants = {
        "RES_PAV_A": (-1, 1),
        "RES_PAV_B": (-1, -1),
        "RES_PAV_C": (1, -1),
        "RES_PAV_D_COMMUNAL": (1, 1),
    }

    for component_id, (x_sign, y_sign) in expected_quadrants.items():
        center = layout.block(component_id).footprint.centroid
        assert (center.x - garden_center.x) * x_sign > 0
        assert (center.y - garden_center.y) * y_sign > 0


def test_residential_envelopes_and_covered_routes_preserve_organic_board_form(layout):
    for block in layout.residential_pavilions:
        assert len(block.footprint.exterior.coords) > 5

    for connector in layout.covered_connectors:
        assert len(connector.footprint.exterior.coords) > 5


def test_room_footprints_are_contained_and_separate_on_each_level(layout):
    for block in layout.blocks:
        for room in block.rooms:
            assert block.footprint.covers(room.polygon)
        for level in block.floor_footprints:
            rooms = [room for room in block.rooms if room.level == level]
            for index, first in enumerate(rooms):
                for second in rooms[index + 1 :]:
                    assert first.polygon.disjoint(second.polygon)


def test_external_program_areas_derive_from_the_versioned_program(program):
    changed_program = deepcopy(program)
    spaces = {
        space["logical_id"]: space
        for sector in changed_program["sectors"]
        for space in sector["spaces"]
    }
    spaces["REQ-07-01"]["target_area_m2"] = 81.0
    spaces["REQ-07-02"]["target_area_m2"] = 79.0

    layout = build_canonical_pavilion_layout(changed_program, _profile())

    areas = {space.logical_id: space.area_m2 for space in layout.external_spaces}
    assert areas["REQ-07-01"] == pytest.approx(81.0)
    assert areas["REQ-07-02"] == pytest.approx(79.0)
    assert sum(areas.values()) == pytest.approx(260.0)


def test_programmed_landscape_areas_are_separate_from_building_footprints(layout):
    for space in layout.external_spaces:
        assert space.polygon.disjoint(layout.footprint)
    for index, first in enumerate(layout.external_spaces):
        for second in layout.external_spaces[index + 1 :]:
            assert first.polygon.disjoint(second.polygon)
