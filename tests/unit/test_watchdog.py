from amanda_agent.recovery.watchdog import (
    WatchdogAction,
    WatchdogState,
    WatchdogInputs,
    decide,
)


def _inputs(**overrides):
    values = {
        "pid": 42,
        "process_start_time": "2026-09-15T10:00:00Z",
        "owned_pid": 42,
        "owned_start_time": "2026-09-15T10:00:00Z",
        "process_exists": True,
        "operation_elapsed_seconds": 10,
        "last_heartbeat_age_seconds": 1,
        "last_mcp_result": "PASS",
        "responsive": True,
        "cpu_percent": 10,
        "task_timeout_seconds": 30,
        "grace_period_seconds": 15,
        "normal_close_attempted": False,
        "prior_checkpoint_verified": True,
        "state_persisted_verified": True,
        "document_disposable": True,
        "force_kill_authorized": True,
    }
    values.update(overrides)
    return WatchdogInputs(**values)


def test_active_operation_is_busy_when_process_and_heartbeat_are_healthy():
    decision = decide(_inputs(operation_elapsed_seconds=20))

    assert decision.state is WatchdogState.BUSY
    assert decision.action is WatchdogAction.WAIT


def test_timeout_alone_becomes_suspected_hang_during_grace_period():
    decision = decide(
        _inputs(
            operation_elapsed_seconds=31,
            last_heartbeat_age_seconds=2,
            responsive=True,
            cpu_percent=12,
        )
    )

    assert decision.state is WatchdogState.SUSPECTED_HANG
    assert decision.action is WatchdogAction.WAIT_GRACE
    assert decision.force_kill_allowed is False


def test_multiple_signals_after_grace_require_normal_close_before_kill():
    decision = decide(
        _inputs(
            operation_elapsed_seconds=60,
            last_heartbeat_age_seconds=45,
            last_mcp_result=None,
            responsive=False,
            cpu_percent=0,
        )
    )

    assert decision.state is WatchdogState.HUNG
    assert decision.action is WatchdogAction.ATTEMPT_NORMAL_CLOSE
    assert decision.force_kill_allowed is False


def test_force_kill_is_last_action_only_for_owned_disposable_work():
    decision = decide(
        _inputs(
            operation_elapsed_seconds=60,
            last_heartbeat_age_seconds=45,
            last_mcp_result=None,
            responsive=False,
            cpu_percent=0,
            normal_close_attempted=True,
        )
    )

    assert decision.state is WatchdogState.HUNG
    assert decision.action is WatchdogAction.FORCE_KILL
    assert decision.force_kill_allowed is True


def test_unknown_or_unverified_work_is_never_force_killed():
    decision = decide(
        _inputs(
            operation_elapsed_seconds=60,
            last_heartbeat_age_seconds=45,
            last_mcp_result=None,
            responsive=False,
            cpu_percent=0,
            normal_close_attempted=True,
            owned_pid=999,
            document_disposable=False,
        )
    )

    assert decision.state is WatchdogState.HUNG
    assert decision.action is WatchdogAction.ESCALATE
    assert decision.force_kill_allowed is False
    assert "checkpoint" in decision.reason.lower() or "owned" in decision.reason.lower()


def test_missing_process_is_crashed_without_attempting_a_new_checkpoint():
    decision = decide(_inputs(process_exists=False))

    assert decision.state is WatchdogState.CRASHED
    assert decision.action is WatchdogAction.RECOVER
    assert "checkpoint" not in decision.action.value.lower()
