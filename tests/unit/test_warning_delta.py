from __future__ import annotations

from amanda_agent.qa.models import Severity
from amanda_agent.qa.warnings import compare_warnings, load_warning_baseline


def baseline():
    return {
        "schema_version": 1,
        "severity_map_version": 3,
        "severity_map": {"known-room": "LOW"},
        "entries": [
            {
                "id": "known-room",
                "regex": "room overlap",
                "text": "room overlap warning",
                "severity": "LOW",
                "status": "KNOWN",
                "reason": "accepted study limitation",
                "provenance": {"source": "fixture"},
            }
        ],
    }


def test_baseline_warning_is_known_and_not_new():
    delta = compare_warnings(
        baseline(),
        [{"id": "known-room", "text": "room overlap warning", "query": "warnings"}],
    )
    assert len(delta.known) == 1
    assert delta.new == []
    assert delta.known[0].status == "KNOWN"


def test_new_warning_is_emitted_with_query_evidence():
    delta = compare_warnings(
        baseline(),
        [{"id": "new-door", "text": "door has no host", "query": "door-query"}],
    )
    assert len(delta.new) == 1
    assert delta.new[0].status == "NEW"
    assert delta.new[0].evidence["id"] == "new-door"
    assert delta.new[0].evidence["query"] == "door-query"


def test_severity_map_is_versioned_and_unknown_is_reviewable():
    loaded = load_warning_baseline(baseline())
    delta = compare_warnings(loaded, [{"id": "unknown", "text": "unexpected"}])
    assert delta.severity_map_version == 3
    assert delta.new[0].severity == "REVIEW"
    assert delta.new[0].status == "REVIEW"
    assert delta.new[0].severity != Severity.INFO.value
    assert delta.new[0].status != "IGNORED"
