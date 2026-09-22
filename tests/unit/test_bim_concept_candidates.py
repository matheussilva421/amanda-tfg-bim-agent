"""Offline contract tests for conceptual finalist preparation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from amanda_agent.bim.lab_fixture import BUILD, SCHEMA, build_lab_fixture_registry
from amanda_agent.bim.models import BimStage
from scripts.bim_concept_candidates import (
    CandidatePreparationError,
    prepare_concept_candidate,
    prepare_concept_candidates,
)

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


def _registry(tmp_path: Path):
    return build_lab_fixture_registry(
        root=tmp_path / "registry",
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
    )


def _prepare(tmp_path: Path, **overrides):
    return prepare_concept_candidate(
        SOLUTION_PATH,
        output_root=tmp_path / "candidates",
        registry=_registry(tmp_path),
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
        amanda_template=tmp_path / "Default_M_PTB.rte",
        amanda_template_tested=True,
        **overrides,
    )


def test_prepares_separate_concept_bundle_with_honest_pending_live_evidence(
    tmp_path: Path,
):
    (tmp_path / "Default_M_PTB.rte").write_bytes(b"tested template")

    result = _prepare(tmp_path)

    assert [plan.stage for plan in result.plans] == [
        BimStage.R01,
        BimStage.R02,
        BimStage.R03,
        BimStage.R04,
    ]
    assert result.execution_mode == "CONCEPT_ONLY"
    assert result.live_revit_evidence is False
    assert result.status == "OFFLINE_PLAN_READY"
    assert list(result.rejected_stages) == [
        stage.name for stage in BimStage if stage.value not in {
            "EMPTY_SANDBOX",
            "PROJECT_INITIALIZED",
            "SITE",
            "LEVELS_AND_REFERENCES",
            "MASSING",
        }
    ]
    assert result.writer_lease_acquired is False
    assert result.output_directory == tmp_path / "candidates" / "AMANDA-RUN-001-F01"

    bundle = json.loads((result.output_directory / "candidate-bundle.json").read_text())
    assert bundle["solution_id"] == "AMANDA-RUN-001-F01"
    assert bundle["execution_mode"] == "CONCEPT_ONLY"
    assert bundle["live_revit_evidence"] is False
    assert bundle["metrics_verification"]["status"] == "PASS"
    assert (result.output_directory / "preview.svg").is_file()
    assert (result.output_directory / "metrics-verification.json").is_file()
    assert (result.output_directory / "plans" / "R04.json").is_file()
    assert not (tmp_path / "candidates" / "revit-writer.lock").exists()


def test_concept_preparation_refuses_r05_and_later(tmp_path: Path):
    (tmp_path / "Default_M_PTB.rte").write_bytes(b"tested template")

    with pytest.raises(CandidatePreparationError, match="CONCEPT_ONLY.*R04"):
        _prepare(tmp_path, max_stage=BimStage.R05)


def test_concept_preparation_refuses_existing_candidate_directory(tmp_path: Path):
    (tmp_path / "Default_M_PTB.rte").write_bytes(b"tested template")
    target = tmp_path / "candidates" / "AMANDA-RUN-001-F01"
    target.mkdir(parents=True)

    with pytest.raises(CandidatePreparationError, match="already exists"):
        _prepare(tmp_path)

F02_SOLUTION_PATH = (
    REPOSITORY_ROOT
    / "design-engine"
    / "runs"
    / "AMANDA-RUN-001"
    / "finalists"
    / "AMANDA-RUN-001-F02"
    / "solution.json"
)


def test_batch_prepares_each_finalist_under_a_distinct_directory(tmp_path: Path):

    template = tmp_path / "Default_M_PTB.rte"
    template.write_bytes(b"tested template")
    registry = _registry(tmp_path)

    results = prepare_concept_candidates(
        [SOLUTION_PATH, F02_SOLUTION_PATH],
        output_root=tmp_path / "candidates",
        registry=registry,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
        amanda_template=template,
        amanda_template_tested=True,
    )

    assert [result.solution_id for result in results] == [
        "AMANDA-RUN-001-F01",
        "AMANDA-RUN-001-F02",
    ]
    assert [result.output_directory.name for result in results] == [
        "AMANDA-RUN-001-F01",
        "AMANDA-RUN-001-F02",
    ]
    assert all(result.status == "OFFLINE_PLAN_READY" for result in results)
