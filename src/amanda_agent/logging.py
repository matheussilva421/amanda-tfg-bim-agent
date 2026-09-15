"""Append-only JSONL event log with redaction applied before persisting.

Redaction happens on the way in, not on the way out, so an unhandled failure
cannot leave a credential on disk. Each line is a self-contained JSON object,
which keeps the log readable after a crash mid-run and lets several processes
append concurrently on Windows without a shared lock.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .redaction import redact, redact_text


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class EventLog:
    path: Path
    task: str
    provider: str | None = None
    _sequence: int = field(default=0, repr=False)

    def _next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    def record(
        self,
        *,
        operation: str,
        status: str,
        provider: str | None = None,
        detail: str | None = None,
        data: dict | None = None,
        **extra,
    ) -> dict:
        event = {
            "timestamp_utc": _utc_now(),
            "sequence": self._next_sequence(),
            "task": self.task,
            "operation": operation,
            "provider": provider or self.provider,
            "status": status,
            "pid": os.getpid(),
        }
        if detail is not None:
            event["detail"] = redact_text(str(detail))
        if data is not None:
            event["data"] = redact(data)
        for key, value in extra.items():
            if isinstance(value, str):
                event[key] = redact_text(value)
            else:
                event[key] = redact(value)
        self._append(redact(event))
        return event

    def record_exception(
        self,
        *,
        operation: str,
        error: BaseException,
        provider: str | None = None,
        data: dict | None = None,
    ) -> dict:
        return self.record(
            operation=operation,
            provider=provider,
            status="FAIL",
            detail=redact_text(str(error)),
            data=data,
            error_type=type(error).__name__,
            error_message=redact_text(str(error)),
        )

    def _append(self, event: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(line)
            stream.flush()
            os.fsync(stream.fileno())


@dataclass
class EventReadResult:
    events: list[dict]
    problems: list[str] = field(default_factory=list)

    def __iter__(self):
        return iter(self.events)

    def __len__(self) -> int:
        return len(self.events)

    def __getitem__(self, index):
        return self.events[index]


def read_events(
    path: Path, *, include_problems: bool = False
) -> EventReadResult:
    """Read back well-formed events; unparsable lines are reported, not fatal."""
    result = EventReadResult(events=[])
    path = Path(path)
    if not path.exists():
        return result
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for number, line in enumerate(stream, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                result.problems.append(
                    "unparsable JSONL record at line " + str(number)
                )
                continue
            if isinstance(parsed, dict):
                result.events.append(parsed)
            else:
                result.problems.append("non-object record at line " + str(number))
    if not include_problems:
        return EventReadResult(events=result.events, problems=result.problems)
    return result
