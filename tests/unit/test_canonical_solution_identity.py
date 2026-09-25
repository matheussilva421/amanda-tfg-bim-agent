from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

import amanda_agent.production.selection as selection_module
from amanda_agent.design.canonical_reference import CanonicalReferenceProfile
from amanda_agent.production.canonical_identity import (
    IDENTITY_ARTIFACT_PATH,
    CanonicalIdentityError,
    CanonicalSolutionIdentity,
    assign_canonical_solution_identity,
    write_canonical_solution_identity,
)

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_SOLUTION_IDS = (
    "AMANDA-RUN-002-PAVILION-S02",
    "AMANDA-RUN-001-S01",
    "AMANDA-RUN-002-PAVILION-S01",
    "AMANDA-RUN-001-F01",
    "AMANDA-RUN-001-F02",
    "AMANDA-RUN-001-S01-R12",
)


def _resign_identity_payload(payload: dict) -> CanonicalSolutionIdentity:
    material = {
        key: payload[key]
        for key in (
            "canonical_boards",
            "program_source",
            "reconciliation_id",
            "reconciliation_report",
        )
    }
    encoded = json.dumps(
        material, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    fingerprint = hashlib.sha256(encoded).hexdigest()
    payload["identity_fingerprint"] = fingerprint
    payload["solution_id"] = (
        "AMANDA-RUN-003-PAVILION-CANONICAL-" + fingerprint[:12].upper()
    )
    return CanonicalSolutionIdentity.model_validate(payload)


def test_identity_binds_exact_four_canonical_boards_and_official_program():
    identity = assign_canonical_solution_identity(ROOT)
    profile = CanonicalReferenceProfile.load(ROOT)
    program = json.loads(
        (ROOT / "project/requirements/program.json").read_text(encoding="utf-8")
    )

    assert len(identity.canonical_boards) == 4
    assert tuple(item.path for item in identity.canonical_boards) == tuple(
        f"docs/source/{image}" for image in profile.canonical_images
    )
    assert tuple(item.sha256 for item in identity.canonical_boards) == profile.source_hashes
    assert identity.program_source.path == "docs/source/programa_necessidades.pdf"
    assert identity.program_source.sha256 == hashlib.sha256(
        (ROOT / identity.program_source.path).read_bytes()
    ).hexdigest()
    assert identity.program_source.sha256 == program["baseline"]["source_sha256"]


def test_identity_binds_the_p1_t01_reconciliation_artifact():
    identity = assign_canonical_solution_identity(ROOT)
    report_path = ROOT / identity.reconciliation_report.path

    assert identity.reconciliation_id == "P1-T01"
    assert identity.reconciliation_report.path == (
        "docs/reports/P1-T01-four-board-reconciliation.md"
    )
    assert identity.reconciliation_report.sha256 == hashlib.sha256(
        report_path.read_bytes()
    ).hexdigest()


@pytest.mark.parametrize("forbidden_id", FORBIDDEN_SOLUTION_IDS)
def test_identity_model_rejects_stale_and_linear_solution_ids(forbidden_id: str):
    identity = assign_canonical_solution_identity(ROOT)
    payload = identity.model_dump(mode="json")

    with pytest.raises(ValueError):
        CanonicalSolutionIdentity.model_validate(
            payload | {"solution_id": forbidden_id}
        )


def test_identity_is_new_and_does_not_authorize_selection_or_bim():
    identity = assign_canonical_solution_identity(ROOT)

    assert identity.solution_id not in FORBIDDEN_SOLUTION_IDS
    assert identity.solution_id.startswith("AMANDA-RUN-003-PAVILION-CANONICAL-")
    assert identity.selected_design is None
    assert identity.approval_hash is None
    assert identity.bim_eligible is False
    assert identity.bim00_authorized is False
    assert identity.revit_write_authorized is False
    assert selection_module.SELECTION_SOLUTION_ID is None


def test_identity_requires_all_four_board_bindings_and_program_source_hash():
    identity = assign_canonical_solution_identity(ROOT)
    payload = identity.model_dump(mode="json")

    with pytest.raises(ValueError):
        CanonicalSolutionIdentity.model_validate(
            payload | {"canonical_boards": payload["canonical_boards"][:3]}
        )

    missing_program_source = dict(payload)
    missing_program_source.pop("program_source")
    with pytest.raises(ValueError):
        CanonicalSolutionIdentity.model_validate(missing_program_source)

    missing_program_hash = dict(payload)
    missing_program_hash["program_source"] = {"path": "docs/source/programa_necessidades.pdf"}
    with pytest.raises(ValueError):
        CanonicalSolutionIdentity.model_validate(missing_program_hash)

    wrong_program_hash = dict(payload)
    wrong_program_hash["program_source"] = {
        "path": "docs/source/programa_necessidades.pdf",
        "sha256": "0" * 64,
    }
    with pytest.raises(ValueError, match="adopted official program PDF hash"):
        CanonicalSolutionIdentity.model_validate(wrong_program_hash)


def test_identity_generation_is_deterministic_and_matches_persisted_artifact():
    first = assign_canonical_solution_identity(ROOT)
    second = assign_canonical_solution_identity(ROOT)
    persisted = yaml.safe_load((ROOT / IDENTITY_ARTIFACT_PATH).read_text(encoding="utf-8"))

    assert first == second
    assert persisted == first.model_dump(mode="json")
    assert not {
        "geometry",
        "layout_hash",
        "selection_decision",
        "bim_authorization",
    }.intersection(persisted)


def test_identity_writer_is_idempotent_and_refuses_conflicting_replacement():
    identity = assign_canonical_solution_identity(ROOT)
    first_path = write_canonical_solution_identity(ROOT, identity)
    first_bytes = first_path.read_bytes()

    second_path = write_canonical_solution_identity(ROOT, identity)

    assert second_path == first_path
    assert second_path.read_bytes() == first_bytes
    tampered = identity.model_copy(update={"identity_fingerprint": "0" * 64})
    with pytest.raises(ValueError, match="identity fingerprint"):
        write_canonical_solution_identity(ROOT, tampered)
    assert first_path.read_bytes() == first_bytes


@pytest.mark.parametrize("source_kind", ["board", "reconciliation"])
def test_identity_writer_rejects_self_consistent_hashes_that_do_not_match_live_sources(
    source_kind: str,
):
    identity = assign_canonical_solution_identity(ROOT)
    payload = identity.model_dump(mode="json")
    if source_kind == "board":
        payload["canonical_boards"][0]["sha256"] = "f" * 64
    else:
        payload["reconciliation_report"]["sha256"] = "e" * 64
    incorrect_but_self_consistent = _resign_identity_payload(payload)

    with pytest.raises(
        CanonicalIdentityError, match="does not match the current source bindings"
    ):
        write_canonical_solution_identity(ROOT, incorrect_but_self_consistent)

    assert (ROOT / IDENTITY_ARTIFACT_PATH).read_bytes() == yaml.safe_dump(
        identity.model_dump(mode="json"), allow_unicode=True, sort_keys=False
    ).encode("utf-8")
