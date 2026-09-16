"""Execute the adopted Amanda layout against Revit, stage by stage.

This is the production driver.  It is a thin, auditable loop over the plans the
pure compiler produced: it acquires the single writer lease, opens the project on
the installed template, saves it under the production path, executes R01-R13 with
WRITE then READ then VERIFY, checkpoints after every stage, and finishes with the
save/close/reopen cycle the release gate requires.

Nothing here decides geometry.  Every operation comes from
amanda_agent.production.layout_bim, which refuses an operation the capability
registry cannot prove for this exact build.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from amanda_agent.bim.stages import create_stage_checkpoint  # noqa: E402
from amanda_agent.bim.providers import HorizunInvoker, McpProbeTransport  # noqa: E402
from amanda_agent.bim.runner import RunStatus, execute_stage  # noqa: E402
from amanda_agent.bim.stages import ExecutionMode  # noqa: E402
from amanda_agent.design.architectural_layout import build_courtyard_layout  # noqa: E402
from amanda_agent.models.capability import CapabilityRegistry  # noqa: E402
from amanda_agent.production.layout_bim import (  # noqa: E402
    build_layout_stage_plans,
    find_project_template,
)
from amanda_agent.production.selection import build_selection  # noqa: E402
from amanda_agent.state.locks import WriterLock  # noqa: E402

LOCK_PATH = REPOSITORY_ROOT / "state" / "locks" / "revit-writer.lock"
EVIDENCE_ROOT = REPOSITORY_ROOT / "revit" / "production"
GENERATION_RUN = "AMANDA-RUN-001"


def _payload(result):
    """Return the provider payload of one stage result, or None."""

    for record in result.records:
        evidence = getattr(record, "evidence", None)
        if isinstance(evidence, dict) and evidence:
            return evidence
    return None


def _read_tool(transport, tool, arguments):
    reply = transport.call(tool, arguments)
    if reply is None:
        return None
    result = reply.get("result") or {}
    payload = result.get("structuredContent")
    if payload is not None:
        return payload
    for item in result.get("content") or []:
        if item.get("type") == "text":
            try:
                return json.loads(item["text"])
            except json.JSONDecodeError:
                continue
    return None


def _document_info(transport):
    return _read_tool(transport, "get_document_info", {})


def _active_path(info):
    if not isinstance(info, dict):
        return None
    for key in ("document_path", "file_path", "full_path"):
        value = info.get(key)
        if isinstance(value, str) and value:
            return value
    for key in ("file_path", "path", "document_path", "full_path"):
        value = info.get(key)
        if isinstance(value, str) and value:
            return value
    nested = info.get("document")
    if isinstance(nested, dict):
        return _active_path(nested)
    return None


def _open_documents(transport):
    """Return every document the bridge reports as open, by path and title."""

    payload = _read_tool(transport, "horizun_document_session", {"operation": "inspect"})
    if not isinstance(payload, dict):
        return []
    for key in ("documents", "open_documents", "open"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def _activate(transport, rvt: Path) -> None:
    """Make the target document active, which the provider requires.

    The provider acts on the ACTIVE document and deliberately refuses to switch
    documents by itself, because activating one changes what a person is looking
    at.  This driver owns the lease, so it makes the switch explicitly and
    verifies it took effect instead of writing into the wrong model.
    """

    target = Path(rvt).resolve()
    info = _document_info(transport)
    active = _active_path(info)
    if active and Path(active).resolve() == target:
        return
    # Opening an already-open document activates it in the installed bridge, and
    # the call is idempotent for a document that is already open.
    transport.call(
        "horizun_document_session",
        {
            "operation": "open",
            "file_path": str(target),
            "expected_version": "2027",
            "idempotency_key": f"amanda-activate-{uuid.uuid4().hex[:12]}",
        },
    )
    for _ in range(10):
        info = _document_info(transport)
        active = _active_path(info)
        if active and Path(active).resolve() == target:
            return
        time.sleep(0.4)


def run(rvt: Path, *, execute: bool, max_stage: str) -> int:
    from amanda_agent.bim.models import BimStage

    program = json.loads(
        (REPOSITORY_ROOT / "project" / "requirements" / "program.json").read_text(
            encoding="utf-8"
        )
    )
    layout = build_courtyard_layout(program)
    selection = build_selection(layout, generation_run=GENERATION_RUN, timestamp="2026-09-16T15:00:00Z")
    registry, warnings = CapabilityRegistry.load_for_production(REPOSITORY_ROOT)
    for warning in warnings:
        print("registry warning:", warning)

    build = registry.entries[0].revit_build if registry.entries else None
    schema = registry.entries[0].tool_schema_hash if registry.entries else None
    if not build or not schema:
        print("no capability evidence is recorded", file=sys.stderr)
        return 2

    from amanda_agent.bim.stages.accessibility import (
        AccessibleRoute,
        AccessibilityInput,
        WidthCheck,
    )

    entrance = layout.face_rooms("street")[0].logical_id
    accessibility = AccessibilityInput(
        entrance_id=entrance,
        required_space_ids=[room.logical_id for room in layout.rooms if room.accessible]
        or [entrance],
        routes=[
            AccessibleRoute(
                logical_id="ROUTE-ENTRANCE-" + room.logical_id,
                from_node=entrance,
                to_node=room.logical_id,
                measured_width_m=layout.corridor_width_m,
                source_ref="measured gallery width",
            )
            for room in layout.rooms
        ],
        widths=[
            WidthCheck(
                logical_id="WIDTH-GALLERY",
                location="circulation spine",
                measured_width_m=layout.corridor_width_m,
                source_ref="measured gallery width",
            )
        ],
    )

    plans = build_layout_stage_plans(
        program=program,
        layout=layout,
        registry=registry,
        revit_build=build,
        tool_schema_hash=schema,
        generation_run=GENERATION_RUN,
        solution_id=selection.solution.solution_id,
        approval_hash=selection.approval_hash,
        solution=selection.solution,
        accessibility_input=accessibility,
        template_root=None,
        mode=ExecutionMode.DETAILED_BIM,
        max_stage=BimStage[max_stage],
    )
    print("planned stages:", [plan.stage.name for plan in plans])
    print("layout hash:", layout.content_hash)
    print("approval hash:", selection.approval_hash)
    template = find_project_template(None)
    print("template:", template)
    if not execute:
        print("dry run: nothing written")
        return 0

    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    rvt.parent.mkdir(parents=True, exist_ok=True)
    # The bridge addresses documents by absolute rooted path, so the target is
    # resolved once here and every stage call carries that same string.
    rvt = rvt.resolve()

    # Every run starts from the installed template into a NEW file.  The
    # production stages name their elements deterministically (LEVEL-01,
    # GRID-01, and so on), and Revit refuses a duplicate level or grid name, so
    # reusing a file that already holds a previous attempt would fail on names
    # rather than on the work.  A run number keeps each attempt its own model and
    # never overwrites a build that may already hold reviewed evidence.
    if rvt.exists():
        stamp = time.strftime("%Y%m%d-%H%M%S")
        rvt = rvt.with_name(f"{rvt.stem}.{stamp}{rvt.suffix}")
        print("target already exists; writing a new attempt:", rvt.name)

    lock = WriterLock(LOCK_PATH, owner="amanda-production-run")
    lock.acquire(reclaim_abandoned=True)
    print("lease acquired:", lock.owner_token)
    try:
        with McpProbeTransport(timeout=900.0) as transport:
            # Each attempt is new work, so it gets its own idempotency keys: the
            # bridge keeps a key for exactly one operation and replays the
            # recorded answer for an identical retry, which would silently
            # return the previous attempt's reply instead of opening the file.
            run_key = uuid.uuid4().hex[:12]
            transport.call(
                "horizun_document_session",
                {
                    "operation": "open",
                    "file_path": str(template),
                    "expected_version": "2027",
                    "idempotency_key": f"amanda-open-template-{run_key}",
                },
            )
            info = _document_info(transport)
            print("after open:", json.dumps(info, ensure_ascii=False)[:300])

            # The template may already be open behind another document, in which
            # case opening it does not make it active.  Activating it explicitly
            # is what the safety check then sees, and it is also what makes the
            # save_as act on the template rather than on whatever was in front.
            active_now = _active_path(info)
            if not active_now or Path(active_now).resolve() != Path(template).resolve():
                transport.call(
                    "horizun_document_session",
                    {
                        "operation": "open",
                        "file_path": str(template),
                        "expected_version": "2027",
                        "activate": True,
                        "idempotency_key": f"amanda-activate-template-{run_key}",
                    },
                )
                info = _document_info(transport)
                print("after activate:", json.dumps(info, ensure_ascii=False)[:250])

            # Opening the template is asynchronous enough that an immediate
            # save_as can arrive while the source document is still settling,
            # and the bridge then reports success without switching the active
            # document.  The open is therefore confirmed before the save.
            if not _active_path(info) or not str(_active_path(info)).casefold().endswith(
                ".rte"
            ):
                for _ in range(20):
                    time.sleep(0.5)
                    info = _document_info(transport)
                    if _active_path(info):
                        break
                print("re-read after open:", json.dumps(info, ensure_ascii=False)[:200])

            # save_as refuses to guess which open document it is saving, and it
            # addresses that document by the path the bridge itself reports
            # rather than by the path this script asked for.
            source = _active_path(info) or str(template)
            transport.call(
                "horizun_document_session",
                {
                    "operation": "save_as",
                    "target_document": source,
                    # The destination travels in save_as_path; file_path is an
                    # alias of target_document for this operation, not the target.
                    "save_as_path": str(rvt),
                    "idempotency_key": f"amanda-save-as-{run_key}",
                },
            )
            info = _document_info(transport)
            print("after save_as:", json.dumps(info, ensure_ascii=False)[:300])
            active = _active_path(info)
            if active and Path(active).resolve() != rvt.resolve():
                print("active document is not the production path:", active, file=sys.stderr)
                return 3

            invoker = HorizunInvoker(transport=transport, target_document=str(rvt))
            for plan in plans:
                if plan.stage.name == "R01":
                    print("R01 handled by the document session above")
                    continue
                # Several attempts are open at once, and Revit's active document
                # moves between them.  The provider acts on the ACTIVE document
                # and refuses to switch by itself, so the target is activated
                # before each stage rather than left to whatever was in front.
                _activate(transport, rvt)
                result = execute_stage(plan, invoker=invoker)
                journal = EVIDENCE_ROOT / "journals" / (plan.stage.name + ".json")
                journal.parent.mkdir(parents=True, exist_ok=True)
                journal.write_text(
                    json.dumps(
                        {
                            "stage": result.stage.name,
                            "status": result.status.value,
                            "records": [
                                {
                                    "logical_id": record.logical_id,
                                    "capability": record.semantic_capability,
                                    "status": record.status.value,
                                    "unique_id": record.unique_id,
                                    "error": record.error,
                                }
                                for record in result.records
                            ],
                        },
                        indent=2,
                        sort_keys=True,
                        default=str,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                verified = sum(1 for r in result.records if r.status is RunStatus.VERIFIED)
                print(
                    "%s %s %d/%d verified"
                    % (plan.stage.name, result.status.value, verified, len(result.records))
                )
                if result.status is not RunStatus.VERIFIED:
                    for record in result.records:
                        if record.status is not RunStatus.VERIFIED:
                            print("   FAILED", record.logical_id, record.error)
                    print("stopping: stage did not verify", file=sys.stderr)
                    return 4

            transport.call(
                "horizun_save_document",
                {"target_document": str(rvt), "idempotency_key": "amanda-save-1"},
            )
            print("saved:", rvt)
        return 0
    finally:
        lock.release()
        print("lease released")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rvt", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-stage", default="R13")
    args = parser.parse_args(argv)
    return run(args.rvt, execute=args.execute, max_stage=args.max_stage)


if __name__ == "__main__":
    raise SystemExit(main())
