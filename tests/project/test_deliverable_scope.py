"""Project-level contracts for academic deliverables and delegated decisions."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
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
    load_decision_register,
)
from amanda_agent.requirements.regulations import (
    RegulationRule,
    RegulationStatus,
    compile_derived_constraint,
)

ROOT = Path(__file__).resolve().parents[2]
DELIVERABLES_PATH = ROOT / "project" / "requirements" / "academic-deliverables.yaml"
DECISIONS_PATH = ROOT / "project" / "requirements" / "decisions.yaml"


EXPECTED_DELIVERABLE_IDS = {
    "academic-caderno-revision",
    "academic-visits",
    "academic-metaprojeto",
    "academic-preliminary-study",
    "academic-anteprojeto",
    "academic-pranchas",
    "academic-descriptive-memorial",
    "academic-calculation-memorial",
    "academic-defense",
    "academic-authorship",
    "academic-institutional-submission",
}


def _load_scope() -> AcademicDeliverableScope:
    payload = yaml.safe_load(DELIVERABLES_PATH.read_text(encoding="utf-8"))
    return AcademicDeliverableScope.model_validate(payload)


def _delegated_record(**overrides: object) -> DecisionRecord:
    values: dict[str, object] = {
        "decision_id": "DEC-P03-T15-TEST-001",
        "topic": "SITE_BOUNDARY",
        "alternatives": [
            "VERIFIED_BOUNDARY_PENDING",
            "PROVISIONAL_ASSUMPTION: study boundary",
        ],
        "selected_option": "PROVISIONAL_ASSUMPTION: study boundary",
        "rationale": "A verified boundary is unavailable for this study scenario.",
        "source_refs": ["SRC-TEST-001#page-1"],
        "confidence": 0.3,
        "affected_requirements": [
            "project/site/site.json@v1",
            "bim/desired-state.json@v1",
            "deliverables/study-export@v1",
        ],
        "selection_authority": SelectionAuthority.AGENT_DELEGATED,
        "timestamp": "2026-09-15",
        "validation_status": ValidationStatus.PENDING_VERIFICATION,
        "revision_procedure": "Append a revision and preserve this record.",
        "review_status": ReviewStatus.AMANDA_REVIEW_PENDING,
        "fact_class": FactClass.DESIGN_HYPOTHESIS,
        "scenario": DecisionScenario.STUDY,
        "selection_kind": SelectionKind.PROVISIONAL_ASSUMPTION,
        "verification_required": True,
    }
    values.update(overrides)
    return DecisionRecord(**values)


def test_academic_deliverables_yaml_loads_and_preserves_human_boundary():
    scope = _load_scope()

    assert {item.deliverable_id for item in scope.deliverables} == EXPECTED_DELIVERABLE_IDS
    assert all(item.owner == "Amanda" for item in scope.deliverables)
    assert all(item.source_refs for item in scope.deliverables)
    assert all(item.evidence == [] for item in scope.deliverables)
    assert all(item.date is None for item in scope.deliverables)
    assert {
        item.production_role for item in scope.deliverables
    } <= {
        "BIM_GENERATED_WITH_HUMAN_VALIDATION",
        "HUMAN_AUTHORED_VALIDATED",
        "HUMAN_REQUIRED",
    }
    assert all(item.requires_human_action for item in scope.deliverables)
    assert all(item.required_for_tfg_complete for item in scope.deliverables)

    boards = scope.get("academic-pranchas")
    assert boards.status == "PROVISIONAL"
    assert boards.expected_quantity == "4-6 A1"
    assert boards.date is None
    assert "institutional regulation" in boards.status_reason

    for deliverable_id in (
        "academic-visits",
        "academic-defense",
        "academic-authorship",
        "academic-institutional-submission",
    ):
        assert scope.get(deliverable_id).production_role == "HUMAN_REQUIRED"


def test_unresolved_required_academic_work_blocks_tfg_complete_but_allows_study():
    scope = _load_scope()

    assert scope.can_claim_tfg_complete is False
    assert scope.can_release(DecisionScenario.STUDY) is True
    assert scope.can_release(DecisionScenario.FINAL) is False
    assert any("academic-visits" in reason for reason in scope.final_blocked_reasons)


def test_unverified_data_is_a_study_hypothesis_and_never_verified():
    decision = _delegated_record()

    assert decision.selection_authority is SelectionAuthority.AGENT_DELEGATED
    assert decision.fact_class is FactClass.DESIGN_HYPOTHESIS
    assert decision.selection_kind is SelectionKind.PROVISIONAL_ASSUMPTION
    assert decision.scenario is DecisionScenario.STUDY
    assert decision.validation_status is not ValidationStatus.VERIFIED
    assert decision.can_execute is True

    invalid_promotion = decision.model_dump()
    invalid_promotion["validation_status"] = ValidationStatus.VERIFIED
    with pytest.raises(ValidationError, match="cannot have validation_status VERIFIED"):
        DecisionRecord(**invalid_promotion)


def test_numeric_rule_from_unverified_source_cannot_be_a_verified_hard_constraint():
    rule = RegulationRule(
        logical_id="LC-208-unverified-numeric-claim",
        title="Unverified setback claim",
        status=RegulationStatus.SOURCE_ACQUIRED,
        primary_source="secondary-reference.docx",
        source_version="unverified-copy",
        source_date="2026-09-15",
        article="unknown",
        map_reference="unknown",
        extracted_rule="A secondary reference claims a numeric setback.",
        numeric_value=1.5,
        unit="m",
        scope="study placeholder",
        source_refs=["secondary-reference.docx#ATENDE"],
    )

    with pytest.raises(ValueError, match="status VERIFIED"):
        compile_derived_constraint(rule)


def test_decisions_yaml_loads_delegated_baseline_with_derived_hash():
    register = load_decision_register(DECISIONS_PATH)

    assert isinstance(register, DecisionRegister)
    assert register.decisions
    assert all(
        decision.selection_authority is SelectionAuthority.AGENT_DELEGATED
        for decision in register.decisions
    )
    assert all(decision.approval_hash_valid for decision in register.decisions)

    baseline = register.for_topic("PROGRAM_BASELINE")
    assert baseline.selected_option == "20 pessoas, conforme programa_necessidades.pdf"
    assert baseline.adoption_status == "ACCEPTED"
    assert baseline.source_sha256 == (
        "11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17"
    )
    assert "42 pessoas" in " ".join(baseline.rejected_options)
    assert baseline.rationale


def test_replacing_an_assumption_propagates_targets_and_preserves_prior_version():
    original = _delegated_record()
    register = DecisionRegister(decisions=[original])

    revised = register.create_revision(
        original.decision_id,
        selected_option="VERIFIED_BOUNDARY: surveyed polygon",
        rationale="A later survey replaces the study boundary assumption.",
        validation_status=ValidationStatus.VERIFIED,
        fact_class=FactClass.SOURCE_FACT,
        selection_kind=SelectionKind.EVIDENCE_BACKED,
        scenario=DecisionScenario.STUDY,
    )

    assert revised.supersedes == original.decision_id
    assert revised.affected_requirements == original.affected_requirements
    assert set(revised.affected_requirements) == {
        "project/site/site.json@v1",
        "bim/desired-state.json@v1",
        "deliverables/study-export@v1",
    }
    assert revised.approval_hash_valid is True
    assert revised.is_approval_hash_valid(original.approval_hash) is False
    assert register.get(original.decision_id).selected_option == original.selected_option
    assert register.get(original.decision_id).review_status is ReviewStatus.SUPERSEDED


def test_amanda_feedback_creates_revision_and_supersedes_original_without_overwrite():
    original = _delegated_record(
        selected_option="PROVISIONAL_ASSUMPTION: courtyard access",
        rationale="The delegated study choice is reversible.",
    )
    register = DecisionRegister(decisions=[original])
    old_hash = original.approval_hash

    revised = register.create_revision(
        original.decision_id,
        selected_option="Amanda feedback: street access",
        rationale="Amanda's feedback takes precedence over the delegated choice.",
        review_status=ReviewStatus.AMANDA_ACCEPTED,
    )

    assert revised.decision_id != original.decision_id
    assert revised.supersedes == original.decision_id
    assert revised.review_status is ReviewStatus.AMANDA_ACCEPTED
    assert revised.approval_hash != old_hash
    assert revised.is_approval_hash_valid(old_hash) is False
    assert register.get(original.decision_id).approval_hash == old_hash
    assert register.get(original.decision_id).validation_status is ValidationStatus.SUPERSEDED
    assert register.get(original.decision_id).review_status is ReviewStatus.SUPERSEDED
