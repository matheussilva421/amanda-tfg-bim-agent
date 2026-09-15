"""Fail-closed publication of immutable GOLDEN release directories."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .manifest import (
    ManifestVerification,
    ReleaseManifest,
    ReleaseProfile,
    load_manifest,
    verify_manifest,
)

COMPLETION_MARKER = "RELEASE_COMPLETE.json"
REQUIRED_REPORTS = (
    "QA_REPORT.md",
    "PROGRAM_COMPLIANCE.md",
    "ACCESSIBILITY_REPORT.md",
    "CAPABILITY_REPORT.md",
    "EXPORT_REPORT.md",
    "provenance.json",
)


class PromotionRefused(RuntimeError):
    """A release candidate failed an immutable-publication gate."""


@dataclass(frozen=True)
class PromotionPlan:
    release_id: str
    source: Path
    golden_root: Path
    target: Path


@dataclass(frozen=True)
class ReleaseVerification:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    manifest: dict[str, Any] | None
    manifest_result: ManifestVerification | None

    def __bool__(self) -> bool:
        return self.valid


@dataclass(frozen=True)
class PromotionResult:
    target: Path
    staging: Path
    manifest: dict[str, Any]


def _resolve_source(
    release: str | Path,
    release_id: str | None,
) -> tuple[Path, str]:
    candidate = Path(release)
    if release_id is not None:
        if (candidate / "manifest.json").is_file():
            return candidate, release_id
        roots = (
            candidate / "releases" / release_id,
            candidate / "release" / release_id,
            candidate / "deliverables" / release_id,
            candidate / release_id,
        )
        for root in roots:
            if (root / "manifest.json").is_file():
                return root, release_id
        return roots[0], release_id
    if candidate.is_file() and candidate.name == "manifest.json":
        source = candidate.parent
    else:
        source = candidate
    manifest_path = source / "manifest.json"
    if not manifest_path.is_file():
        raise PromotionRefused("release manifest is missing: " + str(manifest_path))
    try:
        release_name = load_manifest(manifest_path).release
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise PromotionRefused("release manifest is invalid: " + str(exc)) from exc
    return source, release_name


def plan_promotion(
    release: str | Path,
    *,
    release_id: str | None = None,
    golden_root: str | Path | None = None,
) -> PromotionPlan:
    """Resolve a promotion without creating or mutating any directory."""

    source, resolved_id = _resolve_source(release, release_id)
    root = Path(golden_root) if golden_root is not None else source.parent / "GOLDEN"
    return PromotionPlan(
        release_id=resolved_id,
        source=source,
        golden_root=root,
        target=root / resolved_id,
    )


def _status(value: Any) -> str:
    if isinstance(value, str):
        return value.upper()
    return str(value).upper()


def _has_explicit_waiver(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, str):
        return bool(value.strip())
    return value is True


def _check_qa(manifest: ReleaseManifest) -> list[str]:
    summary = manifest.qa_summary
    status = _status(
        summary.get("status", summary.get("overall", summary.get("result", "UNKNOWN")))
    )
    if status in {"FAIL", "FAILED", "BLOCKED", "BLOCKED_BY_INPUT"}:
        return ["QA status is " + status]
    if status not in {"PASS", "PASS_WITH_WARNINGS"}:
        return ["QA status is not an explicit PASS: " + status]
    return []


def _check_required_checks(manifest: ReleaseManifest) -> list[str]:
    checks = manifest.required_checks
    if not checks:
        return ["no explicit mandatory checks were recorded"]
    errors: list[str] = []
    for check in checks:
        if not check.mandatory:
            continue
        status = _status(check.status)
        if status == "PASS":
            continue
        if (
            status == "BLOCKED"
            and manifest.release_profile is ReleaseProfile.STUDY
            and _has_explicit_waiver(check.waiver)
            and bool(manifest.accepted_limitations)
        ):
            continue
        suffix = " for FINAL profile" if manifest.release_profile is ReleaseProfile.FINAL else ""
        errors.append(f"mandatory check {check.id} is {status}{suffix}")
    if not any(check.mandatory for check in checks):
        errors.append("no explicit mandatory checks were recorded")
    return errors


def _check_persistence(manifest: ReleaseManifest) -> list[str]:
    summary = manifest.persistence_summary
    try:
        from ..qa.persistence import PersistenceRecord

        record = PersistenceRecord.model_validate(summary)
    except (TypeError, ValueError) as exc:
        return ["persistence evidence is invalid: " + str(exc)]
    return [] if record.is_complete else ["persistence sequence is incomplete"]


def _check_exports(manifest: ReleaseManifest) -> list[str]:
    mandatory = [
        export
        for export in manifest.exports
        if bool(export.get("mandatory", export.get("required", False)))
    ]
    if not mandatory:
        return ["no mandatory export validation was recorded"]
    errors: list[str] = []
    for export in mandatory:
        status = _status(
            export.get(
                "validation_status",
                export.get("status", export.get("result", "UNKNOWN")),
            )
        )
        if status not in {"PASS", "VALID", "VERIFIED"}:
            errors.append(
                "mandatory export "
                + str(export.get("path", "<unnamed>"))
                + " is "
                + status
            )
    return errors


def _check_reports(source: Path) -> list[str]:
    return [
        "required report is missing: " + relative
        for relative in REQUIRED_REPORTS
        if not (source / relative).is_file()
    ]


def verify_release(
    release: str | Path,
    *,
    require_sealed: bool = False,
) -> ReleaseVerification:
    """Verify hashes, explicit gates, reports and optional seal marker."""

    source = Path(release)
    manifest_path = source / "manifest.json"
    if not manifest_path.is_file():
        return ReleaseVerification(
            valid=False,
            errors=("release manifest is missing: " + str(manifest_path),),
            warnings=(),
            manifest=None,
            manifest_result=None,
        )
    try:
        manifest = load_manifest(manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return ReleaseVerification(
            valid=False,
            errors=("invalid release manifest: " + str(exc),),
            warnings=(),
            manifest=None,
            manifest_result=None,
        )

    manifest_result = verify_manifest(manifest_path)
    errors = list(manifest_result.errors)
    errors.extend(_check_qa(manifest))
    errors.extend(_check_required_checks(manifest))
    errors.extend(_check_persistence(manifest))
    errors.extend(_check_exports(manifest))
    errors.extend(_check_reports(source))
    if require_sealed and not (source / COMPLETION_MARKER).is_file():
        errors.append("release completion marker is missing")
    if manifest.release_profile is ReleaseProfile.FINAL and manifest.accepted_limitations:
        errors.append("FINAL profile cannot retain accepted limitations")
    return ReleaseVerification(
        valid=not errors,
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(manifest_result.warnings),
        manifest=manifest.payload(),
        manifest_result=manifest_result,
    )


def _ensure_new_target(target: Path) -> None:
    if os.path.lexists(str(target)):
        raise PromotionRefused("GOLDEN target already exists: " + str(target))


def _write_marker(staging: Path, manifest: ReleaseManifest) -> None:
    marker = staging / COMPLETION_MARKER
    marker.write_text(
        json.dumps(
            {
                "release": manifest.release,
                "manifest": "manifest.json",
                "status": "SEALED",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    with marker.open("r+b") as stream:
        stream.flush()
        os.fsync(stream.fileno())


def promote(
    release: str | Path,
    *,
    release_id: str | None = None,
    golden_root: str | Path | None = None,
) -> PromotionResult:
    """Validate an RC, stage a complete copy, and publish without overwrite."""

    plan = plan_promotion(
        release,
        release_id=release_id,
        golden_root=golden_root,
    )
    initial = verify_release(plan.source)
    if not initial.valid:
        raise PromotionRefused("; ".join(initial.errors))
    assert initial.manifest is not None
    manifest = ReleaseManifest.model_validate(initial.manifest)
    _ensure_new_target(plan.target)
    plan.golden_root.mkdir(parents=True, exist_ok=True)
    _ensure_new_target(plan.target)
    staging = Path(
        tempfile.mkdtemp(
            prefix="." + plan.release_id + ".",
            suffix=".staging",
            dir=str(plan.golden_root),
        )
    )
    shutil.copytree(plan.source, staging, dirs_exist_ok=True)
    staged = verify_release(staging)
    if not staged.valid:
        raise PromotionRefused(
            "staged release verification failed: " + "; ".join(staged.errors)
        )
    _write_marker(staging, manifest)
    os.rename(staging, plan.target)
    return PromotionResult(
        target=plan.target,
        staging=staging,
        manifest=manifest.payload(),
    )


__all__ = [
    "COMPLETION_MARKER",
    "PromotionPlan",
    "PromotionRefused",
    "PromotionResult",
    "ReleaseVerification",
    "plan_promotion",
    "promote",
    "verify_release",
]
