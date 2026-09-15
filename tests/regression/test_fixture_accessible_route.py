"""Regression: accessible room accounting and the corridor width gate."""

from __future__ import annotations

import regression_support as support


def test_accessible_room_is_flagged_and_room_layout_is_hard_free() -> None:
    observed = support.evaluate_fixture("accessible-route")["observed"]

    assert observed["room_ids"] == ["consult", "therapy"]
    assert observed["accessible_room_ids"] == ["consult"]
    assert observed["room_refinement_violation_codes"] == []
    assert observed["room_hard_violation_codes"] == []
    assert observed["room_net_area_total_m2"] == 48.0


def test_route_is_only_traversable_at_the_accessible_corridor_width() -> None:
    routes = support.evaluate_fixture("accessible-route")["observed"]["routes"]

    assert routes["to-consult"]["ok"] is True
    assert routes["to-therapy-accessible-width"]["ok"] is False
    assert routes["to-therapy-accessible-width"]["violation_codes"] == [
        "disconnected_route"
    ]
    assert routes["to-therapy-standard-width"]["ok"] is True
    assert routes["to-therapy-standard-width"]["distance_m"] > 0
