"""Typed save/close/reopen evidence for release candidates.

This module deliberately keeps the persistence gate as an ordered record.  A
provider boolean or a single saved flag cannot prove a cold reopen.
Callbacks used by PersistenceCoordinator must return typed evidence for each
step.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..redaction import redact


class PersistenceStatus(StrEnum):
    """Status of one independently evidenced persistence step."""

    NOT_RUN = "NOT_RUN"
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    IN_DOUBT = "IN_DOUBT"

    NOT_STARTED = NOT_RUN


class PersistenceStep(StrEnum):
    """Required order for an RC cold-persistence verification."""

    SAVE_RC = "save_rc"
    WAIT_SAVE_COMPLETION = "wait_save_completion"
    CLOSE_AND_HASH = "close_and_hash"
    PROCESS_EXIT = "process_exit"
    START_REVIT_2027 = "start_revit_2027"
    OPEN_RC = "open_rc"
    RECONNECT_PROVIDER = "reconnect_provider"
    PROVIDER_HEALTH = "provider_health"
    CRITICAL_QA = "critical_qa"
    SEMANTIC_STATE = "semantic_state"

    # Descriptive aliases for callers that use the shorter plan vocabulary.
    SAVE = SAVE_RC
    WAIT_FOR_SAVE = WAIT_SAVE_COMPLETION
    CLOSE_HASH = CLOSE_AND_HASH
    START_REVIT = START_REVIT_2027
    REOPEN_RC = OPEN_RC
    RECONNECT = RECONNECT_PROVIDER
    HEALTH = PROVIDER_HEALTH
    QA = CRITICAL_QA
    SEMANTIC_COMPARE = SEMANTIC_STATE


REQUIRED_SEQUENCE: tuple[PersistenceStep, ...] = tuple(PersistenceStep)


class PersistenceIncompleteError(RuntimeError):
    """The record cannot be used as release evidence."""

    def __init__(self, message: str, *, record: PersistenceRecord | None = None) -> None:
        self.record = record
        super().__init__(message)


class PersistenceStepRecord(BaseModel):
    """One typed step and its redacted evidence."""

    model_config = ConfigDict(extra="forbid")

    step: PersistenceStep
    status: PersistenceStatus = PersistenceStatus.NOT_RUN
    detail: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def redact_evidence(self) -> PersistenceStepRecord:
        self.evidence = redact(self.evidence)
        return self


def _empty_steps() -> list[PersistenceStepRecord]:
    return [PersistenceStepRecord(step=step) for step in REQUIRED_SEQUENCE]


class PersistenceRecord(BaseModel):
    """Complete ordered persistence evidence for one release candidate."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, ge=1)
    release_id: str = Field(min_length=1)
    steps: list[PersistenceStepRecord] = Field(default_factory=_empty_steps)
    saved_file_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    final_file_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    later_save_changed_bytes: bool = False
    revalidated_after_later_save: bool = False
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_steps(cls, values: Any) -> Any:
        if not isinstance(values, Mapping):
            return values
        normalized = dict(values)
        supplied = normalized.get("steps")
        if isinstance(supplied, Mapping):
            normalized["steps"] = [
                (
                    value
                    if isinstance(value, Mapping) and "step" in value
                    else {
                        "step": key,
                        "status": (
                            value.get("status", PersistenceStatus.NOT_RUN)
                            if isinstance(value, Mapping)
                            else value
                        ),
                        "evidence": (
                            value.get("evidence", {})
                            if isinstance(value, Mapping)
                            else {}
                        ),
                    }
                )
                for key, value in supplied.items()
            ]
        return normalized

    @model_validator(mode="after")
    def normalize_sequence(self) -> PersistenceRecord:
        by_step = {item.step: item for item in self.steps}
        unknown = set(by_step) - set(REQUIRED_SEQUENCE)
        if unknown:
            raise ValueError("unknown persistence steps: " + ", ".join(sorted(map(str, unknown))))
        self.steps = [
            by_step.get(step, PersistenceStepRecord(step=step))
            for step in REQUIRED_SEQUENCE
        ]
        return self

    def record_step(
        self,
        step: PersistenceStep | str,
        *,
        status: PersistenceStatus | str,
        evidence: Mapping[str, Any] | None = None,
        detail: str = "",
    ) -> PersistenceStepRecord:
        """Replace one step with a typed, redacted observation."""

        selected = step if isinstance(step, PersistenceStep) else PersistenceStep(step)
        replacement = PersistenceStepRecord(
            step=selected,
            status=PersistenceStatus(status),
            detail=detail,
            evidence=dict(evidence or {}),
        )
        for index, current in enumerate(self.steps):
            if current.step is selected:
                self.steps[index] = replacement
                break
        else:
            raise ValueError("unknown persistence step: " + str(step))
        return replacement

    def step(self, step: PersistenceStep | str) -> PersistenceStepRecord:
        selected = step if isinstance(step, PersistenceStep) else PersistenceStep(step)
        return next(item for item in self.steps if item.step is selected)

    @property
    def missing_steps(self) -> list[PersistenceStep]:
        return [
            item.step
            for item in self.steps
            if item.status is not PersistenceStatus.PASS
        ]

    @property
    def sequence_valid(self) -> bool:
        """Whether no later step passed before an earlier step passed."""

        seen_nonpass = False
        for item in self.steps:
            if item.status is not PersistenceStatus.PASS:
                seen_nonpass = True
            elif seen_nonpass:
                return False
        return True

    @property
    def incomplete_reasons(self) -> list[str]:
        reasons: list[str] = []
        if not self.sequence_valid:
            reasons.append("persistence steps are out of order or have a gap")
        for item in self.steps:
            if item.status is not PersistenceStatus.PASS:
                reasons.append(f"{item.step.value} is {item.status.value}")
        if self.later_save_changed_bytes and not self.revalidated_after_later_save:
            reasons.append("later save changed bytes without regenerated hashes and revalidation")
        return reasons

    @property
    def is_complete(self) -> bool:
        return (
            self.sequence_valid
            and not self.missing_steps
            and not (
                self.later_save_changed_bytes
                and not self.revalidated_after_later_save
            )
        )

    @property
    def promotion_ready(self) -> bool:
        return self.is_complete

    def require_complete(self) -> PersistenceRecord:
        if not self.is_complete:
            raise PersistenceIncompleteError(
                "persistence sequence incomplete: " + "; ".join(self.incomplete_reasons),
                record=self,
            )
        return self

    def mark_later_save(
        self,
        *,
        changed_bytes: bool,
        revalidated: bool = False,
        final_file_sha256: str | None = None,
    ) -> None:
        """Record the extra revalidation obligation after a later save."""

        self.later_save_changed_bytes = changed_bytes
        self.revalidated_after_later_save = revalidated
        if final_file_sha256 is not None:
            self.final_file_sha256 = final_file_sha256

    def to_file(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                self.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            ),
            encoding="utf-8",
        )
        return target

    @classmethod
    def from_file(cls, path: str | Path) -> PersistenceRecord:
        source = Path(path)
        return cls.model_validate(json.loads(source.read_text(encoding="utf-8")))


