"""Fail-closed checks for BIM mutation targets.

The filename check is deliberately only a secondary guard.  Authorization is
based on canonical roots, protected identities, the active document and the
writer lease supplied by the caller.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

_FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def _is_reparse_point(path: Path) -> bool:
    """Return True for symlinks, junctions and other reparse points.

    ``pathlib.is_symlink`` misses junctions on Windows, so use the Win32
    attribute directly while keeping the POSIX fallback.
    """

    try:
        if path.is_symlink():
            return True
        if not path.exists():
            return False
    except OSError:
        return False
    if os.name == "nt":
        try:
            import ctypes

            attributes = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            return int(attributes) != 0xFFFFFFFF and bool(
                attributes & _FILE_ATTRIBUTE_REPARSE_POINT
            )
        except (AttributeError, OSError):
            return False
    return False


class SafetyError(RuntimeError):
    """A target cannot be proven safe for a BIM write."""

    def __init__(
        self,
        message: str,
        *,
        reason_code: SafetyReason | None = None,
        assessment: OperationRiskAssessment | None = None,
    ) -> None:
        self.reason_code = reason_code or SafetyReason.UNSAFE_TARGET
        self.reason = self.reason_code
        self.assessment = assessment
        super().__init__(message)


TargetRejected = SafetyError


class SafetyReason(StrEnum):
    """Machine-readable reason for every Sentinel refusal."""

    UNSAFE_TARGET = "UNSAFE_TARGET"
    TARGET_OUTSIDE_WRITABLE_ROOT = "TARGET_OUTSIDE_WRITABLE_ROOT"
    PROTECTED_TARGET = "PROTECTED_TARGET"
    AMBIGUOUS_TARGET_IDENTITY = "AMBIGUOUS_TARGET_IDENTITY"
    TARGET_NOT_REGULAR_FILE = "TARGET_NOT_REGULAR_FILE"
    ACTIVE_DOCUMENT_MISMATCH = "ACTIVE_DOCUMENT_MISMATCH"
    ACTIVE_DOCUMENT_UNLABELLED = "ACTIVE_DOCUMENT_UNLABELLED"
    WRITER_LEASE_REQUIRED = "WRITER_LEASE_REQUIRED"
    WRITER_LEASE_INVALID = "WRITER_LEASE_INVALID"
    WRITER_LEASE_DOCUMENT_MISMATCH = "WRITER_LEASE_DOCUMENT_MISMATCH"
    EXPLICIT_CONFIRMATION_REQUIRED = "EXPLICIT_CONFIRMATION_REQUIRED"
    UNKNOWN_OPERATION = "UNKNOWN_OPERATION"
    UNKNOWN_CASCADE = "UNKNOWN_CASCADE"
    INVALID_RISK_INPUT = "INVALID_RISK_INPUT"


class RiskLevel(StrEnum):
    """Risk severity used by the operation Sentinel."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class OperationRiskAssessment:
    """Deterministic risk classification before a BIM operation is invoked."""

    operation: str
    risk: RiskLevel
    destructive: bool
    affected_count: int
    cascade_count: int
    impact_count: int
    managed_count: int | None
    ratio: float | None
    cascade_unknown: bool
    reason: str

_PROTECTED_TOKENS = frozenset(
    {"golden", "master", "source", "baseline", "checkpoint", "checkpoints", "release", "releases"}
)


@dataclass(frozen=True)
class DocumentIdentity:
    """The identity Revit reported for the active document."""

    document_id: str
    path: Path


@dataclass(frozen=True)
class ProtectedIdentity:
    """A path plus an optional file identity retained by a manifest."""

    path: Path
    file_id: tuple[int, int] | None = None


def _as_roots(
    writable_roots: Iterable[Path] | Path | None,
    *,
    root: Path | None,
    writable_root: Path | None,
) -> list[Path]:
    if writable_roots is None:
        values: list[Path] = []
    elif isinstance(writable_roots, (str, Path)):
        values = [Path(writable_roots)]
    else:
        values = [Path(value) for value in writable_roots]
    if root is not None:
        values.append(Path(root))
    if writable_root is not None:
        values.append(Path(writable_root))
    if not values:
        values = [Path.cwd() / "revit" / "production" / "working"]
    return [value.resolve(strict=False) for value in values]


