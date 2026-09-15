"""Behavioural tests for the R12 materials stage (P05-T20)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import ExecutionMode, PreflightRequest
from amanda_agent.bim.stages.materials import (
    MaterialAssignment,
    MaterialCatalogEntry,
    execute_materials_stage,
    plan_materials_stage,
    verify_materials_stage,
)
from amanda_agent.models.capability import (
    CapabilityRegistry,
    EvidenceScope,
    ProviderCapability,
)
from amanda_agent.requirements.decisions import DecisionScenario

CAPABILITY = "revit.assign_material"


class RecordingInvoker:
    def __init__(self) -> None:
        self.calls = []

    def invoke(self, call):
        self.calls.append(call)
        return {"reported_success": True, "unique_id": f"uid-{call.logical_id}"}


def _request(root: Path) -> PreflightRequest:
    evidence = root / "materials-evidence.json"
    evidence.write_text("synthetic materials provider evidence", encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    return PreflightRequest(
        mode=ExecutionMode.SYNTHETIC_LAB,
        stage=BimStage.R12,
        scenario=DecisionScenario.STUDY,
        registry=CapabilityRegistry(
            entries=[
                ProviderCapability(
                    provider="fixture",
                    status="PASS",
                    priority=1,
                    provider_commit="d" * 40,
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


CATALOG = [
    MaterialCatalogEntry(
        material_name="MAT-PISO-01",
        material_type="ceramic",
        source_ref="https://example.org/materials/piso",
        justification="Durable wet-area floor selected for the design intent.",
    ),
    MaterialCatalogEntry(
        material_name="MAT-PAREDE-01",
        material_type="paint",
        source_ref="https://example.org/materials/parede",
        justification="Low-maintenance wall finish selected for the design intent.",
    ),
]


ASSIGNMENTS = [
    MaterialAssignment(
        element_logical_id="WALL-01",
        material_name="MAT-PAREDE-01",
        material_type="paint",
        requirement_id="R12-WALL",
        design_intent="calm washable interior envelope",
    ),
    MaterialAssignment(
        element_logical_id="FLOOR-01",
        material_name="MAT-PISO-01",
        material_type="ceramic",
        requirement_id="R12-FLOOR",
        design_intent="durable accessible circulation floor",
    ),
]


def test_material_assignments_carry_registered_provenance(tmp_path: Path):
    plan = plan_materials_stage(
        _request(tmp_path), assignments=ASSIGNMENTS, catalog=CATALOG
    )

    assert len(plan.desired_state.elements) == 2
    for element in plan.desired_state.elements:
        assert element.properties["source_ref"].startswith("https://")
        assert element.properties["justification"]
        assert element.properties["design_intent"]


def test_material_without_catalog_provenance_is_refused(tmp_path: Path):
    unregistered = [
        MaterialAssignment(
            element_logical_id="WALL-02",
            material_name="MAT-UNKNOWN",
            material_type="unknown",
            requirement_id="R12-UNKNOWN",
            design_intent="unrecorded finish",
        )
    ]

    with pytest.raises(ValueError, match="provenance"):
        plan_materials_stage(
            _request(tmp_path), assignments=unregistered, catalog=CATALOG
        )


def test_duplicate_material_name_and_type_in_catalog_is_refused(tmp_path: Path):
    duplicate = [*CATALOG, CATALOG[0].model_copy()]

    with pytest.raises(ValueError, match="duplicate"):
        plan_materials_stage(
            _request(tmp_path), assignments=ASSIGNMENTS, catalog=duplicate
        )


def test_material_write_is_dispatched_and_requeried(tmp_path: Path):
    plan = plan_materials_stage(
        _request(tmp_path), assignments=ASSIGNMENTS, catalog=CATALOG
    )
    invoker = RecordingInvoker()

    records = execute_materials_stage(plan, invoker=invoker)

    assert len(records) == len(plan.operations)
    assert all(call.stage is BimStage.R12 for call in invoker.calls)
    query = {
        element.logical_id: {
            "unique_id": f"uid-{element.logical_id}",
            "geometry": element.geometry,
            "properties": element.properties,
        }
        for element in plan.desired_state.elements
    }
    assert all(
        result.passed for result in verify_materials_stage(plan, query_result=query)
    )
