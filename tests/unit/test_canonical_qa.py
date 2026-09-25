from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from shapely.affinity import translate as move_geometry

from amanda_agent.design.architectural_layout import build_courtyard_layout
from amanda_agent.design.canonical_pavilion_layout import (
    build_canonical_pavilion_layout,
)
from amanda_agent.design.canonical_qa import run_canonical_checks
from amanda_agent.design.canonical_reference import CanonicalReferenceProfile

ROOT = Path(__file__).resolve().parents[2]
PROGRAM_PATH = ROOT / "project/requirements/program.json"
REQUIRED_VISUAL_STAGES = ("R04", "R06", "R08", "R12", "R13", "R15")


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
    return CanonicalReferenceProfile(
        status="CANONICAL_DESIGN_REFERENCE",
        supersedes=("AMANDA-RUN-001-S01", "COURTYARD_DOUBLE_LOADED_BAR"),
        canonical_images=(
            "canonical/01_implantacao.png",
            "canonical/02_administrativo.png",
            "canonical/03_residencial.png",
            "canonical/04_servicos.png",
        ),
        source_hashes=("a" * 64, "b" * 64, "c" * 64, "d" * 64),
        data={
            "program": {
                "people": 20,
                "net_internal_m2": 626.0,
                "external_programmed_m2": 260.0,
                "enclosed_estimate_m2": [783.0, 814.0],
                "covered_estimate_m2": [850.0, 950.0],
            },
            "required_parti": parti,
        },
    )


