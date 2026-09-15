from __future__ import annotations

import pytest
from pydantic import ValidationError

from amanda_agent.site.models import (
    BoundaryKind,
    BoundaryPolygon,
    CoordinateOrigin,
    FrontageRoad,
    HypotheticalElevationPoint,
    ScenarioElevationOverride,
    ScenarioOverrideStatus,
    SiteModel,
    SourceReference,
    SourceTopographyState,
    SurveyedElevationPoint,
    Topography,
    TopographyRepresentation,
)

SOURCE = SourceReference(
    source_id="survey/topography.pdf",
    locator="page 4, drawing T-01",
    sha256="a" * 64,
    version="2026-01",
)


def _placeholder_boundary() -> BoundaryPolygon:
    return BoundaryPolygon(
        coordinates=[(0, 0), (155, 0), (155, 155.709677), (0, 155.709677), (0, 0)],
        kind=BoundaryKind.STUDY_PLACEHOLDER,
        placeholder_area_m2=24_135,
    )


def test_invalid_self_intersecting_boundary_is_rejected():
    with pytest.raises(ValidationError, match="self-intersect"):
        BoundaryPolygon(
            coordinates=[(0, 0), (10, 10), (0, 10), (10, 0), (0, 0)],
            kind=BoundaryKind.STUDY_PLACEHOLDER,
        )


def test_source_topography_and_representation_are_separate_enums():
    assert SourceTopographyState.MISSING.value == "MISSING"
    assert TopographyRepresentation.PLANAR_PLACEHOLDER.value == "PLANAR_PLACEHOLDER"
    assert (
        SourceTopographyState.VERIFIED_TOPOGRAPHY
        is not TopographyRepresentation.VERIFIED_TOPOGRAPHY
    )


def test_missing_topography_cannot_carry_surveyed_elevation_points():
    with pytest.raises(ValidationError, match="MISSING.*elevation"):
        Topography(
            source_state=SourceTopographyState.MISSING,
            representation=TopographyRepresentation.PLANAR_PLACEHOLDER,
            elevation_points=[
                SurveyedElevationPoint(
                    coordinate=(1, 2, 3),
                    source_ref=SOURCE,
                )
            ],
        )


def test_source_facts_carry_a_source_reference():
    with pytest.raises(ValidationError, match="source_ref"):
        FrontageRoad(name="Rua sem fonte", source_ref=None)


def test_scenario_override_is_provisional_and_replaced_by_new_survey():
    site = SiteModel(
        boundary=_placeholder_boundary(),
        design_coordinate_origin=CoordinateOrigin(x=0, y=0, z=0),
        topography=Topography(
            source_state=SourceTopographyState.MISSING,
            representation=TopographyRepresentation.PLANAR_PLACEHOLDER,
        ),
        provenance=[SOURCE],
    )
    scenario = ScenarioElevationOverride(
        scenario_id="sloping-study",
        version=1,
        elevations=[HypotheticalElevationPoint(x=0, y=0, elevation_m=0.0)],
        affected_checks=["final_grading", "altimetric_accessibility"],
        rationale="Study-only slope assumption pending a survey.",
    )

    study = site.add_scenario_override(scenario)
    survey = Topography(
        source_state=SourceTopographyState.VERIFIED_TOPOGRAPHY,
        representation=TopographyRepresentation.VERIFIED_TOPOGRAPHY,
        elevation_points=[
            SurveyedElevationPoint(coordinate=(0, 0, 1.25), source_ref=SOURCE)
        ],
        provenance=[SOURCE],
    )
    replaced = study.replace_scenario_with_survey("sloping-study", survey)

    assert study.topography.source_state is SourceTopographyState.MISSING
    assert replaced.topography.source_state is SourceTopographyState.VERIFIED_TOPOGRAPHY
    assert replaced.site_version == study.site_version + 1
    assert replaced.invalidated_checks == ["final_grading", "altimetric_accessibility"]
    assert len(replaced.scenario_overrides) == 1
    assert replaced.scenario_overrides[0].version == 1
    assert replaced.scenario_overrides[0].status is ScenarioOverrideStatus.REPLACED_BY_SURVEY
    assert replaced.scenario_overrides[0].elevations[0].elevation_m == 0.0
