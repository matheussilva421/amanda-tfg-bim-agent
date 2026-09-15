from __future__ import annotations

from amanda_agent.design.flows import (
    FlowPolicy,
    analyze_route,
    build_flow_graph,
    build_flow_graphs,
)
from amanda_agent.requirements.relations import FlowNetwork


def _line(x1: float, x2: float):
    return [(x1, 0), (x2, 0)]


def _layout():
    return {
        "nodes": [
            {"id": "entry", "privacy_level": 0},
            {"id": "public-hall", "privacy_level": 1},
            {
                "id": "private-home",
                "privacy_level": 5,
                "private_residential": True,
            },
            {"id": "visitor-destination", "privacy_level": 1},
            {"id": "service-destination", "privacy_level": 3},
        ],
        "corridors": [
            {
                "id": "corridor-1",
                "from": "entry",
                "to": "public-hall",
                "geometry": _line(0, 4),
                "width_m": 1.2,
                "allowed_flows": ["visitor", "service", "resident"],
            },
            {
                "id": "corridor-2",
                "from": "public-hall",
                "to": "private-home",
                "geometry": _line(4, 8),
                "width_m": 1.2,
                "allowed_flows": ["visitor", "service", "resident"],
            },
            {
                "id": "corridor-3",
                "from": "private-home",
                "to": "visitor-destination",
                "geometry": _line(8, 12),
                "width_m": 1.2,
                "allowed_flows": ["visitor"],
            },
            {
                "id": "corridor-4",
                "from": "private-home",
                "to": "service-destination",
                "geometry": _line(8, 11),
                "width_m": 1.2,
                "allowed_flows": ["service"],
            },
        ],
        "portals": [
            {
                "id": "door-entry",
                "from": "entry",
                "to": "public-hall",
                "geometry": _line(0, 0.1),
                "width_m": 1.0,
                "allowed_flows": ["visitor", "service", "resident"],
            }
        ],
        "obstacles": [],
    }


def test_independent_flow_graphs_exist_for_all_canonical_networks():
    graphs = build_flow_graphs(_layout())

    assert set(graphs) == set(FlowNetwork)


def test_visitor_route_crossing_private_residential_node_is_hard_failure():
    graph = build_flow_graph(_layout(), FlowNetwork.VISITOR)

    result = analyze_route(
        graph,
        "entry",
        "visitor-destination",
        policy=FlowPolicy(forbid_private_residential=True),
    )

    assert result.ok is False
    assert any(item.code == "private_residential_access" for item in result.violations)


def test_configured_service_resident_crossing_is_a_soft_penalty():
    graph = build_flow_graph(_layout(), FlowNetwork.SERVICE)

    result = analyze_route(
        graph,
        "entry",
        "service-destination",
        policy=FlowPolicy(
            forbid_private_residential=False,
            service_resident_crossing_penalty=4.0,
        ),
    )

    assert result.ok is True
    assert result.soft_penalty == 4.0


def test_route_uses_real_edges_and_rejects_disconnected_or_undersized_paths():
    layout = {
        "nodes": [{"id": "a"}, {"id": "b"}],
        "corridors": [],
        "portals": [],
    }
    graph = build_flow_graph(layout, FlowNetwork.RESIDENT)
    disconnected = analyze_route(graph, "a", "b")
    assert disconnected.ok is False
    assert any(item.code == "disconnected_route" for item in disconnected.violations)

    layout["corridors"] = [
        {
            "id": "too-narrow",
            "from": "a",
            "to": "b",
            "geometry": _line(0, 2),
            "width_m": 0.5,
            "allowed_flows": ["resident"],
        }
    ]
    narrow = build_flow_graph(layout, FlowNetwork.RESIDENT)
    result = analyze_route(narrow, "a", "b")
    assert result.ok is False
