import hashlib
from pathlib import Path

import pytest


def test_checkpoint_copy_publishes_equal_hash_manifest(tmp_path: Path):
    from amanda_agent.bim.checkpoints import CheckpointManager

    source = tmp_path / "working.rvt"
    target = tmp_path / "R01_PROJECT_INITIALIZED.rvt"
    source.write_bytes(b"stable model bytes")

    manifest = CheckpointManager().create_checkpoint(
        source, target, stage="R01_PROJECT_INITIALIZED"
    )

    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    assert target.read_bytes() == source.read_bytes()
    assert manifest.sha256 == expected
    assert manifest.manifest_path.is_file()
    assert manifest.manifest_path.read_text(encoding="utf-8").find(expected) >= 0


def test_checkpoint_refuses_active_or_incomplete_save(tmp_path: Path):
    from amanda_agent.bim.checkpoints import CheckpointError, CheckpointManager

    source = tmp_path / "working.rvt"
    source.write_bytes(b"model")

    with pytest.raises(CheckpointError, match="save"):
        CheckpointManager().create_checkpoint(
            source,
            tmp_path / "checkpoint.rvt",
            stage="R01_PROJECT_INITIALIZED",
            save_in_progress=True,
        )


def test_checkpoint_failure_does_not_publish_a_manifest(tmp_path: Path):
    from amanda_agent.bim.checkpoints import CheckpointError, CheckpointManager

    missing = tmp_path / "missing.rvt"
    target = tmp_path / "checkpoint.rvt"

    with pytest.raises((CheckpointError, FileNotFoundError)):
        CheckpointManager().create_checkpoint(
            missing, target, stage="R01_PROJECT_INITIALIZED"
        )

    assert not target.exists()
    assert not target.with_suffix(target.suffix + ".manifest.json").exists()


def test_existing_checkpoint_path_cannot_be_overwritten(tmp_path: Path):
    from amanda_agent.bim.checkpoints import CheckpointError, CheckpointManager

    source = tmp_path / "working.rvt"
    target = tmp_path / "checkpoint.rvt"
    source.write_bytes(b"new bytes")
    target.write_bytes(b"old bytes")

    with pytest.raises(CheckpointError, match="already exists"):
        CheckpointManager().create_checkpoint(
            source, target, stage="R01_PROJECT_INITIALIZED"
        )
    assert target.read_bytes() == b"old bytes"


def test_golden_cannot_be_used_as_checkpoint_target(tmp_path: Path):
    from amanda_agent.bim.checkpoints import CheckpointError, CheckpointManager

    source = tmp_path / "working.rvt"
    source.write_bytes(b"model")

    with pytest.raises(CheckpointError, match="protected"):
        CheckpointManager().create_checkpoint(
            source, tmp_path / "GOLDEN.rvt", stage="R16_GOLDEN"
        )


def test_rollback_verifies_checkpoint_hash_before_copy(tmp_path: Path):
    from amanda_agent.bim.checkpoints import CheckpointError, CheckpointManager

    source = tmp_path / "working.rvt"
    checkpoint = tmp_path / "R01.rvt"
    restore = tmp_path / "restore.rvt"
    source.write_bytes(b"known good")
    manager = CheckpointManager()
    manifest = manager.create_checkpoint(source, checkpoint, stage="R01")
    checkpoint.write_bytes(b"tampered")

    with pytest.raises(CheckpointError, match="hash"):
        manager.rollback(manifest, restore)
    assert not restore.exists()


def test_manifest_keeps_version_document_identity_and_provenance(tmp_path: Path):
    from amanda_agent.bim.checkpoints import CheckpointManager, CheckpointManifest

    source = tmp_path / "working.rvt"
    target = tmp_path / "R02_SITE.rvt"
    source.write_bytes(b"document bytes")

    manifest = CheckpointManager().create_checkpoint(
        source,
        target,
        stage="R02_SITE",
        document_id="doc-001",
        provenance={"generation_run": "run-001", "source_refs": ["site-v1"]},
    )
    loaded = CheckpointManifest.load(manifest.manifest_path)

    assert manifest.version == 1
    assert manifest.source_sha256 == manifest.sha256
    assert manifest.document_id == "doc-001"
    assert manifest.provenance["generation_run"] == "run-001"
    assert loaded.document_id == manifest.document_id
    assert loaded.provenance == manifest.provenance


def test_rollback_refuses_checkpoint_for_a_different_current_document(tmp_path: Path):
    from amanda_agent.bim.checkpoints import CheckpointError, CheckpointManager

    source = tmp_path / "working.rvt"
    checkpoint = tmp_path / "R02.rvt"
    restore = tmp_path / "restore.rvt"
    source.write_bytes(b"known good")
    manager = CheckpointManager()
    manifest = manager.create_checkpoint(
        source, checkpoint, stage="R02", document_id="doc-before-save-as"
    )

    with pytest.raises(CheckpointError, match="document identity") as caught:
        manager.rollback(
            manifest,
            restore,
            current_document_id="doc-after-save-as",
        )

    assert caught.value.reason_code == "DOCUMENT_IDENTITY_MISMATCH"
    assert not restore.exists()


def test_rollback_requires_current_identity_when_manifest_has_one(tmp_path: Path):
    from amanda_agent.bim.checkpoints import CheckpointError, CheckpointManager

    source = tmp_path / "working.rvt"
    checkpoint = tmp_path / "R02.rvt"
    restore = tmp_path / "restore.rvt"
    source.write_bytes(b"known good")
    manager = CheckpointManager()
    manifest = manager.create_checkpoint(
        source, checkpoint, stage="R02", document_id="doc-001"
    )

    with pytest.raises(CheckpointError, match="current document"):
        manager.rollback(manifest, restore)


def test_rollback_requires_current_path_when_manifest_has_only_document_path(
    tmp_path: Path,
):
    from amanda_agent.bim.checkpoints import CheckpointError, CheckpointManager

    source = tmp_path / "working.rvt"
    checkpoint = tmp_path / "R02.rvt"
    restore = tmp_path / "restore.rvt"
    source.write_bytes(b"known good")
    manager = CheckpointManager()
    manifest = manager.create_checkpoint(
        source,
        checkpoint,
        stage="R02",
        document_path=source,
    )

    with pytest.raises(CheckpointError, match="current document"):
        manager.rollback(manifest, restore)


def test_checkpoint_protection_applies_to_parent_directories(tmp_path: Path):
    from amanda_agent.bim.checkpoints import CheckpointError, CheckpointManager

    source = tmp_path / "working.rvt"
    source.write_bytes(b"model")

    with pytest.raises(CheckpointError, match="protected"):
        CheckpointManager().create_checkpoint(
            source,
            tmp_path / "GOLDEN" / "R02.rvt",
            stage="R02",
        )
