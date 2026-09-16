"""Contract tests for the fail-closed BIM lab preflight."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from amanda_agent.bim.providers import McpTransportError
from amanda_agent.state.locks import WriterLock
from scripts.bim_lab_drill import run_preflight


class FakeTransport:
    def __init__(self, reply: Any = None, error: Exception | None = None) -> None:
        self.reply = reply
        self.error = error
        self.calls: list[str] = []

    def __enter__(self) -> "FakeTransport":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def call(self, tool: str, arguments: dict[str, Any]) -> Any:
        del arguments
        self.calls.append(tool)
        if self.error is not None:
            raise self.error
        return self.reply


def _target(tmp_path: Path, name: str = "candidate.rvt") -> tuple[Path, Path, Path]:
    lab_root = tmp_path / "lab"
    lab_root.mkdir()
    target = lab_root / name
    target.write_bytes(b"synthetic lab target")
    lock_path = tmp_path / "revit-writer.lock"
    return lab_root, target, lock_path


def _health(transport: FakeTransport) -> Any:
    return transport.call("horizun_health", {})


def test_unreachable_provider_returns_exit_3_without_recording_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lab_root, target, lock_path = _target(tmp_path)
    transport = FakeTransport(error=McpTransportError("no Revit is reachable"))

    exit_code = run_preflight(
        target,
        lab_root=lab_root,
        lock_path=lock_path,
        transport_factory=lambda: transport,
        health_check=_health,
    )

    captured = capsys.readouterr()
    assert exit_code == 3
    assert "PROVIDER_UNREACHABLE" in captured.err
    assert "PASS" not in captured.out + captured.err
    assert transport.calls == ["horizun_health"]


def test_reachable_provider_with_free_lock_and_allowed_target_returns_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lab_root, target, lock_path = _target(tmp_path)
    transport = FakeTransport(reply={"healthy": True})

    exit_code = run_preflight(
        target,
        lab_root=lab_root,
        lock_path=lock_path,
        transport_factory=lambda: transport,
        health_check=_health,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "PREFLIGHT: PASS" in captured.out
    assert transport.calls == ["horizun_health"]


@pytest.mark.parametrize("protected_token", ["baseline", "release", "golden"])
def test_protected_target_is_refused_before_provider_health(
    tmp_path: Path, protected_token: str, capsys: pytest.CaptureFixture[str]
) -> None:
    lab_root, target, lock_path = _target(tmp_path, f"{protected_token}-candidate.rvt")
    transport = FakeTransport(reply={"healthy": True})

    exit_code = run_preflight(
        target,
        lab_root=lab_root,
        lock_path=lock_path,
        transport_factory=lambda: transport,
        health_check=_health,
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "REFUSED" in captured.err
    assert protected_token in captured.err.casefold()
    assert transport.calls == []


def test_occupied_writer_lock_is_refused_before_provider_health(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lab_root, target, lock_path = _target(tmp_path)
    holder = WriterLock(lock_path, owner="other-writer", process_id=os.getpid())
    holder.acquire()
    transport = FakeTransport(reply={"healthy": True})

    try:
        exit_code = run_preflight(
            target,
            lab_root=lab_root,
            lock_path=lock_path,
            transport_factory=lambda: transport,
            health_check=_health,
        )
    finally:
        holder.release()

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "writer lock" in captured.err.casefold()
    assert transport.calls == []
