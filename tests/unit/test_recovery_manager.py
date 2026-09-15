from pathlib import Path

import pytest

from amanda_agent.bim.checkpoints import CheckpointManager
from amanda_agent.recovery.manager import (
    RecoveryDecision,
    RecoveryPlanningError,
    RecoveryState,
    RecoveryStepKind,
    build_recovery_plan,
    select_checkpoint,
)


def _checkpoint(root: Path, name: str, content: bytes, stage: str):
    source = root / f"working-{name}.rvt"
    target = root / f"{name}.rvt"
    source.write_bytes(content)
    return CheckpointManager().create_checkpoint(source, target, stage=stage)


def test_crashed_state_selects_latest_verified_pass_checkpoint(tmp_path: Path):
    earlier = _checkpoint(tmp_path, "R01", b"one", "R01")
    later = _checkpoint(tmp_path, "R02", b"two", "R02")

    selected = select_checkpoint(
        [earlier.manifest_path, later.manifest_path],
        state=RecoveryState.CRASHED,
    )

    assert selected.manifest_path == later.manifest_path


def test_corrupt_latest_checkpoint_is_skipped_for_earlier_verified_checkpoint(
    tmp_path: Path,
):
    earlier = _checkpoint(tmp_path, "R01", b"one", "R01")
    later = _checkpoint(tmp_path, "R02", b"two", "R02")
    later.checkpoint_path.write_bytes(b"tampered")

    selected = select_checkpoint(
        [later.manifest_path, earlier.manifest_path],
        state=RecoveryState.CRASHED,
    )

    assert selected.manifest_path == earlier.manifest_path


def test_interrupted_mutation_never_gets_a_blind_retry(tmp_path: Path):
    checkpoint = _checkpoint(tmp_path, "R02", b"known-good", "R02")

    plan = build_recovery_plan(
        state=RecoveryState.CRASHED,
        checkpoints=[checkpoint.manifest_path],
        provider="horizun",
        mutation_interrupted=True,
    )

    assert plan.decision is RecoveryDecision.MANUAL_REVIEW
    assert plan.retry_allowed is False
    assert [step.kind for step in plan.steps] == [
        RecoveryStepKind.REOPEN_CHECKPOINT,
        RecoveryStepKind.RECONNECT_PROVIDER,
        RecoveryStepKind.HEALTHCHECK,
        RecoveryStepKind.REQUERY_CURRENT_STATE,
        RecoveryStepKind.DECIDE_RETRY_OR_FALLBACK,
    ]


def test_recovery_can_decide_retry_only_after_requery_when_no_mutation_was_interrupted(
    tmp_path: Path,
):
    checkpoint = _checkpoint(tmp_path, "R02", b"known-good", "R02")

    plan = build_recovery_plan(
        state=RecoveryState.CRASHED,
        checkpoints=[checkpoint.manifest_path],
        provider="horizun",
        mutation_interrupted=False,
    )

    assert plan.decision is RecoveryDecision.RETRY_OR_FALLBACK
    assert plan.retry_allowed is True


def test_recovery_refuses_crashed_state_without_verified_checkpoint(tmp_path: Path):
    with pytest.raises(RecoveryPlanningError, match="verified PASS checkpoint"):
        build_recovery_plan(
            state=RecoveryState.CRASHED,
            checkpoints=[],
            provider="horizun",
        )
