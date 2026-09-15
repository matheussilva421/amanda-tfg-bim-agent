"""Behavioral tests for R03 levels, grids and references (P05-T11)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import ExecutionMode, PreflightRequest, StagePreflightError
from amanda_agent.bim.stages.levels import (
    GRID_CAPABILITY,
    LEVEL_CAPABILITY,
    REFERENCE_CAPABILITY,
    GridAxis,
    LevelReference,
    ReferenceMarker,
    execute_levels_stage,
    plan_levels_stage,
    verify_levels_stage,
)
from amanda_agent.models.capability import CapabilityRegistry, ProviderCapability
from amanda_agent.requirements.decisions import DecisionScenario


class RecordingInvoker:
    def __init__(self):
        self.calls = []

    def invoke(self, call):
        self.calls.append(call)
        return {"reported_success": True, "unique_id": f"uid-{call.logical_id}"}


def _capability(root: Path, operation: str) -> ProviderCapability:
    path = root / (operation.replace(".", "-") + ".json")
    path.write_text(operation, encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return ProviderCapability(
        provider="horizun",
        status="PASS",
        priority=1,
        provider_commit="a" * 40,
        transport_provider="mcp",
        tool_schema_hash="hash-1",
        tested_scope={"operation": operation, "writes": True},
        evidence_scope="PROVIDER",
        revit_build="2027",
        save_reopen=True,
        independent_query=True,
        evidence=[f"{path}::sha256={digest}"],
    )


def _request(root: Path, **overrides):
    values = {
        "mode": ExecutionMode.CONCEPT_ONLY,
        "stage": BimStage.R03,
        "scenario": DecisionScenario.STUDY,
        "registry": CapabilityRegistry(
            entries=[
                _capability(root, LEVEL_CAPABILITY),
                _capability(root, GRID_CAPABILITY),
                _capability(root, REFERENCE_CAPABILITY),
            ]
        ),
        "revit_build": "2027",
        "tool_schema_hash": "hash-1",
        "expected_build": "2027",
        "expected_tool_schema_hash": "hash-1",
        "generation_run": "run-03",
    }
    values.update(overrides)
    return PreflightRequest(**values)


def test_only_required_levels_are_generated_with_grid_and_reference_desired_state(tmp_path: Path):
    plan = plan_levels_stage(
        _request(tmp_path),
        levels=[
            LevelReference(
                logical_id="LEVEL-01",
                name="Térreo",
                elevation_m=0.0,
                evidence=["survey:level-01"],
            ),
            LevelReference(
                logical_id="LEVEL-OPTIONAL",
                name="Unused",
                elevation_m=4.0,
                required=False,
                evidence=["concept:optional"],
            ),
        ],
        grids=[
            GridAxis(
                logical_id="GRID-A",
                name="A",
                start=(0.0, 0.0),
                end=(10.0, 0.0),
                assumption="PROVISIONAL_ASSUMPTION",
            )
        ],
        references=[
            ReferenceMarker(
                logical_id="REF-01",
                name="Project Origin",
                kind="PROJECT_ORIGIN",
                coordinate=(0.0, 0.0, 0.0),
            )
        ],
    )

    assert [item.logical_id for item in plan.desired_state.elements] == [
        "LEVEL-01",
        "GRID-A",
        "REF-01",
    ]
    assert [operation.semantic_capability for operation in plan.operations] == [
        LEVEL_CAPABILITY,
        GRID_CAPABILITY,
        REFERENCE_CAPABILITY,
    ]
    assert plan.grids[0].assumption == "PROVISIONAL_ASSUMPTION"
    assert plan.grids[0].engineering_verified is False


def test_level_without_provable_elevation_is_refused(tmp_path: Path):
    with pytest.raises(StagePreflightError, match="level_evidence"):
        plan_levels_stage(
            _request(tmp_path),
            levels=[
                LevelReference(
                    logical_id="LEVEL-01",
                    name="Térreo",
                    elevation_m=0.0,
                    evidence=["unverified:level-01"],
                    is_provable=False,
                )
            ],
        )


def test_level_write_can_be_verified_by_name_and_elevation(tmp_path: Path):
    plan = plan_levels_stage(
        _request(tmp_path),
        levels=[
            LevelReference(
                logical_id="LEVEL-01",
                name="Térreo",
                elevation_m=0.0,
                evidence=["survey:level-01"],
            )
        ],
    )
    invoker = RecordingInvoker()
    records = execute_levels_stage(plan, invoker=invoker)

    assert len(records) == 1
    assert invoker.calls[0].payload["name"] == "Térreo"
    verified = verify_levels_stage(
        plan,
        tool_reported_success=True,
        query_results={
            "LEVEL-01": {
                "logical_id": "LEVEL-01",
                "unique_id": "uid-LEVEL-01",
                "geometry": {"elevation_m": 0.0},
                "properties": {"name": "Térreo"},
            }
        },
    )
    assert all(result.passed for result in verified)
