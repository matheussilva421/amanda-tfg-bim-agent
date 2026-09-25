from __future__ import annotations

from copy import copy
from pathlib import Path

import pytest
from pydantic import ValidationError

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import (
    CheckStatus,
    PreflightReport,
    StageCheck,
    StageOperation,
)
from amanda_agent.bim.write_gate import (
    BIM00_REQUIRED_CHECKS,
    Bim00Evidence,
    Bim00GateRefused,
    WriteGateCheck,
    authorize_preacceptance_stage,
)

TARGET = Path(r"C:\synthetic\revit\working\RUN-003-BIM-00-fixture.rvt")
CHECKPOINT = Path(r"C:\synthetic\revit\checkpoints\RUN-003-BIM-00-fixture\checkpoint.rvt")
ANCHOR = Path.home() / ".horizun" / "anchor" / "HZ_ANCHOR_2027.rvt"
SOLUTION = "AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"
APPROVAL = "a" * 64
LAYOUT = "b" * 64
BOARD_HASHES = ("c" * 64, "d" * 64, "e" * 64, "f" * 64)
OFFICIAL_PROGRAM_SHA256 = "9" * 64
REPOSITORY_COMMIT_SHA = "a" * 40
PROJECT_STATE_REVISION = 180
PROJECT_STATE_SHA256 = "8" * 64
NEW_BINDING_CHECKS = (
    "official_program_sha256",
    "repository_commit_sha",
    "project_state_revision",
    "project_state_sha256",
)
EXPECTED_BINDINGS = {
    "official_program_sha256": OFFICIAL_PROGRAM_SHA256,
    "repository_commit_sha": REPOSITORY_COMMIT_SHA,
    "project_state_revision": PROJECT_STATE_REVISION,
    "project_state_sha256": PROJECT_STATE_SHA256,
}


class _Plan:
    def __init__(self, stage: BimStage, operations: list[StageOperation]):
        self.stage = stage
        self.operations = operations
        self.preflight = PreflightReport(
            mode="DETAILED_BIM",
            stage=stage,
            scenario="STUDY",
            checks=[
                StageCheck(name="bim_00", status=CheckStatus.BLOCKED, detail="BIM-00 pending"),
                StageCheck(name="capability", status=CheckStatus.PASS, detail="typed provider verified"),
            ],
            notes=["BIM-00 blocks massing"],
        )

    def model_copy(self, *, update: dict):
        result = copy(self)
        for name, value in update.items():
            setattr(result, name, value)
        return result


def _evidence(**updates) -> Bim00Evidence:
    values = {
        "gate_id": "BIM-00",
        "status": CheckStatus.PASS,
        "target_path": TARGET,
        "target_sha256": "f" * 64,
        "checkpoint_path": CHECKPOINT,
        "checkpoint_sha256": "f" * 64,
        "solution_id": SOLUTION,
        "approval_hash": APPROVAL,
        "layout_hash": LAYOUT,
        "canonical_source_hashes": BOARD_HASHES,
        **EXPECTED_BINDINGS,
        "historical_r12_sha256": "1" * 64,
        "capability_registry_sha256": "2" * 64,
        "revit_build": "27.2.0.39",
        "provider_status": "HEALTHY",
        "active_document_path": TARGET,
        "open_document_count": 1,
        "open_document_paths": [TARGET],
        "other_clients_connected": 0,
        "checks": [WriteGateCheck(name=name, status=CheckStatus.PASS, evidence=f"verified {name}") for name in BIM00_REQUIRED_CHECKS],
    }
    values.update(updates)
    return Bim00Evidence(**values)


def _plan(stage: BimStage) -> _Plan:
    operation = StageOperation(
        stage=stage,
        logical_id="CANONICAL-MASS-ADMIN",
        semantic_capability="revit.create_mass",
        blocked_by=["BIM-00", "CANONICAL_GEOMETRIC_ACCEPTANCE"],
        preferred_provider="horizun-revit-mcp",
    )
    return _Plan(stage, [operation])


def _authorize(plan: _Plan, evidence: Bim00Evidence, **expected_updates):
    expected = {**EXPECTED_BINDINGS, **expected_updates}
    return authorize_preacceptance_stage(
        plan,
        evidence,
        target_path=TARGET,
        solution_id=SOLUTION,
        approval_hash=APPROVAL,
        layout_hash=LAYOUT,
        canonical_source_hashes=BOARD_HASHES,
        **expected,
    )


def test_bim00_evidence_requires_exactly_four_canonical_board_hashes():
    with pytest.raises(ValidationError):
        _evidence(canonical_source_hashes=BOARD_HASHES[:3])


def test_bim00_required_checks_cover_each_new_binding():
    assert set(NEW_BINDING_CHECKS) <= set(BIM00_REQUIRED_CHECKS)


@pytest.mark.parametrize("field", NEW_BINDING_CHECKS)
def test_bim00_evidence_requires_each_new_binding(field):
    values = _evidence().model_dump()
    values.pop(field)

    with pytest.raises(ValidationError):
        Bim00Evidence(**values)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    (
        ("official_program_sha256", "A" * 64),
        ("official_program_sha256", "9" * 63),
        ("repository_commit_sha", "A" * 40),
        ("repository_commit_sha", "a" * 39),
        ("repository_commit_sha", "g" * 40),
        ("project_state_revision", -1),
        ("project_state_revision", True),
        ("project_state_sha256", "G" * 64),
        ("project_state_sha256", "8" * 63),
    ),
)
def test_bim00_evidence_rejects_malformed_new_bindings(field, invalid_value):
    values = _evidence().model_dump()
    values[field] = invalid_value

    with pytest.raises(ValidationError):
        Bim00Evidence(**values)


