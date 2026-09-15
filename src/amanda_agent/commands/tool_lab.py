"""Deterministic, read-only controls for the Revit Tool Lab."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import typer
import yaml

TOOL_LAB_PLAN = "02-revit-tool-lab-providers.md"
_PASS_STATUSES = frozenset({"PASS", "PASS_WITH_WARNINGS", "VERIFIED", "SUCCESS"})
_FAIL_STATUSES = frozenset(
    {
        "BLOCKED",
        "BLOCKED_BY_TOOL",
        "CRITICAL_FAILURE",
        "DEGRADED",
        "FAIL",
        "FAILED",
        "FAILED_ROLLED_BACK",
        "NOT_AVAILABLE",
        "RETIRED",
    }
)
_PROVIDER_PASS_STATUSES = frozenset(
    {"CONNECTED", "HEALTHY", "PASS", "PASS_WITH_WARNINGS", "VERIFIED"}
)
_STATUS_KEYS = ("status", "health", "result", "verdict", "outcome", "state")
_SAFE_LABEL = re.compile(r"^[A-Za-z0-9_.-]+$")

tool_lab_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Read-only Revit Tool Lab controls.",
)


class ToolLabStateError(RuntimeError):
    """Raised when the durable Tool Lab state cannot be read safely."""


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _read_yaml(root: Path, relative: str) -> dict[str, Any]:
    path = Path(root) / relative
    if not path.is_file():
        raise ToolLabStateError(f"required state file not found: {relative}")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ToolLabStateError(f"cannot read {relative}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ToolLabStateError(f"state file must contain a mapping: {relative}")
    return dict(payload)


def load_tool_lab_state(root: Path) -> dict[str, Any]:
    """Load the four durable inputs used by every Tool Lab command."""

    registry_path = Path(root) / "state/capabilities.yaml"
    return {
        "root": Path(root).resolve(),
        "tool_health": _read_yaml(root, "state/tool-health.yaml"),
        "toolmap": _read_yaml(root, "state/providers/horizun-toolmap.yaml"),
        "environment": _read_yaml(root, "state/bim-environment.lock.yaml"),
        "task_graph": _read_yaml(root, "state/task-graph.yaml"),
        "registry": (
            _read_yaml(root, "state/capabilities.yaml")
            if registry_path.is_file()
            else {}
        ),
    }


def _value(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def _raw_status(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip().upper() or None
    if isinstance(value, Mapping):
        raw = _value(value, *_STATUS_KEYS)
        if raw is not None:
            return str(raw).strip().upper() or None
    return None


def _normalize_capability_status(value: Any) -> str:
    raw = _raw_status(value)
    if raw in _PASS_STATUSES:
        return "PASS"
    if raw in _FAIL_STATUSES:
        return "FAIL"
    return "UNTESTED"


def _provider_status(value: Any) -> str:
    raw = _raw_status(value)
    if raw in _PROVIDER_PASS_STATUSES:
        return "PASS"
    if raw in _FAIL_STATUSES:
        return "FAIL"
    return "UNTESTED"


def _same_provider(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    first = re.sub(r"[^a-z0-9]", "", str(left).lower())
    second = re.sub(r"[^a-z0-9]", "", str(right).lower())
    return bool(
        first and second and (first == second or first in second or second in first)
    )


def _preferred_provider(data: Mapping[str, Any]) -> str:
    toolmap = _mapping(data.get("toolmap"))
    environment = _mapping(data.get("environment"))
    for source in (toolmap, environment):
        value = _value(source, "preferred_provider", "preferred")
        if isinstance(value, str) and value.strip():
            return value.strip()
    providers = _mapping(environment.get("providers"))
    for name, entry in providers.items():
        if isinstance(entry, Mapping) and entry.get("preferred") is True:
            return str(name)
    for source in (toolmap, environment):
        value = source.get("provider")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "UNKNOWN"


def _provider_entry(container: Any, provider: str) -> Mapping[str, Any] | None:
    mapping = _mapping(container)
    for key in ("providers", "provider_health", "provider_status"):
        entries = _mapping(mapping.get(key))
        for name, entry in entries.items():
            if _same_provider(name, provider):
                return _mapping(entry)
    return None


def _provider_commit(data: Mapping[str, Any], provider: str) -> str | None:
    toolmap = _mapping(data.get("toolmap"))
    provenance = _mapping(toolmap.get("provenance"))
    commit = _value(provenance, "source_commit", "commit", "provider_commit")
    if commit is None:
        source = _mapping(toolmap.get("source"))
        commit = _value(source, "source_commit", "commit", "provider_commit")
    if commit is None:
        commit = _value(toolmap, "source_commit", "commit", "provider_commit")
    if commit is None:
        entry = _provider_entry(data.get("environment"), provider)
        if entry is not None:
            commit = _value(entry, "source_commit", "commit", "provider_commit")
            if commit is None:
                commit = _value(
                    _mapping(entry.get("source")), "commit", "source_commit"
                )
    return str(commit) if commit not in (None, "") else None


def _provider_health(data: Mapping[str, Any], provider: str) -> str:
    health = _provider_entry(data.get("tool_health"), provider)
    if health is not None:
        value = _value(health, "health", "status", "state")
        if value is not None:
            return str(value).strip().upper()
    tool_health = _mapping(data.get("tool_health"))
    revit = _mapping(tool_health.get("revit"))
    value = _value(revit, "health", "status", "state")
    if value is not None:
        return str(value).strip().upper()
    environment_entry = _provider_entry(data.get("environment"), provider)
    if environment_entry is not None:
        value = _value(environment_entry, "health", "status", "state")
        if value is not None:
            return str(value).strip().upper()
    return "UNKNOWN"


def _phase_tasks(data: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    raw_tasks = _mapping(_mapping(data.get("task_graph")).get("tasks"))
    tasks: list[tuple[str, Mapping[str, Any]]] = []
    for task_id, raw_task in raw_tasks.items():
        task = _mapping(raw_task)
        phase = str(task.get("phase", "")).upper()
        plan = str(task.get("plan_path", "")).replace("\\", "/")
        if phase == "PHASE_02" or TOOL_LAB_PLAN in plan:
            tasks.append((str(task_id), task))
    return tasks


def _task_statuses(data: Mapping[str, Any]) -> list[str]:
    return [_normalize_capability_status(task) for _, task in _phase_tasks(data)]


def _capabilities(data: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    registry_entries = _mapping(data.get("registry")).get("entries")
    if isinstance(registry_entries, list):
        capabilities: list[tuple[str, Mapping[str, Any]]] = []
        for item in registry_entries:
            entry = _mapping(item)
            scope = _mapping(entry.get("tested_scope"))
            name = _value(scope, "operation") or _value(
                entry, "operation", "capability", "name"
            )
            if name is not None:
                capabilities.append((str(name), entry))
        if capabilities:
            return capabilities
    raw = _mapping(_mapping(data.get("toolmap")).get("capabilities"))
    return [(str(name), _mapping(entry)) for name, entry in raw.items()]


def _explicit_capability_statuses(
    capabilities: list[tuple[str, Mapping[str, Any]]],
) -> bool:
    return any(_raw_status(entry) is not None for _, entry in capabilities)


def _task_matches_capability(
    name: str, task: Mapping[str, Any], *, include_id: str = ""
) -> bool:
    haystack = " ".join(
        [
            include_id,
            str(task.get("title", "")),
            " ".join(str(item) for item in task.get("evidence", []) or []),
        ]
    ).lower()
    variants = {name.lower(), name.replace("_", " ").lower()}
    if not name.lower().startswith("create_"):
        variants.add(f"create_{name}".lower())
    return any(variant and variant in haystack for variant in variants)


def _task_status_for_capability(name: str, data: Mapping[str, Any]) -> str:
    matching = [
        _normalize_capability_status(task)
        for task_id, task in _phase_tasks(data)
        if _task_matches_capability(name, task, include_id=task_id)
    ]
    if "FAIL" in matching:
        return "FAIL"
    if "PASS" in matching:
        return "PASS"
    return "UNTESTED"


def _capability_status(
    name: str, entry: Mapping[str, Any], data: Mapping[str, Any]
) -> str:
    explicit = _raw_status(entry)
    if explicit is not None:
        return _normalize_capability_status(entry)
    availability = str(entry.get("availability", "")).strip().upper()
    if availability == "NOT_AVAILABLE":
        return "FAIL"
    return _task_status_for_capability(name, data)


def _status_counts(data: Mapping[str, Any]) -> dict[str, int]:
    capabilities = _capabilities(data)
    if capabilities and _explicit_capability_statuses(capabilities):
        statuses = [
            _capability_status(name, entry, data) for name, entry in capabilities
        ]
    else:
        statuses = _task_statuses(data)
    return {status: statuses.count(status) for status in ("PASS", "FAIL", "UNTESTED")}


def _effect_is_write(value: Any) -> bool:
    effect = str(_mapping(value).get("effect", "")).strip().lower()
    return bool(
        effect
        and "readonly" not in effect
        and any(
            word in effect for word in ("mutat", "document", "external", "destruct")
        )
    )


def _is_write_capability(entry: Mapping[str, Any]) -> bool:
    for key in ("writes", "write", "mutates", "is_write"):
        if entry.get(key) is True:
            return True
    tested_scope = _mapping(entry.get("tested_scope"))
    if tested_scope.get("writes") is True or tested_scope.get("write") is True:
        return True
    if entry.get("required_fields"):
        return True
    flags = _mapping(entry.get("effect_flags"))
    return any(_effect_is_write(effect) for effect in flags.values())


def _has_required_marker(entry: Mapping[str, Any]) -> bool:
    return any(key in entry for key in ("required", "required_for", "core", "critical"))


def _is_required_capability(entry: Mapping[str, Any], *, has_markers: bool) -> bool:
    if has_markers:
        return bool(
            entry.get("required") is True
            or entry.get("core") is True
            or entry.get("critical") is True
            or entry.get("required_for")
        )
    return _is_write_capability(entry)


def _queue_items(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    capabilities = _capabilities(data)
    if capabilities:
        has_markers = any(_has_required_marker(entry) for _, entry in capabilities)
        items = [
            {
                "name": name,
                "status": _capability_status(name, entry, data),
                "required": _is_required_capability(entry, has_markers=has_markers),
                "order": index,
            }
            for index, (name, entry) in enumerate(capabilities)
        ]
        items = [item for item in items if item["required"]]
    else:
        items = [
            {
                "name": task_id,
                "status": _capability_status(task_id, task, data),
                "required": True,
                "order": index,
            }
            for index, (task_id, task) in enumerate(_phase_tasks(data))
        ]

    def sort_key(item: Mapping[str, Any]) -> tuple[int, int, int]:
        status = str(item["status"])
        if item["required"] and status == "UNTESTED":
            bucket = 0
        elif item["required"] and status == "FAIL":
            bucket = 1
        elif item["required"]:
            bucket = 2
        elif status == "UNTESTED":
            bucket = 3
        else:
            bucket = 4
        return (bucket, 0 if status == "UNTESTED" else 1, int(item["order"]))

    return sorted(items, key=sort_key)


def _safe_label(value: Any, fallback: str) -> str:
    label = str(value)
    return label if _SAFE_LABEL.fullmatch(label) else fallback


def _provider_registry_status(data: Mapping[str, Any], provider: str) -> str:
    candidates: list[str] = []
    for container in (
        data.get("tool_health"),
        data.get("environment"),
        data.get("toolmap"),
    ):
        entry = _provider_entry(container, provider)
        if entry is not None:
            raw = _raw_status(entry)
            if raw is not None:
                candidates.append(_provider_status(raw))

    toolmap = _mapping(data.get("toolmap"))
    for key in ("provider_status", "status"):
        raw = toolmap.get(key)
        if raw is not None:
            candidates.append(_provider_status(raw))

    for _, entry in _capabilities(data):
        entry_provider = _value(entry, "provider", "provider_name")
        if entry_provider is None or _same_provider(entry_provider, provider):
            raw = _raw_status(entry)
            if raw is not None:
                candidates.append(_normalize_capability_status(entry))
    if "FAIL" in candidates:
        return "FAIL"
    if candidates and all(candidate == "PASS" for candidate in candidates):
        return "PASS"
    return "UNTESTED"


def _text_contains_save_reopen(value: Any) -> bool:
    if isinstance(value, str):
        text = value.lower().replace("-", "")
        return "save" in text and ("reopen" in text or "close" in text)
    if isinstance(value, Mapping):
        for key in ("save_reopen", "persistence", "persisted"):
            if value.get(key) is True:
                return True
        saved = any(value.get(key) is True for key in ("save", "saved"))
        reopened = any(
            value.get(key) is True for key in ("reopen", "reopened", "close", "closed")
        )
        if saved and reopened:
            return True
        return any(_text_contains_save_reopen(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_text_contains_save_reopen(item) for item in value)
    return False


def _save_reopen_proven(
    name: str, entry: Mapping[str, Any], data: Mapping[str, Any]
) -> bool:
    for key in ("save_reopen", "save_reopen_evidence"):
        if key in entry:
            value = entry[key]
            if isinstance(value, bool):
                return value
            if _text_contains_save_reopen(value):
                return True
    for key in ("persistence", "persistence_evidence", "evidence"):
        if _text_contains_save_reopen(entry.get(key)):
            return True
    for task_id, task in _phase_tasks(data):
        if _task_matches_capability(
            name, task, include_id=task_id
        ) and _text_contains_save_reopen(task.get("evidence", [])):
            return True
    provider = _preferred_provider(data)
    proven = _mapping(_mapping(data.get("environment")).get("providers"))
    provider_entry = next(
        (entry for key, entry in proven.items() if _same_provider(key, provider)),
        None,
    )
    if isinstance(provider_entry, Mapping):
        for item in provider_entry.get("capabilities_proven", []) or []:
            if (
                isinstance(item, Mapping)
                and _task_matches_capability(name, item)
                and _text_contains_save_reopen(item)
            ):
                return True
    return False


def _registry_findings(data: Mapping[str, Any]) -> tuple[str, list[str]]:
    provider = _preferred_provider(data)
    findings: list[str] = []
    provider_status = _provider_registry_status(data, provider)
    if provider == "UNKNOWN":
        findings.append("preferred provider is not recorded")
    elif provider_status in {"UNTESTED", "FAIL"}:
        findings.append(f"preferred provider {provider} status {provider_status}")

    map_commit = _provider_commit(data, provider)
    environment_entry = _provider_entry(data.get("environment"), provider)
    lock_commit = _value(
        environment_entry or {}, "source_commit", "commit", "provider_commit"
    )
    if map_commit and lock_commit and str(map_commit) != str(lock_commit):
        findings.append("provider commit differs between toolmap and environment lock")

    capabilities = _capabilities(data)
    if not capabilities:
        findings.append("no capability registry entries are available")
    has_markers = any(_has_required_marker(entry) for _, entry in capabilities)
    for name, entry in capabilities:
        entry_provider = _value(entry, "provider", "provider_name")
        if entry_provider is not None and not _same_provider(entry_provider, provider):
            continue
        if not _is_required_capability(entry, has_markers=has_markers):
            continue
        status = _capability_status(name, entry, data)
        if status in {"UNTESTED", "FAIL"}:
            findings.append(f"{name}: preferred provider capability status {status}")
        if _is_write_capability(entry) and not _save_reopen_proven(name, entry, data):
            findings.append(f"{name}: write capability lacks save/reopen evidence")
    return provider, findings


def _root() -> Path:
    from .doctor import project_root

    return project_root()


@tool_lab_app.command()
def status() -> None:
    """Report provider provenance, health and Tool Lab result counts."""

    try:
        data = load_tool_lab_state(_root())
    except ToolLabStateError as exc:
        typer.echo("tool-lab status: " + str(exc), err=True)
        raise typer.Exit(code=2) from exc
    provider = _preferred_provider(data)
    commit = _provider_commit(data, provider) or "UNKNOWN"
    health = _provider_health(data, provider)
    counts = _status_counts(data)
    typer.echo("tool-lab status")
    typer.echo(f"provider {provider}")
    typer.echo(f"commit {commit}")
    typer.echo(f"health {health}")
    for key in ("PASS", "FAIL", "UNTESTED"):
        typer.echo(f"{key} {counts[key]}")
    revit = _mapping(data.get("environment")).get("revit")
    build = _value(_mapping(revit), "selected_build", "build")
    if build is not None:
        typer.echo(f"revit-build {build}")


@tool_lab_app.command()
def queue() -> None:
    """Print the deterministic evidence queue without exposing file paths."""

    try:
        data = load_tool_lab_state(_root())
    except ToolLabStateError as exc:
        typer.echo("tool-lab queue: " + str(exc), err=True)
        raise typer.Exit(code=2) from exc
    typer.echo("tool-lab queue")
    items = _queue_items(data)
    if not items:
        typer.echo("empty")
        return
    for index, item in enumerate(items, start=1):
        label = _safe_label(item["name"], f"capability-{index}")
        typer.echo(f"{index}. {item['status']} {label}")


@tool_lab_app.command(name="verify-registry")
def verify_registry() -> None:
    """Validate preferred-provider health and write persistence evidence."""

    try:
        data = load_tool_lab_state(_root())
    except ToolLabStateError as exc:
        typer.echo("tool-lab verify-registry: " + str(exc), err=True)
        raise typer.Exit(code=2) from exc
    provider, findings = _registry_findings(data)
    if findings:
        typer.echo("tool-lab registry FAIL")
        typer.echo(f"preferred {provider}")
        for finding in findings:
            typer.echo("FAIL " + finding)
        raise typer.Exit(code=1)
    typer.echo("tool-lab registry PASS")
    typer.echo(f"preferred {provider}")


__all__ = [
    "ToolLabStateError",
    "load_tool_lab_state",
    "queue",
    "status",
    "verify_registry",
]
