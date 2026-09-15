"""Deterministic desired/current-state reconciliation for managed BIM data."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .current_state import CurrentElement, CurrentState
from .desired_state import DesiredElement, DesiredState, load_desired_state


class DiffAction(StrEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    REPLACE = "REPLACE"
    NOOP = "NOOP"
    DELETE = "DELETE"


Action = DiffAction


class UserDivergence(RuntimeError):
    """The current managed element no longer matches its recorded baseline."""


class DocumentIdentityMismatch(RuntimeError):
    """A diff was requested for a document other than the active document."""


class DiffOperation(BaseModel):
    """One stable reconciliation operation."""

    model_config = ConfigDict(extra="forbid")

    logical_id: str = Field(min_length=1)
    action: DiffAction
    desired: DesiredElement | None = None
    current: CurrentElement | None = None
    semantic_capability: str = Field(default="bim.reconcile", min_length=1)
    cascade_count: int | None = Field(default=0, ge=0)
    cascade_unknown: bool = False
    cascade_dependents: list[str] = Field(default_factory=list)

    @property
    def destructive(self) -> bool:
        return self.action in {DiffAction.DELETE, DiffAction.REPLACE}

    @property
    def unique_id(self) -> str | None:
        return self.current.unique_id if self.current is not None else None

    @property
    def document_id(self) -> str | None:
        return self.current.document_id if self.current is not None else None


class DiffResult(BaseModel):
    """The complete stable diff, including NOOPs for auditability."""

    model_config = ConfigDict(extra="forbid")

    operations: list[DiffOperation] = Field(default_factory=list)
    managed_count: int = Field(default=0, ge=0)
    document_id: str = Field(default="unknown", min_length=1)

    @property
    def destructive_operations(self) -> list[DiffOperation]:
        return [operation for operation in self.operations if operation.destructive]

    @property
    def changed_operations(self) -> list[DiffOperation]:
        return [operation for operation in self.operations if operation.action is not DiffAction.NOOP]

    def assess_destructive_threshold(self, **kwargs: Any) -> DestructiveRiskAssessment:
        return assess_destructive_threshold(
            self.operations, managed_count=self.managed_count, **kwargs
        )


class DestructiveRiskStatus(StrEnum):
    PASS = "PASS"
    CHECKPOINT_REQUIRED = "CHECKPOINT_REQUIRED"
    HIGH_RISK_PLAN = "HIGH_RISK_PLAN"
    UNKNOWN_CASCADE = "UNKNOWN_CASCADE"
    NO_MANAGED_BASELINE = "NO_MANAGED_BASELINE"


class DestructiveThresholdError(RuntimeError):
    """The planned destructive delta is not currently authorized."""


class DestructiveThresholdConfig(BaseModel):
    """Versioned threshold values consumed by the diff safety gate."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, ge=1)
    managed_ratio: float = Field(default=0.10, gt=0, le=1)
    absolute_maximum: int = Field(default=10, ge=1)
    minimum_managed_elements: int = Field(default=10, ge=1)
    small_denominator_maximum: int = Field(default=1, ge=1)


DEFAULT_DESTRUCTIVE_THRESHOLD_YAML = """schema_version: 1
managed_ratio: 0.10
absolute_maximum: 10
minimum_managed_elements: 10
small_denominator_maximum: 1
"""


class DestructiveRiskAssessment(BaseModel):
    """Auditable outcome of evaluating the destructive part of a diff."""

    model_config = ConfigDict(extra="forbid")

    status: DestructiveRiskStatus
    managed_count: int = Field(ge=0)
    destructive_count: int = Field(ge=0)
    ratio: float = Field(ge=0)
    blocked: bool
    allowed: bool
    reason: str = Field(min_length=1)
    config_version: int = Field(ge=1)


def _coerce_operation(operation: DiffOperation | Mapping[str, Any]) -> DiffOperation:
    return operation if isinstance(operation, DiffOperation) else DiffOperation.model_validate(operation)


def _destructive_impact(operation: DiffOperation) -> tuple[int, bool]:
    if not operation.destructive:
        return 0, False
    if operation.cascade_unknown or operation.cascade_count is None:
        return 0, True
    cascade_count = max(operation.cascade_count, len(operation.cascade_dependents))
    return 1 + cascade_count, False


