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
import hashlib
import json
import sys
import time
import uuid
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.providers import HorizunInvoker, McpProbeTransport
from amanda_agent.bim.runner import RunStatus, execute_stage
from amanda_agent.bim.stages import (
    ExecutionMode,
    stage_at_or_before,
)
from amanda_agent.design.canonical_pavilion_layout import (
    build_canonical_pavilion_layout,
)
from amanda_agent.design.canonical_reference import (
    CanonicalReferenceProfile,
)
from amanda_agent.models.capability import CapabilityRegistry
from amanda_agent.production.layout_bim import (
    build_layout_stage_plans,
    find_project_template,
)
from amanda_agent.production.selection import (
    build_selection,
    legacy_selection_history,
)
from amanda_agent.state.locks import WriterLock


def _shared_repository_root(repository_root: Path) -> Path:
    """Resolve linked worktrees to the checkout that owns their common Git dir."""

    root = Path(repository_root).resolve()
    marker = root / ".git"
    if marker.is_dir():
        return root
    if marker.is_file():
        first_line = marker.read_text(encoding="utf-8").splitlines()
        if first_line and first_line[0].casefold().startswith("gitdir:"):
            git_dir = Path(first_line[0].split(":", 1)[1].strip())
            if not git_dir.is_absolute():
                git_dir = root / git_dir
            git_dir = git_dir.resolve()
            common_git_dir = git_dir.parent.parent
            if (
                git_dir.parent.name.casefold() == "worktrees"
                and common_git_dir.name.casefold() == ".git"
            ):
                return common_git_dir.parent.resolve()
    return root


COMMON_REPOSITORY_ROOT = _shared_repository_root(REPOSITORY_ROOT)
LOCK_PATH = COMMON_REPOSITORY_ROOT / "state" / "locks" / "revit-writer.lock"
EVIDENCE_ROOT = REPOSITORY_ROOT / "revit" / "production"
GENERATION_RUN = "AMANDA-RUN-002-PAVILION"


def _new_idempotency_key(label: str, run_key: str) -> str:
    """Build a key scoped to one deliberate production attempt."""

    return f"amanda-{label}-{run_key}"


def _execution_scope(
    *, bim_eligible: bool, requested_max_stage: str
) -> tuple[ExecutionMode, BimStage]:
    """Keep an unaccepted selection inside the R01-R04 preacceptance window."""

    requested = BimStage[requested_max_stage]
    if requested is BimStage.R00:
        raise ValueError("R00 is not an executable production stage")
    if bim_eligible:
        return ExecutionMode.DETAILED_BIM, requested
    if stage_at_or_before(requested, BimStage.R04):
        return ExecutionMode.CANONICAL_PREACCEPTANCE, requested
    return ExecutionMode.CANONICAL_PREACCEPTANCE, BimStage.R04


def _validate_revit_session(
    health: object, *, expected_build: str, revit_pid: int | None
) -> dict:
    """Require a healthy, idle, exclusive Revit process before opening a target."""

    if not isinstance(health, dict):
        raise TypeError("Horizun health did not return a typed object")
    if str(health.get("status", "")).casefold() != "healthy":
        raise ValueError("Horizun provider is not healthy")
    if health.get("revit_build") != expected_build:
        raise ValueError(
            f"live Revit build {health.get('revit_build')!r} does not match "
            f"capability registry {expected_build!r}"
        )
    if revit_pid is not None and health.get("process_id") != revit_pid:
        raise ValueError(
            f"live Revit PID {health.get('process_id')!r} does not match requested {revit_pid}"
        )
    if health.get("other_clients_connected") != 0:
        raise ValueError(
            "Revit reports another MCP client in the 10-minute window; wait until "
            "the shared-session count returns to zero"
        )
    if health.get("open_document_count") != 0 or health.get("no_active_document") is not True:
        raise ValueError("Revit must have no open document before a new canonical target is created")
    return health


