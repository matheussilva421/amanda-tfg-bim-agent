"""Bounded retries, fallbacks, and time decisions for one task.

The budget object is deliberately local to a task.  It records decisions for
the orchestrator, but it does not own or release a writer lease: a hard
timeout moves the task to reconciliation and leaves lease ownership to the
recovery protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class BudgetError(RuntimeError):
    """Base class for a rejected budget decision."""


class BudgetExhausted(BudgetError):
    """The requested retry or fallback budget has no capacity left."""


class MutationRetryDenied(BudgetError):
    """A mutation cannot be retried after a partial mutation was observed."""


class FallbackDenied(BudgetError):
    """A fallback is unsafe or unavailable in the current task state."""


class LoopDetected(BudgetError):
    """Equivalent failures repeated enough times to require intervention."""

    code = "LOOP_DETECTED"


class OperationKind(StrEnum):
    READ = "read"
    MUTATION = "mutation"
    # Accept the wording used by callers while retaining one counter.
    MUTATING = "mutation"


class TimeoutState(StrEnum):
    ACTIVE = "ACTIVE"
    SOFT_LIMIT = "SOFT_LIMIT"
    RECONCILIATION = "RECONCILIATION"


@dataclass(frozen=True)
class BudgetPolicy:
    """Default retry/fallback limits shared by task budget instances."""

    read_retry_budget: int = 3
    mutation_retry_budget: int = 2
    fallback_budget: int = 3
    loop_detection_threshold: int = 3

    def __post_init__(self) -> None:
        for name in (
            "read_retry_budget",
            "mutation_retry_budget",
            "fallback_budget",
            "loop_detection_threshold",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(name + " must be a non-negative integer")
        if self.loop_detection_threshold == 0:
            raise ValueError("loop_detection_threshold must be greater than zero")


@dataclass(frozen=True)
class TaskBudgetConfig:
    """Time limits belonging to one task, rather than to global policy."""

    soft_time_limit_seconds: float | None = None
    hard_time_limit_seconds: float | None = None

    def __post_init__(self) -> None:
        for name in ("soft_time_limit_seconds", "hard_time_limit_seconds"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(name + " must be non-negative")
        if (
            self.soft_time_limit_seconds is not None
            and self.hard_time_limit_seconds is not None
            and self.soft_time_limit_seconds > self.hard_time_limit_seconds
        ):
            raise ValueError("soft time limit cannot exceed hard time limit")


@dataclass(frozen=True)
class TimeoutDecision:
    state: TimeoutState
    stop_new_dispatch: bool
    enter_reconciliation: bool
    release_writer_lock: bool
    allow_fallback: bool


@dataclass
class TaskBudget:
    """Mutable budget ledger for one task execution."""

    task_id: str
    policy: BudgetPolicy = field(default_factory=BudgetPolicy)
    config: TaskBudgetConfig = field(default_factory=TaskBudgetConfig)
    read_retries_used: int = 0
    mutation_retries_used: int = 0
    fallbacks_used: int = 0
    _timeout_state: TimeoutState = field(
        default=TimeoutState.ACTIVE, init=False, repr=False
    )
    _stop_new_dispatch: bool = field(default=False, init=False, repr=False)
    _fallback_in_progress: bool = field(default=False, init=False, repr=False)
    _last_error_signature: str | None = field(default=None, init=False, repr=False)
    _equivalent_error_count: int = field(default=0, init=False, repr=False)
    _loop_detected: bool = field(default=False, init=False, repr=False)

    @property
    def timeout_state(self) -> TimeoutState:
        return self._timeout_state

    @property
    def reconciliation_required(self) -> bool:
        return self._timeout_state is TimeoutState.RECONCILIATION

    @property
    def dispatch_stopped(self) -> bool:
        return self._stop_new_dispatch

    @property
    def fallback_in_progress(self) -> bool:
        return self._fallback_in_progress

    @property
    def loop_detected(self) -> bool:
        return self._loop_detected

    @property
    def fallback_retries_used(self) -> int:
        """Compatibility name for callers treating strategies as retries."""
        return self.fallbacks_used

    def consume_retry(
        self,
        operation: OperationKind | str,
        *,
        partial_mutation: bool | None = None,
        partial_mutation_occurred: bool | None = None,
    ) -> bool:
        """Reserve one retry after the caller's post-failure inspection.

        A mutation retry is permitted only when inspection established that no
        partial mutation occurred.  The flag is intentionally explicit so a
        caller cannot accidentally treat an unknown state as safe.
        """
        kind = self._operation_kind(operation)
        if partial_mutation_occurred is not None:
            partial_mutation = partial_mutation_occurred
        if kind is OperationKind.MUTATION and partial_mutation is not False:
            if partial_mutation:
                reason = "partial mutation must be reconciled first"
            else:
                reason = "no-partial-mutation state must be verified first"
            raise MutationRetryDenied("mutation retry denied: " + reason)
        if self.reconciliation_required:
            raise BudgetExhausted(
                "retry denied for " + self.task_id + ": task is in reconciliation"
            )

        if kind is OperationKind.READ:
            if self.read_retries_used >= self.policy.read_retry_budget:
                raise BudgetExhausted("read retry budget exhausted")
            self.read_retries_used += 1
        else:
            if self.mutation_retries_used >= self.policy.mutation_retry_budget:
                raise BudgetExhausted("mutation retry budget exhausted")
            self.mutation_retries_used += 1
        return True

    def record_error_signature(self, signature: str) -> int:
        """Record one failure and raise on the configured equivalent run."""
        normalised = str(signature).strip()
        if not normalised:
            raise ValueError("error signature must not be empty")
        if normalised == self._last_error_signature:
            self._equivalent_error_count += 1
        else:
            self._last_error_signature = normalised
            self._equivalent_error_count = 1

        if self._equivalent_error_count >= self.policy.loop_detection_threshold:
            self._loop_detected = True
            raise LoopDetected(
                "LOOP_DETECTED: equivalent error signature repeated "
                + str(self._equivalent_error_count)
                + " times"
            )
        return self._equivalent_error_count

    # Short alias for orchestrators that call these failures rather than
    # signatures.
    record_failure = record_error_signature

    def check_timeout(self, *, elapsed_seconds: float) -> TimeoutDecision:
        """Apply the task's time policy without touching the writer lease."""
        if elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be non-negative")

        if self.reconciliation_required:
            return self._timeout_decision()

        hard = self.config.hard_time_limit_seconds
        if hard is not None and elapsed_seconds >= hard:
            self._timeout_state = TimeoutState.RECONCILIATION
            self._stop_new_dispatch = True
            return self._timeout_decision()

        soft = self.config.soft_time_limit_seconds
        if soft is not None and elapsed_seconds >= soft:
            self._timeout_state = TimeoutState.SOFT_LIMIT
        else:
            self._timeout_state = TimeoutState.ACTIVE
        return self._timeout_decision()

    def can_dispatch(self) -> bool:
        return not self._stop_new_dispatch

    def can_start_fallback(self) -> bool:
        return (
            not self._stop_new_dispatch
            and not self._fallback_in_progress
            and self.fallbacks_used < self.policy.fallback_budget
        )

    def consume_fallback(self) -> bool:
        """Reserve one provider/strategy from the fallback budget."""
        if self.reconciliation_required:
            raise FallbackDenied(
                "fallback denied: hard timeout requires reconciliation"
            )
        if self._fallback_in_progress:
            raise FallbackDenied("fallback denied: another fallback is in progress")
        if self.fallbacks_used >= self.policy.fallback_budget:
            raise BudgetExhausted("fallback budget exhausted")
        self.fallbacks_used += 1
        return True

    def start_fallback(self) -> bool:
        """Start a fallback while making overlap explicit and rejectable."""
        if not self.can_start_fallback():
            if self.reconciliation_required:
                raise FallbackDenied(
                    "fallback denied: hard timeout requires reconciliation"
                )
            if self._fallback_in_progress:
                raise FallbackDenied("fallback denied: another fallback is in progress")
            raise BudgetExhausted("fallback budget exhausted")
        self.consume_fallback()
        self._fallback_in_progress = True
        return True

    def finish_fallback(self) -> None:
        self._fallback_in_progress = False

    @staticmethod
    def _operation_kind(operation: OperationKind | str) -> OperationKind:
        try:
            return OperationKind(operation)
        except ValueError as exc:
            raise ValueError("unknown operation kind: " + str(operation)) from exc

    def _timeout_decision(self) -> TimeoutDecision:
        if self.reconciliation_required:
            return TimeoutDecision(
                state=TimeoutState.RECONCILIATION,
                stop_new_dispatch=True,
                enter_reconciliation=True,
                release_writer_lock=False,
                allow_fallback=False,
            )
        return TimeoutDecision(
            state=self._timeout_state,
            stop_new_dispatch=False,
            enter_reconciliation=False,
            release_writer_lock=False,
            allow_fallback=self.can_start_fallback(),
        )


# Names used by callers that describe the policy as a retry controller.
RetryPolicy = BudgetPolicy
RetryBudget = TaskBudget
