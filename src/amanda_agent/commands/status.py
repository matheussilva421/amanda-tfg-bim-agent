"""Read-only project status plus the resume plan.

Both commands only read. Reporting must never advance a revision or create a
directory, because a status call is exactly what you run when something has
already gone wrong.
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


def status_snapshot(root: Path) -> dict:
    paths = ProjectPaths.from_root(root)
    state = StateStore(paths.project_state).load()
    blockers = load_blockers(paths.state)
    lease_path = paths.state / "locks" / "revit-writer.lock"
    lease_info = WriterLock(lease_path, owner="status-probe").inspect()
    graph = phase_graph()
    blocked = graph.blocked_tasks(blockers)
    return {
        "phase_id": state.phase_id,
        "phase_name": state.phase_name,
        "phase_status": str(state.phase_status),
        "next_task": state.next_task,
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


def render_status(snapshot: dict) -> None:
    typer.echo(
        "phase        " + snapshot["phase_id"] + " (" + snapshot["phase_name"] + ")"
    )
    typer.echo("status       " + snapshot["phase_status"])
    typer.echo("next task    " + snapshot["next_task"])
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
