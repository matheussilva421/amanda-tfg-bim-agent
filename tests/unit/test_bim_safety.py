from pathlib import Path

import pytest


def test_filename_containing_golden_is_rejected():
    from amanda_agent.bim.safety import SafetyError, assert_writable_target

    with pytest.raises(SafetyError, match="protected"):
        assert_writable_target(Path("revit/production/working/GOLDEN_copy.rvt"))


def test_filename_containing_master_is_rejected():
    from amanda_agent.bim.safety import SafetyError, assert_writable_target

    with pytest.raises(SafetyError, match="protected"):
        assert_writable_target(Path("revit/production/working/MASTER_copy.rvt"))


def test_filename_containing_source_is_rejected():
    from amanda_agent.bim.safety import SafetyError, assert_writable_target

    with pytest.raises(SafetyError, match="protected"):
        assert_writable_target(Path("revit/production/working/source_copy.rvt"))


def test_canonical_working_target_is_accepted():
    from amanda_agent.bim.safety import assert_writable_target

    target = assert_writable_target(
        Path("revit/production/working/AMANDA_WORKING_001.rvt")
    )

    assert target.name == "AMANDA_WORKING_001.rvt"
    assert target.is_absolute()


def test_target_outside_allowlisted_root_is_rejected(tmp_path: Path):
    from amanda_agent.bim.safety import SafetyError, assert_writable_target

    with pytest.raises(SafetyError, match="writable root"):
        assert_writable_target(tmp_path / "outside.rvt", writable_roots=[tmp_path / "working"])


def test_active_document_switch_is_rejected(tmp_path: Path):
    from amanda_agent.bim.safety import SafetyError, assert_writable_target

    working = tmp_path / "working"
    working.mkdir()
    target = working / "AMANDA_WORKING_001.rvt"

    with pytest.raises(SafetyError, match="active document"):
        assert_writable_target(
            target,
            writable_roots=[working],
            active_document_path=working / "AMANDA_WORKING_002.rvt",
        )


def test_ambiguous_hardlink_identity_is_rejected(tmp_path: Path):
    from amanda_agent.bim.safety import SafetyError, assert_writable_target

    working = tmp_path / "working"
    working.mkdir()
    target = working / "AMANDA_WORKING_001.rvt"
    target.write_bytes(b"owned model")
    alias = working / "alias.rvt"
    try:
        alias.hardlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("hardlinks are unavailable in this test environment")

    with pytest.raises(SafetyError, match="hardlink"):
        assert_writable_target(target, writable_roots=[working])


def test_junction_escape_identity_is_rejected(tmp_path: Path):
    from amanda_agent.bim.safety import SafetyError, assert_writable_target

    real_root = tmp_path / "area-restrita"
    target_dir = tmp_path / "revit" / "production" / "working"
    try:
        real_root.mkdir()
        target_dir.parent.mkdir(parents=True)
        import _winapi

        _winapi.CreateJunction(str(real_root), str(target_dir))
    except (AttributeError, OSError, ImportError):
        pytest.skip("junctions are unavailable in this test environment")

    with pytest.raises(SafetyError, match="symlink|junction"):
        assert_writable_target(
            target_dir / "AMANDA_WORKING_001.rvt",
            writable_roots=[tmp_path],
        )


def test_broken_symlink_identity_is_rejected(tmp_path: Path, monkeypatch):
    from amanda_agent.bim import safety

    working = tmp_path / "working"
    working.mkdir()
    target = working / "AMANDA_WORKING_001.rvt"
    monkeypatch.setattr(safety, "_is_reparse_point", lambda path: path == target)

    with pytest.raises(safety.SafetyError, match="symlink|junction"):
        safety.assert_writable_target(target, writable_roots=[working])


def test_renamed_original_with_matching_file_identity_is_rejected(tmp_path: Path):
    from amanda_agent.bim.safety import (
        ProtectedIdentity,
        SafetyError,
        assert_writable_target,
    )

    working = tmp_path / "working"
    working.mkdir()
    original = tmp_path / "AMANDA_BASELINE.rvt"
    original.write_bytes(b"baseline bytes")
    stat = original.stat()
    renamed = working / "AMANDA_WORKING_001.rvt"
    original.rename(renamed)

    with pytest.raises(SafetyError, match="identity"):
        assert_writable_target(
            renamed,
            writable_roots=[working],
            protected_identities=[
                ProtectedIdentity(path=tmp_path / "AMANDA_BASELINE.rvt", file_id=(stat.st_dev, stat.st_ino))
            ],
        )


def test_destructive_operation_requires_explicit_confirmation_and_reports_reason():
    from amanda_agent.bim.safety import (
        SafetyError,
        SafetyReason,
        assert_operation_safe,
    )

    try:
        assert_operation_safe("DELETE", affected_count=1, managed_count=10)
    except SafetyError as exc:
        assert exc.reason_code is SafetyReason.EXPLICIT_CONFIRMATION_REQUIRED
        assert "confirmation" in str(exc).lower()
    else:
        pytest.fail("a destructive operation without confirmation must be refused")


def test_operation_risk_increases_with_destructive_scale():
    from amanda_agent.bim.safety import RiskLevel, classify_operation_risk

    assessment = classify_operation_risk(
        "REPLACE", affected_count=11, managed_count=100, cascade_count=2
    )

    assert assessment.destructive is True
    assert assessment.impact_count == 13
    assert assessment.risk is RiskLevel.CRITICAL
    assert assessment.ratio == pytest.approx(0.13)


def test_unknown_destructive_cascade_is_critical_and_requires_confirmation():
    from amanda_agent.bim.safety import (
        RiskLevel,
        SafetyError,
        SafetyReason,
        assert_operation_safe,
        classify_operation_risk,
    )

    assessment = classify_operation_risk(
        "DELETE", affected_count=1, managed_count=100, cascade_unknown=True
    )
    assert assessment.risk is RiskLevel.CRITICAL

    with pytest.raises(SafetyError) as caught:
        assert_operation_safe(
            "DELETE",
            affected_count=1,
            managed_count=100,
            cascade_unknown=True,
            confirmed=True,
        )
    assert caught.value.reason_code is SafetyReason.UNKNOWN_CASCADE


def test_stale_writer_lease_document_identity_is_rejected(tmp_path: Path):
    from amanda_agent.bim.safety import SafetyError, assert_writable_target

    working = tmp_path / "working"
    working.mkdir()
    with pytest.raises(SafetyError, match="lease.*document"):
        assert_writable_target(
            working / "AMANDA_WORKING_001.rvt",
            writable_roots=[working],
            active_document_id="doc-current",
            target_document_id="doc-current",
            lease={
                "owner_token": "owner-1",
                "document_identity": "doc-stale",
            },
            lease_token="owner-1",
            require_lease=True,
        )
