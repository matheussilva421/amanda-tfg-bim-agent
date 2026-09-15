"""When the agent must stop, and — more importantly — when it must not.

Under AGENT_DELEGATED the agent is authorised to make routine architectural
choices and to proceed on reversible provisional assumptions. Over-asking is
therefore a real failure mode: it stalls the project for decisions that were
already delegated.
"""

import pytest

from amanda_agent.state.human_gate import (
    HumanGateDecision,
    HumanGateReason,
    SelectionAuthority,
    evaluate_gate,
)


def test_delegated_routine_design_choices_never_emit_a_gate():
    delegated = [
        "choose the structural system for the 20-person shelter",
        "select among three researched roof typologies",
        "pick a material palette from the researched options",
        "choose the finalist for the site layout",
        "adopt a provisional STUDY assumption for the missing topography",
        "install a package already approved by the platform permission model",
        "fall back to a previously tested provider",
    ]

    for action in delegated:
        decision = evaluate_gate(action, authority=SelectionAuthority.AGENT_DELEGATED)
        assert decision.required is False, action
        assert decision.reason is None
        assert "AGENT_DELEGATED" in decision.explanation


def test_the_genuinely_human_boundaries_do_raise_a_gate():
    human = {
        "UAC is prompting for elevation to repair the ACLs": HumanGateReason.UAC_APPROVAL,
        "sign in to the Autodesk account with MFA": HumanGateReason.AUTHENTICATION_OR_MFA,
        "validate the Revit licence": HumanGateReason.LICENSE_VALIDATION,
        "buy a paid dataset from the provider": HumanGateReason.EXTERNAL_DATA_OR_COST,
        "publish the release package to the external portal": HumanGateReason.IRREVERSIBLE_EXTERNAL_ACTION,
        "kill the Revit process that holds unsaved user work": HumanGateReason.USER_WORK_AT_RISK,
    }

    for action, reason in human.items():
        decision = evaluate_gate(action, authority=SelectionAuthority.AGENT_DELEGATED)
        assert decision.required is True, action
        assert decision.reason is reason


def test_architectural_selection_is_disabled_as_a_waiting_gate_under_delegation():
    """Amanda may review afterwards; that must not become a blocking gate now."""
    decision = evaluate_gate(
        "Amanda should approve the facade composition before it is modelled",
        authority=SelectionAuthority.AGENT_DELEGATED,
    )

    assert decision.required is False
    assert decision.reason is not HumanGateReason.ARCHITECTURAL_SELECTION


def test_architectural_selection_becomes_a_gate_only_if_the_user_takes_it_back():
    decision = evaluate_gate(
        "approve the facade composition before modelling",
        authority=SelectionAuthority.USER_REQUESTED_PAUSE,
    )

    assert decision.required is True
    assert decision.reason is HumanGateReason.ARCHITECTURAL_SELECTION


def test_essential_source_data_is_a_last_resort_not_a_first_response():
    """It must demand the study alternative was exhausted, not merely tried."""
    premature = evaluate_gate(
        "essential source data: the survey elevation is missing",
        authority=SelectionAuthority.AGENT_DELEGATED,
        provisional_study_possible=True,
        research_exhausted=False,
    )
    exhausted = evaluate_gate(
        "essential source data: the survey elevation is missing",
        authority=SelectionAuthority.AGENT_DELEGATED,
        provisional_study_possible=False,
        research_exhausted=True,
    )

    assert premature.required is False, "a reversible STUDY path still exists"
    assert exhausted.required is True
    assert exhausted.reason is HumanGateReason.ESSENTIAL_SOURCE_DATA


def test_the_program_baseline_is_no_longer_asked_about():
    decision = evaluate_gate(
        "confirm the 20-person program baseline of 626 m2 internal",
        authority=SelectionAuthority.AGENT_DELEGATED,
    )

    assert decision.required is False, "the baseline is already resolved"


def test_a_material_change_to_the_selected_brief_is_still_escalated():
    decision = evaluate_gate(
        "materially change the selected 20-person brief to 42 residents",
        authority=SelectionAuthority.AGENT_DELEGATED,
    )

    assert decision.required is True
    assert decision.reason is HumanGateReason.PROGRAM_BASELINE


def test_a_gate_always_says_what_the_user_must_do_and_what_continues():
    decision = evaluate_gate(
        "sign in to Autodesk with MFA to license Revit",
        authority=SelectionAuthority.AGENT_DELEGATED,
    )

    assert decision.required is True
    assert decision.action.strip(), "a gate without an action is a stall"
    assert decision.blocked_work, "the gate must name what it blocks"
    assert decision.allowed_work, "the gate must name what may still proceed"
    assert "PHASE_02" in " ".join(decision.blocked_work)
    assert any("PHASE_03" in item for item in decision.allowed_work)


def test_blocked_work_is_never_left_ambiguous_when_nothing_is_blocked():
    decision = evaluate_gate("choose a roof typology", authority=SelectionAuthority.AGENT_DELEGATED)

    assert decision.blocked_work == []
    assert decision.allowed_work == []


def test_an_unknown_authority_value_is_refused():
    with pytest.raises(ValueError):
        evaluate_gate("choose a roof", authority="SOMEBODY_ELSE_DECIDES")


def test_the_decision_serialises_for_the_blocker_registry():
    decision = evaluate_gate(
        "validate the Revit licence", authority=SelectionAuthority.AGENT_DELEGATED
    )

    payload = decision.as_blocker()

    assert payload["severity"] == "BLOCKING"
    assert payload["reason"] == "LICENSE_VALIDATION"
    assert payload["affected_tasks"] == list(decision.blocked_work)
    assert payload["resolution_action"] == decision.action
