import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = (
    ROOT
    / "revit"
    / "production"
    / "evidence"
    / "AMANDA-RUN-003-R04"
    / "views"
    / "p6-canon-011-20260926"
    / "p6-canon-011-captures.json"
)


def test_run003_revit_capture_set_covers_required_views_and_hashes():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert data["run"] == "RUN-003"
    assert data["stage"] == "R04"
    assert data["source_document"].endswith("AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt")
    assert data["provider"] == "Horizun 1.3.3"

    source_checkpoint = data["source_checkpoint"]
    checkpoint_path = ROOT / source_checkpoint["path"]
    checkpoint_manifest_path = ROOT / source_checkpoint["manifest_path"]
    checkpoint_manifest = json.loads(checkpoint_manifest_path.read_text(encoding="utf-8"))
    checkpoint_sha256 = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
    assert checkpoint_sha256 == source_checkpoint["sha256"]
    assert checkpoint_manifest["sha256"] == source_checkpoint["sha256"]
    assert source_checkpoint["captured_after_cold_reopen"] is True
    assert source_checkpoint["reopen_readback_count"] == 25
    spatial_evidence = json.loads(
        (ROOT / "revit" / "production" / "evidence" / "AMANDA-RUN-003-R04" / "r04-spatial-model-evidence.json").read_text(encoding="utf-8")
    )
    assert data["source_readback"]["result_set_fingerprint"] == spatial_evidence["readback"]["result_set_fingerprint"]
    assert source_checkpoint["sha256"] == spatial_evidence["persistence"]["checkpoint_sha256"]

    captures = {entry["role"]: entry for entry in data["captures"]}
    assert {
        "implantation_top",
        "implantation_massing",
        "overall_perspective",
        "administration_mass",
        "administration_ground_route",
        "administration_upper_floor",
        "residential",
        "services",
        "child_sector",
    } <= captures.keys()

    relation = data["reference_captures"]["child_playground_relation"]
    assert relation["visible_element_ids"] == [328658, 329971]
    assert relation["visible_element_names"] == ["MASS-CHILD_SECTOR", "SITE-PLAYGROUND"]
    assert relation["view_id"] == 8251
    assert relation["view_restored"] is True
    assert relation["rollback_status"] == "RolledBack"
    assert relation["use"] == "REFERENCE_ONLY_FOR_UNCHANGED_CHILD_PLAYGROUND_RELATION"
    assert relation["current_revalidation"]["checkpoint_sha256"] == source_checkpoint["sha256"]
    assert relation["current_revalidation"]["element_ids"] == [328658, 329971]
    assert relation["source_checkpoint_sha256"] != source_checkpoint["sha256"]
    relation_path = ROOT / relation["path"]
    assert hashlib.sha256(relation_path.read_bytes()).hexdigest() == relation["sha256"]

    for entry in captures.values():
        image_path = ROOT / entry["path"]
        assert image_path.is_file(), entry["path"]
        assert hashlib.sha256(image_path.read_bytes()).hexdigest() == entry["sha256"]
        assert entry["capture_status"] == "CAPTURED_AFTER_P6_REOPEN"
        assert entry["capture_checkpoint_sha256"] == source_checkpoint["sha256"]
        assert entry["width"] >= 1200
        assert entry["height"] >= 800
        if entry["temporary_options_used"]:
            assert entry["view_restored"] is True
            assert entry["rollback_status"] == "RolledBack"

    excluded = data["excluded_captures"]
    assert excluded[0]["role"] == "child_playground_relation_current_attempt"
    assert "near blank" in excluded[0]["reason"]
