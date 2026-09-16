"""Durable, append-only execution journal for the BIM CLI boundary."""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .plan import BimPlan, PlanOperation

JOURNAL_FILENAME = "BIM_EXECUTION_JOURNAL.jsonl"
JOURNAL_SCHEMA_VERSION = 1


class JournalError(RuntimeError):
    """The execution journal cannot safely advance an operation."""


def _regular_file(path: Path, *, label: str) -> Path:
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise JournalError(f"{label} is missing or mutable: {candidate}")
    return candidate.resolve()


def sha256_file(path: Path) -> str:
    """Return the content hash of a trusted regular file."""

    candidate = _regular_file(Path(path), label="file")
    digest = hashlib.sha256()
    try:
        with candidate.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise JournalError(f"cannot hash file: {candidate}") from exc
    return digest.hexdigest()


def _payload_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_plan(path: Path) -> BimPlan:
    candidate = _regular_file(path, label="plan")
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        return BimPlan.model_validate(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise JournalError(f"invalid BIM plan: {candidate}") from exc


@contextmanager
def _journal_lock(path: Path):
    """Hold a process-safe advisory lock while reading and appending events."""

    lock_path = path.with_name(path.name + ".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt

            while True:
                try:
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.01)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class ExecutionJournal:
    """Read and append execution events without rewriting prior evidence."""

    def __init__(self, path: Path):
        candidate = Path(path)
        if candidate.is_symlink():
            raise JournalError(f"journal is mutable: {candidate}")
        self.path = candidate.resolve(strict=False)

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        if self.path.is_symlink() or not self.path.is_file():
            raise JournalError(f"journal is missing or mutable: {self.path}")
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise JournalError(f"journal cannot be read: {self.path}") from exc
        events: list[dict[str, Any]] = []
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                raise JournalError(f"journal contains an empty event at line {line_number}")
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise JournalError(
                    f"journal contains invalid JSON at line {line_number}"
                ) from exc
            if not isinstance(event, dict):
                raise JournalError(f"journal event at line {line_number} is not an object")
            events.append(event)
        return events

    @property
    def events(self) -> list[dict[str, Any]]:
        """Return a fresh snapshot of all durable events."""

        return self._read_unlocked()

    @property
    def event_count(self) -> int:
        return len(self.events)

    def _latest_by_operation(self, events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for event in events:
            operation_id = event.get("operation_id")
            if isinstance(operation_id, str) and operation_id:
                latest[operation_id] = event
        return latest

    def state_for(self, operation_id: str) -> str | None:
        event = self._latest_by_operation(self.events).get(operation_id)
        state = event.get("state") if event else None
        return state if isinstance(state, str) else None

    def _append_unlocked(self, event: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_symlink() or (
            self.path.exists() and not self.path.is_file()
        ):
            raise JournalError(f"journal is missing or mutable: {self.path}")
        serialized = json.dumps(
            event,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        try:
            with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(serialized + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            raise JournalError(f"journal append failed: {self.path}") from exc

    def claim(self, plan_path: Path) -> dict[str, Any]:
        """Atomically claim the first operation that is still READY."""

        plan = _load_plan(plan_path)
        resolved_plan = Path(plan_path).resolve()
        plan_hash = sha256_file(resolved_plan)
        with _journal_lock(self.path):
            events = self._read_unlocked()
            latest = self._latest_by_operation(events)
            for operation_index, operation in enumerate(plan.operations):
                previous = latest.get(operation.task_id)
                if previous is not None:
                    previous_hash = previous.get("plan_sha256")
                    if previous_hash != plan_hash:
                        raise JournalError(
                            f"operation {operation.task_id} belongs to a stale plan"
                        )
                    state = previous.get("state")
                    if state == "CLAIMED":
                        raise JournalError(f"operation {operation.task_id} is already claimed")
                    if state == "IN_DOUBT":
                        raise JournalError(
                            f"operation {operation.task_id} is IN_DOUBT and needs reconciliation"
                        )
                    if state == "FAILED":
                        raise JournalError(f"operation {operation.task_id} has failed")
                    if state == "VERIFIED":
                        continue
                dependencies = [
                    prior.task_id
                    for prior in plan.operations[:operation_index]
                    if latest.get(prior.task_id, {}).get("state") == "VERIFIED"
                ]
                event = self._claim_event(
                    plan=plan,
                    plan_path=resolved_plan,
                    plan_hash=plan_hash,
                    operation=operation,
                    dependencies=dependencies,
                    event_number=len(events) + 1,
                )
                self._append_unlocked(event)
                return event
        raise JournalError("the BIM plan has no READY operation")

    def _claim_event(
        self,
        *,
        plan: BimPlan,
        plan_path: Path,
        plan_hash: str,
        operation: PlanOperation,
        dependencies: list[str],
        event_number: int,
    ) -> dict[str, Any]:
        provider = operation.preferred_provider
        return {
            "event": "CLAIM",
            "event_number": event_number,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "journal_schema_version": JOURNAL_SCHEMA_VERSION,
            "operation_id": operation.task_id,
            "task_id": operation.task_id,
            "logical_id": operation.logical_id,
            "state": "CLAIMED",
            "plan_path": str(plan_path),
            "plan_sha256": plan_hash,
            "input_hashes": {
                "plan": plan_hash,
                "desired_payload": _payload_hash(operation.desired_payload),
            },
            "checkpoint_hash": None,
            "document_hash": None,
            "lease_token": uuid.uuid4().hex,
            "provider_version": provider,
            "schema_version": plan.schema_version,
            "tool_schema_hash": operation.tool_schema_hash,
            "provider_schema_versions": {
                "provider": provider,
                "revit_build": operation.revit_build,
                "tool_schema_hash": operation.tool_schema_hash,
            },
            "dependencies": dependencies,
            "intended_delta": {
                "action": operation.action.value,
                "logical_id": operation.logical_id,
                "semantic_capability": operation.semantic_capability,
                "payload": operation.desired_payload,
            },
            "verifier": operation.verification_rules,
        }

    def record_result(self, operation_id: str, evidence_path: Path) -> dict[str, Any]:
        """Append a VERIFIED/PASS event after independent evidence validation."""

        evidence = validate_evidence_path(evidence_path)
        evidence_hash = sha256_file(evidence)
        with _journal_lock(self.path):
            events = self._read_unlocked()
            latest = self._latest_by_operation(events)
            claim = latest.get(operation_id)
            if claim is None:
                raise JournalError(f"operation {operation_id} has no claim")
            if claim.get("state") == "VERIFIED":
                raise JournalError(f"operation {operation_id} is already verified")
            if claim.get("state") != "CLAIMED":
                raise JournalError(
                    f"operation {operation_id} cannot record a result from state "
                    + str(claim.get("state"))
                )

            plan_path = Path(str(claim.get("plan_path", "")))
            plan = _load_plan(plan_path)
            if sha256_file(plan_path) != claim.get("plan_sha256"):
                raise JournalError("claimed plan changed before result recording")
            operation = next(
                (item for item in plan.operations if item.task_id == operation_id),
                None,
            )
            if operation is None:
                raise JournalError(f"operation {operation_id} is absent from the claimed plan")
            event = {
                "event": "RESULT",
                "event_number": len(events) + 1,
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "journal_schema_version": JOURNAL_SCHEMA_VERSION,
                "operation_id": operation_id,
                "task_id": operation.task_id,
                "logical_id": operation.logical_id,
                "state": "VERIFIED",
                "result_status": "PASS",
                "plan_path": str(plan_path.resolve()),
                "plan_sha256": claim["plan_sha256"],
                "input_hashes": claim.get("input_hashes", {}),
                "checkpoint_hash": claim.get("checkpoint_hash"),
                "document_hash": claim.get("document_hash"),
                "lease_token": claim.get("lease_token"),
                "provider_version": claim.get("provider_version"),
                "schema_version": claim.get("schema_version"),
                "tool_schema_hash": claim.get("tool_schema_hash"),
                "provider_schema_versions": claim.get("provider_schema_versions", {}),
                "dependencies": claim.get("dependencies", []),
                "intended_delta": claim.get("intended_delta", {}),
                "verifier": claim.get("verifier", []),
                "evidence_path": str(evidence),
                "evidence_sha256": evidence_hash,
                "evidence_bytes": evidence.stat().st_size,
                "independent_evidence": True,
            }
            self._append_unlocked(event)
            return event


def validate_evidence_path(path: Path) -> Path:
    """Require an existing, non-empty, non-symlink evidence artifact."""

    candidate = _regular_file(Path(path), label="evidence path")
    try:
        if candidate.stat().st_size == 0:
            raise JournalError(f"evidence path is empty: {candidate}")
    except OSError as exc:
        raise JournalError(f"evidence path cannot be inspected: {candidate}") from exc
    return candidate


def locate_journal(
    operation_id: str,
    evidence_path: Path,
    *,
    working_directory: Path | None = None,
) -> ExecutionJournal:
    """Find the durable journal beside evidence or in the invoking directory."""

    evidence = Path(evidence_path).resolve(strict=False)
    roots = [evidence.parent]
    if working_directory is not None:
        roots.append(Path(working_directory).resolve())
    roots.append(Path.cwd().resolve())
    seen: set[Path] = set()
    for root in roots:
        candidate = root / JOURNAL_FILENAME
        if candidate in seen or candidate.is_symlink() or not candidate.is_file():
            continue
        seen.add(candidate)
        journal = ExecutionJournal(candidate)
        if journal.state_for(operation_id) is not None:
            return journal
    raise JournalError(f"no journal claim found for operation {operation_id}")


__all__ = [
    "JOURNAL_FILENAME",
    "ExecutionJournal",
    "JournalError",
    "locate_journal",
    "sha256_file",
    "validate_evidence_path",
]
