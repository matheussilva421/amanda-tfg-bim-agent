"""Fail-closed identity pinning for production MCP transport sessions."""

from __future__ import annotations

import pytest

from amanda_agent.bim.providers import transport


class _FakeProcess:
    def __init__(self, pid: int) -> None:
        self.pid = pid
        self.returncode: int | None = None

    def poll(self) -> int | None:
        return self.returncode


def test_health_pinned_transport_refuses_automatic_restart(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    server = tmp_path / "horizun-mcp.exe"
    server.write_bytes(b"stub")
    original_process = _FakeProcess(pid=40000)
    client = transport.McpProbeTransport(server=server)
    client.process = original_process  # type: ignore[assignment]
    client._started = True

    assert client.pin_process_identity() == 40000

    original_process.returncode = 1
    spawned = []

    def record_spawn(*_args: object, **_kwargs: object):
        spawned.append(True)
        return _FakeProcess(pid=40001)

    monkeypatch.setattr(transport.subprocess, "Popen", record_spawn)

    with pytest.raises(transport.McpTransportError, match="pinned.*exited"):
        client._ensure_started()

    assert spawned == []


def test_list_tools_uses_the_existing_started_mcp_process():
    process = _FakeProcess(pid=40002)
    client = transport.McpProbeTransport()
    client.process = process  # type: ignore[assignment]
    client._started = True
    calls = []
    reply = {"jsonrpc": "2.0", "id": 2, "result": {"tools": [{"name": "horizun_health"}]}}

    def send(method, params=None):
        calls.append((method, params))
        return 2

    client._send = send
    client._await_reply = lambda _request_id: reply

    assert client.list_tools() is reply
    assert calls == [("tools/list", {})]
