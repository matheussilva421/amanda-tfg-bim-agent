"""Behavioral tests for the R04 massing stage."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from shapely.geometry import box

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import (
    ExecutionMode,
    PreflightRequest,
    StagePreflightError,
)
from amanda_agent.bim.stages.massing import (
    MASSING_CAPABILITY,
    MassingBlock,
    execute_massing_stage,
    plan_massing_stage,
    verify_massing_stage,
)
from amanda_agent.models.capability import CapabilityRegistry, ProviderCapability
from amanda_agent.requirements.decisions import DecisionScenario


class RecordingInvoker:
    def __init__(self):
        self.calls = []

    def invoke(self, call):
        self.calls.append(call)
        return {"reported_success": True, "unique_id": "uid-mass-01"}


def _request(root: Path):
    path = root / "massing-evidence.json"
    path.write_text("massing", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    registry = CapabilityRegistry(
        entries=[
            ProviderCapability(
                provider="horizun",
                status="PASS",
                priority=1,
                provider_commit="a" * 40,
                transport_provider="mcp",
                tool_schema_hash="hash-1",
                tested_scope={"operation": MASSING_CAPABILITY, "writes": True},
                evidence_scope="PROVIDER",
                revit_build="2027",
                save_reopen=True,
                independent_query=True,
                evidence=[f"{path}::sha256={digest}"],
            )
        ]
    )
    return PreflightRequest(
        mode=ExecutionMode.CONCEPT_ONLY,
        stage=BimStage.R04,
        scenario=DecisionScenario.STUDY,
        registry=registry,
        revit_build="2027",
        tool_schema_hash="hash-1",
        expected_build="2027",
        expected_tool_schema_hash="hash-1",
        generation_run="run-04",
    )


def _block():
    return MassingBlock(
        logical_id="MASS-01",
        name="Acolhimento",
        footprint=[(0.0, 0.0), (10.0, 0.0), (10.0, 5.0), (0.0, 5.0)],
        base_elevation_m=0.0,
        height_m=3.2,
        rotation_degrees=0.0,
    )


def test_concept_massing_creates_a_metric_surrogate_and_desired_state(tmp_path: Path):
    plan = plan_massing_stage(_request(tmp_path), blocks=[_block()])

    assert plan.stage is BimStage.R04
    assert len(plan.desired_state.elements) == 1
    assert plan.operations[0].semantic_capability == MASSING_CAPABILITY
    assert plan.operations[0].payload["height_m"] == 3.2
    assert plan.operations[0].payload["area_m2"] == 50.0
    assert plan.operations[0].payload["geometry"]["centroid"] == [5.0, 2.5]
    assert plan.operations[0].payload["geometry"]["dimensions_m"] == [10.0, 5.0]


def test_massing_write_verifies_geometry_against_the_block(tmp_path: Path):
    plan = plan_massing_stage(_request(tmp_path), blocks=[_block()])
    invoker = RecordingInvoker()
    execute_massing_stage(plan, invoker=invoker)

    results = verify_massing_stage(
        plan,
        tool_reported_success=True,
        query_results={
            "MASS-01": {
                "logical_id": "MASS-01",
                "unique_id": "uid-mass-01",
                "geometry": plan.operations[0].payload["geometry"],
                "properties": {
                    "name": "Acolhimento",
                    "area_projection_m2": 50.0,
                },
            }
        },
    )
    assert results and all(result.passed for result in results)


def test_overlapping_design_blocks_are_refused(tmp_path: Path):
    second = _block().model_copy(update={"logical_id": "MASS-02"})

    with pytest.raises(StagePreflightError, match="separation"):
        plan_massing_stage(_request(tmp_path), blocks=[_block(), second])


def test_detailed_massing_without_content_bound_selection_is_refused(tmp_path: Path):
    request = _request(tmp_path).model_copy(update={"mode": ExecutionMode.DETAILED_BIM})

    with pytest.raises(StagePreflightError, match="selection_record"):
        plan_massing_stage(request, blocks=[_block()])


def test_design_engine_generated_blocks_are_consumed_without_losing_metric_metadata(
    tmp_path: Path,
):
    from amanda_agent.design.blocks import generate_blocks

    generated = generate_blocks(
        [{"logical_id": "SECTOR-A", "geometry": box(0, 0, 10, 5), "demand_m2": 50.0}]
    )

    plan = plan_massing_stage(
        _request(tmp_path),
        blocks=[{**generated.blocks[0], "height_m": 3.2}],
    )

    assert plan.blocks[0].sector_id == "SECTOR-A"
    assert plan.blocks[0].demand_m2 == 50.0
    assert plan.blocks[0].source_area_m2 == 50.0
