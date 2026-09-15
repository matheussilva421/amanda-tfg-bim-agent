"""Typed results for the mandatory BIM ``WRITE -> READ -> VERIFY`` gate.

Human-readable details remain available for reports, while the state and
failure reason used by the compiler are enums. A provider's success flag is
therefore never the operation's final verdict.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .diff import equivalent_geometry, equivalent_properties


class VerificationLayer(StrEnum):
    EXISTENCE = "existence"
    PROPERTIES = "properties"
    GEOMETRY = "geometry"
    PERSISTENCE = "persistence"


class WriteStatus(StrEnum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUSED = "REFUSED"
    IN_DOUBT = "IN_DOUBT"


class ReadStatus(StrEnum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    FOUND = "FOUND"
    MISSING = "MISSING"
    FAILED = "FAILED"


class VerificationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    REFUSED = "REFUSED"


class OperationStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    REFUSED = "REFUSED"
    IN_DOUBT = "IN_DOUBT"


class RefusalReason(StrEnum):
    TOOL_FAILURE = "TOOL_FAILURE"
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"
    UNIQUE_ID_MISSING = "UNIQUE_ID_MISSING"
    GEOMETRY_MISMATCH = "GEOMETRY_MISMATCH"
    PROPERTIES_MISMATCH = "PROPERTIES_MISMATCH"
    PERSISTENCE_UNPROVEN = "PERSISTENCE_UNPROVEN"
    MISSING_CAPABILITY = "MISSING_CAPABILITY"
    UNSUPPORTED_MODE = "UNSUPPORTED_MODE"
    INVALID_INPUT = "INVALID_INPUT"

    # Compatibility names for callers that describe the same typed reason.
    ELEMENT_MISSING = ELEMENT_NOT_FOUND
    PROPERTY_MISMATCH = PROPERTIES_MISMATCH


class WriteResult(BaseModel):
    """Typed outcome reported by the write boundary."""

    model_config = ConfigDict(extra="forbid")

    operation_id: str = Field(min_length=1)
    logical_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    status: WriteStatus
    reason: RefusalReason | None = None
    detail: str = Field(min_length=1)
    unique_id: str | None = None


class ReadResult(BaseModel):
    """Typed outcome of the independent model query."""

    model_config = ConfigDict(extra="forbid")

    operation_id: str = Field(min_length=1)
    logical_id: str = Field(min_length=1)
    status: ReadStatus
    reason: RefusalReason | None = None
    detail: str = Field(min_length=1)
    unique_id: str | None = None
    element: dict[str, Any] | None = None


class VerificationResult(BaseModel):
    """One auditable layer result for a managed logical element."""

    model_config = ConfigDict(extra="forbid")

    logical_id: str = Field(min_length=1)
    layer: VerificationLayer
    status: VerificationStatus
    passed: bool = False
    message: str = Field(min_length=1)
    reason: RefusalReason | None = None
    unique_id: str | None = None
    expected: Any = None
    actual: Any = None
    tolerance: float | None = None

    @model_validator(mode="before")
    @classmethod
    def bridge_legacy_boolean(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if "status" not in values and "passed" in values:
            values["status"] = (
                VerificationStatus.PASS if values["passed"] else VerificationStatus.FAIL
            )
        if "passed" not in values and "status" in values:
            values["passed"] = values["status"] is VerificationStatus.PASS or values["status"] == "PASS"
        return values

    @model_validator(mode="after")
    def align_boolean_verdict(self) -> VerificationResult:
        expected = self.status is VerificationStatus.PASS
        if self.passed != expected:
            raise ValueError("passed must agree with typed verification status")
        return self

    @property
    def ok(self) -> bool:
        return self.status is VerificationStatus.PASS


class OperationResult(BaseModel):
    """Complete typed result of one write/read/verify operation."""

    model_config = ConfigDict(extra="forbid")

    operation_id: str = Field(min_length=1)
    logical_id: str = Field(min_length=1)
    write: WriteResult
    read: ReadResult
    verifications: list[VerificationResult] = Field(default_factory=list)
    status: OperationStatus

    @property
    def write_result(self) -> WriteResult:
        return self.write

    @property
    def read_result(self) -> ReadResult:
        return self.read

    @property
    def verification_results(self) -> list[VerificationResult]:
        return self.verifications


BimOperationResult = OperationResult
WriteReadVerifyResult = OperationResult


def _fail(
    logical_id: str,
    layer: VerificationLayer,
    message: str,
    reason: RefusalReason,
    *,
    unique_id: str | None = None,
    expected: Any = None,
    actual: Any = None,
    tolerance: float | None = None,
) -> VerificationResult:
    return VerificationResult(
        logical_id=logical_id,
        layer=layer,
        status=VerificationStatus.FAIL,
        passed=False,
        message=message,
        reason=reason,
        unique_id=unique_id,
        expected=expected,
        actual=actual,
        tolerance=tolerance,
    )


def _pass(
    logical_id: str,
    layer: VerificationLayer,
    message: str,
    *,
    unique_id: str | None = None,
) -> VerificationResult:
    return VerificationResult(
        logical_id=logical_id,
        layer=layer,
        status=VerificationStatus.PASS,
        passed=True,
        message=message,
        unique_id=unique_id,
    )


def verify_write(
    *,
    logical_id: str,
    tool_reported_success: bool,
    query_result: Mapping[str, Any] | None,
    expected_geometry: Mapping[str, Any] | None = None,
    expected_properties: Mapping[str, Any] | None = None,
    geometry_tolerance: float = 1e-6,
    properties_tolerance: float = 1e-9,
    require_persistence: bool = False,
    persistence_evidence: bool = False,
) -> list[VerificationResult]:
    """Verify existence, properties, geometry and optional persistence."""

    if geometry_tolerance < 0 or properties_tolerance < 0:
        raise ValueError("verification tolerances must be non-negative")
    layers: list[VerificationResult] = []
    unique_id = None if query_result is None else query_result.get("unique_id")

    if not tool_reported_success:
        for layer in VerificationLayer:
            layers.append(
                _fail(
                    logical_id,
                    layer,
                    "tool did not report success; layer is unverified",
                    RefusalReason.TOOL_FAILURE,
                )
            )
        return layers

    if query_result is None:
        layers.extend(
            [
                _fail(
                    logical_id,
                    VerificationLayer.EXISTENCE,
                    "independent query did not return the element after a reported success",
                    RefusalReason.ELEMENT_NOT_FOUND,
                ),
                _fail(
                    logical_id,
                    VerificationLayer.PROPERTIES,
                    "element missing; properties unverified",
                    RefusalReason.ELEMENT_NOT_FOUND,
                ),
                _fail(
                    logical_id,
                    VerificationLayer.GEOMETRY,
                    "element missing; geometry unverified",
                    RefusalReason.ELEMENT_NOT_FOUND,
                ),
            ]
        )
        if require_persistence:
            layers.append(
                _fail(
                    logical_id,
                    VerificationLayer.PERSISTENCE,
                    "element missing; persistence unverified",
                    RefusalReason.ELEMENT_NOT_FOUND,
                )
            )
        return layers

    if not unique_id:
        layers.append(
            _fail(
                logical_id,
                VerificationLayer.EXISTENCE,
                "independent query returned no stable unique_id",
                RefusalReason.UNIQUE_ID_MISSING,
            )
        )
    else:
        layers.append(
            _pass(
                logical_id,
                VerificationLayer.EXISTENCE,
                "independent query returned the element",
                unique_id=unique_id,
            )
        )

    observed_properties = query_result.get("properties") or {}
    observed_geometry = query_result.get("geometry")
    if expected_geometry is not None and not equivalent_geometry(
        expected_geometry, observed_geometry, tolerance=geometry_tolerance
    ):
        layers.append(
            _fail(
                logical_id,
                VerificationLayer.GEOMETRY,
                "geometry exceeds tolerance",
                RefusalReason.GEOMETRY_MISMATCH,
                unique_id=unique_id,
                expected=expected_geometry,
                actual=observed_geometry,
                tolerance=geometry_tolerance,
            )
        )
    elif expected_geometry is not None:
        layers.append(
            _pass(
                logical_id,
                VerificationLayer.GEOMETRY,
                "geometry within tolerance",
                unique_id=unique_id,
            )
        )

    if expected_properties is not None and not equivalent_properties(
        expected_properties, observed_properties, tolerance=properties_tolerance
    ):
        layers.append(
            _fail(
                logical_id,
                VerificationLayer.PROPERTIES,
                "properties differ from expected",
                RefusalReason.PROPERTIES_MISMATCH,
                unique_id=unique_id,
                expected=expected_properties,
                actual=observed_properties,
                tolerance=properties_tolerance,
            )
        )
    elif expected_properties is not None:
        layers.append(
            _pass(
                logical_id,
                VerificationLayer.PROPERTIES,
                "properties match expected",
                unique_id=unique_id,
            )
        )

    if require_persistence:
        if not persistence_evidence:
            layers.append(
                _fail(
                    logical_id,
                    VerificationLayer.PERSISTENCE,
                    "persistence requires save/reopen evidence",
                    RefusalReason.PERSISTENCE_UNPROVEN,
                    unique_id=unique_id,
                )
            )
        else:
            layers.append(
                _pass(
                    logical_id,
                    VerificationLayer.PERSISTENCE,
                    "save/reopen persistence evidence present",
                    unique_id=unique_id,
                )
            )
    return layers


def all_layers_pass(results: list[VerificationResult]) -> bool:
    """Overall verdict: every reported layer must be typed PASS."""

    return bool(results) and all(result.status is VerificationStatus.PASS for result in results)


def overall_result(results: list[VerificationResult]) -> VerificationResult:
    """Return the first typed failure or a summary pass."""

    failed = [result for result in results if result.status is not VerificationStatus.PASS]
    if failed:
        first = failed[0]
        return VerificationResult(
            logical_id=first.logical_id,
            layer=first.layer,
            status=first.status,
            passed=False,
            message=f"verification failed at {first.layer.value}",
            reason=first.reason,
            unique_id=first.unique_id,
        )
    if not results:
        return VerificationResult(
            logical_id="unknown",
            layer=VerificationLayer.EXISTENCE,
            status=VerificationStatus.FAIL,
            passed=False,
            message="verification produced no layer result",
            reason=RefusalReason.ELEMENT_NOT_FOUND,
        )
    return VerificationResult(
        logical_id=results[0].logical_id,
        layer=VerificationLayer.EXISTENCE,
        status=VerificationStatus.PASS,
        passed=True,
        message="all verification layers passed",
        unique_id=results[0].unique_id,
    )


def build_operation_result(
    *,
    operation_id: str,
    logical_id: str,
    provider: str,
    tool_reported_success: bool,
    query_result: Mapping[str, Any] | None,
    expected_geometry: Mapping[str, Any] | None = None,
    expected_properties: Mapping[str, Any] | None = None,
    geometry_tolerance: float = 1e-6,
    properties_tolerance: float = 1e-9,
    require_persistence: bool = False,
    persistence_evidence: bool = False,
) -> OperationResult:
    """Build the operation-level typed result from write and query evidence."""

    write = WriteResult(
        operation_id=operation_id,
        logical_id=logical_id,
        provider=provider,
        status=WriteStatus.SUCCESS if tool_reported_success else WriteStatus.FAILED,
        reason=None if tool_reported_success else RefusalReason.TOOL_FAILURE,
        detail="provider reported success" if tool_reported_success else "provider reported failure",
        unique_id=None if query_result is None else query_result.get("unique_id"),
    )
    if query_result is None:
        read = ReadResult(
            operation_id=operation_id,
            logical_id=logical_id,
            status=ReadStatus.MISSING if tool_reported_success else ReadStatus.FAILED,
            reason=RefusalReason.ELEMENT_NOT_FOUND if tool_reported_success else RefusalReason.TOOL_FAILURE,
            detail="independent query did not find the element"
            if tool_reported_success
            else "write failure prevented a usable independent query",
        )
    else:
        read = ReadResult(
            operation_id=operation_id,
            logical_id=logical_id,
            status=ReadStatus.FOUND,
            detail="independent query returned the element",
            unique_id=query_result.get("unique_id"),
            element=dict(query_result),
        )
    verifications = verify_write(
        logical_id=logical_id,
        tool_reported_success=tool_reported_success,
        query_result=query_result,
        expected_geometry=expected_geometry,
        expected_properties=expected_properties,
        geometry_tolerance=geometry_tolerance,
        properties_tolerance=properties_tolerance,
        require_persistence=require_persistence,
        persistence_evidence=persistence_evidence,
    )
    status = OperationStatus.PASS if all_layers_pass(verifications) else OperationStatus.FAIL
    return OperationResult(
        operation_id=operation_id,
        logical_id=logical_id,
        write=write,
        read=read,
        verifications=verifications,
        status=status,
    )


__all__ = [
    "BimOperationResult",
    "OperationResult",
    "OperationStatus",
    "ReadResult",
    "ReadStatus",
    "RefusalReason",
    "VerificationLayer",
    "VerificationResult",
    "VerificationStatus",
    "WriteReadVerifyResult",
    "WriteResult",
    "WriteStatus",
    "all_layers_pass",
    "build_operation_result",
    "overall_result",
    "verify_write",
]
