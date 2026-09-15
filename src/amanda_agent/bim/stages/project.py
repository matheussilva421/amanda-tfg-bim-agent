"""R01 project-initialization stage.

The stage is pure until an adapter is injected. It preflights the execution
mode, picks the project template in the documented order, fixes the naming
and metadata deterministically, and only then describes the desired
``revit.create_project`` operation. Amanda's template is never written to: if
she supplies one it must already have been validated on a copy.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..checkpoints import sha256_file
from ..models import BimStage
from ..verification import VerificationResult, verify_write
from . import (
    PreflightReport,
    PreflightRequest,
    StageError,
    StageExecutionRecord,
    StageOperation,
    StagePreflightError,
    StageToolInvoker,
    dispatch_operations,
    provider_chain,
    run_preflight,
    stage_checkpoint_label,
    with_stage_requirements,
)

PROJECT_TEMPLATE_SUFFIX = ".rte"
PROJECT_CREATE_CAPABILITY = "revit.create_project"
PROJECT_LOGICAL_ID = "PRJ-0001"

_ARCHITECTURAL_HINTS = ("architect", "arquitet")


class TemplateOrigin(StrEnum):
    """Where the baseline project template came from."""

    AMANDA_SUPPLIED = "AMANDA_SUPPLIED"
    INSTALLED_ARCHITECTURAL = "INSTALLED_ARCHITECTURAL"


class TemplateSelection(BaseModel):
    """The chosen template plus why it was chosen."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    origin: TemplateOrigin
    template_path: Path
    tested: bool = False
    copy_before_use: bool = False
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    discovered: list[Path] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def default_template_roots(program_files: str | None = None) -> list[Path]:
    """Return the usual Autodesk template folders of this machine, if any."""

    base = Path(program_files or os.environ.get("ProgramFiles", r"C:\Program Files"))
    autodesk = base / "Autodesk"
    if not autodesk.is_dir():
        return []
    return sorted(
        (candidate / "Templates" for candidate in autodesk.glob("Revit *")),
        key=lambda path: path.name.casefold(),
    )


def discover_architectural_templates(
    roots: Iterable[Path] | None = None,
) -> list[Path]:
    """Find installed architectural templates in a deterministic order."""

    selected: list[Path] = []
    for root in roots if roots is not None else default_template_roots():
        base = Path(root)
        if not base.is_dir():
            continue
        for path in base.rglob(f"*{PROJECT_TEMPLATE_SUFFIX}"):
            if any(hint in path.name.casefold() for hint in _ARCHITECTURAL_HINTS):
                selected.append(path)
    return sorted(selected, key=lambda path: (path.name.casefold(), str(path).casefold()))


def select_project_template(
    *,
    amanda_template: Path | None = None,
    amanda_template_tested: bool = False,
    roots: Iterable[Path] | None = None,
) -> TemplateSelection:
    """Amanda's tested template first, otherwise an installed architectural one."""

    notes: list[str] = []
    supplied = Path(amanda_template) if amanda_template is not None else None
    if supplied is not None and not supplied.is_file():
        notes.append(f"supplied template is missing on disk: {supplied}")
        supplied = None
    if supplied is not None and not amanda_template_tested:
        notes.append(
            "supplied Amanda template was not tested on a copy; ignored for this run"
        )
        supplied = None

    if supplied is not None:
        return TemplateSelection(
            origin=TemplateOrigin.AMANDA_SUPPLIED,
            template_path=supplied.resolve(),
            tested=True,
            copy_before_use=True,
            sha256=sha256_file(supplied),
            discovered=[supplied.resolve()],
            notes=[
                *notes,
                "only a copy of Amanda's template is used; the original stays untouched",
            ],
        )

    discovered = discover_architectural_templates(roots)
    if not discovered:
        raise StageError("no installed architectural template was discovered")
    chosen = discovered[0]
    return TemplateSelection(
        origin=TemplateOrigin.INSTALLED_ARCHITECTURAL,
        template_path=chosen,
        tested=False,
        copy_before_use=False,
        sha256=sha256_file(chosen),
        discovered=discovered,
        notes=[
            *notes,
            (
                "template was discovered by name and version; it is exercised only when the "
                "project is created"
            ),
        ],
    )


