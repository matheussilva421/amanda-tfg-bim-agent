"""Guarded restore of a verified checkpoint under a new filename.

A rollback never overwrites the checkpoint it reads, never writes outside the
declared writable roots, and never runs while a writer lease is held. The
restored file gets a new name so the previous state stays auditable.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from ..bootstrap.snapshots import sha256_of


class RollbackRefused(Exception):
    """The requested restore violates a safety precondition."""


def _resolved_contained(path: Path, roots: list) -> bool:
    """True when the resolved path stays inside one of the allowed roots."""
    try:
        resolved = Path(path).resolve(strict=False)
    except OSError:
        return False
    for root in roots:
        root_resolved = Path(root).resolve(strict=False)
        if resolved == root_resolved:
            return True
        if root_resolved in resolved.parents:
            return True
    return False


def restore_checkpoint(
    *,
    checkpoint: Path,
    destination: Path,
    expected_sha256: str,
    writable_roots: list,
    lease_path: Path | None = None,
) -> Path:
    from ..state.locks import WriterLock

    checkpoint = Path(checkpoint)
    destination = Path(destination)

    if not checkpoint.is_file():
        raise RollbackRefused("checkpoint not found: " + str(checkpoint))

    if checkpoint.resolve() == destination.resolve():
        raise RollbackRefused(
            "rollback must write to a new filename, never over its own source"
        )

    actual = sha256_of(checkpoint)
    if actual.lower() != str(expected_sha256).lower():
        raise RollbackRefused(
            "hash mismatch: recorded "
            + str(expected_sha256)
            + " but the checkpoint hashes to "
            + actual
        )

    if not _resolved_contained(destination, writable_roots):
        raise RollbackRefused(
            "destination is outside the writable roots: " + str(destination)
        )

    if destination.exists():
        raise RollbackRefused("destination already exists: " + str(destination))

    if lease_path is not None:
        lease = WriterLock(Path(lease_path), owner="rollback-probe")
        if lease.exists() and lease.is_held_by_live_owner():
            raise RollbackRefused(
                "a writer lease is held at "
                + str(lease_path)
                + "; Revit must be quiescent before a restore"
            )

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(checkpoint, destination)
    return destination
