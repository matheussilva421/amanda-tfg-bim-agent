"""Probe the installed Horizun MCP server over its real stdio transport.

This exists because the Codex client only loads MCP tools after a restart, and the
Tool Lab cannot wait for a restart to learn what the bridge actually offers. Here
we speak the same JSON-RPC 2.0 dialect the client speaks: initialize, then
tools/list, then optionally tools/call.

Read-only against the server. It never asks the bridge to write to a model.

Usage:
    python tool-lab/horizun/mcp_probe.py --list
    python tool-lab/horizun/mcp_probe.py --call horizun_health
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

DEFAULT_SERVER = Path(
    os.environ.get("LOCALAPPDATA", "")
) / "Programs" / "Horizun" / "MCP" / "server" / "horizun-mcp.exe"


class McpProbe:
    """One short-lived stdio session against the MCP server."""

    def __init__(self, server: Path, timeout: float = 120.0) -> None:
        self.server = server
        self.timeout = timeout
        self.process: subprocess.Popen[str] | None = None
        self.replies: dict[int, dict] = {}
        self.notifications: list[dict] = []
        self._next_id = 0
        self._lock = threading.Lock()

    def __enter__(self) -> "McpProbe":
        self.process = subprocess.Popen(
            [str(self.server)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()
        return self

    def __exit__(self, *exc: object) -> None:
        if self.process is None:
            return
        try:
            if self.process.stdin:
                self.process.stdin.close()
        except OSError:
            pass
        try:
            self.process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.process.kill()

    def _pump(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        for line in self.process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            with self._lock:
                if message.get("id") is None:
                    self.notifications.append(message)
                else:
                    self.replies[int(message["id"])] = message

    def send(self, method: str, params: dict | None = None) -> int:
        assert self.process is not None and self.process.stdin is not None
        with self._lock:
            self._next_id += 1
            request_id = self._next_id
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()
        return request_id

    def notify(self, method: str, params: dict | None = None) -> None:
        assert self.process is not None and self.process.stdin is not None
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()

    def await_reply(self, request_id: int) -> dict | None:
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            with self._lock:
                if request_id in self.replies:
                    return self.replies[request_id]
            time.sleep(0.05)
        return None

    def initialize(self) -> dict | None:
        request_id = self.send(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "amanda-tool-lab-probe", "version": "1"},
            },
        )
        reply = self.await_reply(request_id)
        self.notify("notifications/initialized")
        return reply

    def list_tools(self) -> dict | None:
        return self.await_reply(self.send("tools/list"))

    def call(self, tool: str, arguments: dict | None = None) -> dict | None:
        return self.await_reply(
            self.send("tools/call", {"name": tool, "arguments": arguments or {}})
        )

    def list_resources(self) -> dict | None:
        return self.await_reply(self.send("resources/list"))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", type=Path, default=DEFAULT_SERVER)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--list", action="store_true", help="print the tool catalog")
    parser.add_argument("--resources", action="store_true", help="print MCP resources")
    parser.add_argument("--call", metavar="TOOL", help="call one tool")
    parser.add_argument("--arguments", default="{}", help="JSON object for --call")
    parser.add_argument("--json", type=Path, help="write the raw session to this file")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if not args.server.is_file():
        print(f"server not found: {args.server}", file=sys.stderr)
        return 2

    session: dict = {"server": str(args.server), "started_utc": None}
    with McpProbe(args.server, timeout=args.timeout) as probe:
        session["started_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        handshake = probe.initialize()
        session["initialize"] = handshake
        if handshake is None:
            print("no reply to initialize: the server did not complete a handshake")
            return 2
        server_info = (handshake.get("result") or {}).get("serverInfo") or {}
        print(f"server: {server_info.get('name')} {server_info.get('version')}")
        protocol = (handshake.get("result") or {}).get("protocolVersion")
        print(f"protocol: {protocol}")

        if args.list:
            catalog = probe.list_tools()
            session["tools_list"] = catalog
            tools = ((catalog or {}).get("result") or {}).get("tools") or []
            print(f"tools: {len(tools)}")
            for tool in tools:
                print(f"  {tool.get('name')}")
                description = (tool.get("description") or "").strip().splitlines()
                if description:
                    print(f"      {description[0][:110]}")

        if args.resources:
            resources = probe.list_resources()
            session["resources_list"] = resources
            entries = ((resources or {}).get("result") or {}).get("resources") or []
            print(f"resources: {len(entries)}")
            for entry in entries:
                print(f"  {entry.get('uri')}")

        if args.call:
            result = probe.call(args.call, json.loads(args.arguments))
            session["call"] = result
            print(json.dumps(result, indent=2, ensure_ascii=False)[:4000])

        session["notifications"] = probe.notifications

    if args.json:
        args.json.write_text(
            json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

