"""Immutable file checkpoints and hash manifests for BIM stages."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .safety import SafetyError, assert_writable_target


class CheckpointError(RuntimeError):
    """A checkpoint cannot be created or safely restored."""

    def __init__(
        self,
        message: str,
        *,
        reason_code: CheckpointReason | None = None,
        manifest: CheckpointManifest | None = None,
    ) -> None:
        self.reason_code = reason_code or CheckpointReason.INVALID_CHECKPOINT
        self.reason = self.reason_code
        self.manifest = manifest
        super().__init__(message)


class CheckpointReason(StrEnum):
    """Machine-readable reason for a refused checkpoint operation."""

    INVALID_CHECKPOINT = "INVALID_CHECKPOINT"
    ACTIVE_SAVE = "ACTIVE_SAVE"
    UNSTABLE_SOURCE = "UNSTABLE_SOURCE"
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    PROTECTED_TARGET = "PROTECTED_TARGET"
    TARGET_EXISTS = "TARGET_EXISTS"
    MANIFEST_EXISTS = "MANIFEST_EXISTS"
    SOURCE_CHANGED = "SOURCE_CHANGED"
    PUBLICATION_FAILED = "PUBLICATION_FAILED"
    HASH_MISMATCH = "HASH_MISMATCH"
    DOCUMENT_IDENTITY_REQUIRED = "DOCUMENT_IDENTITY_REQUIRED"
    DOCUMENT_IDENTITY_MISMATCH = "DOCUMENT_IDENTITY_MISMATCH"
    RESTORE_TARGET_EXISTS = "RESTORE_TARGET_EXISTS"
    RESTORE_FAILED = "RESTORE_FAILED"


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
    {
        "golden",
        "master",
        "source",
        "baseline",
        "checkpoint",
        "checkpoints",
        "release",
        "releases",
    }
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
    for component in path.parts:
        lowered = component.casefold()
        # ``checkpoints`` is the conventional publication directory. Existing
        # checkpoint files are still protected by the no-overwrite gate.
        protected_filename = any(
            token in lowered
            for token in _PROTECTED_COMPONENTS - {"checkpoint", "checkpoints"}
        )
        if protected_filename:
            raise CheckpointError(
                f"protected checkpoint target is forbidden: {path}",
                reason_code=CheckpointReason.PROTECTED_TARGET,
            )


def _path_identity(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return int(stat.st_dev), int(stat.st_ino)


def _fsync_file(path: Path) -> None:
    with path.open("r+b") as stream:
        os.fsync(stream.fileno())


def _document_value(document: Any, key: str) -> Any:
    if document is None:
        return None
    if isinstance(document, Mapping):
        return document.get(key)
    return getattr(document, key, None)


class CheckpointManifest(BaseModel):
    """Published evidence for one stable, immutable stage copy."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    version: int = Field(default=1, ge=1)
    stage: str = Field(min_length=1)
    source_path: Path
    checkpoint_path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    created_utc: datetime
    manifest_path: Path
    document_id: str | None = Field(default=None, min_length=1)
    source_document_id: str | None = Field(default=None, min_length=1)
    source_document_path: Path | None = None
    source_file_id: tuple[int, int] | None = None
    checkpoint_file_id: tuple[int, int] | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def align_document_identity_aliases(cls, values: Any) -> Any:
        if not isinstance(values, Mapping):
            return values
        normalized = dict(values)
        document_id = normalized.get("document_id")
        source_document_id = normalized.get("source_document_id")
        if document_id is None and source_document_id is not None:
            normalized["document_id"] = source_document_id
        if source_document_id is None and document_id is not None:
            normalized["source_document_id"] = document_id
        return normalized

    @model_validator(mode="after")
    def validate_document_identity_aliases(self) -> CheckpointManifest:
        if (
            self.document_id is not None
            and self.source_document_id is not None
            and self.document_id != self.source_document_id
        ):
            raise ValueError("document_id and source_document_id must match")
        return self

    def verify(self) -> bool:
        """Verify the checkpoint bytes against this manifest."""

        path = self.checkpoint_path
        try:
            return (
                path.is_file()
                and path.stat().st_size == self.size_bytes
                and sha256_file(path) == self.sha256
            )
        except OSError:
            return False

    def matches_document(
        self,
        *,
        current_document_id: str | None = None,
        current_document_path: Path | None = None,
    ) -> bool:
        """Return whether the checkpoint is bound to the current document."""

        if self.document_id is not None:
            if current_document_id != self.document_id:
                return False
        elif self.source_document_path is not None and current_document_path is None:
            return False
        return not (
            self.source_document_path is not None
            and current_document_path is not None
            and Path(current_document_path).resolve(strict=False)
            != self.source_document_path.resolve(strict=False)
        )

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
        document_id: str | None = None,
        source_document_id: str | None = None,
        document_path: Path | None = None,
        active_document: Any | None = None,
        provenance: Mapping[str, Any] | None = None,
        writable_roots: list[Path] | tuple[Path, ...] | None = None,
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
            raise CheckpointError(
                "cannot checkpoint while a save is active or incomplete",
                reason_code=CheckpointReason.ACTIVE_SAVE,
            )
        if not source_stable:
            raise CheckpointError(
                "source save is not proven stable",
                reason_code=CheckpointReason.UNSTABLE_SOURCE,
            )
        if not source.is_file():
            raise CheckpointError(
                f"checkpoint source not found: {source}",
                reason_code=CheckpointReason.SOURCE_NOT_FOUND,
            )
        _reject_protected_checkpoint_target(target)
        _reject_protected_checkpoint_target(manifest)
        if target.exists():
            raise CheckpointError(
                f"checkpoint target already exists: {target}",
                reason_code=CheckpointReason.TARGET_EXISTS,
            )
        if manifest.exists():
            raise CheckpointError(
                f"checkpoint manifest already exists: {manifest}",
                reason_code=CheckpointReason.MANIFEST_EXISTS,
            )

        roots = list(writable_roots or [target.parent])
        try:
            safe_target = assert_writable_target(
                target,
                writable_roots=roots,
                allow_checkpoint_directory=True,
            )
            safe_manifest = assert_writable_target(
                manifest,
                writable_roots=[manifest.parent],
                allow_checkpoint_directory=True,
            )
        except SafetyError as exc:
            raise CheckpointError(
                f"checkpoint target failed safety validation: {exc}",
                reason_code=CheckpointReason.PROTECTED_TARGET
                if exc.reason_code.value == "PROTECTED_TARGET"
                else CheckpointReason.INVALID_CHECKPOINT,
            ) from exc

        safe_target.parent.mkdir(parents=True, exist_ok=True)
        safe_manifest.parent.mkdir(parents=True, exist_ok=True)
        active_id = _document_value(active_document, "document_id")
        active_id = active_id or _document_value(active_document, "document_identity")
        active_path = _document_value(active_document, "path")
        resolved_document_id = document_id or source_document_id or active_id
        resolved_document_path = (
            Path(document_path or active_path).resolve(strict=False)
            if document_path is not None or active_path is not None
            else source.resolve(strict=False) if resolved_document_id is not None else None
        )
        target_fd, temporary_target_name = tempfile.mkstemp(
            prefix=f".{safe_target.name}.", suffix=".tmp", dir=safe_target.parent
        )
        manifest_fd, temporary_manifest_name = tempfile.mkstemp(
            prefix=f".{safe_manifest.name}.", suffix=".tmp", dir=safe_manifest.parent
        )
        os.close(target_fd)
        os.close(manifest_fd)
        temporary_target = Path(temporary_target_name)
        temporary_manifest = Path(temporary_manifest_name)
        published_target = False
        try:
            source_identity_before = _path_identity(source)
            before_hash = sha256_file(source)
            shutil.copy2(source, temporary_target)
            _fsync_file(temporary_target)
            source_identity_after = _path_identity(source)
            after_hash = sha256_file(source)
            checkpoint_hash = sha256_file(temporary_target)
            if (
                before_hash != after_hash
                or before_hash != checkpoint_hash
                or source_identity_before != source_identity_after
            ):
                raise CheckpointError(
                    "source changed while creating checkpoint",
                    reason_code=CheckpointReason.SOURCE_CHANGED,
                )
            os.rename(temporary_target, safe_target)
            published_target = True
            if reopen_verify and sha256_file(safe_target) != checkpoint_hash:
                raise CheckpointError(
                    "checkpoint bytes failed post-copy verification",
                    reason_code=CheckpointReason.HASH_MISMATCH,
                )

            record = CheckpointManifest(
                schema_version=1,
                version=1,
                stage=_stage_value(stage),
                source_path=source.resolve(strict=False),
                checkpoint_path=safe_target.resolve(strict=False),
                sha256=checkpoint_hash,
                source_sha256=before_hash,
                size_bytes=safe_target.stat().st_size,
                created_utc=self._clock(),
                manifest_path=safe_manifest.resolve(strict=False),
                document_id=resolved_document_id,
                source_document_id=resolved_document_id,
                source_document_path=resolved_document_path,
                source_file_id=source_identity_before,
                checkpoint_file_id=_path_identity(safe_target),
                provenance=dict(provenance or {}),
            )
            temporary_manifest.write_text(
                json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with temporary_manifest.open("r+b") as stream:
                os.fsync(stream.fileno())
            os.rename(temporary_manifest, safe_manifest)
            return record
        except CheckpointError:
            raise
        except (OSError, ValueError) as exc:
            raise CheckpointError(
                f"checkpoint publication failed: {exc}",
                reason_code=CheckpointReason.PUBLICATION_FAILED,
            ) from exc
        finally:
            temporary_target.unlink(missing_ok=True)
            temporary_manifest.unlink(missing_ok=True)
            if published_target and not safe_manifest.exists():
                safe_target.unlink(missing_ok=True)

    def verify_checkpoint(self, manifest: CheckpointManifest | Path) -> bool:
        """Verify a manifest before it can be used for rollback."""

        record = CheckpointManifest.load(manifest) if isinstance(manifest, (Path, str)) else manifest
        if not record.verify():
            raise CheckpointError(
                f"checkpoint hash verification failed: {record.checkpoint_path}",
                reason_code=CheckpointReason.HASH_MISMATCH,
                manifest=record,
            )
        return True

    def rollback(
        self,
        manifest: CheckpointManifest | Path,
        restore_target: Path,
        *,
        allow_overwrite: bool = False,
        current_document_id: str | None = None,
        expected_document_id: str | None = None,
        current_document_path: Path | None = None,
        current_document: Any | None = None,
        writable_roots: list[Path] | tuple[Path, ...] | None = None,
    ) -> Path:
        """Restore only after verifying the immutable checkpoint hash."""

        record = CheckpointManifest.load(manifest) if isinstance(manifest, (Path, str)) else manifest
        self.verify_checkpoint(record)
        current_id = current_document_id or expected_document_id
        current_id = current_id or _document_value(current_document, "document_id")
        current_id = current_id or _document_value(current_document, "document_identity")
        current_path = current_document_path or _document_value(current_document, "path")
        if record.document_id is not None and current_id is None:
            raise CheckpointError(
                "current document identity is required to restore this checkpoint",
                reason_code=CheckpointReason.DOCUMENT_IDENTITY_REQUIRED,
                manifest=record,
            )
        if (
            record.document_id is None
            and record.source_document_path is not None
            and current_path is None
        ):
            raise CheckpointError(
                "current document path is required to restore this checkpoint",
                reason_code=CheckpointReason.DOCUMENT_IDENTITY_REQUIRED,
                manifest=record,
            )
        if not record.matches_document(
            current_document_id=current_id,
            current_document_path=current_path,
        ):
            raise CheckpointError(
                "checkpoint does not match the current document identity",
                reason_code=CheckpointReason.DOCUMENT_IDENTITY_MISMATCH,
                manifest=record,
            )
        target = Path(restore_target)
        _reject_protected_checkpoint_target(target)
        if target.exists() and not allow_overwrite:
            raise CheckpointError(
                f"rollback target already exists: {target}",
                reason_code=CheckpointReason.RESTORE_TARGET_EXISTS,
                manifest=record,
            )
        roots = list(writable_roots or [target.parent])
        try:
            safe_target = assert_writable_target(
                target,
                writable_roots=roots,
                allow_checkpoint_directory=True,
            )
        except SafetyError as exc:
            raise CheckpointError(
                f"rollback target failed safety validation: {exc}",
                reason_code=CheckpointReason.PROTECTED_TARGET
                if exc.reason_code.value == "PROTECTED_TARGET"
                else CheckpointReason.INVALID_CHECKPOINT,
                manifest=record,
            ) from exc
        if safe_target.resolve(strict=False) == record.checkpoint_path.resolve(strict=False):
            raise CheckpointError(
                "rollback cannot overwrite its checkpoint source",
                reason_code=CheckpointReason.PROTECTED_TARGET,
                manifest=record,
            )
        safe_target.parent.mkdir(parents=True, exist_ok=True)
        temporary_fd, temporary_name = tempfile.mkstemp(
            prefix=f".{safe_target.name}.", suffix=".rollback", dir=safe_target.parent
        )
        os.close(temporary_fd)
        temporary = Path(temporary_name)
        try:
            shutil.copy2(record.checkpoint_path, temporary)
            _fsync_file(temporary)
            if sha256_file(temporary) != record.sha256 or temporary.stat().st_size != record.size_bytes:
                raise CheckpointError(
                    "rollback copy failed hash verification",
                    reason_code=CheckpointReason.HASH_MISMATCH,
                    manifest=record,
                )
            if allow_overwrite:
                os.replace(temporary, safe_target)
            else:
                os.rename(temporary, safe_target)
            if (
                not safe_target.is_file()
                or safe_target.stat().st_size != record.size_bytes
                or sha256_file(safe_target) != record.sha256
            ):
                raise CheckpointError(
                    "restored file failed post-restore verification",
                    reason_code=CheckpointReason.RESTORE_FAILED,
                    manifest=record,
                )
            return safe_target
        except CheckpointError:
            raise
        except OSError as exc:
            raise CheckpointError(
                f"rollback failed: {exc}",
                reason_code=CheckpointReason.RESTORE_FAILED,
                manifest=record,
            ) from exc
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
    "CheckpointReason",
    "CheckpointStage",
    "create_checkpoint",
    "sha256_file",
    "verify_checkpoint",
]
