from __future__ import annotations

import pytest

from amanda_agent.design.constraints import (
    ConstraintResolution,
    hard_violations_only,
    soft_penalties_from_violations,
    validate_candidate,
)
from amanda_agent.design.models import ConstraintStatus
from amanda_agent.requirements.models import (
    ProgramRequirementSet,
    SectorRequirement,
    SpaceRequirement,
)
from amanda_agent.requirements.relations import EnvironmentRelation, RelationType

SITE = [(0, 0), (20, 0), (20, 20), (0, 20), (0, 0)]


def _room_requirement(*, accessible: bool | None = None) -> ProgramRequirementSet:
    return ProgramRequirementSet(
        sectors=[
            SectorRequirement(
                logical_id="sector-care",
                name="Care",
                spaces=[
                    SpaceRequirement(
                        logical_id="room-01",
                        name="Room",
                        sector="sector-care",
                        quantity=1,
                        target_area_m2=9,
                        min_area_m2=8,
                        accessible=accessible,
                        source_refs=["synthetic:room-01"],
                    )
                ],
                source_refs=["synthetic:sector-care"],
            )
        ],
        source_refs=["synthetic:program"],
    )


def _candidate(*rooms: dict) -> dict:
    return {"resolution": "ROOM", "rooms": list(rooms)}


def _room(room_id: str, x: float, *, accessible: bool = False) -> dict:
    return {
        "logical_id": room_id,
        "geometry": [(x, 1), (x + 3, 1), (x + 3, 4), (x, 4), (x, 1)],
        "accessible": accessible,
        "net_area_m2": 9,
    }


def _codes(result):
    return {item.code for item in result if item.status is ConstraintStatus.VIOLATION}


def test_room_outside_buildable_site_is_a_hard_violation():
    candidate = _candidate(_room("room-01", 19))

    violations = validate_candidate(candidate, _room_requirement(), SITE)

    assert "outside_buildable_site" in _codes(violations)
    assert len(hard_violations_only(violations)) >= 1


def test_overlapping_rooms_are_a_hard_violation():
    first = _room("room-01", 1)
    second = _room("room-02", 2)

    violations = validate_candidate(
        _candidate(first, second), _room_requirement(), SITE
    )

    assert "room_overlap" in _codes(violations)


def test_missing_required_room_is_a_hard_violation():
    violations = validate_candidate(_candidate(), _room_requirement(), SITE)

    assert "required_room_missing" in _codes(violations)


def test_missing_required_accessible_room_is_a_hard_violation():
    violations = validate_candidate(
        _candidate(_room("room-01", 1, accessible=False)),
        _room_requirement(accessible=True),
        SITE,
    )

    assert "accessible_room_missing" in _codes(violations)


def test_must_be_separated_cannot_be_treated_as_a_soft_penalty():
    candidate = _candidate(_room("room-a", 1), _room("room-b", 2))
    candidate["relations"] = [
        EnvironmentRelation(
            source_logical_id="room-a",
            target_logical_id="room-b",
            relation=RelationType.MUST_BE_SEPARATED,
            weight=1,
        )
    ]

    violations = validate_candidate(candidate, _room_requirement(), SITE)

    separated = [item for item in violations if item.code == "must_be_separated"]
    assert separated and separated[0].is_hard_violation
    with pytest.raises(ValueError, match="hard constraint"):
        soft_penalties_from_violations(separated)


def test_macro_resolution_does_not_reject_absent_rooms_and_marks_check_unavailable():
    candidate = {
        "resolution": ConstraintResolution.MACRO,
        "sectors": [
            {
                "logical_id": "sector-care",
                "geometry": [(1, 1), (10, 1), (10, 10), (1, 10), (1, 1)],
            }
        ],
    }

    results = validate_candidate(candidate, _room_requirement(), SITE)

    unavailable = [
        item for item in results if item.code == "required_rooms"
    ]
    assert unavailable
    assert unavailable[0].status is ConstraintStatus.NOT_EVALUATED
    assert not hard_violations_only(unavailable)