def assess_destructive_threshold(
    operations: Sequence[DiffOperation | Mapping[str, Any]],
    *,
    managed_count: int,
    pre_operation_checkpoint: bool = False,
    reviewed_plan: bool = False,
    release_high_risk: bool = False,
    config: DestructiveThresholdConfig | Mapping[str, Any] | None = None,
) -> DestructiveRiskAssessment:
    """Apply the versioned managed-element threshold before mutation."""

    if isinstance(managed_count, bool) or managed_count < 0:
        raise ValueError("managed_count must be a non-negative integer")
    threshold = (
        config
        if isinstance(config, DestructiveThresholdConfig)
        else DestructiveThresholdConfig.model_validate(config or {})
    )
    normalized = [_coerce_operation(operation) for operation in operations]
    destructive_count = 0
    unknown_cascade = False
    for operation in normalized:
        impact, unknown = _destructive_impact(operation)
        destructive_count += impact
        unknown_cascade = unknown_cascade or unknown
    ratio = destructive_count / managed_count if managed_count else float("inf") if destructive_count else 0.0

    if unknown_cascade:
        return DestructiveRiskAssessment(
            status=DestructiveRiskStatus.UNKNOWN_CASCADE,
            managed_count=managed_count,
            destructive_count=destructive_count,
            ratio=ratio,
            blocked=True,
            allowed=False,
            reason="cascade impact is unknown; reconcile dependents before mutation",
            config_version=threshold.schema_version,
        )
    if destructive_count == 0:
        return DestructiveRiskAssessment(
            status=DestructiveRiskStatus.PASS,
            managed_count=managed_count,
            destructive_count=0,
            ratio=0.0,
            blocked=False,
            allowed=True,
            reason="no DELETE or REPLACE operation is planned",
            config_version=threshold.schema_version,
        )
    if managed_count == 0:
        return DestructiveRiskAssessment(
            status=DestructiveRiskStatus.NO_MANAGED_BASELINE,
            managed_count=0,
            destructive_count=destructive_count,
            ratio=ratio,
            blocked=True,
            allowed=False,
            reason="destructive changes require a non-empty managed baseline",
            config_version=threshold.schema_version,
        )

    high_risk = (
        ratio > threshold.managed_ratio
        or destructive_count > threshold.absolute_maximum
        or (
            managed_count < threshold.minimum_managed_elements
            and destructive_count > threshold.small_denominator_maximum
        )
    )
    if high_risk:
        allowed = release_high_risk and reviewed_plan and pre_operation_checkpoint
        reason = (
            "HIGH_RISK_PLAN requires a pre-operation checkpoint and concrete reviewed plan"
            if not allowed
            else "HIGH_RISK_PLAN explicitly released by reviewed plan and checkpoint"
        )
        return DestructiveRiskAssessment(
            status=DestructiveRiskStatus.HIGH_RISK_PLAN,
            managed_count=managed_count,
            destructive_count=destructive_count,
            ratio=ratio,
            blocked=not allowed,
            allowed=allowed,
            reason=reason,
            config_version=threshold.schema_version,
        )
    if not pre_operation_checkpoint:
        return DestructiveRiskAssessment(
            status=DestructiveRiskStatus.CHECKPOINT_REQUIRED,
            managed_count=managed_count,
            destructive_count=destructive_count,
            ratio=ratio,
            blocked=True,
            allowed=False,
            reason="a pre-operation checkpoint is required before destructive mutation",
            config_version=threshold.schema_version,
        )
    return DestructiveRiskAssessment(
        status=DestructiveRiskStatus.PASS,
        managed_count=managed_count,
        destructive_count=destructive_count,
        ratio=ratio,
        blocked=False,
        allowed=True,
        reason="destructive delta is within the managed-element threshold",
        config_version=threshold.schema_version,
    )


def enforce_destructive_threshold(
    operations: Sequence[DiffOperation | Mapping[str, Any]],
    *,
    managed_count: int,
    **kwargs: Any,
) -> DestructiveRiskAssessment:
    assessment = assess_destructive_threshold(
        operations, managed_count=managed_count, **kwargs
    )
    if assessment.blocked:
        raise DestructiveThresholdError(assessment.reason)
    return assessment


