import pytest
from pydantic import ValidationError


def _element(**overrides):
    values = {
        "logical_id": "ROOM-001",
        "category": "Rooms",
        "geometry": {"polygon": [[0.0, 0.0], [3.0, 0.0], [3.0, 4.0]]},
        "properties": {"name": "Reception"},
        "requirement_id": "REQ-ROOM-001",
        "design_option": "OPTION-A",
        "generation_run": "run-001",
    }
    values.update(overrides)
    return values


def test_stage_lifecycle_contains_the_formal_revit_states():
    from amanda_agent.bim.models import BimStage

    assert BimStage.R00.value == "EMPTY_SANDBOX"
    assert BimStage.R13.value == "DOCUMENTATION"
    assert BimStage.R16.value == "GOLDEN"
    assert len(BimStage) == 17


def test_desired_element_keeps_requirement_and_generation_provenance():
    from amanda_agent.bim.models import DesiredElement

    element = DesiredElement(**_element())

    assert element.logical_id == "ROOM-001"
    assert element.geometry["polygon"][1] == [3.0, 0.0]
    assert element.requirement_id == "REQ-ROOM-001"
    assert element.design_option == "OPTION-A"
    assert element.generation_run == "run-001"


def test_duplicate_desired_logical_ids_are_rejected():
    from amanda_agent.bim.models import DesiredState

    with pytest.raises(ValidationError, match="duplicate logical_id"):
        DesiredState(elements=[_element(), _element(category="Furniture")])


def test_bim_provenance_is_typed_and_serializable():
    from amanda_agent.bim.provenance import BimProvenance

    provenance = BimProvenance(
        requirement_id="REQ-ROOM-001",
        design_option="OPTION-A",
        generation_run="run-001",
        source_refs=["SRC-001#page=2"],
    )

    assert provenance.model_dump(mode="json")["source_refs"] == ["SRC-001#page=2"]
