"""P08 input, provenance and freeze contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from amanda_agent.requirements.decisions import load_decision_register


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "project" / "provenance" / "source-manifest.yaml"
SOURCE_VERSIONS_PATH = ROOT / "project" / "provenance" / "source-versions.yaml"
FREEZE_PATH = ROOT / "state" / "design-run-freeze.yaml"
SITE_PATH = ROOT / "project" / "site" / "site.json"
MISSING_DATA_PATH = ROOT / "project" / "site" / "missing-data.yaml"
REPORT_PATH = ROOT / "docs" / "reports" / "p08-site-resolution.md"
PREFLIGHT_PATH = ROOT / "docs" / "reports" / "p08-preflight.md"


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_p08_source_version_binds_every_manifest_file_without_new_sources():
    manifest = _yaml(MANIFEST_PATH)
    version = _yaml(SOURCE_VERSIONS_PATH)

    assert version["source_version"] == "source-set-v1"
    assert version["new_sources"] == []
    assert version["source_manifest_sha256"] == _sha256(MANIFEST_PATH)

    recorded = {item["source_id"]: item for item in version["documents"]}
    assert set(recorded) == {item["source_id"] for item in manifest["documents"]}
    for document in manifest["documents"]:
        item = recorded[document["source_id"]]
        source_path = ROOT / document["immutable_path"]
        assert item["filename"] == document["filename"]
        assert item["immutable_path"] == document["immutable_path"]
        assert item["bytes"] == source_path.stat().st_size
        assert item["sha256"] == document["sha256"] == _sha256(source_path)


def test_p08_site_resolution_keeps_planar_placeholder_and_final_blockers():
    site = json.loads(SITE_PATH.read_text(encoding="utf-8"))
    missing = _yaml(MISSING_DATA_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert site["topography"] == {
        "source_state": "MISSING",
        "representation": "PLANAR_PLACEHOLDER",
        "elevation_points": [],
    }
    assert site["boundary"]["kind"] == "STUDY_PLACEHOLDER"
    assert site["boundary"]["placeholder_area_m2"] == 24135.0
    entries = {item["id"]: item for item in missing["entries"]}
    assert {"SITE_TOPOGRAPHY", "SITE_BOUNDARY"} <= set(entries)
    assert "final_grading" in entries["SITE_TOPOGRAPHY"]["blocks"]
    assert "final_altimetric_accessibility_validation" in entries["SITE_TOPOGRAPHY"]["blocks"]
    assert "PLANAR_PLACEHOLDER" in report
    assert "PROVISIONAL_ASSUMPTION" in report
    assert "confidence" in report.lower()


def test_p08_freeze_binds_versions_and_current_file_hashes():
    freeze = _yaml(FREEZE_PATH)

    assert freeze["freeze_id"] == "P08-DESIGN-RUN-001"
    assert freeze["requirements_version"] == "requirements-v1"
    assert freeze["site_version"] == "site-v1"
    assert freeze["weights_version"] == 1
    assert freeze["design_engine_version"] == "design-engine-v1"
    assert len(freeze["design_engine_commit"]) == 40

    for item in freeze["frozen_files"]:
        path = ROOT / item["path"]
        assert path.is_file()
        assert item["sha256"] == _sha256(path)


def test_p08_typology_and_site_boundary_are_versioned_delegated_decisions():
    expected_ids = {
        "DEC-P08-T04-TYPOLOGY-001",
        "DEC-P08-T04-SITE-BOUNDARY-001",
    }
    for path in (
        ROOT / "project" / "requirements" / "decision-register.yaml",
        ROOT / "project" / "requirements" / "decisions.yaml",
    ):
        register = load_decision_register(path)
        current = {item.decision_id: item for item in register.decisions}
        assert expected_ids <= set(current)
        for decision_id in expected_ids:
            decision = current[decision_id]
            assert decision.selection_authority.value == "AGENT_DELEGATED"
            assert decision.review_status.value == "AMANDA_REVIEW_PENDING"
            assert decision.supersedes is not None
            assert decision.approval_hash_valid
            assert any(ref.startswith("https://") for ref in decision.source_refs)

    first = load_decision_register(ROOT / "project" / "requirements" / "decision-register.yaml")
    second = load_decision_register(ROOT / "project" / "requirements" / "decisions.yaml")
    assert first.get("DEC-P08-T04-TYPOLOGY-001") == second.get("DEC-P08-T04-TYPOLOGY-001")
    assert first.get("DEC-P08-T04-SITE-BOUNDARY-001") == second.get("DEC-P08-T04-SITE-BOUNDARY-001")


def test_p08_preflight_report_has_auditable_check_table():
    report = PREFLIGHT_PATH.read_text(encoding="utf-8")

    assert "| check | comando | resultado | PASS|FAIL|PENDENTE | impacto |" in report
    for label in ("P08-T01", "doctor", "status", "task-graph", "source-manifest"):
        assert label in report
