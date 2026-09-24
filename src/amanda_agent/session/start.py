"""Read-only checks required before resuming autonomous work.

The returned mapping is deliberately structured as an ordered list of named
checks.  A caller can therefore distinguish a clean preflight from a report
that merely happened to contain a few useful facts.  No task is started by
this module.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from ..bootstrap.revit import scan_roots
from ..commands.status import load_blockers
from ..models.state import ProjectState
from ..paths import ProjectPaths
from ..state.locks import WriterLock
from ..state.store import StateStore
from ..state.tasks import TaskRegistry, load_registry

GitRunner = Callable[[list[str], Path], Any]
Probe = Callable[[], Any]

_BIM_PHASES = frozenset({"PHASE_02", "PHASE_05", "PHASE_08"})
_HEALTHY_STATUSES = frozenset(
    {"AVAILABLE", "HEALTHY", "OK", "PASS", "READY", "RUNNING"}
)


def _default_git_runner(argv: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, "", str(exc)
    return completed.returncode, completed.stdout or "", completed.stderr or ""


def _normalise_process_result(result: Any) -> tuple[int, str, str]:
    if isinstance(result, tuple) and len(result) == 3:
        return int(result[0]), str(result[1] or ""), str(result[2] or "")
    return (
        int(getattr(result, "returncode", 127)),
        str(getattr(result, "stdout", "") or ""),
        str(getattr(result, "stderr", "") or ""),
    )


def locate_repo_root(root: Path | None = None) -> Path:
    """Resolve the repository root without changing the working tree."""
    if root is not None:
        return Path(root).expanduser().resolve()
    override = os.environ.get("AMANDA_PROJECT_ROOT")
    candidate = (
        Path(override).expanduser().resolve()
        if override
        else Path.cwd().resolve()
    )
    if candidate.is_dir():
        markers = ("AGENTS.md", "PROJECT_STATE.yaml", ".git")
        for parent in (candidate, *candidate.parents):
            if any((parent / marker).exists() for marker in markers):
                return parent
    return candidate


def is_bim_phase(state: ProjectState | None) -> bool:
    if state is None:
        return False
    return state.phase_id in _BIM_PHASES or bool(state.revit_stage)


def _phase_plan_path(root: Path, state: ProjectState | None) -> Path | None:
    if state is None:
        return None
    return root / "docs" / "plan" / "CURRENT.md"


def _registry_plan_path(
    root: Path, state: ProjectState | None, registry: TaskRegistry | None
) -> Path | None:
    if state is not None and registry is not None:
        record = registry.tasks.get(state.next_task)
        if record is not None:
            path = Path(record.plan_path)
            resolved = path if path.is_absolute() else root / path
            if resolved.is_file():
                return resolved
    return _phase_plan_path(root, state)


def _as_mapping(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    as_dict = getattr(value, "as_dict", None)
    if callable(as_dict):
        result = as_dict()
        return result if isinstance(result, dict) else {}
    return {}


def _provider_health_from_file(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(raw, dict):
        return {}
    for key in ("provider_health", "providers", "provider"):
        value = raw.get(key)
        if isinstance(value, (dict, list, bool, str)):
            return {key: value}
    revit = raw.get("revit")
    if isinstance(revit, dict) and any(
        key in revit for key in ("provider_health", "provider_status")
    ):
        return {"provider_health": revit.get("provider_health", revit.get("provider_status"))}
    return {}


def _provider_is_healthy(value: Any) -> bool:
    if value is True:
        return True
    if value is False or value is None:
        return False
    if isinstance(value, str):
        return value.upper() in _HEALTHY_STATUSES
    if isinstance(value, dict):
        if value.get("healthy") is True or value.get("ok") is True:
            return True
        status = value.get("status")
        if isinstance(status, str) and status.upper() in _HEALTHY_STATUSES:
            return True
        for nested in value.values():
            if isinstance(nested, (dict, str, bool)) and _provider_is_healthy(nested):
                return True
        return False
    if isinstance(value, list):
        return bool(value) and all(_provider_is_healthy(item) for item in value)
    return False


def _default_provider_probe(root: Path) -> dict:
    return _provider_health_from_file(root / "state" / "tool-health.yaml")


def _append_check(
    checks: list[dict],
    problems: list[str],
    name: str,
    status: str,
    detail: str,
    **data: Any,
) -> None:
    entry = {"name": name, "status": status, "detail": detail}
    entry.update(data)
    checks.append(entry)
    if status == "PROBLEM":
        problems.append(detail)


def start_session(
    root: Path | None = None,
    *,
    git_runner: GitRunner | None = None,
    revit_probe: Probe | None = None,
    provider_health_probe: Probe | None = None,
) -> dict:
    """Run the ten ordered session-start checks and return their report."""
    resolved_root = locate_repo_root(root)
    paths = ProjectPaths.from_root(resolved_root)
    checks: list[dict] = []
    problems: list[str] = []
    state: ProjectState | None = None
    registry: TaskRegistry | None = None
    registry_error: str | None = None
    environment_lock: dict = {}

    if resolved_root.is_dir():
        _append_check(
            checks,
            problems,
            "locate_repo_root",
            "OK",
            "repository root located at " + str(resolved_root),
            path=str(resolved_root),
        )
    else:
        _append_check(
            checks,
            problems,
            "locate_repo_root",
            "PROBLEM",
            "repository root is not a directory: " + str(resolved_root),
            path=str(resolved_root),
        )

    agents_path = resolved_root / "AGENTS.md"
    try:
        agents_text = agents_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        _append_check(
            checks,
            problems,
            "read_agents",
            "PROBLEM",
            "AGENTS.md could not be read: " + str(exc),
            path=str(agents_path),
        )
    else:
        _append_check(
            checks,
            problems,
            "read_agents",
            "OK",
            "AGENTS.md loaded",
            path=str(agents_path),
            characters=len(agents_text),
        )

    state_path = paths.project_state
    if not state_path.is_file():
        _append_check(
            checks,
            problems,
            "load_project_state",
            "PROBLEM",
            "PROJECT_STATE.yaml is missing: " + str(state_path),
            path=str(state_path),
        )
    else:
        try:
            state = StateStore(state_path).load()
        except (OSError, UnicodeError, ValueError, TypeError, yaml.YAMLError) as exc:
            _append_check(
                checks,
                problems,
                "load_project_state",
                "PROBLEM",
                "PROJECT_STATE.yaml could not be loaded: " + str(exc),
                path=str(state_path),
            )
        else:
            _append_check(
                checks,
                problems,
                "load_project_state",
                "OK",
                "PROJECT_STATE.yaml loaded",
                phase_id=state.phase_id,
                phase_status=str(state.phase_status),
                next_task=state.next_task,
                state_revision=state.state_revision,
            )

    registry_path = paths.state / "task-graph.yaml"
    try:
        registry = load_registry(registry_path)
        registry.validate()
    except (OSError, UnicodeError, ValueError, TypeError, yaml.YAMLError) as exc:
        registry_error = str(exc)

    plan_path = _registry_plan_path(resolved_root, state, registry)
    if plan_path is None:
        _append_check(
            checks,
            problems,
            "load_current_child_plan",
            "PROBLEM",
            "current child plan cannot be resolved without PROJECT_STATE.yaml",
        )
    else:
        try:
            plan_text = plan_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            _append_check(
                checks,
                problems,
                "load_current_child_plan",
                "PROBLEM",
                "current child plan could not be loaded: " + str(exc),
                path=str(plan_path),
            )
        else:
            _append_check(
                checks,
                problems,
                "load_current_child_plan",
                "OK",
                "current child plan loaded",
                path=str(plan_path),
                characters=len(plan_text),
            )

    git = git_runner or _default_git_runner
    try:
        git_result = _normalise_process_result(git(["git", "status", "--short"], resolved_root))
    except (OSError, subprocess.SubprocessError, TypeError, ValueError) as exc:
        git_result = (127, "", str(exc))
    returncode, stdout, stderr = git_result
    dirty_lines = [line for line in stdout.splitlines() if line.strip()]
    if returncode != 0:
        _append_check(
            checks,
            problems,
            "git_status",
            "PROBLEM",
            "git status could not be inspected: " + (stderr.strip() or f"exit code {returncode}"),
            returncode=returncode,
        )
    elif dirty_lines:
        _append_check(
            checks,
            problems,
            "git_status",
            "PROBLEM",
            "dirty working tree reported before execution",
            returncode=returncode,
            changes=dirty_lines,
        )
    else:
        _append_check(
            checks,
            problems,
            "git_status",
            "OK",
            "working tree is clean",
            returncode=returncode,
            changes=[],
        )

    environment_path = paths.state / "bim-environment.lock.yaml"
    if not environment_path.is_file():
        _append_check(
            checks,
            problems,
            "environment_lock",
            "PROBLEM",
            "environment lock is missing: " + str(environment_path),
            path=str(environment_path),
        )
    else:
        try:
            loaded = yaml.safe_load(environment_path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise TypeError("expected a YAML mapping")
            environment_lock = loaded
        except (OSError, UnicodeError, TypeError, yaml.YAMLError) as exc:
            _append_check(
                checks,
                problems,
                "environment_lock",
                "PROBLEM",
                "environment lock could not be loaded: " + str(exc),
                path=str(environment_path),
            )
        else:
            _append_check(
                checks,
                problems,
                "environment_lock",
                "OK",
                "environment lock loaded",
                path=str(environment_path),
                schema_version=environment_lock.get("schema_version"),
            )

    blockers_path = paths.state / "blockers.yaml"
    blockers = []
    if not blockers_path.is_file():
        _append_check(
            checks,
            problems,
            "blockers",
            "PROBLEM",
            "blocker registry is missing: " + str(blockers_path),
            path=str(blockers_path),
        )
    else:
        try:
            raw_blockers = yaml.safe_load(blockers_path.read_text(encoding="utf-8")) or {}
            if not isinstance(raw_blockers, dict) or not isinstance(
                raw_blockers.get("blockers"), list
            ):
                raise TypeError("expected blockers: list")
            required_fields = {"id", "summary", "severity"}
            if any(
                not isinstance(item, dict) or not required_fields.issubset(item)
                for item in raw_blockers["blockers"]
            ):
                raise TypeError("each blocker needs id, summary and severity")
            blockers = load_blockers(paths.state)
            if len(blockers) != len(raw_blockers["blockers"]):
                raise TypeError("one or more blocker records are invalid")
        except (OSError, UnicodeError, TypeError, yaml.YAMLError) as exc:
            _append_check(
                checks,
                problems,
                "blockers",
                "PROBLEM",
                "blocker registry could not be loaded: " + str(exc),
                path=str(blockers_path),
            )
        else:
            open_blockers = [blocker for blocker in blockers if blocker.is_open]
            blocking = [
                blocker
                for blocker in open_blockers
                if str(blocker.severity) == "BLOCKING"
            ]
            blocker_status = (
                "PROBLEM" if blocking else ("WARN" if open_blockers else "OK")
            )
            blocker_detail = (
                f"{len(open_blockers)} open blocker(s) inspected"
                + ("; blocking work is present" if blocking else "")
            )
            _append_check(
                checks,
                problems,
                "blockers",
                blocker_status,
                blocker_detail,
                open=[blocker.model_dump(mode="json") for blocker in open_blockers],
            )

    lease_path = paths.state / "locks" / "revit-writer.lock"
    lease = WriterLock(lease_path, owner="session-start").inspect()
    if lease_path.exists() and lease is None:
        _append_check(
            checks,
            problems,
            "writer_lease",
            "PROBLEM",
            "writer lease exists but could not be inspected: " + str(lease_path),
            path=str(lease_path),
        )
    elif lease is not None:
        _append_check(
            checks,
            problems,
            "writer_lease",
            "PROBLEM",
            "writer lease is held by " + str(lease.get("owner", "unknown")),
            path=str(lease_path),
            held=True,
            lease=lease,
        )
    else:
        _append_check(
            checks,
            problems,
            "writer_lease",
            "OK",
            "writer lease is free",
            path=str(lease_path),
            held=False,
        )

    if not is_bim_phase(state):
        _append_check(
            checks,
            problems,
            "revit_provider_health",
            "SKIPPED",
            "Revit build and provider health are not required for this phase",
            required=False,
        )
    else:
        revit_data: dict = {}
        provider_data: Any = {}
        issues: list[str] = []
        try:
            revit_data = _as_mapping((revit_probe or scan_roots)())
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            issues.append("Revit build probe failed: " + str(exc))
        selected = revit_data.get("selected") or {}
        actual_build = selected.get("file_version") or selected.get("selected_build")
        expected_build = _as_mapping(environment_lock.get("revit")).get("selected_build")
        if revit_data.get("probe_status") not in {None, "DETECTED"}:
            issues.append("Revit build was not detected")
        if not actual_build:
            issues.append("Revit build is not recorded by the probe")
        if (
            expected_build
            and actual_build
            and str(expected_build) != str(actual_build)
        ):
            issues.append(
                f"Revit build {actual_build} does not match locked build {expected_build}"
            )
        if revit_data.get("running") is False:
            issues.append("Revit is not running for the BIM phase")
        try:
            provider_data = (
                provider_health_probe
                or (lambda: _default_provider_probe(resolved_root))
            )()
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            issues.append("provider health probe failed: " + str(exc))
        if not _provider_is_healthy(provider_data):
            issues.append("no healthy provider record is available")
        _append_check(
            checks,
            problems,
            "revit_provider_health",
            "PROBLEM" if issues else "OK",
            "; ".join(issues)
            if issues
            else "locked Revit build and provider health verified",
            required=True,
            revit=revit_data,
            provider=provider_data,
        )

    ready_tasks: list[str] = []
    next_task: str | None = None
    if registry_error is not None or registry is None:
        _append_check(
            checks,
            problems,
            "resolve_next_ready_task",
            "PROBLEM",
            "task registry is unavailable: " + (registry_error or "unknown error"),
            path=str(registry_path),
        )
    else:
        ready_tasks = registry.ready_tasks()
        if ready_tasks:
            next_task = (
                state.next_task
                if state is not None and state.next_task in ready_tasks
                else ready_tasks[0]
            )
            _append_check(
                checks,
                problems,
                "resolve_next_ready_task",
                "OK",
                "next task resolved from the registry ready set",
                next_task=next_task,
                ready_tasks=ready_tasks,
            )
        else:
            _append_check(
                checks,
                problems,
                "resolve_next_ready_task",
                "PROBLEM",
                "task registry has no READY task to resume",
                ready_tasks=[],
            )

    return {
        "status": "READY" if not problems else "BLOCKED",
        "can_execute": not problems,
        "execution_started": False,
        "root": str(resolved_root),
        "phase_id": state.phase_id if state is not None else None,
        "phase_name": state.phase_name if state is not None else None,
        "next_task": next_task,
        "ready_tasks": ready_tasks,
        "checks": checks,
        "problems": problems,
        "state": state.model_dump(mode="json") if state is not None else None,
        "environment_lock": environment_lock,
        "writer_lease": lease,
    }


run_session_start = start_session
session_start = start_session

__all__ = [
    "is_bim_phase",
    "locate_repo_root",
    "run_session_start",
    "session_start",
    "start_session",
]
