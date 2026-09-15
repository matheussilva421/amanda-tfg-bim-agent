"""Behavioural contracts for the R08 canonical rooms stage."""

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
from amanda_agent.requirements.program import (
    AdoptedProgram,
    ProgramBaseline,
    ProgramSector,
    ProgramSpace,
    build_program,
)

ROOM_CAPABILITY = "revit.create_room"


def _api():
    try:
        return importlib.import_module("amanda_agent.bim.stages.rooms")
    except ModuleNotFoundError as exc:
        pytest.fail(f"R08 rooms stage is missing: {exc}")


def _registry(tmp_path: Path) -> CapabilityRegistry:
    evidence = tmp_path / "rooms-evidence.json"
    evidence.write_text(ROOM_CAPABILITY, encoding="utf-8")
    return CapabilityRegistry(
        entries=[
            ProviderCapability(
                provider="synthetic-provider",
                status="PASS",
                priority=1,
                provider_commit="a" * 40,
                transport_provider="test",
                tool_schema_hash="schema-1",
                tested_scope={"operation": ROOM_CAPABILITY, "writes": True},
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
        "stage": BimStage.R08,
        "registry": _registry(tmp_path),
        "revit_build": "2027",
        "tool_schema_hash": "schema-1",
        "expected_build": "2027",
        "expected_tool_schema_hash": "schema-1",
        "fixture": True,
        "evidence_scope": EvidenceScope.SYNTHETIC,
        "generation_run": "run-rooms-01",
    }
    values.update(overrides)
    return PreflightRequest(**values)


def _tiny_program(*, person_capacity: int = 20) -> AdoptedProgram:
    baseline = ProgramBaseline(
        source_id="SRC-TEST",
        source_filename="program.pdf",
        source_sha256="a" * 64,
        source_pages=[1],
        person_capacity=person_capacity,
        adoption_status="ACCEPTED",
        selection_authority="TEST",
        selection_date="2026-09-15",
        evidence="synthetic fixture",
    )
    return AdoptedProgram(
        baseline=baseline,
        sectors=[
            ProgramSector(
                logical_id="SEC-A",
                name="Setor A",
                area_kind="INTERNAL",
                subtotal_m2=20.0,
                spaces=[
                    ProgramSpace(
                        logical_id="REQ-A-01",
                        name="Sala A",
                        quantity=1,
                        target_area_m2=12.0,
                        area_kind="INTERNAL",
                        source_page=1,
                    ),
                    ProgramSpace(
                        logical_id="REQ-A-02",
                        name="Sala B",
                        quantity=1,
                        target_area_m2=8.0,
                        area_kind="INTERNAL",
                        source_page=1,
                    ),
                ],
            )
        ],
        unselected_hypotheses=[],
    )


def test_rooms_expand_canonical_quantities_and_reconcile_the_626_m2_program(
    tmp_path: Path,
):
    api = _api()
    program = build_program()
    geometries = {}
    for sector in program.sectors:
        if sector.area_kind != "INTERNAL":
            continue
        for space in sector.spaces:
            ids = (
                [space.logical_id]
                if space.quantity == 1
                else [
                    f"{space.logical_id}#{index}"
                    for index in range(1, space.quantity + 1)
                ]
            )
            for room_id in ids:
                geometries[room_id] = box(0, 0, space.target_area_m2, 1)

    plan = api.plan_rooms_stage(
        _request(tmp_path), program=program, room_geometries=geometries
    )

    assert plan.program_reconciliation["target_internal_useful_m2"] == pytest.approx(
        626.0
    )
    assert plan.program_reconciliation["person_capacity"] == 20
    assert plan.program_reconciliation["capacity_ok"] is True
    assert len(plan.desired_state.elements) == len(geometries)
    assert all(
        element.properties["requirement_id"] for element in plan.desired_state.elements
    )
    assert any(
        element.properties["number"] == "SEC-02-001"
        for element in plan.desired_state.elements
    )


def test_rooms_mark_geometry_area_divergence_without_rounding_it(tmp_path: Path):
    api = _api()
    program = _tiny_program()
    plan = api.plan_rooms_stage(
        _request(tmp_path),
        program=program,
        room_geometries={"REQ-A-01": box(0, 0, 13, 1), "REQ-A-02": box(0, 0, 8, 1)},
    )

    reconciliation = plan.program_reconciliation
    assert reconciliation["target_internal_useful_m2"] == pytest.approx(20.0)
    assert reconciliation["actual_geometry_area_m2"] == pytest.approx(21.0)
    assert reconciliation["divergence"] is True
    assert reconciliation["area_delta_m2"] == pytest.approx(1.0)


def test_rooms_reject_an_unplaced_canonical_room(tmp_path: Path):
    api = _api()

    with pytest.raises(StageError, match="unplaced"):
        api.plan_rooms_stage(
            _request(tmp_path),
            program=_tiny_program(),
            room_geometries={"REQ-A-01": box(0, 0, 12, 1)},
        )


def test_rooms_refuse_when_the_execution_mode_cannot_reach_r08(tmp_path: Path):
    api = _api()

    with pytest.raises(StagePreflightError, match="mode_stage_window"):
        api.plan_rooms_stage(
            _request(tmp_path, mode=ExecutionMode.CONCEPT_ONLY, fixture=False),
            program=_tiny_program(),
            room_geometries={"REQ-A-01": box(0, 0, 12, 1), "REQ-A-02": box(0, 0, 8, 1)},
        )


def test_rooms_verify_metadata_and_enclosure_against_independent_query(tmp_path: Path):
    api = _api()
    plan = api.plan_rooms_stage(
        _request(tmp_path),
        program=_tiny_program(),
        room_geometries={"REQ-A-01": box(0, 0, 12, 1), "REQ-A-02": box(0, 0, 8, 1)},
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

    results = api.verify_rooms_stage(
        plan, tool_reported_success=True, query_results=query_results
    )

    assert results and all(result.passed for result in results)
