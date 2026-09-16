"""Prove the unregistered grid and roof routes on a disposable lab file.

state/providers/semantic-crosswalk.yaml records revit.create_grid and
revit.create_roof with registered_entry null: the routes are proven to write and
to read back, but nothing has proven that the elements survive a save and a
reopen, which is what the capability registry demands of a write before any
stage may select it.  This script closes exactly that gap on a lab file.

It writes into a COPY of the lab baseline and never touches a production model,
an original, a checkpoint or a GOLDEN release.  It publishes evidence with a
sha256 for each record so the crosswalk row can be registered against a hash
rather than a claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from amanda_agent.bim.providers.transport import McpProbeTransport  # noqa: E402
from amanda_agent.state.locks import WriterLock  # noqa: E402

LAB = REPOSITORY_ROOT / "revit" / "lab"
LOCK_PATH = REPOSITORY_ROOT / "state" / "locks" / "revit-writer.lock"
RESULTS = REPOSITORY_ROOT / "tool-lab" / "horizun" / "results"

#: The two capabilities this script exists to register.
TARGETS = (
    {
        "capability": "revit.create_grid",
        "kind": "grid",
        "element": {
            "kind": "grid",
            "name": "AMANDA-PROBE-GRID-A",
            "start": [10.0, 0.0],
            "end": [10.0, 12.0],
        },
        "readback_categories": ["OST_Grids"],
    },
    {
        "capability": "revit.create_roof",
        "kind": "roof",
        "element": {
            "kind": "roof",
            "profile": [
                [0.0, 0.0],
                [12.0, 0.0],
                [12.0, 8.0],
                [0.0, 8.0],
                [0.0, 0.0],
            ],
            "level_id": None,
        },
        "readback_categories": ["OST_Roofs"],
    },
)


def _reply_payload(reply):
    if reply is None:
        return None, "no reply"
    if reply.get("error"):
        return None, str(reply["error"])
    result = reply.get("result") or {}
    if result.get("isError"):
        text = " ".join(
            str(item.get("text", ""))
            for item in result.get("content") or []
            if item.get("type") == "text"
        )
        return None, text[:400] or "isError"
    payload = result.get("structuredContent")
    if payload is not None:
        return payload, None
    for item in result.get("content") or []:
        if item.get("type") == "text":
            try:
                return json.loads(item["text"]), None
            except json.JSONDecodeError:
                continue
    return None, "no structured payload"


def _call(transport, tool, arguments):
    payload, error = _reply_payload(transport.call(tool, arguments))
    return payload, error


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(rvt: Path, *, execute: bool) -> int:
    if not rvt.is_file():
        print("lab target is missing:", rvt, file=sys.stderr)
        return 2
    if LAB.resolve() not in rvt.resolve().parents:
        print("refusing: the probe writes only inside revit/lab", file=sys.stderr)
        return 2

    print("lab target:", rvt)
    print("sha256 before:", _sha256(rvt))
    for target in TARGETS:
        print("will prove:", target["capability"], "via", target["kind"])
    if not execute:
        print("dry run: pass --execute to contact the bridge")
        return 0

    lock = WriterLock(LOCK_PATH, owner="amanda-crosswalk-probe")
    lock.acquire(reclaim_abandoned=True)
    print("lease acquired:", lock.owner_token)
    evidence: dict[str, object] = {"target": str(rvt), "target_sha256_before": _sha256(rvt)}
    try:
        with McpProbeTransport(timeout=600.0) as transport:
            health, error = _call(transport, "horizun_health", {})
            if error or not health or health.get("status") != "healthy":
                print("provider is not healthy:", error or health, file=sys.stderr)
                return 3
            print("provider:", health.get("horizun_version"), health.get("revit_build"))
            evidence["health"] = {
                key: health.get(key)
                for key in ("status", "horizun_version", "contract_hash", "revit_build")
            }

            opened, error = _call(
                transport,
                "horizun_document_session",
                {
                    "operation": "open",
                    "file_path": str(rvt),
                    "expected_version": "2027",
                    "idempotency_key": "amanda-crosswalk-open",
                },
            )
            if error:
                print("open failed:", error, file=sys.stderr)
                return 3
            print("opened:", opened.get("active_document"), "upgraded:", opened.get("upgraded_on_open"))

            # A level is needed by both element kinds and is already registered.
            level, error = _call(
                transport,
                "horizun_create_elements",
                {
                    "target_document": str(rvt),
                    "units": "m",
                    "elements": [
                        {
                            "kind": "level",
                            "name": "AMANDA-PROBE-LEVEL",
                            "elevation": 0.0,
                        }
                    ],
                    "idempotency_key": "amanda-crosswalk-level",
                },
            )
            level_id = None
            if isinstance(level, dict):
                for entry in (level.get("results") or level.get("created") or []):
                    if isinstance(entry, dict) and entry.get("element_id"):
                        level_id = entry["element_id"]
                        break
                level_id = level_id or level.get("element_id")
            print("level id:", level_id)

            records = []
            for target in TARGETS:
                element = dict(target["element"])
                if element.get("level_id") is None and level_id is not None:
                    element["level_id"] = level_id
                created, error = _call(
                    transport,
                    "horizun_create_elements",
                    {
                        "target_document": str(rvt),
                        "units": "m",
                        "elements": [element],
                        "idempotency_key": "amanda-crosswalk-" + target["kind"],
                    },
                )
                element_id = None
                if isinstance(created, dict):
                    for entry in (created.get("results") or created.get("created") or []):
                        if isinstance(entry, dict) and entry.get("element_id"):
                            element_id = entry["element_id"]
                            break
                    element_id = element_id or created.get("element_id")
                print(target["capability"], "write ->", "error" if error else "ok", element_id, error or "")
                if error or element_id is None:
                    return 4

                readback, read_error = _call(
                    transport,
                    "horizun_query_model",
                    {
                        "element_ids": [element_id],
                        "response_mode": "compact",
                        "cache_mode": "bypass",
                        "include_links": False,
                    },
                )
                matched = (readback or {}).get("matched_total")
                print("   independent read ->", matched, read_error or "")
                if read_error or matched != 1:
                    return 4
                records.append(
                    {
                        "capability": target["capability"],
                        "kind": target["kind"],
                        "element_id": element_id,
                        "write": "PASS",
                        "independent_read": "PASS",
                        "readback_matched_total": matched,
                    }
                )

            saved, error = _call(
                transport,
                "horizun_save_document",
                {"target_document": str(rvt), "idempotency_key": "amanda-crosswalk-save"},
            )
            if error:
                print("save failed:", error, file=sys.stderr)
                return 4
            print("saved:", saved.get("outcome"), saved.get("bytes_changed_on_disk"))

            closed, error = _call(
                transport,
                "horizun_document_session",
                {
                    "operation": "close",
                    "target_document": str(rvt),
                    "save_on_close": False,
                    "idempotency_key": "amanda-crosswalk-close",
                },
            )
            print("closed:", (closed or {}).get("closed"), "disk_changed:", (closed or {}).get("disk_changed"))

            reopened, error = _call(
                transport,
                "horizun_open_document",
                {
                    "path": str(rvt),
                    "expected_version": "2027",
                    "idempotency_key": "amanda-crosswalk-reopen",
                },
            )
            if error:
                print("reopen failed:", error, file=sys.stderr)
                return 4
            print("reopened:", reopened.get("opened"), "path_matches_request:", reopened.get("path_matches_request"))

            for record in records:
                after, read_error = _call(
                    transport,
                    "horizun_query_model",
                    {
                        "element_ids": [record["element_id"]],
                        "response_mode": "compact",
                        "cache_mode": "bypass",
                        "include_links": False,
                    },
                )
                matched = (after or {}).get("matched_total")
                record["after_reopen_read"] = "PASS" if matched == 1 else "FAIL"
                record["after_reopen_matched_total"] = matched
                print("   after reopen ->", record["capability"], matched, read_error or "")

            evidence["records"] = records
            evidence["target_sha256_after"] = _sha256(rvt)
            evidence["all_persisted"] = all(
                record["after_reopen_read"] == "PASS" for record in records
            )
    finally:
        lock.release()
        print("lease released")

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "crosswalk-grid-roof-probe.json"
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("evidence:", out)
    print("sha256:", _sha256(out))
    print("all persisted:", evidence["all_persisted"])
    return 0 if evidence["all_persisted"] else 5


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rvt", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    return run(args.rvt, execute=args.execute)


if __name__ == "__main__":
    raise SystemExit(main())

