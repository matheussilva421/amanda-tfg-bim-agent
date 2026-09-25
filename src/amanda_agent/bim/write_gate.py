"""Evidence-bound BIM-00 authorization for canonical preacceptance stages."""

from __future__ import annotations

import os
import re
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import BimStage
from .stages import CheckStatus, PreflightReport, StageCheck, StageOperation
from ..requirements.decisions import DecisionScenario

BIM00_REQUIRED_CHECKS: tuple[str, ...] = (
    "target_path",
    "writer_lease",
    "checkpoint",
    "historical_r12",
    "canonical_references",
    "capability_registry",
    "revit_provider",
    "units",
    "coordinate_site_mode",
    "family_strategy",
    "canonical_selection",
    "official_program_sha256",
    "repository_commit_sha",
    "project_state_revision",
    "project_state_sha256",
)
_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_COMMIT_SHA_PATTERN = r"^[0-9a-f]{40}$"


class CoordinateSiteMode(StrEnum):
    """Explicit coordinate basis permitted for the provisional study gate."""

    LOCAL_NORMALIZED_STUDY_NOT_SURVEYED = "LOCAL_NORMALIZED_STUDY_NOT_SURVEYED"


class Bim00GateRefused(RuntimeError):
    """BIM-00 evidence is incomplete, stale, or bound to another target."""


