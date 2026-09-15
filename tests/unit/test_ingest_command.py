import hashlib
from pathlib import Path

import pytest
import yaml


def test_ingest_copies_source_bytes_and_writes_manifest(tmp_path: Path):
    from amanda_agent.commands.ingest import ingest_sources

    source = tmp_path / "input.pdf"
    source.write_bytes(b"source bytes\x00\xff")

    documents = ingest_sources(tmp_path, [source])

    destination = tmp_path / "docs" / "source" / "input.pdf"
    manifest_path = tmp_path / "project" / "provenance" / "source-manifest.yaml"
    assert destination.read_bytes() == source.read_bytes()
    assert len(documents) == 1
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["documents"][0]["sha256"] == documents[0].sha256
    assert manifest["documents"][0]["immutable_path"] == "docs/source/input.pdf"


def test_ingest_recognises_identical_hash_without_duplicate_copy(tmp_path: Path):
    from amanda_agent.commands.ingest import ingest_sources

    first = tmp_path / "first.pdf"
    second = tmp_path / "renamed-copy.pdf"
    first.write_bytes(b"same source")
    second.write_bytes(first.read_bytes())

    first_result = ingest_sources(tmp_path, [first])
    second_result = ingest_sources(tmp_path, [second])

    assert second_result == first_result
    assert sorted(path.name for path in (tmp_path / "docs" / "source").iterdir()) == [
        "first.pdf"
    ]
    manifest = yaml.safe_load(
        (tmp_path / "project" / "provenance" / "source-manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert len(manifest["documents"]) == 1


def test_ingest_refuses_different_content_at_existing_immutable_path(tmp_path: Path):
    from amanda_agent.commands.ingest import (
        ImmutableSourcePathConflict,
        ingest_sources,
    )

    first = tmp_path / "source.pdf"
    first.write_bytes(b"original")
    ingest_sources(tmp_path, [first])

    replacement = tmp_path / "replacement" / "source.pdf"
    replacement.parent.mkdir()
    replacement.write_bytes(b"different")

    with pytest.raises(ImmutableSourcePathConflict, match="immutable source path"):
        ingest_sources(tmp_path, [replacement])

    assert (tmp_path / "docs" / "source" / "source.pdf").read_bytes() == b"original"


def test_ingest_refuses_an_immutable_destination_that_is_not_a_file(tmp_path: Path):
    from amanda_agent.commands.ingest import (
        ImmutableSourcePathConflict,
        ingest_sources,
    )

    destination = tmp_path / "docs" / "source" / "folder.pdf"
    destination.mkdir(parents=True)
    source = tmp_path / "folder.pdf"
    source.write_bytes(b"source")

    with pytest.raises(ImmutableSourcePathConflict, match="immutable source path"):
        ingest_sources(tmp_path, [source])


def test_ingest_rejects_manifest_paths_outside_project_root(tmp_path: Path):
    from amanda_agent.commands.ingest import SourceManifestError, ingest_sources

    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")
    outside = tmp_path.parent / "outside-source.pdf"
    outside.write_bytes(source.read_bytes())
    manifest_path = tmp_path / "project" / "provenance" / "source-manifest.yaml"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "documents": [
                    {
                        "source_id": "SRC-outside",
                        "filename": source.name,
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        "mime_type": "application/pdf",
                        "ingested_at": "2026-09-15T00:00:00Z",
                        "immutable_path": "../outside-source.pdf",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SourceManifestError, match="outside project root"):
        ingest_sources(tmp_path, [source])


def test_ingest_validates_all_manifest_paths_before_adding_a_new_source(
    tmp_path: Path,
):
    from amanda_agent.commands.ingest import SourceManifestError, ingest_sources

    source = tmp_path / "new-source.pdf"
    source.write_bytes(b"new source")
    manifest_path = tmp_path / "project" / "provenance" / "source-manifest.yaml"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "documents": [
                    {
                        "source_id": "SRC-unrelated",
                        "filename": "unrelated.pdf",
                        "sha256": hashlib.sha256(b"unrelated").hexdigest(),
                        "mime_type": "application/pdf",
                        "ingested_at": "2026-09-15T00:00:00Z",
                        "immutable_path": "project/unrelated.pdf",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SourceManifestError, match="docs/source"):
        ingest_sources(tmp_path, [source])

    assert not (tmp_path / "docs" / "source" / source.name).exists()


def test_ingest_updates_manifest_with_atomic_replace(tmp_path: Path, monkeypatch):
    from amanda_agent.commands import ingest as ingest_command

    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")
    replaced = []
    original_replace = ingest_command.os.replace

    def record_replace(source_path, destination_path):
        replaced.append((Path(source_path), Path(destination_path)))
        return original_replace(source_path, destination_path)

    monkeypatch.setattr(ingest_command.os, "replace", record_replace)

    ingest_command.ingest_sources(tmp_path, [source])

    manifest_path = tmp_path / "project" / "provenance" / "source-manifest.yaml"
    assert any(destination == manifest_path for _, destination in replaced)
    assert not list(manifest_path.parent.glob(".source-manifest.*.tmp"))
