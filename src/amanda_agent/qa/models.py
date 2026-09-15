"""Typed, deterministic models shared by the QA validators."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Severity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class QaResult(StrEnum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"
    BLOCKED_BY_INPUT = "BLOCKED_BY_INPUT"


class QaCheckStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class QaIssue(BaseModel):
    """One observable QA finding, including its evidence boundary."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    severity: Severity
    scope: str = Field(min_length=1)
    mandatory: bool = False
    evidence: dict[str, Any] | None = None
    check_id: str = Field(min_length=1)
    missing_input: bool = False

    @property
    def is_missing_input(self) -> bool:
        """Return whether this issue indicates an unavailable input boundary."""

        code = self.code.casefold()
        message = self.message.casefold()
        return self.missing_input or (
            ("missing" in code and "input" in code)
            or "missing input" in message
            or code.startswith("input_missing")
        )


class QaCheck(BaseModel):
    """Status of one check, independent of its individual findings."""

    model_config = ConfigDict(extra="forbid")

    check_id: str = Field(min_length=1)
    mandatory: bool = False
    status: QaCheckStatus
    severity_if_failed: Severity = Severity.HIGH
    scope: str = Field(min_length=1)


PROFILE_MANDATORY_CHECKS: dict[str, tuple[str, ...]] = {
    "STUDY": ("program", "model", "architecture", "accessibility"),
    "FINAL": (
        "program",
        "model",
        "architecture",
        "accessibility",
        "ifc",
        "pdf",
        "dwg",
    ),
}


def aggregate_result(
    checks: Iterable[QaCheck],
    issues: Iterable[QaIssue],
    *,
    required_check_ids: Iterable[str] = (),
    profile: str | None = None,
) -> QaResult:
    """Aggregate findings with fail-closed status precedence."""

    check_list = list(checks)
    issue_list = list(issues)
    required = set(required_check_ids)
    if not required and profile is not None:
        required.update(PROFILE_MANDATORY_CHECKS.get(profile.upper(), ()))
    present = {check.check_id for check in check_list}

    if any(issue.severity is Severity.CRITICAL for issue in issue_list):
        return QaResult.FAIL
    if any(issue.is_missing_input for issue in issue_list):
        return QaResult.BLOCKED_BY_INPUT
    if required - present:
        return QaResult.BLOCKED_BY_INPUT
    if any(
        check.mandatory and check.status is QaCheckStatus.FAIL
        for check in check_list
    ):
        return QaResult.FAIL
    if any(
        check.mandatory and check.status in {QaCheckStatus.BLOCKED, QaCheckStatus.SKIPPED}
        for check in check_list
    ):
        return QaResult.BLOCKED_BY_INPUT
    if any(check_id not in present for check_id in required):
        return QaResult.BLOCKED_BY_INPUT
    if any(check.status is QaCheckStatus.FAIL for check in check_list):
        return QaResult.PASS_WITH_WARNINGS
    if issue_list:
        return QaResult.PASS_WITH_WARNINGS
    return QaResult.PASS


class QaReport(BaseModel):
    """A complete QA report whose result is always derived from its contents."""

    model_config = ConfigDict(extra="forbid")

    profile: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    checks: list[QaCheck] = Field(default_factory=list)
    issues: list[QaIssue] = Field(default_factory=list)
    result: QaResult = QaResult.PASS
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    required_check_ids: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def derive_result(self) -> QaReport:
        self.result = aggregate_result(
            self.checks,
            self.issues,
            required_check_ids=self.required_check_ids,
            profile=self.profile,
        )
        return self

    @property
    def metrics(self) -> dict[str, Any]:
        return dict(self.details.get("metrics", {}))

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Serialize with sorted keys so reports can be hashed reproducibly."""

        return json.dumps(
            self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n"


def render_report_markdown(report: QaReport) -> str:
    """Render a compact human-readable report from the typed report."""

    lines = [
        f"# QA report: {report.profile}",
        "",
        f"- Scope: `{report.scope}`",
        f"- Result: **{report.result.value}**",
        f"- Generated at: `{report.generated_at.isoformat()}`",
        "",
        "## Checks",
        "",
        "| Check | Mandatory | Status | Scope |",
        "|---|---:|---|---|",
    ]
    lines.extend(
        f"| `{check.check_id}` | {'yes' if check.mandatory else 'no'} | "
        f"{check.status.value} | {check.scope} |"
        for check in report.checks
    )
    lines.extend(["", "## Issues", ""])
    if report.issues:
        lines.extend(
            f"- `{issue.code}` ({issue.severity.value}): {issue.message} "
            f"[check `{issue.check_id}`]"
            for issue in report.issues
        )
    else:
        lines.append("No issues.")
    return "\n".join(lines) + "\n"


__all__ = [
    "PROFILE_MANDATORY_CHECKS",
    "QaCheck",
    "QaCheckStatus",
    "QaIssue",
    "QaReport",
    "QaResult",
    "Severity",
    "aggregate_result",
    "render_report_markdown",
]
