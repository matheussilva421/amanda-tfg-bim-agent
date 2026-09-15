"""Regression: privacy gradient ordering is stable and auditable."""

from __future__ import annotations

import regression_support as support


def test_direct_public_to_residential_is_invalid_and_strongly_penalized() -> None:
    sequences = support.evaluate_fixture("privacy-gradient")["observed"]["sequences"]
    direct = sequences["direct"]

    assert direct["valid"] is False
    assert direct["direct_public_to_residential"] is True
    assert direct["penalty"] >= 100.0
    assert direct["transition_sequence"] == [0, 5]


def test_staged_and_stepwise_gradients_score_better_than_the_direct_jump() -> None:
    sequences = support.evaluate_fixture("privacy-gradient")["observed"]["sequences"]

    assert sequences["staged"]["valid"] is True
    assert sequences["stepwise"]["valid"] is True
    assert sequences["stepwise"]["penalty"] < sequences["staged"]["penalty"]
    assert sequences["staged"]["penalty"] < sequences["direct"]["penalty"]
    assert sequences["stepwise"]["score"] > sequences["staged"]["score"]


def test_raw_transition_sequence_and_node_ids_are_kept_as_evidence() -> None:
    sequences = support.evaluate_fixture("privacy-gradient")["observed"]["sequences"]
    staged = sequences["staged"]

    assert staged["transition_sequence"] == [0, 1, 3, 4, 5]
    assert staged["node_ids"] == ["street", "gate", "technical", "transition", "home"]
