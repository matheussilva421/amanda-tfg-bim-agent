"""Evidence record contracts for Revit capability tests (P02-T03)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


def _reference(path: Path, content: str) -> str:
    path.write_text(content, encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{path}::sha256={digest}"


def test_write_pass_requires_independent_model_query_before_serialization(
    tmp_path: Path,
) -> None:
    from amanda_agent.tools.evidence import (
        EvidenceRecord,
        EvidenceValidationError,
    )

    fixture = _reference(tmp_path / "fixture.json", '{"wall_type": "basic"}')
    raw_output = _reference(tmp_path / "raw-output.json", '{"success": true}')
    record = EvidenceRecord(
        provider="horizun",
        tool="create_wall",
        input_fixture_reference=fixture,
        raw_output_path=raw_output,
        model_query_evidence=None,
        warnings_delta=0,
        duration_seconds=0.25,
        save_reopen_result=True,
        artifact_hashes=[],
        success=True,
        provider_commit="cc4ea04e9ecfe547ad349f22e0864019ce1ead1f",
        transport_provider="horizun-revit",
        tool_schema_hash="sha256:" + "a" * 64,
        tested_scope={"operation": "create_wall", "writes": True},
        evidence_scope="PROVIDER",
        revit_build="20260716_1515(x64)",
    )

    with pytest.raises(EvidenceValidationError, match="independent model-query"):
        record.to_provider_capability()


def test_complete_record_bridges_all_registry_evidence_fields(tmp_path: Path) -> None:
    from amanda_agent.tools.evidence import EvidenceRecord

    fixture = _reference(tmp_path / "fixture.json", '{"wall_type": "basic"}')
    raw_output = _reference(tmp_path / "raw-output.json", '{"success": true}')
    query = _reference(tmp_path / "query.json", '{"wall_id": 42}')
    persistence = _reference(tmp_path / "reopen.json", '{"wall_id": 42}')
    artifact = _reference(tmp_path / "model.rvt", "disposable model")
    record = EvidenceRecord(
        provider="horizun",
        tool="create_wall",
        input_fixture_reference=fixture,
        raw_output_path=raw_output,
        model_query_evidence={
            "independent": True,
            "references": [query],
            "result": {"wall_id": 42},
        },
        warnings_delta=1,
        duration_seconds=1.5,
        save_reopen_result={"success": True, "references": [persistence]},
        artifact_hashes=[artifact],
        success=True,
        provider_commit="cc4ea04e9ecfe547ad349f22e0864019ce1ead1f",
        transport_provider="horizun-revit",
        tool_schema_hash="sha256:" + "a" * 64,
        tested_scope={"operation": "create_wall", "writes": True},
        evidence_scope="PROVIDER",
        revit_build="20260716_1515(x64)",
    )

    capability = record.to_provider_capability()

    assert capability.status.value == "PASS_WITH_WARNINGS"
    assert capability.evidence_scope.value == "PROVIDER"
    assert capability.revit_build == "20260716_1515(x64)"
    assert capability.tool_schema_hash == "sha256:" + "a" * 64
    assert capability.save_reopen is True
    assert capability.independent_query is True
    assert capability.evidence == [fixture, raw_output, query, persistence, artifact]
    assert capability.tested_scope == {"operation": "create_wall", "writes": True}


def test_successful_read_requires_hashed_evidence_references(tmp_path: Path) -> None:
    from amanda_agent.tools.evidence import EvidenceRecord, EvidenceValidationError

    fixture = _reference(tmp_path / "fixture.json", '{"query": "levels"}')
    raw_output = _reference(tmp_path / "raw-output.json", '{"levels": []}')
    record = EvidenceRecord(
        provider="horizun",
        tool="list_levels",
        input_fixture_reference=fixture,
        raw_output_path=raw_output.split("::sha256=")[0],
        success=True,
        provider_commit="cc4ea04e9ecfe547ad349f22e0864019ce1ead1f",
        transport_provider="horizun-revit",
        tool_schema_hash="sha256:" + "a" * 64,
        tested_scope={"operation": "list_levels", "writes": False},
        evidence_scope="PROVIDER",
        revit_build="20260716_1515(x64)",
    )

    with pytest.raises(EvidenceValidationError, match="::sha256=<hash>"):
        record.to_provider_capability()


def test_write_pass_requires_save_reopen_persistence(tmp_path: Path) -> None:
    from amanda_agent.tools.evidence import EvidenceRecord, EvidenceValidationError

    fixture = _reference(tmp_path / "fixture.json", '{"wall_type": "basic"}')
    raw_output = _reference(tmp_path / "raw-output.json", '{"success": true}')
    query = _reference(tmp_path / "query.json", '{"wall_id": 42}')
    record = EvidenceRecord(
        provider="horizun",
        tool="create_wall",
        input_fixture_reference=fixture,
        raw_output_path=raw_output,
        model_query_evidence={"independent": True, "references": [query]},
        success=True,
        save_reopen_result=False,
        provider_commit="cc4ea04e9ecfe547ad349f22e0864019ce1ead1f",
        transport_provider="horizun-revit",
        tool_schema_hash="sha256:" + "a" * 64,
        tested_scope={"operation": "create_wall", "writes": True},
        evidence_scope="PROVIDER",
        revit_build="20260716_1515(x64)",
    )

    with pytest.raises(EvidenceValidationError, match="save/reopen"):
        record.to_provider_capability()


def test_evidence_hash_mismatch_is_rejected_by_bridge(tmp_path: Path) -> None:
    from amanda_agent.tools.evidence import EvidenceRecord, EvidenceValidationError

    fixture = _reference(tmp_path / "fixture.json", '{"query": "levels"}')
    raw_output = _reference(tmp_path / "raw-output.json", '{"levels": []}')
    raw_path = Path(raw_output.split("::sha256=")[0])
    raw_path.write_text('{"levels": ["tampered"]}', encoding="utf-8")
    record = EvidenceRecord(
        provider="horizun",
        tool="list_levels",
        input_fixture_reference=fixture,
        raw_output_path=raw_output,
        success=True,
        provider_commit="cc4ea04e9ecfe547ad349f22e0864019ce1ead1f",
        transport_provider="horizun-revit",
        tool_schema_hash="sha256:" + "a" * 64,
        tested_scope={"operation": "list_levels", "writes": False},
        evidence_scope="PROVIDER",
        revit_build="20260716_1515(x64)",
    )

    with pytest.raises(EvidenceValidationError, match="hash mismatch"):
        record.to_provider_capability()
