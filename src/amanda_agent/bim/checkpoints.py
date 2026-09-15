"""Immutable file checkpoints and hash manifests for BIM stages."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CheckpointError(RuntimeError):
    """A checkpoint cannot be created or safely restored."""


class CheckpointStage(StrEnum):
    """Small convenience enum for callers that do not import BIM models."""

    R00 = "EMPTY_SANDBOX"
    R01 = "PROJECT_INITIALIZED"
    R02 = "SITE"
    R03 = "LEVELS_AND_REFERENCES"
    R04 = "MASSING"
    R05 = "ARCHITECTURAL_SHELL"
    R06 = "INTERNAL_LAYOUT"
    R07 = "OPENINGS"
    R08 = "ROOMS"
    R09 = "ACCESSIBILITY"
    R10 = "FURNITURE"
    R11 = "LANDSCAPE"
    R12 = "MATERIALS"
    R13 = "DOCUMENTATION"
    R14 = "QA"
    R15 = "RELEASE_CANDIDATE"
    R16 = "GOLDEN"


_PROTECTED_COMPONENTS = frozenset(
    {"golden", "master", "source"}
)


def sha256_file(path: Path) -> str:
    """Hash a file in bounded chunks."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stage_value(stage: Any) -> str:
    value = getattr(stage, "value", stage)
    return str(value)


def _manifest_default_path(checkpoint_path: Path) -> Path:
    return checkpoint_path.with_suffix(checkpoint_path.suffix + ".manifest.json")


def _reject_protected_checkpoint_target(path: Path) -> None:
    lowered = path.name.casefold()
    if any(token in lowered for token in _PROTECTED_COMPONENTS):
        raise CheckpointError(f"protected checkpoint target is forbidden: {path}")


class CheckpointManifest(BaseModel):
    """Published evidence for one stable, immutable stage copy."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    stage: str = Field(min_length=1)
    source_path: Path
    checkpoint_path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    created_utc: datetime
    manifest_path: Path

    def verify(self) -> bool:
        """Verify the checkpoint bytes against this manifest."""

        path = self.checkpoint_path
        return path.is_file() and sha256_file(path) == self.sha256

    @classmethod
    def load(cls, path: Path) -> CheckpointManifest:
        manifest_path = Path(path)
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["manifest_path"] = manifest_path
        return cls.model_validate(payload)


class CheckpointManager:
    """Create, verify and restore immutable stage copies."""

    def __init__(self, *, clock: Any | None = None):
        self._clock = clock or (lambda: datetime.now(UTC))

    def create_checkpoint(
        self,
        source_path: Path,
        checkpoint_path: Path,
        *,
        stage: Any,
        manifest_path: Path | None = None,
        save_in_progress: bool = False,
        active_save: bool = False,
        save_state: str = "STABLE",
        source_stable: bool = True,
        reopen_verify: bool = False,
    ) -> CheckpointManifest:
        """Copy stable bytes and publish a manifest only after verification.

        ``reopen_verify`` records the caller's requested boundary but cannot
        emulate Revit reopen; the file-level manager verifies stable bytes.
        A Revit adapter must provide separate save/close/reopen evidence.
        """

        source = Path(source_path)
        target = Path(checkpoint_path)
        manifest = Path(manifest_path) if manifest_path is not None else _manifest_default_path(target)
        if save_in_progress or active_save or save_state.casefold() not in {"stable", "closed", "saved"}:
            raise CheckpointError("cannot checkpoint while a save is active or incomplete")
        if not source_stable:
            raise CheckpointError("source save is not proven stable")
        if not source.is_file():
            raise FileNotFoundError(f"checkpoint source not found: {source}")
        _reject_protected_checkpoint_target(target)
        if target.exists():
            raise CheckpointError(f"checkpoint target already exists: {target}")
        if manifest.exists():
            raise CheckpointError(f"checkpoint manifest already exists: {manifest}")

        target.parent.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        target_fd, temporary_target_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
        )
        manifest_fd, temporary_manifest_name = tempfile.mkstemp(
            prefix=f".{manifest.name}.", suffix=".tmp", dir=manifest.parent
        )
        os.close(target_fd)
        os.close(manifest_fd)
        temporary_target = Path(temporary_target_name)
        temporary_manifest = Path(temporary_manifest_name)
        published_target = False
        try:
            before_hash = sha256_file(source)
            shutil.copy2(source, temporary_target)
            after_hash = sha256_file(source)
            checkpoint_hash = sha256_file(temporary_target)
            if before_hash != after_hash or before_hash != checkpoint_hash:
                raise CheckpointError("source changed while creating checkpoint")
            os.rename(temporary_target, target)
            published_target = True
            if reopen_verify and sha256_file(target) != checkpoint_hash:
                raise CheckpointError("checkpoint bytes failed post-copy verification")

            record = CheckpointManifest(
                stage=_stage_value(stage),
                source_path=source.resolve(strict=False),
                checkpoint_path=target.resolve(strict=False),
                sha256=checkpoint_hash,
                size_bytes=target.stat().st_size,
                created_utc=self._clock(),
                manifest_path=manifest.resolve(strict=False),
            )
            temporary_manifest.write_text(
                json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            os.rename(temporary_manifest, manifest)
            return record
        except (OSError, ValueError) as exc:
            raise CheckpointError(f"checkpoint publication failed: {exc}") from exc
        finally:
            temporary_target.unlink(missing_ok=True)
            temporary_manifest.unlink(missing_ok=True)
            if published_target and not manifest.exists():
                target.unlink(missing_ok=True)

    def verify_checkpoint(self, manifest: CheckpointManifest | Path) -> bool:
        """Verify a manifest before it can be used for rollback."""

        record = CheckpointManifest.load(manifest) if isinstance(manifest, Path) else manifest
        if not record.verify():
            raise CheckpointError(f"checkpoint hash verification failed: {record.checkpoint_path}")
        return True

    def rollback(
        self,
        manifest: CheckpointManifest | Path,
        restore_target: Path,
        *,
        allow_overwrite: bool = True,
    ) -> Path:
        """Restore only after verifying the immutable checkpoint hash."""

        record = CheckpointManifest.load(manifest) if isinstance(manifest, Path) else manifest
        self.verify_checkpoint(record)
        target = Path(restore_target)
        _reject_protected_checkpoint_target(target)
        if target.exists() and not allow_overwrite:
            raise CheckpointError(f"rollback target already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary_fd, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".rollback", dir=target.parent
        )
        os.close(temporary_fd)
        temporary = Path(temporary_name)
        try:
            shutil.copy2(record.checkpoint_path, temporary)
            if sha256_file(temporary) != record.sha256:
                raise CheckpointError("rollback copy failed hash verification")
            os.replace(temporary, target)
            return target
        except OSError as exc:
            raise CheckpointError(f"rollback failed: {exc}") from exc
        finally:
            temporary.unlink(missing_ok=True)


def create_checkpoint(
    source_path: Path,
    checkpoint_path: Path,
    *,
    stage: Any,
    **kwargs: Any,
) -> CheckpointManifest:
    """Functional wrapper around :class:`CheckpointManager`."""

    return CheckpointManager().create_checkpoint(
        source_path, checkpoint_path, stage=stage, **kwargs
    )


def verify_checkpoint(manifest: CheckpointManifest | Path) -> bool:
    """Functional wrapper for pre-rollback verification."""

    return CheckpointManager().verify_checkpoint(manifest)


__all__ = [
    "CheckpointError",
    "CheckpointManager",
    "CheckpointManifest",
    "CheckpointStage",
    "create_checkpoint",
    "sha256_file",
    "verify_checkpoint",
]
