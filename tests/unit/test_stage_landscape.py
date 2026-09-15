"""Behavioural tests for the R11 landscape stage (P05-T19)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import ExecutionMode, PreflightRequest
from amanda_agent.bim.stages.landscape import (
    DEFAULT_LANDSCAPE_PROGRAM,
    execute_landscape_stage,
    plan_landscape_stage,
    verify_landscape_stage,
)
from amanda_agent.models.capability import (
    CapabilityRegistry,
    EvidenceScope,
    ProviderCapability,
)
from amanda_agent.requirements.decisions import DecisionScenario

CAPABILITY = "revit.create_landscape_element"


class RecordingInvoker:
    def __init__(self) -> None:
        self.calls = []

    def invoke(self, call):
        self.calls.append(call)
        return {"reported_success": True, "unique_id": f"uid-{call.logical_id}"}


def _request(root: Path) -> PreflightRequest:
    evidence = root / "landscape-evidence.json"
    evidence.write_text("synthetic landscape provider evidence", encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    return PreflightRequest(
        mode=ExecutionMode.SYNTHETIC_LAB,
        stage=BimStage.R11,
        scenario=DecisionScenario.STUDY,
        registry=CapabilityRegistry(
            entries=[
                ProviderCapability(
                    provider="fixture",
                    status="PASS",
                    priority=1,
                    provider_commit="c" * 40,
                    transport_provider="fixture",
                    tool_schema_hash="schema-1",
                    tested_scope={"operation": CAPABILITY, "writes": True},
                    evidence_scope=EvidenceScope.SYNTHETIC,
                    revit_build="2027",
                    save_reopen=True,
                    independent_query=True,
                    evidence=[f"{evidence}::sha256={digest}"],
                )
            ]
        ),
        revit_build="2027",
        tool_schema_hash="schema-1",
        expected_build="2027",
        expected_tool_schema_hash="schema-1",
        fixture=True,
        evidence_scope=EvidenceScope.SYNTHETIC,
        generation_run="run-01",
    )


def test_default_external_program_sums_to_260_square_metres(tmp_path: Path):
    plan = plan_landscape_stage(_request(tmp_path), spaces=DEFAULT_LANDSCAPE_PROGRAM)

    assert plan.programmed_area_m2 == pytest.approx(260.0)
    assert [space.target_area_m2 for space in DEFAULT_LANDSCAPE_PROGRAM] == [
        80,
        80,
        30,
        30,
        40,
    ]
    assert {
        element.properties["landscape_kind"] for element in plan.desired_state.elements
    } >= {
        "external_zone",
        "external_floor",
        "vegetation",
        "outdoor_furniture",
        "shading",
    }


def test_landscape_keeps_privacy_and_adjacency_as_explicit_properties(tmp_path: Path):
    plan = plan_landscape_stage(_request(tmp_path), spaces=DEFAULT_LANDSCAPE_PROGRAM)

    zones = [
        element
        for element in plan.desired_state.elements
        if element.category == "landscape_zone"
    ]
    assert len(zones) == 5
    assert all(element.properties["privacy"] for element in zones)
    assert all(element.properties["adjacent_to"] for element in zones)


def test_unapproved_west_privacy_strategy_is_refused(tmp_path: Path):
    with pytest.raises(ValueError, match="approved"):
        plan_landscape_stage(
            _request(tmp_path),
            spaces=DEFAULT_LANDSCAPE_PROGRAM,
            include_west_privacy_strategy=True,
            approved_design_option=False,
        )


def test_landscape_write_is_dispatched_and_requeried(tmp_path: Path):
    plan = plan_landscape_stage(_request(tmp_path), spaces=DEFAULT_LANDSCAPE_PROGRAM)
    invoker = RecordingInvoker()

    records = execute_landscape_stage(plan, invoker=invoker)

    assert len(records) == len(plan.operations)
    assert all(call.stage is BimStage.R11 for call in invoker.calls)
    query = {
        element.logical_id: {
            "unique_id": f"uid-{element.logical_id}",
            "geometry": element.geometry,
            "properties": element.properties,
        }
        for element in plan.desired_state.elements
    }
    assert all(
        result.passed for result in verify_landscape_stage(plan, query_result=query)
    )


def test_landscape_can_include_external_artifacts_from_injected_planner(tmp_path: Path):
    def fake_external_planner():
        return [
            {
                "logical_id": "EXT-TOPO-01",
                "category": "linked_toposolid",
                "geometry": {"reference": "toposolid"},
                "properties": {"source": "fake"},
                "requirement_id": "EXT-TOPO",
                "design_option": "COURTYARD",
                "generation_run": "run-01",
            }
        ]

    plan = plan_landscape_stage(
        _request(tmp_path),
        spaces=DEFAULT_LANDSCAPE_PROGRAM,
        external_planner=fake_external_planner,
    )

    assert "EXT-TOPO-01" in plan.desired_state.by_logical_id()
