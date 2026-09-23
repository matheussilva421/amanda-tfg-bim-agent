"""R02 site stage: planar placeholder or verified topography.

``PLANAR_PLACEHOLDER`` is a synthetic design reference. It emits no surveyed
elevation point, and a hypothesised slope lives only in a marked study
scenario. ``VERIFIED_TOPOGRAPHY`` may request Toposolid/grading, and only when
the capability registry proves that operation for the exact build.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from amanda_agent.site.models import (
    Coordinate2D,
    Coordinate3D,
    ScenarioOverrideStatus,
    SiteModel,
    SourceTopographyState,
    TopographyRepresentation,
)

from ..models import BimStage, DesiredElement
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
    provider_assignment,
    run_preflight,
    stage_checkpoint_label,
    with_stage_requirements,
)

TOPOSOLID_CAPABILITY = "revit.create_toposolid"
TOPO_LOGICAL_ID = "SITE-TOPO-01"

#: The checks a planar placeholder leaves explicitly blocked.
DEFAULT_TOPOGRAPHY_BLOCKERS = (
    "final_grading",
    "final_altimetric_accessibility",
)


class PlanarReference(BaseModel):
    """A local drawing plane that is never sold as a surveyed elevation."""

    model_config = ConfigDict(extra="forbid")

    boundary: list[Coordinate2D] = Field(min_length=4)
    z_m: float = 0.0
    reference_kind: Literal["SYNTHETIC_DESIGN_REFERENCE"] = "SYNTHETIC_DESIGN_REFERENCE"
    is_surveyed: bool = False
    notes: list[str] = Field(default_factory=list)


class StudyTerrainScenario(BaseModel):
    """A versioned hypothetical terrain kept outside the surveyed point set."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scenario_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    assumption: Literal["PROVISIONAL_ASSUMPTION"] = "PROVISIONAL_ASSUMPTION"
    elevations: list[Coordinate3D] = Field(default_factory=list)
    affected_checks: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)


class SiteExtent(BaseModel):
    """Desired X/Y/Z extents of the site topography."""

    model_config = ConfigDict(extra="forbid")

    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    def as_geometry(self) -> dict[str, Any]:
        return {
            "extent": [
                self.min_x,
                self.min_y,
                self.min_z,
                self.max_x,
                self.max_y,
                self.max_z,
            ]
        }


class ToposolidRequest(BaseModel):
    """The verified-topography request, bound to its desired operation."""

    model_config = ConfigDict(extra="forbid")

    operation: StageOperation
    extent: SiteExtent
    point_count: int = Field(ge=1)
    desired_element: DesiredElement
    source_representation: TopographyRepresentation = (
        TopographyRepresentation.VERIFIED_TOPOGRAPHY
    )


class SiteStagePlan(BaseModel):
    """The read-only R02 plan and the claims it does *not* make."""

    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R02
    preflight: PreflightReport
    representation: TopographyRepresentation
    source_state: SourceTopographyState
    surveyed_points: list[Coordinate3D] = Field(default_factory=list)
    placeholder: PlanarReference | None = None
    study_scenario: StudyTerrainScenario | None = None
    toposolid: ToposolidRequest | None = None
    operations: list[StageOperation] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    checkpoint_label: str = Field(default="R02_SITE", min_length=1)

    @property
    def final_claim_allowed(self) -> bool:
        """Only verified input without a provisional override can carry FINAL."""

        if self.representation is not TopographyRepresentation.VERIFIED_TOPOGRAPHY:
            return False
        if self.source_state is not SourceTopographyState.VERIFIED_TOPOGRAPHY:
            return False
        if self.study_scenario is not None:
            return False
        return self.toposolid is not None


def _study_scenario(site: SiteModel) -> StudyTerrainScenario | None:
    active = [
        override
        for override in site.scenario_overrides
        if override.status is ScenarioOverrideStatus.ACTIVE
    ]
    if not active:
        return None
    latest = max(active, key=lambda override: override.version)
    return StudyTerrainScenario(
        scenario_id=latest.scenario_id,
        version=latest.version,
        elevations=[
            (point.x, point.y, point.elevation_m) for point in latest.elevations
        ],
        affected_checks=list(latest.affected_checks),
        rationale=latest.rationale,
    )


def _extent(points: Sequence[Coordinate3D]) -> SiteExtent:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]
    return SiteExtent(
        min_x=min(xs),
        min_y=min(ys),
        min_z=min(zs),
        max_x=max(xs),
        max_y=max(ys),
        max_z=max(zs),
    )


def _default_toposolid_element(
    footprint: Sequence[Coordinate2D],
    *,
    elevation: float,
    name: str,
    points: Sequence[Coordinate3D],
    generation_run: str,
) -> DesiredElement:
    """Small local fallback used when the external artifact module is absent."""

    return DesiredElement(
        logical_id=name,
        category="Toposolid",
        geometry={
            "footprint": [list(point) for point in footprint],
            "points": [list(point) for point in points],
            "base_elevation_m": elevation,
        },
        properties={
            "name": name,
            "source_representation": TopographyRepresentation.VERIFIED_TOPOGRAPHY.value,
        },
        requirement_id="P05-T10:TOPOGRAPHY",
        design_option="SELECTED_SOLUTION",
        generation_run=generation_run,
    )


