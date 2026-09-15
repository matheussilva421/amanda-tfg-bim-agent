from __future__ import annotations

from amanda_agent.design.pareto import pareto_frontier


def test_known_dominated_vector_is_removed_deterministically():
    candidates = [
        {"id": "balanced", "metrics": {"privacy": 0.8, "area": 0.8}},
        {"id": "dominated", "metrics": {"privacy": 0.7, "area": 0.7}},
        {"id": "tradeoff", "metrics": {"privacy": 0.95, "area": 0.5}},
    ]

    frontier = pareto_frontier(candidates, dimensions=["privacy", "area"])

    assert [item["id"] for item in frontier] == ["balanced", "tradeoff"]


def test_tradeoff_is_preserved_even_with_lower_weighted_total():
    candidates = [
        {"id": "weighted-winner", "metrics": {"privacy": 0.7, "area": 0.95}, "weighted_total": 0.95},
        {"id": "privacy-specialist", "metrics": {"privacy": 0.98, "area": 0.7}, "weighted_total": 0.80},
    ]

    frontier = pareto_frontier(candidates, dimensions=["privacy", "area"])

    assert {item["id"] for item in frontier} == {"weighted-winner", "privacy-specialist"}


def test_missing_dimensions_are_ignored_when_all_candidates_lack_that_evidence():
    candidates = [
        {"id": "a", "metrics": {"privacy": 0.8, "solar": None}},
        {"id": "b", "metrics": {"privacy": 0.7, "solar": None}},
    ]

    frontier = pareto_frontier(candidates, dimensions=["privacy", "solar"])

    assert [item["id"] for item in frontier] == ["a"]
