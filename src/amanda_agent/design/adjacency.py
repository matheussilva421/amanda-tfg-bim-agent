"""Deterministic adjacency graph and relation evaluation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

try:  # NetworkX is optional in this locked environment.
    import networkx as nx
except ImportError:  # pragma: no cover - exercised by this repository's venv
    nx = None

from amanda_agent.requirements.relations import EnvironmentRelation, RelationType

from .geometry import minimum_distance, overlaps, validate_polygon


class AdjacencyStatus(StrEnum):
    """Evaluation outcome for one canonical relation."""

    PASS = "PASS"
    VIOLATION = "VIOLATION"
    NOT_EVALUATED = "NOT_EVALUATED"


class DeterministicGraph:
    """Small NetworkX-compatible subset used when NetworkX is unavailable."""

    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: dict[tuple[str, str], dict[str, Any]] = {}

    @property
    def nodes(self) -> tuple[str, ...]:
        return tuple(sorted(self._nodes))

    @property
    def edges(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._edges))

    def add_node(self, node: str, **attributes: Any) -> None:
        self._nodes.setdefault(node, {}).update(attributes)

    def add_edge(self, first: str, second: str, **attributes: Any) -> None:
        self.add_node(first)
        self.add_node(second)
        self._edges[tuple(sorted((first, second)))] = dict(attributes)

    def has_edge(self, first: str, second: str) -> bool:
        return tuple(sorted((first, second))) in self._edges

    def get_edge_data(self, first: str, second: str) -> dict[str, Any] | None:
        return self._edges.get(tuple(sorted((first, second))))

    def neighbors(self, node: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                other
                for first, second in self._edges
                for other in ((second,) if first == node else (first,))
                if first == node or second == node
            )
        )

    def number_of_nodes(self) -> int:
        return len(self._nodes)

    def number_of_edges(self) -> int:
        return len(self._edges)


@dataclass(frozen=True)
class AdjacencyResult:
    """Relation result with hard/soft semantics kept explicit."""

    source_logical_id: str
    target_logical_id: str
    relation: RelationType
    status: AdjacencyStatus
    distance_m: float | None = None
    penalty: float | None = None
    hard_violation: bool = False
    evidence: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status is AdjacencyStatus.PASS


def _relation_value(relation: Any, key: str, default: Any = None) -> Any:
    if isinstance(relation, Mapping):
        return relation.get(key, default)
    return getattr(relation, key, default)


def _as_relation(value: Any) -> EnvironmentRelation:
    if isinstance(value, EnvironmentRelation):
        return value
    if isinstance(value, Mapping):
        return EnvironmentRelation(**value)
    raise TypeError("adjacency relation must be EnvironmentRelation or mapping")


def _geometry_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        for key in ("geometry", "polygon", "coordinates"):
            if key in value:
                return value[key]
    return value


def _geometry_map(geometries: Any) -> dict[str, Any]:
    if isinstance(geometries, Mapping):
        if "rooms" in geometries or "spaces" in geometries:
            items = geometries.get("rooms", geometries.get("spaces", []))
            return _geometry_map(items)
        return {
            str(identifier): _geometry_value(value)
            for identifier, value in geometries.items()
        }
    if isinstance(geometries, Sequence) and not isinstance(geometries, (str, bytes)):
        result: dict[str, Any] = {}
        for item in geometries:
            if isinstance(item, Mapping):
                identifier = item.get("logical_id", item.get("id"))
            else:
                identifier = getattr(item, "logical_id", getattr(item, "id", None))
            if identifier is not None:
                result[str(identifier)] = _geometry_value(item)
        return result
    raise TypeError("geometries must be a mapping or sequence of identified items")


def build_adjacency_graph(
    relations: Iterable[EnvironmentRelation | Mapping[str, Any]],
) -> Any:
    """Build a graph whose edges preserve canonical relation metadata."""

    graph: Any = nx.Graph() if nx is not None else DeterministicGraph()
    for raw_relation in relations:
        relation = _as_relation(raw_relation)
        graph.add_edge(
            relation.source_logical_id,
            relation.target_logical_id,
            relation=relation.relation,
            weight=relation.weight,
            max_distance_m=relation.max_distance_m,
            preferred_distance_m=relation.preferred_distance_m,
            flow=relation.flow,
        )
    return graph


def _result(
    relation: EnvironmentRelation,
    status: AdjacencyStatus,
    *,
    distance: float | None = None,
    penalty: float | None = None,
    hard: bool = False,
    evidence: list[str] | None = None,
) -> AdjacencyResult:
    return AdjacencyResult(
        source_logical_id=relation.source_logical_id,
        target_logical_id=relation.target_logical_id,
        relation=relation.relation,
        status=status,
        distance_m=distance,
        penalty=penalty,
        hard_violation=hard,
        evidence=evidence or [],
    )


def evaluate_adjacency(
    relations: Iterable[EnvironmentRelation | Mapping[str, Any]],
    geometries: Any,
    *,
    tolerance_m: float = 0.01,
) -> list[AdjacencyResult]:
    """Evaluate real polygon relations without treating a graph edge as proof."""

    geometry_by_id = _geometry_map(geometries)
    results: list[AdjacencyResult] = []
    for raw_relation in relations:
        relation = _as_relation(raw_relation)
        source = relation.source_logical_id
        target = relation.target_logical_id
        if source not in geometry_by_id or target not in geometry_by_id:
            results.append(
                _result(
                    relation,
                    AdjacencyStatus.NOT_EVALUATED,
                    evidence=["geometry unavailable"],
                )
            )
            continue
        left = validate_polygon(geometry_by_id[source])
        right = validate_polygon(geometry_by_id[target])
        distance = minimum_distance(left, right)
        relation_type = relation.relation
        if relation_type is RelationType.MUST_ADJOIN:
            adjoins = left.touches(right) and distance <= tolerance_m
            results.append(
                _result(
                    relation,
                    AdjacencyStatus.PASS if adjoins else AdjacencyStatus.VIOLATION,
                    distance=distance,
                    hard=not adjoins,
                    evidence=["polygon boundaries touch" if adjoins else "polygon boundaries do not touch"],
                )
            )
        elif relation_type is RelationType.MUST_BE_SEPARATED:
            separated = not overlaps(left, right) and distance > tolerance_m
            results.append(
                _result(
                    relation,
                    AdjacencyStatus.PASS if separated else AdjacencyStatus.VIOLATION,
                    distance=distance,
                    hard=not separated,
                    evidence=["positive gap" if separated else "overlap or insufficient gap"],
                )
            )
        elif relation_type in {
            RelationType.SHOULD_ADJOIN,
            RelationType.SHOULD_BE_NEAR,
            RelationType.SHOULD_BE_SEPARATED,
        }:
            preferred = relation.preferred_distance_m or 0.0
            penalty = relation.weight * max(0.0, distance - preferred)
            results.append(
                _result(
                    relation,
                    AdjacencyStatus.PASS if penalty == 0 else AdjacencyStatus.VIOLATION,
                    distance=distance,
                    penalty=penalty,
                    evidence=["preferred distance met" if penalty == 0 else "preferred distance exceeded"],
                )
            )
        else:
            results.append(
                _result(relation, AdjacencyStatus.PASS, distance=distance)
            )
    return results


def adjacency_penalty(results: Iterable[AdjacencyResult]) -> float:
    """Sum only numeric soft penalties; hard failures remain boolean failures."""

    return sum(
        result.penalty or 0.0
        for result in results
        if not result.hard_violation
    )


def validate_adjacency(
    relations: Iterable[EnvironmentRelation | Mapping[str, Any]],
    geometries: Any,
    *,
    tolerance_m: float = 0.01,
) -> list[AdjacencyResult]:
    """Compatibility name for the relation evaluator."""

    return evaluate_adjacency(relations, geometries, tolerance_m=tolerance_m)


def must_relations_satisfied(results: Iterable[AdjacencyResult]) -> bool:
    """Return whether every evaluated mandatory relation passed."""

    return all(
        result.status is AdjacencyStatus.PASS
        for result in results
        if result.relation
        in {RelationType.MUST_ADJOIN, RelationType.MUST_BE_SEPARATED}
    )


__all__ = [
    "AdjacencyResult",
    "AdjacencyStatus",
    "DeterministicGraph",
    "adjacency_penalty",
    "build_adjacency_graph",
    "evaluate_adjacency",
    "must_relations_satisfied",
    "validate_adjacency",
]
