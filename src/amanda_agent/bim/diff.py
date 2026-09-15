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


class DiffReason(StrEnum):
    """Machine-readable reason for a refused reconciliation."""

    INVALID_INPUT = "INVALID_INPUT"
    DUPLICATE_CURRENT_IDENTITY = "DUPLICATE_CURRENT_IDENTITY"
    USER_DIVERGENCE = "USER_DIVERGENCE"
    DOCUMENT_IDENTITY_MISMATCH = "DOCUMENT_IDENTITY_MISMATCH"


class DiffError(ValueError):
    """Base error carrying a non-silent diff refusal reason."""

    def __init__(self, message: str, *, reason_code: DiffReason) -> None:
        self.reason_code = reason_code
        self.reason = reason_code
        super().__init__(message)


class DuplicateCurrentIdentity(DiffError):
    """Two current elements claim the same persistent Revit identity."""

    def __init__(self, message: str) -> None:
        super().__init__(message, reason_code=DiffReason.DUPLICATE_CURRENT_IDENTITY)


class UserDivergence(DiffError):
    """The current managed element no longer matches its recorded baseline."""

    def __init__(self, message: str) -> None:
        super().__init__(message, reason_code=DiffReason.USER_DIVERGENCE)


class DocumentIdentityMismatch(DiffError):
    """A diff was requested for a document other than the active document."""

    def __init__(self, message: str) -> None:
        super().__init__(message, reason_code=DiffReason.DOCUMENT_IDENTITY_MISMATCH)


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
    type_changed: bool = False
    unmanaged_dependents: list[str] = Field(default_factory=list)

    @property
    def destructive(self) -> bool:
        return self.action in {DiffAction.DELETE, DiffAction.REPLACE} or self.type_changed

    @property
    def unique_id(self) -> str | None:
        return self.current.unique_id if self.current is not None else None

    @property
    def document_id(self) -> str | None:
        return self.current.document_id if self.current is not None else None

    @property
    def identity(self) -> dict[str, str | None]:
        """Persistent identity; ``element_id`` is intentionally excluded."""

        return {
            "logical_id": self.logical_id,
            "unique_id": self.unique_id,
            "document_id": self.document_id,
        }

    @property
    def persistent_identity(self) -> dict[str, str | None]:
        """Explicit alias for callers serializing reconciliation evidence."""

        return self.identity


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

    @property
    def identity_map(self) -> dict[str, dict[str, str | None]]:
        """Stable logical-to-Revit identity mapping for audit output."""

        return {
            operation.logical_id: operation.identity
            for operation in self.operations
            if operation.current is not None
        }

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

    def __init__(
        self,
        message: str,
        *,
        assessment: DestructiveRiskAssessment | None = None,
    ) -> None:
        self.assessment = assessment
        self.reason_code = assessment.status if assessment is not None else "THRESHOLD_BLOCKED"
        self.reason = self.reason_code
        super().__init__(message)


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
    direct_destructive_count: int = Field(default=0, ge=0)
    cascade_count: int = Field(default=0, ge=0)
    impact_breakdown: list[dict[str, Any]] = Field(default_factory=list)
    calculation: str = Field(default="", min_length=1)
    override_requested: bool = False
    override_applied: bool = False
    audit_reference: str | None = None
    evidence: str = Field(default="", min_length=1)


def _coerce_operation(operation: DiffOperation | Mapping[str, Any]) -> DiffOperation:
    return operation if isinstance(operation, DiffOperation) else DiffOperation.model_validate(operation)


def _impact_parts(operation: DiffOperation) -> tuple[int, int, bool]:
    if not operation.destructive:
        return 0, 0, False
    dependent_ids = set(operation.cascade_dependents)
    dependent_ids.update(operation.unmanaged_dependents)
    cascade_count = max(operation.cascade_count or 0, len(dependent_ids))
    return 1, cascade_count, operation.cascade_unknown or operation.cascade_count is None


def _destructive_impact(operation: DiffOperation) -> tuple[int, bool]:
    direct_count, cascade_count, unknown = _impact_parts(operation)
    return direct_count + cascade_count, unknown


def _risk_evidence(
    *,
    managed_count: int,
    destructive_count: int,
    direct_count: int,
    cascade_count: int,
    breakdown: list[dict[str, Any]],
    audit_reference: str | None,
) -> tuple[str, str]:
    denominator = managed_count if managed_count else 0
    ratio = "inf" if managed_count == 0 and destructive_count else f"{destructive_count / managed_count:.6f}"
    calculation = (
        f"{destructive_count}/{denominator} managed elements; "
        f"ratio={ratio}; direct={direct_count}; cascade={cascade_count}"
    )
    evidence = calculation
    if breakdown:
        evidence += "; impacts=" + ",".join(
            f"{item['logical_id']}:{item['impact_count']}" for item in breakdown
        )
    if audit_reference:
        evidence += f"; audit_reference={audit_reference}"
    return calculation, evidence


