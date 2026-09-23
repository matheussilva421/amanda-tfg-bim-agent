from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

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
            "canonical/01_implantacao_geral_canonica.png",
            "canonical/02_bloco_residencial_canonico.png",
            "canonical/03_bloco_administrativo_canonico.png",
        ),
        source_hashes=("a" * 64, "b" * 64, "c" * 64),
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

    assert set(checks) == {f"CANON-{number:03d}" for number in range(1, 13)}
    assert all(
        checks[f"CANON-{number:03d}"].status == "PASS" for number in range(1, 11)
    )
    assert checks["CANON-011"].status == "BLOCKED"
    assert checks["CANON-012"].status == "PASS"


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
