"""Regression: courtyard archetype with first-class external program geometry."""

from __future__ import annotations

import regression_support as support


def test_courtyard_seed_keeps_privacy_order_and_a_materialized_courtyard() -> None:
    observed = support.evaluate_fixture("courtyard")["observed"]

    assert observed["archetype"] == "COURTYARD"
    assert observed["sector_ids"] == ["public", "controlled", "residential"]
    assert observed["sector_privacy_levels"] == [0, 1, 5]
    assert observed["courtyard_ids"] == ["courtyard"]
    assert observed["sectors_inside_site"] is True
    assert observed["courtyards_inside_site"] is True


def test_external_spaces_are_programmed_geometry_not_leftovers() -> None:
    observed = support.evaluate_fixture("courtyard")["observed"]

    assert observed["external_space_ids"] == ["courtyard", "therapeutic", "playground"]
    assert observed["external_space_areas_m2"] == [80.0, 60.0, 40.0]
    assert observed["external_violation_codes"] == []
    assert observed["external_validation_codes"] == []
    assert observed["used_leftover_as_garden"] is False


def test_environmental_heuristics_stay_labeled_and_feed_versioned_scoring() -> None:
    observed = support.evaluate_fixture("courtyard")["observed"]

    assert observed["heuristic_labels"] == {"solar": "HEURISTIC", "ventilation": "HEURISTIC"}
    assert observed["solar_score"] > observed["ventilation_score"]
    assert observed["not_evaluated_dimensions"] == []
    assert 0.0 < observed["weighted_total"] < 1.0


def test_pareto_filtering_drops_the_dominated_candidate() -> None:
    observed = support.evaluate_fixture("courtyard")["observed"]

    assert observed["pareto_frontier_ids"] == ["A", "C", "D"]
    assert "B" not in observed["pareto_frontier_ids"]


def test_explanation_is_evidence_bound_and_free_of_hard_violations() -> None:
    observed = support.evaluate_fixture("courtyard")["observed"]

    assert observed["explanation_hard_violations"] == []
    assert any("program_compliance" in item for item in observed["explanation_strengths"])
    assert any("adjacency" in item for item in observed["explanation_tradeoffs"])
