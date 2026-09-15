"""Behavioural tests for the canonical site record built from source facts."""

from __future__ import annotations

import json
from pathlib import Path

from amanda_agent.site.compile import (
    SITE_AREA_ASSERTION_M2,
    build_site_facts,
    build_site_model,
    missing_data_payload,
    site_payload,
)
from amanda_agent.site.models import (
    BoundaryKind,
    SourceTopographyState,
    TopographyRepresentation,
)


def test_reported_area_stays_a_source_assertion_not_verified_area():
    facts = build_site_facts()
    assertion = facts.reported_area
    assert assertion.value_m2 == SITE_AREA_ASSERTION_M2 == 24_135.0
    assert assertion.fact_type == "SOURCE_ASSERTION"
    assert assertion.source_ref.startswith("SRC-TFG-001#")
    # The equal-area study rectangle must never be sold as the cadastral lot.
    model = build_site_model(facts)
    assert model.boundary.kind is BoundaryKind.STUDY_PLACEHOLDER
    assert model.buildable_area is None
    assert model.setbacks == []
    assert model.true_north is None


def test_topography_is_missing_and_carries_no_invented_elevation():
    model = build_site_model(build_site_facts())
    assert model.topography.source_state is SourceTopographyState.MISSING
    assert (
        model.topography.representation
        is TopographyRepresentation.PLANAR_PLACEHOLDER
    )
    assert model.topography.elevation_points == []


def test_frontage_conflict_is_preserved_with_both_locators():
    facts = build_site_facts()
    conflict = facts.frontage_conflict
    assert conflict.three_frontage_locator != conflict.four_frontage_locator
    assert len(conflict.roads) == 4
    assert conflict.resolution.startswith("UNRESOLVED")
    public_roads = {road.name for road in build_site_model(facts).frontages}
    assert "Avenida Prudente de Morais" in public_roads


def test_missing_data_registry_lists_the_blocking_gaps():
    payload = missing_data_payload(build_site_facts())
    ids = {entry["id"] for entry in payload["entries"]}
    assert {"SITE_TOPOGRAPHY", "SITE_BOUNDARY", "SITE_OCCUPANCY"} <= ids
    topography = next(
        entry for entry in payload["entries"] if entry["id"] == "SITE_TOPOGRAPHY"
    )
    assert topography["state"] == "MISSING"
    assert "final_grading" in topography["blocks"]
    assert "2d_macrozoning" in topography["allows"]
    assert "schematic_massing_on_planar_reference" in topography["allows"]


def test_site_payload_round_trips_and_records_source_references():
    payload = site_payload(build_site_facts())
    assert payload["topography"]["source_state"] == "MISSING"
    assert payload["boundary"]["kind"] == "STUDY_PLACEHOLDER"
    assert payload["boundary"]["placeholder_area_m2"] == 24_135.0
    assert payload["provenance"]
    assert all(ref["sha256"] for ref in payload["provenance"])
    # JSON must be serialisable exactly as written to disk.
    assert json.loads(json.dumps(payload)) == payload


def test_written_files_are_derived_from_the_payload(tmp_path: Path):
    from amanda_agent.site.compile import write_site_files

    written = write_site_files(tmp_path, build_site_facts())
    target = tmp_path / "project" / "site"
    site = json.loads((target / "site.json").read_text(encoding="utf-8"))
    assert site["site_version"] == 1
    assert written["site.json"] == site_payload(build_site_facts())
    assert (target / "missing-data.yaml").exists()
    assert site["reported_area"]["value_m2"] == 24_135.0
    assert site["reported_area"]["fact_type"] == "SOURCE_ASSERTION"


def test_gap_registry_projects_onto_typed_blockers(tmp_path: Path):
    from amanda_agent.site.gaps import (
        blocker_records,
        load_missing_data,
        sync_blockers,
    )

    records = {record.id: record for record in blocker_records()}
    topography = records["SITE_TOPOGRAPHY"]
    assert "final-grading" in topography.tasks_blocked
    assert "2d_macrozoning" not in topography.tasks_still_allowed
    assert "schematic-macrozoning" in topography.tasks_still_allowed
    # A conflict degrades work; it must not stop the whole project dead.
    assert records["SITE_FRONTAGE_COUNT"].severity.value == "DEGRADING"
    assert topography.severity.value == "BLOCKING"

    written = sync_blockers(tmp_path / "state" / "blockers.yaml")
    assert {item["id"] for item in written["blockers"]} == set(records)
    on_disk = load_missing_data(
        Path(__file__).resolve().parents[2]
    )
    assert on_disk["entries"]
