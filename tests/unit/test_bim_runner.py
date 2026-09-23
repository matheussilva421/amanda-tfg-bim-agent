"""Contract tests for the pure BIM stage runner bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.providers import McpTransportError
from amanda_agent.bim.stages import StageOperation


@dataclass
class FakePreflight:
    failures: list[Any] = field(default_factory=list)

    @property
    def problems(self) -> list[str]:
        return [str(item) for item in self.failures]


@dataclass
class FakePlan:
    stage: BimStage
    operations: list[StageOperation]
    preflight: FakePreflight = field(default_factory=FakePreflight)
    warnings: list[str] = field(default_factory=list)


def _operation(
    stage: BimStage = BimStage.R01,
    logical_id: str = "PROJECT-001",
) -> StageOperation:
    return StageOperation(
        stage=stage,
        logical_id=logical_id,
        semantic_capability="revit.create_project",
        payload={
            "properties": {"project_name": "SYNTHETIC"},
            "idempotency_key": "provided-key",
        },
        preferred_provider="fake-provider",
    )


class SuccessfulInvoker:
    def __init__(self) -> None:
        self.calls: list[Any] = []

    def invoke(self, call: Any) -> dict[str, Any]:
        self.calls.append(call)
        return {
            "provider": "fake-provider",
            "tool": "fake-write",
            "reported_success": True,
            "read_payload": {
                "unique_id": "uid:PROJECT-001",
                "readback_verified": True,
                "properties": {"project_name": "SYNTHETIC"},
            },
        }


def test_execute_stage_reports_verified_after_independent_readback() -> None:
    from amanda_agent.bim.runner import RunStatus, execute_stage

    invoker = SuccessfulInvoker()
    result = execute_stage(FakePlan(BimStage.R01, [_operation()]), invoker=invoker)

    assert result.status is RunStatus.VERIFIED
    assert len(result.records) == 1
    record = result.records[0]
    assert record.status is RunStatus.VERIFIED
    assert record.unique_id == "uid:PROJECT-001"
    assert all(layer.passed for layer in record.layers)
    assert invoker.calls[0].payload["idempotency_key"] == "provided-key"


def test_success_without_independent_readback_is_failed_with_typed_reason() -> None:
    from amanda_agent.bim.runner import RunStatus, execute_stage

    class NoReadInvoker(SuccessfulInvoker):
        def invoke(self, call: Any) -> dict[str, Any]:
            self.calls.append(call)
            return {"reported_success": True, "tool": "fake-write"}

    result = execute_stage(
        FakePlan(BimStage.R01, [_operation()]), invoker=NoReadInvoker()
    )

    assert result.status is RunStatus.FAILED
    assert result.records[0].status is RunStatus.FAILED
    assert result.records[0].error["code"] == "INDEPENDENT_READ_MISSING"


def test_provider_failure_is_failed_and_preserves_provider_error() -> None:
    from amanda_agent.bim.runner import RunStatus, execute_stage

    provider_error = {"type": "ProviderFailure", "message": "transaction refused"}

    class FailingInvoker(SuccessfulInvoker):
        def invoke(self, call: Any) -> dict[str, Any]:
            self.calls.append(call)
            return {
                "provider": "fake-provider",
                "tool": "fake-write",
                "reported_success": False,
                "error": provider_error,
            }

    result = execute_stage(
        FakePlan(BimStage.R01, [_operation()]), invoker=FailingInvoker()
    )

    assert result.status is RunStatus.FAILED
    assert result.records[0].status is RunStatus.FAILED
    assert result.records[0].error == provider_error


def test_failed_provider_with_indeterminate_state_is_in_doubt() -> None:
    from amanda_agent.bim.runner import RunStatus, execute_stage

    class IndeterminateInvoker(SuccessfulInvoker):
        def invoke(self, call: Any) -> dict[str, Any]:
            self.calls.append(call)
            return {
                "provider": "fake-provider",
                "tool": "fake-write",
                "reported_success": False,
                "state": "unknown",
                "error": {"type": "ProviderFailure", "message": "partial result"},
            }

    result = execute_stage(
        FakePlan(BimStage.R01, [_operation()]), invoker=IndeterminateInvoker()
    )

    assert result.status is RunStatus.IN_DOUBT
    assert result.records[0].status is RunStatus.IN_DOUBT


def test_returned_transport_error_is_in_doubt() -> None:
    from amanda_agent.bim.runner import RunStatus, execute_stage

    class ReturnedTransportErrorInvoker(SuccessfulInvoker):
        def invoke(self, call: Any) -> dict[str, Any]:
            self.calls.append(call)
            return {
                "reported_success": False,
                "error": {"type": "McpTransportError", "message": "pipe closed"},
            }

    result = execute_stage(
        FakePlan(BimStage.R01, [_operation()]), invoker=ReturnedTransportErrorInvoker()
    )

    assert result.status is RunStatus.IN_DOUBT
    assert result.records[0].status is RunStatus.IN_DOUBT


def test_transport_error_is_in_doubt_and_stops_following_mutations() -> None:
    from amanda_agent.bim.runner import RunStatus, execute_chain

    class TransportFailingInvoker(SuccessfulInvoker):
        def invoke(self, call: Any) -> dict[str, Any]:
            self.calls.append(call)
            if len(self.calls) == 1:
                raise McpTransportError("transport disconnected")
            return {
                "reported_success": True,
                "read_payload": {
                    "unique_id": "uid:SECOND",
                    "readback_verified": True,
                },
            }

    invoker = TransportFailingInvoker()
    plan = FakePlan(
        BimStage.R01,
        [_operation(logical_id="FIRST"), _operation(logical_id="SECOND")],
    )

    results = execute_chain([plan], invoker=invoker)

    assert results[0].status is RunStatus.IN_DOUBT
    assert results[0].records[0].status is RunStatus.IN_DOUBT
    assert [call.logical_id for call in invoker.calls] == ["FIRST"]


def test_chain_rejects_empty_out_of_order_duplicate_and_failed_preflight() -> None:
    from amanda_agent.bim.runner import StageRunnerError, execute_chain

    with pytest.raises(StageRunnerError, match="empty"):
        execute_chain([], invoker=SuccessfulInvoker())

    with pytest.raises(StageRunnerError, match="order"):
        execute_chain(
            [
                FakePlan(BimStage.R02, [_operation(BimStage.R02, "R02")]),
                FakePlan(BimStage.R01, [_operation(BimStage.R01, "R01")]),
            ],
            invoker=SuccessfulInvoker(),
        )
    with pytest.raises(StageRunnerError, match="duplicate"):
        execute_chain(
            [
                FakePlan(BimStage.R01, [_operation()]),
                FakePlan(BimStage.R01, [_operation()]),
            ],
            invoker=SuccessfulInvoker(),
        )

    with pytest.raises(StageRunnerError, match="original preflight failure"):
        execute_chain(
            [
                FakePlan(
                    BimStage.R01,
                    [_operation()],
                    preflight=FakePreflight(["original preflight failure"]),
                )
            ],
            invoker=SuccessfulInvoker(),
        )


def test_execute_stage_refuses_planning_only_plan_before_invoker():
    from amanda_agent.bim.runner import StageRunnerError, execute_stage

    plan = FakePlan(BimStage.R01, [_operation()])
    plan.preflight.mode = "PLANNING_ONLY"
    invoker = SuccessfulInvoker()

    with pytest.raises(StageRunnerError, match="PLANNING_ONLY"):
        execute_stage(plan, invoker=invoker)

    assert invoker.calls == []


def test_execute_stage_refuses_operations_with_unmet_evidence_gates():
    from amanda_agent.bim.runner import StageRunnerError, execute_stage

    operation = _operation()
    operation.blocked_by = ["BIM-00"]
    invoker = SuccessfulInvoker()

    with pytest.raises(StageRunnerError, match="BIM-00"):
        execute_stage(FakePlan(BimStage.R01, [operation]), invoker=invoker)

    assert invoker.calls == []
