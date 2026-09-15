"""TDD contract for deterministic, content-bound release manifests."""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest


def _manifest():
    try:
        return importlib.import_module("amanda_agent.release.manifest")
    except ModuleNotFoundError as exc:
        pytest.fail(f"release manifest is not implemented yet: {exc}")


def _valid_manifest(root: Path, *, include_hash: bool = True):
    module = _manifest()
    artifact = root / "model.rvt"
    artifact.write_bytes(b"stable model")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    return module.ReleaseManifest(
        project="Amanda TFG BIM Agent",
        release="RC01",
        timestamp="2026-09-15T12:00:00Z",
        revit={"product": "Revit", "build": "2027.0"},
        providers=[{"provider": "local", "commit": "a" * 40, "installed_hash": "b" * 64}],
        design_engine={"version": "1.0", "commit": "c" * 40},
        selected_solution={"id": "SOL-001", "run": "RUN-001", "seed": 7},
        requirements={"version": "req-1"},
        site={"version": "site-1"},
        regulation={"version": "reg-1"},
        qa_summary={"status": "PASS"},
        persistence_summary={"complete": True},
        exports=[{"path": "model.rvt", "mandatory": True, "validation_status": "PASS"}],
        release_profile="STUDY",
        required_checks=[{"id": "qa-critical", "mandatory": True, "status": "PASS"}],
        optional_checks=[],
        accepted_limitations=["survey pending"],
        approval_evidence={"mode": "study"},
        artifacts=[
            {
                "path": "model.rvt",
                "kind": "rvt",
                "required": True,
                "sha256": digest if include_hash else None,
            }
        ],
        content_hashes={"model.rvt": digest} if include_hash else {},
        source_export_map={"source-1": {"export": "model.rvt", "coordinates": "local"}},
    )


def test_manifest_serialization_is_deterministic(tmp_path: Path):
    module = _manifest()
    path = tmp_path / "manifest.json"
    manifest = _valid_manifest(tmp_path)

    module.write_manifest(path, manifest)
    first = path.read_bytes()
    module.write_manifest(path, module.load_manifest(path))

    assert path.read_bytes() == first
    assert json.loads(first)["project"] == "Amanda TFG BIM Agent"


def test_required_artifact_without_hash_blocks_golden(tmp_path: Path):
    module = _manifest()
    path = tmp_path / "manifest.json"
    manifest = _valid_manifest(tmp_path, include_hash=False)
    path.write_text(
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True),
        encoding="utf-8",
    )

    result = module.verify_manifest(path)

    assert result.valid is False
    assert any("hash" in error.lower() for error in result.errors)


def test_manifest_does_not_hash_itself(tmp_path: Path):
    module = _manifest()
    path = tmp_path / "manifest.json"
    module.write_manifest(path, _valid_manifest(tmp_path))

    loaded = module.load_manifest(path)

    assert "manifest.json" not in loaded.content_hashes
    assert all(artifact.path != "manifest.json" for artifact in loaded.artifacts)


def test_verify_manifest_detects_tampered_artifact(tmp_path: Path):
    module = _manifest()
    path = tmp_path / "manifest.json"
    module.write_manifest(path, _valid_manifest(tmp_path))
    (tmp_path / "model.rvt").write_bytes(b"tampered")

    result = module.verify_manifest(path)

    assert result.valid is False
    assert any("mismatch" in error.lower() for error in result.errors)