def assess_destructive_threshold(
    operations: Sequence[DiffOperation | Mapping[str, Any]],
    *,
    managed_count: int,
    pre_operation_checkpoint: bool = False,
    reviewed_plan: bool = False,
    release_high_risk: bool = False,
    config: DestructiveThresholdConfig | Mapping[str, Any] | None = None,
    override: bool = False,
    explicit_override: bool = False,
    audit_reference: str | None = None,
) -> DestructiveRiskAssessment:
    """Apply the versioned managed-element threshold before mutation."""

    if isinstance(managed_count, bool) or not isinstance(managed_count, int) or managed_count < 0:
        raise ValueError("managed_count must be a non-negative integer")
    threshold = (
        config
        if isinstance(config, DestructiveThresholdConfig)
        else DestructiveThresholdConfig.model_validate(config or {})
    )
    normalized = sorted(
        (_coerce_operation(operation) for operation in operations),
        key=lambda operation: (operation.logical_id, operation.action.value),
    )
    destructive_count = 0
    direct_destructive_count = 0
    cascade_count = 0
    unknown_cascade = False
    breakdown: list[dict[str, Any]] = []
    for operation in normalized:
        direct_count, operation_cascade_count, unknown = _impact_parts(operation)
        impact = direct_count + operation_cascade_count
        destructive_count += impact
        direct_destructive_count += direct_count
        cascade_count += operation_cascade_count
        unknown_cascade = unknown_cascade or unknown
        if direct_count:
            breakdown.append(
                {
                    "logical_id": operation.logical_id,
                    "action": operation.action.value,
                    "direct_count": direct_count,
                    "cascade_count": operation_cascade_count,
                    "impact_count": impact,
                }
            )
    ratio = destructive_count / managed_count if managed_count else float("inf") if destructive_count else 0.0
    requested_override = bool(override or explicit_override or release_high_risk)
    audit_reference = audit_reference.strip() if isinstance(audit_reference, str) else None
    calculation, evidence = _risk_evidence(
        managed_count=managed_count,
        destructive_count=destructive_count,
        direct_count=direct_destructive_count,
        cascade_count=cascade_count,
        breakdown=breakdown,
        audit_reference=audit_reference,
    )

    def result(
        *,
        status: DestructiveRiskStatus,
        blocked: bool,
        allowed: bool,
        reason: str,
        override_applied: bool = False,
    ) -> DestructiveRiskAssessment:
        return DestructiveRiskAssessment(
            status=status,
            managed_count=managed_count,
            destructive_count=destructive_count,
            ratio=ratio,
            blocked=blocked,
            allowed=allowed,
            reason=reason,
            config_version=threshold.schema_version,
            direct_destructive_count=direct_destructive_count,
            cascade_count=cascade_count,
            impact_breakdown=breakdown,
            calculation=calculation,
            override_requested=requested_override,
            override_applied=override_applied,
            audit_reference=audit_reference,
            evidence=evidence,
        )

    if unknown_cascade:
        return result(
            status=DestructiveRiskStatus.UNKNOWN_CASCADE,
            blocked=True,
            allowed=False,
            reason="cascade impact is unknown; reconcile dependents before mutation",
        )
    if destructive_count == 0:
        return result(
            status=DestructiveRiskStatus.PASS,
            blocked=False,
            allowed=True,
            reason="no DELETE or REPLACE operation is planned",
        )
    if managed_count == 0:
        return result(
            status=DestructiveRiskStatus.NO_MANAGED_BASELINE,
            blocked=True,
            allowed=False,
            reason="destructive changes require a non-empty managed baseline",
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
        if (override or explicit_override) and not audit_reference:
            return result(
                status=DestructiveRiskStatus.HIGH_RISK_PLAN,
                blocked=True,
                allowed=False,
                reason="explicit threshold override requires an audit reference",
            )
        allowed = (
            pre_operation_checkpoint
            and reviewed_plan
            and (release_high_risk or override or explicit_override)
        )
        reason = (
            "HIGH_RISK_PLAN requires a pre-operation checkpoint, concrete reviewed plan and explicit audit"
            if not allowed
            else "HIGH_RISK_PLAN explicitly released by reviewed plan, checkpoint and audit"
        )
        return result(
            status=DestructiveRiskStatus.HIGH_RISK_PLAN,
            blocked=not allowed,
            allowed=allowed,
            reason=reason,
            override_applied=allowed,
        )
    if not pre_operation_checkpoint:
        return result(
            status=DestructiveRiskStatus.CHECKPOINT_REQUIRED,
            blocked=True,
            allowed=False,
            reason="a pre-operation checkpoint is required before destructive mutation",
        )
    return result(
        status=DestructiveRiskStatus.PASS,
        blocked=False,
        allowed=True,
        reason="destructive delta is within the managed-element threshold",
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
        raise DestructiveThresholdError(assessment.reason, assessment=assessment)
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
    state = current if isinstance(current, CurrentState) else CurrentState.model_validate(current)
    seen: dict[tuple[str, str], str] = {}
    for element in state.elements:
        identity = (element.document_id, element.unique_id)
        previous = seen.get(identity)
        if previous is not None:
            raise DuplicateCurrentIdentity(
                "duplicate current persistent identity: "
                f"document_id={element.document_id!r}, unique_id={element.unique_id!r} "
                f"claimed by {previous!r} and {element.logical_id!r}"
            )
        seen[identity] = element.logical_id or f"<unmanaged:{element.unique_id}>"
    return state


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
            if observed is not None and observed.diverged:
                raise UserDivergence(
                    f"user divergence detected for managed logical_id {logical_id}"
                )
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
    "DiffError",
    "DiffOperation",
    "DiffReason",
    "DiffResult",
    "DocumentIdentityMismatch",
    "DuplicateCurrentIdentity",
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
