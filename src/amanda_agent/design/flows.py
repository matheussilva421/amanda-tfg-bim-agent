"""Independent circulation graphs derived from built geometry and permissions."""

from __future__ import annotations

import heapq
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite
from typing import Any

from shapely.geometry import LineString

from amanda_agent.requirements.relations import FlowNetwork

from .geometry import InvalidDesignGeometryError, validate_polygon


class FlowViolationSeverity(StrEnum):
    HARD = "HARD"
    SOFT = "SOFT"


@dataclass(frozen=True)
class FlowPolicy:
    """Policy controlling access and whether residential crossings are hard."""

    min_width_m: float = 0.9
    forbid_private_residential: bool = True
    service_resident_crossing_penalty: float = 0.0

    def __post_init__(self) -> None:
        if not isfinite(self.min_width_m) or self.min_width_m < 0:
            raise ValueError("min_width_m must be finite and non-negative")
        if (
            not isfinite(self.service_resident_crossing_penalty)
            or self.service_resident_crossing_penalty < 0
        ):
            raise ValueError("service crossing penalty must be finite and non-negative")


@dataclass(frozen=True)
class FlowViolation:
    code: str
    message: str
    severity: FlowViolationSeverity = FlowViolationSeverity.HARD
    penalty: float = 0.0

    @property
    def hard(self) -> bool:
        return self.severity is FlowViolationSeverity.HARD


@dataclass
class FlowAnalysis:
    """Deterministic route result with path evidence and explicit failures."""

    flow: FlowNetwork
    start: str
    goal: str
    path: list[str] = field(default_factory=list)
    distance_m: float | None = None
    crossings: int = 0
    violations: list[FlowViolation] = field(default_factory=list)
    soft_penalty: float = 0.0
    evidence: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(violation.hard for violation in self.violations)

    @property
    def connected(self) -> bool:
        return bool(self.path)

    @property
    def hard_violations(self) -> list[FlowViolation]:
        return [violation for violation in self.violations if violation.hard]


class FlowGraph:
    """A small deterministic undirected graph containing only real route edges."""

    def __init__(self, flow: FlowNetwork) -> None:
        self.flow = FlowNetwork(flow)
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: dict[str, list[tuple[str, float, str]]] = {}

    @property
    def nodes(self) -> tuple[str, ...]:
        return tuple(sorted(self._nodes))

    @property
    def edges(self) -> tuple[tuple[str, str], ...]:
        pairs = {
            tuple(sorted((source, target)))
            for source, values in self._edges.items()
            for target, _, _ in values
        }
        return tuple(sorted(pairs))

    def add_node(self, identifier: str, **attributes: Any) -> None:
        self._nodes.setdefault(identifier, {}).update(attributes)
        self._edges.setdefault(identifier, [])

    def add_edge(
        self,
        source: str,
        target: str,
        *,
        length_m: float,
        edge_id: str,
        **attributes: Any,
    ) -> None:
        self.add_node(source)
        self.add_node(target)
        payload = (target, float(length_m), edge_id)
        reverse = (source, float(length_m), edge_id)
        self._edges[source].append(payload)
        self._edges[target].append(reverse)
        self._nodes[source].setdefault("edge_attributes", {})[edge_id] = attributes
        self._nodes[target].setdefault("edge_attributes", {})[edge_id] = attributes

    def neighbors(self, identifier: str) -> tuple[tuple[str, float, str], ...]:
        return tuple(sorted(self._edges.get(identifier, []), key=lambda item: item[0:3]))

    def node_data(self, identifier: str) -> dict[str, Any]:
        return self._nodes[identifier]

    def has_edge(self, source: str, target: str) -> bool:
        return any(neighbor == target for neighbor, _, _ in self._edges.get(source, []))

    def number_of_nodes(self) -> int:
        return len(self._nodes)

    def number_of_edges(self) -> int:
        return len(self.edges)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="python")
    raise TypeError("flow candidate must be a mapping or Pydantic model")


def _flow_name(flow: FlowNetwork | str) -> str:
    return FlowNetwork(flow).value


def _allowed(value: Any, flow: FlowNetwork) -> bool:
    if value is None:
        return True
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError("allowed_flows must be a sequence")
    return flow.value in {str(item.value if isinstance(item, StrEnum) else item) for item in value}