def load_destructive_threshold(path: str | Path | None = None) -> DestructiveThresholdConfig:
    """Load an explicit versioned YAML config, or the checked-in default text."""

    payload = (
        yaml.safe_load(DEFAULT_DESTRUCTIVE_THRESHOLD_YAML)
        if path is None
        else yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    )
    return DestructiveThresholdConfig.model_validate(payload or {})


def _equivalent(left: Any, right: Any, tolerance: float) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return set(left) == set(right) and all(
            _equivalent(left[key], right[key], tolerance) for key in left
        )
    if isinstance(left, Sequence) and isinstance(right, Sequence) and not isinstance(left, (str, bytes)) and not isinstance(right, (str, bytes)):
        return len(left) == len(right) and all(
            _equivalent(a, b, tolerance) for a, b in zip(left, right, strict=True)
        )
    return left == right


def equivalent_geometry(left: Any, right: Any, *, tolerance: float = 1e-6) -> bool:
    """Compare geometry recursively using an absolute model tolerance."""

    if tolerance < 0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and non-negative")
    return _equivalent(left, right, tolerance)


def equivalent_properties(left: Mapping[str, Any], right: Mapping[str, Any], *, tolerance: float = 1e-9) -> bool:
    return equivalent_geometry(left, right, tolerance=tolerance)


def _coerce_current(current: CurrentState | Mapping[str, Any]) -> CurrentState:
    return current if isinstance(current, CurrentState) else CurrentState.model_validate(current)


def diff_states(
    desired: DesiredState | Mapping[str, Any],
    current: CurrentState | Mapping[str, Any],
    *,
    expected_document_id: str | None = None,
    geometry_tolerance: float = 1e-6,
    properties_tolerance: float = 1e-9,
) -> DiffResult:
    """Compute the smallest managed diff without mutating either state."""

    desired_state = load_desired_state(desired)
    current_state = _coerce_current(current)
    if expected_document_id is not None and current_state.document_id != expected_document_id:
        raise DocumentIdentityMismatch(
            "document identity mismatch: "
            f"expected {expected_document_id!r}, got {current_state.document_id!r}"
        )

    desired_by_id = desired_state.by_logical_id()
    current_by_id = current_state.managed_by_logical_id()
    all_ids = sorted(set(desired_by_id) | set(current_by_id))
    operations: list[DiffOperation] = []
    for logical_id in all_ids:
        expected = desired_by_id.get(logical_id)
        observed = current_by_id.get(logical_id)
        if expected is None:
            operations.append(
                DiffOperation(logical_id=logical_id, action=DiffAction.DELETE, current=observed)
            )
            continue
        if observed is None:
            operations.append(
                DiffOperation(logical_id=logical_id, action=DiffAction.CREATE, desired=expected)
            )
            continue
        if observed.diverged:
            raise UserDivergence(
                f"user divergence detected for managed logical_id {logical_id}"
            )
        geometry_same = equivalent_geometry(
            expected.geometry, observed.geometry, tolerance=geometry_tolerance
        )
        properties_same = equivalent_properties(
            expected.properties, observed.properties, tolerance=properties_tolerance
        )
        if geometry_same and properties_same and expected.category == observed.category:
            action = DiffAction.NOOP
        elif expected.category != observed.category:
            action = DiffAction.REPLACE
        else:
            action = DiffAction.UPDATE
        operations.append(
            DiffOperation(logical_id=logical_id, action=action, desired=expected, current=observed)
        )

    return DiffResult(
        operations=operations,
        managed_count=len(current_by_id),
        document_id=current_state.document_id,
    )


compute_diff = diff_states
desired_current_diff = diff_states


__all__ = [
    "DEFAULT_DESTRUCTIVE_THRESHOLD_YAML",
    "Action",
    "DestructiveRiskAssessment",
    "DestructiveRiskStatus",
    "DestructiveThresholdConfig",
    "DestructiveThresholdError",
    "DiffAction",
    "DiffOperation",
    "DiffResult",
    "DocumentIdentityMismatch",
    "UserDivergence",
    "assess_destructive_threshold",
    "compute_diff",
    "desired_current_diff",
    "diff_states",
    "enforce_destructive_threshold",
    "equivalent_geometry",
    "equivalent_properties",
    "load_destructive_threshold",
]
