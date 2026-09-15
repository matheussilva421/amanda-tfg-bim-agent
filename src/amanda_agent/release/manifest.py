"""Deterministic, content-bound release manifests.

The manifest is an index of evidence.  It intentionally excludes its own
bytes from the content hash map, otherwise writing the manifest would create a
recursive hash that could never stabilize.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any, overload

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..redaction import redact


class ReleaseProfile(StrEnum):
    STUDY = "STUDY"
    FINAL = "FINAL"


class ArtifactRecord(BaseModel):
    """One release artifact and its expected content identity."""

    model_config = ConfigDict(extra="allow")

    path: str = Field(min_length=1)
    kind: str = "artifact"
    required: bool = False
    mandatory: bool = False
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    size_bytes: int | None = Field(default=None, ge=0)
    validation_status: str | None = None
    signature: str | None = None

    @field_validator("path")
    @classmethod
    def relative_path(cls, value: str) -> str:
        candidate = Path(value)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("artifact path must be relative to the release directory")
        return candidate.as_posix()


class ReleaseCheck(BaseModel):
    """Explicit check result used by profile promotion gates."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    mandatory: bool = False
    waiver: dict[str, Any] | str | bool | None = None
    evidence: list[str] = Field(default_factory=list)


class ManifestVerification(BaseModel):
    """Recomputed manifest integrity result."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checked_artifacts: list[str] = Field(default_factory=list)
    missing_required_hashes: list[str] = Field(default_factory=list)
    missing_required_files: list[str] = Field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid


class ReleaseManifest(BaseModel):
    """All release identity, QA, persistence and export evidence."""

    model_config = ConfigDict(extra="allow")

    schema_version: int = Field(default=1, ge=1)
    project: str = Field(min_length=1)
    release: str = Field(min_length=1)
    timestamp: str = Field(min_length=1)
    revit: dict[str, Any] = Field(default_factory=dict)
    providers: list[dict[str, Any]] = Field(default_factory=list)
    design_engine: dict[str, Any] = Field(default_factory=dict)
    selected_solution: dict[str, Any] = Field(default_factory=dict)
    requirements: dict[str, Any] = Field(default_factory=dict)
    site: dict[str, Any] = Field(default_factory=dict)
    regulation: dict[str, Any] = Field(default_factory=dict)
    qa_summary: dict[str, Any] = Field(default_factory=dict)
    persistence_summary: dict[str, Any] = Field(default_factory=dict)
    exports: list[dict[str, Any]] = Field(default_factory=list)
    release_profile: ReleaseProfile = ReleaseProfile.STUDY
    required_checks: list[ReleaseCheck] = Field(default_factory=list)
    optional_checks: list[ReleaseCheck] = Field(default_factory=list)
    required_artifacts: list[str] = Field(default_factory=list)
    optional_artifacts: list[str] = Field(default_factory=list)
    accepted_limitations: list[str] = Field(default_factory=list)
    approval_evidence: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[ArtifactRecord] = Field(default_factory=list)
    content_hashes: dict[str, str] = Field(default_factory=dict)
    source_export_map: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "revit",
        "design_engine",
        "selected_solution",
        "requirements",
        "site",
        "regulation",
        "qa_summary",
        "persistence_summary",
        "approval_evidence",
        "source_export_map",
        mode="before",
    )
    @classmethod
    def copy_mapping(cls, value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("manifest metadata must be an object")
        return dict(value)

    @field_validator("timestamp", mode="before")
    @classmethod
    def timestamp_text(cls, value: Any) -> str:
        if value is None:
            raise ValueError("manifest timestamp is required")
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    def payload(self) -> dict[str, Any]:
        """Return the redacted JSON-compatible payload for stable writing."""

        return redact(self.model_dump(mode="json"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_and_path(
    first: ReleaseManifest | Mapping[str, Any] | str | Path,
    second: ReleaseManifest | Mapping[str, Any] | str | Path | None,
) -> tuple[ReleaseManifest, Path]:
    if isinstance(first, (str, Path)):
        if second is None:
            raise TypeError("write_manifest requires a manifest object")
        return (
            second
            if isinstance(second, ReleaseManifest)
            else ReleaseManifest.model_validate(second),
            Path(first),
        )
    if second is None or not isinstance(second, (str, Path)):
        raise TypeError("write_manifest requires a manifest path")
    return (
        first if isinstance(first, ReleaseManifest) else ReleaseManifest.model_validate(first),
        Path(second),
    )


@overload
def write_manifest(
    path: str | Path, manifest: ReleaseManifest | Mapping[str, Any]
) -> Path: ...


@overload
def write_manifest(
    manifest: ReleaseManifest | Mapping[str, Any], path: str | Path
) -> Path: ...


def write_manifest(
    first: ReleaseManifest | Mapping[str, Any] | str | Path,
    second: ReleaseManifest | Mapping[str, Any] | str | Path | None = None,
) -> Path:
    """Write a deterministic manifest without hashing the manifest itself."""

    manifest, target = _manifest_and_path(first, second)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            manifest.payload(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return target


def load_manifest(path: str | Path) -> ReleaseManifest:
    source = Path(path)
    return ReleaseManifest.model_validate(
        json.loads(source.read_text(encoding="utf-8"))
    )


def _safe_artifact(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("artifact path escapes release directory: " + relative)
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("artifact path escapes release directory: " + relative) from exc
    return resolved


def verify_manifest(
    source: str | Path | ReleaseManifest,
    *,
    root: str | Path | None = None,
) -> ManifestVerification:
    """Recompute all declared artifact hashes and required-file invariants."""

    errors: list[str] = []
    warnings: list[str] = []
    checked: list[str] = []
    missing_hashes: list[str] = []
    missing_files: list[str] = []

    manifest_path: Path | None = None
    try:
        if isinstance(source, ReleaseManifest):
            manifest = source
            if root is None:
                errors.append("manifest object verification requires a release root")
                return ManifestVerification(
                    valid=False,
                    errors=errors,
                    warnings=warnings,
                    checked_artifacts=checked,
                    missing_required_hashes=missing_hashes,
                    missing_required_files=missing_files,
                )
            release_root = Path(root)
        else:
            manifest_path = Path(source)
            manifest = load_manifest(manifest_path)
            release_root = Path(root) if root is not None else manifest_path.parent
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return ManifestVerification(valid=False, errors=["invalid manifest: " + str(exc)])

    self_names = {"manifest.json", manifest_path.name if manifest_path else ""}
    declared: dict[str, ArtifactRecord] = {}
    for artifact in manifest.artifacts:
        if artifact.path in self_names:
            errors.append("manifest must not hash itself: " + artifact.path)
            continue
        declared[artifact.path] = artifact

    for relative, expected in manifest.content_hashes.items():
        if relative in self_names:
            errors.append("manifest must not hash itself: " + relative)
            continue
        if relative not in declared:
            declared[relative] = ArtifactRecord(path=relative, sha256=expected)

    required_names = set(manifest.required_artifacts)
    for artifact in manifest.artifacts:
        if artifact.required or artifact.mandatory:
            required_names.add(artifact.path)

    for relative in sorted(declared):
        artifact = declared[relative]
        expected = artifact.sha256 or manifest.content_hashes.get(relative)
        if not expected:
            if relative in required_names:
                missing_hashes.append(relative)
                errors.append("required artifact has no hash: " + relative)
            else:
                warnings.append("optional artifact has no hash: " + relative)
            continue
        try:
            actual_path = _safe_artifact(release_root, relative)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not actual_path.is_file():
            if relative in required_names or artifact.required or artifact.mandatory:
                missing_files.append(relative)
                errors.append("required artifact is missing: " + relative)
            else:
                warnings.append("optional artifact is missing: " + relative)
            continue
        checked.append(relative)
        actual = _sha256(actual_path)
        if actual != expected:
            errors.append(
                f"hash mismatch for {relative}: expected {expected}, got {actual}"
            )
        expected_size = artifact.size_bytes
        if expected_size is not None and actual_path.stat().st_size != expected_size:
            errors.append(
                f"size mismatch for {relative}: expected {expected_size}, "
                f"got {actual_path.stat().st_size}"
            )

    valid = not errors and not missing_hashes and not missing_files
    return ManifestVerification(
        valid=valid,
        errors=errors,
        warnings=warnings,
        checked_artifacts=checked,
        missing_required_hashes=missing_hashes,
        missing_required_files=missing_files,
    )


__all__ = [
    "ArtifactRecord",
    "ManifestVerification",
    "ReleaseCheck",
    "ReleaseManifest",
    "ReleaseProfile",
    "load_manifest",
    "verify_manifest",
    "write_manifest",
]
