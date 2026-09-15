from __future__ import annotations

from amanda_agent.design.privacy import evaluate_privacy_gradient


def test_direct_public_to_residential_transition_is_invalid_and_strongly_penalized():
    result = evaluate_privacy_gradient([0, 5])

    assert result.valid is False
    assert result.penalty >= 50
    assert result.evidence["transition_sequence"] == [0, 5]


def test_staged_public_to_residential_gradient_scores_better():
    result = evaluate_privacy_gradient([0, 1, 3, 4, 5])
    direct = evaluate_privacy_gradient([0, 5])

    assert result.valid is True
    assert result.penalty < direct.penalty
    assert result.score > direct.score


def test_privacy_metric_accepts_identified_nodes_and_keeps_raw_sequence():
    sequence = [
        {"id": "street", "privacy_level": 0},
        {"id": "gate", "privacy_level": 1},
        {"id": "technical", "privacy_level": 3},
        {"id": "transition", "privacy_level": 4},
        {"id": "home", "privacy_level": 5},
    ]

    result = evaluate_privacy_gradient(sequence)

    assert result.evidence["transition_sequence"] == [0, 1, 3, 4, 5]
    assert result.evidence["node_ids"] == [
        "street",
        "gate",
        "technical",
        "transition",
        "home",
    ]
