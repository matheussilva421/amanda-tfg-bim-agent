"""Pure Revit-process watchdog decisions with a fail-closed kill boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WatchdogState(StrEnum):
    HEALTHY = "HEALTHY"
    BUSY = "BUSY"
    SUSPECTED_HANG = "SUSPECTED_HANG"
    HUNG = "HUNG"
    CRASHED = "CRASHED"


class WatchdogAction(StrEnum):
    NONE = "NONE"
    WAIT = "WAIT"
    WAIT_GRACE = "WAIT_GRACE"
    ATTEMPT_NORMAL_CLOSE = "ATTEMPT_NORMAL_CLOSE"
    FORCE_KILL = "FORCE_KILL"
    ESCALATE = "ESCALATE"
    RECOVER = "RECOVER"


@dataclass(frozen=True)
class WatchdogInputs:
    """Measured inputs; no field causes a process lookup or a kill itself."""

    pid: int | None = None
    process_start_time: str | None = None
    start_time: str | None = None
    owned_pid: int | None = None
    owned_start_time: str | None = None
    owned_process_start_time: str | None = None
    process_exists: bool = True
    operation_elapsed_seconds: float = 0.0
    last_heartbeat_age_seconds: float | None = None
    last_mcp_result: Any = None
    responsive: bool | None = None
    cpu_percent: float | None = None
    task_timeout_seconds: float = 300.0
    grace_period_seconds: float = 30.0
    normal_close_attempted: bool = False
    prior_checkpoint_verified: bool = False
    state_persisted_verified: bool = False
    document_disposable: bool = False
    force_kill_authorized: bool = False

    def __post_init__(self) -> None:
        if self.process_start_time is None and self.start_time is not None:
            object.__setattr__(self, "process_start_time", self.start_time)
        if self.start_time is None and self.process_start_time is not None:
            object.__setattr__(self, "start_time", self.process_start_time)
        if self.owned_start_time is None and self.owned_process_start_time is not None:
            object.__setattr__(self, "owned_start_time", self.owned_process_start_time)
        if self.owned_process_start_time is None and self.owned_start_time is not None:
            object.__setattr__(self, "owned_process_start_time", self.owned_start_time)
        for name in (
            "operation_elapsed_seconds",
            "task_timeout_seconds",
            "grace_period_seconds",
        ):
            value = float(getattr(self, name))
            if value < 0:
                raise ValueError(name + " cannot be negative")
            object.__setattr__(self, name, value)
        if self.last_heartbeat_age_seconds is not None:
            age = float(self.last_heartbeat_age_seconds)
            if age < 0:
                raise ValueError("last_heartbeat_age_seconds cannot be negative")
            object.__setattr__(self, "last_heartbeat_age_seconds", age)


@dataclass(frozen=True)
class WatchdogDecision:
    state: WatchdogState
    action: WatchdogAction
    reason: str
    corroborating_signals: tuple[str, ...] = field(default_factory=tuple)
    force_kill_allowed: bool = False

    @property
    def signals(self) -> tuple[str, ...]:
        return self.corroborating_signals


def _inputs(value: WatchdogInputs | Mapping[str, Any]) -> WatchdogInputs:
    if isinstance(value, WatchdogInputs):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("watchdog inputs must be WatchdogInputs or a mapping")
    payload = dict(value)
    aliases = {
        "elapsed_seconds": "operation_elapsed_seconds",
        "operation_elapsed": "operation_elapsed_seconds",
        "timeout_seconds": "task_timeout_seconds",
        "heartbeat_age_seconds": "last_heartbeat_age_seconds",
        "mcp_result": "last_mcp_result",
        "document_is_disposable": "document_disposable",
        "checkpoint_verified": "prior_checkpoint_verified",
        "persisted_state_verified": "state_persisted_verified",
    }
    for old, new in aliases.items():
        if new not in payload and old in payload:
            payload[new] = payload[old]
    return WatchdogInputs(**payload)


def _owned_identity(inputs: WatchdogInputs) -> bool:
    return bool(
        inputs.pid is not None
        and inputs.process_start_time
        and inputs.owned_pid == inputs.pid
        and inputs.owned_start_time
        and inputs.owned_start_time == inputs.process_start_time
    )


def decide(inputs: WatchdogInputs | Mapping[str, Any]) -> WatchdogDecision:
    """Return a pure recommendation from measured process/task signals."""

    measured = _inputs(inputs)
    if not measured.process_exists:
        return WatchdogDecision(
            WatchdogState.CRASHED,
            WatchdogAction.RECOVER,
            "owned Revit process is no longer present; recover from the last verified checkpoint",
        )

    if not measured.operation_elapsed_seconds:
        return WatchdogDecision(
            WatchdogState.HEALTHY,
            WatchdogAction.NONE,
            "no active operation is being timed",
        )

    timed_out = measured.operation_elapsed_seconds >= measured.task_timeout_seconds
    heartbeat_stale = (
        measured.last_heartbeat_age_seconds is not None
        and measured.last_heartbeat_age_seconds > measured.grace_period_seconds
    )
    no_result = measured.last_mcp_result is None
    unresponsive = measured.responsive is False
    cpu_idle = measured.cpu_percent is not None and measured.cpu_percent <= 0.1
    signals = tuple(
        name
        for name, present in (
            ("task timeout", timed_out),
            ("stale MCP heartbeat", heartbeat_stale),
            ("missing MCP result", no_result),
            ("unresponsive process", unresponsive),
            ("idle process CPU", cpu_idle),
        )
        if present
    )

    if not timed_out:
        return WatchdogDecision(
            WatchdogState.BUSY,
            WatchdogAction.WAIT,
            "operation is within its task timeout",
            signals,
        )

    grace_elapsed = measured.operation_elapsed_seconds >= (
        measured.task_timeout_seconds + measured.grace_period_seconds
    )
    corroborating_count = len(signals) - 1  # timeout is not corroboration
    hung = grace_elapsed and corroborating_count >= 2
    if not hung:
        return WatchdogDecision(
            WatchdogState.SUSPECTED_HANG,
            WatchdogAction.WAIT_GRACE,
            "timeout alone or insufficient corroborating signals; wait through the grace period",
            signals,
        )

    if not measured.normal_close_attempted:
        return WatchdogDecision(
            WatchdogState.HUNG,
            WatchdogAction.ATTEMPT_NORMAL_CLOSE,
            "multiple signals corroborate a hang; attempt a normal close before any force action",
            signals,
        )

    missing_guards = []
    if not _owned_identity(measured):
        missing_guards.append("owned PID/StartTime")
    if not measured.prior_checkpoint_verified:
        missing_guards.append("verified prior checkpoint")
    if not measured.state_persisted_verified:
        missing_guards.append("verified persisted state")
    if not measured.document_disposable:
        missing_guards.append("disposable or authorized document")
    if not measured.force_kill_authorized:
        missing_guards.append("force-kill authorization")
    if missing_guards:
        return WatchdogDecision(
            WatchdogState.HUNG,
            WatchdogAction.ESCALATE,
            "force kill refused; missing " + ", ".join(missing_guards),
            signals,
        )
    return WatchdogDecision(
        WatchdogState.HUNG,
        WatchdogAction.FORCE_KILL,
        "normal close was attempted and all ownership, persistence and authorization guards passed",
        signals,
        force_kill_allowed=True,
    )


decide_watchdog = decide
evaluate_watchdog = decide
HealthState = WatchdogState


__all__ = [
    "HealthState",
    "WatchdogAction",
    "WatchdogDecision",
    "WatchdogInputs",
    "WatchdogState",
    "decide",
    "decide_watchdog",
    "evaluate_watchdog",
]
