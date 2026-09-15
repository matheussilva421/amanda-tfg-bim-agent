"""Regression: a plain three-room program still solves end to end."""

from __future__ import annotations

import regression_support as support


def test_three_room_program_reaches_a_hard_free_finalist() -> None:
    observed = support.evaluate_fixture("simple-3-room")["observed"]

    assert observed["finalist_count"] == 1
    assert observed["finalist_room_count"] == 3
    assert observed["finalist_room_ids"] == ["office", "reception", "dorm"]
    assert observed["finalist_hard_violation_codes"] == []
    assert observed["net_area_total_m2"] == 150.0


def test_pipeline_stays_offline_and_keeps_configured_stage_order() -> None:
    observed = support.evaluate_fixture("simple-3-room")["observed"]

    assert observed["revit_calls"] == 0
    assert observed["stage_order"] == [
        "macro",
        "hard_filter",
        "top_macro",
        "rooms",
        "finalists",
        "detailed",
    ]
    assert observed["rejected_count"] == 0


def test_seeded_generation_explores_more_than_one_macro_optimum() -> None:
    observed = support.evaluate_fixture("simple-3-room")["observed"]

    assert observed["macro_candidate_statuses"] == ["OPTIMAL"]
    assert observed["macro_candidate_hash_count"] >= 2, (
        "three seeds must not collapse onto a single macro geometry"
    )
