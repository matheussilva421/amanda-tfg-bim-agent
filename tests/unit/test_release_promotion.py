"""TDD contract for immutable GOLDEN promotion guards."""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest


def _modules():
    try:
        manifest = importlib.import_module("amanda_agent.release.manifest")
        promote = importlib.import_module("amanda_agent.release.promote")
        persistence = importlib.import_module("amanda_agent.qa.persistence")
        return manifest, promote, persistence
    except ModuleNotFoundError as exc:
        pytest.fail(f"release promotion is not implemented yet: {exc}")


def _release(tmp_path: Path, *, profile: str = "STUDY", **changes):
    manifest, _, persistence = _modules()
    rc = tmp_path / "RC01"
    rc.mkdir()
    artifact = rc / "model.rvt"
    artifact.write_bytes(b"stable model")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    record = persistence.PersistenceRecord(release_id="RC01")
    for step in persistence.PersistenceStep:
        record.record_step(
            step,
            status=persistence.PersistenceStatus.PASS,
            evidence={"observed": step.value},
        )
    payload = dict(
        project="Amanda TFG BIM Agent",
        release="RC01",
        timestamp="2026-09-15T12:00:00Z",
        revit={"product": "Revit", "build": "2027.0"},
        providers=[],
        design_engine={"version": "1.0", "commit": "c" * 40},
        selected_solution={"id": "SOL-001", "run": "RUN-001", "seed": 7},
        requirements={},
        site={},
        regulation={},
        qa_summary={"status": "PASS"},
        persistence_summary=record.model_dump(mode="json"),
        exports=[{"path": "model.rvt", "mandatory": True, "validation_status": "PASS"}],
        release_profile=profile,
        required_checks=[{"id": "qa-critical", "mandatory": True, "status": "PASS"}],
        optional_checks=[],
        accepted_limitations=["survey pending"] if profile == "STUDY" else [],
        approval_evidence={"mode": "study"},
        artifacts=[{"path": "model.rvt", "kind": "rvt", "required": True, "sha256": digest}],
        content_hashes={"model.rvt": digest},
        source_export_map={},
    )
    payload.update(changes)
    manifest.write_manifest(rc / "manifest.json", manifest.ReleaseManifest(**payload))
    return rc


def test_qa_fail_blocks_promotion(tmp_path: Path):
    _, promote, _ = _modules()
    rc = _release(tmp_path, qa_summary={"status": "FAIL"})

    with pytest.raises(promote.PromotionRefused, match="QA"):
        promote.promote(rc, golden_root=tmp_path / "golden")


def test_unwaived_mandatory_blocked_check_blocks(tmp_path: Path):
    _, promote, _ = _modules()
    rc = _release(
        tmp_path,
        required_checks=[{"id": "norm", "mandatory": True, "status": "BLOCKED"}],
    )

    with pytest.raises(promote.PromotionRefused, match="mandatory"):
        promote.promote(rc, golden_root=tmp_path / "golden")


def test_incomplete_persistence_blocks(tmp_path: Path):
    _, promote, persistence = _modules()
    record = persistence.PersistenceRecord(release_id="RC01")
    rc = _release(tmp_path, persistence_summary=record.model_dump(mode="json"))

    with pytest.raises(promote.PromotionRefused, match="persistence"):
        promote.promote(rc, golden_root=tmp_path / "golden")


def test_incomplete_mandatory_export_blocks(tmp_path: Path):
    _, promote, _ = _modules()
    rc = _release(
        tmp_path,
        exports=[{"path": "model.rvt", "mandatory": True, "validation_status": "BLOCKED"}],
    )

    with pytest.raises(promote.PromotionRefused, match="export"):
        promote.promote(rc, golden_root=tmp_path / "golden")


def test_existing_golden_is_never_overwritten(tmp_path: Path):
    _, promote, _ = _modules()
    rc = _release(tmp_path)
    golden_root = tmp_path / "golden"
    target = golden_root / "RC01"
    target.mkdir(parents=True)
    sentinel = target / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(promote.PromotionRefused, match="exists"):
        promote.promote(rc, golden_root=golden_root)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_interrupted_staging_never_becomes_golden(tmp_path: Path, monkeypatch):
    _, promote, _ = _modules()
    rc = _release(tmp_path)
    golden_root = tmp_path / "golden"

    def interrupt(*args, **kwargs):
        raise OSError("simulated interruption")

    monkeypatch.setattr(promote.os, "rename", interrupt)
    with pytest.raises(OSError, match="interruption"):
        promote.promote(rc, golden_root=golden_root)

    assert not (golden_root / "RC01").exists()
    assert not any(
        child.name.startswith(".RC01.") and child.name.endswith(".staging")
        for child in golden_root.iterdir()
    )


def test_empty_issue_list_does_not_imply_acceptance(tmp_path: Path):
    _, promote, _ = _modules()
    rc = _release(tmp_path, qa_summary={"status": "PASS", "issues": []}, required_checks=[])

    with pytest.raises(promote.PromotionRefused, match="mandatory"):
        promote.promote(rc, golden_root=tmp_path / "golden")


def test_study_can_retain_visible_limitation_but_final_cannot(tmp_path: Path):
    _, promote, _ = _modules()
    study = _release(
        tmp_path / "study",
        required_checks=[
            {
                "id": "survey",
                "mandatory": True,
                "status": "BLOCKED",
                "waiver": {"reason": "survey unavailable"},
            }
        ],
        accepted_limitations=["Survey unavailable; study scope only."],
    )

    result = promote.promote(study, golden_root=tmp_path / "golden-study")
    assert result.target.is_dir()
    assert "Survey unavailable" in (result.manifest.get("accepted_limitations") or [""])[0]

    final = _release(
        tmp_path / "final",
        profile="FINAL",
        required_checks=[
            {
                "id": "survey",
                "mandatory": True,
                "status": "BLOCKED",
                "waiver": {"reason": "survey unavailable"},
            }
        ],
    )
    with pytest.raises(promote.PromotionRefused, match="FINAL"):
        promote.promote(final, golden_root=tmp_path / "golden-final")
