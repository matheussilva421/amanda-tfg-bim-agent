"""Durable, evidence-backed session closure and handoff writing."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from datetime import date as date_type
from pathlib import Path
from typing import Any

from ..models.state import TaskStatus
from ..state.store import StateStore
from ..state.tasks import TaskRegistry, load_registry


class SessionEndRefused(Exception):
    """The session cannot be closed without losing authoritative context."""


_SUSPENSION_STATUSES = frozenset(
    {TaskStatus.SUSPENDED, TaskStatus.BLOCKED_BY_INPUT, TaskStatus.BLOCKED_BY_TOOL}
)


def _items(value: Iterable[Any] | Any | None) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value]
    if isinstance(value, Mapping):
        return [value]
    return list(value)


def _text_items(value: Iterable[Any] | Any | None, *, empty: str) -> list[str]:
    values = [str(item).strip() for item in _items(value) if str(item).strip()]
    return values or [empty]


def _test_items(value: Iterable[Any] | Any | None) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for item in _items(value):
        if isinstance(item, Mapping):
            command = str(item.get("command", "")).strip()
            result = str(item.get("result", item.get("outcome", ""))).strip()
            if not command or not result:
                raise SessionEndRefused(
                    "test evidence must record both a command and its result"
                )
            records.append({"command": command, "result": result})
        else:
            text = str(item).strip()
            if text:
                records.append({"command": text, "result": "recorded"})
    if not records:
        raise SessionEndRefused(
            "session end requires recorded test command/result evidence"
        )
    return records


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower()
    if not slug:
        raise SessionEndRefused("handoff scope must contain a usable name")
    return slug


def _date_text(value: str | date_type | None) -> str:
    if value is None:
        return datetime.now(UTC).date().isoformat()
    if isinstance(value, date_type):
        return value.isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)):
        raise SessionEndRefused("handoff date must use YYYY-MM-DD")
    return str(value)


def _markdown_lines(values: list[str]) -> str:
    return "\n".join("- " + value for value in values)


def compose_handoff(
    *,
    scope: str,
    generated_date: str,
    changes: list[str],
    evidence: list[str],
    tests: list[dict[str, str]],
    github_status: str,
    blockers: list[str],
    resume_instructions: list[str],
    next_task_id: str,
    state_status: str,
    state_revision: int,
    checkpoint_reference: str | None,
) -> str:
    test_lines = "\n".join(
        f"- `{record['command']}` — {record['result']}" for record in tests
    )
    checkpoint = checkpoint_reference or "none recorded (no BIM mutation declared)"
    return (
        f"# Session handoff: {_slug(scope)}\n\n"
        f"Date: {generated_date}\n\n"
        "## Changes\n\n"
        + _markdown_lines(changes)
        + "\n\n## Evidence\n\n"
        + _markdown_lines(evidence)
        + "\n\n## Tests\n\n"
        + test_lines
        + "\n\n## GitHub status\n\n- "
        + str(github_status or "GitHub status not recorded")
        + "\n\n## Blockers\n\n"
        + _markdown_lines(blockers)
        + "\n\n## Resume instructions\n\n"
        + _markdown_lines(resume_instructions)
        + f"\n\n- explicit next task: `{next_task_id}`"
        + f"\n- persisted project-state status: `{state_status}` (revision {state_revision})"
        + f"\n- checkpoint reference: `{checkpoint}`\n"
    )


def write_incremental_handoff(root: Path, *, filename: str, content: str) -> Path:
    """Create a handoff or append to the exact existing path without replacing it."""
    target = Path(root) / "docs" / "notes" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise SessionEndRefused("refusing to write a handoff through a symlink")
    if not target.exists():
        target.write_text(content, encoding="utf-8")
        return target
    try:
        existing = target.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise SessionEndRefused("existing handoff could not be read: " + str(exc)) from exc
    if content in existing:
        return target
    separator = "" if existing.endswith("\n") else "\n"
    with target.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(separator + "\n" + content)
    return target


def end_session(
    root: Path,
    *,
    scope: str,
    changes: Iterable[Any] | Any | None = None,
    evidence: Iterable[Any] | Any | None = None,
    test_evidence: Iterable[Any] | Any | None = None,
    tests: Iterable[Any] | Any | None = None,
    test_results: Iterable[Any] | Any | None = None,
    github_status: str = "GitHub status not changed by this session",
    blockers: Iterable[Any] | Any | None = None,
    resume_instructions: Iterable[Any] | Any | None = None,
    next_task_id: str | None = None,
    next_task: str | None = None,
    project_state_update: Mapping[str, Any] | None = None,
    state_update: Mapping[str, Any] | None = None,
    bim_mutated: bool = False,
    checkpoint_reference: str | None = None,
    date: str | date_type | None = None,
) -> dict:
    """Persist the end state and append a complete incremental handoff."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise SessionEndRefused("repository root is not a directory: " + str(root))
    if project_state_update is not None and state_update is not None:
        raise SessionEndRefused("provide only one project-state update mapping")
    updates = dict(
        project_state_update
        if project_state_update is not None
        else (state_update or {})
    )
    if not updates:
        raise SessionEndRefused("session end requires an explicit project-state update")

    selected_next_task = (next_task_id or next_task or "").strip()
    if not selected_next_task:
        raise SessionEndRefused("session end requires an explicit next task id")

    state_path = root / "PROJECT_STATE.yaml"
    if not state_path.is_file():
        raise SessionEndRefused("PROJECT_STATE.yaml is missing; cannot record session end")
    try:
        store = StateStore(state_path)
        current = store.load()
    except Exception as exc:
        raise SessionEndRefused("project state could not be loaded: " + str(exc)) from exc

    registry_path = root / "state" / "task-graph.yaml"
    try:
        registry: TaskRegistry = load_registry(registry_path)
        registry.validate()
    except Exception as exc:
        raise SessionEndRefused("task registry could not be loaded: " + str(exc)) from exc

    running_tasks = [
        task_id
        for task_id, record in registry.tasks.items()
        if str(record.status) == str(TaskStatus.RUNNING)
    ]
    requested_status = updates.get("phase_status")
    try:
        requested_status = (
            TaskStatus(requested_status) if requested_status is not None else None
        )
    except ValueError as exc:
        raise SessionEndRefused("project-state phase_status is invalid") from exc
    if running_tasks and requested_status not in _SUSPENSION_STATUSES:
        preview = ", ".join(running_tasks)
        raise SessionEndRefused(
            "cannot end while task(s) are RUNNING: "
            + preview
            + "; move project state to SUSPENDED or a blocker status first"
        )

    evidence_records = _test_items(
        test_evidence
        if test_evidence is not None
        else (tests if tests is not None else test_results)
    )

    checkpoint = (
        checkpoint_reference
        or str(updates.get("current_checkpoint", "")).strip()
        or None
    )
    if bim_mutated and not checkpoint:
        raise SessionEndRefused(
            "a BIM mutation requires a checkpoint reference before session end"
        )

    updates["next_task"] = selected_next_task
    if checkpoint is not None:
        updates.setdefault("current_checkpoint", checkpoint)
    candidate = current.model_copy(update=updates)
    try:
        saved = store.save(candidate, expected_revision=current.state_revision)
    except Exception as exc:
        raise SessionEndRefused("project-state update could not be persisted: " + str(exc)) from exc

    suspended_tasks: list[str] = []
    if running_tasks and requested_status is not None:
        for task_id in running_tasks:
            registry.set_status(task_id, requested_status)
            suspended_tasks.append(task_id)
        registry.save(registry_path)

    generated_date = _date_text(date)
    slug = _slug(scope)
    content = compose_handoff(
        scope=scope,
        generated_date=generated_date,
        changes=_text_items(changes, empty="no changes recorded"),
        evidence=_text_items(evidence, empty="no additional evidence recorded"),
        tests=evidence_records,
        github_status=str(github_status),
        blockers=_text_items(blockers, empty="none recorded"),
        resume_instructions=_text_items(
            resume_instructions, empty="read this handoff and continue the explicit next task"
        ),
        next_task_id=selected_next_task,
        state_status=str(saved.phase_status),
        state_revision=saved.state_revision,
        checkpoint_reference=checkpoint,
    )
    handoff_path = write_incremental_handoff(
        root,
        filename=f"{generated_date}-{slug}-handoff.md",
        content=content,
    )
    return {
        "status": str(saved.phase_status),
        "handoff_path": str(handoff_path),
        "next_task_id": selected_next_task,
        "state_revision": saved.state_revision,
        "suspended_tasks": suspended_tasks,
        "checkpoint_reference": checkpoint,
    }


session_end = end_session

__all__ = [
    "SessionEndRefused",
    "compose_handoff",
    "end_session",
    "session_end",
    "write_incremental_handoff",
]
