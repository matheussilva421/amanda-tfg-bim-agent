"""Typed discovery records and the Tool Lab promotion boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Any

REQUIRED_REPORT_FIELDS: tuple[str, ...] = (
    "repository_url",
    "commit_or_tag",
    "license",
    "build_method",
    "install_effects",
    "network_behavior",
    "revit_support",
    "mcp_codex_support",
    "rollback",
    "risk_score",
    "exact_capability",
)


class DiscoveryReportError(ValueError):
    """A discovery report is incomplete or invalid."""


class ToolLabRequiredError(PermissionError):
    """A candidate tried to cross the production boundary without the Lab."""


@dataclass(frozen=True)
class ToolDiscoveryReport:
    """The complete, reviewable record for one discovered candidate."""

    repository_url: str
    commit_or_tag: str
    license: str
    build_method: str
    install_effects: str
    network_behavior: str
    revit_support: str
    mcp_codex_support: str
    rollback: str
    risk_score: float
    exact_capability: str

    def __post_init__(self) -> None:
        for field_name in REQUIRED_REPORT_FIELDS:
            value = getattr(self, field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise DiscoveryReportError(
                    "required discovery field is missing or blank: " + field_name
                )
        value = float(self.risk_score)
        if not isfinite(value) or not 0 <= value <= 100:
            raise DiscoveryReportError("risk_score must be between 0 and 100")
        object.__setattr__(self, "risk_score", value)

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> ToolDiscoveryReport:
        if not isinstance(values, Mapping):
            raise DiscoveryReportError("discovery report must be a mapping")
        missing = [field for field in REQUIRED_REPORT_FIELDS if field not in values]
        if missing:
            raise DiscoveryReportError(
                "missing required discovery field(s): " + ", ".join(missing)
            )
        try:
            return cls(**{field: values[field] for field in REQUIRED_REPORT_FIELDS})
        except (TypeError, ValueError) as exc:
            if isinstance(exc, DiscoveryReportError):
                raise
            raise DiscoveryReportError(str(exc)) from exc

    def as_dict(self) -> dict[str, Any]:
        return {field: getattr(self, field) for field in REQUIRED_REPORT_FIELDS}


DiscoveryReport = ToolDiscoveryReport


@dataclass(frozen=True)
class ToolLabSubmission:
    """A candidate handoff to the isolated Tool Lab."""

    report: ToolDiscoveryReport


@dataclass(frozen=True)
class DiscoveryCandidate:
    """A discovered candidate with no direct production installation path."""

    report: ToolDiscoveryReport

    def submit_to_tool_lab(self) -> ToolLabSubmission:
        return ToolLabSubmission(report=self.report)

    def install_to_production(self) -> None:
        """Fail closed; only a passed Tool Lab validation creates a plan."""
        raise ToolLabRequiredError(
            "discovery candidates must pass through the Tool Lab first"
        )


@dataclass(frozen=True)
class ToolLabValidation:
    """A recorded result for a Tool Lab submission."""

    submission: ToolLabSubmission
    result: str
    evidence_ref: str

    def __post_init__(self) -> None:
        result = str(self.result).strip().upper()
        if result != "PASS":
            raise ToolLabRequiredError("only a PASS result can leave the Tool Lab")
        if not self.evidence_ref or not str(self.evidence_ref).strip():
            raise DiscoveryReportError("Tool Lab evidence_ref cannot be blank")
        object.__setattr__(self, "result", result)

    @classmethod
    def from_submission(
        cls,
        submission: ToolLabSubmission,
        *,
        result: str,
        evidence_ref: str,
    ) -> ToolLabValidation:
        return cls(
            submission=submission,
            result=result,
            evidence_ref=evidence_ref,
        )

    @property
    def passed(self) -> bool:
        return self.result == "PASS"


_PRODUCTION_PLAN_TOKEN = object()


@dataclass(frozen=True, init=False)
class ProductionInstallPlan:
    """A production intent that can only be minted from Tool Lab validation."""

    report: ToolDiscoveryReport
    tool_lab_evidence: str

    def __init__(
        self,
        report: ToolDiscoveryReport,
        tool_lab_evidence: str,
        *,
        _token: object | None = None,
    ) -> None:
        if _token is not _PRODUCTION_PLAN_TOKEN:
            raise ToolLabRequiredError(
                "production install plans require Tool Lab validation"
            )
        object.__setattr__(self, "report", report)
        object.__setattr__(self, "tool_lab_evidence", tool_lab_evidence)

    @classmethod
    def from_tool_lab_validation(
        cls, validation: ToolLabValidation
    ) -> ProductionInstallPlan:
        if not validation.passed:
            raise ToolLabRequiredError("Tool Lab validation did not pass")
        return cls(
            validation.submission.report,
            validation.evidence_ref,
            _token=_PRODUCTION_PLAN_TOKEN,
        )


__all__ = [
    "REQUIRED_REPORT_FIELDS",
    "DiscoveryCandidate",
    "DiscoveryReport",
    "DiscoveryReportError",
    "ProductionInstallPlan",
    "ToolDiscoveryReport",
    "ToolLabRequiredError",
    "ToolLabSubmission",
    "ToolLabValidation",
]
