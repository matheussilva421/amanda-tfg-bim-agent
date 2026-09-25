"""Read machine state and render the durable human status dashboard."""

from __future__ import annotations

import os
import subprocess
import tempfile
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from .models.capability import CapabilityRegistry
from .security.redaction import redact_text
from .state.locks import WriterLock
from .state.store import StateStore
from .state.tasks import TaskRegistry, load_registry


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return value if isinstance(value, dict) else {}


def _value(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return default


def _status_from_provider(value: Any) -> str:
    if isinstance(value, Mapping):
        value = _value(value, "status", "health", "state", default="UNKNOWN")
    if isinstance(value, bool):
        return "HEALTHY" if value else "FAIL"
    return str(value or "UNKNOWN").upper()


def _task_data(root: Path) -> dict[str, Any]:
    path = root / "state" / "task-graph.yaml"
    if not path.is_file():
        return {"available": False, "error": "task registry is missing"}
    try:
        registry: TaskRegistry = load_registry(path)
        registry.validate()
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        return {"available": False, "error": "task registry could not be read: " + str(exc)}
    records = list(registry.tasks.values())
    statuses = Counter(str(record.status) for record in records)
    phases: dict[str, dict[str, int]] = {}
    for record in records:
        phase = phases.setdefault(record.phase, {"total": 0, "passed": 0})
        phase["total"] += 1
        if str(record.status) in {"PASS", "PASS_WITH_WARNINGS"}:
            phase["passed"] += 1
    return {
        "available": True,
        "total": len(records),
        "statuses": dict(sorted(statuses.items())),
        "phases": dict(sorted(phases.items())),
        "ready": registry.ready_tasks(),
    }


def _capability_data(root: Path) -> dict[str, Any]:
    path = root / "state" / "capabilities.yaml"
    if not path.is_file():
        return {"available": False, "counts": {"PASS": 0, "FAIL": 0, "UNTESTED": 0}}
    try:
        registry = CapabilityRegistry.load(path)
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        return {
            "available": False,
            "counts": {"PASS": 0, "FAIL": 0, "UNTESTED": 0},
            "error": "capability registry could not be read: " + str(exc),
        }
    counts = Counter(str(entry.status).upper() for entry in registry.entries)
    return {
        "available": True,
        "counts": {key: counts.get(key, 0) for key in ("PASS", "FAIL", "UNTESTED")},
        "all_counts": dict(sorted(counts.items())),
    }


def _provider_data(root: Path) -> dict[str, Any]:
    lock = _read_yaml(root / "state" / "bim-environment.lock.yaml")
    health = _read_yaml(root / "state" / "tool-health.yaml")
    lock_providers = lock.get("providers") if isinstance(lock.get("providers"), dict) else {}
    health_providers = health.get("providers") if isinstance(health.get("providers"), dict) else {}
    names = sorted(set(lock_providers) | set(health_providers))
    providers = []
    for name in names:
        source = health_providers.get(name, lock_providers.get(name))
        providers.append(
            {
                "name": name,
                "status": _status_from_provider(source),
                "role": _value(
                    health_providers.get(name, {}),
                    "role",
                    default=_value(lock_providers.get(name, {}), "role", default=""),
                ),
            }
        )
    return {
        "preferred": _value(lock, "preferred_provider", default="NOT_RECORDED"),
        "providers": providers,
    }


def _git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _blocker_data(root: Path) -> list[dict[str, str]]:
    raw = _read_yaml(root / "state" / "blockers.yaml")
    entries = raw.get("blockers", [])
    if not isinstance(entries, list):
        return []
    result = []
    for entry in entries:
        if not isinstance(entry, Mapping) or entry.get("resolved_utc"):
            continue
        result.append(
            {
                "id": str(entry.get("id", "UNKNOWN")),
                "severity": str(entry.get("severity", "UNKNOWN")),
                "summary": str(entry.get("summary", "not recorded")),
            }
        )
    return result


def build_status_dashboard(root: Path) -> dict[str, Any]:
    """Build a dashboard data object entirely from on-disk observations."""

    resolved_root = Path(root).resolve()
    state_path = resolved_root / "PROJECT_STATE.yaml"
    state_error = None
    try:
        state = StateStore(state_path).load()
        state_data = state.model_dump(mode="json")
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        state = None
        state_data = {}
        state_error = "project state could not be read: " + str(exc)

    lease_path = resolved_root / "state" / "locks" / "revit-writer.lock"
    lease_info = WriterLock(lease_path, owner="status-dashboard").inspect()
    if lease_info is None:
        lease = {
            "status": "UNKNOWN" if lease_path.exists() else "FREE",
            "owner": None,
            "fencing_generation": None,
        }
    else:
        lease = {
            "status": "HELD",
            "owner": lease_info.get("owner"),
            "fencing_generation": lease_info.get("fencing_generation"),
        }

    lock = _read_yaml(resolved_root / "state" / "bim-environment.lock.yaml")
    revit = lock.get("revit") if isinstance(lock.get("revit"), dict) else {}
    metadata = _read_yaml(resolved_root / "state" / "revit-metadata.json")
    selected = metadata.get("installations", [])
    selected_metadata = selected[0] if isinstance(selected, list) and selected else {}
    revit_build = _value(
        revit,
        "selected_build",
        default=_value(selected_metadata, "fileVersion", default="NOT_RECORDED"),
    )
    return {
        "root": str(resolved_root),
        "state": state_data,
        "state_error": state_error,
        "tasks": _task_data(resolved_root),
        "revit": {
            "build": revit_build,
            "product_version": _value(
                revit,
                "product_version",
                default=_value(selected_metadata, "productVersion", default="NOT_RECORDED"),
            ),
        },
        "providers": _provider_data(resolved_root),
        "capabilities": _capability_data(resolved_root),
        "blockers": _blocker_data(resolved_root),
        "writer_lease": lease,
        "writer_lease_path": str(lease_path),
        "git_head_observed": _git_head(resolved_root),
    }


def _render_list(values: list[str] | tuple[str, ...] | None) -> str:
    if not values:
        return "- none recorded"
    return "\n".join("- " + redact_text(str(value)) for value in values)


def render_status_markdown(data: Mapping[str, Any]) -> str:
    """Render dashboard observations without replacing missing values."""

    state = data.get("state") or {}
    tasks = data.get("tasks") or {}
    phases = tasks.get("phases") or {}
    if tasks.get("available"):
        phase_lines = "\n".join(
            f"- `{redact_text(str(phase))}`: {bucket.get('passed', 0)}/{bucket.get('total', 0)} PASS"
            for phase, bucket in sorted(phases.items())
        ) or "- none recorded"
        task_line = f"- Tasks: {tasks.get('total', 0)} total; READY: {', '.join(tasks.get('ready') or []) or '(none)'}"
    else:
        phase_lines = "- phase/task registry unavailable: " + redact_text(
            str(tasks.get("error", "not recorded"))
        )
        task_line = "- Tasks: not recorded"
    capabilities = data.get("capabilities") or {}
    capability_counts = capabilities.get("counts") or {"PASS": 0, "FAIL": 0, "UNTESTED": 0}
    providers = data.get("providers") or {}
    provider_lines = "\n".join(
        f"- `{redact_text(str(item.get('name')) )}`: {redact_text(str(item.get('status', 'UNKNOWN')))}"
        + (f" ({redact_text(str(item.get('role')))})" if item.get("role") else "")
        for item in providers.get("providers", [])
    ) or "- not recorded"
    blocker_lines = "\n".join(
        f"- `{redact_text(item['id'])}` [{redact_text(item['severity'])}]: {redact_text(item['summary'])}"
        for item in data.get("blockers", [])
    ) or "- none recorded"
    lease = data.get("writer_lease") or {}
    state_error = data.get("state_error")
    return (
        "# Status dashboard\n\n"
        "Source: live files in the project workspace. Missing values remain `NOT_RECORDED`.\n\n"
        "## Phase and task progress\n\n"
        f"- Phase: `{redact_text(str(state.get('phase_id', 'NOT_RECORDED')))}` — "
        f"{redact_text(str(state.get('phase_name', 'NOT_RECORDED')))}\n"
        f"- Phase status: `{redact_text(str(state.get('phase_status', 'NOT_RECORDED')))}`\n"
        f"- Next task: `{redact_text(str(state.get('next_task', 'NOT_RECORDED')))}`\n"
        f"- Last recorded task: `{redact_text(str(state.get('last_completed_task') or 'NOT_RECORDED'))}`\n"
        + task_line
        + "\n"
        + phase_lines
        + "\n\n## Environment\n\n"
        + f"- Revit build: `{redact_text(str((data.get('revit') or {}).get('build', 'NOT_RECORDED')))}`\n"
        + f"- Revit product version: `{redact_text(str((data.get('revit') or {}).get('product_version', 'NOT_RECORDED')))}`\n\n"
        "## Provider health\n\n"
        + f"- Preferred provider: `{redact_text(str(providers.get('preferred', 'NOT_RECORDED')))}`\n"
        + provider_lines
        + "\n\n## Capability counts\n\n"
        + f"- PASS: {capability_counts.get('PASS', 0)}\n"
        + f"- FAIL: {capability_counts.get('FAIL', 0)}\n"
        + f"- UNTESTED: {capability_counts.get('UNTESTED', 0)}\n\n"
        "## Blockers\n\n"
        + blocker_lines
        + "\n\n## Design and Revit recovery\n\n"
        + f"- Selected design: `{redact_text(str(state.get('selected_design') or 'NOT_RECORDED'))}`\n"
        + f"- Revit stage: `{redact_text(str(state.get('revit_stage') or 'NOT_RECORDED'))}`\n"
        + f"- Current checkpoint: `{redact_text(str(state.get('current_checkpoint') or 'NOT_RECORDED'))}`\n\n"
        "## Writer lease\n\n"
        + f"- Status: `{redact_text(str(lease.get('status', 'UNKNOWN')))}`\n"
        + f"- Owner: `{redact_text(str(lease.get('owner') or 'NOT_RECORDED'))}`\n"
        + f"- Fencing generation: `{redact_text(str(lease.get('fencing_generation') or 'NOT_RECORDED'))}`\n\n"
        "## Git verification\n\n"
        + f"- Last verified commit: `{redact_text(str(state.get('last_verified_commit') or 'NOT_RECORDED'))}`\n"
        + f"- Observed HEAD: `{redact_text(str(data.get('git_head_observed') or 'NOT_RECORDED'))}`\n"
        + ("\nState read note: " + redact_text(str(state_error)) + "\n" if state_error else "")
    )


def write_status_markdown(root: Path, data: Mapping[str, Any] | None = None) -> Path:
    """Atomically update ``state/status.md`` from the current disk state."""

    resolved_root = Path(root).resolve()
    target = resolved_root / "state" / "status.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    content = render_status_markdown(data or build_status_dashboard(resolved_root))
    handle, temporary_name = tempfile.mkstemp(
        prefix=".status.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


build_dashboard = build_status_dashboard
render_dashboard = render_status_markdown
write_status_dashboard = write_status_markdown


__all__ = [
    "build_dashboard",
    "build_status_dashboard",
    "render_dashboard",
    "render_status_markdown",
    "write_status_dashboard",
    "write_status_markdown",
]
