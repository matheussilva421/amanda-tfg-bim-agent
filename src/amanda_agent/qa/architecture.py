"""Concept and adjacency checks for the compiled logical architecture graph."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .models import QaCheck, QaCheckStatus, QaIssue, QaReport, Severity


def _payload(graph: Any) -> dict[str, Any]:
    if isinstance(graph, Mapping):
        return dict(graph)
    return {"edges": list(graph or [])}


def _edge(value: Any) -> tuple[str, str, str, str]:
    if isinstance(value, Mapping):
        return (
            str(value.get("source", value.get("from", ""))),
            str(value.get("target", value.get("to", ""))),
            str(value.get("flow", "internal")),
            str(value.get("relation", value.get("kind", "adjacency"))),
        )
    values = list(value)
    return (
        str(values[0]),
        str(values[1]),
        str(values[2]) if len(values) > 2 else "internal",
        str(values[3]) if len(values) > 3 else "adjacency",
    )


def _edges(graph: Any) -> set[tuple[str, str, str, str]]:
    return {_edge(value) for value in _payload(graph).get("edges", []) or []}


def _has_relation(
    edges: set[tuple[str, str, str, str]],
    relation: Mapping[str, Any],
) -> bool:
    expected = _edge(relation)
    for actual in edges:
        if (
            actual[0] == expected[0]
            and actual[1] == expected[1]
            and actual[3] == expected[3]
            and ("flow" not in relation or actual[2] == expected[2])
        ):
            return True
        if (
            actual[0] == expected[1]
            and actual[1] == expected[0]
            and actual[3] == expected[3]
            and ("flow" not in relation or actual[2] == expected[2])
        ):
            return True
    return False


def _issue(code: str, message: str, check_id: str, evidence: Mapping[str, Any]) -> QaIssue:
    return QaIssue(
        code=code,
        message=message,
        severity=Severity.HIGH,
        scope="architecture",
        mandatory=True,
        evidence=dict(evidence),
        check_id=check_id,
    )


def qa_architecture(
    approved_graph: Mapping[str, Any] | Iterable[Any],
    bim_graph: Mapping[str, Any] | Iterable[Any],
    *,
    policy: Mapping[str, Any] | None = None,
    profile: str = "STUDY",
    scope: str = "architecture",
) -> QaReport:
    """Compare a BIM graph with an approved graph and injected flow policy."""

    approved = _payload(approved_graph)
    bim = _payload(bim_graph)
    settings = dict(policy or {})
    approved_edges = _edges(approved)
    bim_edges = _edges(bim)
    issues: list[QaIssue] = []
    checks: list[QaCheck] = []
    required: list[str] = []

    def add(check_id: str, failed: bool, status: QaCheckStatus | None = None) -> None:
        required.append(check_id)
        checks.append(
            QaCheck(
                check_id=check_id,
                mandatory=True,
                status=status or (QaCheckStatus.FAIL if failed else QaCheckStatus.PASS),
                severity_if_failed=Severity.HIGH,
                scope="architecture",
            )
        )

    missing_approved = sorted(
        edge
        for edge in approved_edges
        if not _has_relation(
            bim_edges,
            {"source": edge[0], "target": edge[1], "flow": edge[2], "relation": edge[3]},
        )
    )
    for source, target, flow, relation in missing_approved:
        issues.append(
            _issue(
                "MISSING_APPROVED_EDGE",
                f"approved adjacency {source!r}->{target!r} is absent from BIM graph",
                "architecture.adjacency",
                {"source": source, "target": target, "flow": flow, "relation": relation},
            )
        )
    add("architecture.adjacency", bool(missing_approved))

    private_nodes = {str(node) for node in settings.get("private_residential_nodes", [])}
    public_nodes = {str(node) for node in settings.get("public_flow_nodes", [])}
    authorized = {
        _edge(edge) for edge in settings.get("authorized_public_flow_edges", []) or []
    }
    unauthorized = []
    for edge in bim_edges:
        source, target, flow, relation = edge
        if flow.casefold() not in {"public", "public_flow"}:
            continue
        touches_private = source in private_nodes or target in private_nodes
        touches_public = not public_nodes or source in public_nodes or target in public_nodes
        if touches_private and touches_public and edge not in authorized:
            unauthorized.append(edge)
    for source, target, flow, relation in unauthorized:
        issues.append(
            _issue(
                "UNAUTHORIZED_PUBLIC_FLOW",
                f"public flow edge {source!r}->{target!r} enters a private residential zone",
                "architecture.private_public_flow",
                {"source": source, "target": target, "flow": flow, "relation": relation},
            )
        )
    add("architecture.private_public_flow", bool(unauthorized))

    service_policy = settings.get("service_flow", {}) or {}
    required_service = service_policy.get("required_edges", []) or []
    forbidden_service = service_policy.get("forbidden_edges", []) or []
    missing_service = [edge for edge in required_service if not _has_relation(bim_edges, edge)]
    forbidden_present = [edge for edge in forbidden_service if _has_relation(bim_edges, edge)]
    for edge in missing_service:
        issues.append(
            _issue(
                "MISSING_SERVICE_FLOW",
                "required service-flow relation is absent",
                "architecture.service_flow",
                {"edge": edge},
            )
        )
    for edge in forbidden_present:
        issues.append(
            _issue(
                "FORBIDDEN_SERVICE_FLOW",
                "forbidden service-flow relation is present",
                "architecture.service_flow",
                {"edge": edge},
            )
        )
    add("architecture.service_flow", bool(missing_service or forbidden_present))

    missing_gardens = [
        relation
        for relation in settings.get("garden_relations", []) or []
        if relation.get("required", True) and not _has_relation(bim_edges, relation)
    ]
    for relation in missing_gardens:
        issues.append(
            _issue(
                "MISSING_GARDEN_RELATION",
                "programmed therapeutic/protected garden relation is absent",
                "architecture.gardens",
                {"relation": relation},
            )
        )
    add("architecture.gardens", bool(missing_gardens))

    approved_metrics = approved.get("metrics", {}) or {}
    bim_metrics = bim.get("metrics", {}) or {}
    sequence_policy = settings.get("sequence_metrics", {}) or {}
    collapsed = []
    missing_metrics = []
    for metric_id, rule in sequence_policy.items():
        expected = rule.get("minimum", approved_metrics.get(metric_id)) if isinstance(rule, Mapping) else rule
        observed = bim_metrics.get(metric_id)
        if observed is None:
            missing_metrics.append(metric_id)
        elif expected is not None and float(observed) < float(expected):
            collapsed.append((metric_id, expected, observed))
    for metric_id in missing_metrics:
        issues.append(
            QaIssue(
                code="MISSING_SEQUENCE_METRIC",
                message=f"sequence metric {metric_id!r} is missing",
                severity=Severity.HIGH,
                scope="architecture",
                mandatory=True,
                evidence={"metric": metric_id},
                check_id="architecture.sequence_metrics",
                missing_input=True,
            )
        )
    for metric_id, expected, observed in collapsed:
        issues.append(
            _issue(
                "SEQUENCE_COLLAPSED",
                f"sequence metric {metric_id!r} fell from required {expected} to {observed}",
                "architecture.sequence_metrics",
                {"metric": metric_id, "expected": expected, "observed": observed},
            )
        )
    add("architecture.sequence_metrics", bool(missing_metrics or collapsed))

    return QaReport(
        profile=profile,
        scope=scope,
        checks=checks,
        issues=issues,
        required_check_ids=required,
        details={"approved_edge_count": len(approved_edges), "bim_edge_count": len(bim_edges)},
    )


validate_architecture = qa_architecture
architecture_qa = qa_architecture


__all__ = ["architecture_qa", "qa_architecture", "validate_architecture"]
