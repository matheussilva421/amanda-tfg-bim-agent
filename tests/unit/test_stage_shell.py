"""Behavioural contracts for the R05 architectural shell stage."""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest
from shapely.geometry import box

from amanda_agent.bim.models import BimStage, DesiredElement
from amanda_agent.bim.stages import (
    EvidenceScope,
    ExecutionMode,
    PreflightRequest,
    StageError,
    StagePreflightError,
)
from amanda_agent.models.capability import CapabilityRegistry, ProviderCapability

SHELL_CAPABILITIES = (
    "revit.create_wall",
    "revit.create_floor",
    "revit.create_slab",
    "revit.create_roof",
)


def _api():
    try:
        return importlib.import_module("amanda_agent.bim.stages.shell")
    except ModuleNotFoundError as exc:  # red phase: the stage is not implemented yet
        pytest.fail(f"R05 shell stage is missing: {exc}")


def _registry(tmp_path: Path) -> CapabilityRegistry:
    entries = []
    for index, operation in enumerate(SHELL_CAPABILITIES):
        evidence = tmp_path / f"evidence-{index}.json"
        evidence.write_text(operation, encoding="utf-8")
        entries.append(
            ProviderCapability(
                provider="synthetic-provider",
                status="PASS",
                priority=index,
                provider_commit="a" * 40,
                transport_provider="test",
                tool_schema_hash="schema-1",
                tested_scope={"operation": operation, "writes": True},
                evidence_scope=EvidenceScope.SYNTHETIC,
                revit_build="2027",
                save_reopen=True,
                independent_query=True,
                evidence=[
                    f"{evidence}::sha256={hashlib.sha256(evidence.read_bytes()).hexdigest()}"
                ],
            )
        )
    return CapabilityRegistry(entries=entries)


def _request(tmp_path: Path, **overrides) -> PreflightRequest:
    values = {
        "mode": ExecutionMode.SYNTHETIC_LAB,
        "stage": BimStage.R05,
        "registry": _registry(tmp_path),
        "revit_build": "2027",
        "tool_schema_hash": "schema-1",
        "expected_build": "2027",
        "expected_tool_schema_hash": "schema-1",
        "fixture": True,
        "evidence_scope": EvidenceScope.SYNTHETIC,
        "generation_run": "run-shell-01",
    }
    values.update(overrides)
    return PreflightRequest(**values)


def _rooms():
    return [
        {"logical_id": "room-a", "sector_id": "SEC-A", "geometry": box(0, 0, 4, 4)},
        {"logical_id": "room-b", "sector_id": "SEC-B", "geometry": box(4, 0, 8, 4)},
    ]


def test_shell_derives_one_shared_wall_and_reconciles_net_area(tmp_path: Path):
    api = _api()

    plan = api.plan_shell_stage(
        _request(tmp_path),
        _rooms(),
        gross_shell=box(0, 0, 8, 4),
        floor_loops=[box(0, 0, 8, 4)],
        slab_loops=[box(0, 0, 8, 4)],
        roof={"type": "simple-approved", "elevation_m": 3.2},
    )

    walls = [
        element for element in plan.desired_state.elements if element.category == "WALL"
    ]
    assert len(walls) == 5
    assert len({element.logical_id for element in walls}) == len(walls)
    assert sum(element.properties["is_shared"] for element in walls) == 1
    assert all(
        element.properties["type_id"] in {"EXT_WALL_01", "INT_WALL_01"}
        for element in walls
    )
    assert plan.area_reconciliation["net_room_area_m2"] == pytest.approx(32.0)
    assert plan.area_reconciliation["gross_shell_area_m2"] == pytest.approx(32.0)
    assert {element.category for element in plan.desired_state.elements} == {
        "WALL",
        "FLOOR",
        "SLAB",
        "ROOF",
    }


def test_shell_merges_overlapping_and_touching_collinear_runs():
    api = _api()
    first = ((0.0, 0.0), (5.0, 0.0))
    second = ((4.0, 0.0), (8.0, 0.0))
    touching = ((8.0, 0.0), (10.0, 0.0))
    separated = ((20.0, 0.0), (22.0, 0.0))
    diagonal = ((0.0, 4.0), (2.0, 6.0))
    occurrences = {
        first: ["room-a"],
        second: ["room-b"],
        touching: ["room-c"],
        separated: ["room-d"],
        diagonal: ["room-a"],
    }

    merged = api._merge_collinear_edges(occurrences, {key: key for key in occurrences})

    assert ((0.0, 0.0), (10.0, 0.0)) in merged
    assert first not in merged
    assert second not in merged
    assert touching not in merged
    assert separated in merged
    assert diagonal in merged
    assert merged[((0.0, 0.0), (10.0, 0.0))][0] == (
        "room-a",
        "room-b",
        "room-c",
    )


