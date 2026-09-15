"""Compile known site facts into the canonical record and gap registry.

Every value below is a transcription of an inspected source.  Nothing is
measured here: the study rectangle preserves the reported area so downstream
massing work has a planar reference, and it is labelled STUDY_PLACEHOLDER
because an equal-area rectangle is not the cadastral boundary.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .geometry import build_area_preserving_rectangular_placeholder
from .models import (
    BoundaryKind,
    BoundaryPolygon,
    FrontageRoad,
    SiteModel,
    SourceReference,
    SourceTopographyState,
    Topography,
    TopographyRepresentation,
)

TFG_SOURCE_ID = "SRC-TFG-001"
TFG_SOURCE_SHA256 = "16abe602ac50643482ce3c782780b4135fa8468b5ca814061fe426c8ca292a7e"
PLAN_SOURCE_ID = "SRC-SUP-002"
PLAN_SOURCE_SHA256 = "81c7d97f7b2aff2fa0eafaa81ce3db8eafb836164cef194b9932656d84b8127d"
LC208_SOURCE_ID = "SRC-SUP-006"
LC208_SOURCE_SHA256 = "b493c7a8f84b9410a07aba34bb1ac6c88f86b6bc64755d4cec63f62299a01043"
LAYOUT_SOURCE_ID = "SRC-SUP-016"
LAYOUT_SOURCE_SHA256 = "e1b4f5ebbd26a03142a058860b459483651ba17248b29ca2018d2d2ff8e2739c"

SITE_AREA_ASSERTION_M2 = 24_135.0
SITE_NAME = "Terreno da Companhia de Policia de Choque (CPChoque)"
SITE_LOCATION = "Lagoa Nova, Natal/RN"

# Transcribed frontage names, in the order the source lists them.
SOURCE_FRONTAGES = (
    "Avenida Prudente de Morais",
    "Avenida Miguel Castro",
    "Avenida Romualdo Galvao",
    "Rua Professor Otto de Brito Guerra",
)

# The support material flags the disagreement between the sentence that says
# four frontages and the one that says three.  It stays unresolved until a
# survey or cadastral document settles it.
THREE_FRONTAGE_LOCATOR = "page 60, section 5.3"
FOUR_FRONTAGE_LOCATOR = "page 61, section 5.3"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AreaAssertion(_Model):
    """A reported area with the exact location that reports it."""

    value_m2: float = Field(gt=0)
    fact_type: str = "SOURCE_ASSERTION"
    source_ref: str
    verification_status: str = "UNVERIFIED_AGAINST_CADASTRAL_DOCUMENT"


class FrontageConflict(_Model):
    roads: list[str] = Field(min_length=1)
    three_frontage_locator: str
    four_frontage_locator: str
    resolution: str
    impact: str


class OrientationFinding(_Model):
    """A stated climate/orientation finding that is source-backed."""

    statement: str
    source_ref: str


class SiteFacts(_Model):
    site_name: str
    location: str
    reported_area: AreaAssertion
    frontage_conflict: FrontageConflict
    orientation_findings: list[OrientationFinding]
    reference_sha256: dict[str, str]


def _ref(source_id: str, sha256: str, locator: str) -> SourceReference:
    return SourceReference(source_id=source_id, locator=locator, sha256=sha256)


def build_site_facts() -> SiteFacts:
    """Assemble the source statements the canonical site record is built from."""

    return SiteFacts(
        site_name=SITE_NAME,
        location=SITE_LOCATION,
        reported_area=AreaAssertion(
            value_m2=SITE_AREA_ASSERTION_M2,
            source_ref=TFG_SOURCE_ID + "#page 60, section 5.3",
        ),
        frontage_conflict=FrontageConflict(
            roads=list(SOURCE_FRONTAGES),
            three_frontage_locator=THREE_FRONTAGE_LOCATOR,
            four_frontage_locator=FOUR_FRONTAGE_LOCATOR,
            resolution=(
                "UNRESOLVED_PENDING_SURVEY_OR_CADASTRAL_DOCUMENT: the source "
                "states three and four frontages in the same section; the "
                "count is not settled by counting names in prose"
            ),
            impact=(
                "frontage count changes corner conditions, access points and "
                "setback obligations"
            ),
        ),
        orientation_findings=[
            OrientationFinding(
                statement=(
                    "Natal sits at roughly 5 degrees 47 minutes south, so the "
                    "sun crosses the northern sky for most of the year"
                ),
                source_ref=TFG_SOURCE_ID + "#page 68, section 5.4.3",
            ),
            OrientationFinding(
                statement=(
                    "the east facade on Avenida Prudente de Morais takes "
                    "morning sun from about 06h41 with long shadows cast into "
                    "the lot"
                ),
                source_ref=TFG_SOURCE_ID + "#page 69, section 5.4.3",
            ),
            OrientationFinding(
                statement=(
                    "the cited facade study is a design-support simulation, "
                    "not a surveyed orientation datum"
                ),
                source_ref=TFG_SOURCE_ID + "#page 68, section 5.4.3",
            ),
        ],
        reference_sha256={
            TFG_SOURCE_ID: TFG_SOURCE_SHA256,
            PLAN_SOURCE_ID: PLAN_SOURCE_SHA256,
            LC208_SOURCE_ID: LC208_SOURCE_SHA256,
            LAYOUT_SOURCE_ID: LAYOUT_SOURCE_SHA256,
        },
    )


def build_study_boundary(area_m2: float = SITE_AREA_ASSERTION_M2) -> BoundaryPolygon:
    """Build the planar study reference kept explicitly separate from survey."""

    return build_area_preserving_rectangular_placeholder(
        area_m2, aspect_ratio=1.0
    ).model_copy(update={"kind": BoundaryKind.STUDY_PLACEHOLDER})


def build_site_model(facts: SiteFacts | None = None) -> SiteModel:
    """Compile the canonical site model from source-backed statements."""

    facts = facts or build_site_facts()
    provenance = [
        _ref(TFG_SOURCE_ID, TFG_SOURCE_SHA256, "page 60, section 5.3"),
        _ref(LC208_SOURCE_ID, LC208_SOURCE_SHA256, "chapter 5 verification"),
    ]
    return SiteModel(
        site_version=1,
        boundary=build_study_boundary(facts.reported_area.value_m2),
        frontages=[
            FrontageRoad(
                name=name,
                source_ref=_ref(
                    TFG_SOURCE_ID,
                    TFG_SOURCE_SHA256,
                    "page 60-61, section 5.3",
                ),
            )
            for name in facts.frontage_conflict.roads
        ],
        topography=Topography(
            source_state=SourceTopographyState.MISSING,
            representation=TopographyRepresentation.PLANAR_PLACEHOLDER,
            elevation_points=[],
            provenance=[
                _ref(TFG_SOURCE_ID, TFG_SOURCE_SHA256, "page 61, section 5.3")
            ],
        ),
        buildable_area=None,
        setbacks=[],
        true_north=None,
        provenance=provenance,
    )


def missing_data_payload(facts: SiteFacts | None = None) -> dict:
    """Describe every known gap with what it blocks and what it still allows."""

    facts = facts or build_site_facts()
    return {
        "schema_version": 1,
        "site_name": facts.site_name,
        "entries": [
            {
                "id": "SITE_TOPOGRAPHY",
                "state": "MISSING",
                "what_is_missing": (
                    "verified survey or topographic elevations for the lot"
                ),
                "blocks": [
                    "final_grading",
                    "final_altimetric_accessibility_validation",
                ],
                "allows": [
                    "2d_macrozoning",
                    "schematic_massing_on_planar_reference",
                ],
                "resolution_action": (
                    "supply and validate a survey or topographic file with a "
                    "known datum"
                ),
                "source_refs": [TFG_SOURCE_ID + "#page 61, section 5.3"],
                "evidence": (
                    "section 5.3 states elevations as the placeholders [X], "
                    "[Y], [Z] and [W]; no numeric elevation is asserted"
                ),
            },
            {
                "id": "SITE_BOUNDARY",
                "state": "MISSING",
                "what_is_missing": (
                    "surveyed or cadastral polygon in a stated coordinate system"
                ),
                "blocks": [
                    "final_area_verification",
                    "legal_frontage_and_setback_verification",
                    "final_construction_permitting_check",
                ],
                "allows": [
                    "study_massing_on_planar_reference",
                    "schematic_sectorization",
                ],
                "resolution_action": (
                    "obtain the lot certificate or a georeferenced survey and "
                    "re-import the boundary as VERIFIED_CADASTRAL"
                ),
                "source_refs": [TFG_SOURCE_ID + "#page 60, section 5.3"],
                "evidence": (
                    "only a reported area of 24135 m2 is available; no polygon "
                    "vertex list was supplied"
                ),
            },
            {
                "id": "SITE_OCCUPANCY",
                "state": "MISSING",
                "what_is_missing": (
                    "confirmation of the current use of the lot and of the "
                    "relocation premise for the police company unit"
                ),
                "blocks": [
                    "final_site_availability_claim",
                    "institutional_relocation_assumption_verification",
                ],
                "allows": ["study_scenario_development"],
                "resolution_action": (
                    "confirm the current use and the relocation premise with "
                    "the responsible public body"
                ),
                "source_refs": [PLAN_SOURCE_ID + "#phase 2, closing the research"],
                "evidence": (
                    "the plan of accompaniment lists closing the research on "
                    "visits, sources and verifications as a pending phase"
                ),
            },
            {
                "id": "SITE_FRONTAGE_COUNT",
                "state": "CONFLICTING",
                "what_is_missing": (
                    "whether the lot has three or four frontages"
                ),
                "blocks": ["final_corner_and_setback_designation"],
                "allows": [
                    "study_massing_with_independent_flows",
                    "preliminary_access_split",
                ],
                "resolution_action": (
                    "settle the frontage count against a survey or cadastral "
                    "document; do not resolve it by counting names in prose"
                ),
                "source_refs": [
                    TFG_SOURCE_ID + "#" + THREE_FRONTAGE_LOCATOR,
                    TFG_SOURCE_ID + "#" + FOUR_FRONTAGE_LOCATOR,
                    PLAN_SOURCE_ID + "#phase 1, standardise the frontage count",
                ],
                "evidence": (
                    "the plan of accompaniment records that the source text "
                    "asserts both, and notes that Otto de Brito Guerra is a "
                    "street rather than an avenue"
                ),
            },
            {
                "id": "SITE_TRUE_NORTH",
                "state": "PARTIAL",
                "what_is_missing": (
                    "a verified true-north bearing with a source drawing datum"
                ),
                "blocks": ["final_orientation_compliance_statement"],
                "allows": ["study_orientation_reasoning_from_stated_findings"],
                "resolution_action": (
                    "supply a source drawing or survey that fixes true north"
                ),
                "source_refs": [TFG_SOURCE_ID + "#page 68, section 5.4.3"],
                "evidence": (
                    "solar findings are stated narratively; no north azimuth "
                    "for the source drawing was supplied"
                ),
            },
        ],
    }


def site_payload(facts: SiteFacts | None = None) -> dict:
    """Serialize the canonical site record without losing provenance."""

    facts = facts or build_site_facts()
    model = build_site_model(facts)
    return {
        "schema_version": 1,
        "site_name": facts.site_name,
        "location": facts.location,
        "site_version": model.site_version,
        "boundary": {
            "kind": model.boundary.kind.value,
            "coordinates": [list(point) for point in model.boundary.coordinates],
            "placeholder_area_m2": model.boundary.placeholder_area_m2,
            "geojson": model.boundary.to_geojson(),
            "disclaimer": (
                "equal-area planar study reference; not the cadastral "
                "boundary and not a survey"
            ),
        },
        "design_coordinate_origin": model.design_coordinate_origin.model_dump(),
        "true_north": None,
        "frontages": [
            {
                "name": road.name,
                "source_ref": road.source_ref.ref,
                "sha256": road.source_ref.sha256,
            }
            for road in model.frontages
        ],
        "frontage_conflict": facts.frontage_conflict.model_dump(),
        "candidate_access_points": [],
        "buildable_area": None,
        "setbacks": [],
        "topography": {
            "source_state": model.topography.source_state.value,
            "representation": model.topography.representation.value,
            "elevation_points": [],
        },
        "reported_area": facts.reported_area.model_dump(),
        "provenance": [
            {
                "source_id": reference.source_id,
                "locator": reference.locator,
                "sha256": reference.sha256,
            }
            for reference in model.provenance
        ],
    }


def write_site_files(root: Path, facts: SiteFacts | None = None) -> dict:
    """Write site.json and missing-data.yaml atomically."""

    facts = facts or build_site_facts()
    target = Path(root) / "project" / "site"
    target.mkdir(parents=True, exist_ok=True)
    payload = site_payload(facts)
    _atomic_text(
        target / "site.json",
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    )
    _atomic_text(
        target / "missing-data.yaml",
        yaml.safe_dump(
            missing_data_payload(facts),
            allow_unicode=True,
            sort_keys=False,
        ),
    )
    return {"site.json": payload}


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


__all__ = [
    "SITE_AREA_ASSERTION_M2",
    "SITE_NAME",
    "SOURCE_FRONTAGES",
    "AreaAssertion",
    "FrontageConflict",
    "OrientationFinding",
    "SiteFacts",
    "build_site_facts",
    "build_site_model",
    "build_study_boundary",
    "missing_data_payload",
    "site_payload",
    "write_site_files",
]