def plan_site_stage(
    request: PreflightRequest,
    *,
    blockers: Sequence[str] = DEFAULT_TOPOGRAPHY_BLOCKERS,
    include_study_scenario: bool = True,
    toposolid_planner: Callable[..., DesiredElement] | None = None,
) -> SiteStagePlan:
    """Preflight the mode, then describe the site representation honestly."""

    site = request.site
    if site is None:
        raise StageError("the R02 site stage requires a site model")

    representation = site.topography.representation
    extra = (
        (TOPOSOLID_CAPABILITY,)
        if representation is TopographyRepresentation.VERIFIED_TOPOGRAPHY
        else ()
    )
    effective = with_stage_requirements(request, extra=extra)
    report = run_preflight(effective)
    if not report.ok:
        raise StagePreflightError("R02 preflight refused: " + "; ".join(report.problems))

    source_state = site.topography.source_state
    study_scenario = _study_scenario(site) if include_study_scenario else None
    notes = [
        (
            f"topography source remains {source_state.value}; "
            "no surveyed elevation is claimed by this plan"
        )
    ]

    if representation is TopographyRepresentation.PLANAR_PLACEHOLDER:
        placeholder = PlanarReference(
            boundary=list(site.boundary.coordinates),
            z_m=0.0,
            notes=[
                "z=0 is a local design convention, not a surveyed elevation",
                "no surveyed elevation point is emitted from a planar placeholder",
            ],
        )
        if source_state is SourceTopographyState.VERIFIED_TOPOGRAPHY:
            notes.append(
                "verified source points are not emitted while the representation is planar"
            )
        if study_scenario is not None:
            notes.append(
                "a hypothetical study terrain is carried only as "
                "PROVISIONAL_ASSUMPTION and never as source data"
            )
        return SiteStagePlan(
            preflight=report,
            representation=representation,
            source_state=source_state,
            surveyed_points=[],
            placeholder=placeholder,
            study_scenario=study_scenario,
            toposolid=None,
            operations=[],
            blockers=list(blockers),
            notes=notes,
            checkpoint_label=stage_checkpoint_label(BimStage.R02),
        )

    points: list[Coordinate3D] = [
        (float(point[0]), float(point[1]), float(point[2]))
        for point in (
            elevation.coordinate for elevation in site.topography.elevation_points
        )
    ]
    if not points:
        raise StageError("verified topography requires elevation points")
    extent = _extent(points)
    preferred, rest = provider_assignment(effective, TOPOSOLID_CAPABILITY)
    operation = StageOperation(
        stage=BimStage.R02,
        logical_id=TOPO_LOGICAL_ID,
        semantic_capability=TOPOSOLID_CAPABILITY,
        payload={
            "points": [list(point) for point in points],
            "point_count": len(points),
            "extent": extent.as_geometry()["extent"],
            "source_state": SourceTopographyState.VERIFIED_TOPOGRAPHY.value,
        },
        verification_rules=[
            "independent_requery",
            "extent_within_tolerance",
            "elevations_match_source_points",
        ],
        preferred_provider=preferred,
        fallback_providers=rest,
    )
    planner = toposolid_planner
    if planner is None:
        try:
            from ..external import place_toposolid as external_planner
        except ModuleNotFoundError as exc:
            if exc.name != "amanda_agent.bim.external":
                raise
            external_planner = None
        planner = external_planner or (
            lambda footprint, *, elevation, name: _default_toposolid_element(
                footprint,
                elevation=elevation,
                name=name,
                points=points,
                generation_run=effective.generation_run,
            )
        )
    try:
        desired_element = planner(
            list(site.boundary.coordinates),
            elevation=extent.min_z,
            name=TOPO_LOGICAL_ID,
        )
    except Exception as exc:
        raise StageError(f"Toposolid desired-element planner failed: {exc}") from exc
    if not isinstance(desired_element, DesiredElement):
        raise StageError("Toposolid desired-element planner must return DesiredElement")
    if desired_element.logical_id != TOPO_LOGICAL_ID or desired_element.category != "Toposolid":
        properties = dict(desired_element.properties)
        properties.setdefault("external_logical_id", desired_element.logical_id)
        desired_element = desired_element.model_copy(
            update={
                "logical_id": TOPO_LOGICAL_ID,
                "category": "Toposolid",
                "properties": properties,
            }
        )
    operation.payload["desired_element"] = desired_element.model_dump(mode="json")
    return SiteStagePlan(
        preflight=report,
        representation=representation,
        source_state=source_state,
        surveyed_points=points,
        placeholder=None,
        study_scenario=study_scenario,
        toposolid=ToposolidRequest(
            operation=operation,
            extent=extent,
            point_count=len(points),
            desired_element=desired_element,
        ),
        operations=[operation],
        blockers=list(blockers) if study_scenario is not None else [],
        notes=notes,
        checkpoint_label=stage_checkpoint_label(BimStage.R02),
    )


def verify_site_stage(
    plan: SiteStagePlan,
    *,
    tool_reported_success: bool,
    query_result: Mapping[str, Any] | None,
    tolerance: float = 1e-6,
) -> list[VerificationResult]:
    """Verify the written topography against an independent re-query."""

    if plan.toposolid is None:
        raise StageError("the planar placeholder writes nothing to verify independently")
    return verify_write(
        logical_id=plan.toposolid.operation.logical_id,
        tool_reported_success=tool_reported_success,
        query_result=query_result,
        expected_geometry=plan.toposolid.extent.as_geometry(),
        geometry_tolerance=tolerance,
    )


def execute_site_stage(
    plan: SiteStagePlan,
    *,
    invoker: StageToolInvoker,
) -> list[StageExecutionRecord]:
    """Dispatch the desired site operations through the injected adapter."""

    return dispatch_operations(plan.operations, invoker=invoker)


__all__ = [
    "DEFAULT_TOPOGRAPHY_BLOCKERS",
    "TOPOSOLID_CAPABILITY",
    "TOPO_LOGICAL_ID",
    "PlanarReference",
    "SiteExtent",
    "SiteStagePlan",
    "StudyTerrainScenario",
    "ToposolidRequest",
    "execute_site_stage",
    "plan_site_stage",
    "verify_site_stage",
]
