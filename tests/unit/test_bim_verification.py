"""Typed write-read-verify behavior for the BIM compiler (P05-T08)."""

from __future__ import annotations

from amanda_agent.bim.verification import (
    OperationStatus,
    ReadStatus,
    RefusalReason,
    VerificationStatus,
    WriteStatus,
    build_operation_result,
)


def _query(geometry=None):
    return {
        "logical_id": "ROOM-01",
        "unique_id": "uid-1",
        "geometry": geometry or {"bounds": [0.0, 0.0, 3.0, 4.0]},
        "properties": {"name": "Acolhimento"},
    }


def test_tool_success_but_missing_query_is_a_typed_failure():
    result = build_operation_result(
        operation_id="op-01",
        logical_id="ROOM-01",
        provider="horizun",
        tool_reported_success=True,
        query_result=None,
    )

    assert result.status is OperationStatus.FAIL
    assert result.write.status is WriteStatus.SUCCESS
    assert result.read.status is ReadStatus.MISSING
    assert result.read.reason is RefusalReason.ELEMENT_NOT_FOUND
    assert any(item.status is VerificationStatus.FAIL for item in result.verifications)


def test_geometry_outside_tolerance_is_a_typed_failure():
    result = build_operation_result(
        operation_id="op-02",
        logical_id="ROOM-01",
        provider="horizun",
        tool_reported_success=True,
        query_result=_query({"bounds": [0.0, 0.0, 3.0, 5.0]}),
        expected_geometry={"bounds": [0.0, 0.0, 3.0, 4.0]},
    )

    geometry = [item for item in result.verifications if item.layer.value == "geometry"]
    assert len(geometry) == 1
    assert geometry[0].status is VerificationStatus.FAIL
    assert geometry[0].reason is RefusalReason.GEOMETRY_MISMATCH


def test_correct_write_read_verify_is_a_typed_pass():
    result = build_operation_result(
        operation_id="op-03",
        logical_id="ROOM-01",
        provider="horizun",
        tool_reported_success=True,
        query_result=_query(),
        expected_geometry={"bounds": [0.0, 0.0, 3.0, 4.0]},
        expected_properties={"name": "Acolhimento"},
    )

    assert result.status is OperationStatus.PASS
    assert result.write.status is WriteStatus.SUCCESS
    assert result.read.status is ReadStatus.FOUND
    assert all(item.status is VerificationStatus.PASS for item in result.verifications)
