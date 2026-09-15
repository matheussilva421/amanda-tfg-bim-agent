"""Typed, provenance-preserving models for canonical site intelligence.

The model deliberately keeps source topography and its drawing
representation as different concepts.  A local z=0 plane is a design
convention; it is never a survey point and cannot be stored in the surveyed
point collection.
"""

from __future__ import annotations

from enum import StrEnum
from math import isfinite
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import Polygon
from shapely.validation import explain_validity

Coordinate2D = tuple[float, float]
Coordinate3D = tuple[float, float, float]


class SourceTopographyState(StrEnum):
    """What the supplied source material proves about site topography."""

    MISSING = "MISSING"
    VERIFIED_TOPOGRAPHY = "VERIFIED_TOPOGRAPHY"


class TopographyRepresentation(StrEnum):
    """How a site is represented for a design study or verified model."""

    PLANAR_PLACEHOLDER = "PLANAR_PLACEHOLDER"
    VERIFIED_TOPOGRAPHY = "VERIFIED_TOPOGRAPHY"


class BoundaryKind(StrEnum):
    """The evidentiary status of a polygon's boundary."""

    VERIFIED_CADASTRAL = "VERIFIED_CADASTRAL"
    STUDY_PLACEHOLDER = "STUDY_PLACEHOLDER"


class ScenarioOverrideStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REPLACED_BY_SURVEY = "REPLACED_BY_SURVEY"


class SourceReference(BaseModel):
    """Stable locator and digest for an input source.

    The digest is required so a source fact cannot be detached from the exact
    bytes that were inspected.  ``locator`` may be a page, sheet, cell,
    drawing id, URL fragment, or another precise source location.
    """

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    version: str | None = Field(default=None, min_length=1)

    @property
    def ref(self) -> str:
        """Human-readable source locator used in reports."""

        return f"{self.source_id}#{self.locator}"


class SourceFact[T](BaseModel):
    """A value that is explicitly classified as a source fact."""

    model_config = ConfigDict(extra="forbid")

    fact_type: Literal["SOURCE_FACT"] = "SOURCE_FACT"
    value: T
    source_ref: SourceReference


class BoundaryPolygon(BaseModel):
    """A validated ring whose evidentiary role is explicit.

    A study placeholder is valid design geometry but is never accepted as a
    verified cadastral boundary.  A verified cadastral polygon must carry a
    source reference.
    """

    model_config = ConfigDict(extra="forbid")

    coordinates: list[Coordinate2D] = Field(min_length=4)
    kind: BoundaryKind = BoundaryKind.STUDY_PLACEHOLDER
    source_ref: SourceReference | None = None
    placeholder_area_m2: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_ring_and_evidence(self) -> BoundaryPolygon:
        if self.coordinates[0] != self.coordinates[-1]:
            raise ValueError("boundary ring must be closed")
        if len(set(self.coordinates[:-1])) < 3:
            raise ValueError("boundary ring needs at least three distinct vertices")

        polygon = Polygon(self.coordinates)
        if not polygon.is_valid:
            reason = explain_validity(polygon)
            if "Self-intersection" in reason:
                raise ValueError("boundary self-intersects: " + reason)
            raise ValueError("boundary is invalid: " + reason)
        if polygon.area <= 0:
            raise ValueError("boundary area must be positive")
        if self.kind is BoundaryKind.VERIFIED_CADASTRAL and self.source_ref is None:
            raise ValueError("verified cadastral boundary requires source_ref")
        return self

    @property
    def is_provisional(self) -> bool:
        return self.kind is BoundaryKind.STUDY_PLACEHOLDER

    @property
    def is_cadastral(self) -> bool:
        return self.kind is BoundaryKind.VERIFIED_CADASTRAL

    def to_geojson(self) -> dict:
        return {
            "type": "Polygon",
            "coordinates": [[list(point) for point in self.coordinates]],
        }

    @classmethod
    def from_geojson(
        cls,
        payload: dict,
        *,
        kind: BoundaryKind = BoundaryKind.STUDY_PLACEHOLDER,
        source_ref: SourceReference | None = None,
    ) -> BoundaryPolygon:
        if payload.get("type") != "Polygon":
            raise ValueError("site boundary GeoJSON must have type Polygon")
        coordinates = payload.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 1:
            raise ValueError("site boundary GeoJSON must contain one linear ring")
        return cls(coordinates=coordinates[0], kind=kind, source_ref=source_ref)