def sha256_file(path: str | Path) -> str:
    """Hash a closed stable file in bounded chunks."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def persist_record(record: PersistenceRecord, release_directory: str | Path) -> Path:
    """Persist deterministic evidence in the release directory."""

    return record.to_file(Path(release_directory) / "persistence.json")


def load_record(path: str | Path) -> PersistenceRecord:
    return PersistenceRecord.from_file(path)


def _typed_result(
    step: PersistenceStep,
    result: Any,
) -> tuple[PersistenceStatus, dict[str, Any], str]:
    if isinstance(result, PersistenceStepRecord):
        return result.status, result.evidence, result.detail
    if isinstance(result, Mapping):
        return (
            PersistenceStatus(result.get("status", PersistenceStatus.PASS)),
            dict(result.get("evidence", {})),
            str(result.get("detail", "")),
        )
    if isinstance(result, PersistenceStatus):
        return result, {}, ""
    if isinstance(result, bool):
        return (
            PersistenceStatus.BLOCKED,
            {},
            "boolean callback result is not typed persistence evidence",
        )
    if result is None:
        return (
            PersistenceStatus.BLOCKED,
            {},
            f"{step.value} returned no typed persistence evidence",
        )
    raise TypeError(f"{step.value} callback returned unsupported evidence")


class PersistenceCoordinator:
    """Run the fixed persistence protocol through injected boundaries."""

    def __init__(
        self,
        release_id: str,
        actions: Mapping[PersistenceStep | str, Callable[[], Any]],
        *,
        release_directory: str | Path | None = None,
    ) -> None:
        self.release_id = release_id
        self.actions = {
            key if isinstance(key, PersistenceStep) else PersistenceStep(key): callback
            for key, callback in actions.items()
        }
        self.release_directory = Path(release_directory) if release_directory else None

    def run(self) -> PersistenceRecord:
        record = PersistenceRecord(release_id=self.release_id)
        for step in REQUIRED_SEQUENCE:
            action = self.actions.get(step)
            if action is None:
                record.record_step(
                    step,
                    status=PersistenceStatus.BLOCKED,
                    detail="required persistence action was not provided",
                )
                break
            try:
                status, evidence, detail = _typed_result(step, action())
            except Exception as exc:
                status, evidence, detail = (
                    PersistenceStatus.FAIL,
                    {},
                    f"{type(exc).__name__}: {exc}",
                )
            record.record_step(
                step,
                status=status,
                evidence=evidence,
                detail=detail,
            )
            if status is not PersistenceStatus.PASS:
                break

            if step is PersistenceStep.CLOSE_AND_HASH:
                digest = evidence.get("sha256")
                if isinstance(digest, str) and len(digest) == 64:
                    record.saved_file_sha256 = digest
        if self.release_directory is not None:
            persist_record(record, self.release_directory)
        return record


__all__ = [
    "PersistenceCoordinator",
    "PersistenceIncompleteError",
    "PersistenceRecord",
    "PersistenceStatus",
    "PersistenceStep",
    "PersistenceStepRecord",
    "REQUIRED_SEQUENCE",
    "load_record",
    "persist_record",
    "sha256_file",
]
