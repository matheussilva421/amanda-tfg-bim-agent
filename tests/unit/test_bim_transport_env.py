"""Regression tests for the MCP stdio child environment."""

from __future__ import annotations

import io
import os
from pathlib import Path

from amanda_agent.bim.providers import transport


class _FakeProcess:
    stdin = None
    stdout = ()
    stderr = None

    def poll(self) -> None:
        return None


def test_stdio_child_receives_the_controller_user_profile(monkeypatch, tmp_path: Path):
    server = tmp_path / "horizun-mcp.exe"
    server.write_bytes(b"stub")
    profile = tmp_path / "interactive-user"
    monkeypatch.setenv("USERPROFILE", str(profile))
    monkeypatch.setenv("AMANDA_TRANSPORT_ENV_SENTINEL", "preserved")
    expected_env = dict(os.environ)
    captured: dict[str, object] = {}

    def fake_popen(*_args: object, **kwargs: object) -> _FakeProcess:
        captured.update(kwargs)
        return _FakeProcess()

    monkeypatch.setattr(transport.subprocess, "Popen", fake_popen)
    client = transport.McpProbeTransport(server=server)
    monkeypatch.setattr(client, "_send", lambda *_args, **_kwargs: 1)
    monkeypatch.setattr(client, "_await_reply", lambda _request_id: {})
    monkeypatch.setattr(client, "_notify", lambda *_args, **_kwargs: None)

    client._ensure_started()

    child_env = captured["env"]
    assert isinstance(child_env, dict)
    assert child_env == expected_env
    assert child_env["USERPROFILE"] == str(profile)
    assert child_env["AMANDA_TRANSPORT_ENV_SENTINEL"] == "preserved"


def test_stdio_stderr_is_drained_without_retaining_provider_output(monkeypatch, tmp_path: Path):
    server = tmp_path / "horizun-mcp.exe"
    server.write_bytes(b"stub")
    stderr_text = "provider diagnostic secret-marker\n" * 4096

    class FakeProcess:
        pid = 40001
        stdin = io.StringIO()
        stdout = ()
        stderr = io.StringIO(stderr_text)

        def poll(self):
            return None

    process = FakeProcess()
    monkeypatch.setattr(transport.subprocess, "Popen", lambda *_args, **_kwargs: process)
    client = transport.McpProbeTransport(server=server)
    monkeypatch.setattr(client, "_send", lambda *_args, **_kwargs: 1)
    monkeypatch.setattr(client, "_await_reply", lambda _request_id: {})
    monkeypatch.setattr(client, "_notify", lambda *_args, **_kwargs: None)

    client._ensure_started()
    client._stderr_reader.join(timeout=2)

    assert not client._stderr_reader.is_alive()
    assert client.stderr_diagnostics == {
        "bytes_drained": len(stderr_text.encode("utf-8")),
        "reader_error": None,
    }
    assert "secret-marker" not in repr(client.stderr_diagnostics)
