"""Project status plus the resume plan.

The state report remains read-only with respect to project state. In addition
to the existing stdout contract, each status call refreshes the derived
``state/status.md`` dashboard from the files it reads.
"""

from __future__ import annotations

from pathlib import Path

import typer
import yaml

from ..models.tasks import Blocker, Severity
from ..paths import ProjectPaths
from ..program import phase_graph
from ..state.locks import WriterLock
from ..state.store import StateStore


def load_blockers(state_dir: Path) -> list:
    path = Path(state_dir) / "blockers.yaml"
    if not path.exists():
        return []
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return []
    entries = raw.get("blockers", []) if isinstance(raw, dict) else []
    blockers = []
    for entry in entries:
        if isinstance(entry, dict):
            entry.setdefault("severity", Severity.BLOCKING)
            try:
                blockers.append(Blocker(**entry))
            except Exception:
                continue
    return blockers


def load_ready_tasks(root: Path) -> dict:
    """Task-level readiness, which the coarse phase graph cannot express.

    A missing registry is reported as missing instead of being invented: the
    point of a status call is to tell the truth about an incomplete checkout.
    """
    from ..state.tasks import load_registry

    path = Path(root) / "state" / "task-graph.yaml"
    if not path.exists():
        return {"available": False, "ready": [], "blocked": [], "total": 0}
    try:
        registry = load_registry(path)
        registry.validate()
    except Exception as exc:  # a broken registry is data, not a crash
        return {
            "available": False,
            "ready": [],
            "blocked": [],
            "total": 0,
            "problem": str(exc),
        }
    ready = registry.ready_tasks()
    ready_set = set(ready)
    blocked = sorted(
        task_id
        for task_id in registry.tasks
        if task_id not in ready_set
        and str(registry.tasks[task_id].status) == "PENDING"
    )
    return {
        "available": True,
        "ready": ready,
        "blocked": blocked,
        "total": len(registry.tasks),
    }


def status_snapshot(root: Path) -> dict:
    paths = ProjectPaths.from_root(root)
    state = StateStore(paths.project_state).load()
    blockers = load_blockers(paths.state)
    lease_path = paths.state / "locks" / "revit-writer.lock"
    lease_info = WriterLock(lease_path, owner="status-probe").inspect()
    graph = phase_graph()
    blocked = graph.blocked_tasks(blockers)
    tasks = load_ready_tasks(root)
    next_task = state.next_task
    if tasks["available"] and tasks["ready"]:
        if next_task not in tasks["ready"]:
            next_task = tasks["ready"][0]
    snapshot = {
        "phase_id": state.phase_id,
        "phase_name": state.phase_name,
        "phase_status": str(state.phase_status),
        "next_task": next_task,
        "ready_tasks": tasks["ready"],
        "task_registry": tasks,
        "last_completed_task": state.last_completed_task,
        "revit_stage": state.revit_stage,
        "current_checkpoint": state.current_checkpoint,
        "blockers": [blocker for blocker in blockers if blocker.is_open],
        "blocked_phases": sorted(blocked),
        "runnable_phases": graph.runnable_tasks(blockers),
        "writer_lease": {
            "path": str(lease_path),
            "held": lease_info is not None,
            "owner": (lease_info or {}).get("owner"),
            "fencing_generation": (lease_info or {}).get("fencing_generation"),
        },
        "state_revision": state.state_revision,
    }
    try:
        from ..status_dashboard import write_status_markdown

        write_status_markdown(root)
    except (OSError, ValueError, TypeError) as exc:
        # The existing terminal report remains usable when a derived dashboard
        # cannot be written; expose the failure to callers instead of hiding it.
        snapshot["status_dashboard_error"] = str(exc)
    return snapshot


def render_status(snapshot: dict) -> None:
    typer.echo(
        "phase        " + snapshot["phase_id"] + " (" + snapshot["phase_name"] + ")"
    )
    typer.echo("status       " + snapshot["phase_status"])
    typer.echo("next task    " + snapshot["next_task"])
    tasks = snapshot.get("task_registry") or {}
    if tasks.get("available"):
        typer.echo("ready tasks  " + (" ".join(tasks["ready"]) or "(none)"))
        blocked = tasks["blocked"]
        preview = blocked[:8]
        suffix = "" if len(blocked) <= 8 else " (+%d more)" % (len(blocked) - 8)
        typer.echo(
            "pending      "
            + ((" ".join(preview) + suffix) if blocked else "(none)")
        )
    else:
        typer.echo("ready tasks  (registry missing)")
    if snapshot["last_completed_task"]:
        typer.echo("last task    " + snapshot["last_completed_task"])
    typer.echo("revit stage  " + str(snapshot["revit_stage"]))
    typer.echo("checkpoint   " + str(snapshot["current_checkpoint"]))
    typer.echo("revision     " + str(snapshot["state_revision"]))
    lease = snapshot["writer_lease"]
    typer.echo(
        "writer lease "
        + ("HELD by " + str(lease["owner"]) if lease["held"] else "free")
    )
    open_blockers = snapshot["blockers"]
    typer.echo("open blockers " + str(len(open_blockers)))
    for blocker in open_blockers:
        typer.echo(
            "  " + blocker.id + " [" + str(blocker.severity) + "] " + blocker.summary
        )
    if snapshot["blocked_phases"]:
        typer.echo("blocked      " + ", ".join(snapshot["blocked_phases"]))


def resume_plan(root: Path) -> dict:
    snapshot = status_snapshot(root)
    return {
        "blocked_phases": snapshot["blocked_phases"],
        "runnable_phases": snapshot["runnable_phases"],
        "blockers": snapshot["blockers"],
        "next_task": snapshot["next_task"],
    }
