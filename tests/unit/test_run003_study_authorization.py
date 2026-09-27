"""P6 grants a narrowly bound normalized-study continuation, not BIM eligibility."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT
    / "revit"
    / "production"
    / "evidence"
    / "AMANDA-RUN-003-R04"
    / "r04-spatial-model-evidence.json"
)
SOLUTION_ID = "AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"


def _api():
    try:
        return importlib.import_module("amanda_agent.production.run003_study")
    except ModuleNotFoundError as exc:
        pytest.fail(f"RUN-003 post-P6 authorization gate is missing: {exc}")


def test_current_p6_grant_is_source_bound_and_limited_to_r05_through_r13():
    api = _api()

    grant = api.load_run003_study_authorization(ROOT)

    assert grant.solution_id == SOLUTION_ID
    assert grant.status == "VERIFIED_P6_STUDY_CONTINUATION"
    assert grant.start_stage == "R05"
    assert grant.max_stage == "R13"
    assert grant.bim_eligible is False
    assert len(grant.canonical_board_sha256) == 4
    assert grant.official_program_sha256 == (
        "11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17"
    )
    assert grant.checkpoint_sha256 == (
        "8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326"
    )
    assert grant.approval_hash == (
        "961b6edc95bd097fe600b2ce968aacdf28876bf3c587b788a0b2358baddfc0b0"
    )
    assert grant.layout_hash == (
        "7fde3e34a162167ce27fe2e3158a38f446882816a7c81bb326d486bdfaaae2e2"
    )
    assert grant.target_path == (
        "revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt"
    )
    assert grant.storey_element_ids == {1: 311, 2: 694}
    assert grant.administrative_floor_element_ids == {
        "R04-ADMIN-FLOOR-L1": 331163,
        "R04-ADMIN-FLOOR-L2": 331170,
    }
    assert grant.mass_bounding_boxes_m["ADMIN_ACOLHIMENTO"] == {
        "min": (-5.0, -52.00000000000001, 0.0),
        "max": (5.0, -32.0, 6.4),
    }
    assert grant.permits_target_path(ROOT / grant.target_path) is True
    assert grant.permits_target_path(ROOT / "revit/production/archive/linear-r12-superseded.rvt") is False
    assert grant.permits_stage("R05") is True
    assert grant.permits_stage("R13") is True
    assert grant.permits_stage("R04") is False
    assert grant.permits_stage("R14") is False
    assert grant.wall_elevations_m("ADMIN_ACOLHIMENTO", (1, 2)) == (
        (0, 0.0, 4.0),
        (1, 4.0, 6.4),
    )
    assert grant.wall_elevations_m("RES_PAV_A", (1,)) == ((0, 0.0, 3.2),)


def test_resume_loads_the_exact_p6_bound_selection_artifacts():
    api = _api()
    grant = api.load_run003_study_authorization(ROOT)

    selection = api.load_run003_study_selection(ROOT, grant)

    assert selection.solution.solution_id == grant.solution_id
    assert selection.solution.approval_hash == grant.approval_hash
    assert selection.approval_hash == grant.approval_hash
    assert selection.layout_hash == grant.layout_hash


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda data: data["p6_acceptance"].update(status="PENDING"), "P6 status"),
        (
            lambda data: data["p6_acceptance"]["canonical_board_sha256"].__setitem__(0, "0" * 64),
            "canonical board",
        ),
        (
            lambda data: data["p6_acceptance"].update(solution_id="AMANDA-RUN-002-PAVILION-S02"),
            "solution ID",
        ),
        (
            lambda data: data["p6_acceptance"].update(room_area_readback_deferred_to="R06"),
            "R08",
        ),
        (
            lambda data: data["readback"]["administrative_storey_levels"]["2"].update(
                level_id=999
            ),
            "level IDs",
        ),
    ],
)
def test_stale_or_mismatched_p6_receipt_fails_closed(tmp_path, mutate, message):
    api = _api()
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    mutate(evidence)
    altered = tmp_path / "p6-evidence.json"
    altered.write_text(json.dumps(evidence), encoding="utf-8")

    with pytest.raises(api.Run003StudyAuthorizationError, match=message):
        api.load_run003_study_authorization(ROOT, evidence_path=altered)


def test_run003_grant_does_not_promote_canonical_identity_or_authorize_other_targets():
    api = _api()

    grant = api.load_run003_study_authorization(ROOT)

    assert grant.identity_bim_eligible is False
    assert grant.identity_revit_write_authorized is False
    assert grant.permits_target(SOLUTION_ID) is True
    assert grant.permits_target("AMANDA-RUN-002-PAVILION-S02") is False
    assert grant.permits_target("AMANDA-RUN-001-S01") is False
