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

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.providers import HorizunInvoker, McpProbeTransport
from amanda_agent.bim.runner import RunStatus, execute_stage
from amanda_agent.bim.checkpoints import CheckpointManager
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
from amanda_agent.production.selection import (
    build_selection,
    legacy_selection_history,
)
from amanda_agent.production.run003_study import (
    load_run003_study_authorization,
    load_run003_study_selection,
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
    if health.get("other_clients_connected") != 0:
        client_state = health.get("clients")
        clients_seen = (
            client_state.get("clients_seen")
            if isinstance(client_state, dict)
            else None
        )
        client_details = []
        if isinstance(clients_seen, list):
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
                    continue
                client_details.append(
                    "pid={pid}, process_name={process_name}, "
                    "seconds_since_last_request={age}, process_alive={alive}".format(
                        pid=safe_client_value(client.get("pid", "unknown")),
                        process_name=safe_client_value(
                            client.get("process_name") or "unknown"
                        ),
                        age=safe_client_value(
                            client.get("seconds_since_last_request", "unknown")
                        ),
                        alive=safe_client_value(
                            str(client.get("process_alive", "unknown")).lower()
                        ),
                    )
                )
        detail = (
            f"; clients_seen=[{'; '.join(client_details)}]"
            if client_details
            else ""
        )
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
            "parameter_format": "compact",
            "response_mode": "compact",
        },
    )
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
    if (
        not isinstance(reopened, dict)
        or reopened.get("opened") is not True
        or reopened.get("path_matches_request") is not True
        or reopened.get("upgraded_on_open") is not False
    ):
        raise RuntimeError(f"{result.stage.name} exact cold reopen failed: {reopened!r}")
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
            if study_authorization is not None:
                health = _read_tool(transport, "horizun_health", {})
                _validate_revit_session(
                    health,
                    expected_build=build,
                    revit_pid=revit_pid,
                    target_path=rvt,
                )
            if revit_pid is not None:
                selected = _select_revit_target(transport, revit_pid)
                print("selected Revit PID:", selected["selected_pid"])
            if study_authorization is not None:
                info = _document_info(transport)
                active = _active_path(info)
                if not active or Path(active).resolve() != rvt:
                    raise ValueError("Horizun document readback does not match RUN-003")
                baseline_fingerprint = _verify_p6_live_readback(
                    transport, study_authorization
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
                # Several attempts are open at once, and Revit's active document
                # moves between them.  The provider acts on the ACTIVE document
                # and refuses to switch by itself, so the target is activated
                # before each stage rather than left to whatever was in front.
                _activate(transport, rvt)
                result = execute_stage(plan, invoker=invoker)
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
