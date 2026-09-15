"""Synthetic contract tests for discovery reports and Tool Lab gating."""

import pytest

from amanda_agent.tools.discovery import (
    REQUIRED_REPORT_FIELDS,
    DiscoveryCandidate,
    DiscoveryReportError,
    ProductionInstallPlan,
    ToolDiscoveryReport,
    ToolLabRequiredError,
    ToolLabValidation,
)


def synthetic_report_payload() -> dict:
    return {
        "repository_url": "https://synthetic.invalid/tool",
        "commit_or_tag": "fixture-commit-001",
        "license": "Synthetic Permissive License",
        "build_method": "build from source fixture",
        "install_effects": "writes only to synthetic lab directory",
        "network_behavior": "no network after source retrieval",
        "revit_support": "synthetic Revit compatibility fixture",
        "mcp_codex_support": "synthetic MCP adapter fixture",
        "rollback": "delete synthetic lab directory and restore manifest",
        "risk_score": 20,
        "exact_capability": "synthetic wall metadata read",
    }


def test_discovery_report_requires_every_field():
    payload = synthetic_report_payload()

    for missing_field in REQUIRED_REPORT_FIELDS:
        incomplete = payload.copy()
        incomplete.pop(missing_field)
        with pytest.raises(DiscoveryReportError, match=missing_field):
            ToolDiscoveryReport.from_mapping(incomplete)


def test_report_rejects_blank_required_values_and_out_of_range_risk():
    blank = synthetic_report_payload()
    blank["rollback"] = ""
    with pytest.raises(DiscoveryReportError, match="rollback"):
        ToolDiscoveryReport.from_mapping(blank)

    invalid_risk = synthetic_report_payload()
    invalid_risk["risk_score"] = 101
    with pytest.raises(DiscoveryReportError, match="risk_score"):
        ToolDiscoveryReport.from_mapping(invalid_risk)


def test_discovery_candidate_cannot_install_directly_to_production():
    candidate = DiscoveryCandidate(ToolDiscoveryReport.from_mapping(synthetic_report_payload()))

    with pytest.raises(ToolLabRequiredError):
        candidate.install_to_production()


def test_only_tool_lab_validation_can_create_a_production_install_plan():
    report = ToolDiscoveryReport.from_mapping(synthetic_report_payload())
    candidate = DiscoveryCandidate(report)
    submission = candidate.submit_to_tool_lab()
    validation = ToolLabValidation.from_submission(
        submission,
        result="PASS",
        evidence_ref="synthetic-lab-run-001",
    )

    plan = ProductionInstallPlan.from_tool_lab_validation(validation)

    assert plan.report == report
    assert plan.tool_lab_evidence == "synthetic-lab-run-001"

