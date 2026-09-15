from __future__ import annotations

import pytest

from amanda_agent.design.scoring import load_weights, score_candidate


def test_scoring_normalizes_units_and_stores_raw_and_weighted_values():
    result = score_candidate(
        {
            "program_compliance": 0.9,
            "privacy_security": 0.8,
            "adjacency": 0.7,
            "circulation": 0.6,
            "accessibility": 1.0,
            "solar_heuristic": 0.5,
            "ventilation_heuristic": 0.5,
            "green_integration": 0.4,
            "compactness": 0.8,
            "constructability": 0.7,
            "concept_fidelity": 0.9,
        }
    )

    assert result.weighted_total == pytest.approx(sum(result.contributions.values()))
    assert result.raw_metrics["program_compliance"] == 0.9
    assert result.normalized_metrics["program_compliance"] == 0.9
    assert result.weights_version == 1
    assert "beauty" not in result.raw_metrics


def test_unknown_dimension_is_rejected_and_missing_environment_is_transparent():
    with pytest.raises(ValueError, match="unknown score dimension"):
        score_candidate({"beauty": 1.0})

    result = score_candidate({"program_compliance": 1.0})
    assert "solar_heuristic" in result.not_evaluated
    assert "solar_heuristic" not in result.contributions
    assert result.rebalanced_weight_total == pytest.approx(1.0)


def test_weight_changes_change_total_but_not_raw_metrics():
    weights = load_weights()
    baseline = score_candidate({"program_compliance": 1.0, "privacy_security": 0.0})
    changed = dict(weights)
    changed["program_compliance"] = weights["program_compliance"] * 2
    weighted = score_candidate({"program_compliance": 1.0, "privacy_security": 0.0}, weights=changed)

    assert weighted.raw_metrics == baseline.raw_metrics
    assert weighted.weighted_total != baseline.weighted_total
