"""Regression: two independent accesses with explicit flow policies."""

from __future__ import annotations

import regression_support as support


def test_fixture_declares_two_distinct_accesses() -> None:
    observed = support.evaluate_fixture("two-access")["observed"]

    assert observed["entry_node_count"] == 2
    assert observed["entry_nodes"] == ["main-entry", "service-entry"]


def test_visitor_route_avoids_private_residential_space() -> None:
    routes = support.evaluate_fixture("two-access")["observed"]["routes"]
    visitor = routes["visitor"]

    assert visitor["ok"] is True
    assert visitor["path"] == ["main-entry", "public-hall", "visitor-room"]
    assert "private-dorm" not in visitor["path"]
    assert visitor["crossings"] == 0
    assert visitor["distance_m"] > 0


def test_service_crossing_is_hard_by_default_and_a_configured_soft_penalty() -> None:
    routes = support.evaluate_fixture("two-access")["observed"]["routes"]

    strict = routes["service-default-policy"]
    assert strict["ok"] is False
    assert strict["violation_codes"] == ["private_residential_access"]
    assert strict["crossings"] == 1

    weighted = routes["service-weighted-policy"]
    assert weighted["ok"] is True
    assert weighted["violation_codes"] == ["service_resident_crossing"]
    assert weighted["soft_penalty"] == 4.0
    assert weighted["path"] == strict["path"]
