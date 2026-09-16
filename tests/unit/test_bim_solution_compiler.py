"""Unit contract for compiling a finalist solution into the conceptual BIM stages."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from amanda_agent.bim.lab_fixture import BUILD, SCHEMA, build_lab_fixture_registry
from amanda_agent.bim.models import BimStage
from amanda_agent.bim.solution_compiler import (
    SolutionCompilerError,
    compile_solution,
)
from amanda_agent.design.models import compute_design_approval_hash
from amanda_agent.site.models import TopographyRepresentation

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOLUTION_PATH = (
    REPOSITORY_ROOT
    / "design-engine"
    / "runs"
    / "AMANDA-RUN-001"
    / "finalists"
    / "AMANDA-RUN-001-F01"
    / "solution.json"
)


def _compile(tmp_path: Path, solution_path: Path = SOLUTION_PATH, **options):
    tmp_path.mkdir(parents=True, exist_ok=True)
    template = tmp_path / "amanda-template.rte"
    template.write_bytes(b"tested architectural template")
    registry = build_lab_fixture_registry(
        root=tmp_path / "registry",
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
    )
    return compile_solution(
        solution_path,
        registry=registry,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
        amanda_template=template,
        amanda_template_tested=True,
        **options,
    )


def _identity_markers(plan) -> str:
    return json.dumps(plan.model_dump(mode="json"), sort_keys=True)


def test_compiles_real_finalist_into_r01_to_r04_with_honest_provisional_assumption(
    tmp_path: Path,
):
    plans = _compile(tmp_path)

    assert [plan.stage for plan in plans] == [
        BimStage.R01,
        BimStage.R02,
        BimStage.R03,
        BimStage.R04,
    ]

    solution = json.loads(SOLUTION_PATH.read_text(encoding="utf-8"))
    solution_id = solution["solution_id"]
    approval_hash = solution["approval_hash"]

    assert plans[0].metadata.solution_id == solution_id
    assert plans[1].representation is TopographyRepresentation.PLANAR_PLACEHOLDER
    assert plans[1].operations == []
    assert plans[1].blockers
    assert plans[1].surveyed_points == []
    assert plans[1].placeholder is not None
    assert len(plans[2].levels) == 1
    assert plans[2].levels[0].evidence
    assert len(plans[2].grids) == 1
    assert plans[2].references[0].kind == "PROJECT_ORIGIN"
    assert plans[2].references[0].is_provisional is True
    assert any("PROVISIONAL_ASSUMPTION" in note for note in plans[2].notes)

    assert len(plans[3].blocks) == 6
    assert all(block.height_m == 3.2 for block in plans[3].blocks)
    assert {
        block.logical_id: block.source_area_m2 for block in plans[3].blocks
    } == {
        "SEC-01-block-1": 53.00000000000028,
        "SEC-02-block-1": 208.99999999999994,
        "SEC-03-block-1": 51.999999999999936,
        "SEC-04-block-1": 80.00000000000003,
        "SEC-05-block-1": 80.99999999999997,
        "SEC-06-block-1": 150.99999999999997,
    }
    assert all(
        operation.payload["properties"]["source_solution_id"] == solution_id
        for operation in plans[3].operations
    )
    assert any("PROVISIONAL_ASSUMPTION" in note for note in plans[3].notes)

    for plan in plans:
        marker = _identity_markers(plan)
        assert solution_id in marker
        assert approval_hash in marker


def test_solution_identity_changes_the_compiled_plan(tmp_path: Path):
    source = json.loads(SOLUTION_PATH.read_text(encoding="utf-8"))
    source["solution_id"] = "AMANDA-RUN-001-F02"
    source["approval_hash"] = compute_design_approval_hash(source)
    alternate = tmp_path / "alternate-solution.json"
    alternate.write_text(json.dumps(source), encoding="utf-8")

    original_plans = _compile(tmp_path / "original")
    alternate_plans = _compile(tmp_path / "alternate", alternate)

    assert original_plans[0].metadata.solution_id != alternate_plans[0].metadata.solution_id
    assert original_plans[0].operations[0].payload["approval_hash"] != (
        alternate_plans[0].operations[0].payload["approval_hash"]
    )


def test_concept_only_refuses_a_requested_stage_after_r04(tmp_path: Path):
    with pytest.raises(SolutionCompilerError, match="CONCEPT_ONLY.*R04.*R05"):
        _compile(tmp_path, max_stage=BimStage.R05)
