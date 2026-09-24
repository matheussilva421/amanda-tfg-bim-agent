"""Integrity checks for the repository's canonical provenance artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from amanda_agent.ingest.manifest import sha256_file
from amanda_agent.ingest.provenance import FactClass
from amanda_agent.requirements.program import AdoptedProgram, reconcile

ROOT = Path(__file__).resolve().parents[2]
PROGRAM_PATH = ROOT / "project" / "requirements" / "program.json"
PRINCIPLES_PATH = ROOT / "project" / "requirements" / "source-principles.yaml"
HYPOTHESES_PATH = ROOT / "project" / "requirements" / "design-hypotheses.yaml"
MISSING_DATA_PATH = ROOT / "project" / "site" / "missing-data.yaml"
SITE_PATH = ROOT / "project" / "site" / "site.json"
MANIFEST_PATH = ROOT / "project" / "provenance" / "source-manifest.yaml"
SOURCE_DIR = ROOT / "docs" / "source"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _manifest_documents() -> dict[str, dict]:
    manifest = _load_yaml(MANIFEST_PATH)
    return {document["source_id"]: document for document in manifest["documents"]}


def _source_id_from_ref(source_ref: str) -> str:
    source_id, separator, locator = source_ref.partition("#")
    assert source_id.startswith("SRC-")
    assert separator and locator
    return source_id


def _assert_manifest_reference(
    source_id: str,
    source_hash: str | None,
    documents: dict[str, dict],
) -> None:
    assert source_id.startswith("SRC-")
    assert source_id in documents
    if source_hash is not None:
        assert source_hash.lower() == documents[source_id]["sha256"].lower()


def _assert_string_source_ref(
    source_ref: str,
    source_hash: str | None,
    documents: dict[str, dict],
) -> None:
    source_id = _source_id_from_ref(source_ref)
    _assert_manifest_reference(source_id, source_hash, documents)


def test_canonical_source_facts_reference_existing_manifest_hashes():
    """All source-backed canonical claims resolve to the immutable manifest."""
    documents = _manifest_documents()
    program = _load_json(PROGRAM_PATH)
    baseline = program["baseline"]

    # program.json names this source pointer as source_id/source_sha256.
    _assert_manifest_reference(
        baseline["source_id"], baseline["source_sha256"], documents
    )
    assert baseline["source_filename"] == documents[baseline["source_id"]]["filename"]
    assert baseline["source_pages"]
    for sector in program["sectors"]:
        for space in sector["spaces"]:
            assert space["source_page"] in baseline["source_pages"]

    for hypothesis in program["unselected_hypotheses"]:
        _assert_manifest_reference(hypothesis["source_id"], None, documents)

    principles = _load_yaml(PRINCIPLES_PATH)["principles"]
    for principle in principles:
        assert principle["fact_class"] == FactClass.SOURCE_FACT.value
        assert principle["source_refs"]
        for reference in principle["source_refs"]:
            _assert_manifest_reference(
                reference["source_id"], reference["source_hash"], documents
            )

    site = _load_json(SITE_PATH)
    site_provenance = {
        item["source_id"]: item for item in site["provenance"]
    }
    for frontage in site["frontages"]:
        _assert_string_source_ref(
            frontage["source_ref"], frontage["sha256"], documents
        )
    reported_area_ref = site["reported_area"]["source_ref"]
    reported_area_source_id = _source_id_from_ref(reported_area_ref)
    assert reported_area_source_id in site_provenance
    _assert_manifest_reference(
        reported_area_source_id,
        site_provenance[reported_area_source_id]["sha256"],
        documents,
    )
    for item in site["provenance"]:
        _assert_manifest_reference(item["source_id"], item["sha256"], documents)

    missing_data = _load_yaml(MISSING_DATA_PATH)
    for entry in missing_data["entries"]:
        for source_ref in entry["source_refs"]:
            _assert_string_source_ref(source_ref, None, documents)


def test_requirement_and_statement_logical_ids_are_unique():
    program = _load_json(PROGRAM_PATH)
    requirement_ids = [sector["logical_id"] for sector in program["sectors"]]
    requirement_ids.extend(
        space["logical_id"]
        for sector in program["sectors"]
        for space in sector["spaces"]
    )
    statement_ids = [
        item["statement_id"]
        for path, collection in (
            (PRINCIPLES_PATH, "principles"),
            (HYPOTHESES_PATH, "hypotheses"),
        )
        for item in _load_yaml(path)[collection]
    ]

    assert requirement_ids
    assert len(requirement_ids) == len(set(requirement_ids))
    assert statement_ids
    assert len(statement_ids) == len(set(statement_ids))


def test_missing_site_topography_keeps_placeholders_without_invented_elevations():
    site = _load_json(SITE_PATH)
    topography = site["topography"]

    assert site["boundary"]["kind"] == "STUDY_PLACEHOLDER"
    assert "not the cadastral boundary" in site["boundary"]["disclaimer"]
    assert topography["source_state"] == "MISSING"
    assert topography["representation"] == "PLANAR_PLACEHOLDER"
    assert topography["elevation_points"] == []

    # z=0 is allowed only as the declared local drawing-plane convention.
    origin = site["design_coordinate_origin"]
    assert origin == {"x": 0.0, "y": 0.0, "z": 0.0, "convention": "LOCAL_DESIGN_PLANE"}
    assert all(len(point) == 2 for point in site["boundary"]["coordinates"])
    assert all(
        len(point) == 2
        for point in site["boundary"]["geojson"]["coordinates"][0]
    )

    missing_text = MISSING_DATA_PATH.read_text(encoding="utf-8")
    assert all(token in missing_text for token in ("[X]", "[Y]", "[Z]", "[W]"))


def test_fact_files_keep_source_facts_and_design_hypotheses_separate():
    principles = _load_yaml(PRINCIPLES_PATH)["principles"]
    hypotheses = _load_yaml(HYPOTHESES_PATH)["hypotheses"]

    assert principles
    assert hypotheses
    assert {item["fact_class"] for item in principles} == {
        FactClass.SOURCE_FACT.value
    }
    assert all(item.get("hypothesis") is not True for item in principles)
    assert {item["fact_class"] for item in hypotheses} == {
        FactClass.DESIGN_HYPOTHESIS.value
    }
    assert all(item["hypothesis"] is True for item in hypotheses)


def test_all_immutable_source_files_exist_and_match_manifest_hashes():
    manifest = _load_yaml(MANIFEST_PATH)
    documents = manifest["documents"]

    assert len(documents) == 23
    assert len({item["source_id"] for item in documents}) == len(documents)
    manifest_paths = {
        Path(item["immutable_path"]).as_posix() for item in documents
    }
    actual_paths = {
        path.relative_to(ROOT).as_posix()
        for path in SOURCE_DIR.rglob("*")
        if path.is_file()
    }
    assert manifest_paths <= actual_paths

    for item in documents:
        path = ROOT / item["immutable_path"]
        assert path.is_file()
        expected_stored_name = {
            "SRC-TFG-001": "TFG.pdf",
        }.get(item["source_id"], item["filename"])
        assert path.name == expected_stored_name
        assert sha256_file(path) == item["sha256"]


def test_program_subtotals_and_global_totals_reconcile_from_canonical_json():
    payload = _load_json(PROGRAM_PATH)
    sectors = payload["sectors"]

    for sector in sectors:
        computed = sum(
            space["quantity"] * space["target_area_m2"]
            for space in sector["spaces"]
        )
        assert computed == pytest.approx(sector["subtotal_m2"])

    internal = sum(
        sector["subtotal_m2"] for sector in sectors if sector["area_kind"] == "INTERNAL"
    )
    external = sum(
        sector["subtotal_m2"] for sector in sectors if sector["area_kind"] == "EXTERNAL"
    )
    assert internal == pytest.approx(626.0)
    assert external == pytest.approx(260.0)
    assert payload["totals"]["internal_useful_m2"] == pytest.approx(626.0)
    assert payload["totals"]["external_programmed_m2"] == pytest.approx(260.0)
    assert payload["totals"]["enclosed_estimate_m2"] == [783.0, 814.0]
    assert payload["totals"]["covered_estimate_m2"] == [850.0, 950.0]
    assert payload["reconciliation"]["ok"] is True
    assert payload["reconciliation"]["mismatches"] == []

    model_sectors = [
        {
            **sector,
            "spaces": [
                {
                    key: value
                    for key, value in space.items()
                    if key != "total_area_m2"
                }
                for space in sector["spaces"]
            ],
        }
        for sector in sectors
    ]
    canonical_program = AdoptedProgram.model_validate(
        {
            "baseline": payload["baseline"],
            "sectors": model_sectors,
            "unselected_hypotheses": payload["unselected_hypotheses"],
        }
    )
    assert reconcile(canonical_program)["ok"] is True
