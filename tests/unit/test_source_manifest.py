from datetime import UTC, datetime
from pathlib import Path


def test_sha256_file_matches_known_digest_for_abc(tmp_path: Path):
    from amanda_agent.ingest.manifest import sha256_file

    source = tmp_path / "fixture.bin"
    source.write_bytes(b"abc")

    assert (
        sha256_file(source)
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_source_document_round_trips_through_json_serialisation():
    from amanda_agent.ingest.manifest import SourceDocument

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
