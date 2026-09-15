"""Fail-closed checks for BIM mutation targets.

The filename check is deliberately only a secondary guard.  Authorization is
based on canonical roots, protected identities, the active document and the
writer lease supplied by the caller.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_FILE_ATTRIBUTE_REPARSE_POINT = 0x400

def _is_reparse_point(path: Path) -> bool:
    """Return True for symlinks, junctions and other reparse points.

    ``pathlib.is_symlink`` misses junctions on Windows, so use the Win32
    attribute directly while keeping the POSIX fallback.
    """

    try:
        if not path.exists():
            return False
        if path.is_symlink():
            return True
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


TargetRejected = SafetyError

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


def _reject_path_components(candidate: Path) -> None:
    for component in candidate.parts:
        lowered = component.casefold()
        if any(token in lowered for token in _PROTECTED_TOKENS):
            raise SafetyError(
                f"protected filename/path component {component!r} cannot be a writable target"
            )


def _reject_symlink_components(candidate: Path, roots: list[Path]) -> None:
    """Reject links in the target path, while permitting the configured root."""

    root_set = set(roots)
    cursor = candidate
    while True:
        try:
            linked = _is_reparse_point(cursor) if cursor.exists() else False
        except OSError as exc:
            raise SafetyError(f"cannot inspect target path component {cursor}") from exc
        if linked and cursor not in root_set:
            raise SafetyError(f"symlink/junction target identity is ambiguous: {cursor}")
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
            raise SafetyError(f"protected source/baseline/checkpoint/release identity: {candidate}")

    for raw_identity in protected_identities:
        if isinstance(raw_identity, ProtectedIdentity):
            protected_path = raw_identity.path
            file_id = raw_identity.file_id
        else:
            protected_path = Path(raw_identity["path"])
            file_id = raw_identity.get("file_id")
        canonical = protected_path.resolve(strict=False)
        if candidate == canonical or _under(candidate, canonical):
            raise SafetyError(f"protected manifest identity: {candidate}")
        if file_id is not None and candidate_identity == tuple(file_id):
            raise SafetyError(f"protected file identity: {candidate}")


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

    if not any(_under(candidate, allowed) for allowed in roots):
        raise SafetyError(f"target is outside the canonical writable root allowlist: {candidate}")
    relative_targets = [candidate.relative_to(allowed) for allowed in roots if _under(candidate, allowed)]
    for relative_target in relative_targets:
        _reject_path_components(relative_target)
    _reject_symlink_components(raw_absolute, roots)
    _reject_symlink_components(candidate, roots)

    if candidate.exists() and candidate.is_file():
        try:
            if candidate.stat().st_nlink > 1:
                raise SafetyError(f"hardlink target identity is ambiguous: {candidate}")
        except OSError as exc:
            raise SafetyError(f"cannot inspect target identity: {candidate}") from exc
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
                f"active document path does not match target: {active_path} != {candidate}"
            )
    if expected_active_id is not None:
        if target_document_id is None:
            raise SafetyError("active document identity cannot be matched to an unlabelled target")
        if expected_active_id != target_document_id:
            raise SafetyError(
                f"active document identity does not match target: {expected_active_id} != {target_document_id}"
            )

    if require_lease and lease is None:
        raise SafetyError("a shared writer lease is required before a BIM write")
    if lease is not None:
        info = _lease_info(lease)
        if not info or not info.get("owner_token"):
            raise SafetyError("writer lease is missing or unreadable")
        if lease_token is not None and info.get("owner_token") != lease_token:
            raise SafetyError("writer lease token is stale or belongs to another owner")

    return candidate


__all__ = [
    "DocumentIdentity",
    "ProtectedIdentity",
    "SafetyError",
    "TargetRejected",
    "assert_writable_target",
]
