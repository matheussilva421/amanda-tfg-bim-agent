"""Pure bridge from BIM stage plans to an injected provider invoker.

The runner owns orchestration and evidence classification.  It does not open
Revit, write files, or know how a provider transports a request.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .models import BimStage
from .providers import HorizunRequestError, McpTransportError
from .stages import ExecutionMode, StageOperation, StageToolCall
from .verification import (
    VerificationResult,
    all_layers_pass,
    overall_result,
    verify_write,
)


class RunStatus(StrEnum):
    """Status shared by operation and stage run records."""

    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    IN_DOUBT = "IN_DOUBT"


OperationRunStatus = RunStatus
StageRunStatus = RunStatus


class StageRunnerError(ValueError):
    """A stage chain or plan cannot be safely dispatched."""


@dataclass(slots=True)
class OperationRunRecord:
    stage: BimStage
    logical_id: str
    semantic_capability: str
    provider: str
    tool: str | None
    reported_success: bool
    status: RunStatus
    layers: list[VerificationResult] = field(default_factory=list)
    unique_id: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    error: Any = None


@dataclass(slots=True)
class StageRunResult:
    stage: BimStage
    status: RunStatus
    records: list[OperationRunRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


_MISSING = object()
_TRANSPORT_ERROR_TYPES = frozenset(
    {
        "connectionerror",
        "mcptimeout",
        "mcptransporterror",
        "timeouterror",
        "transporterror",
    }
)
_INDETERMINATE_STATES = frozenset(
    {"in_doubt", "indeterminate", "unknown", "uncertain", "pending"}
)


def _value(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _error_payload(error: BaseException) -> dict[str, str]:
    return {"type": type(error).__name__, "message": str(error)}


def _looks_like_transport_error(error: Any) -> bool:
    if isinstance(error, (McpTransportError, TimeoutError, ConnectionError)):
        return True
    if isinstance(error, HorizunRequestError):
        message = str(error).casefold()
        return any(
            marker in message
            for marker in (
                "transport",
                "timeout",
                "timed out",
                "connection",
                "network",
            )
        )
    if isinstance(error, Mapping):
        error_type = str(error.get("type", "")).casefold().replace(" ", "")
        if error_type in _TRANSPORT_ERROR_TYPES:
            return True
        return _looks_like_transport_error(error.get("message", ""))
    if isinstance(error, str):
        message = error.casefold()
        return any(
            marker in message
            for marker in (
                "transport",
                "timeout",
                "timed out",
                "connection",
                "network",
            )
        )
    return False


def _state_is_indeterminate(*sources: Any) -> bool:
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        for key in ("state_indeterminate", "indeterminate", "mutation_indeterminate"):
            if source.get(key) is True:
                return True
        for key in ("state", "mutation_state", "outcome"):
            value = source.get(key)
            if isinstance(value, str) and value.casefold() in _INDETERMINATE_STATES:
                return True
    return False


def _read_payload(result: Any) -> Any:
    payload = _value(result, "read_payload", _MISSING)
    if payload is not _MISSING and payload is not None:
        return payload
    return _value(result, "payload", None)


def _has_independent_read(payload: Any) -> bool:
    if not isinstance(payload, Mapping):
        return False
    if payload.get("readback_verified") is False:
        return False
    unique_id = payload.get("unique_id")
    return payload.get("readback_verified") is True or (
        isinstance(unique_id, str) and bool(unique_id.strip())
    )


def _desired_expectations(plan: Any, operation: StageOperation) -> tuple[Any, Any]:
    geometry = None
    properties = None
    desired_state = getattr(plan, "desired_state", None)
    if desired_state is not None:
        by_logical_id = getattr(desired_state, "by_logical_id", None)
        if callable(by_logical_id):
            element = by_logical_id().get(operation.logical_id)
            if element is not None:
                geometry = getattr(element, "geometry", None)
                properties = getattr(element, "properties", None)
    payload = operation.payload
    if geometry is None:
        geometry = payload.get("geometry")
    if properties is None:
        properties = payload.get("properties")
    return geometry, properties


def _preflight_messages(plan: Any) -> list[str]:
    preflight = getattr(plan, "preflight", None)
    failures = list(getattr(preflight, "failures", ()) or ())
    if not failures:
        return []
    problems = getattr(preflight, "problems", None)
    if problems:
        return [str(problem) for problem in problems]
    messages: list[str] = []
    for failure in failures:
        name = getattr(failure, "name", None)
        detail = getattr(failure, "detail", None)
        messages.append(f"{name}: {detail}" if name and detail else str(failure))
    return messages


def _selected_provider(operation: StageOperation) -> str:
    provider = operation.preferred_provider
    if provider is None and operation.fallback_providers:
        provider = operation.fallback_providers[0]
    if not provider:
        raise StageRunnerError(
            f"operation {operation.logical_id} has no selected provider"
        )
    return provider


def _validate_plan(plan: Any) -> BimStage:
    stage = getattr(plan, "stage", None)
    if not isinstance(stage, BimStage):
        raise StageRunnerError("plan stage must be a BimStage")
    if stage is BimStage.R00:
        raise StageRunnerError("R00 is not executable by the stage runner")
    failures = _preflight_messages(plan)
    if failures:
        raise StageRunnerError("preflight failures: " + "; ".join(failures))
    preflight = getattr(plan, "preflight", None)
    if getattr(preflight, "mode", None) == ExecutionMode.PLANNING_ONLY:
        raise StageRunnerError("PLANNING_ONLY plans cannot be executed")
    operations = getattr(plan, "operations", None)
    if operations is None:
        raise StageRunnerError(f"{stage.name} plan has no operations list")
    blocked = [
        (operation.logical_id, sorted(set(operation.blocked_by)))
        for operation in operations
        if isinstance(operation, StageOperation) and operation.blocked_by
    ]
    if blocked:
        details = "; ".join(
            f"{logical_id}: {', '.join(gates)}" for logical_id, gates in blocked
        )
        raise StageRunnerError("operation dispatch blocked by evidence gate: " + details)
    for operation in operations:
        if not isinstance(operation, StageOperation):
            raise StageRunnerError("plan operation must be a StageOperation")
        if operation.stage is not stage:
            raise StageRunnerError(
                f"operation {operation.logical_id} belongs to {operation.stage.name}, "
                f"not {stage.name}"
            )
        _selected_provider(operation)
    return stage


def _status_for_records(records: list[OperationRunRecord]) -> RunStatus:
    if any(record.status is RunStatus.IN_DOUBT for record in records):
        return RunStatus.IN_DOUBT
    if any(record.status is RunStatus.FAILED for record in records):
        return RunStatus.FAILED
    return RunStatus.VERIFIED


def _record_from_result(
    plan: Any,
    operation: StageOperation,
    provider: str,
    result: Any,
) -> OperationRunRecord:
    reported_success = bool(_value(result, "reported_success", False))
    payload = _read_payload(result)
    error = _value(result, "error", None)
    if error is None and isinstance(payload, Mapping):
        error = payload.get("error")
    provider_name = str(_value(result, "provider", provider) or provider)
    tool = _value(result, "tool", None)
    tool_name = str(tool) if tool is not None else None
    evidence = dict(payload) if isinstance(payload, Mapping) else {}
    unique_id = evidence.get("unique_id")
    unique_id = str(unique_id) if unique_id is not None else None

    if not reported_success:
        layers = verify_write(
            logical_id=operation.logical_id,
            tool_reported_success=False,
            query_result=None,
        )
        indeterminate = _looks_like_transport_error(error) or _state_is_indeterminate(
            result, payload, error
        )
        status = RunStatus.IN_DOUBT if indeterminate else RunStatus.FAILED
        return OperationRunRecord(
            stage=plan.stage,
            logical_id=operation.logical_id,
            semantic_capability=operation.semantic_capability,
            provider=provider_name,
            tool=tool_name,
            reported_success=False,
            status=status,
            layers=layers,
            unique_id=unique_id,
            evidence=evidence,
            error=error,
        )

    if not _has_independent_read(payload):
        layers = verify_write(
            logical_id=operation.logical_id,
            tool_reported_success=True,
            query_result=None,
        )
        missing_read = {
            "type": "IndependentReadEvidenceMissing",
            "code": "INDEPENDENT_READ_MISSING",
            "message": "provider success has no independent readback in read_payload",
        }
        return OperationRunRecord(
            stage=plan.stage,
            logical_id=operation.logical_id,
            semantic_capability=operation.semantic_capability,
            provider=provider_name,
            tool=tool_name,
            reported_success=True,
            status=RunStatus.FAILED,
            layers=layers,
            unique_id=unique_id,
            evidence=evidence,
            error=missing_read,
        )

    expected_geometry, expected_properties = _desired_expectations(plan, operation)
    query_result = payload if isinstance(payload, Mapping) else None
    requires_mass_geometry = operation.semantic_capability == "revit.create_mass"
    layers = verify_write(
        logical_id=operation.logical_id,
        tool_reported_success=True,
        query_result=query_result,
        expected_geometry=(
            expected_geometry
            if isinstance(query_result, Mapping)
            and (
                query_result.get("geometry") is not None or requires_mass_geometry
            )
            and isinstance(expected_geometry, Mapping)
            else None
        ),
        expected_properties=(
            expected_properties
            if isinstance(query_result, Mapping)
            and query_result.get("properties") is not None
            and isinstance(expected_properties, Mapping)
            else None
        ),
    )
    verdict = overall_result(layers)
    status = RunStatus.VERIFIED if all_layers_pass(layers) else RunStatus.FAILED
    if error is None and status is RunStatus.FAILED:
        error = {
            "type": "VerificationFailed",
            "code": verdict.reason.value
            if verdict.reason is not None
            else "VERIFY_FAILED",
            "message": verdict.message,
        }
    return OperationRunRecord(
        stage=plan.stage,
        logical_id=operation.logical_id,
        semantic_capability=operation.semantic_capability,
        provider=provider_name,
        tool=tool_name,
        reported_success=True,
        status=status,
        layers=layers,
        unique_id=unique_id,
        evidence=evidence,
        error=error,
    )


def _record_from_exception(
    plan: Any,
    operation: StageOperation,
    provider: str,
    error: BaseException,
) -> OperationRunRecord:
    layers = verify_write(
        logical_id=operation.logical_id,
        tool_reported_success=False,
        query_result=None,
    )
    return OperationRunRecord(
        stage=plan.stage,
        logical_id=operation.logical_id,
        semantic_capability=operation.semantic_capability,
        provider=provider,
        tool=None,
        reported_success=False,
        status=(
            RunStatus.IN_DOUBT
            if _looks_like_transport_error(error)
            else RunStatus.FAILED
        ),
        layers=layers,
        error=_error_payload(error),
    )


def execute_stage(plan: Any, *, invoker: Any) -> StageRunResult:
    """Execute one stage in operation order and classify its evidence."""

    _validate_plan(plan)
    records: list[OperationRunRecord] = []
    warnings = list(getattr(plan, "warnings", ()) or ())
    # The bridge keeps an idempotency key for exactly one operation and refuses
    # to reuse it for different work, so a stage that is deliberately re-run
    # needs its own namespace rather than replaying the previous attempt.
    run_token = uuid.uuid4().hex[:12]
    for operation in plan.operations:
        provider = _selected_provider(operation)
        payload = dict(operation.payload)
        payload.setdefault(
            "idempotency_key",
            f"bim:{plan.stage.name}:{operation.logical_id}:{run_token}",
        )
        # These are real writes, and the invoker only plans its independent READ
        # when the call says so: without an explicit dry_run=False the bridge
        # rehearses instead of writing, and no readback is scheduled.
        payload.setdefault("dry_run", False)
        call = StageToolCall(
            stage=operation.stage,
            logical_id=operation.logical_id,
            semantic_capability=operation.semantic_capability,
            provider=provider,
            payload=payload,
        )
        try:
            result = invoker.invoke(call)
        except Exception as error:  # noqa: BLE001 - provider boundary is fail-closed
            record = _record_from_exception(plan, operation, provider, error)
        else:
            record = _record_from_result(plan, operation, provider, result)
        records.append(record)
        if record.status is RunStatus.IN_DOUBT:
            break
    return StageRunResult(
        stage=plan.stage,
        status=_status_for_records(records),
        records=records,
        warnings=warnings,
    )


def _validate_chain(plans: list[Any]) -> None:
    if not plans:
        raise StageRunnerError("cannot execute an empty stage plan list")
    previous_index = -1
    seen: set[BimStage] = set()
    for plan in plans:
        stage = _validate_plan(plan)
        if stage in seen:
            raise StageRunnerError(f"duplicate stage {stage.name} in chain")
        stage_index = list(BimStage).index(stage)
        if stage_index <= previous_index:
            raise StageRunnerError("stage chain is out of order")
        seen.add(stage)
        previous_index = stage_index


def execute_chain(
    plans: Iterable[Any],
    *,
    invoker: Any,
    stop_on_failure: bool = True,
    on_stage: Callable[[StageRunResult], None] | None = None,
) -> list[StageRunResult]:
    """Execute validated stages in order, stopping at uncertainty."""

    materialized = list(plans)
    _validate_chain(materialized)
    results: list[StageRunResult] = []
    for plan in materialized:
        result = execute_stage(plan, invoker=invoker)
        results.append(result)
        if on_stage is not None:
            on_stage(result)
        if result.status is RunStatus.IN_DOUBT:
            break
        if stop_on_failure and result.status is RunStatus.FAILED:
            break
    return results


__all__ = [
    "OperationRunRecord",
    "OperationRunStatus",
    "RunStatus",
    "StageRunResult",
    "StageRunStatus",
    "StageRunnerError",
    "execute_chain",
    "execute_stage",
]