def _identity(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return (int(stat.st_dev), int(stat.st_ino))


def _under(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _document_value(document: Any, key: str) -> Any:
    if document is None:
        return None
    if isinstance(document, Mapping):
        return document.get(key)
    return getattr(document, key, None)


def _lease_info(lease: Any) -> Mapping[str, Any] | None:
    if lease is None:
        return None
    if isinstance(lease, Mapping):
        return lease
    inspect = getattr(lease, "inspect", None)
    if callable(inspect):
        info = inspect()
        return info if isinstance(info, Mapping) else None
    return None


def _reject_path_components(
    candidate: Path, *, ignored_exact_tokens: frozenset[str] = frozenset()
) -> None:
    for component in candidate.parts:
        lowered = component.casefold()
        if any(
            token in lowered
            and not (token in ignored_exact_tokens and lowered == token)
            for token in _PROTECTED_TOKENS
        ):
            raise SafetyError(
                f"protected filename/path component {component!r} cannot be a writable target",
                reason_code=SafetyReason.PROTECTED_TARGET,
            )


def _reject_protected_root_components(
    root: Path, *, ignored_exact_tokens: frozenset[str] = frozenset()
) -> None:
    """Reject reserved root names without matching incidental test/path text."""

    for component in root.parts:
        lowered = component.casefold()
        if lowered in _PROTECTED_TOKENS and lowered not in ignored_exact_tokens:
            raise SafetyError(
                f"protected writable root component {component!r} is not allowed",
                reason_code=SafetyReason.PROTECTED_TARGET,
            )


def _reject_symlink_components(candidate: Path, roots: list[Path]) -> None:
    """Reject links in the target path, while permitting the configured root."""

    root_set = set(roots)
    cursor = candidate
    while True:
        try:
            linked = _is_reparse_point(cursor)
        except OSError as exc:
            raise SafetyError(
                f"cannot inspect target path component {cursor}",
                reason_code=SafetyReason.AMBIGUOUS_TARGET_IDENTITY,
            ) from exc
        if linked and cursor not in root_set:
            raise SafetyError(
                f"symlink/junction target identity is ambiguous: {cursor}",
                reason_code=SafetyReason.AMBIGUOUS_TARGET_IDENTITY,
            )
        if cursor.parent == cursor:
            break
        cursor = cursor.parent


def _reject_protected_identity(
    candidate: Path,
    *,
    protected_paths: Iterable[Path],
    protected_identities: Iterable[ProtectedIdentity | Mapping[str, Any]],
) -> None:
    candidate_identity = _identity(candidate)
    for raw_path in protected_paths:
        protected = Path(raw_path).resolve(strict=False)
        if candidate == protected or _under(candidate, protected):
            raise SafetyError(
                f"protected source/baseline/checkpoint/release identity: {candidate}",
                reason_code=SafetyReason.PROTECTED_TARGET,
            )

    for raw_identity in protected_identities:
        if isinstance(raw_identity, ProtectedIdentity):
            protected_path = raw_identity.path
            file_id = raw_identity.file_id
        else:
            try:
                protected_path = Path(raw_identity["path"])
                file_id = raw_identity.get("file_id")
            except (KeyError, TypeError) as exc:
                raise SafetyError(
                    "protected manifest identity is not readable",
                    reason_code=SafetyReason.AMBIGUOUS_TARGET_IDENTITY,
                ) from exc
        canonical = protected_path.resolve(strict=False)
        if candidate == canonical or _under(candidate, canonical):
            raise SafetyError(
                f"protected manifest identity: {candidate}",
                reason_code=SafetyReason.PROTECTED_TARGET,
            )
        if file_id is not None and candidate_identity == tuple(file_id):
            raise SafetyError(
                f"protected file identity: {candidate}",
                reason_code=SafetyReason.PROTECTED_TARGET,
            )


_KNOWN_READ_OPERATIONS = frozenset({"READ", "QUERY", "INSPECT", "NOOP", "VERIFY"})
_KNOWN_MUTATIONS = frozenset({"CREATE", "UPDATE", "UPSERT", "WRITE"})
_KNOWN_DESTRUCTIVE = frozenset(
    {"DELETE", "REMOVE", "PURGE", "REPLACE", "OVERWRITE", "RESET", "ROLLBACK"}
)


def _operation_name(operation: Any) -> str:
    value = getattr(operation, "value", operation)
    if not isinstance(value, str) or not value.strip():
        raise SafetyError(
            "operation must be a non-empty name",
            reason_code=SafetyReason.INVALID_RISK_INPUT,
        )
    return value.strip().upper().rsplit(".", 1)[-1]


def _risk_count(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SafetyError(
            f"{label} must be a non-negative integer",
            reason_code=SafetyReason.INVALID_RISK_INPUT,
        )
    return value


def classify_operation_risk(
    operation: Any,
    *,
    affected_count: int = 0,
    managed_count: int | None = None,
    cascade_count: int = 0,
    cascade_unknown: bool = False,
) -> OperationRiskAssessment:
    """Classify operation risk from its action and known damage scale."""

    name = _operation_name(operation)
    affected = _risk_count(affected_count, "affected_count")
    cascades = _risk_count(cascade_count, "cascade_count")
    if managed_count is not None:
        managed = _risk_count(managed_count, "managed_count")
    else:
        managed = None
    if not isinstance(cascade_unknown, bool):
        raise SafetyError(
            "cascade_unknown must be boolean",
            reason_code=SafetyReason.INVALID_RISK_INPUT,
        )

    known = name in _KNOWN_READ_OPERATIONS | _KNOWN_MUTATIONS | _KNOWN_DESTRUCTIVE
    destructive = name in _KNOWN_DESTRUCTIVE
    if not known:
        return OperationRiskAssessment(
            operation=name,
            risk=RiskLevel.CRITICAL,
            destructive=True,
            affected_count=affected,
            cascade_count=cascades,
            impact_count=affected + cascades,
            managed_count=managed,
            ratio=None if managed is None else float("inf") if managed == 0 else (affected + cascades) / managed,
            cascade_unknown=cascade_unknown,
            reason="operation is not in the Sentinel allowlist",
        )

    impact = affected + cascades
    ratio = None if managed is None else float("inf") if managed == 0 and impact else (impact / managed if managed else 0.0)
    if not destructive:
        risk = RiskLevel.LOW if name in _KNOWN_READ_OPERATIONS else RiskLevel.MEDIUM
        reason = "operation does not delete or replace managed content"
    elif cascade_unknown:
        risk = RiskLevel.CRITICAL
        reason = "destructive cascade cannot be bounded before mutation"
    elif impact > 10 or (ratio is not None and ratio > 0.10):
        risk = RiskLevel.CRITICAL
        reason = "destructive impact exceeds the Sentinel scale guard"
    else:
        risk = RiskLevel.HIGH
        reason = "destructive operation requires explicit confirmation"
    return OperationRiskAssessment(
        operation=name,
        risk=risk,
        destructive=destructive,
        affected_count=affected,
        cascade_count=cascades,
        impact_count=impact,
        managed_count=managed,
        ratio=ratio,
        cascade_unknown=cascade_unknown,
        reason=reason,
    )


def assert_operation_safe(
    operation: Any,
    *,
    affected_count: int = 0,
    managed_count: int | None = None,
    cascade_count: int = 0,
    cascade_unknown: bool = False,
    confirmation: str | bool | None = None,
    confirmed: bool = False,
) -> OperationRiskAssessment:
    """Allow an operation only after fail-closed Sentinel checks."""

    assessment = classify_operation_risk(
        operation,
        affected_count=affected_count,
        managed_count=managed_count,
        cascade_count=cascade_count,
        cascade_unknown=cascade_unknown,
    )
    if assessment.operation not in _KNOWN_READ_OPERATIONS | _KNOWN_MUTATIONS | _KNOWN_DESTRUCTIVE:
        raise SafetyError(
            f"unknown operation {assessment.operation!r} is refused by default",
            reason_code=SafetyReason.UNKNOWN_OPERATION,
            assessment=assessment,
        )
    if assessment.cascade_unknown:
        raise SafetyError(
            "destructive cascade is unknown; operation is refused",
            reason_code=SafetyReason.UNKNOWN_CASCADE,
            assessment=assessment,
        )
    has_confirmation = confirmed is True or (
        isinstance(confirmation, str) and bool(confirmation.strip())
    ) or confirmation is True
    if assessment.destructive and not has_confirmation:
        raise SafetyError(
            "explicit confirmation is required for a destructive operation",
            reason_code=SafetyReason.EXPLICIT_CONFIRMATION_REQUIRED,
            assessment=assessment,
        )
    return assessment


def assert_writable_target(
    target: Path,
    *,
    writable_roots: Iterable[Path] | Path | None = None,
    root: Path | None = None,
    writable_root: Path | None = None,
    protected_paths: Iterable[Path] = (),
    protected_identities: Iterable[ProtectedIdentity | Mapping[str, Any]] = (),
    active_document: DocumentIdentity | Mapping[str, Any] | Any | None = None,
    active_document_id: str | None = None,
    active_document_path: Path | None = None,
    target_document_id: str | None = None,
    lease: Any | None = None,
    lease_token: str | None = None,
    require_lease: bool = False,
    operation: Any | None = None,
    affected_count: int = 0,
    managed_count: int | None = None,
    cascade_count: int = 0,
    cascade_unknown: bool = False,
    confirmation: str | bool | None = None,
    confirmed: bool = False,
    allow_checkpoint_directory: bool = False,
) -> Path:
    """Return a canonical target only when every supplied safety invariant passes.

    A non-existent target is valid only inside a canonical allowlisted root. An
    existing file is rejected when its identity is ambiguous (for example, a
    hardlink) or when it matches a protected manifest identity.
    """

    candidate_input = Path(target)
    raw_absolute = (
        candidate_input
        if candidate_input.is_absolute()
        else Path.cwd() / candidate_input
    )
    candidate = candidate_input.resolve(strict=False)
    roots = _as_roots(writable_roots, root=root, writable_root=writable_root)
    ignored_exact_tokens = (
        frozenset({"checkpoint", "checkpoints"})
        if allow_checkpoint_directory
        else frozenset()
    )

    if not any(_under(candidate, allowed) for allowed in roots):
        raise SafetyError(
            f"target is outside the canonical writable root allowlist: {candidate}",
            reason_code=SafetyReason.TARGET_OUTSIDE_WRITABLE_ROOT,
        )
    for allowed in roots:
        _reject_protected_root_components(
            allowed, ignored_exact_tokens=ignored_exact_tokens
        )
    relative_targets = [candidate.relative_to(allowed) for allowed in roots if _under(candidate, allowed)]
    for relative_target in relative_targets:
        _reject_path_components(
            relative_target, ignored_exact_tokens=ignored_exact_tokens
        )
    _reject_symlink_components(raw_absolute, roots)
    _reject_symlink_components(candidate, roots)

    if candidate.exists() and candidate.is_file():
        try:
            if candidate.stat().st_nlink > 1:
                raise SafetyError(
                    f"hardlink target identity is ambiguous: {candidate}",
                    reason_code=SafetyReason.AMBIGUOUS_TARGET_IDENTITY,
                )
        except OSError as exc:
            raise SafetyError(
                f"cannot inspect target identity: {candidate}",
                reason_code=SafetyReason.AMBIGUOUS_TARGET_IDENTITY,
            ) from exc
    elif candidate.exists():
        raise SafetyError(
            f"writable target is not a regular file: {candidate}",
            reason_code=SafetyReason.TARGET_NOT_REGULAR_FILE,
        )
    _reject_protected_identity(
        candidate,
        protected_paths=protected_paths,
        protected_identities=protected_identities,
    )

    reported_id = _document_value(active_document, "document_id")
    reported_path = _document_value(active_document, "path")
    expected_active_id = active_document_id or reported_id
    expected_active_path = active_document_path or reported_path
    if expected_active_path is not None:
        active_path = Path(expected_active_path).resolve(strict=False)
        if active_path != candidate:
            raise SafetyError(
                f"active document path does not match target: {active_path} != {candidate}",
                reason_code=SafetyReason.ACTIVE_DOCUMENT_MISMATCH,
            )
    if expected_active_id is not None:
        if target_document_id is None:
            raise SafetyError(
                "active document identity cannot be matched to an unlabelled target",
                reason_code=SafetyReason.ACTIVE_DOCUMENT_UNLABELLED,
            )
        if expected_active_id != target_document_id:
            raise SafetyError(
                f"active document identity does not match target: {expected_active_id} != {target_document_id}",
                reason_code=SafetyReason.ACTIVE_DOCUMENT_MISMATCH,
            )

    if require_lease and lease is None:
        raise SafetyError(
            "a shared writer lease is required before a BIM write",
            reason_code=SafetyReason.WRITER_LEASE_REQUIRED,
        )
    if lease is not None:
        info = _lease_info(lease)
        if not info or not info.get("owner_token"):
            raise SafetyError(
                "writer lease is missing or unreadable",
                reason_code=SafetyReason.WRITER_LEASE_INVALID,
            )
        if lease_token is not None and info.get("owner_token") != lease_token:
            raise SafetyError(
                "writer lease token is stale or belongs to another owner",
                reason_code=SafetyReason.WRITER_LEASE_INVALID,
            )
        lease_document_id = info.get("document_identity", info.get("document_id"))
        expected_document_id = target_document_id or expected_active_id
        if expected_document_id is not None:
            if lease_document_id is None:
                raise SafetyError(
                    "writer lease has no document identity to match the target",
                    reason_code=SafetyReason.WRITER_LEASE_DOCUMENT_MISMATCH,
                )
            if str(lease_document_id) != str(expected_document_id):
                raise SafetyError(
                    "writer lease document identity does not match the active target document",
                    reason_code=SafetyReason.WRITER_LEASE_DOCUMENT_MISMATCH,
                )

    if operation is not None:
        assert_operation_safe(
            operation,
            affected_count=affected_count,
            managed_count=managed_count,
            cascade_count=cascade_count,
            cascade_unknown=cascade_unknown,
            confirmation=confirmation,
            confirmed=confirmed,
        )

    return candidate


__all__ = [
    "DocumentIdentity",
    "OperationRiskAssessment",
    "ProtectedIdentity",
    "RiskLevel",
    "SafetyError",
    "SafetyReason",
    "TargetRejected",
    "assert_operation_safe",
    "assert_writable_target",
    "classify_operation_risk",
]
