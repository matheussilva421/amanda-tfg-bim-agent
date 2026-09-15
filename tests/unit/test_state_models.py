import yaml

from amanda_agent.models.state import PhaseGate, ProjectState, TaskStatus


def test_default_state_is_pending_foundation():
    state = ProjectState()
    assert state.phase_id == "PHASE_01"
    assert state.phase_status is TaskStatus.PENDING
    assert state.next_task == "P01-T01"
    assert state.state_revision == 0
    assert state.phase_gate is None
    assert state.revit_stage is None


def test_state_dump_is_yaml_safe_and_roundtrips():
    state = ProjectState(
        phase_status=TaskStatus.PASS,
        phase_gate=PhaseGate.GO,
        last_completed_task="P01-T01",
        next_task="P01-T02",
        state_revision=3,
        blockers=["SITE_TOPOGRAPHY:MISSING"],
    )

    text = yaml.safe_dump(state.model_dump(mode="json"), sort_keys=True)
    restored = ProjectState(**yaml.safe_load(text))

    assert restored == state
    assert restored.blockers == ["SITE_TOPOGRAPHY:MISSING"]


def test_unknown_status_is_rejected():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ProjectState(phase_status="MAYBE_DONE")
