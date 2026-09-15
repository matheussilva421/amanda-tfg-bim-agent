"""Record task and phase progress from the command line.

The writer itself lives in :mod:`amanda_agent.state.advance`; this module only
translates a refusal into a non-zero exit code and keeps the messages short
enough to paste into a handoff.
"""

from __future__ import annotations

from pathlib import Path

import typer

from ..models.state import PhaseGate, TaskStatus
from ..state.advance import (
    AdvanceRefused,
    complete_phase,
    complete_task,
    set_phase_gate,
)
from ..state.store import StateStore
from ..state.tasks import load_registry


def task_graph_report(root: Path) -> dict:
    """Read-only progress summary over the task registry."""
    root = Path(root)
    path = root / "state" / "task-graph.yaml"
    try:
        registry = load_registry(path)
    except FileNotFoundError as exc:
        raise AdvanceRefused(
            str(exc) + "; run python -m amanda_agent.state.build_task_graph"
        ) from exc
    registry.validate()
    counts: dict = {}
    for record in registry.tasks.values():
        counts[str(record.status)] = counts.get(str(record.status), 0) + 1
    ready = registry.ready_tasks()
    ready_set = set(ready)
    blocked = sorted(
        task_id for task_id in registry.tasks if task_id not in ready_set
        and str(registry.tasks[task_id].status) == "PENDING"
    )
    phases: dict = {}
    for record in registry.tasks.values():
        bucket = phases.setdefault(record.phase, {"total": 0, "passed": 0})
        bucket["total"] += 1
        if str(record.status) in {"PASS", "PASS_WITH_WARNINGS"}:
            bucket["passed"] += 1
    return {
        "path": str(path),
        "total": len(registry.tasks),
        "counts": counts,
        "ready": ready,
        "pending_blocked": blocked,
        "batches": registry.parallel_batches(),
        "phases": phases,
    }


def render_task_graph(report: dict) -> None:
    typer.echo("registry     " + report["path"])
    typer.echo("total        " + str(report["total"]))
    for status, count in sorted(report["counts"].items()):
        typer.echo("  " + status.ljust(20) + str(count))
    for phase, bucket in sorted(report["phases"].items()):
        typer.echo(
            "  "
            + phase.ljust(12)
            + str(bucket["passed"])
            + "/"
            + str(bucket["total"])
            + " passed"
        )
    typer.echo("ready        " + (" ".join(report["ready"]) or "(none)"))
    blocked = report["pending_blocked"]
    preview = blocked[:8]
    suffix = "" if len(blocked) <= 8 else " (+%d more)" % (len(blocked) - 8)
    typer.echo(
        "blocked      " + ((" ".join(preview) + suffix) if blocked else "(none)")
    )
    if report["batches"]:
        parallel = report["batches"][0]
        typer.echo("parallel     " + " ".join(parallel))


def run_advance(
    root: Path,
    *,
    task_id: str,
    status: str,
    evidence: list,
    next_task: str | None = None,
    expected_revision: int | None = None,
    allow_unready: str | None = None,
) -> dict:
    try:
        parsed = TaskStatus(status)
    except ValueError as exc:
        raise AdvanceRefused("--status " + status + " is not a task status")
    return complete_task(
        Path(root),
        task_id=task_id,
        status=parsed,
        evidence=evidence,
        next_task=next_task,
        expected_revision=expected_revision,
        allow_unready=allow_unready,
    )


def run_phase_gate(
    root: Path, *, gate: str, reason: str, verified_commit: str | None = None
) -> dict:
    try:
        PhaseGate(gate)
    except ValueError as exc:
        raise AdvanceRefused("--gate " + gate + " is not a phase gate") from exc
    if not reason.strip():
        raise AdvanceRefused("a phase gate needs a reason worth recording")
    return set_phase_gate(
        Path(root), gate=gate, reason=reason, verified_commit=verified_commit
    )


def run_advance_phase(
    root: Path,
    *,
    gate: str,
    next_phase_id: str,
    next_phase_name: str,
    next_task: str,
    reason: str,
) -> dict:
    """Close a phase, refusing while tasks in it are still open.

    Closing a phase is the moment a gate becomes a claim, so it is the wrong
    place to be generous: an unfinished or failed task must stop the close.
    """
    root = Path(root)
    try:
        PhaseGate(gate)
    except ValueError as exc:
        raise AdvanceRefused("--gate " + gate + " is not a phase gate") from exc
    if not reason.strip():
        raise AdvanceRefused("closing a phase needs a recorded reason")

    registry = load_registry(root / "state" / "task-graph.yaml")
    registry.validate()
    state = StateStore(root / "PROJECT_STATE.yaml").load()
    open_tasks = sorted(
        task_id
        for task_id, record in registry.tasks.items()
        if record.phase == state.phase_id
        and str(record.status) not in {"PASS", "PASS_WITH_WARNINGS"}
    )
    if open_tasks:
        preview = " ".join(open_tasks[:8])
        if len(open_tasks) > 8:
            preview += " (+%d more)" % (len(open_tasks) - 8)
        raise AdvanceRefused(
            "phase " + state.phase_id + " still has open tasks: " + preview
        )
    if next_task not in registry.tasks:
        raise AdvanceRefused("unknown next task " + next_task)
    return complete_phase(
        root,
        gate=gate,
        next_phase_id=next_phase_id,
        next_phase_name=next_phase_name,
        next_task=next_task,
        reason=reason,
    )
