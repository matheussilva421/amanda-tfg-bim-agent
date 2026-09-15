from __future__ import annotations

import asyncio

from amanda_agent.qa.models import QaResult
from amanda_agent.qa.program import reconcile_program


def program_config():
    return {
        "person_capacity": 20,
        "totals": {"internal_useful_m2": 626, "external_programmed_m2": 260},
        "spaces": [
            {
                "logical_id": "room-a",
                "quantity": 2,
                "area_range_m2": [10, 12],
                "soft_tolerance_m2": 1,
                "hard_minimum_m2": 8,
                "area_kind": "INTERNAL",
            },
            {
                "logical_id": "garden-a",
                "quantity": 1,
                "area_range_m2": [80, 80],
                "soft_tolerance_m2": 5,
                "hard_minimum_m2": 70,
                "area_kind": "EXTERNAL",
            },
        ],
    }


def observe(room_quantity=2, room_area=11, garden_quantity=1, garden_area=80):
    return [
        {"logical_id": "room-a", "quantity": room_quantity, "area_m2": room_area},
        {
            "logical_id": "garden-a",
            "quantity": garden_quantity,
            "area_m2": garden_area,
        },
    ]


def run(observed):
    return asyncio.run(reconcile_program(program_config(), observed))


def test_missing_required_room_fails():
    report = run([{"logical_id": "garden-a", "quantity": 1, "area_m2": 80}])
    assert report.result is QaResult.FAIL
    assert any(issue.code == "MISSING_REQUIRED_SPACE" for issue in report.issues)


def test_quantity_mismatch_fails():
    report = run(observe(room_quantity=1))
    assert report.result is QaResult.FAIL
    assert any(issue.code == "QUANTITY_MISMATCH" for issue in report.issues)


def test_area_inside_configured_range_passes():
    report = run(observe(room_area=11))
    assert report.result is QaResult.PASS
    assert not report.issues


def test_area_outside_soft_tolerance_but_above_hard_minimum_is_warning():
    report = run(observe(room_area=8.5))
    assert report.result is QaResult.PASS_WITH_WARNINGS
    issue = next(issue for issue in report.issues if issue.code == "AREA_OUTSIDE_SOFT_TOLERANCE")
    assert issue.mandatory is False


def test_area_below_hard_minimum_fails():
    report = run(observe(room_area=7))
    assert report.result is QaResult.FAIL
    assert any(issue.code == "AREA_BELOW_HARD_MINIMUM" for issue in report.issues)


def test_external_programmed_spaces_are_reconciled():
    report = run(observe(garden_quantity=0))
    assert report.result is QaResult.FAIL
    issue = next(issue for issue in report.issues if issue.code == "QUANTITY_MISMATCH")
    assert issue.evidence["area_kind"] == "EXTERNAL"
