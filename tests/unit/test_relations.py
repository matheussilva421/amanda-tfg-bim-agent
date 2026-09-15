"""Behavioral contracts for the canonical environment relations schema."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from amanda_agent.requirements.relations import (
    EnvironmentRelation,
    FlowNetwork,
    RelationType,
)


def _relation(**overrides) -> dict:
    value = {
        "source_logical_id": "living-room",
        "target_logical_id": "kitchen",
        "relation": RelationType.SHOULD_BE_NEAR,
        "weight": 0.75,
    }
    value.update(overrides)
    return value


def test_relation_between_two_environment_ids_is_valid():
    relation = EnvironmentRelation(**_relation())

    assert relation.source_logical_id == "living-room"
    assert relation.target_logical_id == "kitchen"
    assert relation.relation is RelationType.SHOULD_BE_NEAR


def test_self_relation_is_rejected_by_default():
    with pytest.raises(ValidationError, match="self relation"):
        EnvironmentRelation(
            **_relation(target_logical_id="living-room")
        )


def test_group_self_relation_is_accepted_when_explicitly_allowed():
    relation = EnvironmentRelation(
        **_relation(
            target_logical_id="living-room",
            allow_self=True,
        )
    )

    assert relation.allow_self is True


@pytest.mark.parametrize("weight", [-0.01, 1.01])
def test_weight_must_be_between_zero_and_one(weight: float):
    with pytest.raises(ValidationError):
        EnvironmentRelation(**_relation(weight=weight))


@pytest.mark.parametrize(
    "field",
    ["max_distance_m", "preferred_distance_m"],
)
def test_distance_must_be_positive(field: str):
    with pytest.raises(ValidationError):
        EnvironmentRelation(**_relation(**{field: -0.1}))


def test_preferred_distance_cannot_exceed_max_distance():
    with pytest.raises(ValidationError, match="preferred distance"):
        EnvironmentRelation(
            **_relation(
                preferred_distance_m=4,
                max_distance_m=3,
            )
        )


def test_flow_network_exposes_all_supported_flows():
    assert {flow.value for flow in FlowNetwork} == {
        "resident",
        "child",
        "staff",
        "visitor",
        "service",
        "emergency",
    }
