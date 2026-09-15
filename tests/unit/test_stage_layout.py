"""Behavioural contracts for the R06 internal layout stage."""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest
from shapely.geometry import box

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import (
    EvidenceScope,
    ExecutionMode,
    PreflightRequest,
    StageError,
    StagePreflightError,
)
from amanda_agent.models.capability import CapabilityRegistry, ProviderCapability
from amanda_agent.requirements.relations import (
    EnvironmentRelation,
    FlowNetwork,
    RelationType,
)

LAYOUT_CAPABILITY = "revit.create_internal_wall"


def _api():
    try:
        return importlib.import_module("amanda_agent.bim.stages.layout")
    except ModuleNotFoundError as exc:
        pytest.fail(f"R06 layout stage is missing: {exc}")


def _registry(
    tmp_path: Path, *, operation: str = LAYOUT_CAPABILITY, status: str = "PASS"
) -> CapabilityRegistry:
    evidence = tmp_path / "layout-evidence.json"
    evidence.write_text(operation, encoding="utf-8")
    return CapabilityRegistry(
        entries=[
            ProviderCapability(
                provider="synthetic-provider",
                status=status,
                priority=1,
                provider_commit="a" * 40,
                transport_provider="test",
                tool_schema_hash="schema-1",
                tested_scope={"operation": operation, "writes": True},
                evidence_scope=EvidenceScope.SYNTHETIC,
                revit_build="2027",
                save_reopen=True,
                independent_query=True,
                evidence=[]
                if status != "PASS"
                else [
                    f"{evidence}::sha256={hashlib.sha256(evidence.read_bytes()).hexdigest()}"
                ],
            )
        ]
    )


def _request(tmp_path: Path, **overrides) -> PreflightRequest:
    values = {
        "mode": ExecutionMode.SYNTHETIC_LAB,
        "stage": BimStage.R06,
        "registry": _registry(tmp_path),
        "revit_build": "2027",
        "tool_schema_hash": "schema-1",
        "expected_build": "2027",
        "expected_tool_schema_hash": "schema-1",
        "fixture": True,
        "evidence_scope": EvidenceScope.SYNTHETIC,
        "generation_run": "run-layout-01",
    }
    values.update(overrides)
    return PreflightRequest(**values)


def _rooms():
    return [
        {"logical_id": "room-a", "geometry": box(0, 0, 4, 4), "target_area_m2": 16.0},
        {"logical_id": "room-b", "geometry": box(4, 0, 8, 4), "target_area_m2": 16.0},
    ]


def test_layout_preserves_ids_deduplicates_boundary_and_checks_adjacency(
    tmp_path: Path,
):
    api = _api()
    relation = EnvironmentRelation(
        source_logical_id="room-a",
        target_logical_id="room-b",
        relation=RelationType.MUST_ADJOIN,
        weight=1.0,
    )

    plan = api.plan_layout_stage(
        _request(tmp_path),
        _rooms(),
        adjacency_relations=[relation],
        area_ranges={"room-a": (15.5, 16.5), "room-b": (15.5, 16.5)},
    )

    walls = [
        element
        for element in plan.desired_state.elements
        if element.category == "INTERNAL_WALL"
    ]
    assert len(walls) == 1
    assert walls[0].logical_id.startswith("LAYOUT-WALL-")
    assert plan.adjacency_results[0].passed is True
    assert plan.area_results["room-a"]["actual_area_m2"] == pytest.approx(16.0)
    assert plan.area_results["room-a"]["geometry_unchanged"] is True


def test_layout_refuses_a_mandatory_adjacency_violation(tmp_path: Path):
    api = _api()
    relation = EnvironmentRelation(
        source_logical_id="room-a",
        target_logical_id="room-b",
        relation=RelationType.MUST_ADJOIN,
        weight=1.0,
    )
    rooms = [
        {"logical_id": "room-a", "geometry": box(0, 0, 4, 4), "target_area_m2": 16.0},
        {"logical_id": "room-b", "geometry": box(5, 0, 9, 4), "target_area_m2": 16.0},
    ]

    with pytest.raises(StageError, match="adjacency"):
        api.plan_layout_stage(_request(tmp_path), rooms, adjacency_relations=[relation])


def test_layout_reuses_flow_graph_contract_when_routes_are_requested(tmp_path: Path):
    api = _api()
    flow_candidate = {
        "nodes": [{"id": "room-a"}, {"id": "room-b"}],
        "corridors": [
            {
                "id": "corridor-a-b",
                "from": "room-a",
                "to": "room-b",
                "geometry": [(0, 2), (8, 2)],
                "width_m": 1.2,
                "allowed_flows": ["visitor"],
            }
        ],
    }

    plan = api.plan_layout_stage(
        _request(tmp_path),
        _rooms(),
        flow_candidate=flow_candidate,
        flow_routes={FlowNetwork.VISITOR: ("room-a", "room-b")},
    )

    assert plan.flow_results[FlowNetwork.VISITOR].connected is True
    assert plan.flow_results[FlowNetwork.VISITOR].ok is True


def test_layout_refuses_when_the_execution_mode_cannot_reach_r06(tmp_path: Path):
    api = _api()

    with pytest.raises(StagePreflightError, match="mode_stage_window"):
        api.plan_layout_stage(
            _request(tmp_path, mode=ExecutionMode.CONCEPT_ONLY, fixture=False),
            _rooms(),
        )


def test_layout_verifies_boundary_elements_against_independent_query(tmp_path: Path):
    api = _api()
    plan = api.plan_layout_stage(_request(tmp_path), _rooms())
    query_results = {
        element.logical_id: {
            "logical_id": element.logical_id,
            "unique_id": f"uid-{element.logical_id}",
            "geometry": element.geometry,
            "properties": element.properties,
        }
        for element in plan.desired_state.elements
    }

    results = api.verify_layout_stage(
        plan, tool_reported_success=True, query_results=query_results
    )

    assert results and all(result.passed for result in results)