class NamingScheme(BaseModel):
    """The deterministic naming vocabulary of the project."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    view_prefix: str = Field(default="V", min_length=1)
    sheet_prefix: str = Field(default="S", min_length=1)
    room_scheme: str = Field(default="{sector}-{index:03d}", min_length=1)
    family_prefix: str = Field(default="FAM", min_length=1)
    material_prefix: str = Field(default="MAT", min_length=1)
    stage_prefix: str = Field(default="STAGE", min_length=1)


class ProjectMetadata(BaseModel):
    """Desired project identity and naming, reproducible from its inputs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    project_name: str = Field(min_length=1)
    project_number: str = Field(min_length=1)
    project_code: str = Field(min_length=1)
    solution_id: str = Field(min_length=1)
    generation_run: str = Field(min_length=1)
    requirements_version: str = Field(min_length=1)
    site_version: str = Field(min_length=1)
    template_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    view_prefix: str = Field(min_length=1)
    sheet_prefix: str = Field(min_length=1)
    room_number_scheme: str = Field(min_length=1)
    family_prefix: str = Field(min_length=1)
    material_prefix: str = Field(min_length=1)
    stage_prefix: str = Field(min_length=1)


def _sanitize(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()


def build_project_metadata(
    *,
    project_code: str,
    solution_id: str,
    generation_run: str,
    requirements_version: str,
    site_version: str,
    template_sha256: str | None = None,
    naming: NamingScheme | None = None,
) -> ProjectMetadata:
    """Derive the project identity by pure computation, never by a clock."""

    scheme = naming or NamingScheme()
    number = _sanitize(project_code)
    return ProjectMetadata(
        project_name=f"{number}-{_sanitize(solution_id)}",
        project_number=number,
        project_code=project_code,
        solution_id=solution_id,
        generation_run=generation_run,
        requirements_version=requirements_version,
        site_version=site_version,
        template_sha256=template_sha256,
        view_prefix=f"{number}-{_sanitize(scheme.view_prefix)}",
        sheet_prefix=f"{number}-{_sanitize(scheme.sheet_prefix)}",
        room_number_scheme=f"{number}-{scheme.room_scheme}",
        family_prefix=f"{number}-{_sanitize(scheme.family_prefix)}",
        material_prefix=f"{number}-{_sanitize(scheme.material_prefix)}",
        stage_prefix=f"{number}-{_sanitize(scheme.stage_prefix)}",
    )


class ProjectInitializationPlan(BaseModel):
    """The read-only R01 plan plus the label of the checkpoint it must leave."""

    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R01
    preflight: PreflightReport
    template: TemplateSelection
    metadata: ProjectMetadata
    operations: list[StageOperation] = Field(default_factory=list)
    checkpoint_label: str = Field(default="R01_PROJECT_INITIALIZED", min_length=1)


def _version(
    selected_inputs: dict[str, str],
    key: str,
    explicit: object | None,
) -> str:
    if explicit is not None and str(explicit):
        return str(explicit)
    return selected_inputs.get(key) or "UNVERSIONED"


def plan_project_initialization(
    request: PreflightRequest,
    *,
    amanda_template: Path | None = None,
    amanda_template_tested: bool = False,
    template_roots: Iterable[Path] | None = None,
    project_code: str = "AMANDA",
    naming: NamingScheme | None = None,
) -> ProjectInitializationPlan:
    """Preflight, choose the template, fix the naming and describe the write."""

    effective = with_stage_requirements(request)
    report = run_preflight(effective)
    if not report.ok:
        raise StagePreflightError("R01 preflight refused: " + "; ".join(report.problems))

    template = select_project_template(
        amanda_template=amanda_template,
        amanda_template_tested=amanda_template_tested,
        roots=template_roots,
    )
    solution = effective.solution
    metadata = build_project_metadata(
        project_code=project_code,
        solution_id=solution.solution_id if solution is not None else "STUDY",
        generation_run=effective.generation_run,
        requirements_version=_version(
            effective.selected_inputs,
            "requirements_version",
            solution.requirements_version if solution is not None else None,
        ),
        site_version=_version(
            effective.selected_inputs,
            "site_version",
            str(solution.site_version) if solution is not None else None,
        ),
        template_sha256=template.sha256,
        naming=naming,
    )
    preferred, fallbacks = provider_chain(
        effective.registry,
        PROJECT_CREATE_CAPABILITY,
        revit_build=effective.revit_build,
        tool_schema_hash=effective.tool_schema_hash,
        scope=effective.evidence_scope,
    )
    operation = StageOperation(
        stage=BimStage.R01,
        logical_id=PROJECT_LOGICAL_ID,
        semantic_capability=PROJECT_CREATE_CAPABILITY,
        payload={
            "template_path": str(template.template_path),
            "template_origin": template.origin.value,
            "template_sha256": template.sha256,
            "project_name": metadata.project_name,
            "project_number": metadata.project_number,
            "view_prefix": metadata.view_prefix,
            "sheet_prefix": metadata.sheet_prefix,
            "room_number_scheme": metadata.room_number_scheme,
            "family_prefix": metadata.family_prefix,
            "material_prefix": metadata.material_prefix,
            "stage_prefix": metadata.stage_prefix,
            "solution_id": metadata.solution_id,
            "generation_run": metadata.generation_run,
        },
        verification_rules=[
            "independent_requery",
            "document_identity_matches",
            "template_matches",
            "naming_matches",
        ],
        preferred_provider=preferred,
        fallback_providers=fallbacks,
    )
    return ProjectInitializationPlan(
        preflight=report,
        template=template,
        metadata=metadata,
        operations=[operation],
        checkpoint_label=stage_checkpoint_label(BimStage.R01),
    )


def execute_project_initialization(
    plan: ProjectInitializationPlan,
    *,
    invoker: StageToolInvoker,
) -> list[StageExecutionRecord]:
    """Dispatch the desired operations through the injected adapter."""

    return dispatch_operations(plan.operations, invoker=invoker)


def verify_project_initialization(
    plan: ProjectInitializationPlan,
    *,
    tool_reported_success: bool,
    query_result: dict[str, object] | None,
    require_persistence: bool = False,
    persistence_evidence: bool = False,
) -> list[VerificationResult]:
    """Verify the R01 project identity and naming after an independent query."""

    if not plan.operations:
        raise StageError("R01 project plan has no operation to verify")
    operation = plan.operations[0]
    metadata = plan.metadata
    expected = {
        "project_name": metadata.project_name,
        "project_number": metadata.project_number,
        "view_prefix": metadata.view_prefix,
        "sheet_prefix": metadata.sheet_prefix,
        "room_number_scheme": metadata.room_number_scheme,
        "family_prefix": metadata.family_prefix,
        "material_prefix": metadata.material_prefix,
        "stage_prefix": metadata.stage_prefix,
    }
    return verify_write(
        logical_id=operation.logical_id,
        tool_reported_success=tool_reported_success,
        query_result=query_result,
        expected_properties=expected,
        require_persistence=require_persistence,
        persistence_evidence=persistence_evidence,
    )


__all__ = [
    "PROJECT_CREATE_CAPABILITY",
    "PROJECT_LOGICAL_ID",
    "PROJECT_TEMPLATE_SUFFIX",
    "NamingScheme",
    "ProjectInitializationPlan",
    "ProjectMetadata",
    "TemplateOrigin",
    "TemplateSelection",
    "build_project_metadata",
    "default_template_roots",
    "discover_architectural_templates",
    "execute_project_initialization",
    "plan_project_initialization",
    "select_project_template",
    "verify_project_initialization",
]
