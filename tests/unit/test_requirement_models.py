"""Behavioral contracts for canonical and draft program requirements."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from amanda_agent.requirements.models import (
    DraftProgramRequirementSet,
    DraftSpaceRequirement,
    SectorRequirement,
    SpaceRequirement,
    UnknownRequirementFieldError,
)


def _space(**overrides) -> dict:
    value = {
        "logical_id": "space-01",
        "name": "Synthetic room",
        "sector": "care",
        "quantity": 1,
        "target_area_m2": 12.5,
        "source_refs": ["synthetic-source:page-1"],
    }
    value.update(overrides)
    return value


def _sector(logical_id: str, spaces: list[dict] | None = None) -> SectorRequirement:
    return SectorRequirement(
        logical_id=logical_id,
        name="Synthetic sector",
        spaces=[SpaceRequirement(**space) for space in (spaces or [_space()])],
        source_refs=["synthetic-source:sector-1"],
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quantity", 0),
        ("quantity", -1),
        ("target_area_m2", 0),
        ("target_area_m2", -0.1),
        ("target_area_m2", math.nan),
        ("target_area_m2", math.inf),
        ("min_area_m2", 0),
        ("max_area_m2", -1),
    ],
)
def test_canonical_space_rejects_non_positive_or_non_finite_values(
    field: str, value: float
):
    with pytest.raises(ValidationError):
        SpaceRequirement(**_space(**{field: value}))


def test_canonical_space_rejects_empty_provenance():
    with pytest.raises(ValidationError):
        SpaceRequirement(**_space(source_refs=[]))
    with pytest.raises(ValidationError):
        SpaceRequirement(**_space(source_refs=[""]))


@pytest.mark.parametrize(
    "overrides",
    [
        {"min_area_m2": 13, "target_area_m2": 12},
        {"max_area_m2": 12, "target_area_m2": 13},
        {"min_area_m2": 14, "max_area_m2": 13},
    ],
)
def test_canonical_space_rejects_invalid_area_ranges(overrides: dict):
    with pytest.raises(ValidationError):
        SpaceRequirement(**_space(**overrides))


def test_program_rejects_duplicate_logical_ids_across_sectors():
    first = _sector("sector-01", [_space(logical_id="space-duplicate")])
    second = _sector("sector-02", [_space(logical_id="space-duplicate")])

    from amanda_agent.requirements.models import ProgramRequirementSet

    with pytest.raises(ValidationError, match="duplicate logical_id"):
        ProgramRequirementSet(
            sectors=[first, second],
            source_refs=["synthetic-source:program"],
        )


def test_program_rejects_duplicate_sector_logical_ids():
    from amanda_agent.requirements.models import ProgramRequirementSet

    with pytest.raises(ValidationError, match="duplicate logical_id"):
        ProgramRequirementSet(
            sectors=[_sector("sector-01"), _sector("sector-01")],
            source_refs=["synthetic-source:program"],
        )


def test_draft_unknown_required_field_cannot_compile_without_supply():
    draft = DraftSpaceRequirement(
        logical_id="space-01",
        name="Synthetic room",
        sector="care",
        quantity=None,
        target_area_m2=None,
        source_refs=["synthetic-source:page-1"],
    )

    with pytest.raises(UnknownRequirementFieldError, match="quantity"):
        draft.to_canonical()

    completed = draft.model_copy(update={"quantity": 1, "target_area_m2": 12.5})
    canonical = completed.to_canonical()
    assert isinstance(canonical, SpaceRequirement)
    assert canonical.quantity == 1


def test_draft_program_compilation_keeps_unknown_nested_fields_explicit():
    draft = DraftProgramRequirementSet(
        sectors=[
            {
                "logical_id": "sector-01",
                "name": "Synthetic sector",
                "spaces": [
                    {
                        **_space(),
                        "target_area_m2": None,
                    }
                ],
                "source_refs": ["synthetic-source:sector-1"],
            }
        ],
        source_refs=["synthetic-source:program"],
    )

    with pytest.raises(UnknownRequirementFieldError, match="target_area_m2"):
        draft.compile()
