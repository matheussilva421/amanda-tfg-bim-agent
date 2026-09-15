"""Behavioural contracts for the R07 hosted openings stage."""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import (
    EvidenceScope,
    ExecutionMode,
    PreflightRequest,
    StageError,
    StagePreflightError,
)
from amanda_agent.models.capability import CapabilityRegistry, ProviderCapability

OPENING_CAPABILITY = "revit.create_opening"


def _api():
    try:
        return importlib.import_module("amanda_agent.bim.stages.openings")
    except ModuleNotFoundError as exc:
        pytest.fail(f"R07 openings stage is missing: {exc}")


def _registry(tmp_path: Path) -> CapabilityRegistry:
    evidence = tmp_path / "openings-evidence.json"
    evidence.write_text(OPENING_CAPABILITY, encoding="utf-8")
    return CapabilityRegistry(
        entries=[
            ProviderCapability(
                provider="synthetic-provider",
                status="PASS",
                priority=1,
                provider_commit="a" * 40,
                transport_provider="test",
                tool_schema_hash="schema-1",
                tested_scope={"operation": OPENING_CAPABILITY, "writes": True},
                evidence_scope=EvidenceScope.SYNTHETIC,
                revit_build="2027",
                save_reopen=True,
                independent_query=True,
                evidence=[
                    f"{evidence}::sha256={hashlib.sha256(evidence.read_bytes()).hexdigest()}"
                ],
            )
        ]
    )


def _request(tmp_path: Path, **overrides) -> PreflightRequest:
    values = {
        "mode": ExecutionMode.SYNTHETIC_LAB,
        "stage": BimStage.R07,
        "registry": _registry(tmp_path),
        "revit_build": "2027",
        "tool_schema_hash": "schema-1",
        "expected_build": "2027",
        "expected_tool_schema_hash": "schema-1",
        "fixture": True,
        "evidence_scope": EvidenceScope.SYNTHETIC,
        "generation_run": "run-openings-01",
    }
    values.update(overrides)
    return PreflightRequest(**values)


HOSTS = [
    {
        "logical_id": "WALL-01",
        "category": "WALL",
        "geometry": {"type": "LineString", "coordinates": [[0, 0], [4, 0]]},
    },
]
CATALOG = {
    "DOOR_INT_01": {"kind": "DOOR", "family": "Door-Interior", "type": "Single-080"},
    "WINDOW_EXT_01": {
        "kind": "WINDOW",
        "family": "Window-Standard",
        "type": "Fixed-120",
    },
}


def test_openings_require_catalogued_family_and_preserve_host_dimensions(
    tmp_path: Path,
):
    api = _api()
    plan = api.plan_openings_stage(
        _request(tmp_path),
        [
            {
                "logical_id": "DOOR-01",
                "kind": "DOOR",
                "host_logical_id": "WALL-01",
                "family_type": "DOOR_INT_01",
                "position": (2.0, 0.0),
                "width_m": 0.90,
                "height_m": 2.10,
                "connects": ["room-a", "room-b"],
            },
            {
                "logical_id": "WINDOW-01",
                "kind": "WINDOW",
                "host_logical_id": "WALL-01",
                "family_type": "WINDOW_EXT_01",
                "position": (3.0, 0.0),
                "width_m": 1.20,
                "height_m": 1.20,
                "sill_m": 0.90,
            },
        ],
        hosts=HOSTS,
        family_catalog=CATALOG,
    )

    assert {element.category for element in plan.desired_state.elements} == {
        "DOOR",
        "WINDOW",
    }
    door = next(
        element for element in plan.desired_state.elements if element.category == "DOOR"
    )
    assert door.properties["host_logical_id"] == "WALL-01"
    assert door.properties["clear_width_m"] == pytest.approx(0.90)
    assert door.properties["connectivity"] == ["room-a", "room-b"]
    window = next(
        element
        for element in plan.desired_state.elements
        if element.category == "WINDOW"
    )
    assert window.properties["sill_m"] == pytest.approx(0.90)


def test_openings_refuse_a_family_type_missing_from_the_controlled_catalog(
    tmp_path: Path,
):
    api = _api()

    with pytest.raises(StageError, match="catalog"):
        api.plan_openings_stage(
            _request(tmp_path),
            [
                {
                    "logical_id": "DOOR-01",
                    "kind": "DOOR",
                    "host_logical_id": "WALL-01",
                    "family_type": "UNKNOWN",
                }
            ],
            hosts=HOSTS,
            family_catalog=CATALOG,
        )


def test_openings_reject_a_door_below_the_configured_accessibility_minimum(
    tmp_path: Path,
):
    api = _api()

    with pytest.raises(StageError, match="clear width"):
        api.plan_openings_stage(
            _request(tmp_path),
            [
                {
                    "logical_id": "DOOR-01",
                    "kind": "DOOR",
                    "host_logical_id": "WALL-01",
                    "family_type": "DOOR_INT_01",
                    "position": (2.0, 0.0),
                    "width_m": 0.70,
                    "height_m": 2.10,
                }
            ],
            hosts=HOSTS,
            family_catalog=CATALOG,
        )


def test_openings_reject_a_window_without_an_explicit_sill(tmp_path: Path):
    api = _api()

    with pytest.raises(StageError, match="sill"):
        api.plan_openings_stage(
            _request(tmp_path),
            [
                {
                    "logical_id": "WINDOW-01",
                    "kind": "WINDOW",
                    "host_logical_id": "WALL-01",
                    "family_type": "WINDOW_EXT_01",
                    "position": (3.0, 0.0),
                    "width_m": 1.20,
                    "height_m": 1.20,
                }
            ],
            hosts=HOSTS,
            family_catalog=CATALOG,
        )


def test_openings_refuse_when_the_execution_mode_cannot_reach_r07(tmp_path: Path):
    api = _api()

    with pytest.raises(StagePreflightError, match="mode_stage_window"):
        api.plan_openings_stage(
            _request(tmp_path, mode=ExecutionMode.CONCEPT_ONLY, fixture=False),
            [],
            hosts=HOSTS,
            family_catalog=CATALOG,
        )


def test_openings_verify_hosted_elements_against_independent_query(tmp_path: Path):
    api = _api()
    plan = api.plan_openings_stage(
        _request(tmp_path),
        [
            {
                "logical_id": "DOOR-01",
                "kind": "DOOR",
                "host_logical_id": "WALL-01",
                "family_type": "DOOR_INT_01",
                "position": (2.0, 0.0),
                "width_m": 0.90,
                "height_m": 2.10,
                "connects": ["room-a", "room-b"],
            }
        ],
        hosts=HOSTS,
        family_catalog=CATALOG,
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

    results = api.verify_openings_stage(
        plan, tool_reported_success=True, query_results=query_results
    )

    assert results and all(result.passed for result in results)