def _item_geometry(item: Any) -> Any:
    if isinstance(item, Mapping):
        for key in ("geometry", "polygon", "coordinates"):
            if key in item:
                return item[key]
    return item


def _identifier(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("id", item.get("logical_id"))
    else:
        value = getattr(item, "id", getattr(item, "logical_id", None))
    return str(value) if value is not None else None


def _connection_ends(item: Mapping[str, Any]) -> tuple[str, str] | None:
    source = item.get("from", item.get("source"))
    target = item.get("to", item.get("target"))
    if source is not None and target is not None:
        return str(source), str(target)
    nodes = item.get("nodes")
    if isinstance(nodes, Sequence) and len(nodes) == 2:
        return str(nodes[0]), str(nodes[1])
    return None


def _path_geometry(value: Any) -> LineString:
    geometry = _item_geometry(value)
    if isinstance(geometry, LineString):
        return geometry
    if isinstance(geometry, Mapping):
        coordinates = geometry.get("coordinates")
        if geometry.get("type") == "LineString" and coordinates is not None:
            return LineString(coordinates)
    if isinstance(geometry, Sequence) and not isinstance(geometry, (str, bytes)):
        try:
            line = LineString(geometry)
        except Exception as exc:  # pragma: no cover - Shapely owns details
            raise ValueError("route edge geometry must be a LineString") from exc
        if len(line.coords) >= 2:
            return line
    raise ValueError("route edge requires actual LineString geometry")


def _obstacle_polygons(candidate: Mapping[str, Any]) -> list[Any]:
    result = []
    for obstacle in candidate.get("obstacles", []) or []:
        try:
            result.append(validate_polygon(_item_geometry(obstacle)))
        except InvalidDesignGeometryError as exc:
            raise ValueError(f"invalid obstacle geometry: {exc}") from exc
    return result


def _candidate_nodes(candidate: Mapping[str, Any]) -> list[Any]:
    values = candidate.get("nodes", candidate.get("flow_nodes", []))
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise TypeError("flow nodes must be a sequence")
    return list(values)


def _candidate_connections(candidate: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    connections: list[Mapping[str, Any]] = []
    for key, kind in (
        ("corridors", "corridor"),
        ("portals", "portal"),
        ("vertical_connections", "vertical"),
        ("connections", "connection"),
        ("edges", "edge"),
    ):
        values = candidate.get(key, []) or []
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise TypeError(f"flow {key} must be a sequence")
        for item in values:
            if not isinstance(item, Mapping):
                raise TypeError(f"flow {key} items must be mappings")
            connection = dict(item)
            connection.setdefault("kind", kind)
            connections.append(connection)
    return connections


def build_flow_graph(
    candidate: Any,
    flow: FlowNetwork | str,
    *,
    min_width_m: float = 0.9,
) -> FlowGraph:
    """Build one flow graph from corridors, portals, widths, permissions, and obstacles."""

    values = _as_mapping(candidate)
    network = FlowNetwork(flow)
    if not isfinite(min_width_m) or min_width_m < 0:
        raise ValueError("min_width_m must be finite and non-negative")
    graph = FlowGraph(network)
    blocked_nodes: set[str] = set()
    for raw_node in _candidate_nodes(values):
        identifier = _identifier(raw_node)
        if identifier is None:
            raise ValueError("flow nodes require id or logical_id")
        if not _allowed(
            raw_node.get("allowed_flows") if isinstance(raw_node, Mapping) else None,
            network,
        ):
            blocked_nodes.add(identifier)
            continue
        attributes = dict(raw_node) if isinstance(raw_node, Mapping) else {}
        graph.add_node(identifier, **attributes)

    obstacles = _obstacle_polygons(values)
    for connection in _candidate_connections(values):
        ends = _connection_ends(connection)
        if ends is None:
            continue
        source, target = ends
        if source in blocked_nodes or target in blocked_nodes:
            continue
        if source not in graph.nodes or target not in graph.nodes:
            continue
        if not _allowed(connection.get("allowed_flows"), network):
            continue
        width = connection.get("width_m", connection.get("width"))
        if width is None or float(width) < min_width_m:
            continue
        line = _path_geometry(connection)
        if any(line.intersects(obstacle) for obstacle in obstacles):
            continue
        length = connection.get("length_m")
        route_length = float(line.length if length is None else length)
        if not isfinite(route_length) or route_length <= 0:
            continue
        edge_id = str(connection.get("id", f"{source}->{target}"))
        graph.add_edge(
            source,
            target,
            length_m=route_length,
            edge_id=edge_id,
            kind=connection.get("kind", "connection"),
            width_m=float(width),
            allowed_flows=connection.get("allowed_flows"),
        )
    return graph


def build_flow_graphs(candidate: Any, *, min_width_m: float = 0.9) -> dict[FlowNetwork, FlowGraph]:
    """Build all six independent flow networks from the same actual layout."""

    return {
        flow: build_flow_graph(candidate, flow, min_width_m=min_width_m)
        for flow in FlowNetwork
    }


def _private_node(data: Mapping[str, Any]) -> bool:
    return bool(data.get("private_residential")) or data.get("privacy_level") == 5


def _shortest_path(graph: FlowGraph, start: str, goal: str) -> tuple[list[str], float] | None:
    queue: list[tuple[float, tuple[str, ...], str]] = [(0.0, (start,), start)]
    best: dict[str, tuple[float, tuple[str, ...]]] = {start: (0.0, (start,))}
    while queue:
        distance, path, current = heapq.heappop(queue)
        if current == goal:
            return list(path), distance
        if best.get(current) != (distance, path):
            continue
        for neighbor, weight, _ in graph.neighbors(current):
            candidate = (distance + weight, path + (neighbor,))
            known = best.get(neighbor)
            if known is None or candidate < known:
                best[neighbor] = candidate
                heapq.heappush(queue, (candidate[0], candidate[1], neighbor))
    return None


def analyze_route(
    graph: FlowGraph,
    start: str,
    goal: str,
    *,
    policy: FlowPolicy | None = None,
) -> FlowAnalysis:
    """Compute a deterministic route and apply its flow access policy."""

    policy = policy or FlowPolicy()
    result = FlowAnalysis(flow=graph.flow, start=start, goal=goal)
    route = (
        _shortest_path(graph, start, goal)
        if start in graph.nodes and goal in graph.nodes
        else None
    )
    if route is None:
        result.violations.append(
            FlowViolation(
                code="disconnected_route",
                message=f"no traversable {graph.flow.value} route from {start} to {goal}",
            )
        )
        result.evidence.append(
            "route requires actual corridor, portal, vertical connection, width, "
            "permission, and obstacle checks"
        )
        return result
    result.path, result.distance_m = route
    interior = result.path[1:-1]
    private_crossings = sum(
        _private_node(graph.node_data(identifier)) for identifier in interior
    )
    result.crossings = private_crossings
    if private_crossings and policy.forbid_private_residential:
        result.violations.append(
            FlowViolation(
                code="private_residential_access",
                message="route crosses a private residential node forbidden by policy",
            )
        )
    if (
        private_crossings
        and graph.flow is FlowNetwork.SERVICE
        and policy.service_resident_crossing_penalty > 0
    ):
        result.soft_penalty = policy.service_resident_crossing_penalty * private_crossings
        result.violations.append(
            FlowViolation(
                code="service_resident_crossing",
                message="service route crosses resident circulation",
                severity=FlowViolationSeverity.SOFT,
                penalty=result.soft_penalty,
            )
        )
    result.evidence.append("path derived from actual traversable edges")
    return result


def validate_route(
    graph: FlowGraph,
    start: str,
    goal: str,
    *,
    policy: FlowPolicy | None = None,
) -> FlowAnalysis:
    """Compatibility name for route analysis."""

    return analyze_route(graph, start, goal, policy=policy)


build_independent_flow_graphs = build_flow_graphs


__all__ = [
    "FlowAnalysis",
    "FlowGraph",
    "FlowPolicy",
    "FlowViolation",
    "FlowViolationSeverity",
    "analyze_route",
    "build_flow_graph",
    "build_flow_graphs",
    "build_independent_flow_graphs",
    "validate_route",
]
