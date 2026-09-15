from __future__ import annotations

from amanda_agent.qa.model import qa_model
from amanda_agent.qa.models import QaResult, Severity


def element(logical_id: str, **overrides):
    value = {
        "logical_id": logical_id,
        "managed": True,
        "category": "GenericModel",
        "positioned": True,
        "enclosed": True,
        "redundant": False,
        "within_site": True,
        "level": "Level 1",
        "expected_level": "Level 1",
    }
    value.update(overrides)
    return value


def test_duplicate_managed_logical_ids_are_critical():
    report = qa_model({"elements": [element("room-a"), element("room-a")]})
    issue = next(issue for issue in report.issues if issue.code == "DUPLICATE_LOGICAL_ID")
    assert report.result is QaResult.FAIL
    assert issue.severity is Severity.CRITICAL


def test_hosted_element_without_host_is_reported():
    report = qa_model(
        {"elements": [element("door-a", hosted=True, host_id=None, host_exists=False)]}
    )
    assert report.result is QaResult.FAIL
    issue = next(issue for issue in report.issues if issue.code == "HOST_MISSING")
    assert issue.severity in {Severity.HIGH, Severity.CRITICAL}


def test_room_must_be_positioned_enclosed_and_nonredundant():
    report = qa_model(
        {
            "elements": [
                element("room-a", category="Room", positioned=False),
                element("room-b", category="Room", enclosed=False),
                element("room-c", category="Room", redundant=True),
            ]
        }
    )
    assert report.result is QaResult.FAIL
    codes = {issue.code for issue in report.issues}
    assert {"ROOM_NOT_POSITIONED", "ROOM_NOT_ENCLOSED", "ROOM_REDUNDANT"} <= codes
    assert all(issue.severity is Severity.HIGH for issue in report.issues)


def test_managed_element_outside_prohibited_site_fails():
    report = qa_model(
        {"elements": [element("wall-a", within_site=False)]},
        config={"prohibit_outside_site": True},
    )
    assert report.result is QaResult.FAIL
    assert any(issue.code == "OUTSIDE_SITE" for issue in report.issues)


def test_unexpected_level_uses_stage_severity():
    report = qa_model(
        {"elements": [element("wall-a", level="Level 2")]},
        stage="R13",
        config={"level_severity_by_stage": {"R13": "HIGH"}},
    )
    issue = next(issue for issue in report.issues if issue.code == "UNEXPECTED_LEVEL")
    assert issue.severity is Severity.HIGH


def test_massive_count_delta_is_critical():
    report = qa_model(
        {"elements": [element("wall-a")], "counts": {"before": 10, "after": 30}},
        config={"massive_delta_absolute": 5, "massive_delta_ratio": 0.5},
    )
    assert report.result is QaResult.FAIL
    issue = next(issue for issue in report.issues if issue.code == "MASSIVE_COUNT_DELTA")
    assert issue.severity is Severity.CRITICAL
