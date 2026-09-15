"""Synthetic contract tests for tool trust scoring."""

import pytest

from amanda_agent.tools.trust import (
    TRUST_DIMENSIONS,
    Evidence,
    PromotionDenied,
    TrustEvidence,
    TrustVerdict,
    evaluate_trust,
    promote_trust,
)


def complete_evidence(**overrides: Evidence) -> TrustEvidence:
    values = {
        dimension: Evidence(score=8, status="SUPPORTED", note="synthetic fixture")
        for dimension in TRUST_DIMENSIONS
    }
    values.update(overrides)
    return TrustEvidence(**values)


def test_assessment_scores_every_required_dimension():
    assessment = evaluate_trust(complete_evidence())

    assert set(assessment.dimension_scores) == set(TRUST_DIMENSIONS)
    assert assessment.total_score == 80
    assert assessment.verdict is TrustVerdict.REVIEW_REQUIRED
    assert assessment.automatic_promotion is False


def test_unknown_license_blocks_automatic_promotion():
    assessment = evaluate_trust(
        complete_evidence(license=Evidence.unknown("synthetic unknown licence"))
    )

    assert assessment.verdict is TrustVerdict.REVIEW_REQUIRED
    assert assessment.automatic_promotion is False
    assert any("license" in risk.lower() for risk in assessment.risks)


def test_unsigned_windows_binary_with_source_path_records_risk_without_rejection():
    assessment = evaluate_trust(
        complete_evidence(
            release_provenance_signing_hashes=Evidence(
                score=5, status="UNSIGNED", note="synthetic unsigned Windows artifact"
            )
        ),
        windows_binary=True,
        source_build_available=True,
        provenance_available=True,
    )

    assert assessment.verdict is TrustVerdict.REVIEW_REQUIRED
    assert assessment.rejected is False
    assert any("unsigned" in risk.lower() for risk in assessment.risks)


def test_official_sample_code_is_sample_risk_and_not_production_by_default():
    assessment = evaluate_trust(
        complete_evidence(), official_source=True, sample_code=True
    )

    assert assessment.production_eligible is False
    assert any("sample" in risk.lower() for risk in assessment.risks)
    assert assessment.verdict is TrustVerdict.REVIEW_REQUIRED


def test_promotion_requires_a_deliberate_verdict():
    assessment = evaluate_trust(complete_evidence())

    with pytest.raises(PromotionDenied):
        promote_trust(assessment, tool_lab_validated=True)

    promoted = promote_trust(
        assessment, deliberate=True, tool_lab_validated=True
    )
    assert promoted.verdict is TrustVerdict.PROMOTED

