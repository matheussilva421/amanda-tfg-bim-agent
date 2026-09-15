from __future__ import annotations

from amanda_agent.qa.models import (
    QaCheck,
    QaCheckStatus,
    QaIssue,
    QaReport,
    QaResult,
    Severity,
    render_report_markdown,
)


def check(check_id: str, status: QaCheckStatus, mandatory: bool = True) -> QaCheck:
    return QaCheck(
        check_id=check_id,
        mandatory=mandatory,
        status=status,
        severity_if_failed=Severity.HIGH,
        scope="model",
    )


def test_report_serializes_deterministically_and_renders_markdown():
    report = QaReport(
        profile="STUDY",
        scope="model-001",
        checks=[check("geometry", QaCheckStatus.PASS)],
        issues=[],
        required_check_ids=["geometry"],
    )

    assert report.result is QaResult.PASS
    assert report.to_json() == report.to_json()
    assert '"profile": "STUDY"' in report.to_json()
    markdown = render_report_markdown(report)
    assert "STUDY" in markdown
    assert "geometry" in markdown
    assert "PASS" in markdown


def test_critical_issue_forces_fail():
    report = QaReport(
        profile="STUDY",
        scope="model",
        checks=[check("geometry", QaCheckStatus.PASS)],
        issues=[
            QaIssue(
                code="DUPLICATE_ID",
                message="managed logical id is duplicated",
                severity=Severity.CRITICAL,
                scope="model",
                mandatory=False,
                evidence={"logical_id": "room-a"},
                check_id="geometry",
            )
        ],
        required_check_ids=["geometry"],
    )
    assert report.result is QaResult.FAIL


def test_mandatory_failed_check_forces_fail():
    report = QaReport(
        profile="FINAL",
        scope="model",
        checks=[check("geometry", QaCheckStatus.FAIL)],
        issues=[],
        required_check_ids=["geometry"],
    )
    assert report.result is QaResult.FAIL


def test_mandatory_blocked_check_blocks_report():
    report = QaReport(
        profile="FINAL",
        scope="model",
        checks=[check("regulation", QaCheckStatus.BLOCKED)],
        issues=[],
        required_check_ids=["regulation"],
    )
    assert report.result is QaResult.BLOCKED_BY_INPUT


def test_missing_mandatory_check_blocks_even_without_issues():
    report = QaReport(
        profile="FINAL",
        scope="model",
        checks=[],
        issues=[],
        required_check_ids=["geometry"],
    )
    assert report.result is QaResult.BLOCKED_BY_INPUT


def test_missing_input_issue_cannot_be_pass():
    report = QaReport(
        profile="STUDY",
        scope="model",
        checks=[check("input", QaCheckStatus.PASS)],
        issues=[
            QaIssue(
                code="MISSING_INPUT_PROGRAM",
                message="required source input is missing",
                severity=Severity.HIGH,
                scope="program",
                mandatory=False,
                evidence={"path": "programa_necessidades.pdf"},
                check_id="input",
            )
        ],
        required_check_ids=["input"],
    )
    assert report.result is QaResult.BLOCKED_BY_INPUT
