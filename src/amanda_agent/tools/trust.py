"""Evidence scoring for discovered tools.

The module deliberately models evidence without making claims about a real
third-party tool.  A score is a review input, not an automatic production
approval.  Tool Lab validation and an explicit promotion decision remain
separate gates.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum
from math import isfinite
from collections.abc import Mapping
from typing import Any


TRUST_DIMENSIONS: tuple[str, ...] = (
    "maintainer_source_reputation",
    "recency_maintenance",
    "license",
    "revit_codex_compatibility",
    "tests_ci",
    "issue_quality",
    "release_provenance_signing_hashes",
    "security_docs",
    "api_write_scope",
)

_UNKNOWN_STATUSES = frozenset({"UNKNOWN", "UNVERIFIED", "MISSING"})


class TrustVerdict(StrEnum):
    """State of the trust review, independent of discovery."""

    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"
    PROMOTED = "PROMOTED"


class PromotionDenied(RuntimeError):
    """Raised when a caller tries to promote without the required gate."""


@dataclass(frozen=True)
class Evidence:
    """One synthetic or observed evidence item.

    Scores are on a zero-to-ten scale.  ``None`` explicitly means that the
    dimension is unknown and must not be treated as a passing score.
    """

    score: float | None
    status: str = "SUPPORTED"
    note: str = ""

    def __post_init__(self) -> None:
        if self.score is not None:
            value = float(self.score)
            if not isfinite(value) or not 0 <= value <= 10:
                raise ValueError("evidence score must be between 0 and 10")
            object.__setattr__(self, "score", value)
        normalized = str(self.status).strip().upper()
        if not normalized:
            raise ValueError("evidence status cannot be blank")
        object.__setattr__(self, "status", normalized)

    @classmethod
    def unknown(cls, note: str = "") -> "Evidence":
        return cls(score=None, status="UNKNOWN", note=note)

    @property
    def is_unknown(self) -> bool:
        return self.score is None or self.status in _UNKNOWN_STATUSES


def _unknown_evidence() -> Evidence:
    return Evidence.unknown()


@dataclass(frozen=True)
class TrustEvidence:
    """Evidence inputs for all nine trust dimensions."""

    maintainer_source_reputation: Evidence = field(default_factory=_unknown_evidence)
    recency_maintenance: Evidence = field(default_factory=_unknown_evidence)
    license: Evidence = field(default_factory=_unknown_evidence)
    revit_codex_compatibility: Evidence = field(default_factory=_unknown_evidence)
    tests_ci: Evidence = field(default_factory=_unknown_evidence)
    issue_quality: Evidence = field(default_factory=_unknown_evidence)
    release_provenance_signing_hashes: Evidence = field(
        default_factory=_unknown_evidence
    )
    security_docs: Evidence = field(default_factory=_unknown_evidence)
    api_write_scope: Evidence = field(default_factory=_unknown_evidence)
    windows_binary: bool = False
    source_build_available: bool = False
    provenance_available: bool = False
    binary_signed: bool | None = None
    official_source: bool = False
    sample_code: bool = False

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "TrustEvidence":
        """Build a fixture-friendly typed record from a mapping.

        A numeric dimension is accepted as shorthand for supported evidence;
        mappings are accepted for the full ``Evidence`` shape.
        """
        payload = dict(values)
        for dimension in TRUST_DIMENSIONS:
            if dimension not in payload:
                continue
            item = payload[dimension]
            if isinstance(item, Evidence):
                continue
            if isinstance(item, Mapping):
                payload[dimension] = Evidence(**dict(item))
            else:
                payload[dimension] = Evidence(score=item)
        return cls(**payload)

    @property
    def dimensions(self) -> dict[str, Evidence]:
        return {dimension: getattr(self, dimension) for dimension in TRUST_DIMENSIONS}

    @property
    def unknown_license(self) -> bool:
        return self.license.is_unknown

    @property
    def unsigned_windows_binary(self) -> bool:
        status = self.release_provenance_signing_hashes.status
        return self.windows_binary and (
            self.binary_signed is False or "UNSIGNED" in status
        )


@dataclass(frozen=True)
class TrustAssessment:
    """The score and explicit review gates produced from trust evidence."""

    dimension_scores: dict[str, float]
    total_score: float
    risks: tuple[str, ...] = ()
    verdict: TrustVerdict = TrustVerdict.REVIEW_REQUIRED
    automatic_promotion: bool = False
    production_eligible: bool = False
    rejected: bool = False
    evidence: TrustEvidence | None = None


def _coerce_evidence(evidence: TrustEvidence | Mapping[str, Any]) -> TrustEvidence:
    if isinstance(evidence, TrustEvidence):
        return evidence
    if isinstance(evidence, Mapping):
        return TrustEvidence.from_mapping(evidence)
    raise TypeError("trust evidence must be TrustEvidence or a mapping")


def evaluate_trust(
    evidence: TrustEvidence | Mapping[str, Any],
    *,
    windows_binary: bool | None = None,
    source_build_available: bool | None = None,
    provenance_available: bool | None = None,
    official_source: bool | None = None,
    sample_code: bool | None = None,
) -> TrustAssessment:
    """Score every trust dimension and return a non-promoting assessment."""
    typed = _coerce_evidence(evidence)
    if any(value is not None for value in (
        windows_binary,
        source_build_available,
        provenance_available,
        official_source,
        sample_code,
    )):
        typed = replace(
            typed,
            **{
                key: value
                for key, value in {
                    "windows_binary": windows_binary,
                    "source_build_available": source_build_available,
                    "provenance_available": provenance_available,
                    "official_source": official_source,
                    "sample_code": sample_code,
                }.items()
                if value is not None
            },
        )

    dimension_scores = {
        dimension: item.score if item.score is not None else 0.0
        for dimension, item in typed.dimensions.items()
    }
    total_score = round(
        sum(dimension_scores.values()) / len(TRUST_DIMENSIONS) * 10, 2
    )
    risks: list[str] = []
    rejected = False

    if typed.unknown_license:
        risks.append("license evidence is UNKNOWN; automatic promotion is blocked")

    if typed.unsigned_windows_binary:
        risks.append("unsigned Windows binary risk is recorded")
        if not (typed.source_build_available or typed.provenance_available):
            rejected = True
            risks.append(
                "unsigned Windows binary has no source-build path or provenance"
            )
        else:
            risks.append(
                "source-build path or provenance is available for the unsigned artifact"
            )

    sample_risk = typed.sample_code and typed.official_source
    if sample_risk:
        risks.append("official source is sample code; sample risk applies")

    if rejected:
        verdict = TrustVerdict.REJECTED
    else:
        verdict = TrustVerdict.REVIEW_REQUIRED

    production_eligible = not rejected and not typed.unknown_license and not sample_risk
    return TrustAssessment(
        dimension_scores=dimension_scores,
        total_score=total_score,
        risks=tuple(risks),
        verdict=verdict,
        automatic_promotion=False,
        production_eligible=production_eligible,
        rejected=rejected,
        evidence=typed,
    )


def promote_trust(
    assessment: TrustAssessment,
    *,
    deliberate: bool = False,
    tool_lab_validated: bool = False,
) -> TrustAssessment:
    """Promote only after an explicit verdict and Tool Lab validation."""
    if not deliberate:
        raise PromotionDenied("promotion requires deliberate=True")
    if not tool_lab_validated:
        raise PromotionDenied("promotion requires Tool Lab validation")
    if assessment.rejected or not assessment.production_eligible:
        raise PromotionDenied("assessment contains an unresolved promotion risk")
    return replace(assessment, verdict=TrustVerdict.PROMOTED)


# Descriptive aliases keep the public policy surface discoverable for callers.
score_trust = evaluate_trust


__all__ = [
    "TRUST_DIMENSIONS",
    "Evidence",
    "PromotionDenied",
    "TrustAssessment",
    "TrustEvidence",
    "TrustVerdict",
    "evaluate_trust",
    "promote_trust",
    "score_trust",
]

