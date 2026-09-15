"""Behavioural tests for the R13 documentation stage (P05-T21)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import ExecutionMode, PreflightRequest
from amanda_agent.bim.stages.documentation import (
    MINIMUM_TABLES,
    execute_documentation_stage,
    plan_documentation_stage,
    verify_documentation_stage,
)
from amanda_agent.models.capability import (
    CapabilityRegistry,
    EvidenceScope,
    ProviderCapability,
)
from amanda_agent.requirements.decisions import DecisionScenario

CAPABILITY = "revit.create_documentation_element"


class RecordingInvoker:
    def __init__(self) -> None:
        self.calls = []

    def invoke(self, call):
        self.calls.append(call)
        return {"reported_success": True, "unique_id": f"uid-{call.logical_id}"}


def _request(root: Path) -> PreflightRequest:
    evidence = root / "documentation-evidence.json"
    evidence.write_text("synthetic documentation provider evidence", encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    return PreflightRequest(
        mode=ExecutionMode.SYNTHETIC_LAB,
        stage=BimStage.R13,
        scenario=DecisionScenario.STUDY,
        registry=CapabilityRegistry(
            entries=[
                ProviderCapability(
                    provider="fixture",
                    status="PASS",
                    priority=1,
                    provider_commit="e" * 40,
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


def test_documentation_contains_deterministic_views_tables_sheets_and_annotations(
    tmp_path: Path,
):
    plan = plan_documentation_stage(_request(tmp_path))
    categories = {element.category for element in plan.desired_state.elements}

    assert {"view", "table", "sheet", "viewport", "dimension", "tag"} <= categories
    assert plan.table_names == MINIMUM_TABLES
    assert "PLAN_SITE" in plan.view_names
    assert "PLAN_ROOF" in plan.view_names
    assert {
        "SECTION_COURTYARD",
        "SECTION_RESIDENTIAL",
        "SECTION_TRANSITIONS",
        "SECTION_ACCESS",
    } <= set(plan.view_names)


def test_documentation_plan_is_repeatable(tmp_path: Path):
    first = plan_documentation_stage(_request(tmp_path))
    second = plan_documentation_stage(_request(tmp_path))

    assert first.desired_state.model_dump(
        mode="json"
    ) == second.desired_state.model_dump(mode="json")
    assert first.sheet_registry == second.sheet_registry


def test_documentation_write_is_dispatched_and_requeried(tmp_path: Path):
    plan = plan_documentation_stage(_request(tmp_path))
    invoker = RecordingInvoker()

    records = execute_documentation_stage(plan, invoker=invoker)

    assert len(records) == len(plan.operations)
    assert all(call.stage is BimStage.R13 for call in invoker.calls)
    query = {
        element.logical_id: {
            "unique_id": f"uid-{element.logical_id}",
            "geometry": element.geometry,
            "properties": element.properties,
        }
        for element in plan.desired_state.elements
    }
    assert all(
        result.passed for result in verify_documentation_stage(plan, query_result=query)
    )
