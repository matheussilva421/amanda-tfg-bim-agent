"""TDD contract for the QA, export and release CLI boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from amanda_agent.cli import app

runner = CliRunner()


def test_qa_writes_json_and_markdown(tmp_path: Path):
    model_manifest = tmp_path / "model.json"
    model_manifest.write_text(json.dumps({"model": "fixture"}), encoding="utf-8")
    output = tmp_path / "qa-output"

    result = runner.invoke(
        app,
        [
            "qa",
            "--model-manifest",
            str(model_manifest),
            "--release-id",
            "RC01",
            "--output-dir",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (output / "RC01-qa.json").is_file()
    assert (output / "RC01-qa.md").is_file()
    assert "BLOCKED" in (output / "RC01-qa.json").read_text(encoding="utf-8")


def test_export_plan_is_read_only(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    result = runner.invoke(app, ["export", "plan", "--release-id", "RC01"])

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert result.exit_code == 0, result.output
    assert "read-only" in result.output.lower()
    assert "manifest" in result.output.lower()
    assert after == before


def test_promotion_guard_is_exposed_by_cli(tmp_path: Path):
    monkeypatch_root = tmp_path / "project"
    monkeypatch_root.mkdir()

    result = runner.invoke(
        app,
        [
            "release",
            "promote",
            "--release-id",
            "RC01",
            "--root",
            str(monkeypatch_root),
        ],
    )

    assert result.exit_code != 0
    assert "refused" in result.output.lower()


def test_release_verify_detects_wrong_hash(tmp_path: Path):
    release = tmp_path / "GOLDEN-001"
    release.mkdir()
    artifact = release / "model.rvt"
    artifact.write_bytes(b"actual")
    manifest = {
        "schema_version": 1,
        "project": "Amanda TFG BIM Agent",
        "release": "GOLDEN-001",
        "timestamp": "2026-09-15T12:00:00Z",
        "revit": {},
        "providers": [],
        "design_engine": {},
        "selected_solution": {},
        "requirements": {},
        "site": {},
        "regulation": {},
        "qa_summary": {"status": "PASS"},
        "persistence_summary": {"complete": True},
        "exports": [{"path": "model.rvt", "mandatory": True, "validation_status": "PASS"}],
        "release_profile": "STUDY",
        "required_checks": [{"id": "qa", "mandatory": True, "status": "PASS"}],
        "optional_checks": [],
        "accepted_limitations": ["study"],
        "approval_evidence": {},
        "artifacts": [
            {
                "path": "model.rvt",
                "kind": "rvt",
                "required": True,
                "sha256": hashlib.sha256(b"original").hexdigest(),
            }
        ],
        "content_hashes": {
            "model.rvt": hashlib.sha256(b"original").hexdigest()
        },
        "source_export_map": {},
    }
    (release / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "release",
            "verify",
            "--release-id",
            "GOLDEN-001",
            "--root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "mismatch" in result.output.lower()
