import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from amanda_agent.commands.design import DesignInputError, _manifest_by_id
from amanda_agent.ingest.manifest import SourceDocument, SourceManifest
from amanda_agent.ingest.validate import _ValidationContext, _validate_manifest


def test_sha256_file_matches_known_digest_for_abc(tmp_path: Path):
    from amanda_agent.ingest.manifest import sha256_file

    source = tmp_path / "fixture.bin"
    source.write_bytes(b"abc")

    assert (
        sha256_file(source)
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_source_document_round_trips_through_json_serialisation():
    original = SourceDocument(
        source_id="SRC-001",
        filename="programa_necessidades.pdf",
        sha256="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        mime_type="application/pdf",
        ingested_at=datetime(2026, 9, 15, 12, 30, tzinfo=UTC),
        immutable_path="docs/source/programa_necessidades.pdf",
    )

    restored = SourceDocument.model_validate(original.model_dump(mode="json"))

    assert restored == original


def _source_tree_with_catalogued_assets(root: Path):
    source_root = root / "docs/source"
    primary_source = source_root / "program.pdf"
    primary_source.parent.mkdir(parents=True)
    primary_source.write_bytes(b"private source")
    primary_hash = hashlib.sha256(primary_source.read_bytes()).hexdigest()

    supplemental_paths = (
        "docs/source/canonical/board.png",
        "docs/source/references/profile.yaml",
    )
    for relative in supplemental_paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("catalogued asset", encoding="utf-8")
    (source_root / "SOURCE_MANIFEST.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "assets": [{"path": path} for path in supplemental_paths],
            }
        ),
        encoding="utf-8",
    )
    manifest = SourceManifest(
        documents=[
            SourceDocument(
                source_id="SRC-001",
                filename="program.pdf",
                sha256=primary_hash,
                mime_type="application/pdf",
                ingested_at=datetime(2026, 9, 24, tzinfo=UTC),
                immutable_path="docs/source/program.pdf",
            )
        ]
    )
    persisted_manifest = root / "project/provenance/source-manifest.yaml"
    persisted_manifest.parent.mkdir(parents=True, exist_ok=True)
    persisted_manifest.write_text(
        yaml.safe_dump(manifest.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return manifest


def test_design_source_loader_accepts_catalogued_supplemental_assets(tmp_path: Path):
    manifest = _source_tree_with_catalogued_assets(tmp_path)

    records = _manifest_by_id(tmp_path, manifest)

    assert tuple(records) == ("SRC-001",)


def test_design_source_loader_rejects_uncatalogued_source_files(tmp_path: Path):
    manifest = _source_tree_with_catalogued_assets(tmp_path)
    (tmp_path / "docs/source/unclassified.bin").write_bytes(b"unknown")

    with pytest.raises(DesignInputError, match="docs/source differs"):
        _manifest_by_id(tmp_path, manifest)


def test_ingest_source_validator_rejects_uncatalogued_source_files(tmp_path: Path):
    _source_tree_with_catalogued_assets(tmp_path)
    (tmp_path / "docs/source/unclassified.bin").write_bytes(b"unknown")

    with pytest.raises(ValueError, match="docs/source diverge"):
        _validate_manifest(_ValidationContext(tmp_path))