def test_shell_canonicalizes_edge_endpoints_before_revit():
    api = _api()
    raw = ((33.69642857142857, 13.158333), (41.19642857142857, 13.158333))
    key = api._edge_key(*raw)

    merged = api._merge_collinear_edges(
        {key: ["room-a"]},
        {key: raw},
    )

    assert merged[key][1:3] == (
        (33.696429, 13.158333),
        (41.196429, 13.158333),
    )


def test_shell_rejects_an_uncontrolled_wall_type(tmp_path: Path):
    api = _api()

    with pytest.raises(StageError, match="type catalog"):
        api.plan_shell_stage(
            _request(tmp_path),
            _rooms(),
            wall_types={"external": "WALL_INVENTED_99"},
        )


def test_shell_refuses_when_the_execution_mode_cannot_reach_r05(tmp_path: Path):
    api = _api()
    request = _request(tmp_path, mode=ExecutionMode.CONCEPT_ONLY, fixture=False)

    with pytest.raises(StagePreflightError, match="mode_stage_window"):
        api.plan_shell_stage(request, _rooms())


class _RecordingInvoker:
    def __init__(self):
        self.calls = []

    def invoke(self, call):
        self.calls.append(call)
        return {"reported_success": True, "unique_id": f"uid-{call.logical_id}"}


def test_shell_dispatches_desired_operations_through_injected_invoker(tmp_path: Path):
    api = _api()
    plan = api.plan_shell_stage(
        _request(tmp_path), _rooms(), gross_shell=box(0, 0, 8, 4)
    )
    invoker = _RecordingInvoker()

    records = api.execute_shell_stage(plan, invoker=invoker)

    assert len(records) == len(plan.operations)
    assert invoker.calls
    assert all(call.stage is BimStage.R05 for call in invoker.calls)
    assert all(call.provider == "synthetic-provider" for call in invoker.calls)


def test_shell_adds_external_elements_from_an_injected_planner(tmp_path: Path):
    api = _api()
    link_evidence = tmp_path / "link-evidence.json"
    link_evidence.write_text("link", encoding="utf-8")
    registry = _registry(tmp_path)
    registry.entries.append(
        ProviderCapability(
            provider="synthetic-provider",
            status="PASS",
            priority=1,
            provider_commit="a" * 40,
            transport_provider="test",
            tool_schema_hash="schema-1",
            tested_scope={"operation": "revit.link_model", "writes": True},
            evidence_scope=EvidenceScope.SYNTHETIC,
            revit_build="2027",
            save_reopen=True,
            independent_query=True,
            evidence=[
                f"{link_evidence}::sha256={hashlib.sha256(link_evidence.read_bytes()).hexdigest()}"
            ],
        )
    )

    def external_planner():
        return [
            DesiredElement(
                logical_id="EXT-LINK-01",
                category="external_model_link",
                geometry={"model_path": "linked.rvt"},
                properties={"name": "linked"},
                requirement_id="BIM-EXTERNAL-LINK",
                design_option="EXTERNAL_ARTIFACTS",
                generation_run="external-run",
            )
        ]

    plan = api.plan_shell_stage(
        _request(tmp_path, registry=registry),
        _rooms(),
        external_planner=external_planner,
    )

    assert "EXT-LINK-01" in plan.desired_state.by_logical_id()
    assert plan.operations[-1].semantic_capability == "revit.link_model"


def test_shell_verifies_each_element_against_independent_query(tmp_path: Path):
    api = _api()
    plan = api.plan_shell_stage(
        _request(tmp_path), _rooms(), gross_shell=box(0, 0, 8, 4)
    )
    query_results = {
        element.logical_id: {
            "logical_id": element.logical_id,
            "unique_id": f"uid-{element.logical_id}",
            "geometry": element.geometry,
            "properties": element.properties,
        }
        for element in plan.desired_state.elements
    }

    results = api.verify_shell_stage(
        plan, tool_reported_success=True, query_results=query_results
    )

    assert results and all(result.passed for result in results)
