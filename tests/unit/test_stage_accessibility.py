"""Behavioural tests for the R09 accessibility stage (P05-T17)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import ExecutionMode, PreflightRequest
from amanda_agent.bim.stages.accessibility import (
    AccessibilityInput,
    AccessibilityStatus,
    AccessibleRoute,
    ParkingCheck,
    RampCheck,
    SanitaryCheck,
    WidthCheck,
    execute_accessibility_stage,
    load_verified_numeric_rules,
    plan_accessibility_stage,
    verify_accessibility_stage,
)
from amanda_agent.models.capability import (
    CapabilityRegistry,
    EvidenceScope,
    ProviderCapability,
)
from amanda_agent.requirements.decisions import DecisionScenario

CAPABILITY = "revit.create_accessibility_element"


class RecordingInvoker:
    def __init__(self, *, reported_success: bool = True) -> None:
        self.calls = []
        self.reported_success = reported_success

    def invoke(self, call):
        self.calls.append(call)
        return {
            "reported_success": self.reported_success,
            "unique_id": f"uid-{call.logical_id}",
        }


def _registry(root: Path) -> CapabilityRegistry:
    evidence = root / "accessibility-evidence.json"
    evidence.write_text("synthetic accessibility provider evidence", encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    return CapabilityRegistry(
        entries=[
            ProviderCapability(
                provider="fixture",
                status="PASS",
                priority=1,
                provider_commit="a" * 40,
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


def _request(root: Path, **overrides) -> PreflightRequest:
    values = {
        "mode": ExecutionMode.SYNTHETIC_LAB,
        "stage": BimStage.R09,
        "scenario": DecisionScenario.STUDY,
        "registry": _registry(root),
        "revit_build": "2027",
        "tool_schema_hash": "schema-1",
        "expected_build": "2027",
        "expected_tool_schema_hash": "schema-1",
        "fixture": True,
        "evidence_scope": EvidenceScope.SYNTHETIC,
        "generation_run": "run-01",
    }
    values.update(overrides)
    return PreflightRequest(**values)


def _inputs_without_measurements() -> AccessibilityInput:
    return AccessibilityInput(
        entrance_id="ENTRANCE-01",
        required_space_ids=["RECEPTION-01", "WC-ACCESS-01"],
        routes=[
            AccessibleRoute(
                logical_id="ROUTE-01",
                from_node="ENTRANCE-01",
                to_node="RECEPTION-01",
                measured_width_m=None,
            ),
            AccessibleRoute(
                logical_id="ROUTE-02",
                from_node="RECEPTION-01",
                to_node="WC-ACCESS-01",
                measured_width_m=None,
            ),
        ],
        ramps=[
            RampCheck(logical_id="RAMP-01", measured_slope=None, landing_depth_m=None)
        ],
        widths=[
            WidthCheck(
                logical_id="WIDTH-01", location="corridor", measured_width_m=None
            )
        ],
        parking=[
            ParkingCheck(
                logical_id="PARK-01", measured_width_m=None, side_access_m=None
            )
        ],
        sanitary=[
            SanitaryCheck(
                logical_id="SAN-01", turning_diameter_m=None, door_clearance_m=None
            )
        ],
    )


def test_missing_measurements_are_blocked_and_never_claim_compliance(tmp_path: Path):
    plan = plan_accessibility_stage(
        _request(tmp_path), inputs=_inputs_without_measurements()
    )

    assert plan.compliance_claim_allowed is False
    assert plan.numeric_status is AccessibilityStatus.STATUS_NAO_VERIFICADO
    assert all(
        check.status is AccessibilityStatus.STATUS_NAO_VERIFICADO
        for check in plan.checks
    )
    assert plan.preflight.get("normative_numeric_data").status.value == "BLOCKED"
    assert "STATUS_NAO_VERIFICADO" in plan.notes[0]


def test_numeric_rules_are_loaded_only_from_verified_registry_rows():
    registry = {
        "rules": [
            {
                "logical_id": "NBR-9050",
                "status": "IDENTIFIED",
                "numeric_value": 1.2,
                "source_refs": ["paid-or-unread-source"],
            },
            {
                "logical_id": "FREE-ROUTE-WIDTH",
                "status": "VERIFIED",
                "numeric_value": 1.5,
                "unit": "m",
                "source_refs": ["https://example.org/free-rule"],
            },
        ]
    }

    rules = load_verified_numeric_rules(registry)

    assert list(rules) == ["FREE-ROUTE-WIDTH"]
    assert rules["FREE-ROUTE-WIDTH"].numeric_value == 1.5


def test_route_graph_contains_entrance_and_required_spaces(tmp_path: Path):
    plan = plan_accessibility_stage(
        _request(tmp_path), inputs=_inputs_without_measurements()
    )

    assert plan.route_graph.nodes == {"ENTRANCE-01", "RECEPTION-01", "WC-ACCESS-01"}
    assert plan.route_graph.edges == [
        ("ENTRANCE-01", "RECEPTION-01"),
        ("RECEPTION-01", "WC-ACCESS-01"),
    ]
    assert {element.category for element in plan.desired_state.elements} >= {
        "accessible_route",
        "accessible_ramp",
        "accessible_parking",
        "accessible_sanitary",
    }


def test_accessibility_write_uses_injected_invoker_and_independent_query(
    tmp_path: Path,
):
    plan = plan_accessibility_stage(
        _request(tmp_path), inputs=_inputs_without_measurements()
    )
    invoker = RecordingInvoker()

    records = execute_accessibility_stage(plan, invoker=invoker)

    assert len(invoker.calls) == len(plan.operations)
    assert all(call.stage is BimStage.R09 for call in invoker.calls)
    assert all(record.reported_success for record in records)

    query = {
        element.logical_id: {
            "logical_id": element.logical_id,
            "unique_id": f"uid-{element.logical_id}",
            "geometry": element.geometry,
            "properties": element.properties,
        }
        for element in plan.desired_state.elements
    }
    verified = verify_accessibility_stage(
        plan, tool_reported_success=True, query_result=query
    )
    assert verified and all(result.passed for result in verified)

    query[plan.desired_state.elements[0].logical_id]["properties"] = {"wrong": True}
    failed = verify_accessibility_stage(
        plan, tool_reported_success=True, query_result=query
    )
    assert any(not result.passed for result in failed)


def test_final_profile_refuses_unmeasured_accessibility(tmp_path: Path):
    request = _request(tmp_path, scenario=DecisionScenario.FINAL)

    with pytest.raises(Exception, match="R09 preflight refused"):
        plan_accessibility_stage(request, inputs=_inputs_without_measurements())
