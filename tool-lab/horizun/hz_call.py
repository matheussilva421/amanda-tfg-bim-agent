"""Temporary interactive Horizun call helper (not committed).

Usage:
    python .tmp-hz.py get_document_info
    python .tmp-hz.py horizun_list_elements --args-file .tmp-args.json
    python .tmp-hz.py horizun_create_elements --args-file .tmp-args.json --chars 4000
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path("tool-lab/horizun").resolve()))
from mcp_probe import DEFAULT_SERVER, McpProbe  # noqa: E402


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("tool")
    ap.add_argument("--args-file", default=None)
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--chars", type=int, default=2500)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    args = json.loads(Path(a.args_file).read_text(encoding="utf-8")) if a.args_file else {}
    with McpProbe(DEFAULT_SERVER, timeout=a.timeout) as probe:
        if probe.initialize() is None:
            print("no handshake"); return 2
        reply = probe.call(a.tool, args)
    if reply is None:
        print("no reply (timeout)"); return 3
    if a.out:
        Path(a.out).write_text(json.dumps(reply, indent=2, ensure_ascii=False), encoding="utf-8")
    result = reply.get("result") or {}
    err = reply.get("error")
    if err:
        print("ERROR:", json.dumps(err, ensure_ascii=False)[:a.chars])
    texts = [c.get("text", "") for c in (result.get("content") or []) if c.get("type") == "text"]
    for t in texts:
        print(t[:a.chars])
    sc = result.get("structuredContent")
    if sc:
        print("--- structuredContent ---")
        print(json.dumps(sc, ensure_ascii=False)[:a.chars])
    if result.get("isError"):
        print("isError: true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
