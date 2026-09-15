from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from amanda_agent.tools.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    FailureKind,
    FailureScope,
    ProbeDenied,
)


class FakeClock:
    def __init__(self, value: float = 1_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def scope(error_signature: str = "transport-timeout") -> FailureScope:
    return FailureScope(
        provider="horizun",
        revit_build="20260716_1515(x64)",
        capability="read-levels",
        error_signature=error_signature,
    )


def test_three_consecutive_equivalent_provider_failures_open_breaker(
    tmp_path: Path,
) -> None:
    breaker = CircuitBreaker(tmp_path / "breaker.yaml")
    failure_scope = scope()

    breaker.record_failure(failure_scope, failure_kind=FailureKind.PROVIDER_HEALTH)
    breaker.record_failure(failure_scope, failure_kind=FailureKind.PROVIDER_HEALTH)
    assert breaker.get_state(failure_scope) is CircuitState.CLOSED

    breaker.record_failure(failure_scope, failure_kind=FailureKind.PROVIDER_HEALTH)

    assert breaker.get_state(failure_scope) is CircuitState.OPEN
    assert breaker.failure_count(failure_scope) == 3
    assert breaker.can_call(failure_scope) is False
    with pytest.raises(CircuitOpenError):
        breaker.assert_can_call(failure_scope)


def test_different_error_signatures_have_independent_failure_counters(
    tmp_path: Path,
) -> None:
    breaker = CircuitBreaker(tmp_path / "breaker.yaml")
    timeout = scope("transport-timeout")
    disconnected = scope("transport-disconnected")

    for _ in range(2):
        breaker.record_failure(timeout)
    for _ in range(3):
        breaker.record_failure(disconnected)

    assert breaker.get_state(timeout) is CircuitState.CLOSED
    assert breaker.failure_count(timeout) == 2
    assert breaker.get_state(disconnected) is CircuitState.OPEN


def test_success_resets_the_failure_counter_for_its_scope(tmp_path: Path) -> None:
    breaker = CircuitBreaker(tmp_path / "breaker.yaml")
    failure_scope = scope()

    breaker.record_failure(failure_scope)
    breaker.record_failure(failure_scope)
    breaker.record_success(failure_scope)
    breaker.record_failure(failure_scope)

    assert breaker.get_state(failure_scope) is CircuitState.CLOSED
    assert breaker.failure_count(failure_scope) == 1


def test_input_and_validation_errors_do_not_count_as_provider_failures(
    tmp_path: Path,
) -> None:
    breaker = CircuitBreaker(tmp_path / "breaker.yaml")
    failure_scope = scope()

    for _ in range(4):
        breaker.record_failure(failure_scope, failure_kind=FailureKind.INPUT)
    for _ in range(4):
        breaker.record_failure(failure_scope, failure_kind=FailureKind.VALIDATION)

    assert breaker.get_state(failure_scope) is CircuitState.CLOSED
    assert breaker.failure_count(failure_scope) == 0


def test_open_scope_is_persisted_and_reloaded_without_a_bom(tmp_path: Path) -> None:
    path = tmp_path / "state" / "breaker.yaml"
    failure_scope = scope()
    breaker = CircuitBreaker(path)

    for _ in range(3):
        breaker.record_failure(failure_scope)

    reloaded = CircuitBreaker(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert reloaded.get_state(failure_scope) is CircuitState.OPEN
    assert reloaded.failure_count(failure_scope) == 3
    assert payload["breakers"][0]["provider"] == "horizun"
    assert payload["breakers"][0]["revit_build"] == "20260716_1515(x64)"
    assert payload["breakers"][0]["capability"] == "read-levels"
    assert payload["breakers"][0]["error_signature"] == "transport-timeout"
    assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert not list(path.parent.glob("*.tmp"))


def test_open_breaker_requires_controlled_read_only_probe_after_cooldown(
    tmp_path: Path,
) -> None:
    clock = FakeClock()
    breaker = CircuitBreaker(
        tmp_path / "breaker.yaml",
        cooldown_seconds=30,
        clock=clock,
    )
    failure_scope = scope()
    for _ in range(3):
        breaker.record_failure(failure_scope)

    clock.advance(30)
    assert breaker.can_call(failure_scope) is False
    with pytest.raises(ProbeDenied):
        breaker.begin_probe(failure_scope, read_only=False)
    assert breaker.get_state(failure_scope) is CircuitState.OPEN

    assert breaker.begin_probe(failure_scope, read_only=True) is True
    assert breaker.get_state(failure_scope) is CircuitState.HALF_OPEN
    assert breaker.can_call(failure_scope) is False


def test_remediation_can_authorize_a_read_only_probe_before_cooldown(
    tmp_path: Path,
) -> None:
    breaker = CircuitBreaker(
        tmp_path / "breaker.yaml",
        cooldown_seconds=30,
    )
    failure_scope = scope()
    for _ in range(3):
        breaker.record_failure(failure_scope)

    assert (
        breaker.begin_probe(
            failure_scope,
            read_only=True,
            remediation_confirmed=True,
        )
        is True
    )
    assert breaker.get_state(failure_scope) is CircuitState.HALF_OPEN


def test_half_open_closes_only_after_independent_success(tmp_path: Path) -> None:
    clock = FakeClock()
    breaker = CircuitBreaker(
        tmp_path / "breaker.yaml",
        cooldown_seconds=1,
        clock=clock,
    )
    failure_scope = scope()
    for _ in range(3):
        breaker.record_failure(failure_scope)
    clock.advance(1)
    breaker.begin_probe(failure_scope, read_only=True)

    breaker.record_success(failure_scope)
    assert breaker.get_state(failure_scope) is CircuitState.HALF_OPEN
    assert breaker.failure_count(failure_scope) == 3

    breaker.record_success(failure_scope, independent=True)

    assert breaker.get_state(failure_scope) is CircuitState.CLOSED
    assert breaker.failure_count(failure_scope) == 0
    assert breaker.can_call(failure_scope) is True


def test_failed_half_open_probe_reopens_breaker(tmp_path: Path) -> None:
    clock = FakeClock()
    breaker = CircuitBreaker(
        tmp_path / "breaker.yaml",
        cooldown_seconds=1,
        clock=clock,
    )
    failure_scope = scope()
    for _ in range(3):
        breaker.record_failure(failure_scope)
    clock.advance(1)
    breaker.begin_probe(failure_scope, read_only=True)

    breaker.record_failure(failure_scope)

    assert breaker.get_state(failure_scope) is CircuitState.OPEN
    assert breaker.can_call(failure_scope) is False


def test_failed_atomic_write_preserves_previous_breaker_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "breaker.yaml"
    failure_scope = scope()
    breaker = CircuitBreaker(path)
    breaker.record_failure(failure_scope)
    before = path.read_bytes()

    def interrupted_replace(source: str, destination: str) -> None:
        raise OSError("simulated interruption")

    monkeypatch.setattr("amanda_agent.tools.circuit_breaker.os.replace", interrupted_replace)
    with pytest.raises(OSError, match="simulated interruption"):
        breaker.record_failure(failure_scope)

    assert path.read_bytes() == before
    assert CircuitBreaker(path).failure_count(failure_scope) == 1
