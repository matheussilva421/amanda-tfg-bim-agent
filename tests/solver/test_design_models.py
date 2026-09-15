from __future__ import annotations

import pytest
from pydantic import ValidationError

from amanda_agent.design.models import (
    ConstraintViolation,
    DesignSolution,
    DesignStatus,
    MetricSet,
)
from amanda_agent.requirements.decisions import (
    DecisionRecord,
    DecisionScenario,
    FactClass,
    ReviewStatus,
    SelectionAuthority,
    ValidationStatus,
    compute_approval_hash,
)


def _decision(solution_id: str = "sol-01") -> DecisionRecord:
    selected = f"{solution_id}:COURTYARD"
    rationale = "Synthetic delegated design candidate"
    refs = ["requirements-v1", "site-v1"]
    affected = [solution_id, "program-person-capacity=20"]
    return DecisionRecord(
        decision_id="decision-01",
        topic="design-selection",
        alternatives=["COURTYARD", "LINEAR_SPINE"],
        selected_option=selected,
        rationale=rationale,
        source_refs=refs,
        confidence=0.9,
        affected_requirements=affected,
        selection_authority=SelectionAuthority.AGENT_DELEGATED,
        timestamp="2026-09-15T00:00:00Z",
        approval_hash=compute_approval_hash(
            selected_option=selected,
            rationale=rationale,
            source_refs=refs,
            affected_requirements=affected,
        ),
        validation_status=ValidationStatus.VERIFIED,
        revision_procedure="Create a new decision revision",
        review_status=ReviewStatus.AMANDA_REVIEW_PENDING,
        fact_class=FactClass.SOURCE_FACT,
        scenario=DecisionScenario.STUDY,
    )


def _solution(**overrides: object) -> DesignSolution:
    values: dict[str, object] = {
        "solution_id": "sol-01",
        "run_id": "run-01",
        "seed": 42,
        "requirements_version": "requirements-v1",
        "site_version": "site-v1",
        "engine_version": "design-engine-v1",
        "archetype": "COURTYARD",
        "geometry": {"sectors": [], "rooms": []},
        "metrics": MetricSet(program_compliance=1.0, privacy_security=0.8),
        "hard_violations": [],
        "soft_penalties": {"adjacency": 1.5},
        "parents": [],
        "status": DesignStatus.AMANDA_REVIEW_PENDING,
        "selection_authority": SelectionAuthority.AGENT_DELEGATED,
        "decision_evidence": _decision(),
    }
    values.update(overrides)
    return DesignSolution(**values)


def test_design_solution_json_round_trip_preserves_required_contract():
    solution = _solution()

    restored = DesignSolution.model_validate_json(solution.model_dump_json())

    assert restored == solution
    assert restored.seed == 42
    assert restored.metrics.program_compliance == pytest.approx(1.0)


def test_approved_for_bim_requires_explicit_content_bound_delegated_evidence():
    solution = _solution(
        status=DesignStatus.APPROVED_FOR_BIM,
        approval_hash=None,
    )

    assert solution.bim_eligible is True
    assert solution.status is DesignStatus.APPROVED_FOR_BIM


def test_approved_for_bim_is_not_a_default_status():
    values = _solution().model_dump(exclude={"status"})

    with pytest.raises(ValidationError, match="status"):
        DesignSolution(**values)


def test_amanda_review_pending_does_not_block_delegated_bim_work():
    solution = _solution(status=DesignStatus.AMANDA_REVIEW_PENDING)

    assert solution.bim_eligible is True


def test_changed_content_after_copy_is_no_longer_bim_eligible():
    solution = _solution()
    changed = solution.model_copy(update={"geometry": {"sectors": ["changed"]}})

    assert changed.bim_eligible is False


def test_personal_approval_claim_and_non_twenty_program_are_rejected():
    with pytest.raises(ValidationError, match="personal Amanda approval"):
        _solution(amanda_approved=True)

    with pytest.raises(ValidationError, match="20"):
        _solution(program_person_capacity=42)

    with pytest.raises(ValidationError, match="20"):
        _solution(geometry={"program": {"person_capacity": 42}})


def test_hard_violation_cannot_become_a_numeric_soft_penalty():
    violation = ConstraintViolation(
        code="outside_site",
        message="Room is outside the buildable site",
        severity="HARD",
    )

    with pytest.raises(ValueError, match="soft penalty"):
        violation.as_soft_penalty()
