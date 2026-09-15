"""Record task and phase progress without lying about it.

Phase 01 shipped the durable state but nothing could move it forward, so the
file kept reporting ``PENDING`` / ``P01-T01`` while thirteen tasks were already
implemented, tested and committed. This module is the missing writer:

* a task is only completed with evidence and a pass-like status;
* the registry and the durable state are updated in one call, so they cannot
  drift apart;
* every completion is appended to ``state/task-history.yaml``;
* a stale expected revision is refused instead of silently overwriting a
  concurrent writer's work.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..models.state import PhaseGate, ProjectState, TaskStatus
from .store import StateStore, StateStoreError
from .tasks import load_registry

#: Statuses that legitimately record a finished attempt.
COMPLETION_STATUSES = frozenset(
    {
        TaskStatus.PASS,
        TaskStatus.PASS_WITH_WARNINGS,
        TaskStatus.DEGRADED,
        TaskStatus.BLOCKED_BY_INPUT,
        TaskStatus.BLOCKED_BY_TOOL,
        TaskStatus.FAILED_ROLLED_BACK,
        TaskStatus.SUSPENDED,
    }
)


class AdvanceRefused(Exception):
    """The requested progress update would make the state unreliable."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_history(root: Path, entry: dict) -> None:
    path = Path(root) / "state" / "task-history.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        entries = list(document.get("entries", []))
    else:
        entries = []
    entries.append(entry)
    path.write_text(
        yaml.safe_dump(
            {"schema_version": 1, "entries": entries},
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def complete_task(
    root: Path,
    *,
    task_id: str,
    status: TaskStatus,
    evidence: list,
    next_task: str | None = None,
    expected_revision: int | None = None,
    note: str | None = None,
    allow_unready: str | None = None,
) -> dict:
    """Record one finished task in the registry, the state and the history.

    A task whose hard dependencies have not passed yet is refused: the registry
    is a graph, and a completion recorded ahead of its inputs is a progress
    claim that never happened. An operator who deliberately wants to close such
    a task passes ``allow_unready`` with the reason; the reason is appended to
    the evidence so the history keeps it.
    """
    root = Path(root)
    if not evidence:
        raise AdvanceRefused(
            "a task cannot be completed without evidence; "
            "record the command and its result instead"
        )
    if status not in COMPLETION_STATUSES:
        raise AdvanceRefused(
            "status "
            + str(status)
            + " does not record completion; use a pass-like or blocked status"
        )

    registry_path = root / "state" / "task-graph.yaml"
    try:
        registry = load_registry(registry_path)
    except FileNotFoundError as exc:
        raise AdvanceRefused(str(exc)) from exc

    if task_id not in registry.tasks:
        raise AdvanceRefused("unknown task " + task_id)

    unready = registry.unready_dependencies(task_id)
    if unready:
        if allow_unready is None or not allow_unready.strip():
            raise AdvanceRefused(
                "task "
                + task_id
                + " still has unfinished dependencies ("
                + ", ".join(unready)
                + "); finish them first, or pass --allow-unready with the reason"
            )
        evidence = list(evidence) + [
            "unready dependency override for " + ", ".join(unready) + ": "
            + allow_unready.strip()
        ]

    store = StateStore(root / "PROJECT_STATE.yaml")
    current = store.load()
    if (
        expected_revision is not None
        and current.state_revision != expected_revision
    ):
        raise AdvanceRefused(
            "state revision mismatch: expected "
            + str(expected_revision)
            + " but found "
            + str(current.state_revision)
        )

    registry.set_status(task_id, status)
    for reference in evidence:
        registry.add_evidence(task_id, reference)
    registry.propagate()
    registry.save(registry_path)

    update = {"last_completed_task": task_id}
    if next_task is not None:
        update["next_task"] = next_task
    else:
        ready = registry.ready_tasks()
        if ready:
            update["next_task"] = ready[0]
    if status in {TaskStatus.BLOCKED_BY_INPUT, TaskStatus.BLOCKED_BY_TOOL}:
        update["phase_status"] = status

    try:
        saved = store.save(
            current.model_copy(update=update),
            expected_revision=current.state_revision,
        )
    except StateStoreError as exc:
        raise AdvanceRefused(str(exc)) from exc

    _append_history(
        root,
        {
            "task_id": task_id,
            "status": str(status),
            "evidence": list(evidence),
            "recorded_utc": _utc_now(),
            "note": note,
        },
    )

    return {
        "task_id": task_id,
        "status": str(status),
        "evidence": list(evidence),
        "next_task": saved.next_task,
        "state_revision": saved.state_revision,
        "unready_dependencies": unready,
        "override_reason": allow_unready.strip() if unready and allow_unready else None,
    }


def set_phase_gate(
    root: Path,
    *,
    gate: str,
    reason: str,
    verified_commit: str | None = None,
) -> dict:
    """Record the phase gate decision on the durable state."""
    root = Path(root)
    store = StateStore(root / "PROJECT_STATE.yaml")
    current = store.load()
    update = {"phase_gate": PhaseGate(gate)}
    if verified_commit is not None:
        update["last_verified_commit"] = verified_commit
    saved = store.save(
        current.model_copy(update=update),
        expected_revision=current.state_revision,
    )
    _append_history(
        root,
        {
            "task_id": "PHASE_GATE",
            "status": str(gate),
            "evidence": [reason],
            "recorded_utc": _utc_now(),
            "note": "phase gate recorded",
        },
    )
    return {
        "phase_gate": str(saved.phase_gate),
        "reason": reason,
        "state_revision": saved.state_revision,
    }


def complete_phase(
    root: Path,
    *,
    gate: str,
    next_phase_id: str,
    next_phase_name: str,
    next_task: str,
    reason: str,
) -> dict:
    """Close the current phase and open the next one at ``PENDING``."""
    root = Path(root)
    store = StateStore(root / "PROJECT_STATE.yaml")
    current = store.load()
    saved = store.save(
        current.model_copy(
            update={
                "phase_gate": PhaseGate(gate),
                "phase_id": next_phase_id,
                "phase_name": next_phase_name,
                "phase_status": TaskStatus.PENDING,
                "next_task": next_task,
            }
        ),
        expected_revision=current.state_revision,
    )
    _append_history(
        root,
        {
            "task_id": "PHASE_GATE",
            "status": str(gate),
            "evidence": [reason],
            "recorded_utc": _utc_now(),
            "note": "advanced to " + next_phase_id,
        },
    )
    return {
        "phase_id": saved.phase_id,
        "phase_gate": str(saved.phase_gate),
        "next_task": saved.next_task,
        "state_revision": saved.state_revision,
    }
