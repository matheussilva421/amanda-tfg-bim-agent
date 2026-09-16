"""Focused contract tests for the synthetic R14 to R16 release drill."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from amanda_agent.commands.export import verify_exports
from amanda_agent.qa.persistence import PersistenceStep
from amanda_agent.release.manifest import load_manifest, verify_manifest, write_manifest
from amanda_agent.release.promote import PromotionRefused, promote, verify_release
from scripts.bim_release_drill import (
    build_persistence_actions,
    main,
    run_release_drill,
)


def test_dry_run_returns_plan_without_writing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "lab"

    exit_code = main(["--release-root", str(root), "--release-id", "RC01"])

    assert exit_code == 0
    assert "dry-run" in capsys.readouterr().out.casefold()
    assert not root.exists()


def test_complete_drill_passes_qa_persistence_exports_manifest_and_promotion(tmp_path: Path) -> None:
    root = tmp_path / "lab"

    result = run_release_drill(root, "RC01", execute=True)

    source = root / "RC01"
    golden = root / "GOLDEN" / "RC01"
    assert result.success is True
    assert result.second_promotion_refused is True
    assert source.is_dir()
    assert golden.is_dir()
    assert (source / "model.rvt").is_file()
    assert (source / "exports" / "model.ifc").is_file()
    assert (source / "exports" / "documentation.pdf").is_file()
    assert (source / "exports" / "documentation.dwg").is_file()
    fixture_manifest = json.loads(
        (source / "model-manifest.json").read_text(encoding="utf-8")
    )
    assert fixture_manifest["source_plan"] == "P05"
    assert fixture_manifest["plan_05"]["stages"][-1] == "DOCUMENTATION"
    assert verify_manifest(source / "manifest.json").valid is True
    assert verify_exports(root, "RC01").valid is True
    assert verify_release(source).valid is True
    assert verify_release(golden, require_sealed=True).valid is True


def test_missing_close_and_hash_keeps_release_unpromotable(tmp_path: Path) -> None:
    root = tmp_path / "lab"
    source = root / "RC01"
    actions = build_persistence_actions(source / "model.rvt")
    actions.pop(PersistenceStep.CLOSE_AND_HASH)

    result = run_release_drill(
        root,
        "RC01",
        execute=True,
        persistence_actions=actions,
    )

    assert result.success is False
    assert not (root / "GOLDEN" / "RC01").exists()
    assert verify_release(source).valid is False
    with pytest.raises(PromotionRefused, match="persistence"):
        promote(source, golden_root=root / "GOLDEN")


def test_invalid_mandatory_export_status_keeps_release_unpromotable(tmp_path: Path) -> None:
    root = tmp_path / "lab"
    run_release_drill(root, "RC01", execute=True)
    manifest_path = root / "RC01" / "manifest.json"
    manifest = load_manifest(manifest_path)
    manifest.exports[0]["validation_status"] = "BLOCKED"
    write_manifest(manifest_path, manifest)

    assert verify_release(root / "RC01").valid is False
    with pytest.raises(PromotionRefused, match="mandatory export"):
        promote(root / "RC01", golden_root=root / "another-golden")


def test_second_promotion_to_same_target_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "lab"
    result = run_release_drill(root, "RC01", execute=True)

    with pytest.raises(PromotionRefused, match="already exists"):
        promote(result.release_directory, golden_root=root / "GOLDEN")


def test_divergent_export_hash_is_detected_by_manifest_and_export_verification(tmp_path: Path) -> None:
    root = tmp_path / "lab"
    run_release_drill(root, "RC01", execute=True)
    ifc_path = root / "RC01" / "exports" / "model.ifc"
    ifc_path.write_bytes(ifc_path.read_bytes() + b"tampered")

    manifest_result = verify_manifest(root / "RC01" / "manifest.json")
    export_result = verify_exports(root, "RC01")
    assert manifest_result.valid is False
    assert any("hash mismatch" in error for error in manifest_result.errors)
    assert export_result.valid is False
    assert any("hash mismatch" in error for error in export_result.errors)
