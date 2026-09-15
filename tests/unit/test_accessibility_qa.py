from __future__ import annotations

from amanda_agent.qa.accessibility import qa_accessibility
from amanda_agent.qa.models import QaResult


def test_route_continuity_is_checked_from_graph_data():
    report = qa_accessibility(
        {
            "routes": [
                {
                    "check_id": "route.main",
                    "start": "entrance",
                    "end": "room",
                    "edges": [("entrance", "hall"), ("hall", "room")],
                }
            ]
        }
    )
    assert report.result is QaResult.PASS


def test_verified_regulation_rule_is_used_for_numeric_dimension():
    report = qa_accessibility(
        {"dimensions": [{"check_id": "door.width", "rule_id": "door_width", "value": 0.9}]},
        regulation_rules={
            "door_width": {"minimum": 0.8, "status": "VERIFIED", "source": "NBR fixture"}
        },
    )
    assert report.result is QaResult.PASS
    assert any(check.check_id == "door.width" for check in report.checks)


def test_missing_verified_rule_blocks_dimension_check():
    report = qa_accessibility(
        {"dimensions": [{"check_id": "door.width", "rule_id": "door_width", "value": 0.9}]},
        regulation_rules={},
    )
    assert report.result is QaResult.BLOCKED_BY_INPUT
    check = next(check for check in report.checks if check.check_id == "door.width")
    assert check.status.value == "BLOCKED"


def test_failed_verified_dimension_is_fail():
    report = qa_accessibility(
        {"dimensions": [{"check_id": "door.width", "rule_id": "door_width", "value": 0.7}]},
        regulation_rules={
            "door_width": {"minimum": 0.8, "status": "VERIFIED", "source": "NBR fixture"}
        },
    )
    assert report.result is QaResult.FAIL
    assert any(issue.code == "DIMENSION_BELOW_RULE" for issue in report.issues)


def test_unsupported_check_is_explicitly_skipped_with_reason():
    report = qa_accessibility(
        {"unsupported": [{"check_id": "tactile.surface", "reason": "no verified source"}]}
    )
    check = next(check for check in report.checks if check.check_id == "tactile.surface")
    assert check.status.value == "SKIPPED"
    assert any(issue.code == "UNSUPPORTED_CHECK" for issue in report.issues)
    assert report.result is QaResult.PASS_WITH_WARNINGS
