"""Behavioural tests for the R10 furniture stage (P05-T18)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import ExecutionMode, PreflightRequest
from amanda_agent.bim.stages.furniture import (
    execute_furniture_stage,
    plan_furniture_stage,
    verify_furniture_stage,
)
from amanda_agent.models.capability import (
    CapabilityRegistry,
    EvidenceScope,
    ProviderCapability,
)
from amanda_agent.requirements.decisions import DecisionScenario

CAPABILITY = "revit.create_furniture_element"


class RecordingInvoker:
    def __init__(self) -> None:
        self.calls = []

    def invoke(self, call):
        self.calls.append(call)
        return {"reported_success": True, "unique_id": f"uid-{call.logical_id}"}


def _request(root: Path) -> PreflightRequest:
    evidence = root / "furniture-evidence.json"
    evidence.write_text("synthetic furniture provider evidence", encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    registry = CapabilityRegistry(
        entries=[
            ProviderCapability(
                provider="fixture",
                status="PASS",
                priority=1,
                provider_commit="b" * 40,
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
    )
    return PreflightRequest(
        mode=ExecutionMode.SYNTHETIC_LAB,
        stage=BimStage.R10,
        scenario=DecisionScenario.STUDY,
        registry=registry,
        revit_build="2027",
        tool_schema_hash="schema-1",
        expected_build="2027",
        expected_tool_schema_hash="schema-1",
        fixture=True,
        evidence_scope=EvidenceScope.SYNTHETIC,
        generation_run="run-01",
    )


PROGRAM = {
    "baseline": {"person_capacity": 20},
    "sectors": [
        {
            "logical_id": "SEC-RES",
            "name": "Setor residencial",
            "spaces": [
                {
                    "logical_id": "REQ-BED",
                    "name": "Quarto individual",
                    "quantity": 2,
                    "beds_per_unit": 1,
                },
                {
                    "logical_id": "REQ-DIN",
                    "name": "Refeitorio residencial",
                    "quantity": 1,
                    "beds_per_unit": None,
                },
            ],
        },
        {
            "logical_id": "SEC-TECH",
            "name": "Atendimento tecnico",
            "spaces": [
                {
                    "logical_id": "REQ-PSY",
                    "name": "Psicologia",
                    "quantity": 1,
                    "beds_per_unit": None,
                },
            ],
        },
        {
            "logical_id": "SEC-CHILD",
            "name": "Setor infantil",
            "spaces": [
                {
                    "logical_id": "REQ-CHILD",
                    "name": "Brinquedoteca",
                    "quantity": 1,
                    "beds_per_unit": None,
                },
            ],
        },
    ],
}


def test_furniture_sets_are_explicit_and_have_family_and_type(tmp_path: Path):
    plan = plan_furniture_stage(_request(tmp_path), program=PROGRAM)

    assert plan.person_capacity == 20
    assert plan.desired_state.stage is BimStage.R10
    assert len(plan.desired_state.elements) >= 8
    assert all(element.properties["family"] for element in plan.desired_state.elements)
    assert all(element.properties["type"] for element in plan.desired_state.elements)
    categories = {
        element.properties["furniture_set"] for element in plan.desired_state.elements
    }
    assert {"bedroom", "dining", "psychology", "child-area"} <= categories


def test_furniture_generation_rejects_a_program_above_twenty_people(tmp_path: Path):
    over_capacity = {**PROGRAM, "baseline": {"person_capacity": 21}}

    with pytest.raises(ValueError, match="20"):
        plan_furniture_stage(_request(tmp_path), program=over_capacity)


def test_furniture_generation_excludes_explicit_external_sectors(tmp_path: Path):
    program = {
        **PROGRAM,
        "sectors": [
            *PROGRAM["sectors"],
            {
                "logical_id": "SEC-EXT",
                "name": "Áreas externas",
                "area_kind": "EXTERNAL",
                "spaces": [
                    {
                        "logical_id": "REQ-EXT",
                        "name": "Jardim terapêutico",
                        "quantity": 1,
                    }
                ],
            },
        ],
    }

    plan = plan_furniture_stage(_request(tmp_path), program=program)

    assert all(item.sector_id != "SEC-EXT" for item in plan.items)
    assert all(
        element.properties["sector_id"] != "SEC-EXT"
        for element in plan.desired_state.elements
    )


def test_furniture_ids_are_stable_for_the_same_program(tmp_path: Path):
    first = plan_furniture_stage(_request(tmp_path), program=PROGRAM)
    second = plan_furniture_stage(_request(tmp_path), program=PROGRAM)

    assert [element.logical_id for element in first.desired_state.elements] == [
        element.logical_id for element in second.desired_state.elements
    ]
    assert first.desired_state.model_dump(
        mode="json"
    ) == second.desired_state.model_dump(mode="json")


def test_furniture_write_is_dispatched_and_requeried(tmp_path: Path):
    plan = plan_furniture_stage(_request(tmp_path), program=PROGRAM)
    invoker = RecordingInvoker()

    records = execute_furniture_stage(plan, invoker=invoker)

    assert len(records) == len(plan.operations)
    assert all(call.stage is BimStage.R10 for call in invoker.calls)
    query = {
        element.logical_id: {
            "unique_id": f"uid-{element.logical_id}",
            "geometry": element.geometry,
            "properties": element.properties,
        }
        for element in plan.desired_state.elements
    }
    assert all(
        result.passed for result in verify_furniture_stage(plan, query_result=query)
    )
