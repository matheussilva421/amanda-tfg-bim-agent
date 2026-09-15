
import pytest
from pydantic import ValidationError


def _desired(logical_id: str):
    return {
        "logical_id": logical_id,
        "category": "Rooms",
        "geometry": {"bounds": [0.0, 0.0, 3.0, 4.0]},
        "properties": {"name": logical_id},
        "requirement_id": "REQ-ROOM",
        "design_option": "OPTION-A",
        "generation_run": "run-001",
    }


def _current(logical_id: str | None, *, unique_id: str | None = None, **overrides):
    values = {
        "logical_id": logical_id,
        "category": "Rooms",
        "geometry": {"bounds": [0.0, 0.0, 3.0, 4.0]},
        "properties": {"name": logical_id},
        "unique_id": unique_id or f"uid-{logical_id}",
        "document_id": "doc-001",
        "element_id": 42,
    }
    values.update(overrides)
    return values


def test_seventeen_desired_rooms_with_sixteen_current_has_one_create():
    from amanda_agent.bim.current_state import CurrentElement, CurrentState
    from amanda_agent.bim.desired_state import DesiredState
    from amanda_agent.bim.diff import DiffAction, diff_states

    desired = DesiredState(elements=[_desired(f"ROOM-{number:02d}") for number in range(1, 18)])
    current = CurrentState(
        document_id="doc-001",
        elements=[CurrentElement(**_current(f"ROOM-{number:02d}")) for number in range(1, 17)],
    )

    result = diff_states(desired, current)

    creates = [item for item in result.operations if item.action is DiffAction.CREATE]
    assert len(creates) == 1
    assert creates[0].logical_id == "ROOM-17"


def test_equivalent_geometry_and_properties_are_a_noop():
    from amanda_agent.bim.current_state import CurrentElement, CurrentState
    from amanda_agent.bim.desired_state import DesiredState
    from amanda_agent.bim.diff import DiffAction, diff_states

    result = diff_states(
        DesiredState(elements=[_desired("ROOM-01")]),
        CurrentState(
            document_id="doc-001",
            elements=[CurrentElement(**_current("ROOM-01"))],
        ),
    )

    assert len(result.operations) == 1
    assert result.operations[0].action is DiffAction.NOOP


def test_duplicate_current_logical_id_is_a_hard_error():
    from amanda_agent.bim.current_state import CurrentElement, CurrentState

    with pytest.raises(ValidationError, match="duplicate logical_id"):
        CurrentState(
            document_id="doc-001",
            elements=[
                CurrentElement(**_current("ROOM-01", unique_id="uid-a")),
                CurrentElement(**_current("ROOM-01", unique_id="uid-b")),
            ],
        )


def test_unmanaged_current_elements_are_not_deleted():
    from amanda_agent.bim.current_state import CurrentElement, CurrentState
    from amanda_agent.bim.desired_state import DesiredState
    from amanda_agent.bim.diff import diff_states

    result = diff_states(
        DesiredState(elements=[]),
        CurrentState(
            document_id="doc-001",
            elements=[CurrentElement(**_current(None, unique_id="user-element"))],
        ),
    )

    assert result.operations == []


def test_user_divergence_is_detected_before_overwrite():
    from amanda_agent.bim.current_state import CurrentElement, CurrentState
    from amanda_agent.bim.desired_state import DesiredState
    from amanda_agent.bim.diff import UserDivergence, diff_states

    with pytest.raises(UserDivergence, match="divergence"):
        diff_states(
            DesiredState(elements=[_desired("ROOM-01")]),
            CurrentState(
                document_id="doc-001",
                elements=[CurrentElement(**_current("ROOM-01", diverged=True))],
            ),
        )


def test_document_identity_mismatch_is_detected_before_overwrite():
    from amanda_agent.bim.current_state import CurrentElement, CurrentState
    from amanda_agent.bim.desired_state import DesiredState
    from amanda_agent.bim.diff import DocumentIdentityMismatch, diff_states

    with pytest.raises(DocumentIdentityMismatch, match="document identity"):
        diff_states(
            DesiredState(elements=[_desired("ROOM-01")]),
            CurrentState(
                document_id="after-save-as",
                elements=[CurrentElement(**_current("ROOM-01", document_id="after-save-as"))],
            ),
            expected_document_id="before-save-as",
        )


def test_unique_id_and_document_identity_survive_process_round_trip():
    from amanda_agent.bim.current_state import CurrentElement, CurrentState

    current = CurrentState(
        document_id="doc-001",
        elements=[CurrentElement(**_current("ROOM-01", unique_id="revit-unique-1"))],
    )
    restored = CurrentState.model_validate_json(current.model_dump_json())

    assert restored.elements[0].unique_id == "revit-unique-1"
    assert restored.elements[0].document_id == "doc-001"
    assert restored.elements[0].element_id is None