class WriteGateCheck(BaseModel):
    """One independently backed check in the BIM-00 record."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    status: CheckStatus
    evidence: str = Field(min_length=1)


class Bim00Evidence(BaseModel):
    """The typed, content-bound evidence required before R03/R04 writes."""

    model_config = ConfigDict(extra="forbid")

    gate_id: str = Field(pattern=r"^BIM-00$")
    status: CheckStatus
    target_path: Path
    target_sha256: str = Field(pattern=_SHA256_PATTERN)
    checkpoint_path: Path
    checkpoint_sha256: str = Field(pattern=_SHA256_PATTERN)
    solution_id: str = Field(min_length=1)
    approval_hash: str = Field(pattern=_SHA256_PATTERN)
    layout_hash: str = Field(pattern=_SHA256_PATTERN)
    coordinate_site_mode: CoordinateSiteMode
    canonical_source_hashes: tuple[str, str, str, str]
    official_program_sha256: str = Field(pattern=_SHA256_PATTERN)
    repository_commit_sha: str = Field(pattern=_COMMIT_SHA_PATTERN)
    project_state_revision: int = Field(ge=0, strict=True)
    project_state_sha256: str = Field(pattern=_SHA256_PATTERN)
    historical_r12_sha256: str = Field(pattern=_SHA256_PATTERN)
    capability_registry_sha256: str = Field(pattern=_SHA256_PATTERN)
    revit_build: str = Field(min_length=1)
    provider_status: str = Field(min_length=1)
    active_document_path: Path
    open_document_count: int = Field(ge=0)
    open_document_paths: list[Path] = Field(min_length=1)
    other_clients_connected: int = Field(ge=0)
    checks: list[WriteGateCheck] = Field(min_length=1)

    @field_validator("canonical_source_hashes")
    @classmethod
    def _validate_source_hashes(
        cls, values: tuple[str, str, str, str]
    ) -> tuple[str, str, str, str]:
        if len(values) != 4 or any(
            re.fullmatch(_SHA256_PATTERN, value) is None for value in values
        ):
            raise ValueError(
                "canonical_source_hashes must contain exactly four SHA-256 values"
            )
        return values


def _canonical_path(path: Path) -> str:
    return os.path.normcase(str(Path(path).resolve(strict=False)))


def _required_checks_passed(evidence: Bim00Evidence) -> None:
    by_name: dict[str, WriteGateCheck] = {}
    for check in evidence.checks:
        if check.name in by_name:
            raise Bim00GateRefused(f"duplicate BIM-00 check: {check.name}")
        by_name[check.name] = check
    missing = sorted(set(BIM00_REQUIRED_CHECKS) - by_name.keys())
    if missing:
        raise Bim00GateRefused("missing required BIM-00 checks: " + ", ".join(missing))
    if any(by_name[name].status is not CheckStatus.PASS for name in BIM00_REQUIRED_CHECKS):
        raise Bim00GateRefused("not all required checks passed")
    if (
        by_name["coordinate_site_mode"].evidence
        != evidence.coordinate_site_mode.value
    ):
        raise Bim00GateRefused(
            "coordinate-site-mode check does not match the typed coordinate site mode"
        )


def _validate_expected_bindings(
    *,
    official_program_sha256: str,
    repository_commit_sha: str,
    project_state_revision: int,
    project_state_sha256: str,
    coordinate_site_mode: CoordinateSiteMode,
) -> None:
    if (
        not isinstance(coordinate_site_mode, CoordinateSiteMode)
        or coordinate_site_mode
        is not CoordinateSiteMode.LOCAL_NORMALIZED_STUDY_NOT_SURVEYED
    ):
        raise Bim00GateRefused("expected BIM-00 coordinate site mode is invalid")
    for name, value in (
        ("official_program_sha256", official_program_sha256),
        ("project_state_sha256", project_state_sha256),
    ):
        if not isinstance(value, str) or re.fullmatch(_SHA256_PATTERN, value) is None:
            raise Bim00GateRefused(f"expected BIM-00 {name} is invalid")
    if (
        not isinstance(repository_commit_sha, str)
        or re.fullmatch(_COMMIT_SHA_PATTERN, repository_commit_sha) is None
    ):
        raise Bim00GateRefused("expected BIM-00 repository_commit_sha is invalid")
    if (
        isinstance(project_state_revision, bool)
        or not isinstance(project_state_revision, int)
        or project_state_revision < 0
    ):
        raise Bim00GateRefused("expected BIM-00 project_state_revision is invalid")


def _verify_binding(
    evidence: Bim00Evidence,
    *,
    target_path: Path,
    solution_id: str,
    approval_hash: str,
    layout_hash: str,
    canonical_source_hashes: tuple[str, str, str, str],
    official_program_sha256: str,
    repository_commit_sha: str,
    project_state_revision: int,
    project_state_sha256: str,
    coordinate_site_mode: CoordinateSiteMode,
) -> None:
    _required_checks_passed(evidence)
    _validate_expected_bindings(
        official_program_sha256=official_program_sha256,
        repository_commit_sha=repository_commit_sha,
        project_state_revision=project_state_revision,
        project_state_sha256=project_state_sha256,
        coordinate_site_mode=coordinate_site_mode,
    )
    if evidence.status is not CheckStatus.PASS:
        raise Bim00GateRefused("BIM-00 evidence status is not PASS")
    if _canonical_path(evidence.target_path) != _canonical_path(target_path):
        raise Bim00GateRefused("BIM-00 target path does not match the requested target")
    if _canonical_path(evidence.active_document_path) != _canonical_path(target_path):
        raise Bim00GateRefused("active document is not the BIM-00 target")
    if _canonical_path(evidence.checkpoint_path) == _canonical_path(target_path):
        raise Bim00GateRefused("checkpoint must be a separate immutable file")
    if evidence.target_sha256 != evidence.checkpoint_sha256:
        raise Bim00GateRefused("checkpoint hash does not match the saved target")
    if evidence.solution_id != solution_id:
        raise Bim00GateRefused("BIM-00 solution_id does not match the active selection")
    if evidence.approval_hash != approval_hash:
        raise Bim00GateRefused("BIM-00 approval_hash does not match the active selection")
    if evidence.layout_hash != layout_hash:
        raise Bim00GateRefused("BIM-00 layout_hash does not match the current geometry plan")
    if evidence.canonical_source_hashes != canonical_source_hashes:
        raise Bim00GateRefused(
            "BIM-00 canonical board hashes do not match the loaded references"
        )
    if evidence.official_program_sha256 != official_program_sha256:
        raise Bim00GateRefused(
            "BIM-00 official program SHA-256 does not match the active source"
        )
    if evidence.repository_commit_sha != repository_commit_sha:
        raise Bim00GateRefused(
            "BIM-00 repository commit does not match the active checkout"
        )
    if evidence.project_state_revision != project_state_revision:
        raise Bim00GateRefused(
            "BIM-00 PROJECT_STATE revision does not match the active state"
        )
    if evidence.project_state_sha256 != project_state_sha256:
        raise Bim00GateRefused(
            "BIM-00 PROJECT_STATE SHA-256 does not match the active state file"
        )
    if evidence.coordinate_site_mode is not coordinate_site_mode:
        raise Bim00GateRefused(
            "BIM-00 coordinate site mode does not match the expected study mode"
        )
    open_paths = [_canonical_path(path) for path in evidence.open_document_paths]
    if len(open_paths) != evidence.open_document_count:
        raise Bim00GateRefused(
            "BIM-00 open-document paths do not match the live document count"
        )
    if len(set(open_paths)) != len(open_paths):
        raise Bim00GateRefused("BIM-00 open-document paths contain duplicates")
    target = _canonical_path(target_path)
    if open_paths.count(target) != 1:
        raise Bim00GateRefused("BIM-00 target must appear exactly once in open documents")
    bridge_anchor = _canonical_path(
        Path.home() / ".horizun" / "anchor" / "HZ_ANCHOR_2027.rvt"
    )
    unexpected = [path for path in open_paths if path not in {target, bridge_anchor}]
    if unexpected or len(open_paths) > 2:
        raise Bim00GateRefused(
            "BIM-00 permits only the target and the bridge-owned anchor as open documents"
        )
    if evidence.other_clients_connected != 0:
        raise Bim00GateRefused("BIM-00 requires zero other Revit clients")
    if evidence.provider_status.casefold() != "healthy":
        raise Bim00GateRefused("BIM-00 provider is not healthy")


def authorize_preacceptance_stage(
    plan: Any,
    evidence: Bim00Evidence,
    *,
    target_path: Path,
    solution_id: str,
    approval_hash: str,
    layout_hash: str,
    canonical_source_hashes: tuple[str, str, str, str],
    official_program_sha256: str,
    repository_commit_sha: str,
    project_state_revision: int,
    project_state_sha256: str,
    coordinate_site_mode: CoordinateSiteMode,
) -> Any:
    """Remove only BIM-00 from R03/R04 after every binding is checked."""

    stage = getattr(plan, "stage", None)
    if stage not in {BimStage.R03, BimStage.R04}:
        raise Bim00GateRefused("BIM-00 authorization is available only R03/R04 stages")
    _verify_binding(
        evidence,
        target_path=target_path,
        solution_id=solution_id,
        approval_hash=approval_hash,
        layout_hash=layout_hash,
        canonical_source_hashes=canonical_source_hashes,
        official_program_sha256=official_program_sha256,
        repository_commit_sha=repository_commit_sha,
        project_state_revision=project_state_revision,
        project_state_sha256=project_state_sha256,
        coordinate_site_mode=coordinate_site_mode,
    )
    operations = getattr(plan, "operations", None)
    if not isinstance(operations, list) or not all(
        isinstance(operation, StageOperation) for operation in operations
    ):
        raise Bim00GateRefused("preacceptance plan operations are invalid")
    released = [
        operation.model_copy(
            update={
                "blocked_by": [
                    gate for gate in operation.blocked_by if gate != "BIM-00"
                ]
            }
        )
        for operation in operations
    ]
    preflight = getattr(plan, "preflight", None)
    if not isinstance(preflight, PreflightReport):
        raise Bim00GateRefused("preacceptance plan has no typed preflight report")
    if preflight.scenario is not DecisionScenario.STUDY:
        raise Bim00GateRefused("BIM-00 authorization is available only for STUDY scenario")
    checks = [check for check in preflight.checks if check.name != "bim_00"]
    checks.append(
        StageCheck(
            name="bim_00",
            status=CheckStatus.PASS,
            detail=(
                "BIM-00 passed for this target, checkpoint, selection and canonical board set"
            ),
        )
    )
    authorized_preflight = preflight.model_copy(update={"checks": checks})
    return plan.model_copy(
        update={"operations": released, "preflight": authorized_preflight}
    )


__all__ = [
    "BIM00_REQUIRED_CHECKS",
    "Bim00Evidence",
    "Bim00GateRefused",
    "CoordinateSiteMode",
    "WriteGateCheck",
    "authorize_preacceptance_stage",
]
