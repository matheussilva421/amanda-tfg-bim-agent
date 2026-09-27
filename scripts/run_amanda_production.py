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
import math
import sys
import time
import uuid
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

RUN003_FAILED_R05_JOURNAL = (
    REPOSITORY_ROOT / "revit/production/journals/R05-2f373fcb3511.json"
)
RUN003_FAILED_R05_FLOOR_IDS = {
    "FLOOR-RES_PAV_A-L1": 331188,
    "FLOOR-RES_PAV_B-L1": 331289,
    "FLOOR-RES_PAV_C-L1": 331377,
    "FLOOR-RES_PAV_D_COMMUNAL-L1": 331474,
    "FLOOR-CHILD_SECTOR-L1-P01": 331548,
    "FLOOR-CHILD_SECTOR-L1-P02": 331556,
    "FLOOR-CHILD_SECTOR-L1-P03": 331564,
    "FLOOR-CHILD_SECTOR-L1-P04": 331572,
}

from amanda_agent.bim.checkpoints import CheckpointManager
from amanda_agent.bim.models import BimStage
from amanda_agent.bim.providers import HorizunInvoker, McpProbeTransport
from amanda_agent.bim.runner import (
    OperationRunRecord,
    RunStatus,
    execute_stage,
)
from amanda_agent.bim.stages import (
    ExecutionMode,
    stage_at_or_before,
    stage_checkpoint_label,
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
from amanda_agent.production.p6_fingerprint_reconciliation import (
    P6FingerprintReconciliationError,
    verify_reconciled_p6_readback,
)
from amanda_agent.production.run003_study import (
    load_run003_study_authorization,
    load_run003_study_selection,
)
from amanda_agent.production.selection import (
    build_selection,
    legacy_selection_history,
)
from amanda_agent.state.locks import LockHeldByAnotherOwner, WriterLock


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
GENERATION_RUN = "AMANDA-RUN-003-PAVILION-CANONICAL"


def _new_idempotency_key(label: str, run_key: str) -> str:
    """Build a key scoped to one deliberate production attempt."""

    return f"amanda-{label}-{run_key}"


def _stage_journal_path(stage: str | BimStage, run_key: str) -> Path:
    """Keep the evidence journal for each stage attempt immutable."""

    stage_name = stage.name if isinstance(stage, BimStage) else str(stage)
    return EVIDENCE_ROOT / "journals" / f"{stage_name}-{run_key}.json"


def _execution_scope(
    *,
    bim_eligible: bool,
    requested_max_stage: str,
    run003_study_authorization=None,
    target_path: Path | None = None,
) -> tuple[ExecutionMode, BimStage]:
    """Resolve the detailed or narrowly granted post-P6 stage window."""

    requested = BimStage[requested_max_stage]
    if requested is BimStage.R00:
        raise ValueError("R00 is not an executable production stage")
    if run003_study_authorization is not None:
        if bim_eligible:
            raise ValueError("RUN-003 P6 grant requires BIM-ineligible canonical identity")
        if (
            target_path is None
            or not run003_study_authorization.permits_target_path(target_path)
        ):
            raise ValueError("post-P6 continuation requires the exact RUN-003 target")
        if not run003_study_authorization.permits_stage(requested):
            raise ValueError("post-P6 continuation is limited to R05 through R13")
        return ExecutionMode.NORMALIZED_STUDY_POST_P6, requested
    if bim_eligible:
        return ExecutionMode.DETAILED_BIM, requested
    if stage_at_or_before(requested, BimStage.R04):
        return ExecutionMode.CANONICAL_PREACCEPTANCE, requested
    return ExecutionMode.CANONICAL_PREACCEPTANCE, BimStage.R04


def _validate_revit_session(
    health: object,
    *,
    expected_build: str,
    revit_pid: int | None,
    target_path: Path | None = None,
    mcp_client_pid: int | None = None,
) -> dict:
    """Require a healthy, exclusive Revit process and the intended document."""

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
    has_top_level_count = "other_clients_connected" in health
    top_level_count = health.get("other_clients_connected")
    if has_top_level_count and (
        type(top_level_count) is not int or top_level_count < 0
    ):
        raise ValueError("Horizun health has an invalid other-client count")
    client_state = health.get("clients")
    if not isinstance(client_state, dict):
        raise ValueError("Horizun health has inconsistent client metadata")
    if "other_clients_connected" not in client_state:
        raise ValueError("Horizun health has no authoritative other-client count")
    other_clients = client_state.get("other_clients_connected")
    if type(other_clients) is not int or other_clients < 0:
        raise ValueError("Horizun health has an invalid other-client count")
    if has_top_level_count and top_level_count != other_clients:
        raise ValueError("Horizun health has inconsistent client metadata")

    required_client_fields = {
        "clients_seen",
        "distinct_clients_in_window",
        "unidentified_connections_in_window",
    }
    if not required_client_fields.issubset(client_state):
        raise ValueError("Horizun health has incomplete client metadata")
    clients_seen = client_state.get("clients_seen")
    distinct_clients = client_state.get("distinct_clients_in_window")
    unidentified = client_state.get("unidentified_connections_in_window")
    if (
        not isinstance(clients_seen, list)
        or type(distinct_clients) is not int
        or distinct_clients < 0
        or distinct_clients != len(clients_seen)
        or type(unidentified) is not int
        or unidentified < 0
    ):
        raise ValueError("Horizun health has inconsistent client metadata")
    if unidentified != 0:
        raise ValueError("Horizun health reports unidentified recent clients")
    if type(mcp_client_pid) is not int or mcp_client_pid <= 0:
        raise ValueError("Horizun health cannot identify the current MCP transport")

    seen_pids: set[int] = set()
    current_clients = 0
    client_details = []

    def safe_client_value(value: object) -> str:
        rendered = str(value)
        return "".join(
            char
            if char.isprintable()
            else char.encode("unicode_escape").decode("ascii")
            for char in rendered
        )

    for client in clients_seen:
        if not isinstance(client, dict):
            raise ValueError("Horizun health has inconsistent client metadata")
        pid = client.get("pid")
        process_name = client.get("process_name")
        age = client.get("seconds_since_last_request")
        process_alive = client.get("process_alive")
        if (
            type(pid) is not int
            or pid <= 0
            or pid in seen_pids
            or (process_name is not None and not isinstance(process_name, str))
            or type(age) not in (int, float)
            or not 0 <= age <= 600
            or type(process_alive) is not bool
        ):
            raise ValueError("Horizun health has inconsistent client metadata")
        seen_pids.add(pid)
        if pid == mcp_client_pid:
            current_clients += 1
            if (
                str(process_name or "").casefold() != "horizun-mcp"
                or process_alive is not True
            ):
                raise ValueError("Horizun health has inconsistent client metadata")
        client_details.append(
            "pid={pid}, process_name={process_name}, "
            "seconds_since_last_request={age}, process_alive={alive}".format(
                pid=safe_client_value(pid),
                process_name=safe_client_value(process_name or "unknown"),
                age=safe_client_value(age),
                alive=safe_client_value(str(process_alive).lower()),
            )
        )
    if current_clients != 1 or other_clients != distinct_clients - 1:
        raise ValueError("Horizun health has inconsistent client metadata")
    if other_clients != 0:
        detail = f"; clients_seen=[{'; '.join(client_details)}]"
        raise ValueError(
            "Revit reports another MCP client in the 10-minute window; wait until "
            f"the shared-session count returns to zero{detail}"
        )
    if target_path is None:
        if (
            health.get("open_document_count") != 0
            or health.get("no_active_document") is not True
        ):
            raise ValueError(
                "Revit must have no open document before a new canonical target is created"
            )
    else:
        active_document = health.get("active_document")
        active_path = _active_path(active_document)
        if not active_path or Path(active_path).resolve() != Path(target_path).resolve():
            raise ValueError("the exact authorized RUN-003 document must be active")
        if not isinstance(active_document, dict) or active_document.get(
            "has_been_saved_to_disk"
        ) is not True:
            raise ValueError("the RUN-003 target must already be saved to disk")
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

    if len(profile.canonical_images) != 4 or len(profile.source_hashes) != 4:
        raise ValueError("production planning requires exactly four canonical board hashes")
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


def _health_reply_diagnostic(reply: object) -> str:
    if reply is None:
        return "no JSON-RPC reply"
    if not isinstance(reply, dict):
        return f"reply_type={type(reply).__name__}"
    result = reply.get("result")
    result_type = type(result).__name__ if "result" in reply else "missing"
    result_keys = sorted(result) if isinstance(result, dict) else []
    content = result.get("content", []) if isinstance(result, dict) else []
    content_types = [
        item.get("type") for item in content if isinstance(item, dict)
    ] if isinstance(content, list) else []
    text_preview = next(
        (
            " ".join(item["text"].split())[:160]
            for item in content
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        ),
        None,
    ) if isinstance(content, list) else None
    error = reply.get("error")
    if isinstance(error, dict):
        error = {
            "code": error.get("code"),
            "message": str(error.get("message", ""))[:160],
        }
    return (
        f"reply_keys={sorted(reply)}, result_type={result_type}, "
        f"result_keys={result_keys}, "
        f"content_types={content_types}, error={error!r}, "
        f"text_preview={text_preview!r}"
    )


def _read_tool(transport, tool, arguments):
    reply = transport.call(tool, arguments)
    if reply is None:
        if tool == "horizun_health":
            raise TypeError(
                "Horizun health reply was untyped: "
                f"{_health_reply_diagnostic(reply)}"
            )
        return None
    result = reply.get("result")
    if not isinstance(result, dict):
        if tool == "horizun_health":
            raise TypeError(
                "Horizun health reply was untyped: "
                f"{_health_reply_diagnostic(reply)}"
            )
        result = {}
    payload = result.get("structuredContent")
    if payload is not None:
        return payload
    for item in result.get("content") or []:
        if item.get("type") == "text":
            try:
                return json.loads(item["text"])
            except json.JSONDecodeError:
                continue
    if tool == "horizun_health":
        raise TypeError(
            "Horizun health reply was untyped: "
            f"{_health_reply_diagnostic(reply)}"
        )
    return None


def _document_info(transport):
    return _read_tool(transport, "get_document_info", {})


def _validate_document_open_result(
    payload: object,
    requested_path: Path,
    *,
    expected_version: str,
    context: str,
) -> dict:
    """Require the installed bridge's exact-path, no-upgrade open evidence."""

    requested = Path(requested_path).resolve()
    if not isinstance(payload, dict):
        raise RuntimeError(f"{context} failed verification: {payload!r}")
    observed_paths = (payload.get("path"), payload.get("opened_from"))
    paths_match = all(
        isinstance(value, str) and Path(value).resolve() == requested
        for value in observed_paths
    )
    if (
        payload.get("status") != "opened"
        or payload.get("opened_now") is not True
        or payload.get("active_document_verified") is not True
        or payload.get("path_is_the_one_requested") is not True
        or payload.get("identified_by") != "path"
        or not paths_match
        or payload.get("expected_version") != expected_version
        or payload.get("host_version") != expected_version
        or payload.get("file_version_before_open") != expected_version
        or payload.get("upgraded") is not False
        or payload.get("version_guard") != "checked"
    ):
        raise RuntimeError(f"{context} failed verification: {payload!r}")
    return payload


def _select_revit_target(transport, revit_pid: int) -> dict:
    """Select one Revit process inside this MCP session and verify the result."""

    payload = _read_tool(transport, "horizun_target", {"pid": revit_pid})
    if not isinstance(payload, dict) or payload.get("selected_pid") != revit_pid:
        raise RuntimeError(
            f"Horizun did not select requested Revit PID {revit_pid}: {payload!r}"
        )
    return payload


def _validate_p6_live_readback(payload: object, authorization) -> str:
    """Require a typed query payload to match the accepted R04 baseline."""

    if not isinstance(payload, dict):
        raise TypeError("RUN-003 P6 baseline query did not return a typed object")
    if (
        payload.get("matched_total") != 25
        or payload.get("returned") != 25
        or payload.get("coverage_complete") is not True
        or payload.get("unreadable_total") != 0
    ):
        raise ValueError("RUN-003 live model no longer matches the accepted P6 element count")
    expected_categories = {"Massa": 7, "Pisos": 14, "Telhados": 4}
    if payload.get("summary", {}).get("by_category") != expected_categories:
        raise ValueError("RUN-003 live model categories differ from the accepted P6 baseline")

    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != 25:
        raise ValueError("RUN-003 P6 baseline query returned an incomplete row set")
    mass_rows = {
        row.get("name"): row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("name"), str)
        and row["name"].startswith("MASS-")
    }
    expected_mass_names = {
        f"MASS-{component}" for component in authorization.mass_bounding_boxes_m
    }
    if set(mass_rows) != expected_mass_names or len(mass_rows) != 7:
        raise ValueError("RUN-003 live mass set differs from the accepted P6 baseline")

    for component, expected in authorization.mass_bounding_boxes_m.items():
        actual = mass_rows[f"MASS-{component}"].get("bounding_box")
        if not isinstance(actual, dict):
            raise ValueError(f"RUN-003 live mass bounding box is missing: {component}")
        for bound in ("min", "max"):
            coordinates = actual.get(bound)
            expected_coordinates = expected.get(bound)
            if (
                not isinstance(coordinates, list)
                or expected_coordinates is None
                or len(coordinates) != 3
                or any(
                    not math.isclose(float(value), float(reference), abs_tol=1e-6)
                    for value, reference in zip(
                        coordinates, expected_coordinates, strict=True
                    )
                )
            ):
                raise ValueError(
                    f"RUN-003 P6 mass bounding boxes differ: {component} {bound}"
                )

    row_ids = [row.get("element_id") for row in rows if isinstance(row, dict)]
    if len(row_ids) != 25 or len(set(row_ids)) != 25:
        raise ValueError("RUN-003 P6 query element IDs are missing or duplicated")
    for floor_id in authorization.administrative_floor_element_ids.values():
        if row_ids.count(floor_id) != 1:
            raise ValueError("RUN-003 administrative P6 floor IDs changed")

    fingerprint = payload.get("result_set_fingerprint")
    if not isinstance(fingerprint, str) or not fingerprint:
        raise ValueError("RUN-003 P6 live query has no result fingerprint")
    return fingerprint


