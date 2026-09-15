"""Behavioural tests for the R02 site stage (P05-T10).

The stage never claims a surveyed elevation that the source does not prove,
and the Toposolid request is gated by a selectable capability for the exact
build. Providers arrive through the injected ``StageToolInvoker`` double.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import (
    CheckStatus,
    ExecutionMode,
    EvidenceScope,
    MissingCapabilityError,
    PreflightRequest,
    StageError,
    StagePreflightError,
    require_capability,
    run_preflight,
    stage_checkpoint_label,
)
from amanda_agent.bim.stages.site import (
    execute_site_stage,
    plan_site_stage,
    verify_site_stage,
)
from amanda_agent.models.capability import CapabilityRegistry, ProviderCapability
from amanda_agent.requirements.decisions import DecisionScenario
from amanda_agent.site.models import (
    BoundaryKind,
    BoundaryPolygon,
    HypotheticalElevationPoint,
    ScenarioElevationOverride,
    SiteModel,
    SourceReference,
    SourceTopographyState,
    SurveyedElevationPoint,
    Topography,
    TopographyRepresentation,
)

TOPOSOLID_CAPABILITY = "revit.create_toposolid"


class RecordingInvoker:
    """Offline double: records calls and never touches Revit."""

    def __init__(self, *, reported_success: bool = True, unique_id: str = "uid-topo") -> None:
        self.calls: list = []
        self._reported_success = reported_success
        self._unique_id = unique_id

    def invoke(self, call):
        self.calls.append(call)
        return {"reported_success": self._reported_success, "unique_id": self._unique_id}


def _evidence_ref(root: Path, name: str, content: str) -> str:
    path = root / name
    path.write_text(content, encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{path}::sha256={digest}"


def _capability(root: Path, *, operation: str = TOPOSOLID_CAPABILITY, **overrides):
    values = {
        "provider": "horizun",
        "status": "PASS",
        "priority": 1,
        "provider_commit": "a" * 40,
        "transport_provider": "mcp",
        "tool_schema_hash": "hash-1",
        "tested_scope": {"operation": operation, "writes": True},
        "evidence_scope": "PROVIDER",
        "revit_build": "2027",
        "save_reopen": True,
        "independent_query": True,
        "evidence": [_evidence_ref(root, operation + ".evidence.json", operation)],
    }
    values.update(overrides)
    return ProviderCapability(**values)


def _registry(root: Path, *entries: ProviderCapability) -> CapabilityRegistry:
    if not entries:
        entries = (_capability(root),)
    return CapabilityRegistry(entries=list(entries))


def _boundary() -> BoundaryPolygon:
    return BoundaryPolygon(
        coordinates=[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)],
        kind=BoundaryKind.STUDY_PLACEHOLDER,
        placeholder_area_m2=100.0,
    )


def _planar_site(*, with_slope_scenario: bool = False) -> SiteModel:
    overrides = []
    if with_slope_scenario:
        overrides.append(
            ScenarioElevationOverride(
                scenario_id="slope-study",
                version=1,
                elevations=[
                    HypotheticalElevationPoint(x=0.0, y=0.0, elevation_m=-1.5),
                    HypotheticalElevationPoint(x=10.0, y=0.0, elevation_m=2.5),
                    HypotheticalElevationPoint(x=10.0, y=10.0, elevation_m=3.5),
                ],
                affected_checks=["final_grading"],
                rationale="Study-only slope reading from a schematic drawing.",
            )
        )
    return SiteModel(boundary=_boundary(), scenario_overrides=overrides)


def _verified_site() -> SiteModel:
    reference = SourceReference(
        source_id="SRC-TOPO-001", locator="page=1", sha256="b" * 64
    )
    points = [(0.0, 0.0, 1.0), (10.0, 0.0, 2.0), (10.0, 10.0, 3.0), (0.0, 10.0, 1.5)]
    return SiteModel(
        boundary=_boundary(),
        topography=Topography(
            source_state=SourceTopographyState.VERIFIED_TOPOGRAPHY,
            representation=TopographyRepresentation.VERIFIED_TOPOGRAPHY,
            elevation_points=[
                SurveyedElevationPoint(coordinate=point, source_ref=reference)
                for point in points
            ],
            provenance=[reference],
        ),
    )


def _request(root: Path, site: SiteModel, **overrides) -> PreflightRequest:
    values = {
        "mode": ExecutionMode.CONCEPT_ONLY,
        "stage": BimStage.R02,
        "scenario": DecisionScenario.STUDY,
        "registry": _registry(root),
        "revit_build": "2027",
        "tool_schema_hash": "hash-1",
        "expected_build": "2027",
        "expected_tool_schema_hash": "hash-1",
        "selected_inputs": {},
        "expected_inputs": {},
        "required_operations": (),
        "solution": None,
        "site": site,
        "generation_run": "run-01",
    }
    values.update(overrides)
    return PreflightRequest(**values)


def test_planar_placeholder_claims_no_surveyed_z(tmp_path: Path):
    plan = plan_site_stage(_request(tmp_path, _planar_site()))

    assert plan.stage is BimStage.R02
    assert plan.representation is TopographyRepresentation.PLANAR_PLACEHOLDER
    assert plan.source_state is SourceTopographyState.MISSING
    assert plan.surveyed_points == []
    assert plan.toposolid is None
    assert plan.operations == []
    assert plan.final_claim_allowed is False
    assert plan.blockers

    placeholder = plan.placeholder
    assert placeholder is not None
    assert placeholder.z_m == 0.0
    assert placeholder.reference_kind == "SYNTHETIC_DESIGN_REFERENCE"
    assert placeholder.is_surveyed is False
    assert placeholder.boundary[0] == placeholder.boundary[-1]


def test_hypothetical_slope_stays_a_provisional_study_scenario(tmp_path: Path):
    plan = plan_site_stage(_request(tmp_path, _planar_site(with_slope_scenario=True)))

    assert plan.source_state is SourceTopographyState.MISSING
    assert plan.surveyed_points == []
    assert plan.toposolid is None
    scenario = plan.study_scenario
    assert scenario is not None
    assert scenario.assumption == "PROVISIONAL_ASSUMPTION"
    assert scenario.scenario_id == "slope-study"
    assert len(scenario.elevations) == 3
    assert any("MISSING" in note for note in plan.notes)


def test_verified_point_set_creates_the_toposolid_operation(tmp_path: Path):
    plan = plan_site_stage(_request(tmp_path, _verified_site()))

    assert plan.representation is TopographyRepresentation.VERIFIED_TOPOGRAPHY
    assert plan.source_state is SourceTopographyState.VERIFIED_TOPOGRAPHY
    assert plan.surveyed_points == [
        (0.0, 0.0, 1.0),
        (10.0, 0.0, 2.0),
        (10.0, 10.0, 3.0),
        (0.0, 10.0, 1.5),
    ]
    assert plan.placeholder is None
    assert plan.toposolid is not None
    assert len(plan.operations) == 1
    operation = plan.operations[0]
    assert operation.semantic_capability == TOPOSOLID_CAPABILITY
    assert operation.preferred_provider == "horizun"
    assert operation.payload["point_count"] == 4
    assert plan.toposolid.extent.min_z == 1.0
    assert plan.toposolid.extent.max_z == 3.0
    assert plan.final_claim_allowed is True


def test_verified_point_set_without_a_pass_provider_is_refused(tmp_path: Path):
    untested = _registry(
        tmp_path,
        _capability(
            tmp_path,
            status="UNTESTED",
            save_reopen=False,
            independent_query=False,
            evidence=[],
            evidence_scope="SYNTHETIC",
        ),
    )

    with pytest.raises(StagePreflightError, match=TOPOSOLID_CAPABILITY):
        plan_site_stage(_request(tmp_path, _verified_site(), registry=untested))


def test_require_capability_refuses_an_untested_provider(tmp_path: Path):
    untested = _registry(
        tmp_path,
        _capability(tmp_path, status="UNTESTED", evidence=[], evidence_scope="SYNTHETIC"),
    )

    with pytest.raises(MissingCapabilityError, match=TOPOSOLID_CAPABILITY):
        require_capability(
            untested,
            TOPOSOLID_CAPABILITY,
            revit_build="2027",
            tool_schema_hash="hash-1",
            scope=EvidenceScope.PRODUCTION,
        )


def test_site_stage_requires_a_site_model(tmp_path: Path):
    with pytest.raises(StageError, match="requires a site model"):
        plan_site_stage(_request(tmp_path, None))


def test_planar_site_cannot_certify_a_final_claim(tmp_path: Path):
    report = run_preflight(
        _request(tmp_path, _planar_site(), scenario=DecisionScenario.FINAL)
    )

    assert report.ok is False
    assert report.get("site_profile").status is CheckStatus.FAIL


def test_toposolid_write_is_dispatched_through_the_injected_adapter(tmp_path: Path):
    plan = plan_site_stage(_request(tmp_path, _verified_site()))
    invoker = RecordingInvoker()

    records = execute_site_stage(plan, invoker=invoker)

    assert len(invoker.calls) == 1
    call = invoker.calls[0]
    assert call.stage is BimStage.R02
    assert call.semantic_capability == TOPOSOLID_CAPABILITY
    assert call.provider == "horizun"
    assert call.payload["point_count"] == 4
    assert records[0].reported_success is True


def test_extent_verification_detects_a_divergent_model(tmp_path: Path):
    plan = plan_site_stage(_request(tmp_path, _verified_site()))
    extent = plan.toposolid.extent.as_geometry()

    matching = {
        "logical_id": plan.toposolid.operation.logical_id,
        "unique_id": "uid-topo",
        "geometry": extent,
    }
    results = verify_site_stage(plan, tool_reported_success=True, query_result=matching)
    assert results and all(result.passed for result in results)

    diverged = dict(matching, geometry=dict(extent, max_z=9.0))
    failed = verify_site_stage(plan, tool_reported_success=True, query_result=diverged)
    assert any(not result.passed for result in failed)


def test_site_checkpoint_label_is_r02_site(tmp_path: Path):
    plan = plan_site_stage(_request(tmp_path, _planar_site()))

    assert plan.checkpoint_label == stage_checkpoint_label(BimStage.R02)
    assert plan.checkpoint_label == "R02_SITE"