@pytest.fixture(scope="module")
def program() -> dict:
    return json.loads(PROGRAM_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def profile() -> CanonicalReferenceProfile:
    return _profile()


@pytest.fixture(scope="module")
def canonical_layout(program: dict, profile: CanonicalReferenceProfile):
    return build_canonical_pavilion_layout(program, profile)


def _checks_by_id(layout, profile):
    return {item.check_id: item for item in run_canonical_checks(layout, profile)}


def test_qa_exposes_every_rubric_check_and_blocks_unproven_visual_regression(
    canonical_layout, profile
):
    checks = _checks_by_id(canonical_layout, profile)

    assert set(checks) == {f"CANON-{number:03d}" for number in range(1, 19)}
    assert all(
        checks[f"CANON-{number:03d}"].status == "PASS" for number in range(1, 11)
    )
    assert checks["CANON-011"].status == "BLOCKED"
    assert checks["CANON-012"].status == "PASS"
    assert all(checks[f"CANON-{number:03d}"].status == "PASS" for number in range(13, 19))


def test_explicit_reconciliation_checks_fail_when_floor_or_child_membership_drifts(
    canonical_layout, profile
):
    blocks = []
    for block in canonical_layout.blocks:
        if block.component_id == "ADMIN_ACOLHIMENTO":
            rooms = tuple(
                replace(room, level=2) if room.logical_id == "REQ-01-01" else room
                for room in block.rooms
            )
            block = replace(block, rooms=rooms)
        elif block.component_id == "CHILD_SECTOR":
            block = replace(
                block,
                rooms=tuple(room for room in block.rooms if room.logical_id != "REQ-03-04"),
            )
        blocks.append(block)
    drifted = replace(canonical_layout, blocks=tuple(blocks))
    checks = _checks_by_id(drifted, profile)

    assert checks["CANON-015"].status == "FAIL"
    assert checks["CANON-018"].status == "FAIL"


def test_administration_qa_requires_board02_ground_floor_support_rooms(
    canonical_layout, profile
):
    blocks = [
        replace(
            block,
            rooms=tuple(
                room
                for room in block.rooms
                if room.logical_id not in {"REQ-05-03", "REQ-05-04"}
            ),
        )
        if block.component_id == "ADMIN_ACOLHIMENTO"
        else block
        for block in canonical_layout.blocks
    ]
    displaced = replace(canonical_layout, blocks=tuple(blocks))

    assert _checks_by_id(displaced, profile)["CANON-015"].status == "FAIL"


def test_four_board_qa_rejects_missing_or_unbound_fourth_reference(canonical_layout, profile):
    params = {
        **canonical_layout.parameters,
        "canonical_source_hashes": list(profile.source_hashes[:3]),
    }
    unbound = replace(canonical_layout, parameters=params)

    assert _checks_by_id(unbound, profile)["CANON-013"].status == "FAIL"


def test_curved_service_qa_rejects_a_missing_or_overcounted_courtyard(
    canonical_layout, profile
):
    service = next(
        block for block in canonical_layout.blocks if block.component_id == "SERVICE_CAPACITATION"
    )
    broken = replace(canonical_layout, service_courtyard=service.footprint)

    assert _checks_by_id(broken, profile)["CANON-017"].status == "FAIL"


def test_legacy_single_bar_fails_the_no_bar_and_residential_cluster_checks(
    program, profile
):
    legacy = build_courtyard_layout(program)
    checks = _checks_by_id(legacy, profile)

    assert checks["CANON-001"].status == "FAIL"
    assert checks["CANON-004"].status == "FAIL"
    assert checks["CANON-012"].status == "FAIL"


def test_relative_location_and_program_checks_pass_for_canonical_pavilions(
    canonical_layout, profile
):
    checks = _checks_by_id(canonical_layout, profile)

    for check_id in ("CANON-002", "CANON-005", "CANON-007", "CANON-008", "CANON-009"):
        assert checks[check_id].status == "PASS"


def test_residential_cluster_qa_rejects_communal_pavilion_outside_northeast_quadrant(
    canonical_layout, profile
):
    blocks = []
    for block in canonical_layout.blocks:
        if block.component_id == "RES_PAV_D_COMMUNAL":
            offset = (20.0, -30.0)
            block = replace(
                block,
                footprint=move_geometry(block.footprint, xoff=offset[0], yoff=offset[1]),
                access_point=move_geometry(block.access_point, xoff=offset[0], yoff=offset[1]),
            )
        blocks.append(block)
    misplaced = replace(canonical_layout, blocks=tuple(blocks))

    assert _checks_by_id(misplaced, profile)["CANON-004"].status == "FAIL"


def test_covered_path_qa_rejects_straight_link_geometry(canonical_layout, profile):
    connectors = list(canonical_layout.covered_connectors)
    first = connectors[0]
    connectors[0] = replace(
        first,
        centerline=(first.centerline[0], first.centerline[-1]),
    )
    straight_link = replace(canonical_layout, covered_connectors=tuple(connectors))

    assert _checks_by_id(straight_link, profile)["CANON-006"].status == "FAIL"


def test_visual_gate_requires_all_six_reviewed_stages_and_matching_board_hashes(
    canonical_layout, profile
):
    partial = [
        {"stage": "R04", "status": "PASS", "source_hashes": list(profile.source_hashes)}
    ]
    partial_layout = replace(
        canonical_layout,
        parameters={**canonical_layout.parameters, "visual_regression": partial},
    )
    assert _checks_by_id(partial_layout, profile)["CANON-011"].status == "BLOCKED"

    complete = [
        {"stage": stage, "status": "PASS", "source_hashes": list(profile.source_hashes)}
        for stage in REQUIRED_VISUAL_STAGES
    ]
    complete_layout = replace(
        canonical_layout,
        parameters={**canonical_layout.parameters, "visual_regression": complete},
    )
    assert _checks_by_id(complete_layout, profile)["CANON-011"].status == "PASS"


def test_missing_deviation_register_fails_closed(canonical_layout, profile):
    params = dict(canonical_layout.parameters)
    params.pop("canonical_deviations", None)
    unregistered = replace(canonical_layout, parameters=params)

    assert _checks_by_id(unregistered, profile)["CANON-010"].status == "FAIL"


def test_all_known_board_program_differences_must_be_reconciled(canonical_layout, profile):
    params = {
        **canonical_layout.parameters,
        "canonical_deviations": [],
    }
    unrecorded = replace(canonical_layout, parameters=params)

    assert _checks_by_id(unrecorded, profile)["CANON-010"].status == "FAIL"


def test_program_qa_requires_board02_crosswalk_deviations(canonical_layout, profile):
    deviations = [
        item
        for item in canonical_layout.parameters["canonical_deviations"]
        if not str(item.get("id", "")).startswith("BOARD02-")
    ]
    incomplete = replace(
        canonical_layout,
        parameters={**canonical_layout.parameters, "canonical_deviations": deviations},
    )

    assert _checks_by_id(incomplete, profile)["CANON-010"].status == "FAIL"


def test_deviation_qa_requires_spec_fields_and_current_output_hash(
    canonical_layout, profile
):
    deviations = [
        {
            **item,
            "impact": "",
        }
        if item["id"] == "BOARD02-SEC05-SUPPORT-PLACEMENT"
        else item
        for item in canonical_layout.parameters["canonical_deviations"]
    ]
    malformed = replace(
        canonical_layout,
        parameters={**canonical_layout.parameters, "canonical_deviations": deviations},
    )

    assert _checks_by_id(malformed, profile)["CANON-010"].status == "FAIL"


def test_deviation_qa_rejects_an_output_hash_that_does_not_bind_the_layout(
    canonical_layout, profile
):
    deviations = [
        {**item, "output_hash": "0" * 64}
        if item["id"] == "BOARD02-SEC05-SUPPORT-PLACEMENT"
        else item
        for item in canonical_layout.parameters["canonical_deviations"]
    ]
    mismatched = replace(
        canonical_layout,
        parameters={**canonical_layout.parameters, "canonical_deviations": deviations},
    )

    assert _checks_by_id(mismatched, profile)["CANON-010"].status == "FAIL"


def test_service_qa_rejects_collapsed_campus_and_cargo_accesses(
    canonical_layout, profile
):
    collapsed = replace(
        canonical_layout,
        service_public_access_point=canonical_layout.service_access_point,
    )

    assert _checks_by_id(collapsed, profile)["CANON-017"].status == "FAIL"
