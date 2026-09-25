"""Source-bound identity assignment for the current canonical design.

This is deliberately an identity-only record.  It does not construct a
``DesignSolution``, selection decision, layout, approval hash, or BIM
authorization.  Those belong to later project gates.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from amanda_agent.design.canonical_reference import CanonicalReferenceProfile
from amanda_agent.requirements.program import PROGRAM_SOURCE_SHA256

IDENTITY_ARTIFACT_PATH = "project/requirements/canonical-solution-identity.yaml"
RECONCILIATION_ID = "P1-T01"
RECONCILIATION_REPORT_PATH = "docs/reports/P1-T01-four-board-reconciliation.md"
OFFICIAL_PROGRAM_PATH = "docs/source/programa_necessidades.pdf"
CANONICAL_BOARD_PATHS = (
    "docs/source/canonical/01_implantacao.png",
    "docs/source/canonical/02_administrativo.png",
    "docs/source/canonical/03_residencial.png",
    "docs/source/canonical/04_servicos.png",
)
_IDENTITY_PREFIX = "AMANDA-RUN-003-PAVILION-CANONICAL-"
_FORBIDDEN_IDS = frozenset(
    {
        "AMANDA-RUN-002-PAVILION-S02",
        "AMANDA-RUN-001-S01",
        "AMANDA-RUN-002-PAVILION-S01",
    }
)


class CanonicalIdentityError(ValueError):
    """The current canonical inputs do not support a new identity."""


class SourceHashBinding(BaseModel):
    """One repository source and the SHA-256 of its exact bytes."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class CanonicalSolutionIdentity(BaseModel):
    """A deterministic P2 identity with explicit non-authorization fields."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    schema_version: Literal[1] = 1
    status: Literal["IDENTITY_ASSIGNED"] = "IDENTITY_ASSIGNED"
    solution_id: str = Field(pattern=r"^AMANDA-RUN-003-PAVILION-CANONICAL-[0-9A-F]{12}$")
    identity_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    canonical_boards: tuple[SourceHashBinding, ...] = Field(min_length=4, max_length=4)
    program_source: SourceHashBinding
    reconciliation_id: Literal["P1-T01"]
    reconciliation_report: SourceHashBinding
    selected_design: None = None
    approval_hash: None = None
    bim_eligible: Literal[False] = False
    bim00_authorized: Literal[False] = False
    revit_write_authorized: Literal[False] = False

    @model_validator(mode="after")
    def validate_source_identity(self) -> CanonicalSolutionIdentity:
        if tuple(source.path for source in self.canonical_boards) != CANONICAL_BOARD_PATHS:
            raise ValueError("identity must bind the four canonical boards in profile order")
        board_hashes = tuple(source.sha256 for source in self.canonical_boards)
        if len(set(board_hashes)) != 4:
            raise ValueError("canonical board hashes must be distinct")
        if self.program_source.path != OFFICIAL_PROGRAM_PATH:
            raise ValueError("identity must bind the official program PDF")
        if self.program_source.sha256 != PROGRAM_SOURCE_SHA256:
            raise ValueError("identity must use the adopted official program PDF hash")
        if self.reconciliation_report.path != RECONCILIATION_REPORT_PATH:
            raise ValueError("identity must bind the P1-T01 reconciliation report")
        if self.solution_id in _FORBIDDEN_IDS:
            raise ValueError("stale and superseded linear solution IDs are forbidden")

        material = _identity_material(
            canonical_boards=self.canonical_boards,
            program_source=self.program_source,
            reconciliation_id=self.reconciliation_id,
            reconciliation_report=self.reconciliation_report,
        )
        fingerprint = _fingerprint(material)
        if self.identity_fingerprint != fingerprint:
            raise ValueError("identity fingerprint does not match its source bindings")
        expected_id = _IDENTITY_PREFIX + fingerprint[:12].upper()
        if self.solution_id != expected_id:
            raise ValueError("solution ID must be deterministically derived from its sources")
        return self


def _identity_material(
    *,
    canonical_boards: tuple[SourceHashBinding, ...],
    program_source: SourceHashBinding,
    reconciliation_id: str,
    reconciliation_report: SourceHashBinding,
) -> dict[str, object]:
    return {
        "canonical_boards": [item.model_dump(mode="json") for item in canonical_boards],
        "program_source": program_source.model_dump(mode="json"),
        "reconciliation_id": reconciliation_id,
        "reconciliation_report": reconciliation_report.model_dump(mode="json"),
    }


def _fingerprint(material: dict[str, object]) -> str:
    encoded = json.dumps(
        material, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def assign_canonical_solution_identity(root: Path) -> CanonicalSolutionIdentity:
    """Compute the current P2 identity from canonical files and P1 evidence."""

    root = Path(root)
    profile = CanonicalReferenceProfile.load(root)
    profile_paths = tuple(f"docs/source/{image}" for image in profile.canonical_images)
    if profile_paths != CANONICAL_BOARD_PATHS or len(profile.source_hashes) != 4:
        raise CanonicalIdentityError("canonical profile must bind the four current boards")

    program_path = root / OFFICIAL_PROGRAM_PATH
    try:
        program_hash = hashlib.sha256(program_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise CanonicalIdentityError("cannot read the official program PDF") from exc
    if program_hash != PROGRAM_SOURCE_SHA256:
        raise CanonicalIdentityError("official program PDF hash differs from the adopted baseline")

    program_manifest_path = root / "project/requirements/program.json"
    try:
        program_manifest = json.loads(program_manifest_path.read_text(encoding="utf-8"))
        manifest_program_hash = program_manifest["baseline"]["source_sha256"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise CanonicalIdentityError("adopted program manifest is missing its source hash") from exc
    if manifest_program_hash != program_hash:
        raise CanonicalIdentityError("adopted program manifest does not match the official PDF")

    report_path = root / RECONCILIATION_REPORT_PATH
    try:
        report_bytes = report_path.read_bytes()
    except OSError as exc:
        raise CanonicalIdentityError("cannot read the P1-T01 reconciliation report") from exc
    if not report_bytes or b"P1-T01" not in report_bytes:
        raise CanonicalIdentityError("reconciliation evidence does not identify P1-T01")

    boards = tuple(
        SourceHashBinding(path=path, sha256=digest)
        for path, digest in zip(profile_paths, profile.source_hashes, strict=True)
    )
    program_source = SourceHashBinding(path=OFFICIAL_PROGRAM_PATH, sha256=program_hash)
    reconciliation_report = SourceHashBinding(
        path=RECONCILIATION_REPORT_PATH,
        sha256=hashlib.sha256(report_bytes).hexdigest(),
    )
    material = _identity_material(
        canonical_boards=boards,
        program_source=program_source,
        reconciliation_id=RECONCILIATION_ID,
        reconciliation_report=reconciliation_report,
    )
    fingerprint = _fingerprint(material)
    solution_id = _IDENTITY_PREFIX + fingerprint[:12].upper()
    if solution_id in _FORBIDDEN_IDS:
        raise CanonicalIdentityError("generated solution ID collides with a forbidden identity")

    return CanonicalSolutionIdentity(
        solution_id=solution_id,
        identity_fingerprint=fingerprint,
        canonical_boards=boards,
        program_source=program_source,
        reconciliation_id=RECONCILIATION_ID,
        reconciliation_report=reconciliation_report,
    )


def write_canonical_solution_identity(
    root: Path, identity: CanonicalSolutionIdentity
) -> Path:
    """Persist the identity once; accept an identical repeat and reject drift."""

    root = Path(root)
    identity = CanonicalSolutionIdentity.model_validate(identity.model_dump(mode="json"))
    current_identity = assign_canonical_solution_identity(root)
    if identity != current_identity:
        raise CanonicalIdentityError(
            "identity does not match the current source bindings"
        )
    target = root / IDENTITY_ARTIFACT_PATH
    serialized = yaml.safe_dump(
        identity.model_dump(mode="json"),
        allow_unicode=True,
        sort_keys=False,
    )
    if target.exists():
        try:
            current = CanonicalSolutionIdentity.model_validate(
                yaml.safe_load(target.read_text(encoding="utf-8"))
            )
        except (OSError, yaml.YAMLError, ValueError) as exc:
            raise CanonicalIdentityError(
                "existing canonical solution identity is invalid; refusing overwrite"
            ) from exc
        if current != identity:
            raise CanonicalIdentityError(
                "existing canonical solution identity differs; refusing overwrite"
            )
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(serialized)
            stream.flush()
        temporary_path.replace(target)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return target
