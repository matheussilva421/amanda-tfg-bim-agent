"""Accessibility QA with explicit separation of route evidence and regulations."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from .models import QaCheck, QaCheckStatus, QaIssue, QaReport, Severity


def load_regulation_rules(source: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    """Load dimensional rules from a mapping or YAML file."""

    if isinstance(source, Mapping):
        return dict(source)
    return yaml.safe_load(Path(source).read_text(encoding="utf-8")) or {}


def _payload(evidence: Any) -> dict[str, Any]:
    if isinstance(evidence, Mapping):
        return dict(evidence)
    return {"routes": list(evidence or [])}


def _endpoints(edge: Any) -> tuple[str, str] | None:
    if isinstance(edge, Mapping):
        source = edge.get("source", edge.get("from"))
        target = edge.get("target", edge.get("to"))
        return (str(source), str(target)) if source is not None and target is not None else None
    values = list(edge)
    return (str(values[0]), str(values[1])) if len(values) >= 2 else None


def _continuous(route: Mapping[str, Any]) -> bool:
    path = route.get("path")
    raw_edges = list(route.get("edges", []) or [])
    geometry = route.get("geometry")
    if isinstance(geometry, Mapping):
        raw_edges.extend(geometry.get("edges", geometry.get("segments", [])) or [])
    elif isinstance(geometry, Sequence) and not isinstance(geometry, (str, bytes)):
        raw_edges.extend(geometry)
    edges: list[tuple[str, str]] = []
    for raw_edge in raw_edges:
        endpoint = _endpoints(raw_edge)
        if endpoint is not None:
            edges.append(endpoint)
    if path is not None:
        path_values = [str(item) for item in path]
        edge_set = {tuple(edge) for edge in edges} | {(target, source) for source, target in edges}
        return len(path_values) >= 2 and all(
            (path_values[index], path_values[index + 1]) in edge_set
            for index in range(len(path_values) - 1)
        )
    start, end = route.get("start"), route.get("end")
    if start is None or end is None:
        return False
    adjacency: dict[str, set[str]] = defaultdict(set)
    for source, target in edges:
        adjacency[source].add(target)
        adjacency[target].add(source)
    start_value, end_value = str(start), str(end)
    queue = deque([start_value])
    visited = {start_value}
    while queue:
        current = queue.popleft()
        if current == end_value:
            return True
        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return False


def _rule(rules: Mapping[str, Any], rule_id: str) -> Mapping[str, Any] | None:
    candidate = rules.get(rule_id)
    if isinstance(candidate, Mapping):
        return candidate
    nested = rules.get("rules")
    if isinstance(nested, Mapping) and isinstance(nested.get(rule_id), Mapping):
        return nested[rule_id]
    return None


def qa_accessibility(
    evidence: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    *,
    regulation_rules: Mapping[str, Any] | str | Path | None = None,
    profile: str = "STUDY",
    scope: str = "accessibility",
) -> QaReport:
    """Run route checks and VERIFIED-only numeric regulation checks."""

    payload = _payload(evidence)
    rules = load_regulation_rules(regulation_rules) if regulation_rules is not None else {}
    issues: list[QaIssue] = []
    checks: list[QaCheck] = []
    required: list[str] = []

    for index, route in enumerate(payload.get("routes", []) or [], start=1):
        route = dict(route)
        check_id = str(route.get("check_id", f"accessibility.route.{index}"))
        continuous = _continuous(route)
        required.append(check_id)
        if not continuous:
            issues.append(
                QaIssue(
                    code="ROUTE_NOT_CONTINUOUS",
                    message=f"accessible route {check_id!r} is not continuous in supplied graph/geometry",
                    severity=Severity.HIGH,
                    scope="accessibility",
                    mandatory=True,
                    evidence={"route": route},
                    check_id=check_id,
                )
            )
        checks.append(
            QaCheck(
                check_id=check_id,
                mandatory=True,
                status=QaCheckStatus.PASS if continuous else QaCheckStatus.FAIL,
                severity_if_failed=Severity.HIGH,
                scope="accessibility",
            )
        )

    for index, dimension in enumerate(payload.get("dimensions", []) or [], start=1):
        dimension = dict(dimension)
        check_id = str(dimension.get("check_id", f"accessibility.dimension.{index}"))
        rule_id = str(dimension.get("rule_id", ""))
        rule = _rule(rules, rule_id)
        required.append(check_id)
        verified = bool(
            rule
            and str(rule.get("status", "")).upper() == "VERIFIED"
            and str(rule.get("source", "")).strip()
        )
        if not verified or rule is None:
            issues.append(
                QaIssue(
                    code="MISSING_VERIFIED_RULE",
                    message=f"dimension {check_id!r} has no VERIFIED regulation rule and source",
                    severity=Severity.HIGH,
                    scope="accessibility",
                    mandatory=True,
                    evidence={"check_id": check_id, "rule_id": rule_id, "rule": rule},
                    check_id=check_id,
                    missing_input=True,
                )
            )
            checks.append(
                QaCheck(
                    check_id=check_id,
                    mandatory=True,
                    status=QaCheckStatus.BLOCKED,
                    severity_if_failed=Severity.HIGH,
                    scope="accessibility",
                )
            )
            continue

        verified_rule = rule
        try:
            value = float(dimension["value"])
        except (KeyError, TypeError, ValueError) as exc:
            issues.append(
                QaIssue(
                    code="MISSING_INPUT_DIMENSION",
                    message=f"dimension {check_id!r} cannot be checked: {exc}",
                    severity=Severity.HIGH,
                    scope="accessibility",
                    mandatory=True,
                    evidence={"check_id": check_id, "value": dimension.get("value")},
                    check_id=check_id,
                    missing_input=True,
                )
            )
            checks.append(
                QaCheck(
                    check_id=check_id,
                    mandatory=True,
                    status=QaCheckStatus.BLOCKED,
                    severity_if_failed=Severity.HIGH,
                    scope="accessibility",
                )
            )
            continue
        minimum = verified_rule.get("minimum", verified_rule.get("min"))
        maximum = verified_rule.get("maximum", verified_rule.get("max"))
        passes = (minimum is None or value >= float(minimum)) and (
            maximum is None or value <= float(maximum)
        )
        if not passes:
            issues.append(
                QaIssue(
                    code="DIMENSION_BELOW_RULE" if minimum is not None and value < float(minimum) else "DIMENSION_ABOVE_RULE",
                    message=f"dimension {check_id!r} violates VERIFIED rule {rule_id!r}",
                    severity=Severity.HIGH,
                    scope="accessibility",
                    mandatory=True,
                    evidence={"value": value, "rule_id": rule_id, "rule": dict(verified_rule)},
                    check_id=check_id,
                )
            )
        checks.append(
            QaCheck(
                check_id=check_id,
                mandatory=True,
                status=QaCheckStatus.PASS if passes else QaCheckStatus.FAIL,
                severity_if_failed=Severity.HIGH,
                scope="accessibility",
            )
        )

    unsupported = payload.get("unsupported", []) or []
    if isinstance(unsupported, Mapping):
        unsupported = [
            {"check_id": key, "reason": value} for key, value in unsupported.items()
        ]
    for index, item in enumerate(unsupported, start=1):
        item = dict(item) if isinstance(item, Mapping) else {"reason": str(item)}
        check_id = str(item.get("check_id", f"accessibility.unsupported.{index}"))
        reason = str(item.get("reason", "unsupported check"))
        required.append(check_id)
        checks.append(
            QaCheck(
                check_id=check_id,
                mandatory=False,
                status=QaCheckStatus.SKIPPED,
                severity_if_failed=Severity.INFO,
                scope="accessibility",
            )
        )
        issues.append(
            QaIssue(
                code="UNSUPPORTED_CHECK",
                message=f"accessibility check {check_id!r} is unsupported: {reason}",
                severity=Severity.INFO,
                scope="accessibility",
                mandatory=False,
                evidence={"reason": reason, "status": "UNSUPPORTED"},
                check_id=check_id,
            )
        )

    return QaReport(
        profile=profile,
        scope=scope,
        checks=checks,
        issues=issues,
        required_check_ids=required,
        details={"verified_rule_ids": [key for key, value in rules.items() if isinstance(value, Mapping) and value.get("status") == "VERIFIED"]},
    )


validate_accessibility = qa_accessibility
accessibility_qa = qa_accessibility


__all__ = ["accessibility_qa", "load_regulation_rules", "qa_accessibility", "validate_accessibility"]
