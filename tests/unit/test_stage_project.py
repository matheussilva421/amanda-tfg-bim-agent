"""Behavioural tests for the R01 project-initialization stage (P05-T09).

No test imports a Revit bridge. Providers are reached only through the
injected ``StageToolInvoker``; ``RecordingInvoker`` below records every call.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import (
    CheckStatus,
    ExecutionMode,
    PreflightRequest,
    StageError,
    StagePreflightError,
    create_stage_checkpoint,
    run_preflight,
    stage_checkpoint_label,
)
from amanda_agent.bim.stages.project import (
    TemplateOrigin,
    build_project_metadata,
    discover_architectural_templates,
    execute_project_initialization,
    plan_project_initialization,
    select_project_template,
    verify_project_initialization,
)
from amanda_agent.design.models import DesignSolution, DesignStatus, MetricSet
from amanda_agent.models.capability import CapabilityRegistry, ProviderCapability
from amanda_agent.requirements.decisions import (
    DecisionRecord,
    DecisionScenario,
    ReviewStatus,
    SelectionAuthority,
    ValidationStatus,
    compute_approval_hash,
)

INPUT_VERSIONS = {
    "requirements_version": "requirements-v1",
    "site_version": "site-v1",
    "engine_version": "design-engine-v1",
}


class RecordingInvoker:
    """Offline double: records calls and never touches Revit."""

    def __init__(self, *, reported_success: bool = True, unique_id: str = "uid-1") -> None:
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


def _capability(root: Path, *, operation: str = "revit.create_project", **overrides):
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


def _registry(root: Path, *operations: str) -> CapabilityRegistry:
    selected = operations or ("revit.create_project",)
    return CapabilityRegistry(entries=[_capability(root, operation=name) for name in selected])


def _decision(solution_id: str = "sol-01", **overrides) -> DecisionRecord:
    selected = f"{solution_id}:COURTYARD"
    rationale = "Synthetic delegated design candidate"
    refs = ["requirements-v1", "site-v1"]
    affected = [solution_id, "program-person-capacity=20"]
    values = {
        "decision_id": "decision-01",
        "topic": "design-selection",
        "alternatives": ["COURTYARD", "LINEAR_SPINE"],
        "selected_option": selected,
        "rationale": rationale,
        "source_refs": refs,
        "confidence": 0.9,
        "affected_requirements": affected,
        "selection_authority": SelectionAuthority.AGENT_DELEGATED,
        "timestamp": "2026-09-15T00:00:00Z",
        "approval_hash": compute_approval_hash(
            selected_option=selected,
            rationale=rationale,
            source_refs=refs,
            affected_requirements=affected,
        ),
        "validation_status": ValidationStatus.VERIFIED,
        "revision_procedure": "Create a new decision revision",
        "review_status": ReviewStatus.AMANDA_REVIEW_PENDING,
    }
    values.update(overrides)
    return DecisionRecord(**values)


def _solution(**overrides) -> DesignSolution:
    values = {
        "solution_id": "sol-01",
        "run_id": "run-01",
        "seed": 42,
        "requirements_version": "requirements-v1",
        "site_version": "site-v1",
        "engine_version": "design-engine-v1",
        "archetype": "COURTYARD",
        "geometry": {"sectors": [], "rooms": []},
        "metrics": MetricSet(program_compliance=1.0, privacy_security=0.8),
        "hard_violations": [],
        "soft_penalties": {"adjacency": 1.5},
        "parents": [],
        "status": DesignStatus.APPROVED_FOR_BIM,
        "selection_authority": SelectionAuthority.AGENT_DELEGATED,
        "decision_evidence": _decision(),
    }
    values.update(overrides)
    return DesignSolution(**values)


def _request(root: Path, **overrides) -> PreflightRequest:
    values = {
        "mode": ExecutionMode.DETAILED_BIM,
        "stage": BimStage.R01,
        "scenario": DecisionScenario.STUDY,
        "registry": _registry(root),
        "revit_build": "2027",
        "tool_schema_hash": "hash-1",
        "expected_build": "2027",
        "expected_tool_schema_hash": "hash-1",
        "selected_inputs": dict(INPUT_VERSIONS),
        "expected_inputs": dict(INPUT_VERSIONS),
        "required_operations": ("revit.create_project",),
        "solution": _solution(),
        "generation_run": "run-01",
    }
    values.update(overrides)
    return PreflightRequest(**values)


def _template_roots(tmp_path: Path) -> list[Path]:
    root = tmp_path / "revit-templates"
    root.mkdir(parents=True, exist_ok=True)
    (root / "Revit 2027 - Default Architectural Template.rte").write_text(
        "architectural template", encoding="utf-8"
    )
    (root / "Revit 2027 - Default Metric.rte").write_text("generic template", encoding="utf-8")
    return [root]


def _plan(tmp_path: Path, request: PreflightRequest, **overrides):
    values = {
        "template_roots": _template_roots(tmp_path),
        "amanda_template": None,
        "amanda_template_tested": False,
        "project_code": "AMANDA",
    }
    values.update(overrides)
    return plan_project_initialization(request, **values)


def test_concept_only_is_limited_to_r04(tmp_path: Path):
    allowed = run_preflight(
        _request(tmp_path, mode=ExecutionMode.CONCEPT_ONLY, stage=BimStage.R04)
    )
    refused = run_preflight(
        _request(tmp_path, mode=ExecutionMode.CONCEPT_ONLY, stage=BimStage.R05)
    )

    assert allowed.ok is True
    assert refused.ok is False
    window = refused.get("mode_stage_window")
    assert window is not None and window.status is CheckStatus.FAIL
    assert "R04" in window.detail

    with pytest.raises(StagePreflightError, match="mode_stage_window"):
        _plan(
            tmp_path,
            _request(
                tmp_path,
                mode=ExecutionMode.CONCEPT_ONLY,
                stage=BimStage.R05,
                solution=None,
            ),
        )


def test_synthetic_lab_requires_a_fixture_target(tmp_path: Path):
    real = run_preflight(
        _request(tmp_path, mode=ExecutionMode.SYNTHETIC_LAB, solution=None, fixture=False)
    )
    fixture = run_preflight(
        _request(tmp_path, mode=ExecutionMode.SYNTHETIC_LAB, solution=None, fixture=True)
    )

    assert real.ok is False
    assert real.get("fixture_scope").status is CheckStatus.FAIL
    assert fixture.ok is True


def test_detailed_bim_requires_a_delegated_content_bound_selection(tmp_path: Path):
    approved = run_preflight(_request(tmp_path))
    missing = run_preflight(_request(tmp_path, solution=None))

    assert approved.ok is True
    assert approved.get("selection_record").status is CheckStatus.PASS
    assert missing.ok is False
    assert missing.get("selection_record").status is CheckStatus.FAIL

    with pytest.raises(StagePreflightError, match="selection_record"):
        _plan(tmp_path, _request(tmp_path, solution=None))


def test_amanda_review_pending_does_not_block_the_detailed_stage(tmp_path: Path):
    report = run_preflight(
        _request(tmp_path, solution=_solution(status=DesignStatus.AMANDA_REVIEW_PENDING))
    )

    assert report.ok is True
    assert any("AMANDA_REVIEW_PENDING" in note for note in report.notes)


def test_approval_hash_must_match_the_hash_the_run_was_authorized_for(tmp_path: Path):
    solution = _solution()
    authorized = run_preflight(
        _request(tmp_path, expected_approval_hash=solution.approval_hash)
    )
    stale_run = run_preflight(_request(tmp_path, expected_approval_hash="0" * 64))

    assert authorized.ok is True
    assert authorized.get("approval_hash").status is CheckStatus.PASS
    assert stale_run.ok is False
    assert stale_run.get("approval_hash").status is CheckStatus.FAIL

    with pytest.raises(StagePreflightError, match="approval_hash"):
        _plan(tmp_path, _request(tmp_path, expected_approval_hash="0" * 64))


def test_a_candidate_without_execution_authority_is_not_eligible(tmp_path: Path):
    candidate = DesignSolution(
        solution_id="sol-01",
        run_id="run-01",
        seed=42,
        requirements_version="requirements-v1",
        site_version="site-v1",
        engine_version="design-engine-v1",
        archetype="COURTYARD",
        geometry={"sectors": [], "rooms": []},
        metrics=MetricSet(),
        hard_violations=[],
        soft_penalties={},
        parents=[],
        status=DesignStatus.CANDIDATE,
    )
    report = run_preflight(_request(tmp_path, solution=candidate))

    assert report.ok is False
    assert report.get("selection_record").status is CheckStatus.FAIL
    assert "CANDIDATE" in report.get("selection_record").detail


def test_selected_input_versions_must_match_expected_and_the_solution(tmp_path: Path):
    stale_selection = dict(INPUT_VERSIONS, site_version="site-v2")
    report = run_preflight(_request(tmp_path, selected_inputs=stale_selection))

    assert report.ok is False
    assert report.get("input_versions").status is CheckStatus.FAIL
    assert "site_version" in report.get("input_versions").detail


def test_registry_must_prove_the_exact_build_and_schema(tmp_path: Path):
    wrong_build = _registry(tmp_path)
    wrong_build.entries[0] = _capability(tmp_path, revit_build="2026")
    report = run_preflight(_request(tmp_path, registry=wrong_build))

    assert report.ok is False
    assert report.get("capability_registry").status is CheckStatus.FAIL
    assert "2026" in report.get("capability_registry").detail

    stale_pin = run_preflight(_request(tmp_path, expected_build="2026"))
    assert stale_pin.ok is False
    assert stale_pin.get("revit_build").status is CheckStatus.FAIL


def test_unverified_study_input_cannot_certify_final(tmp_path: Path):
    from amanda_agent.site.models import BoundaryKind, BoundaryPolygon, SiteModel

    planar = SiteModel(
        boundary=BoundaryPolygon(
            coordinates=[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)],
            kind=BoundaryKind.STUDY_PLACEHOLDER,
            placeholder_area_m2=100.0,
        )
    )
    study = run_preflight(_request(tmp_path, site=planar))
    final = run_preflight(_request(tmp_path, site=planar, scenario=DecisionScenario.FINAL))

    assert study.ok is True
    assert final.ok is False
    assert final.get("site_profile").status is CheckStatus.FAIL
    assert "FINAL" in final.get("site_profile").detail


def test_amanda_template_is_used_only_after_it_was_tested_on_a_copy(tmp_path: Path):
    supplied = tmp_path / "amanda-template.rte"
    supplied.write_text("amanda template bytes", encoding="utf-8")

    tested = select_project_template(
        amanda_template=supplied, amanda_template_tested=True, roots=None
    )
    assert tested.origin is TemplateOrigin.AMANDA_SUPPLIED
    assert tested.template_path == supplied.resolve()
    assert tested.tested is True
    assert tested.copy_before_use is True
    assert tested.sha256

    untested = select_project_template(
        amanda_template=supplied,
        amanda_template_tested=False,
        roots=_template_roots(tmp_path),
    )
    assert untested.origin is TemplateOrigin.INSTALLED_ARCHITECTURAL
    assert any("not tested" in note for note in untested.notes)


def test_installed_architectural_template_is_discovered_deterministically(tmp_path: Path):
    roots = _template_roots(tmp_path)
    discovered = discover_architectural_templates(roots)

    assert [path.name for path in discovered] == [
        "Revit 2027 - Default Architectural Template.rte"
    ]

    first = select_project_template(
        amanda_template=None, amanda_template_tested=False, roots=roots
    )
    second = select_project_template(
        amanda_template=None, amanda_template_tested=False, roots=roots
    )
    assert first.template_path == second.template_path
    assert first.origin is TemplateOrigin.INSTALLED_ARCHITECTURAL

    with pytest.raises(StageError, match="installed architectural template"):
        select_project_template(
            amanda_template=None, amanda_template_tested=False, roots=[tmp_path / "empty"]
        )


def test_project_metadata_and_naming_are_deterministic():
    first = build_project_metadata(
        project_code="amanda",
        solution_id="sol-01",
        generation_run="run-01",
        requirements_version="requirements-v1",
        site_version="site-v1",
    )
    second = build_project_metadata(
        project_code="amanda",
        solution_id="sol-01",
        generation_run="run-01",
        requirements_version="requirements-v1",
        site_version="site-v1",
    )
    other = build_project_metadata(
        project_code="amanda2",
        solution_id="sol-01",
        generation_run="run-01",
        requirements_version="requirements-v1",
        site_version="site-v1",
    )

    assert first == second
    assert first.project_number == "AMANDA"
    assert first.view_prefix == "AMANDA-V"
    assert first.sheet_prefix == "AMANDA-S"
    assert first.family_prefix == "AMANDA-FAM"
    assert first.material_prefix == "AMANDA-MAT"
    assert first.room_number_scheme == "AMANDA-{sector}-{index:03d}"
    assert other.project_number == "AMANDA2"
    assert other.view_prefix != first.view_prefix


def test_checkpoint_label_is_r01_project_initialized(tmp_path: Path):
    plan = _plan(tmp_path, _request(tmp_path))
    assert plan.checkpoint_label == stage_checkpoint_label(BimStage.R01)
    assert plan.checkpoint_label == "R01_PROJECT_INITIALIZED"

    source = tmp_path / "working.rvt"
    source.write_bytes(b"working model")
    manifest = create_stage_checkpoint(
        source_path=source,
        checkpoint_path=tmp_path / "checkpoints" / "r01.rvt",
        stage=BimStage.R01,
    )

    assert manifest.stage == "R01_PROJECT_INITIALIZED"
    assert manifest.verify() is True


def test_operations_are_dispatched_through_the_injected_adapter(tmp_path: Path):
    plan = _plan(tmp_path, _request(tmp_path))
    invoker = RecordingInvoker()

    records = execute_project_initialization(plan, invoker=invoker)

    assert len(invoker.calls) == 1
    call = invoker.calls[0]
    assert call.stage is BimStage.R01
    assert call.semantic_capability == "revit.create_project"
    assert call.provider == "horizun"
    assert call.payload["project_number"] == "AMANDA"
    assert call.payload["template_origin"] == TemplateOrigin.INSTALLED_ARCHITECTURAL.value
    assert records[0].reported_success is True
    assert records[0].logical_id == "PRJ-0001"


def test_project_write_requires_independent_read_and_verifies_naming(tmp_path: Path):
    plan = _plan(tmp_path, _request(tmp_path))

    results = verify_project_initialization(
        plan,
        tool_reported_success=True,
        query_result={
            "logical_id": "PRJ-0001",
            "unique_id": "uid-project",
            "properties": {
                "project_name": plan.metadata.project_name,
                "project_number": plan.metadata.project_number,
                "view_prefix": plan.metadata.view_prefix,
                "sheet_prefix": plan.metadata.sheet_prefix,
                "room_number_scheme": plan.metadata.room_number_scheme,
                "family_prefix": plan.metadata.family_prefix,
                "material_prefix": plan.metadata.material_prefix,
                "stage_prefix": plan.metadata.stage_prefix,
            },
        },
    )

    assert results and all(result.passed for result in results)
