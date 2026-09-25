from __future__ import annotations

import json
from pathlib import Path

import pytest

import amanda_agent.production.selection as selection_module
from amanda_agent.design.architectural_layout import build_courtyard_layout
from amanda_agent.design.canonical_pavilion_layout import (
    build_canonical_pavilion_layout,
)
from amanda_agent.design.canonical_reference import CanonicalReferenceProfile
from amanda_agent.production.selection import (
    LEGACY_SELECTION_SOLUTION_ID,
    PARTI_DECISION_ID,
    SELECTION_ARCHETYPE,
    SELECTION_DECISION_ID,
    SELECTION_SOLUTION_ID,
    STALE_SELECTION_SOLUTION_ID,
    SelectionError,
    build_selection,
    legacy_selection_history,
)

ROOT = Path(__file__).resolve().parents[2]
PROGRAM_PATH = ROOT / "project/requirements/program.json"
CURRENT_IMAGES = (
    "canonical/01_implantacao.png",
    "canonical/02_administrativo.png",
    "canonical/03_residencial.png",
    "canonical/04_servicos.png",
)


def _profile(hashes: tuple[str, ...] = ("a" * 64, "b" * 64, "c" * 64, "d" * 64)):
    return CanonicalReferenceProfile(
        status="CANONICAL_DESIGN_REFERENCE",
        supersedes=("AMANDA-RUN-001-S01", "COURTYARD_DOUBLE_LOADED_BAR"),
        canonical_images=CURRENT_IMAGES,
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


def test_s02_remains_stale_and_cannot_become_the_current_selection(program):
    profile = _profile()

    assert SELECTION_SOLUTION_ID is None
    assert STALE_SELECTION_SOLUTION_ID == "AMANDA-RUN-002-PAVILION-S02"
    assert SELECTION_ARCHETYPE == "CANONICAL_PAVILION_CLUSTER"
    assert PARTI_DECISION_ID == "DEC-CANONICAL-PARTI-002"
    assert SELECTION_DECISION_ID == "DEC-CANONICAL-DETAIL-004"
    assert STALE_SELECTION_SOLUTION_ID != LEGACY_SELECTION_SOLUTION_ID
    with pytest.raises(SelectionError, match="STALE_BY_CANONICAL_REFERENCE_EXPANSION"):
        _select(program, profile)


def test_s02_stays_rejected_even_if_some_caller_reactivates_its_constant(
    program, monkeypatch
):
    monkeypatch.setattr(
        selection_module, "SELECTION_SOLUTION_ID", STALE_SELECTION_SOLUTION_ID
    )

    with pytest.raises(SelectionError, match="STALE_BY_CANONICAL_REFERENCE_EXPANSION"):
        _select(program, _profile())


@pytest.mark.parametrize(
    "superseded_solution_id",
    [LEGACY_SELECTION_SOLUTION_ID, "AMANDA-RUN-002-PAVILION-S01"],
)
def test_superseded_linear_solution_id_cannot_authorize_canonical_selection(
    program, monkeypatch, superseded_solution_id
):
    monkeypatch.setattr(
        selection_module, "SELECTION_SOLUTION_ID", superseded_solution_id
    )

    with pytest.raises(SelectionError, match="superseded linear solution identity"):
        _select(program, _profile())


def test_legacy_selection_history_is_non_executable_and_not_geometry_reusable():
    history = legacy_selection_history()

    assert history["solution_id"] == LEGACY_SELECTION_SOLUTION_ID
    assert history["status"] == "SUPERSEDED_BY_USER_DIRECTION"
    assert history["solution_status"] == "SUPERSEDED"
    assert history["superseded_by"] == STALE_SELECTION_SOLUTION_ID
    assert history["geometry_reuse_allowed"] is False


def test_active_selection_builder_rejects_a_legacy_linear_layout(program):
    legacy_layout = build_courtyard_layout(program)

    with pytest.raises(SelectionError, match="legacy linear layouts"):
        build_selection(
            legacy_layout,
            generation_run="AMANDA-RUN-001",
            timestamp="2026-09-22T12:00:00Z",
        )


def test_layout_builder_refuses_a_three_board_profile(program):
    profile = _profile(("a" * 64, "b" * 64, "c" * 64))

    with pytest.raises(ValueError, match="all four canonical board hashes"):
        build_canonical_pavilion_layout(program, profile)


def test_selection_rejects_non_sha256_canonical_source_hashes(program):
    invalid_profile = _profile(("a" * 64, "b" * 64, "c" * 64, "g" * 64))

    with pytest.raises(SelectionError, match="invalid canonical board hash"):
        _select(program, invalid_profile)
