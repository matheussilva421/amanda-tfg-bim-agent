"""Fail-closed recovery planning around verified BIM checkpoints."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from ..bim.checkpoints import CheckpointManifest


class RecoveryState(StrEnum):
    """Observed control-plane state relevant to a recovery decision."""

    HEALTHY = "HEALTHY"
    BUSY = "BUSY"
    SUSPECTED_HANG = "SUSPECTED_HANG"
    HUNG = "HUNG"
    CRASHED = "CRASHED"


class RecoveryStepKind(StrEnum):
    """The ordered gates in a recovery plan."""

    REOPEN_CHECKPOINT = "REOPEN_CHECKPOINT"
    RECONNECT_PROVIDER = "RECONNECT_PROVIDER"
    HEALTHCHECK = "HEALTHCHECK"
    REQUERY_CURRENT_STATE = "REQUERY_CURRENT_STATE"
    DECIDE_RETRY_OR_FALLBACK = "DECIDE_RETRY_OR_FALLBACK"


class RecoveryDecision(StrEnum):
    """Decision emitted only after the ordered recovery probes."""

    RETRY_OR_FALLBACK = "RETRY_OR_FALLBACK"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    NO_RECOVERY = "NO_RECOVERY"


class RecoveryPlanningError(RuntimeError):
    """Recovery cannot proceed without a verified durable checkpoint."""


@dataclass(frozen=True)
class RecoveryStep:
    """One typed, ordered recovery action."""

    kind: RecoveryStepKind
    description: str
    provider: str | None = None


@dataclass(frozen=True)
class RecoveryPlan:
    """A plan that preserves the mutation boundary until re-query evidence."""

    state: RecoveryState
    checkpoint: CheckpointManifest | None
    provider: str
    steps: tuple[RecoveryStep, ...]
    decision: RecoveryDecision
    retry_allowed: bool
    fallback_provider: str | None = None
    reason: str = ""

    @property
    def checkpoint_hash(self) -> str | None:
        return self.checkpoint.sha256 if self.checkpoint is not None else None

    @property
    def step_kinds(self) -> tuple[RecoveryStepKind, ...]:
        return tuple(step.kind for step in self.steps)


def _as_manifest(value: Any) -> CheckpointManifest | None:
    if isinstance(value, CheckpointManifest):
        return value
    if isinstance(value, Mapping):
        try:
            return CheckpointManifest.model_validate(value)
        except (TypeError, ValueError):
            return None
    path = Path(value)
    if path.is_dir():
        return None
    if path.suffix.casefold() == ".rvt":
        path = path.with_suffix(path.suffix + ".manifest.json")
    try:
        return CheckpointManifest.load(path)
    except (OSError, TypeError, ValueError):
        return None


def _manifest_candidates(source: Iterable[Any] | Path | str) -> list[Any]:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if path.is_dir():
            return sorted(path.rglob("*.manifest.json"))
        return [path]
    return list(source)


def _created_key(manifest: CheckpointManifest, ordinal: int) -> tuple[datetime, str, int]:
    created = manifest.created_utc
    return (created, str(manifest.checkpoint_path), ordinal)


def _is_pass_checkpoint(manifest: CheckpointManifest) -> bool:
    """Treat a manifest without an outcome as a verified checkpoint PASS.

    ``CheckpointManager`` publishes a manifest only after stable bytes and a
    hash match.  Optional provenance outcomes are honoured when present so a
    recorded failed checkpoint cannot be selected by omission.
    """

    provenance = manifest.provenance
    status = provenance.get("status", provenance.get("outcome", "PASS"))
    return str(status).strip().upper() in {"PASS", "PASS_WITH_WARNINGS"}


def select_checkpoint(
    checkpoints: Iterable[Any] | Path | str,
    *,
    state: RecoveryState | str = RecoveryState.CRASHED,
) -> CheckpointManifest | None:
    """Return the newest verified PASS manifest, skipping corrupt entries.

    Verification re-reads the file and recomputes its SHA-256 through the same
    ``CheckpointManifest.verify`` contract used by the BIM checkpoint manager.
    Invalid JSON, missing files and hash mismatches are deliberately skipped so
    an earlier verified checkpoint can still be recovered.
    """

    del state  # selection is useful for callers that already classified state
    valid: list[tuple[datetime, str, int, CheckpointManifest]] = []
    for ordinal, candidate in enumerate(_manifest_candidates(checkpoints)):
        manifest = _as_manifest(candidate)
        if manifest is None or not _is_pass_checkpoint(manifest):
            continue
        try:
            verified = manifest.verify()
        except (OSError, ValueError):
            verified = False
        if not verified:
            continue
        key = _created_key(manifest, ordinal)
        valid.append((*key, manifest))
    if not valid:
        return None
    return max(valid, key=lambda item: item[:3])[-1]


def build_recovery_plan(
    *,
    state: RecoveryState | str,
    checkpoints: Iterable[Any] | Path | str,
    provider: str,
    fallback_provider: str | None = None,
    mutation_interrupted: bool = False,
) -> RecoveryPlan:
    """Build the only safe recovery sequence for a crashed operation."""

    observed_state = RecoveryState(state)
    preferred = str(provider).strip()
    if not preferred:
        raise RecoveryPlanningError("preferred provider is required")
    if observed_state is not RecoveryState.CRASHED:
        return RecoveryPlan(
            state=observed_state,
            checkpoint=None,
            provider=preferred,
            steps=(),
            decision=RecoveryDecision.NO_RECOVERY,
            retry_allowed=False,
            fallback_provider=fallback_provider,
            reason="recovery plan is only needed for CRASHED state",
        )

    checkpoint = select_checkpoint(checkpoints, state=observed_state)
    if checkpoint is None:
        raise RecoveryPlanningError("no verified PASS checkpoint available")

    steps = (
        RecoveryStep(
            RecoveryStepKind.REOPEN_CHECKPOINT,
            "reopen the selected verified checkpoint before any mutation",
        ),
        RecoveryStep(
            RecoveryStepKind.RECONNECT_PROVIDER,
            "reconnect the preferred provider after the checkpoint is open",
            provider=preferred,
        ),
        RecoveryStep(
            RecoveryStepKind.HEALTHCHECK,
            "healthcheck the provider and document session",
            provider=preferred,
        ),
        RecoveryStep(
            RecoveryStepKind.REQUERY_CURRENT_STATE,
            "re-query current document state and reconcile the interrupted operation",
        ),
        RecoveryStep(
            RecoveryStepKind.DECIDE_RETRY_OR_FALLBACK,
            "decide retry or fallback only from the re-query result",
            provider=fallback_provider,
        ),
    )
    decision = (
        RecoveryDecision.MANUAL_REVIEW
        if mutation_interrupted
        else RecoveryDecision.RETRY_OR_FALLBACK
    )
    reason = (
        "mutation was interrupted; retry remains disabled until reconciliation "
        "is explicitly reviewed"
        if mutation_interrupted
        else "no interrupted mutation was recorded; retry/fallback remains gated by re-query"
    )
    return RecoveryPlan(
        state=observed_state,
        checkpoint=checkpoint,
        provider=preferred,
        steps=steps,
        decision=decision,
        retry_allowed=not mutation_interrupted,
        fallback_provider=fallback_provider,
        reason=reason,
    )


__all__ = [
    "RecoveryDecision",
    "RecoveryPlan",
    "RecoveryPlanningError",
    "RecoveryState",
    "RecoveryStep",
    "RecoveryStepKind",
    "build_recovery_plan",
    "select_checkpoint",
]
