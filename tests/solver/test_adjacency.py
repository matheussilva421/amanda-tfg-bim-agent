from __future__ import annotations

from amanda_agent.design.adjacency import (
    AdjacencyStatus,
    build_adjacency_graph,
    evaluate_adjacency,
)
from amanda_agent.requirements.relations import EnvironmentRelation, RelationType


def _relation(kind: RelationType, **overrides) -> EnvironmentRelation:
    values = {
        "source_logical_id": "a",
        "target_logical_id": "b",
        "relation": kind,
        "weight": 1.0,
        "preferred_distance_m": 1.0,
    }
    values.update(overrides)
    return EnvironmentRelation(**values)


def _room(x: float, width: float = 2.0):
    return [(x, 0), (x + width, 0), (x + width, 2), (x, 2), (x, 0)]


def test_canonical_relations_build_a_graph_with_edge_metadata():
    relation = _relation(RelationType.MUST_ADJOIN)

    graph = build_adjacency_graph([relation])

    assert set(graph.nodes) == {"a", "b"}
    assert graph.has_edge("a", "b")
    assert graph.get_edge_data("a", "b")["relation"] is RelationType.MUST_ADJOIN


def test_must_adjoin_passes_when_real_boundaries_touch_and_fails_with_gap():
    relation = _relation(RelationType.MUST_ADJOIN)
    touching = {"a": _room(0), "b": _room(2)}
    separated = {"a": _room(0), "b": _room(2.2)}

    passed = evaluate_adjacency([relation], touching)[0]
    failed = evaluate_adjacency([relation], separated)[0]

    assert passed.status is AdjacencyStatus.PASS
    assert failed.status is AdjacencyStatus.VIOLATION
    assert failed.hard_violation is True


def test_should_be_near_penalty_worsens_monotonically_with_distance():
    relation = _relation(RelationType.SHOULD_BE_NEAR, preferred_distance_m=1.0)
    near = evaluate_adjacency(
        [relation], {"a": _room(0), "b": _room(3.0)}
    )[0]
    far = evaluate_adjacency(
        [relation], {"a": _room(0), "b": _room(7.0)}
    )[0]

    assert far.penalty > near.penalty >= 0


def test_must_be_separated_remains_hard_when_polygons_overlap():
    relation = _relation(RelationType.MUST_BE_SEPARATED)

    result = evaluate_adjacency(
        [relation], {"a": _room(0), "b": _room(1)}
    )[0]

    assert result.status is AdjacencyStatus.VIOLATION
    assert result.hard_violation is True
    assert result.penalty is None