class CoordinateOrigin(BaseModel):
    """Origin of the local design plane, not a surveyed datum."""

    model_config = ConfigDict(extra="forbid")

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    convention: Literal["LOCAL_DESIGN_PLANE"] = "LOCAL_DESIGN_PLANE"

    @model_validator(mode="after")
    def finite_coordinates(self) -> CoordinateOrigin:
        if not all(isfinite(value) for value in (self.x, self.y, self.z)):
            raise ValueError("design coordinate origin must be finite")
        return self


class TrueNorth(BaseModel):
    """Verified true-north bearing with the source that establishes it."""

    model_config = ConfigDict(extra="forbid")

    azimuth_degrees: float = Field(ge=0, lt=360)
    source_ref: SourceReference


class FrontageRoad(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    source_ref: SourceReference
    side_or_segment: str | None = Field(default=None, min_length=1)


class CandidateAccessPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_id: str = Field(min_length=1)
    coordinate: Coordinate2D
    road_name: str | None = Field(default=None, min_length=1)
    source_ref: SourceReference


class VerifiedArea(BaseModel):
    """A measured area admitted to the canonical model only with provenance."""

    model_config = ConfigDict(extra="forbid")

    area_m2: float = Field(gt=0)
    source_ref: SourceReference


class Setback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edge: str = Field(min_length=1)
    distance_m: float = Field(gt=0)
    source_ref: SourceReference


class SurveyedElevationPoint(BaseModel):
    """An elevation point that is allowed only with verified-source evidence."""

    model_config = ConfigDict(extra="forbid")

    coordinate: Coordinate3D
    source_ref: SourceReference


class Topography(BaseModel):
    """Source state and representation, with a guarded surveyed point set."""

    model_config = ConfigDict(extra="forbid")

    source_state: SourceTopographyState = SourceTopographyState.MISSING
    representation: TopographyRepresentation = TopographyRepresentation.PLANAR_PLACEHOLDER
    elevation_points: list[SurveyedElevationPoint] = Field(default_factory=list)
    provenance: list[SourceReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def guard_surveyed_points(self) -> Topography:
        if self.source_state is SourceTopographyState.MISSING:
            if self.elevation_points:
                raise ValueError("MISSING topography cannot carry elevation points")
            if self.representation is TopographyRepresentation.VERIFIED_TOPOGRAPHY:
                raise ValueError("MISSING topography cannot use verified representation")
        if self.representation is TopographyRepresentation.VERIFIED_TOPOGRAPHY:
            if self.source_state is not SourceTopographyState.VERIFIED_TOPOGRAPHY:
                raise ValueError("verified representation requires verified topography")
            if not self.elevation_points:
                raise ValueError("verified topography requires elevation points")
        return self


class HypotheticalElevationPoint(BaseModel):
    """An assumption used only by a separately versioned study scenario."""

    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    elevation_m: float


class ScenarioElevationOverride(BaseModel):
    """Versioned provisional terrain assumptions kept outside source points."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    assumption: Literal["PROVISIONAL_ASSUMPTION"] = "PROVISIONAL_ASSUMPTION"
    elevations: list[HypotheticalElevationPoint] = Field(min_length=1)
    affected_checks: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    status: ScenarioOverrideStatus = ScenarioOverrideStatus.ACTIVE
    replaced_by_site_version: int | None = Field(default=None, ge=1)


class SiteModel(BaseModel):
    """Canonical site record consumed by downstream design work."""

    model_config = ConfigDict(extra="forbid")

    site_version: int = Field(default=1, ge=1)
    boundary: BoundaryPolygon
    design_coordinate_origin: CoordinateOrigin = Field(default_factory=CoordinateOrigin)
    true_north: TrueNorth | None = None
    frontages: list[FrontageRoad] = Field(default_factory=list)
    candidate_access_points: list[CandidateAccessPoint] = Field(default_factory=list)
    buildable_area: VerifiedArea | None = None
    setbacks: list[Setback] = Field(default_factory=list)
    topography: Topography = Field(default_factory=Topography)
    provenance: list[SourceReference] = Field(default_factory=list)
    scenario_overrides: list[ScenarioElevationOverride] = Field(default_factory=list)
    invalidated_checks: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_scenario_versions(self) -> SiteModel:
        seen: dict[str, set[int]] = {}
        for override in self.scenario_overrides:
            versions = seen.setdefault(override.scenario_id, set())
            if override.version in versions:
                raise ValueError(
                    "duplicate scenario override version: "
                    + override.scenario_id
                    + " v"
                    + str(override.version)
                )
            versions.add(override.version)
        return self

    @property
    def topography_state(self) -> SourceTopographyState:
        return self.topography.source_state

    @property
    def topography_representation(self) -> TopographyRepresentation:
        return self.topography.representation

    def add_scenario_override(
        self, override: ScenarioElevationOverride
    ) -> SiteModel:
        existing = [
            item
            for item in self.scenario_overrides
            if item.scenario_id == override.scenario_id
        ]
        if any(item.version == override.version for item in existing):
            raise ValueError(
                "scenario override version already exists: "
                + override.scenario_id
                + " v"
                + str(override.version)
            )
        if existing and override.version <= max(item.version for item in existing):
            raise ValueError("scenario override version must increase")
        return self.model_copy(
            deep=True,
            update={
                "site_version": self.site_version + 1,
                "scenario_overrides": [*self.scenario_overrides, override],
            },
        )

    def replace_scenario_with_survey(
        self,
        scenario_id: str,
        survey: Topography,
    ) -> SiteModel:
        if survey.source_state is not SourceTopographyState.VERIFIED_TOPOGRAPHY:
            raise ValueError("replacement survey must have verified topography")
        if survey.representation is not TopographyRepresentation.VERIFIED_TOPOGRAPHY:
            raise ValueError("replacement survey must use verified representation")

        candidates = [
            item
            for item in self.scenario_overrides
            if item.scenario_id == scenario_id
            and item.status is ScenarioOverrideStatus.ACTIVE
        ]
        if not candidates:
            raise ValueError("active scenario override not found: " + scenario_id)
        prior = max(candidates, key=lambda item: item.version)
        new_site_version = self.site_version + 1
        updated_overrides = []
        for item in self.scenario_overrides:
            if item is prior:
                updated_overrides.append(
                    item.model_copy(
                        update={
                            "status": ScenarioOverrideStatus.REPLACED_BY_SURVEY,
                            "replaced_by_site_version": new_site_version,
                        }
                    )
                )
            else:
                updated_overrides.append(item)

        invalidated = list(self.invalidated_checks)
        for check in prior.affected_checks:
            if check not in invalidated:
                invalidated.append(check)
        provenance = list(self.provenance)
        for reference in survey.provenance:
            if reference not in provenance:
                provenance.append(reference)
        return self.model_copy(
            deep=True,
            update={
                "site_version": new_site_version,
                "topography": survey,
                "provenance": provenance,
                "scenario_overrides": updated_overrides,
                "invalidated_checks": invalidated,
            },
        )

    def replace_scenario_override(
        self,
        scenario_id: str,
        survey: Topography,
    ) -> SiteModel:
        """Compatibility spelling for the explicit survey replacement operation."""

        return self.replace_scenario_with_survey(scenario_id, survey)
