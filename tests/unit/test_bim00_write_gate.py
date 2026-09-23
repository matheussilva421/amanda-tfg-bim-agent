from __future__ import annotations

from copy import copy
from pathlib import Path

import pytest

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

TARGET = Path(r"C:\project\revit\production\working\AMANDA-RUN-002-PAVILION-S02.rvt")
CHECKPOINT = Path(r"C:\project\revit\production\checkpoints\AMANDA-RUN-002-PAVILION-S02\R01.rvt")
ANCHOR = Path.home() / ".horizun" / "anchor" / "HZ_ANCHOR_2027.rvt"
SOLUTION = "AMANDA-RUN-002-PAVILION-S02"
APPROVAL = "a" * 64
LAYOUT = "b" * 64
BOARD_HASHES = ("c" * 64, "d" * 64, "e" * 64)


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


def test_valid_bim00_releases_only_the_r03_r04_bim00_blocker():
    plan = _plan(BimStage.R04)

    released = authorize_preacceptance_stage(
        plan,
        _evidence(),
        target_path=TARGET,
        solution_id=SOLUTION,
        approval_hash=APPROVAL,
        layout_hash=LAYOUT,
        canonical_source_hashes=BOARD_HASHES,
    )

    assert released.operations[0].blocked_by == ["CANONICAL_GEOMETRIC_ACCEPTANCE"]
    assert released.preflight.get("bim_00").status is CheckStatus.PASS
    assert released.preflight.failures == []


def test_bim00_accepts_target_with_only_the_bridge_owned_anchor_open():
    evidence = _evidence(
        open_document_count=2,
        open_document_paths=[TARGET, ANCHOR],
    )

    released = authorize_preacceptance_stage(
        _plan(BimStage.R04),
        evidence,
        target_path=TARGET,
        solution_id=SOLUTION,
        approval_hash=APPROVAL,
        layout_hash=LAYOUT,
        canonical_source_hashes=BOARD_HASHES,
    )

    assert released.operations[0].blocked_by == ["CANONICAL_GEOMETRIC_ACCEPTANCE"]


def test_bim00_refuses_any_other_open_document():
    evidence = _evidence(
        open_document_count=2,
        open_document_paths=[TARGET, Path(r"C:\project\other.rvt")],
    )

    with pytest.raises(Bim00GateRefused, match="bridge-owned anchor"):
        authorize_preacceptance_stage(
            _plan(BimStage.R04),
            evidence,
            target_path=TARGET,
            solution_id=SOLUTION,
            approval_hash=APPROVAL,
            layout_hash=LAYOUT,
            canonical_source_hashes=BOARD_HASHES,
        )


def test_bim00_refuses_duplicate_or_incomplete_open_document_paths():
    for changes in (
        {"open_document_paths": [TARGET, TARGET], "open_document_count": 2},
        {"open_document_paths": [ANCHOR], "open_document_count": 1},
        {"open_document_paths": [TARGET, ANCHOR], "open_document_count": 1},
    ):
        with pytest.raises(Bim00GateRefused):
            authorize_preacceptance_stage(
                _plan(BimStage.R04),
                _evidence(**changes),
                target_path=TARGET,
                solution_id=SOLUTION,
                approval_hash=APPROVAL,
                layout_hash=LAYOUT,
                canonical_source_hashes=BOARD_HASHES,
            )


def test_bim00_refuses_missing_or_blocked_checks():
    checks = [WriteGateCheck(name=name, status=CheckStatus.PASS, evidence="readback") for name in BIM00_REQUIRED_CHECKS]
    checks[0] = WriteGateCheck(name=checks[0].name, status=CheckStatus.BLOCKED, evidence="path unresolved")
    evidence = _evidence(status=CheckStatus.BLOCKED, checks=checks)

    with pytest.raises(Bim00GateRefused, match="not all required checks passed"):
        authorize_preacceptance_stage(
            _plan(BimStage.R04), evidence,
            target_path=TARGET, solution_id=SOLUTION, approval_hash=APPROVAL,
            layout_hash=LAYOUT, canonical_source_hashes=BOARD_HASHES,
        )


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
            authorize_preacceptance_stage(
                _plan(BimStage.R04), changed,
                target_path=TARGET, solution_id=SOLUTION, approval_hash=APPROVAL,
                layout_hash=LAYOUT, canonical_source_hashes=BOARD_HASHES,
            )


def test_bim00_cannot_release_r05_detailing_or_geometry_acceptance_blocker():
    with pytest.raises(Bim00GateRefused, match="only R03/R04"):
        authorize_preacceptance_stage(
            _plan(BimStage.R05), _evidence(),
            target_path=TARGET, solution_id=SOLUTION, approval_hash=APPROVAL,
            layout_hash=LAYOUT, canonical_source_hashes=BOARD_HASHES,
        )


def test_checkpoint_and_target_must_match_the_saved_active_document():
    evidence = _evidence(checkpoint_sha256="0" * 64)
    with pytest.raises(Bim00GateRefused, match="checkpoint hash"):
        authorize_preacceptance_stage(
            _plan(BimStage.R04), evidence,
            target_path=TARGET, solution_id=SOLUTION, approval_hash=APPROVAL,
            layout_hash=LAYOUT, canonical_source_hashes=BOARD_HASHES,
        )
