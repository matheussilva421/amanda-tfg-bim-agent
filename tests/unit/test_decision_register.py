"""Behavioral contracts for delegated decisions and academic scope."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from amanda_agent.requirements.decisions import (
    AcademicDeliverableScope,
    DecisionRecord,
    DecisionRegister,
    DecisionScenario,
    FactClass,
    ReviewStatus,
    SelectionAuthority,
    SelectionKind,
    ValidationStatus,
    build_academic_deliverable_scope,
    compute_approval_hash,
    load_decision_register,
)


def _record(**overrides: object) -> DecisionRecord:
    values: dict[str, object] = {
        "decision_id": "DEC-TEST-001",
        "topic": "TYPOLOGY",
        "alternatives": ["option-a", "option-b"],
        "selected_option": "option-a",
        "rationale": "The selected option is supported by the recorded evidence.",
        "source_refs": ["SRC-TEST-001#page-1"],
        "confidence": 0.8,
        "affected_requirements": ["project/requirements/program.json", "REQ-TEST-1"],
        "selection_authority": SelectionAuthority.AGENT_DELEGATED,
        "timestamp": "2026-09-15T12:00:00Z",
        "approval_hash": "placeholder",
        "validation_status": ValidationStatus.VERIFIED,
        "revision_procedure": "Create a new record and supersede the old one.",
        "review_status": ReviewStatus.AMANDA_REVIEW_PENDING,
    }
    values.update(overrides)
    values["approval_hash"] = compute_approval_hash(
        selected_option=values["selected_option"],
        rationale=values["rationale"],
        source_refs=values["source_refs"],
        affected_requirements=values["affected_requirements"],
    )
    return DecisionRecord(**values)


def test_delegated_evidence_backed_decision_has_deterministic_valid_hash():
    record = _record()

    assert record.selection_authority is SelectionAuthority.AGENT_DELEGATED
    assert record.can_execute is True
    assert record.approval_hash_valid is True
    assert record.approval_hash == (
        "3bd467400234e9546761a6bfa3a765f65d897ad496f8abcbda89c9435e4b1613"
    )


def test_hash_is_derived_when_omitted_and_stale_hash_is_rejected():
    original = _record()
    values = original.model_dump()
    values.pop("approval_hash")

    derived = DecisionRecord(**values)
    assert derived.approval_hash == original.approval_hash

    values.update(
        {
            "selected_option": "option-b",
            "approval_hash": original.approval_hash,
        }
    )
    with pytest.raises(ValidationError, match="approval_hash"):
        DecisionRecord(**values)


def test_amanda_review_pending_does_not_block_and_acceptance_is_recordable():
    register = DecisionRegister(decisions=[_record()])

    assert register.can_execute("DEC-TEST-001") is True
    accepted = register.accept_amanda("DEC-TEST-001")

    assert accepted.review_status is ReviewStatus.AMANDA_ACCEPTED
    assert register.get("DEC-TEST-001").review_status is ReviewStatus.AMANDA_ACCEPTED
    assert accepted.approval_hash_valid is True


def test_amanda_feedback_creates_new_revision_and_old_hash_cannot_validate_it():
    original = _record()
    register = DecisionRegister(decisions=[original])

    revised = register.create_revision(
        "DEC-TEST-001",
        selected_option="option-b",
        rationale="Amanda feedback changes the selected option.",
    )

    assert revised.decision_id != original.decision_id
    assert revised.supersedes == original.decision_id
    assert revised.approval_hash != original.approval_hash
    assert revised.approval_hash_valid is True
    assert revised.is_approval_hash_valid(original.approval_hash) is False
    assert register.get(original.decision_id).review_status is ReviewStatus.SUPERSEDED
    assert register.can_proceed(DecisionScenario.STUDY) is True


def test_provisional_assumption_is_restricted_to_study_design_hypothesis():
    provisional = _record(
        selected_option="PROVISIONAL_ASSUMPTION: planar study placeholder",
        selection_kind=SelectionKind.PROVISIONAL_ASSUMPTION,
        fact_class=FactClass.DESIGN_HYPOTHESIS,
        scenario=DecisionScenario.STUDY,
        validation_status=ValidationStatus.PENDING_VERIFICATION,
        verification_required=True,
    )

    assert provisional.can_execute is True
    assert provisional.fact_class is FactClass.DESIGN_HYPOTHESIS
    assert provisional.validation_status is ValidationStatus.PENDING_VERIFICATION

    invalid_fact_class = {
        "selected_option": "PROVISIONAL_ASSUMPTION: unverified value",
        "selection_kind": SelectionKind.PROVISIONAL_ASSUMPTION,
        "fact_class": FactClass.SOURCE_FACT,
        "scenario": DecisionScenario.STUDY,
        "validation_status": ValidationStatus.PENDING_VERIFICATION,
    }
    with pytest.raises(ValidationError, match="DESIGN_HYPOTHESIS"):
        _record(**invalid_fact_class)

    invalid_scenario = {
        "selected_option": "PROVISIONAL_ASSUMPTION: unverified value",
        "selection_kind": SelectionKind.PROVISIONAL_ASSUMPTION,
        "fact_class": FactClass.DESIGN_HYPOTHESIS,
        "scenario": DecisionScenario.FINAL,
        "validation_status": ValidationStatus.PENDING_VERIFICATION,
    }
    with pytest.raises(ValidationError, match="STUDY"):
        _record(**invalid_scenario)

    invalid_validation = {
        "selected_option": "PROVISIONAL_ASSUMPTION: unverified value",
        "selection_kind": SelectionKind.PROVISIONAL_ASSUMPTION,
        "fact_class": FactClass.DESIGN_HYPOTHESIS,
        "scenario": DecisionScenario.STUDY,
        "validation_status": ValidationStatus.VERIFIED,
    }
    with pytest.raises(ValidationError, match="VERIFIED"):
        _record(**invalid_validation)


def test_study_can_proceed_while_final_exposes_pending_verification_reasons():
    register = DecisionRegister(
        decisions=[
            _record(
                selected_option="PROVISIONAL_ASSUMPTION: missing survey",
                selection_kind=SelectionKind.PROVISIONAL_ASSUMPTION,
                fact_class=FactClass.DESIGN_HYPOTHESIS,
                scenario=DecisionScenario.STUDY,
                validation_status=ValidationStatus.PENDING_VERIFICATION,
                verification_required=True,
            )
        ]
    )

    assert register.can_proceed(DecisionScenario.STUDY) is True
    assert register.can_proceed(DecisionScenario.FINAL) is False
    assert register.final_blocked_reasons
    assert "DEC-TEST-001" in " ".join(register.final_blocked_reasons)


def test_academic_scope_keeps_mandatory_work_out_of_tfg_complete():
    scope = build_academic_deliverable_scope()

    assert isinstance(scope, AcademicDeliverableScope)
    assert scope.can_release(DecisionScenario.STUDY) is True
    assert scope.can_claim_tfg_complete is False
    assert scope.final_blocked_reasons
    assert any("visits" in reason for reason in scope.final_blocked_reasons)

    boards = scope.get("academic-pranchas")
    assert boards.status == "PROVISIONAL"
    assert boards.expected_quantity == "4-6 A1"
    assert boards.date is None
    assert "regulation" in boards.status_reason
    assert boards.production_role == "HUMAN_AUTHORED_VALIDATED"
    assert boards.requires_human_action is True


def test_yaml_register_contains_project_and_canonical_topics_and_academic_scope():
    root = Path(__file__).parents[2]
    register = load_decision_register(
        root / "project" / "requirements" / "decision-register.yaml"
    )

    topics = {decision.topic for decision in register.decisions}
    assert topics == {
        "TYPOLOGY",
        "PROGRAM_BASELINE",
        "SITE_BOUNDARY",
        "SITE_OCCUPANCY",
        "SITE_TOPOGRAPHY",
        "REGULATION_APPLICABILITY",
        "CANONICAL_SOLUTION_SUPERSESSION",
        "USER_DIRECTED_CANONICAL_PARTI",
        "CANONICAL_PARTI_IMPLEMENTATION",
    }
    assert all(decision.approval_hash_valid for decision in register.decisions)

    baseline = register.for_topic("PROGRAM_BASELINE")
    assert baseline.selected_option == "20 pessoas, conforme programa_necessidades.pdf"
    assert baseline.adoption_status == "ACCEPTED"
    assert baseline.source_sha256 == (
        "11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17"
    )
    assert any("42 pessoas" in option for option in baseline.rejected_options)
    assert baseline.review_status is ReviewStatus.AMANDA_REVIEW_PENDING
    assert register.academic_scope.get("academic-pranchas").date is None
