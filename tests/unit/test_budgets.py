"""Contract tests for retry, fallback, and task time budgets."""

from pathlib import Path

import pytest

from amanda_agent.state.budgets import (
    BudgetExhausted,
    BudgetPolicy,
    FallbackDenied,
    LoopDetected,
    MutationRetryDenied,
    OperationKind,
    TaskBudget,
    TaskBudgetConfig,
    TimeoutState,
)
from amanda_agent.state.locks import WriterLock


def test_default_policy_exhausts_idempotent_read_retry_budget():
    budget = TaskBudget("P07-T05")

    assert budget.policy.read_retry_budget == 3
    assert [budget.consume_retry(OperationKind.READ) for _ in range(3)] == [
        True,
        True,
        True,
    ]
    with pytest.raises(BudgetExhausted, match="read"):
        budget.consume_retry(OperationKind.READ)


def test_mutating_retry_is_denied_when_partial_mutation_was_observed():
    budget = TaskBudget("P07-T05")

    with pytest.raises(MutationRetryDenied, match="partial mutation"):
        budget.consume_retry(OperationKind.MUTATION, partial_mutation=True)

    assert budget.mutation_retries_used == 0


def test_mutating_retry_requires_explicit_no_partial_mutation_confirmation():
    budget = TaskBudget("P07-T05")

    with pytest.raises(MutationRetryDenied, match="verified"):
        budget.consume_retry(OperationKind.MUTATION)

    assert budget.consume_retry(OperationKind.MUTATION, partial_mutation=False)


def test_equivalent_error_signatures_trigger_loop_detection():
    budget = TaskBudget("P07-T05")

    budget.record_error_signature("E02:provider-unavailable")
    budget.record_error_signature("E02:provider-unavailable")
    with pytest.raises(LoopDetected, match="LOOP_DETECTED"):
        budget.record_error_signature("E02:provider-unavailable")


def test_fallback_budget_allows_three_registered_strategies():
    budget = TaskBudget("P07-T05")

    assert budget.policy.fallback_budget == 3
    assert [budget.consume_fallback() for _ in range(3)] == [True, True, True]
    with pytest.raises(BudgetExhausted, match="fallback"):
        budget.consume_fallback()


def test_hard_timeout_enters_reconciliation_without_releasing_lock_or_starting_fallback(
    tmp_path: Path,
):
    lease_path = tmp_path / "state" / "locks" / "revit-writer.lock"
    lock = WriterLock(lease_path, owner="budget-test")
    lock.acquire()
    try:
        budget = TaskBudget(
            "P07-T05",
            config=TaskBudgetConfig(
                soft_time_limit_seconds=5,
                hard_time_limit_seconds=10,
            ),
        )

        decision = budget.check_timeout(elapsed_seconds=10)

        assert decision.state is TimeoutState.RECONCILIATION
        assert decision.stop_new_dispatch is True
        assert decision.enter_reconciliation is True
        assert decision.release_writer_lock is False
        assert decision.allow_fallback is False
        assert budget.can_dispatch() is False
        assert budget.can_start_fallback() is False
        assert lock.inspect() is not None
        with pytest.raises(FallbackDenied, match="reconciliation"):
            budget.consume_fallback()
    finally:
        lock.release()


def test_soft_limit_keeps_dispatch_available_until_hard_limit():
    budget = TaskBudget(
        "P07-T05",
        config=TaskBudgetConfig(
            soft_time_limit_seconds=5,
            hard_time_limit_seconds=10,
        ),
    )

    decision = budget.check_timeout(elapsed_seconds=5)

    assert decision.state is TimeoutState.SOFT_LIMIT
    assert decision.stop_new_dispatch is False
    assert budget.can_dispatch() is True


def test_task_time_limits_are_configuration_and_not_global_policy():
    policy = BudgetPolicy()
    first = TaskBudget(
        "P07-T05-A",
        policy=policy,
        config=TaskBudgetConfig(hard_time_limit_seconds=10),
    )
    second = TaskBudget(
        "P07-T05-B",
        policy=policy,
        config=TaskBudgetConfig(hard_time_limit_seconds=20),
    )

    assert first.config.hard_time_limit_seconds == 10
    assert second.config.hard_time_limit_seconds == 20
