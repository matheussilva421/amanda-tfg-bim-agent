from __future__ import annotations

from amanda_agent.qa.architecture import qa_architecture
from amanda_agent.qa.models import QaResult


def edge(source, target, flow="internal", relation="adjacency"):
    return {"source": source, "target": target, "flow": flow, "relation": relation}


def test_bim_graph_matches_approved_graph_and_preserves_garden_relations():
    approved = {
        "edges": [
            edge("shelter", "transition"),
            edge("transition", "city"),
            edge("residential", "garden", relation="therapeutic"),
        ],
        "metrics": {"shelter_transition_city": 3},
    }
    bim = {
        "edges": list(approved["edges"]),
        "metrics": {"shelter_transition_city": 3},
    }
    policy = {
        "private_residential_nodes": ["residential"],
        "garden_relations": [
            {"source": "residential", "target": "garden", "relation": "therapeutic"}
        ],
        "sequence_metrics": {"shelter_transition_city": {"minimum": 3}},
    }
    report = qa_architecture(approved, bim, policy=policy)
    assert report.result is QaResult.PASS
    assert not report.issues


def test_private_residential_zone_rejects_unauthorized_public_flow_edge():
    approved = {"edges": [edge("public", "residential", flow="internal")]}
    bim = {"edges": [edge("public", "residential", flow="public")]}
    report = qa_architecture(
        approved,
        bim,
        policy={
            "private_residential_nodes": ["residential"],
            "public_flow_nodes": ["public"],
        },
    )
    assert report.result is QaResult.FAIL
    assert any(issue.code == "UNAUTHORIZED_PUBLIC_FLOW" for issue in report.issues)


def test_service_flow_policy_and_garden_relation_are_checked():
    approved = {"edges": [edge("loading", "kitchen", flow="service")]}
    bim = {"edges": []}
    report = qa_architecture(
        approved,
        bim,
        policy={
            "service_flow": {
                "required_edges": [edge("loading", "kitchen", flow="service")]
            },
            "garden_relations": [
                {"source": "residential", "target": "garden", "relation": "protected"}
            ],
        },
    )
    assert report.result is QaResult.FAIL
    codes = {issue.code for issue in report.issues}
    assert "MISSING_SERVICE_FLOW" in codes
    assert "MISSING_GARDEN_RELATION" in codes


def test_collapsed_sequence_metric_fails_compile_qa():
    report = qa_architecture(
        {"metrics": {"shelter_transition_city": 3}},
        {"metrics": {"shelter_transition_city": 1}},
        policy={"sequence_metrics": {"shelter_transition_city": {"minimum": 3}}},
    )
    assert report.result is QaResult.FAIL
    assert any(issue.code == "SEQUENCE_COLLAPSED" for issue in report.issues)