@pytest.mark.parametrize("check_name", NEW_BINDING_CHECKS)
def test_bim00_refuses_missing_new_binding_check(check_name):
    evidence = _evidence()
    evidence.checks = [check for check in evidence.checks if check.name != check_name]

    with pytest.raises(Bim00GateRefused, match="missing required BIM-00 checks"):
        _authorize(_plan(BimStage.R04), evidence)


@pytest.mark.parametrize("check_name", NEW_BINDING_CHECKS)
def test_bim00_refuses_blocked_new_binding_check(check_name):
    evidence = _evidence()
    evidence.checks = [
        WriteGateCheck(
            name=check.name,
            status=CheckStatus.BLOCKED if check.name == check_name else check.status,
            evidence=check.evidence,
        )
        for check in evidence.checks
    ]

    with pytest.raises(Bim00GateRefused, match="not all required checks passed"):
        _authorize(_plan(BimStage.R04), evidence)


def test_valid_bim00_releases_only_the_r03_r04_bim00_blocker():
    plan = _plan(BimStage.R04)

    released = _authorize(plan, _evidence())

    assert released.operations[0].blocked_by == ["CANONICAL_GEOMETRIC_ACCEPTANCE"]
    assert released.preflight.get("bim_00").status is CheckStatus.PASS
    assert released.preflight.failures == []


def test_bim00_accepts_target_with_only_the_bridge_owned_anchor_open():
    evidence = _evidence(
        open_document_count=2,
        open_document_paths=[TARGET, ANCHOR],
    )

    released = _authorize(_plan(BimStage.R04), evidence)

    assert released.operations[0].blocked_by == ["CANONICAL_GEOMETRIC_ACCEPTANCE"]


def test_bim00_refuses_any_other_open_document():
    evidence = _evidence(
        open_document_count=2,
        open_document_paths=[TARGET, Path(r"C:\project\other.rvt")],
    )

    with pytest.raises(Bim00GateRefused, match="bridge-owned anchor"):
        _authorize(_plan(BimStage.R04), evidence)


def test_bim00_refuses_duplicate_or_incomplete_open_document_paths():
    for changes in (
        {"open_document_paths": [TARGET, TARGET], "open_document_count": 2},
        {"open_document_paths": [ANCHOR], "open_document_count": 1},
        {"open_document_paths": [TARGET, ANCHOR], "open_document_count": 1},
    ):
        with pytest.raises(Bim00GateRefused):
            _authorize(_plan(BimStage.R04), _evidence(**changes))


def test_bim00_refuses_missing_or_blocked_checks():
    checks = [WriteGateCheck(name=name, status=CheckStatus.PASS, evidence="readback") for name in BIM00_REQUIRED_CHECKS]
    checks[0] = WriteGateCheck(name=checks[0].name, status=CheckStatus.BLOCKED, evidence="path unresolved")
    evidence = _evidence(status=CheckStatus.BLOCKED, checks=checks)

    with pytest.raises(Bim00GateRefused, match="not all required checks passed"):
        _authorize(_plan(BimStage.R04), evidence)


def test_bim00_is_bound_to_target_solution_layout_and_board_hashes():
    evidence = _evidence()
    for mismatch in (
        {"target_path": TARGET.with_name("other.rvt")},
        {"solution_id": "AMANDA-RUN-001-S01"},
        {"approval_hash": "9" * 64},
        {"layout_hash": "8" * 64},
        {"canonical_source_hashes": ("7" * 64, *BOARD_HASHES[1:])},
    ):
        changed = evidence.model_copy(update=mismatch)
        with pytest.raises(Bim00GateRefused):
            _authorize(_plan(BimStage.R04), changed)


@pytest.mark.parametrize(
    ("binding", "mismatched_expected"),
    (
        ("official_program_sha256", "7" * 64),
        ("repository_commit_sha", "b" * 40),
        ("project_state_revision", PROJECT_STATE_REVISION + 1),
        ("project_state_sha256", "6" * 64),
    ),
)
def test_bim00_refuses_each_new_binding_when_expected_value_differs(
    binding, mismatched_expected
):
    with pytest.raises(Bim00GateRefused):
        _authorize(
            _plan(BimStage.R04),
            _evidence(),
            **{binding: mismatched_expected},
        )


@pytest.mark.parametrize(
    ("binding", "invalid_expected"),
    (
        ("official_program_sha256", "A" * 64),
        ("repository_commit_sha", "a" * 39),
        ("project_state_revision", -1),
        ("project_state_revision", True),
        ("project_state_sha256", "G" * 64),
    ),
)
def test_bim00_refuses_malformed_expected_new_binding(binding, invalid_expected):
    with pytest.raises(Bim00GateRefused):
        _authorize(
            _plan(BimStage.R04),
            _evidence(),
            **{binding: invalid_expected},
        )


def test_bim00_requires_explicit_expected_values_for_new_bindings():
    with pytest.raises(TypeError, match="official_program_sha256"):
        authorize_preacceptance_stage(
            _plan(BimStage.R04),
            _evidence(),
            target_path=TARGET,
            solution_id=SOLUTION,
            approval_hash=APPROVAL,
            layout_hash=LAYOUT,
            canonical_source_hashes=BOARD_HASHES,
        )


def test_bim00_cannot_release_r05_detailing_or_geometry_acceptance_blocker():
    with pytest.raises(Bim00GateRefused, match="only R03/R04"):
        _authorize(_plan(BimStage.R05), _evidence())


def test_checkpoint_and_target_must_match_the_saved_active_document():
    evidence = _evidence(checkpoint_sha256="0" * 64)
    with pytest.raises(Bim00GateRefused, match="checkpoint hash"):
        _authorize(_plan(BimStage.R04), evidence)
