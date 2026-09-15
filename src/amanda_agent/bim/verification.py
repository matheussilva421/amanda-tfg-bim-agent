"""Independent write-read-verify results for BIM operations.

Every write is verified against an independent model re-query. A successful
tool return value is never treated as proof of model success (design 3.7).
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .diff import equivalent_geometry, equivalent_properties


class VerificationLayer(StrEnum):
    EXISTENCE = "existence"
    PROPERTIES = "properties"
    GEOMETRY = "geometry"
    PERSISTENCE = "persistence"


class VerificationResult(BaseModel):
    """One auditable layer result for a managed logical element."""

    model_config = ConfigDict(extra="forbid")

    logical_id: str = Field(min_length=1)
    layer: VerificationLayer
    passed: bool
    message: str = Field(min_length=1)
    unique_id: str | None = None
    expected: Any = None
    actual: Any = None
    tolerance: float | None = None

    @property
    def ok(self) -> bool:
        return self.passed


def _fail(
    logical_id: str,
    layer: VerificationLayer,
    message: str,
    *,
    unique_id: str | None = None,
    expected: Any = None,
    actual: Any = None,
    tolerance: float | None = None,
) -> VerificationResult:
    return VerificationResult(
        logical_id=logical_id,
        layer=layer,
        passed=False,
        message=message,
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
    """Verify the four layers against an independent query result.

    Failure is loud: every layer reports its own verdict, and any failed
    layer means the overall verification FAILED.
    """

    layers: list[VerificationResult] = []
    unique_id = None if query_result is None else query_result.get("unique_id")

    if not tool_reported_success:
        layers.append(
            _fail(
                logical_id,
                VerificationLayer.EXISTENCE,
                "tool did not report success; nothing to verify",
            )
        )
        layers.append(
            _fail(
                logical_id,
                VerificationLayer.PROPERTIES,
                "tool did not report success; properties unverified",
            )
        )
        layers.append(
            _fail(
                logical_id,
                VerificationLayer.GEOMETRY,
                "tool did not report success; geometry unverified",
            )
        )
        layers.append(
            _fail(
                logical_id,
                VerificationLayer.PERSISTENCE,
                "tool did not report success; persistence unverified",
            )
        )
        return layers

    if query_result is None:
        layers.append(
            _fail(
                logical_id,
                VerificationLayer.EXISTENCE,
                "independent query did not return the element after a reported success",
            )
        )
        layers.append(
            _fail(logical_id, VerificationLayer.PROPERTIES, "element missing; properties unverified")
        )
        layers.append(
            _fail(logical_id, VerificationLayer.GEOMETRY, "element missing; geometry unverified")
        )
        if require_persistence:
            layers.append(
                _fail(
                    logical_id,
                    VerificationLayer.PERSISTENCE,
                    "element missing; persistence unverified",
                )
            )
        return layers

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
    """Overall verdict: every reported layer must pass."""

    return all(result.passed for result in results)


def overall_result(results: list[VerificationResult]) -> VerificationResult:
    """Return the first failure or a summary pass."""

    failed = [result for result in results if not result.passed]
    if failed:
        first = failed[0]
        return VerificationResult(
            logical_id=first.logical_id,
            layer=VerificationLayer.EXISTENCE,
            passed=False,
            message=f"verification FAILED: {first.message}",
            unique_id=first.unique_id,
        )
    return VerificationResult(
        logical_id=results[0].logical_id if results else "unknown",
        layer=VerificationLayer.EXISTENCE,
        passed=True,
        message="verification PASSED",
    )


__all__ = [
    "VerificationLayer",
    "VerificationResult",
    "all_layers_pass",
    "overall_result",
    "verify_write",
]
