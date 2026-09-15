"""Synthetic contract tests for maintenance/update isolation."""

import pytest

from amanda_agent.maintenance.policy import (
    RegressionEvidence,
    UpdateKind,
    UpdateRequest,
    evaluate_update,
)


def passed_regression() -> RegressionEvidence:
    return RegressionEvidence(
        full_provider=True,
        synthetic_e2e=True,
        result="PASS",
        evidence_ref="synthetic-regression-001",
    )


@pytest.mark.parametrize("phase", ["PRODUCTION_BUILD", "QA", "RC", "RELEASE"])
def test_revit_provider_and_critical_dependency_updates_are_refused_in_release_phases(
    phase: str,
):
    for kind in UpdateKind:
        decision = evaluate_update(
            UpdateRequest(
                component=kind,
                phase=phase,
                branch="maintenance/synthetic",
                regression=passed_regression(),
            )
        )
        assert decision.allowed is False
        assert "phase" in decision.reason.lower()


def test_provider_update_is_allowed_only_in_maintenance_with_full_regression():
    decision = evaluate_update(
        UpdateRequest(
            component=UpdateKind.PROVIDER,
            phase="MAINTENANCE",
            branch="maintenance/synthetic-provider",
            regression=passed_regression(),
        )
    )

    assert decision.allowed is True


def test_revit_update_is_allowed_in_experiment_with_full_regression():
    decision = evaluate_update(
        UpdateRequest(
            component=UpdateKind.REVIT,
            phase="EXPERIMENT",
            branch="experiment/synthetic-revit",
            regression=passed_regression(),
        )
    )

    assert decision.allowed is True


def test_provider_update_without_regression_is_refused_even_in_maintenance():
    decision = evaluate_update(
        UpdateRequest(
            component=UpdateKind.PROVIDER,
            phase="MAINTENANCE",
            branch="maintenance/synthetic-provider",
            regression=None,
        )
    )

    assert decision.allowed is False
    assert "regression" in decision.reason.lower()


def test_update_outside_maintenance_or_experiment_is_refused():
    decision = evaluate_update(
        UpdateRequest(
            component=UpdateKind.CRITICAL_DEPENDENCY,
            phase="DEVELOPMENT",
            branch="feature/synthetic",
            regression=None,
        )
    )

    assert decision.allowed is False
    assert "maintenance" in decision.reason.lower()

