from __future__ import annotations

from pathlib import Path

from amanda_agent.qa.dwg import validate_dwg
from amanda_agent.qa.models import QaResult


def test_supported_signatures_are_accepted_with_limited_validation(tmp_path: Path):
    for signature in (b"AC1018", b"AC1032"):
        path = tmp_path / f"{signature.decode()}.dwg"
        path.write_bytes(signature + b"\0" * 32)
        report = validate_dwg(path)
        assert report.result is QaResult.PASS_WITH_WARNINGS
        assert any(issue.code == "LIMITED_DWG_VALIDATION" for issue in report.issues)


def test_garbage_signature_is_rejected(tmp_path: Path):
    path = tmp_path / "garbage.dwg"
    path.write_bytes(b"not a dwg")
    report = validate_dwg(path)
    assert report.result is QaResult.FAIL
    assert any(issue.code == "INVALID_DWG_SIGNATURE" for issue in report.issues)


def test_missing_and_zero_size_dwg_are_rejected(tmp_path: Path):
    assert validate_dwg(tmp_path / "missing.dwg").result is QaResult.BLOCKED_BY_INPUT
    empty = tmp_path / "empty.dwg"
    empty.write_bytes(b"")
    assert validate_dwg(empty).result is not QaResult.PASS
