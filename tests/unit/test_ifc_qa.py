from __future__ import annotations

from pathlib import Path

from amanda_agent.qa.ifc import create_minimal_ifc, validate_ifc
from amanda_agent.qa.models import QaResult


def test_generated_fixture_parses_and_counts_core_entities(tmp_path: Path):
    path = create_minimal_ifc(tmp_path / "fixture.ifc")
    result = validate_ifc(
        path,
        expected_counts={"storeys": 1, "spaces": 1, "walls": 1, "doors": 1},
    )
    assert result.result is QaResult.PASS
    assert result.details["counts"] == {"storeys": 1, "spaces": 1, "walls": 1, "doors": 1}


def test_zero_byte_and_unparseable_ifc_are_rejected(tmp_path: Path):
    empty = tmp_path / "empty.ifc"
    empty.write_bytes(b"")
    garbage = tmp_path / "garbage.ifc"
    garbage.write_text("not an IFC", encoding="ascii")

    assert validate_ifc(empty).result is not QaResult.PASS
    assert validate_ifc(garbage).result is not QaResult.PASS


def test_logical_id_to_ifc_guid_mapping_is_validated(tmp_path: Path):
    path = create_minimal_ifc(tmp_path / "fixture.ifc")
    parsed = validate_ifc(path)
    guid = parsed.details["logical_id_map"]["space-01"]

    mapped = validate_ifc(path, logical_id_map={"space-01": guid})
    assert mapped.result is QaResult.PASS

    missing = validate_ifc(path, logical_id_map={"space-01": "0" * 22})
    assert missing.result is QaResult.FAIL
    assert any(issue.code == "LOGICAL_ID_MAPPING_MISMATCH" for issue in missing.issues)
