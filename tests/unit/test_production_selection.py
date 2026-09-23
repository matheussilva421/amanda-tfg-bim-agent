from __future__ import annotations

import json
from pathlib import Path

import pytest

from amanda_agent.design.architectural_layout import build_courtyard_layout
from amanda_agent.design.canonical_pavilion_layout import (
    build_canonical_pavilion_layout,
)
from amanda_agent.design.canonical_reference import CanonicalReferenceProfile
from amanda_agent.production.selection import (
    LEGACY_SELECTION_SOLUTION_ID,
    SELECTION_ARCHETYPE,
    SELECTION_SOLUTION_ID,
    SelectionError,
    build_selection,
    legacy_selection_history,
)
from amanda_agent.requirements.decisions import SelectionAuthority

ROOT = Path(__file__).resolve().parents[2]
PROGRAM_PATH = ROOT / "project/requirements/program.json"


def _profile(hashes: tuple[str, str, str] = ("a" * 64, "b" * 64, "c" * 64)):
    return CanonicalReferenceProfile(
        status="CANONICAL_DESIGN_REFERENCE",
        supersedes=("AMANDA-RUN-001-S01", "COURTYARD_DOUBLE_LOADED_BAR"),
        canonical_images=(
            "canonical/01_implantacao_geral_canonica.png",
            "canonical/02_bloco_residencial_canonico.png",
            "canonical/03_bloco_administrativo_canonico.png",
        ),
        source_hashes=hashes,
        data={
            "program": {
                "people": 20,
                "net_internal_m2": 626.0,
                "external_programmed_m2": 260.0,
                "enclosed_estimate_m2": [783.0, 814.0],
                "covered_estimate_m2": [850.0, 950.0],
            },
            "required_parti": {
                "single_linear_bar_allowed": False,
                "admin_public_edge": True,
                "admin_storeys_target": 2,
                "residential_cluster": {
                    "required": True,
                    "pavilion_count_target": 4,
                    "sleeping_pavilions_target": 3,
                    "communal_pavilions_target": 1,
                    "central_garden_required": True,
                },
                "child_sector_green_interface": True,
                "service_block_separate": True,
                "service_access_separate": True,
                "covered_external_paths_required": True,
                "landscape_is_program": True,
            },
        },
    )


@pytest.fixture(scope="module")
def program() -> dict:
    return json.loads(PROGRAM_PATH.read_text(encoding="utf-8"))


def _select(program, profile):
    layout = build_canonical_pavilion_layout(program, profile)
    return build_selection(
        layout,
        profile=profile,
        generation_run="AMANDA-RUN-002-PAVILION",
        timestamp="2026-09-22T12:00:00Z",
    )


def test_active_selection_is_the_user_directed_canonical_pavilion_parti():
    assert SELECTION_SOLUTION_ID == "AMANDA-RUN-002-PAVILION-S01"
    assert SELECTION_ARCHETYPE == "CANONICAL_PAVILION_CLUSTER"
    assert SELECTION_SOLUTION_ID != LEGACY_SELECTION_SOLUTION_ID


def test_selection_records_parti_authority_and_delegated_detail_separately(program):
    profile = _profile()
    selection = _select(program, profile)

    assert (
        selection.parti_decision.selection_authority is SelectionAuthority.USER_DIRECTED
    )
    assert selection.decision.selection_authority is SelectionAuthority.AGENT_DELEGATED
    assert selection.solution.selection_authority is SelectionAuthority.AGENT_DELEGATED
    assert selection.solution.solution_id == SELECTION_SOLUTION_ID
    assert selection.solution.archetype == SELECTION_ARCHETYPE
    assert selection.solution.bim_eligible is False
    assert selection.solution.geometry["parti_selection_authority"] == "USER_DIRECTED"
    assert (
        selection.solution.geometry["detailed_variant_authority"] == "AGENT_DELEGATED"
    )
    assert selection.solution.geometry["canonical_source_hashes"] == list(
        profile.source_hashes
    )


def test_changing_any_canonical_board_hash_changes_selection_approval_hashes(program):
    initial = _select(program, _profile())
    changed_profile = _profile(("d" * 64, "b" * 64, "c" * 64))
    changed = _select(program, changed_profile)

    assert initial.parti_decision.approval_hash != changed.parti_decision.approval_hash
    assert initial.decision.approval_hash != changed.decision.approval_hash
    assert initial.solution.approval_hash != changed.solution.approval_hash


def test_superseded_linear_selection_remains_available_as_history():
    history = legacy_selection_history()

    assert history["solution_id"] == "AMANDA-RUN-001-S01"
    assert history["status"] == "SUPERSEDED_BY_USER_DIRECTION"
    assert history["solution_status"] == "SUPERSEDED"
    assert history["superseded_by"] == SELECTION_SOLUTION_ID
    assert history["selection_authority"] == "AGENT_DELEGATED"
    assert history["parti_selection_authority"] == "USER_DIRECTED"


def test_active_selection_builder_rejects_a_legacy_linear_layout(program):
    legacy_layout = build_courtyard_layout(program)

    with pytest.raises(SelectionError, match="legacy linear layout"):
        build_selection(
            legacy_layout,
            generation_run="AMANDA-RUN-001",
            timestamp="2026-09-22T12:00:00Z",
        )


def test_selection_rejects_non_sha256_canonical_source_hashes(program):
    invalid_profile = _profile(("g" * 64, "b" * 64, "c" * 64))

    with pytest.raises(SelectionError, match="invalid canonical board hash"):
        _select(program, invalid_profile)
