"""Run Python through horizun_execute_python with a fresh idempotency key.

Usage: python .tmp-hzpy.py <script.py> <target_document> <out.json> [label]
The key is derived from label + source hash, so an edited script is NEW work
by construction and a repeat of identical source replays instead of rerunning.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path('tool-lab/horizun').resolve()))
from mcp_probe import DEFAULT_SERVER, McpProbe  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main(argv: list[str]) -> int:
    script_path = Path(argv[0])
    target = argv[1]
    out_path = Path(argv[2]) if len(argv) > 2 else None
    label = argv[3] if len(argv) > 3 else script_path.stem
    source = script_path.read_text(encoding='utf-8')
    digest = hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]
    key = 'amanda-%s-%s' % (label, digest)

    with McpProbe(DEFAULT_SERVER, timeout=1800.0) as probe:
        probe.initialize()
        reply = probe.call('horizun_execute_python', {
            'target_document': target,
            'code': source,
            'idempotency_key': key,
        })
    print('key:', key)
    if reply is None:
        print('NO REPLY')
        return 3
    if reply.get('error'):
        print('ERROR:', json.dumps(reply['error'], ensure_ascii=False)[:2500])
        return 2
    result = reply.get('result') or {}
    for c in (result.get('content') or []):
        print(str(c.get('text', ''))[:6000])
    if out_path is not None:
        out_path.write_text(json.dumps(reply, indent=2, ensure_ascii=False), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
