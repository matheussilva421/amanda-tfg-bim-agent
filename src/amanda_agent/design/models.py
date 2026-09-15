"""Typed, content-bound records exchanged by the design engine."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from amanda_agent.requirements.decisions import (
    DecisionRecord,
    ReviewStatus,
    SelectionAuthority,
)


class DesignStatus(StrEnum):
    """Lifecycle status of a generated design solution."""

    DRAFT = "DRAFT"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    APPROVED_FOR_BIM = "APPROVED_FOR_BIM"
    AMANDA_REVIEW_PENDING = "AMANDA_REVIEW_PENDING"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class ConstraintStatus(StrEnum):
    """Outcome of a constraint check at the current design resolution."""

    VIOLATION = "VIOLATION"
    NOT_EVALUATED = "NOT_EVALUATED"


class ViolationSeverity(StrEnum):
    """Severity attached to a failed or unavailable constraint check."""

    HARD = "HARD"
    SOFT = "SOFT"
    INFO = "INFO"


_PROGRAM_CAPACITY_KEYS = frozenset(
    {
        "person_capacity",
        "people_capacity",
        "program_capacity",
        "program_person_capacity",
    }
)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, BaseModel):
        return _canonicalize(value.model_dump(mode="python"))
    if isinstance(value, dict):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def _program_capacities(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _PROGRAM_CAPACITY_KEYS and isinstance(item, (int, float)):
                yield int(item)
            yield from _program_capacities(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _program_capacities(item)


class MetricSet(BaseModel):
    """Version-independent metric dimensions for one candidate.

    The dimensions deliberately remain separate.  A single beauty score is
    not a substitute for program, privacy, circulation, or accessibility
    evidence.
    """

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    program_compliance: float = Field(default=0.0, ge=0, le=1)
    privacy_security: float = Field(default=0.0, ge=0, le=1)
    adjacency: float = Field(default=0.0, ge=0, le=1)
    circulation: float = Field(default=0.0, ge=0, le=1)
    accessibility: float = Field(default=0.0, ge=0, le=1)
    constructability: float = Field(default=0.0, ge=0, le=1)
    overall_score: float | None = Field(default=None, ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def finite_values(self) -> MetricSet:
        for value in self.model_dump(exclude={"evidence"}).values():
            if (
                value is not None
                and isinstance(value, (int, float))
                and not math.isfinite(float(value))
            ):
                raise ValueError("metrics must contain finite numbers")
        return self


class ConstraintViolation(BaseModel):
    """A hard/soft check result, including checks unavailable at this stage."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    severity: ViolationSeverity = ViolationSeverity.HARD
    status: ConstraintStatus = ConstraintStatus.VIOLATION
    resolution: str | None = Field(default=None, min_length=1)
    expected: Any = None
    actual: Any = None
    evidence: list[str] = Field(default_factory=list)
    penalty: float = Field(default=0.0, ge=0)

    @model_validator(mode="before")
    @classmethod
    def accept_constraint_id_alias(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if "code" not in values and "constraint_id" in values:
            values["code"] = values.pop("constraint_id")
        return values

    @property
    def constraint_id(self) -> str:
        """Compatibility name used by validation reports."""

        return self.code

    @property
    def is_hard_violation(self) -> bool:
        return (
            self.severity is ViolationSeverity.HARD
            and self.status is ConstraintStatus.VIOLATION
        )

    def as_soft_penalty(self) -> float:
        """Return a soft penalty, refusing to soften a hard failure."""

        if self.is_hard_violation:
            raise ValueError("hard constraint violations cannot become a soft penalty")
        if self.status is ConstraintStatus.NOT_EVALUATED:
            raise ValueError("a NOT_EVALUATED check cannot become a soft penalty")
        return float(self.penalty)


def compute_design_approval_hash(solution: DesignSolution | dict[str, Any]) -> str:
    """Hash all material design content used by an execution authorization."""

    if isinstance(solution, DesignSolution):
        values = solution.model_dump(
            mode="python",
            include={
                "solution_id",
                "requirements_version",
                "site_version",
                "engine_version",
                "archetype",
                "geometry",
                "metrics",
                "hard_violations",
                "soft_penalties",
                "parents",
                "program_person_capacity",
            },
        )
    else:
        values = {
            key: solution[key]
            for key in (
                "solution_id",
                "requirements_version",
                "site_version",
                "engine_version",
                "archetype",
                "geometry",
                "metrics",
                "hard_violations",
                "soft_penalties",
                "parents",
                "program_person_capacity",
            )
            if key in solution
        }
    encoded = json.dumps(
        _canonicalize(values),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class DesignSolution(BaseModel):
    """A reproducible design candidate and its execution authority."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    solution_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    seed: int
    requirements_version: str = Field(min_length=1)
    site_version: str | int
    engine_version: str = Field(min_length=1)
    archetype: str = Field(min_length=1)
    geometry: dict[str, Any] = Field(min_length=1)
    geometry_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    metrics: MetricSet
    hard_violations: list[ConstraintViolation]
    soft_penalties: dict[str, float]
    parents: list[str]
    status: DesignStatus
    program_person_capacity: int = Field(default=20, ge=1)
    selection_authority: SelectionAuthority | None = None
    decision_evidence: DecisionRecord | None = None
    approval_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    review_status: ReviewStatus | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_authority_aliases(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if "decision_evidence" not in values and "decision_record" in values:
            values["decision_evidence"] = values.pop("decision_record")
        if "program_person_capacity" not in values:
            for alias in ("program_capacity", "person_capacity"):
                if alias in values:
                    values["program_person_capacity"] = values.pop(alias)
                    break
        for key in ("amanda_approved", "approved_by_amanda", "personal_approval"):
            if values.get(key) is True:
                raise ValueError("personal Amanda approval cannot be attributed")
        if any(capacity != 20 for capacity in _program_capacities(values)):
            raise ValueError("the fixed program capacity is 20 people")
        return values

    @model_validator(mode="after")
    def validate_execution_authority(self) -> DesignSolution:
        if self.program_person_capacity != 20:
            raise ValueError("the fixed program capacity is 20 people")
        if any(
            violation.is_hard_violation for violation in self.hard_violations
        ) and self.soft_penalties:
            overlapping = {
                violation.code
                for violation in self.hard_violations
                if violation.is_hard_violation
            }.intersection(self.soft_penalties)
            if overlapping:
                raise ValueError(
                    "hard constraint violations cannot become a soft penalty: "
                    + ", ".join(sorted(overlapping))
                )

        if self.status in {
            DesignStatus.APPROVED_FOR_BIM,
            DesignStatus.AMANDA_REVIEW_PENDING,
        }:
            if self.selection_authority is None:
                raise ValueError("BIM execution status requires selection authority")
            if self.decision_evidence is None:
                raise ValueError("BIM execution status requires decision evidence")
            if (
                self.decision_evidence.selection_authority
                is not self.selection_authority
            ):
                raise ValueError("decision evidence authority does not match solution")
            if not self.decision_evidence.approval_hash_valid:
                raise ValueError("decision evidence approval_hash is invalid")
            if (
                self.selection_authority is SelectionAuthority.AMANDA_DIRECTED
                and self.decision_evidence.review_status is not ReviewStatus.AMANDA_ACCEPTED
            ):
                raise ValueError(
                    "personal Amanda approval requires explicit accepted evidence"
                )
            if any(violation.is_hard_violation for violation in self.hard_violations):
                raise ValueError("a solution with hard violations cannot be BIM eligible")

        expected_hash = compute_design_approval_hash(self)
        if self.approval_hash is None:
            self.approval_hash = expected_hash
        elif self.approval_hash != expected_hash:
            raise ValueError("approval_hash is not bound to the solution content")
        return self

    @property
    def bim_eligible(self) -> bool:
        """Whether detailed BIM work may proceed under current evidence."""

        return (
            self.status
            in {
                DesignStatus.APPROVED_FOR_BIM,
                DesignStatus.AMANDA_REVIEW_PENDING,
            }
            and self.selection_authority
            in {
                SelectionAuthority.AGENT_DELEGATED,
                SelectionAuthority.AMANDA_DIRECTED,
            }
            and self.decision_evidence is not None
            and self.approval_hash == compute_design_approval_hash(self)
        )

    @property
    def can_execute(self) -> bool:
        """Alias used by downstream compilation gates."""

        return self.bim_eligible


__all__ = [
    "ConstraintStatus",
    "ConstraintViolation",
    "DesignSolution",
    "DesignStatus",
    "MetricSet",
    "ViolationSeverity",
    "compute_design_approval_hash",
]
