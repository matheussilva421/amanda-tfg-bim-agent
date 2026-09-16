"""Compile a design-engine solution into the permitted conceptual BIM stages."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from amanda_agent.design.models import DesignSolution
from amanda_agent.models.capability import CapabilityRegistry
from amanda_agent.requirements.decisions import DecisionScenario
from amanda_agent.site.models import (
    BoundaryKind,
    BoundaryPolygon,
    SiteModel,
    SourceTopographyState,
    Topography,
    TopographyRepresentation,
)

from .models import BimStage
from .stages import (
    CONCEPT_ONLY_MAX_STAGE,
    EvidenceScope,
    ExecutionMode,
    PreflightRequest,
    stage_at_or_before,
)
from .stages.levels import GridAxis, LevelReference, ReferenceMarker, plan_levels_stage
from .stages.massing import MassingBlock, plan_massing_stage
from .stages.project import plan_project_initialization
from .stages.site import plan_site_stage

PROVISIONAL_HEIGHT_M = 3.2


class SolutionCompilerError(ValueError):
    """The solution cannot be compiled under the requested BIM scope."""


def _coerce_stage(value: BimStage | str) -> BimStage:
    if isinstance(value, BimStage):
        return value
    try:
        return BimStage(value)
    except ValueError:
        try:
            return BimStage[str(value)]
        except KeyError as exc:
            raise SolutionCompilerError(f"unknown BIM stage {value!r}") from exc


def _load_solution(path: str | Path) -> DesignSolution:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    try:
        return DesignSolution.model_validate_json(source.read_text(encoding="utf-8"))
    except (ValidationError, json.JSONDecodeError) as exc:
        raise SolutionCompilerError(f"invalid solution.json: {source}") from exc


def _site_from_solution(solution: DesignSolution) -> SiteModel:
    geometry = solution.geometry
    raw_site = geometry.get("site")
    if not isinstance(raw_site, Mapping):
        raise SolutionCompilerError("solution geometry has no GeoJSON site polygon")
    try:
        boundary = BoundaryPolygon.from_geojson(
            dict(raw_site),
            kind=BoundaryKind.STUDY_PLACEHOLDER,
        )
    except (TypeError, ValueError) as exc:
        raise SolutionCompilerError("solution geometry site is not a valid polygon") from exc
    version_text = str(solution.site_version)
    version_match = re.search(r"(\d+)$", version_text)
    if version_match is None:
        raise SolutionCompilerError(
            "solution site_version must end with a numeric version for SiteModel"
        )
    return SiteModel(
        site_version=int(version_match.group(1)),
        boundary=boundary,
        topography=Topography(
            source_state=SourceTopographyState.MISSING,
            representation=TopographyRepresentation.PLANAR_PLACEHOLDER,
        ),
    )


def _request(
    solution: DesignSolution,
    site: SiteModel,
    *,
    registry: CapabilityRegistry,
    stage: BimStage,
    mode: ExecutionMode,
    scenario: DecisionScenario,
    revit_build: str,
    tool_schema_hash: str,
    fixture: bool,
    evidence_scope: EvidenceScope,
) -> PreflightRequest:
    selected_inputs = {
        "requirements_version": solution.requirements_version,
        "site_version": str(solution.site_version),
        "engine_version": solution.engine_version,
    }
    return PreflightRequest(
        mode=mode,
        stage=stage,
        scenario=scenario,
        registry=registry,
        revit_build=revit_build,
        tool_schema_hash=tool_schema_hash,
        expected_build=revit_build,
        expected_tool_schema_hash=tool_schema_hash,
        selected_inputs=selected_inputs,
        expected_inputs=selected_inputs,
        solution=solution,
        site=site,
        fixture=fixture,
        evidence_scope=evidence_scope,
        generation_run=solution.run_id,
    )


def _identity_note(solution: DesignSolution) -> str:
    if solution.approval_hash is None:
        raise SolutionCompilerError("solution has no content-bound approval_hash")
    return (
        "BIT_IDENTITY: "
        f"solution_id={solution.solution_id}; approval_hash={solution.approval_hash}"
    )


def _with_identity(plan: Any, solution: DesignSolution) -> Any:
    note = _identity_note(solution)
    operations = [
        operation.model_copy(
            update={
                "payload": {
                    **operation.payload,
                    "solution_id": solution.solution_id,
                    "approval_hash": solution.approval_hash,
                }
            }
        )
        for operation in plan.operations
    ]
    preflight = plan.preflight.model_copy(
        update={"notes": [*plan.preflight.notes, note]}
    )
    updates: dict[str, Any] = {
        "preflight": preflight,
        "operations": operations,
    }
    if hasattr(plan, "notes"):
        updates["notes"] = [*plan.notes, note]
    return plan.model_copy(update=updates)


def _level_and_grid(site: SiteModel) -> tuple[LevelReference, GridAxis, ReferenceMarker]:
    boundary = site.boundary.coordinates
    start = tuple(boundary[0])
    end = tuple(boundary[1])
    level = LevelReference(
        logical_id="LEVEL-01",
        name="Térreo",
        elevation_m=0.0,
        evidence=[
            "solution.json:geometry.rooms[*].level=0 (level index only; no surveyed elevation)"
        ],
        source_kind="VERIFIED_SOURCE",
    )
    grid = GridAxis(
        logical_id="GRID-01",
        name="A",
        start=start,
        end=end,
        assumption="PROVISIONAL_ASSUMPTION",
    )
    reference = ReferenceMarker(
        logical_id="REF-PROJECT-ORIGIN",
        name="Project Origin",
        kind="PROJECT_ORIGIN",
        coordinate=(0.0, 0.0, 0.0),
        evidence=["PROVISIONAL_ASSUMPTION: local design origin z=0; no survey datum"],
        is_provisional=True,
    )
    return level, grid, reference


def _massing_blocks(solution: DesignSolution) -> list[MassingBlock]:
    raw_blocks = solution.geometry.get("blocks")
    if not isinstance(raw_blocks, list) or not raw_blocks:
        raise SolutionCompilerError("solution geometry has no design-engine blocks")
    blocks: list[MassingBlock] = []
    for raw in raw_blocks:
        if not isinstance(raw, Mapping):
            raise SolutionCompilerError("solution geometry contains an invalid block")
        geometry = raw.get("geometry")
        if not isinstance(geometry, Mapping):
            raise SolutionCompilerError("a design-engine block has no geometry")
        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 1:
            raise SolutionCompilerError("a design-engine block is not a single polygon")
        try:
            footprint = [
                (float(point[0]), float(point[1]))
                for point in coordinates[0]
            ]
            blocks.append(
                MassingBlock(
                    logical_id=str(raw["logical_id"]),
                    name=str(raw["logical_id"]),
                    sector_id=str(raw["sector_id"]),
                    footprint=footprint,
                    height_m=PROVISIONAL_HEIGHT_M,
                    source_area_m2=float(raw["area_m2"]),
                    demand_m2=float(raw["demand_m2"]),
                    source_solution_id=solution.solution_id,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SolutionCompilerError("a design-engine block has invalid fields") from exc
    return blocks


def compile_solution(
    solution_path: str | Path,
    *,
    registry=None,
    revit_build: str | None = None,
    tool_schema_hash: str | None = None,
    mode: ExecutionMode | str = ExecutionMode.CONCEPT_ONLY,
    scenario: DecisionScenario | str = DecisionScenario.STUDY,
    fixture: bool = False,
    evidence_scope: EvidenceScope = EvidenceScope.SYNTHETIC,
    amanda_template: Path | None = None,
    amanda_template_tested: bool = False,
    template_roots: Iterable[Path] | None = None,
    project_code: str = "AMANDA",
    max_stage: BimStage | str | None = None,
) -> list[Any]:
    """Read one solution and build the ordered R01-R04 stage plans.

    Capability evidence and the R01 template are injected so planning never
    fabricates provider health or touches Revit.  ``max_stage`` is useful for
    callers that want a shorter prefix; CONCEPT_ONLY refuses R05 and later.
    """

    if registry is None:
        raise SolutionCompilerError("a capability registry is required for compilation")
    solution = _load_solution(solution_path)
    selected_mode = mode if isinstance(mode, ExecutionMode) else ExecutionMode(mode)
    selected_scenario = (
        scenario if isinstance(scenario, DecisionScenario) else DecisionScenario(scenario)
    )
    requested = _coerce_stage(max_stage) if max_stage is not None else BimStage.R04
    if selected_mode is ExecutionMode.CONCEPT_ONLY and not stage_at_or_before(
        requested, CONCEPT_ONLY_MAX_STAGE
    ):
        raise SolutionCompilerError(
            "CONCEPT_ONLY permits stages through R04 only; requested stage is "
            f"{requested.name} (R05 and later are refused)"
        )
    if requested is BimStage.R00:
        return []
    if revit_build is None:
        builds = {entry.revit_build for entry in registry.entries if entry.revit_build}
        if len(builds) != 1:
            raise SolutionCompilerError("revit_build must be supplied when registry builds differ")
        revit_build = next(iter(builds))
    if tool_schema_hash is None:
        schemas = {
            entry.tool_schema_hash
            for entry in registry.entries
            if entry.tool_schema_hash
        }
        if len(schemas) != 1:
            raise SolutionCompilerError(
                "tool_schema_hash must be supplied when registry schemas differ"
            )
        tool_schema_hash = next(iter(schemas))

    site = _site_from_solution(solution)
    plans: list[Any] = []
    if stage_at_or_before(BimStage.R01, requested):
        plans.append(
            plan_project_initialization(
                _request(
                    solution,
                    site,
                    registry=registry,
                    stage=BimStage.R01,
                    mode=selected_mode,
                    scenario=selected_scenario,
                    revit_build=revit_build,
                    tool_schema_hash=tool_schema_hash,
                    fixture=fixture,
                    evidence_scope=evidence_scope,
                ),
                amanda_template=amanda_template,
                amanda_template_tested=amanda_template_tested,
                template_roots=template_roots,
                project_code=project_code,
            )
        )
    if stage_at_or_before(BimStage.R02, requested):
        plans.append(
            plan_site_stage(
                _request(
                    solution,
                    site,
                    registry=registry,
                    stage=BimStage.R02,
                    mode=selected_mode,
                    scenario=selected_scenario,
                    revit_build=revit_build,
                    tool_schema_hash=tool_schema_hash,
                    fixture=fixture,
                    evidence_scope=evidence_scope,
                ),
            )
        )
    if stage_at_or_before(BimStage.R03, requested):
        level, grid, reference = _level_and_grid(site)
        plans.append(
            plan_levels_stage(
                _request(
                    solution,
                    site,
                    registry=registry,
                    stage=BimStage.R03,
                    mode=selected_mode,
                    scenario=selected_scenario,
                    revit_build=revit_build,
                    tool_schema_hash=tool_schema_hash,
                    fixture=fixture,
                    evidence_scope=evidence_scope,
                ),
                levels=[level],
                grids=[grid],
                references=[reference],
            )
        )
    if stage_at_or_before(BimStage.R04, requested):
        plans.append(
            plan_massing_stage(
                _request(
                    solution,
                    site,
                    registry=registry,
                    stage=BimStage.R04,
                    mode=selected_mode,
                    scenario=selected_scenario,
                    revit_build=revit_build,
                    tool_schema_hash=tool_schema_hash,
                    fixture=fixture,
                    evidence_scope=evidence_scope,
                ),
                blocks=_massing_blocks(solution),
                site_boundary=site.boundary,
            )
        )

    enriched = [_with_identity(plan, solution) for plan in plans]
    if enriched and any(plan.stage is BimStage.R04 for plan in enriched):
        r04 = next(plan for plan in enriched if plan.stage is BimStage.R04)
        r04.notes.append(
            "PROVISIONAL_ASSUMPTION: height_m=3.2 m; solution.json provides no block height"
        )
    if enriched and any(plan.stage is BimStage.R03 for plan in enriched):
        r03 = next(plan for plan in enriched if plan.stage is BimStage.R03)
        r03.notes.append(
            "PROVISIONAL_ASSUMPTION: LEVEL-01 elevation_m=0.0 uses the local project origin; "
            "no surveyed elevation is claimed"
        )
    return enriched


compile_solution_file = compile_solution


__all__ = [
    "PROVISIONAL_HEIGHT_M",
    "SolutionCompilerError",
    "compile_solution",
    "compile_solution_file",
]
