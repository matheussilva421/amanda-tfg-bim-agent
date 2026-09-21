"""Small stdlib-only MCP stdio transport matching the Horizun probe contract."""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from typing import Any, Protocol


DEFAULT_SERVER = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Horizun" / "MCP" / "server" / "horizun-mcp.exe"


class McpTransportError(RuntimeError):
    """The stdio MCP session could not be established or used."""


class McpTransport(Protocol):
    """The narrow transport surface injected into ``HorizunInvoker``."""

    def call(self, tool: str, arguments: Mapping[str, Any]) -> Mapping[str, Any] | None:
        """Call one MCP tool and return its raw JSON-RPC reply."""


class McpProbeTransport:
    """Lazy JSON-RPC 2.0 stdio transport for the installed Horizun server.

    The process starts only on the first call. Tests can inject a transport
    double and therefore never construct this class or contact Revit.
    """

    def __init__(self, server: Path = DEFAULT_SERVER, timeout: float = 600.0) -> None:
        self.server = Path(server)
        self.timeout = timeout
        self.process: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None
        self._replies: dict[int, dict[str, Any]] = {}
        self._notifications: list[dict[str, Any]] = []
        self._next_id = 0
        self._lock = threading.Lock()
        self._started = False

    def __enter__(self) -> "McpProbeTransport":
        self._ensure_started()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        process = self.process
        self.process = None
        self._started = False
        if process is None:
            return
        try:
            if process.stdin is not None:
                process.stdin.close()
        except OSError:
            pass
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    def call(self, tool: str, arguments: Mapping[str, Any]) -> Mapping[str, Any] | None:
        self._ensure_started()
        request_id = self._send(
            "tools/call",
            {"name": tool, "arguments": dict(arguments)},
        )
        return self._await_reply(request_id)

    def _ensure_started(self) -> None:
        if self._started and self.process is not None and self.process.poll() is None:
            return
        if not self.server.is_file():
            raise McpTransportError(f"Horizun MCP server not found: {self.server}")
        self.process = subprocess.Popen(
            [str(self.server)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy(),
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        self._replies.clear()
        self._notifications.clear()
        self._next_id = 0
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()
        request_id = self._send(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "amanda-bim-provider", "version": "1"},
            },
        )
        reply = self._await_reply(request_id)
        if reply is None:
            self.close()
            raise McpTransportError("Horizun MCP initialize timed out")
        if reply.get("error"):
            self.close()
            raise McpTransportError(f"Horizun MCP initialize failed: {reply['error']}")
        self._notify("notifications/initialized")
        self._started = True

    def _pump(self) -> None:
        process = self.process
        if process is None or process.stdout is None:
            return
        for line in process.stdout:
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            with self._lock:
                if message.get("id") is None:
                    self._notifications.append(message)
                else:
                    self._replies[int(message["id"])] = message

    def _send(self, method: str, params: Mapping[str, Any] | None = None) -> int:
        process = self.process
        if process is None or process.stdin is None:
            raise McpTransportError("Horizun MCP process is not running")
        with self._lock:
            self._next_id += 1
            request_id = self._next_id
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = dict(params)
        try:
            process.stdin.write(json.dumps(payload) + "\n")
            process.stdin.flush()
        except (OSError, ValueError) as exc:
            raise McpTransportError(f"Horizun MCP request failed: {exc}") from exc
        return request_id

    def _notify(self, method: str, params: Mapping[str, Any] | None = None) -> None:
        process = self.process
        if process is None or process.stdin is None:
            raise McpTransportError("Horizun MCP process is not running")
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = dict(params)
        process.stdin.write(json.dumps(payload) + "\n")
        process.stdin.flush()

    def _await_reply(self, request_id: int) -> dict[str, Any] | None:
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            with self._lock:
                reply = self._replies.pop(request_id, None)
            if reply is not None:
                return reply
            time.sleep(0.05)
        return None


__all__ = ["DEFAULT_SERVER", "McpProbeTransport", "McpTransport", "McpTransportError"]