def _validate_canonical_target(
    rvt: Path, *, repository_root: Path = REPOSITORY_ROOT
) -> None:
    """Refuse the archived R12 path and any byte-identical copy of that RVT."""

    history = legacy_selection_history()
    relative_archive_path = Path(history["historical_rvt"])
    manifest_path = (
        Path(repository_root)
        / relative_archive_path.parent
        / "manifest.json"
    )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"cannot verify superseded R12 archive manifest: {manifest_path}"
        ) from exc

    if not isinstance(manifest, dict):
        raise TypeError("superseded R12 archive manifest must be a JSON object")
    artifact = manifest.get("artifact")
    direction = manifest.get("canonical_direction")
    if not isinstance(artifact, dict) or not isinstance(direction, dict):
        raise TypeError(
            "superseded R12 archive manifest is missing provenance fields"
        )
    archived_sha256 = artifact.get("sha256")
    if (
        manifest.get("record_type") != "ARCHIVED_HISTORICAL_REVIT_MODEL"
        or manifest.get("solution_id") != history["solution_id"]
        or manifest.get("status") != "SUPERSEDED_BY_USER_DIRECTION"
        or manifest.get("historical_only") is not True
        or manifest.get("repository_relative_archive_path")
        != relative_archive_path.as_posix()
        or direction.get("may_reuse_linear_geometry") is not False
        or archived_sha256 != history["historical_rvt_sha256"]
    ):
        raise ValueError("superseded R12 archive manifest is inconsistent or invalid")

    candidate = Path(rvt).resolve()
    repository = Path(repository_root).resolve()
    archived_path = (repository / relative_archive_path).resolve()
    if not archived_path.is_relative_to(repository):
        raise ValueError("superseded R12 archive path escapes the repository")
    if (
        not archived_path.is_file()
        or hashlib.sha256(archived_path.read_bytes()).hexdigest() != archived_sha256
    ):
        raise ValueError("archived R12 bytes do not match the recorded SHA-256")
    same_archive_path = candidate == archived_path
    same_archive_content = candidate.is_file() and hashlib.sha256(
        candidate.read_bytes()
    ).hexdigest() == archived_sha256
    if same_archive_path or same_archive_content:
        raise ValueError(
            "canonical production target is SUPERSEDED_BY_USER_DIRECTION: "
            "AMANDA-RUN-001-S01 R12 cannot be reused"
        )


def _report_canonical_sources(profile: CanonicalReferenceProfile) -> None:
    """Print path-bound SHA-256 identities before the production plan starts."""

    if len(profile.canonical_images) != 3 or len(profile.source_hashes) != 3:
        raise ValueError("production planning requires exactly three canonical board hashes")
    print("canonical source hashes:")
    for image, digest in zip(
        profile.canonical_images, profile.source_hashes, strict=True
    ):
        print(f"  {image}: {digest}")


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


def _select_revit_target(transport, revit_pid: int) -> dict:
    """Select one Revit process inside this MCP session and verify the result."""

    payload = _read_tool(transport, "horizun_target", {"pid": revit_pid})
    if not isinstance(payload, dict) or payload.get("selected_pid") != revit_pid:
        raise RuntimeError(
            f"Horizun did not select requested Revit PID {revit_pid}: {payload!r}"
        )
    return payload


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


def run(
    rvt: Path, *, execute: bool, max_stage: str, revit_pid: int | None = None
) -> int:
    from amanda_agent.bim.models import BimStage

    _validate_canonical_target(rvt)
    program = json.loads(
        (REPOSITORY_ROOT / "project" / "requirements" / "program.json").read_text(
            encoding="utf-8"
        )
    )
    profile = CanonicalReferenceProfile.load(REPOSITORY_ROOT)
    _report_canonical_sources(profile)
    layout = build_canonical_pavilion_layout(program, profile)
    selection = build_selection(
        layout,
        generation_run=GENERATION_RUN,
        timestamp="2026-09-23T00:00:00Z",
        profile=profile,
    )
    print("solution id:", selection.solution.solution_id)
    print("approval hash:", selection.approval_hash)
    if execute and not selection.solution.bim_eligible:
        print(
            "canonical selection is gated: BIM-00, canonical geometric acceptance, "
            "site evidence, and visual regressions must pass before detailed BIM",
            file=sys.stderr,
        )
        return 2

    registry, warnings = CapabilityRegistry.load_for_production(REPOSITORY_ROOT)
    for warning in warnings:
        print("registry warning:", warning)

    build = registry.entries[0].revit_build if registry.entries else None
    schema = registry.entries[0].tool_schema_hash if registry.entries else None
    if not build or not schema:
        print("no capability evidence is recorded", file=sys.stderr)
        return 2

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
        accessibility_input=None,
        template_root=None,
        mode=(
            ExecutionMode.DETAILED_BIM
            if execute
            else ExecutionMode.PLANNING_ONLY
        ),
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
            if revit_pid is not None:
                selected = _select_revit_target(transport, revit_pid)
                print("selected Revit PID:", selected["selected_pid"])
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
                    f"{plan.stage.name} {result.status.value} "
                    f"{verified}/{len(result.records)} verified"
                )
                if result.status is not RunStatus.VERIFIED:
                    for record in result.records:
                        if record.status is not RunStatus.VERIFIED:
                            print("   FAILED", record.logical_id, record.error)
                    print("stopping: stage did not verify", file=sys.stderr)
                    return 4

            transport.call(
                "horizun_save_document",
                {
                    "target_document": str(rvt),
                    "idempotency_key": _new_idempotency_key("save", run_key),
                },
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
    parser.add_argument(
        "--revit-pid",
        type=int,
        default=None,
        help="select this Revit process inside the production MCP session",
    )
    args = parser.parse_args(argv)
    return run(
        args.rvt,
        execute=args.execute,
        max_stage=args.max_stage,
        revit_pid=args.revit_pid,
    )


if __name__ == "__main__":
    raise SystemExit(main())
