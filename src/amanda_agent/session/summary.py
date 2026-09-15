"""Compact, link-based summaries for one autonomous execution."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..security.redaction import redact_text


def _items(value: Iterable[Any] | Any | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values = (value,)
    else:
        try:
            values = tuple(value)
        except TypeError:
            values = (value,)
    return tuple(redact_text(str(item).strip()) for item in values if str(item).strip())


@dataclass(frozen=True)
class RunSummary:
    """The outcome ledger for a run, with raw artifacts kept out of prose."""

    attempted: tuple[str, ...] = ()
    changed: tuple[str, ...] = ()
    passed: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()
    rolled_back: tuple[str, ...] = ()
    next_tasks: tuple[str, ...] = ()
    log_paths: tuple[str, ...] = ()
    evidence_paths: tuple[str, ...] = ()
    provider: str | None = None
    fallback_provider: str | None = None
    fallback_used: bool = False
    provider_events: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "attempted",
            "changed",
            "passed",
            "failed",
            "rolled_back",
            "next_tasks",
            "log_paths",
            "evidence_paths",
            "provider_events",
        ):
            object.__setattr__(self, field_name, _items(getattr(self, field_name)))
        for field_name in ("provider", "fallback_provider"):
            value = getattr(self, field_name)
            object.__setattr__(
                self,
                field_name,
                redact_text(str(value).strip()) if value is not None and str(value).strip() else None,
            )

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> RunSummary:
        if not isinstance(values, Mapping):
            raise TypeError("run summary must be a mapping")
        payload = dict(values)
        if "next_tasks" not in payload and "next" in payload:
            payload["next_tasks"] = payload["next"]
        return cls(**{field: payload[field] for field in cls.__dataclass_fields__ if field in payload})

    @property
    def next(self) -> tuple[str, ...]:
        return self.next_tasks


def _section(title: str, values: Iterable[str]) -> str:
    entries = tuple(values)
    body = "\n".join("- " + redact_text(value) for value in entries) or "- none recorded"
    return f"## {title}\n\n{body}\n\n"


def _links(title: str, paths: Iterable[str]) -> str:
    entries = tuple(paths)
    body = "\n".join(
        f"- [{redact_text(path)}]({redact_text(path)})" for path in entries
    ) or "- none recorded"
    return f"## {title}\n\n{body}\n\n"


def render_run_summary(summary: RunSummary | Mapping[str, Any]) -> str:
    """Render outcomes and links while avoiding raw log/payload insertion."""

    record = summary if isinstance(summary, RunSummary) else RunSummary.from_mapping(summary)
    provider = record.provider or "NOT_RECORDED"
    fallback = record.fallback_provider or "NOT_USED"
    fallback_status = "used" if record.fallback_used else "not used"
    return (
        "# Session run summary\n\n"
        + _section("Attempted", record.attempted)
        + _section("Changed", record.changed)
        + _section("Passed", record.passed)
        + _section("Failed", record.failed)
        + _section("Rolled back", record.rolled_back)
        + _section("Next", record.next_tasks)
        + _links("Logs", record.log_paths)
        + _links("Evidence", record.evidence_paths)
        + "## Provider and fallback usage\n\n"
        + f"- Provider: `{provider}`\n"
        + f"- Fallback provider: `{fallback}`\n"
        + f"- Fallback used: `{fallback_status}`\n"
        + _section("Provider events", record.provider_events)
    )


def write_run_summary(
    root: Path,
    summary: RunSummary | Mapping[str, Any],
    *,
    filename: str = "run-summary.md",
) -> Path:
    """Atomically persist the human summary under ``docs/reports``."""

    target = Path(root).resolve() / "docs" / "reports" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    content = render_run_summary(summary)
    handle, temporary_name = tempfile.mkstemp(
        prefix=".run-summary.", suffix=".tmp", dir=target.parent
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


render_summary = render_run_summary
write_summary = write_run_summary


__all__ = [
    "RunSummary",
    "render_run_summary",
    "render_summary",
    "write_run_summary",
    "write_summary",
]