def _require_accepted_p6_fingerprint(observed: str, accepted: str) -> str:
    if observed != accepted:
        raise ValueError(
            "opened RUN-003 P6 checkpoint fingerprint differs from accepted "
            f"evidence: expected={accepted!r}, observed={observed!r}"
        )
    return observed


def _write_p6_fingerprint_diagnostic(
    *,
    journal_path: Path,
    run_key: str,
    checkpoint: Path,
    authorization,
    checkpoint_verified: bool,
    compact_payload: dict,
    detail_payload: dict,
) -> Path:
    """Persist a bounded read-only comparison artifact without accepting drift."""

    if not run_key or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in run_key):
        raise ValueError("RUN-003 P6 diagnostic run key is not a safe filename component")
    if checkpoint_verified is not True:
        raise ValueError("RUN-003 P6 diagnostic requires a verified checkpoint manifest")
    rows = detail_payload.get("rows")
    if not isinstance(rows, list) or len(rows) != 25:
        raise ValueError("RUN-003 P6 diagnostic requires exactly 25 detailed rows")

    selected_rows = []
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("RUN-003 P6 diagnostic contains a non-object row")
        bounding_box = row.get("bounding_box")
        if not isinstance(bounding_box, dict):
            raise TypeError("RUN-003 P6 diagnostic row has no bounding box")
        bounds = {}
        for bound in ("min", "max"):
            coordinates = bounding_box.get(bound)
            if (
                not isinstance(coordinates, list)
                or len(coordinates) != 3
                or any(not math.isfinite(float(value)) for value in coordinates)
            ):
                raise ValueError("RUN-003 P6 diagnostic row has invalid bounding coordinates")
            bounds[bound] = [float(value) for value in coordinates]
        element_id = row.get("element_id")
        unique_id = row.get("unique_id")
        category = row.get("category")
        name = row.get("name")
        if (
            not isinstance(element_id, int)
            or not isinstance(unique_id, str)
            or not unique_id
            or not isinstance(category, str)
            or not isinstance(name, str)
        ):
            raise TypeError("RUN-003 P6 diagnostic row is missing typed identity fields")
        selected_rows.append(
            {
                "element_id": element_id,
                "unique_id": unique_id,
                "category": category,
                "name": name,
                "bounding_box": bounds,
            }
        )
    selected_rows.sort(key=lambda row: row["element_id"])
    if len({row["element_id"] for row in selected_rows}) != 25:
        raise ValueError("RUN-003 P6 diagnostic ElementIds are not unique")
    if len({row["unique_id"] for row in selected_rows}) != 25:
        raise ValueError("RUN-003 P6 diagnostic UniqueIds are not unique")

    compact_summary = compact_payload.get("summary", {}).get("by_category")
    detail_summary = detail_payload.get("summary", {}).get("by_category")
    if compact_summary != {"Massa": 7, "Pisos": 14, "Telhados": 4}:
        raise ValueError("RUN-003 P6 diagnostic compact category summary is unexpected")
    canonical_rows = json.dumps(
        selected_rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    diagnostic = {
        "schema_version": 1,
        "status": "DIAGNOSTIC_ONLY_FINGERPRINT_MISMATCH",
        "run_key": run_key,
        "checkpoint": {
            "path": str(Path(checkpoint).resolve()),
            "sha256": authorization.checkpoint_sha256,
            "manifest_verified": True,
            "opened_file_version": "2027",
            "upgrade_allowed": False,
        },
        "fingerprints": {
            "accepted": authorization.p6_readback_fingerprint,
            "observed_compact": compact_payload.get("result_set_fingerprint"),
            "observed_detailed": detail_payload.get("result_set_fingerprint"),
        },
        "readback": {
            "matched_total": compact_payload.get("matched_total"),
            "returned": compact_payload.get("returned"),
            "coverage_complete": compact_payload.get("coverage_complete"),
            "unreadable_total": compact_payload.get("unreadable_total"),
            "categories": compact_summary,
            "detailed_categories": detail_summary,
            "row_count": len(selected_rows),
            "rows_sha256": hashlib.sha256(canonical_rows).hexdigest(),
            "rows": selected_rows,
        },
        "model_write_performed": False,
        "acceptance_gate_passed": False,
    }
    journal = Path(journal_path).resolve()
    output_path = journal.with_name(
        f"{journal.stem}-p6-readback-diagnostic-{run_key}.json"
    )
    try:
        output_path.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("RUN-003 P6 diagnostic path is outside the repository") from exc
    with output_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(diagnostic, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    return output_path


def _verify_p6_live_readback(transport, authorization) -> str:
    """Require the live model to match the complete accepted R04 baseline."""

    payload = _read_tool(
        transport,
        "horizun_query_model",
        {
            "categories": [
                "OST_Mass",
                "OST_Floors",
                "OST_Roofs",
                "OST_Walls",
                "OST_Rooms",
            ],
            "coordinate_units": "m",
            "include_bounding_box": True,
            "include_types": False,
            "max_rows": 100,
            "cache_mode": "bypass",
            "parameter_format": "compact",
            "response_mode": "compact",
        },
    )
    fingerprint = _validate_p6_live_readback(payload, authorization)
    if fingerprint == authorization.p6_readback_fingerprint:
        return fingerprint

    detailed_payload = _read_tool(
        transport,
        "horizun_query_model",
        {
            "categories": [
                "OST_Mass",
                "OST_Floors",
                "OST_Roofs",
                "OST_Walls",
                "OST_Rooms",
            ],
            "coordinate_units": "m",
            "include_bounding_box": True,
            "include_types": False,
            "max_rows": 100,
            "parameter_format": "compact",
            "response_mode": "compact",
            "cache_mode": "bypass",
            "return_fields": ["unique_id", "category", "name"],
        },
    )
    _validate_p6_live_readback(detailed_payload, authorization)
    try:
        reconciliation = verify_reconciled_p6_readback(
            REPOSITORY_ROOT, authorization, payload, detailed_payload
        )
    except P6FingerprintReconciliationError as exc:
        raise ValueError(
            "RUN-003 P6 fingerprint mismatch is not covered by exact readback "
            f"reconciliation: {exc}"
        ) from exc
    print(
        "P6 exact-readback reconciliation:",
        reconciliation["historical_accepted_fingerprint"],
        "->",
        reconciliation["observed_compact_fingerprint"],
        "rows_sha256=",
        reconciliation["rows_sha256"],
    )
    return fingerprint


def _load_known_failed_r05_records(journal_path: Path) -> list[dict]:
    """Accept only the recorded eight-floor, unsaved R05 partial from this run."""

    try:
        journal = json.loads(Path(journal_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("known RUN-003 failed R05 journal is unavailable") from exc
    if not isinstance(journal, dict):
        raise TypeError("known RUN-003 failed R05 journal is malformed")
    records = journal.get("records")
    if (
        journal.get("stage") != "R05"
        or journal.get("status") != "FAILED"
        or journal.get("persistence") is not None
        or not isinstance(records, list)
        or len(records) != 705
        or not all(isinstance(record, dict) for record in records)
    ):
        raise ValueError("journal does not describe the known RUN-003 partial R05 attempt")
    verified = [record for record in records if record.get("status") == "VERIFIED"]
    observed = {record.get("logical_id"): record for record in verified}
    if set(observed) != set(RUN003_FAILED_R05_FLOOR_IDS):
        raise ValueError("journal does not describe the known RUN-003 partial R05 attempt")
    if any(
        record.get("element_id") != RUN003_FAILED_R05_FLOOR_IDS[logical_id]
        or record.get("capability") != "revit.create_floor"
        or not isinstance(record.get("unique_id"), str)
        or not record["unique_id"].strip()
        for logical_id, record in observed.items()
    ) or len({record["unique_id"] for record in observed.values()}) != 8:
        raise ValueError("journal identities do not match the known RUN-003 partial R05 attempt")
    if len(verified) != 8 or sum(record.get("status") == "FAILED" for record in records) != 697:
        raise ValueError("journal record statuses do not match the known RUN-003 partial R05 attempt")
    return list(observed.values())


def _validate_known_r05_partial_model(payload: object, records, authorization) -> dict:
    """Prove the live document is exactly P6 plus the eight journaled floor writes."""

    expected_message = "live document does not match the known RUN-003 partial R05 state"
    if not isinstance(payload, dict):
        raise TypeError(expected_message)
    rows = payload.get("rows")
    summary = payload.get("summary")
    reported_categories = (
        summary.get("by_category") if isinstance(summary, dict) else None
    )
    row_categories: dict[str, int] = {}
    row_types: dict[str, int] = {}
    row_keys_sample: list[list[str] | str] = []
    if isinstance(rows, list):
        for row in rows:
            row_type = type(row).__name__
            row_types[row_type] = row_types.get(row_type, 0) + 1
            if len(row_keys_sample) < 3:
                row_keys_sample.append(
                    sorted(str(key) for key in row)[:32]
                    if isinstance(row, dict)
                    else row_type
                )
            if isinstance(row, dict) and isinstance(row.get("category"), str):
                category = row["category"]
                row_categories[category] = row_categories.get(category, 0) + 1
    observed = (
        f"observed matched_total={payload.get('matched_total')!r}, "
        f"returned={payload.get('returned')!r}, row_count={len(rows) if isinstance(rows, list) else None!r}, "
        f"coverage_complete={payload.get('coverage_complete')!r}, "
        f"unreadable_total={payload.get('unreadable_total')!r}, "
        f"reported_categories={reported_categories!r}, row_categories={row_categories!r}, "
        f"row_types={row_types!r}, row_keys_sample={row_keys_sample!r}"
    )

    def reject(detail: str) -> None:
        raise ValueError(f"{expected_message}: {detail}; {observed}")

    expected_live_categories = {"Massa": 7, "Pisos": 22, "Telhados": 4}
    if (
        payload.get("matched_total") != 33
        or payload.get("returned") != 33
        or payload.get("coverage_complete") is not True
        or payload.get("unreadable_total") != 0
        or reported_categories != expected_live_categories
        or not isinstance(rows, list)
        or len(rows) != 33
    ):
        reject("live completeness or expected 7/22/4 category counts differ")
    by_id = {
        row.get("element_id"): row
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("element_id"), int)
        and not isinstance(row.get("element_id"), bool)
    }
    if (
        len(by_id) != 33
        or set(by_id) != {row.get("element_id") for row in rows}
        or len({row.get("unique_id") for row in rows if isinstance(row.get("unique_id"), str)}) != 33
    ):
        reject("element IDs or unique IDs are missing, duplicated, or malformed")
    expected_partial = {record["element_id"]: record for record in records}
    for element_id, expected in expected_partial.items():
        row = by_id.get(element_id)
        if (
            not isinstance(row, dict)
            or row.get("category") != "Pisos"
            or row.get("unique_id") != expected["unique_id"]
        ):
            reject(f"journaled partial element {element_id} is missing or mismatched")

    baseline_rows = [row for element_id, row in by_id.items() if element_id not in expected_partial]
    baseline_categories: dict[str, int] = {}
    for row in baseline_rows:
        category = row.get("category")
        if not isinstance(category, str):
            reject("a P6 baseline row has no category")
        baseline_categories[category] = baseline_categories.get(category, 0) + 1
    if baseline_categories != {"Massa": 7, "Pisos": 14, "Telhados": 4}:
        reject(f"baseline categories are {baseline_categories!r}, expected 7/14/4")

    mass_rows = {
        row.get("name"): row
        for row in baseline_rows
        if row.get("category") == "Massa" and isinstance(row.get("name"), str)
    }
    expected_mass_names = {
        f"MASS-{component}" for component in authorization.mass_bounding_boxes_m
    }
    if set(mass_rows) != expected_mass_names:
        reject(f"baseline mass names are {sorted(mass_rows)!r}")
    for component, expected_bounds in authorization.mass_bounding_boxes_m.items():
        actual = mass_rows[f"MASS-{component}"].get("bounding_box")
        if not isinstance(actual, dict):
            reject(f"baseline mass {component} has no bounding box")
        for bound in ("min", "max"):
            coordinates = actual.get(bound)
            reference = expected_bounds.get(bound)
            if (
                not isinstance(coordinates, (list, tuple))
                or not isinstance(reference, (list, tuple))
                or len(coordinates) != 3
                or len(reference) != 3
                or any(
                    not math.isclose(float(value), float(expected), abs_tol=1e-6)
                    for value, expected in zip(coordinates, reference, strict=True)
                )
            ):
                reject(f"baseline mass {component} {bound} coordinates differ")
    baseline_ids = {row.get("element_id") for row in baseline_rows}
    missing_admin_ids = [
        element_id
        for element_id in authorization.administrative_floor_element_ids.values()
        if element_id not in baseline_ids
    ]
    if missing_admin_ids:
        reject(f"administrative P6 floor IDs are missing: {missing_admin_ids!r}")
    return {
        "matched_total": 33,
        "partial_element_ids": sorted(expected_partial),
        "p6_element_count_after_excluding_partial": 25,
        "p6_categories_after_excluding_partial": baseline_categories,
    }


def _floor_operation_geometry(operation) -> dict:
    """Summarize one current R05 floor profile for typed readback comparison."""

    payload = getattr(operation, "payload", None)
    geometry = payload.get("geometry") if isinstance(payload, dict) else None
    rings = geometry.get("footprint") if isinstance(geometry, dict) else None
    level_id = payload.get("level_id") if isinstance(payload, dict) else None
    if (
        not isinstance(rings, list)
        or not rings
        or isinstance(level_id, bool)
        or not isinstance(level_id, int)
        or level_id <= 0
    ):
        raise ValueError("known R05 floor operation lacks a typed profile or level")

    all_points: list[tuple[float, float]] = []
    ring_areas = []
    for ring in rings:
        if not isinstance(ring, list) or len(ring) < 4:
            raise ValueError("known R05 floor operation has an invalid closed profile")
        points = []
        for point in ring:
            if (
                not isinstance(point, (list, tuple))
                or len(point) not in {2, 3}
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    for value in point
                )
            ):
                raise ValueError("known R05 floor operation has non-finite profile points")
            points.append((float(point[0]), float(point[1])))
        if any(
            not math.isclose(points[0][axis], points[-1][axis], abs_tol=1e-8)
            for axis in range(2)
        ):
            raise ValueError("known R05 floor operation profile is not closed")
        signed_area = sum(
            points[index][0] * points[index + 1][1]
            - points[index + 1][0] * points[index][1]
            for index in range(len(points) - 1)
        ) / 2.0
        ring_areas.append(abs(signed_area))
        all_points.extend(points[:-1])

    area_m2 = ring_areas[0] - sum(ring_areas[1:])
    if not math.isfinite(area_m2) or area_m2 <= 0:
        raise ValueError("known R05 floor operation has non-positive plan area")
    return {
        "level_id": level_id,
        "area_m2": area_m2,
        "bounds_xy_m": {
            "min": [min(point[index] for point in all_points) for index in range(2)],
            "max": [max(point[index] for point in all_points) for index in range(2)],
        },
    }


def _validate_known_r05_partial_geometry(
    payload: object, records, operations, level_names: dict[int, str]
) -> dict:
    """Match all eight persisted partial floors to current plan extents, areas and levels."""

    expected_ids = set(RUN003_FAILED_R05_FLOOR_IDS)
    records = list(records)
    records_by_logical = {
        record.get("logical_id"): record for record in records if isinstance(record, dict)
    }
    known_floor_operations = [
        operation
        for operation in operations
        if getattr(operation, "logical_id", None) in expected_ids
    ]
    operations_by_logical = {
        getattr(operation, "logical_id", None): operation
        for operation in known_floor_operations
    }
    if (
        set(records_by_logical) != expected_ids
        or len(records_by_logical) != len(records)
        or set(operations_by_logical) != expected_ids
        or len(operations_by_logical) != len(known_floor_operations)
        or any(
            getattr(operations_by_logical[logical_id], "semantic_capability", None)
            != "revit.create_floor"
            for logical_id in expected_ids
        )
    ):
        raise ValueError("current R05 plan does not contain the exact known eight-floor set")

    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise TypeError("known R05 floor readback has no typed rows")
    expected_by_id = {
        int(record["element_id"]): (logical_id, record)
        for logical_id, record in records_by_logical.items()
    }
    partial_rows = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("element_id") in expected_by_id
    ]
    if len(partial_rows) != len(expected_ids):
        raise ValueError("known R05 floor readback is missing a journaled floor")
    observed_by_id = {row.get("element_id"): row for row in partial_rows}
    if len(observed_by_id) != len(expected_ids):
        raise ValueError("known R05 floor readback has duplicated ElementIds")

    verified_floors = []
    for element_id, (logical_id, journal_record) in expected_by_id.items():
        row = observed_by_id[element_id]
        # Revit's floor Name is a display/type label; journaled ElementId and
        # UniqueId bind the logical operation, while category checks element kind.
        if (
            row.get("category") != "Pisos"
            or row.get("unique_id") != journal_record.get("unique_id")
        ):
            raise ValueError(f"known R05 floor identity differs for {logical_id}")
        expected = _floor_operation_geometry(operations_by_logical[logical_id])
        expected_level_name = level_names.get(expected["level_id"])
        if not isinstance(expected_level_name, str) or not expected_level_name.strip():
            raise ValueError(f"current R05 floor level name is unavailable for {logical_id}")
        if row.get("level") != expected_level_name:
            raise ValueError(f"known R05 floor level differs for {logical_id}")

        bbox = row.get("bounding_box")
        if not isinstance(bbox, dict):
            raise TypeError(f"known R05 floor bounds are missing for {logical_id}")
        for axis in range(2):
            for bound in ("min", "max"):
                actual = bbox.get(bound)
                expected_value = expected["bounds_xy_m"][bound][axis]
                if (
                    not isinstance(actual, (list, tuple))
                    or len(actual) != 3
                    or isinstance(actual[axis], bool)
                    or not isinstance(actual[axis], (int, float))
                    or not math.isfinite(actual[axis])
                    or not math.isclose(
                        float(actual[axis]), expected_value, rel_tol=0.0, abs_tol=1e-3
                    )
                ):
                    raise ValueError(f"known R05 floor bounds differ for {logical_id}")

        parameters = row.get("parameters")
        actual_area = parameters.get("Area") if isinstance(parameters, dict) else None
        area_source_unit = "scalar_without_reported_unit"
        if isinstance(actual_area, dict):
            area_source_unit = str(actual_area.get("unit", "")).strip()
            unit = (
                area_source_unit.casefold()
                .replace("\u00b2", "2")
                .replace("^", "")
                .replace(".", "")
            )
            unit_to_m2 = {
                "m2": 1.0,
                "sq m": 1.0,
                "sqm": 1.0,
                "square meter": 1.0,
                "square meters": 1.0,
                "square metre": 1.0,
                "square metres": 1.0,
                "ft2": 0.09290304,
                "sf": 0.09290304,
                "sq ft": 0.09290304,
                "sqft": 0.09290304,
                "square feet": 0.09290304,
                "square foot": 0.09290304,
            }
            conversion = unit_to_m2.get(unit)
            if conversion is None:
                raise ValueError(
                    f"known R05 floor Area unit is unsupported for {logical_id}: {unit!r}"
                )
            actual_area = actual_area.get("value")
            if (
                isinstance(actual_area, bool)
                or not isinstance(actual_area, (int, float))
                or not math.isfinite(actual_area)
            ):
                raise ValueError(f"typed Area parameter is missing for {logical_id}")
            actual_area = float(actual_area) * conversion
        if (
            isinstance(actual_area, bool)
            or not isinstance(actual_area, (int, float))
            or not math.isfinite(actual_area)
        ):
            raise ValueError(f"typed Area parameter is missing for {logical_id}")
        if not math.isclose(
            float(actual_area), expected["area_m2"], rel_tol=0.0, abs_tol=1e-2
        ):
            raise ValueError(f"known R05 floor area differs for {logical_id}")
        verified_floors.append(
            {
                "logical_id": logical_id,
                "element_id": element_id,
                "unique_id": row["unique_id"],
                "level_id": expected["level_id"],
                "level": expected_level_name,
                "area_m2": float(actual_area),
                "expected_area_m2": expected["area_m2"],
                "area_source_unit": area_source_unit,
                "bounding_box": bbox,
                "readback_status": "VERIFIED",
            }
        )
    verified_floors.sort(key=lambda floor: floor["logical_id"])
    return {
        "verified_partial_floor_ids": sorted(expected_by_id),
        "geometry_checks": {
            "bounds_xy": "PASS",
            "area_m2": "PASS",
            "level_name": "PASS",
            "expected_geometry_source": "current_R05_plan",
            "observed_geometry_scope": "typed_bounds_area_level",
        },
        "floors": verified_floors,
    }


def _remaining_r05_operations(operations, reconciled_logical_ids: set[str]) -> list:
    """Filter only the exact eight floor operations already read and reconciled."""

    expected_ids = set(RUN003_FAILED_R05_FLOOR_IDS)
    if reconciled_logical_ids != expected_ids:
        raise ValueError("reconciled IDs do not match the exact known eight-floor set")
    operation_ids = [getattr(operation, "logical_id", None) for operation in operations]
    matching = [logical_id for logical_id in operation_ids if logical_id in expected_ids]
    if (
        set(matching) != expected_ids
        or len(matching) != len(expected_ids)
        or any(
            getattr(operation, "semantic_capability", None) != "revit.create_floor"
            for operation in operations
            if getattr(operation, "logical_id", None) in expected_ids
        )
    ):
        raise ValueError("current R05 plan does not contain the exact known eight-floor set")
    return [
        operation
        for operation in operations
        if getattr(operation, "logical_id", None) not in expected_ids
    ]


def _merge_reconciled_r05_records(plan, result, recovery_evidence: dict):
    """Combine current R05 writes with the eight independently re-read prior floors."""

    reconciled = recovery_evidence.get("reconciled_partial_floors")
    if not isinstance(reconciled, dict) or not isinstance(reconciled.get("floors"), list):
        raise TypeError("RUN-003 partial floor reconciliation evidence is incomplete")
    floors_by_id = {floor.get("logical_id"): floor for floor in reconciled["floors"]}
    expected_ids = set(RUN003_FAILED_R05_FLOOR_IDS)
    if set(floors_by_id) != expected_ids or len(floors_by_id) != len(reconciled["floors"]):
        raise ValueError("RUN-003 partial floor reconciliation evidence is not the exact eight-floor set")
    all_operations = {operation.logical_id: operation for operation in plan.operations}
    if set(expected_ids) - set(all_operations):
        raise ValueError("full R05 plan lost a reconciled floor operation")

    existing_ids = {record.logical_id for record in result.records}
    if existing_ids & expected_ids:
        raise ValueError("R05 execution unexpectedly repeated a reconciled floor write")
    for logical_id, floor in floors_by_id.items():
        if floor.get("readback_status") != "VERIFIED":
            raise ValueError(f"RUN-003 partial floor is not verified: {logical_id}")
        operation = all_operations[logical_id]
        result.records.append(
            OperationRunRecord(
                stage=BimStage.R05,
                logical_id=logical_id,
                semantic_capability="revit.create_floor",
                provider=getattr(operation, "preferred_provider", None) or "horizun",
                tool="reconciled_existing_readback",
                reported_success=True,
                status=RunStatus.VERIFIED,
                unique_id=floor["unique_id"],
                evidence={
                    "element_id": floor["element_id"],
                    "unique_id": floor["unique_id"],
                    "level": floor["level"],
                    "level_id": floor["level_id"],
                    "area_m2": floor["area_m2"],
                    "area_source_unit": floor["area_source_unit"],
                    "bounding_box": floor["bounding_box"],
                    "reconciled_existing": True,
                    "prior_journal_status": "VERIFIED",
                    "geometry_checks": reconciled["geometry_checks"],
                },
            )
        )
    order = {operation.logical_id: index for index, operation in enumerate(plan.operations)}
    result.records.sort(key=lambda record: order.get(record.logical_id, len(order)))
    if result.status is RunStatus.VERIFIED and len(result.records) == len(plan.operations):
        result.status = RunStatus.VERIFIED
    return result


def _row_model_snapshot(row: object) -> tuple:
    if not isinstance(row, dict):
        raise TypeError("P6 checkpoint rows differ from the known RUN-003 partial")
    element_id = row.get("element_id")
    unique_id = row.get("unique_id")
    category = row.get("category")
    name = row.get("name")
    bounds = row.get("bounding_box")
    if (
        isinstance(element_id, bool)
        or not isinstance(element_id, int)
        or not isinstance(unique_id, str)
        or not unique_id.strip()
        or not isinstance(category, str)
        or not isinstance(name, str)
        or not isinstance(bounds, dict)
    ):
        raise TypeError("P6 checkpoint rows differ from the known RUN-003 partial")
    normalized_bounds = []
    for bound in ("min", "max"):
        coordinates = bounds.get(bound)
        if not isinstance(coordinates, (list, tuple)) or len(coordinates) != 3:
            raise TypeError("P6 checkpoint rows differ from the known RUN-003 partial")
        values = []
        for value in coordinates:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise TypeError("P6 checkpoint rows differ from the known RUN-003 partial")
            values.append(float(value))
        normalized_bounds.extend(values)
    return element_id, unique_id, category, name, tuple(normalized_bounds)


def _compare_known_partial_to_p6_checkpoint(partial_payload, checkpoint_payload, records) -> None:
    """Require the unsaved target to equal the P6 checkpoint plus eight floors."""

    partial_ids = {record["element_id"] for record in records}
    partial_rows = partial_payload.get("rows") if isinstance(partial_payload, dict) else None
    checkpoint_rows = checkpoint_payload.get("rows") if isinstance(checkpoint_payload, dict) else None
    if not isinstance(partial_rows, list) or not isinstance(checkpoint_rows, list):
        raise TypeError("P6 checkpoint rows differ from the known RUN-003 partial")
    try:
        partial_by_id = {_row_model_snapshot(row)[0]: _row_model_snapshot(row) for row in partial_rows}
        checkpoint_by_id = {
            _row_model_snapshot(row)[0]: _row_model_snapshot(row)
            for row in checkpoint_rows
        }
    except (TypeError, ValueError) as exc:
        raise ValueError("P6 checkpoint rows differ from the known RUN-003 partial") from exc
    if (
        len(partial_by_id) != len(partial_rows)
        or len(checkpoint_by_id) != len(checkpoint_rows)
        or set(partial_by_id) - partial_ids != set(checkpoint_by_id)
        or set(partial_by_id) & partial_ids != partial_ids
    ):
        raise ValueError("P6 checkpoint rows differ from the known RUN-003 partial")
    for element_id, expected in checkpoint_by_id.items():
        actual = partial_by_id[element_id]
        if actual[:4] != expected[:4] or any(
            not math.isclose(left, right, abs_tol=1e-6)
            for left, right in zip(actual[4], expected[4], strict=True)
        ):
            raise ValueError("P6 checkpoint rows differ from the known RUN-003 partial")


def _query_r05_level_names(transport, operations) -> dict[int, str]:
    expected_floor_ids = set(RUN003_FAILED_R05_FLOOR_IDS)
    operations = list(operations)
    known_floors = [
        operation
        for operation in operations
        if getattr(operation, "logical_id", None) in expected_floor_ids
    ]
    known_floor_ids = [getattr(operation, "logical_id", None) for operation in known_floors]
    if (
        set(known_floor_ids) != expected_floor_ids
        or len(known_floor_ids) != len(expected_floor_ids)
        or any(
            getattr(operation, "semantic_capability", None) != "revit.create_floor"
            for operation in known_floors
        )
    ):
        raise ValueError("current R05 plan does not contain the exact known eight-floor set")
    level_ids = sorted(
        {
            _floor_operation_geometry(operation)["level_id"]
            for operation in known_floors
        }
    )
    payload = _read_tool(
        transport,
        "horizun_query_model",
        {
            "element_ids": level_ids,
            "categories": ["OST_Levels"],
            "cache_mode": "bypass",
            "include_types": False,
            "max_rows": len(level_ids),
            "response_mode": "compact",
            "return_fields": ["unique_id", "category", "name"],
        },
    )
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if (
        not isinstance(rows, list)
        or payload.get("matched_total") != len(level_ids)
        or payload.get("returned") != len(level_ids)
        or payload.get("coverage_complete") is not True
        or payload.get("unreadable_total") != 0
        or len(rows) != len(level_ids)
    ):
        raise ValueError("RUN-003 R05 level readback is incomplete")
    names: dict[int, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("RUN-003 R05 level row is not typed")
        element_id = row.get("element_id")
        name = row.get("name")
        if (
            isinstance(element_id, bool)
            or not isinstance(element_id, int)
            or not isinstance(name, str)
            or not name.strip()
            or element_id in names
        ):
            raise ValueError("RUN-003 R05 level identity or name is invalid")
        names[element_id] = name
    if set(names) != set(level_ids) or len(set(names.values())) != len(names):
        raise ValueError("RUN-003 R05 levels do not match the plan's exact level IDs")
    return names


def _close_p6_inspection_checkpoint(transport, target: Path, checkpoint: Path, run_key: str):
    _activate(transport, target)
    closed = _read_tool(
        transport,
        "horizun_document_session",
        {
            "operation": "close",
            "target_document": str(checkpoint),
            "save_on_close": False,
            "activate_other": True,
            "idempotency_key": _new_idempotency_key("close-p6-inspection", run_key),
        },
    )
    if not isinstance(closed, dict) or closed.get("closed") is not True:
        raise RuntimeError(f"RUN-003 P6 checkpoint close was not verified: {closed!r}")
    _activate(transport, target)
    active = _active_path(_document_info(transport))
    if not active or Path(active).resolve() != target:
        raise RuntimeError("RUN-003 target is not active after P6 checkpoint inspection")
    return closed


def _restore_known_failed_r05_partial(
    transport,
    target: Path,
    authorization,
    *,
    journal_path: Path,
    run_key: str,
    operations,
) -> dict:
    """Reconcile the persisted eight-floor partial against P6 and current R05."""

    target = Path(target).resolve()
    permits_target_path = getattr(authorization, "permits_target_path", None)
    if not callable(permits_target_path) or not permits_target_path(target):
        raise ValueError("cannot restore RUN-003 partial: target is outside the P6 grant")
    info = _document_info(transport)
    active = _active_path(info)
    if not active or Path(active).resolve() != target:
        raise ValueError("cannot restore RUN-003 partial: exact target is not active")
    records = _load_known_failed_r05_records(journal_path)
    live = _read_tool(
        transport,
        "horizun_query_model",
        {
            "categories": ["OST_Mass", "OST_Floors", "OST_Roofs", "OST_Walls", "OST_Rooms"],
            "coordinate_units": "m",
            "include_bounding_box": True,
            "include_types": False,
            "max_rows": 100,
            "response_mode": "compact",
            "cache_mode": "bypass",
            "return_fields": ["unique_id", "category", "name"],
        },
    )
    state = _validate_known_r05_partial_model(live, records, authorization)
    checkpoint = (REPOSITORY_ROOT / authorization.checkpoint_path).resolve()
    if not checkpoint.is_file() or checkpoint == target:
        raise ValueError("RUN-003 P6 checkpoint path is unavailable or aliases the target")
    try:
        checkpoint.relative_to(REPOSITORY_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("RUN-003 P6 checkpoint is outside the repository") from exc
    checkpoint_manifest = checkpoint.with_suffix(checkpoint.suffix + ".manifest.json")
    checkpoint_verified = CheckpointManager().verify_checkpoint(checkpoint_manifest)
    checkpoint_opened = False
    try:
        opened_checkpoint = _read_tool(
            transport,
            "horizun_document_session",
            {
                "operation": "open",
                "file_path": str(checkpoint),
                "expected_version": "2027",
                "allow_upgrade": False,
                "idempotency_key": _new_idempotency_key("inspect-p6-checkpoint", run_key),
            },
        )
        checkpoint_info = _document_info(transport)
        checkpoint_active = _active_path(checkpoint_info)
        checkpoint_opened = bool(
            checkpoint_active and Path(checkpoint_active).resolve() == checkpoint
        )
        _validate_document_open_result(
            opened_checkpoint,
            checkpoint,
            expected_version="2027",
            context="RUN-003 P6 checkpoint open",
        )
        if not checkpoint_opened:
            raise RuntimeError("RUN-003 P6 checkpoint was not active after open")
        # Match the accepted compact-query signature for the P6 fingerprint.
        checkpoint_payload = _read_tool(
            transport,
            "horizun_query_model",
            {
                "categories": ["OST_Mass", "OST_Floors", "OST_Roofs", "OST_Walls", "OST_Rooms"],
                "coordinate_units": "m",
                "include_bounding_box": True,
                "include_types": False,
                "max_rows": 100,
                "cache_mode": "bypass",
                "parameter_format": "compact",
                "response_mode": "compact",
            },
        )
        checkpoint_fingerprint = _validate_p6_live_readback(checkpoint_payload, authorization)
        checkpoint_detail_payload = _read_tool(
            transport,
            "horizun_query_model",
            {
                "categories": ["OST_Mass", "OST_Floors", "OST_Roofs", "OST_Walls", "OST_Rooms"],
                "coordinate_units": "m",
                "include_bounding_box": True,
                "include_types": False,
                "max_rows": 100,
                "parameter_format": "compact",
                "response_mode": "compact",
                "cache_mode": "bypass",
                "return_fields": ["unique_id", "category", "name"],
            },
        )
        checkpoint_detail_fingerprint = _validate_p6_live_readback(
            checkpoint_detail_payload, authorization
        )
        if checkpoint_fingerprint != authorization.p6_readback_fingerprint:
            diagnostic_path = _write_p6_fingerprint_diagnostic(
                journal_path=journal_path,
                run_key=run_key,
                checkpoint=checkpoint,
                authorization=authorization,
                checkpoint_verified=checkpoint_verified,
                compact_payload=checkpoint_payload,
                detail_payload=checkpoint_detail_payload,
            )
            try:
                reconciliation = verify_reconciled_p6_readback(
                    REPOSITORY_ROOT,
                    authorization,
                    checkpoint_payload,
                    checkpoint_detail_payload,
                )
            except P6FingerprintReconciliationError as exc:
                raise ValueError(
                    "P6 fingerprint mismatch is not covered by exact readback "
                    f"reconciliation: {exc}; detailed diagnostic saved to {diagnostic_path}"
                ) from exc
            print(
                "P6 checkpoint fingerprint reconciled against exact typed rows:",
                reconciliation["rows_sha256"],
            )
        else:
            checkpoint_fingerprint = _require_accepted_p6_fingerprint(
                checkpoint_fingerprint, authorization.p6_readback_fingerprint
            )
        _activate(transport, target)
        target_active = _active_path(_document_info(transport))
        if not target_active or Path(target_active).resolve() != target:
            raise RuntimeError("RUN-003 partial target could not be reactivated for comparison")
        live_again = _read_tool(
            transport,
            "horizun_query_model",
            {
                "categories": ["OST_Mass", "OST_Floors", "OST_Roofs", "OST_Walls", "OST_Rooms"],
                "coordinate_units": "m",
                "include_bounding_box": True,
                "include_types": False,
                "max_rows": 100,
                "response_mode": "compact",
                "cache_mode": "bypass",
                "return_fields": ["unique_id", "category", "name", "level"],
                "return_parameters": ["Area"],
                "parameter_format": "full",
            },
        )
        live_state = _validate_known_r05_partial_model(
            live_again, records, authorization
        )
        _compare_known_partial_to_p6_checkpoint(
            live_again, checkpoint_detail_payload, records
        )
        level_names = _query_r05_level_names(transport, operations)
        partial_geometry = _validate_known_r05_partial_geometry(
            live_again, records, operations, level_names
        )
    except Exception:
        if checkpoint_opened:
            try:
                _close_p6_inspection_checkpoint(transport, target, checkpoint, run_key)
            except Exception as cleanup_exc:
                raise RuntimeError(
                    "RUN-003 P6 comparison failed and its inspection document could not be closed"
                ) from cleanup_exc
        raise
    checkpoint_closed = _close_p6_inspection_checkpoint(
        transport, target, checkpoint, run_key
    )
    active_after = _document_info(transport)
    active_path = _active_path(active_after)
    if not active_path or Path(active_path).resolve() != target:
        raise RuntimeError("RUN-003 target was not preserved after P6 inspection")
    return {
        "journal_path": str(Path(journal_path).resolve()),
        "reconciled_persisted_writes": state["partial_element_ids"],
        "pre_close_live_state": live_state,
        "reconciled_partial_floors": partial_geometry,
        "p6_checkpoint": {
            "path": str(checkpoint),
            "checkpoint_manager_verified": checkpoint_verified,
            "readback_fingerprint": checkpoint_fingerprint,
            "baseline_element_count": len(checkpoint_detail_payload["rows"]),
            "detailed_readback_fingerprint": checkpoint_detail_fingerprint,
            "target_matches_p6_plus_partial": True,
            "inspection_close": checkpoint_closed,
        },
        "target_preserved_active": True,
        "p6_baseline_fingerprint": checkpoint_fingerprint,
    }


def _save_checkpoint_reopen_stage(
    transport,
    rvt: Path,
    result,
    *,
    run_key: str,
    checkpoint_root: Path,
    p6_checkpoint_sha256: str,
) -> dict:
    """Persist one verified stage and prove its elements after a cold reopen."""

    target = Path(rvt).resolve()
    if result.status is not RunStatus.VERIFIED:
        raise ValueError(f"{result.stage.name} must be VERIFIED before persistence")
    if not result.records:
        raise ValueError(f"{result.stage.name} has no readback records to persist")

    expected_by_id: dict[int, dict[str, str]] = {}
    expected_unique_ids: set[str] = set()
    for record in result.records:
        if record.status is not RunStatus.VERIFIED:
            raise ValueError(f"{record.logical_id} is not VERIFIED")
        evidence = record.evidence
        element_id = evidence.get("element_id") if isinstance(evidence, dict) else None
        unique_id = record.unique_id
        if isinstance(element_id, bool) or not isinstance(element_id, (int, str)):
            raise ValueError(f"{record.logical_id} has no typed element ID")
        try:
            element_id = int(element_id)
        except ValueError as exc:
            raise ValueError(f"{record.logical_id} has an invalid element ID") from exc
        if not isinstance(unique_id, str) or not unique_id.strip():
            raise ValueError(f"{record.logical_id} has no persistent unique ID")
        if evidence.get("unique_id") != unique_id:
            raise ValueError(f"{record.logical_id} readback identity is inconsistent")
        if element_id in expected_by_id or unique_id in expected_unique_ids:
            raise ValueError(f"{record.logical_id} duplicates a stage element identity")
        expected_by_id[element_id] = {
            "logical_id": record.logical_id,
            "unique_id": unique_id,
        }
        expected_unique_ids.add(unique_id)

    active_before_save = _document_info(transport)
    if not isinstance(active_before_save, dict) or _active_path(active_before_save) is None:
        raise ValueError("cannot identify the active document before stage save")
    if Path(_active_path(active_before_save)).resolve() != target:
        raise ValueError("active document changed before stage save")

    query_arguments = {
        "element_ids": sorted(expected_by_id),
        "cache_mode": "bypass",
        "include_bounding_box": True,
        "include_links": False,
        "max_rows": max(100, len(expected_by_id)),
        "response_mode": "compact",
        "return_fields": ["unique_id", "category", "name"],
        "coordinate_units": "m",
    }

    def read_stage_geometry(label: str):
        payload = _read_tool(transport, "horizun_query_model", query_arguments)
        if not isinstance(payload, dict):
            raise RuntimeError(f"{result.stage.name} {label} query is not typed")
        rows = payload.get("rows")
        if (
            payload.get("matched_total") != len(expected_by_id)
            or payload.get("returned") != len(expected_by_id)
            or payload.get("coverage_complete") is not True
            or payload.get("unreadable_total") != 0
            or not isinstance(rows, list)
            or len(rows) != len(expected_by_id)
        ):
            raise RuntimeError(f"{result.stage.name} {label} readback is incomplete")

        rows_by_id = {
            row.get("element_id"): row
            for row in rows
            if isinstance(row, dict)
            and isinstance(row.get("element_id"), int)
            and not isinstance(row.get("element_id"), bool)
        }
        if set(rows_by_id) != set(expected_by_id):
            raise RuntimeError(f"{result.stage.name} {label} element IDs changed")

        bounds_by_id = {}
        for element_id, expected in expected_by_id.items():
            row = rows_by_id[element_id]
            if row.get("unique_id") != expected["unique_id"]:
                raise RuntimeError(
                    f"{result.stage.name} {label} identity changed for {expected['logical_id']}"
                )
            bbox = row.get("bounding_box")
            if not isinstance(bbox, dict):
                raise RuntimeError(
                    f"{result.stage.name} {label} bounds missing for {expected['logical_id']}"
                )
            normalized = {}
            for bound_name in ("min", "max"):
                coordinates = bbox.get(bound_name)
                if not isinstance(coordinates, (list, tuple)) or len(coordinates) != 3:
                    raise RuntimeError(
                        f"{result.stage.name} {label} bounds invalid for {expected['logical_id']}"
                    )
                values = []
                for coordinate in coordinates:
                    if (
                        isinstance(coordinate, bool)
                        or not isinstance(coordinate, (int, float))
                        or not math.isfinite(coordinate)
                    ):
                        raise RuntimeError(
                            f"{result.stage.name} {label} bounds invalid for {expected['logical_id']}"
                        )
                    values.append(float(coordinate))
                normalized[bound_name] = values
            bounds_by_id[element_id] = normalized
        return payload, rows_by_id, bounds_by_id

    pre_save_readback, _pre_save_rows, pre_save_bounds = read_stage_geometry(
        "pre-save"
    )

    save = _read_tool(
        transport,
        "horizun_save_document",
        {
            "target_document": str(target),
            "idempotency_key": _new_idempotency_key("save", run_key),
        },
    )
    if not isinstance(save, dict) or save.get("outcome") != "saved_verified":
        raise RuntimeError(f"{result.stage.name} typed save was not verified: {save!r}")

    closed = _read_tool(
        transport,
        "horizun_document_session",
        {
            "operation": "close",
            "target_document": str(target),
            "save_on_close": True,
            "activate_other": True,
            "idempotency_key": _new_idempotency_key("close", run_key),
        },
    )
    if not isinstance(closed, dict) or closed.get("closed") is not True:
        raise RuntimeError(f"{result.stage.name} close was not verified: {closed!r}")

    checkpoint_dir = Path(checkpoint_root).resolve() / result.stage.name
    checkpoint_path = checkpoint_dir / (
        f"P7-T01-{result.stage.name}-AMANDA-RUN-003-{run_key}.rvt"
    )
    manifest = CheckpointManager().create_checkpoint(
        target,
        checkpoint_path,
        stage=stage_checkpoint_label(result.stage),
        save_state="SAVED",
        source_stable=True,
        reopen_verify=True,
        document_id=target.stem,
        document_path=target,
        provenance={
            "task": "P7-T01",
            "run": "RUN-003",
            "p6_checkpoint_sha256": p6_checkpoint_sha256,
            "stage_element_ids": sorted(expected_by_id),
        },
    )
    manager = CheckpointManager()
    if not manager.verify_checkpoint(manifest):
        raise RuntimeError(f"{result.stage.name} checkpoint hash verification failed")

    reopened = _read_tool(
        transport,
        "horizun_document_session",
        {
            "operation": "open",
            "file_path": str(target),
            "expected_version": "2027",
            "allow_upgrade": False,
            "idempotency_key": _new_idempotency_key("reopen", run_key),
        },
    )
    _validate_document_open_result(
        reopened,
        target,
        expected_version="2027",
        context=f"{result.stage.name} exact cold reopen",
    )
    active_after_reopen = _document_info(transport)
    if (
        not isinstance(active_after_reopen, dict)
        or _active_path(active_after_reopen) is None
        or Path(_active_path(active_after_reopen)).resolve() != target
    ):
        raise RuntimeError(f"{result.stage.name} reopened a different active document")

    readback, rows_by_id, post_reopen_bounds = read_stage_geometry("post-reopen")
    for element_id, expected_bounds in pre_save_bounds.items():
        actual_bounds = post_reopen_bounds[element_id]
        for bound_name in ("min", "max"):
            if any(
                not math.isclose(before, after, rel_tol=0.0, abs_tol=1e-6)
                for before, after in zip(
                    expected_bounds[bound_name], actual_bounds[bound_name]
                )
            ):
                logical_id = expected_by_id[element_id]["logical_id"]
                raise RuntimeError(
                    f"{result.stage.name} post-reopen geometry changed for {logical_id}"
                )

    return {
        "save": save,
        "checkpoint_path": str(manifest.checkpoint_path),
        "checkpoint_manifest_path": str(manifest.manifest_path),
        "checkpoint_sha256": manifest.sha256,
        "checkpoint_size_bytes": manifest.size_bytes,
        "checkpoint_verified": True,
        "p6_checkpoint_sha256": p6_checkpoint_sha256,
        "close": closed,
        "closed": True,
        "reopen": reopened,
        "reopened_exact_target": True,
        "active_document_after_reopen": active_after_reopen,
        "geometry_preserved": True,
        "pre_save_bounds_m": {
            str(element_id): bounds
            for element_id, bounds in sorted(pre_save_bounds.items())
        },
        "post_reopen_readback": {
            "matched_total": readback["matched_total"],
            "returned": readback["returned"],
            "coverage_complete": readback["coverage_complete"],
            "unreadable_total": readback["unreadable_total"],
            "element_ids": sorted(rows_by_id),
            "unique_ids": [rows_by_id[item]["unique_id"] for item in sorted(rows_by_id)],
            "geometry_preserved": True,
        },
    }


def _acquire_writer_lease(
    lock: WriterLock,
    *,
    document_identity: str,
    reuse_existing_run003_lease: bool,
) -> bool:
    """Acquire a fresh lease or retain the exact live RUN-003 P7 lease."""

    existing = lock.inspect()
    if existing is None:
        lock.acquire(
            document_identity=document_identity,
            reclaim_abandoned=False,
        )
        return True

    expected_document = Path(document_identity).resolve()
    try:
        existing_document = Path(existing["document_identity"]).resolve()
    except (KeyError, TypeError, ValueError):
        existing_document = None
    if (
        reuse_existing_run003_lease
        and existing.get("owner") == "amanda-P7-RUN003-production"
        and existing.get("host") == lock.host
        and existing_document == expected_document
        and lock.is_held_by_live_owner()
    ):
        return False

    raise LockHeldByAnotherOwner(
        "writer lease is held by " + str(existing.get("owner")) + " at " + str(lock.path)
    )


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
    rvt: Path,
    *,
    execute: bool,
    max_stage: str | None = None,
    revit_pid: int | None = None,
    resume_run003_study: bool = False,
    reuse_existing_run003_lease: bool = False,
) -> int:
    from amanda_agent.bim.models import BimStage

    rvt = Path(rvt).resolve()
    _validate_canonical_target(rvt)
    max_stage = max_stage or ("R05" if resume_run003_study else "R13")
    if resume_run003_study and max_stage != "R05":
        print("RUN-003 study resume is limited to R05 per execution", file=sys.stderr)
        return 2
    study_authorization = None
    if reuse_existing_run003_lease and not resume_run003_study:
        print("existing P7 lease reuse is only valid for RUN-003 study resume", file=sys.stderr)
        return 2
    if resume_run003_study:
        if not rvt.is_file():
            print("the existing RUN-003 target is missing", file=sys.stderr)
            return 2
        study_authorization = load_run003_study_authorization(REPOSITORY_ROOT)
        if not study_authorization.permits_target_path(rvt):
            print("resume target is not the exact authorized RUN-003 path", file=sys.stderr)
            return 2

    program = json.loads(
        (REPOSITORY_ROOT / "project" / "requirements" / "program.json").read_text(
            encoding="utf-8"
        )
    )
    profile = CanonicalReferenceProfile.load(REPOSITORY_ROOT)
    _report_canonical_sources(profile)
    layout = build_canonical_pavilion_layout(program, profile)
    if study_authorization is not None:
        if layout.content_hash != study_authorization.layout_hash:
            print("current RUN-003 layout hash differs from the accepted P6 layout", file=sys.stderr)
            return 2
        selection = load_run003_study_selection(
            REPOSITORY_ROOT, study_authorization
        )
    else:
        selection = build_selection(
            layout,
            generation_run=GENERATION_RUN,
            timestamp="2026-09-23T00:00:00Z",
            profile=profile,
        )
    print("solution id:", selection.solution.solution_id)
    print("approval hash:", selection.approval_hash)
    if study_authorization is not None and (
        selection.solution.solution_id != study_authorization.solution_id
        or selection.approval_hash != study_authorization.approval_hash
        or selection.layout_hash != study_authorization.layout_hash
        or selection.solution.bim_eligible is not False
        or study_authorization.identity_bim_eligible is not False
        or study_authorization.identity_revit_write_authorized is not False
    ):
        print("RUN-003 selection does not match the P6 continuation grant", file=sys.stderr)
        return 2
    if execute and not selection.solution.bim_eligible and study_authorization is None:
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

    if study_authorization is not None:
        mode, max_bim_stage = _execution_scope(
            bim_eligible=selection.solution.bim_eligible,
            requested_max_stage=max_stage,
            run003_study_authorization=study_authorization,
            target_path=rvt,
        )
    else:
        mode, max_bim_stage = None, BimStage[max_stage]
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
            mode
            if study_authorization is not None
            else ExecutionMode.DETAILED_BIM
            if execute
            else ExecutionMode.PLANNING_ONLY
        ),
        max_stage=max_bim_stage,
        start_stage=(BimStage.R05 if study_authorization is not None else BimStage.R01),
        run003_study_authorization=study_authorization,
    )
    print("planned stages:", [plan.stage.name for plan in plans])
    print("layout hash:", layout.content_hash)
    print("approval hash:", selection.approval_hash)
    template = None
    if study_authorization is None:
        template = find_project_template(None)
        print("template:", template)
    if not execute:
        print("dry run: nothing written")
        return 0

    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    if study_authorization is None:
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
    if study_authorization is None and rvt.exists():
        stamp = time.strftime("%Y%m%d-%H%M%S")
        rvt = rvt.with_name(f"{rvt.stem}.{stamp}{rvt.suffix}")
        print("target already exists; writing a new attempt:", rvt.name)

    lock = WriterLock(
        LOCK_PATH,
        owner=(
            "amanda-P7-RUN003-production"
            if study_authorization is not None
            else "amanda-production-run"
        ),
    )
    try:
        owns_lock = _acquire_writer_lease(
            lock,
            document_identity=str(rvt),
            reuse_existing_run003_lease=(
                study_authorization is not None and reuse_existing_run003_lease
            ),
        )
    except LockHeldByAnotherOwner as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("lease acquired:" if owns_lock else "using existing RUN-003 lease")
    try:
        with McpProbeTransport(timeout=900.0) as transport:
            recovery_evidence = None
            if study_authorization is not None:
                health = _read_tool(transport, "horizun_health", {})
                mcp_client_pid = transport.pin_process_identity()
                _validate_revit_session(
                    health,
                    expected_build=build,
                    revit_pid=revit_pid,
                    target_path=rvt,
                    mcp_client_pid=mcp_client_pid,
                )
            if revit_pid is not None:
                selected = _select_revit_target(transport, revit_pid)
                print("selected Revit PID:", selected["selected_pid"])
            if study_authorization is not None:
                info = _document_info(transport)
                active = _active_path(info)
                if not active or Path(active).resolve() != rvt:
                    raise ValueError("Horizun document readback does not match RUN-003")
                try:
                    baseline_fingerprint = _verify_p6_live_readback(
                        transport, study_authorization
                    )
                except ValueError:
                    exact_run003_target = (
                        REPOSITORY_ROOT
                        / "revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt"
                    ).resolve()
                    if rvt != exact_run003_target or not RUN003_FAILED_R05_JOURNAL.is_file():
                        raise
                    recovery_evidence = _restore_known_failed_r05_partial(
                        transport,
                        rvt,
                        study_authorization,
                        journal_path=RUN003_FAILED_R05_JOURNAL,
                        run_key=uuid.uuid4().hex[:12],
                        operations=plans[0].operations,
                    )
                    baseline_fingerprint = recovery_evidence[
                        "p6_baseline_fingerprint"
                    ]
                    print(
                        "reconciled persisted R05 partial against P6 and the current plan; "
                        "target remains open"
                    )
                print("P6 baseline readback:", baseline_fingerprint)
            run_key = uuid.uuid4().hex[:12]
            if study_authorization is None:
                # New runs start from a clean template and save to a new file.
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

                if not _active_path(info) or not str(_active_path(info)).casefold().endswith(
                    ".rte"
                ):
                    for _ in range(20):
                        time.sleep(0.5)
                        info = _document_info(transport)
                        if _active_path(info):
                            break
                    print("re-read after open:", json.dumps(info, ensure_ascii=False)[:200])

                source = _active_path(info) or str(template)
                transport.call(
                    "horizun_document_session",
                    {
                        "operation": "save_as",
                        "target_document": source,
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
                execution_plan = plan
                if recovery_evidence is not None and plan.stage is BimStage.R05:
                    remaining = _remaining_r05_operations(
                        plan.operations,
                        set(recovery_evidence["reconciled_persisted_writes"]),
                    )
                    execution_plan = plan.model_copy(update={"operations": remaining})
                    print(
                        "R05 idempotent resume:",
                        len(recovery_evidence["reconciled_persisted_writes"]),
                        "reconciled floor operations skipped;",
                        len(remaining),
                        "current plan operations remain",
                    )
                # Several attempts are open at once, and Revit's active document
                # moves between them.  The provider acts on the ACTIVE document
                # and refuses to switch by itself, so the target is activated
                # before each stage rather than left to whatever was in front.
                _activate(transport, rvt)
                result = execute_stage(execution_plan, invoker=invoker)
                if recovery_evidence is not None and plan.stage is BimStage.R05:
                    result = _merge_reconciled_r05_records(
                        plan, result, recovery_evidence
                    )
                journal = _stage_journal_path(plan.stage, run_key)
                journal.parent.mkdir(parents=True, exist_ok=True)
                record_evidence = [
                    {
                        "logical_id": record.logical_id,
                        "capability": record.semantic_capability,
                        "status": record.status.value,
                        "element_id": record.evidence.get("element_id"),
                        "unique_id": record.unique_id,
                        "error": record.error,
                    }
                    for record in result.records
                ]
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
                    journal.write_text(
                        json.dumps(
                            {
                                "stage": result.stage.name,
                                "status": result.status.value,
                                "records": record_evidence,
                                "persistence": None,
                                "recovery": recovery_evidence,
                            },
                            indent=2,
                            sort_keys=True,
                            default=str,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    return 4

                persistence = None
                if study_authorization is not None:
                    try:
                        persistence = _save_checkpoint_reopen_stage(
                            transport,
                            rvt,
                            result,
                            run_key=run_key,
                            checkpoint_root=EVIDENCE_ROOT / "checkpoints",
                            p6_checkpoint_sha256=study_authorization.checkpoint_sha256,
                        )
                    except Exception as exc:  # noqa: BLE001 - persistence is a stage gate
                        journal.write_text(
                            json.dumps(
                                {
                                    "stage": result.stage.name,
                                    "status": "PERSISTENCE_FAILED",
                                    "records": record_evidence,
                                    "persistence_error": {
                                        "type": type(exc).__name__,
                                        "message": str(exc),
                                    },
                                    "recovery": recovery_evidence,
                                },
                                indent=2,
                                sort_keys=True,
                                default=str,
                            )
                            + "\n",
                            encoding="utf-8",
                        )
                        print(
                            f"stopping: {plan.stage.name} persistence gate failed: {exc}",
                            file=sys.stderr,
                        )
                        return 5

                journal.write_text(
                    json.dumps(
                        {
                            "stage": result.stage.name,
                            "status": result.status.value,
                            "records": record_evidence,
                            "persistence": persistence,
                            "recovery": recovery_evidence,
                        },
                        indent=2,
                        sort_keys=True,
                        default=str,
                    )
                    + "\n",
                    encoding="utf-8",
                )

            if study_authorization is None:
                transport.call(
                    "horizun_save_document",
                    {
                        "target_document": str(rvt),
                        "idempotency_key": _new_idempotency_key("save", run_key),
                    },
                )
                print("saved:", rvt)
            else:
                print("completed study stages are saved, checkpointed, reopened, and read back")
        return 0
    finally:
        if owns_lock:
            lock.release()
            print("lease released")
        else:
            print("existing RUN-003 lease retained")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rvt", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--resume-run003-study", action="store_true")
    parser.add_argument("--reuse-existing-run003-lease", action="store_true")
    parser.add_argument("--max-stage", default=None)
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
        max_stage=args.max_stage
        or ("R05" if args.resume_run003_study else "R13"),
        revit_pid=args.revit_pid,
        resume_run003_study=args.resume_run003_study,
        reuse_existing_run003_lease=args.reuse_existing_run003_lease,
    )


if __name__ == "__main__":
    raise SystemExit(main())
