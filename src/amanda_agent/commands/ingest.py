"""Copy source files into the immutable local source store."""

from __future__ import annotations

import mimetypes
import os
import tempfile
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import yaml

from ..ingest.manifest import (
    HASH_CHUNK_SIZE,
    SourceDocument,
    SourceManifest,
    sha256_file,
)
from ..logging import EventLog
from ..models.state import ProjectState
from ..paths import ProjectPaths
from ..redaction import redact
from ..state.store import StateStore
from ..state.tasks import load_registry


class IngestError(Exception):
    """Base class for expected source-ingestion refusals."""


class SourceInputError(IngestError):
    """The requested source path is absent or is not a regular file."""


class SourceManifestError(IngestError):
    """The existing source manifest cannot be trusted or written."""


class ImmutableSourcePathConflict(IngestError):
    """A destination already contains different immutable bytes."""


class ImmutableSourceMissing(IngestError):
    """A manifest entry points at a source copy that is no longer present."""


class SourceCopyVerificationError(IngestError):
    """The copied bytes did not retain the incoming source hash."""


class SourceIdConflict(IngestError):
    """A stable source id was requested for a hash that owns another id."""


# Descriptive alias for callers that prefer the longer exception name.
ImmutableSourceConflictError = ImmutableSourcePathConflict


MANIFEST_RELATIVE_PATH = Path("project") / "provenance" / "source-manifest.yaml"


def _manifest_path(paths: ProjectPaths) -> Path:
    return paths.root / MANIFEST_RELATIVE_PATH


def _load_manifest(path: Path) -> SourceManifest:
    if not path.exists():
        return SourceManifest()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if raw is None:
            return SourceManifest()
        return SourceManifest.model_validate(raw)
    except (OSError, yaml.YAMLError, ValueError, TypeError) as exc:
        raise SourceManifestError("source manifest is invalid: " + str(path)) from exc


def _manifest_copy_path(root: Path, immutable_path: str) -> Path:
    root = root.resolve()
    candidate = (root / immutable_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SourceManifestError(
            "manifest immutable path is outside project root: " + immutable_path
        ) from exc
    return candidate


def _validate_manifest_paths(root: Path, manifest: SourceManifest) -> None:
    immutable_root = (root / "docs" / "source").resolve()
    for document in manifest.documents:
        candidate = _manifest_copy_path(root, document.immutable_path)
        try:
            candidate.relative_to(immutable_root)
        except ValueError as exc:
            raise SourceManifestError(
                "manifest immutable path is outside docs/source: "
                + document.immutable_path
            ) from exc


def _write_manifest_atomically(path: Path, manifest: SourceManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        manifest.model_dump(mode="json"), sort_keys=False, allow_unicode=True
    )
    handle, temporary_name = tempfile.mkstemp(
        prefix=".source-manifest.", suffix=".tmp", dir=str(path.parent)
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException as exc:
        temporary_path.unlink(missing_ok=True)
        if isinstance(exc, IngestError):
            raise
        raise SourceManifestError(
            "could not write source manifest: " + str(path)
        ) from exc


def _load_project_context(paths: ProjectPaths) -> tuple[ProjectState, str | None]:
    """Read existing foundation state for observability without mutating it."""
    state = StateStore(paths.project_state).load()
    task_status = None
    task_graph_path = paths.state / "task-graph.yaml"
    if task_graph_path.exists():
        try:
            record = load_registry(task_graph_path).tasks.get("P03-T03")
            task_status = str(record.status) if record else None
        except (OSError, TypeError, ValueError, yaml.YAMLError):
            task_status = None
    return state, task_status


def _event_log(paths: ProjectPaths) -> EventLog:
    return EventLog(paths.logs / "ingest.jsonl", task="P03-T03")


def _record_event(
    log: EventLog,
    *,
    status: str,
    detail: str,
    source: Path | None = None,
    document: SourceDocument | None = None,
    state_revision: int | None = None,
    task_status: str | None = None,
) -> None:
    data: dict[str, object] = {"source": str(source) if source else None}
    if document is not None:
        data["source_id"] = document.source_id
        data["sha256"] = document.sha256
        data["immutable_path"] = document.immutable_path
    if state_revision is not None:
        data["state_revision"] = state_revision
    if task_status is not None:
        data["task_status"] = task_status
    log.record(
        operation="ingest",
        status=status,
        detail=detail,
        data=redact(data),
    )


def _copy_without_overwrite(
    source: Path, destination: Path, expected_hash: str
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with source.open("rb") as input_stream, destination.open("xb") as output_stream:
            while chunk := input_stream.read(HASH_CHUNK_SIZE):
                output_stream.write(chunk)
            output_stream.flush()
            os.fsync(output_stream.fileno())
    except BaseException:
        if destination.exists():
            destination.unlink(missing_ok=True)
        raise

    actual_hash = sha256_file(destination)
    if actual_hash != expected_hash:
        destination.unlink(missing_ok=True)
        raise SourceCopyVerificationError(
            "copied source hash mismatch at immutable path " + str(destination)
        )


def _document_for(
    source: Path, root: Path, digest: str, source_id: str | None = None
) -> SourceDocument:
    destination = root / "docs" / "source" / source.name
    mime_type = mimetypes.guess_type(source.name, strict=False)[0]
    return SourceDocument(
        source_id=source_id or "SRC-" + digest,
        filename=source.name,
        sha256=digest,
        mime_type=mime_type or "application/octet-stream",
        ingested_at=datetime.now(UTC),
        immutable_path=destination.relative_to(root).as_posix(),
    )


def ingest_sources(
    root: Path,
    source_paths: Iterable[Path],
    *,
    source_ids: Iterable[str | None] | None = None,
) -> list[SourceDocument]:
    """Ingest source files and return their manifest documents.

    Existing identical hashes are returned from the manifest without creating a
    second copy. Existing immutable paths with different hashes are refused.

    ``source_ids`` optionally assigns a stable id such as ``SRC-PROGRAM-001`` to
    each incoming path positionally. An explicit id is never silently discarded.
    """
    paths = ProjectPaths.from_root(Path(root))
    log = _event_log(paths)
    state, task_status = _load_project_context(paths)
    manifest_path = _manifest_path(paths)
    manifest = _load_manifest(manifest_path)
    _validate_manifest_paths(paths.root, manifest)
    results: list[SourceDocument] = []
    candidates = list(source_paths)
    requested_ids = list(source_ids) if source_ids is not None else None
    if requested_ids is not None:
        if len(requested_ids) != len(candidates):
            raise SourceIdConflict(
                "each ingested path needs exactly one --id value; refusing an "
                "ambiguous assignment"
            )
        assigned = [value for value in requested_ids if value]
        if len(set(assigned)) != len(assigned):
            raise SourceIdConflict("the same source id cannot be assigned twice")

    for index, candidate in enumerate(candidates):
        source = Path(candidate)
        requested_id = requested_ids[index] if requested_ids is not None else None
        try:
            if not source.exists() or not source.is_file():
                raise SourceInputError("source file not found: " + str(source))
            digest = sha256_file(source)

            by_hash = next(
                (
                    document
                    for document in manifest.documents
                    if document.sha256 == digest
                ),
                None,
            )
            if by_hash is not None:
                if requested_id and requested_id != by_hash.source_id:
                    raise SourceIdConflict(
                        "source "
                        + str(source)
                        + " already owns id "
                        + by_hash.source_id
                        + "; refusing to rename it to "
                        + requested_id
                    )
                immutable_copy = _manifest_copy_path(paths.root, by_hash.immutable_path)
                if not immutable_copy.is_file():
                    raise ImmutableSourceMissing(
                        "manifest source copy is missing: " + str(immutable_copy)
                    )
                if sha256_file(immutable_copy) != by_hash.sha256:
                    raise SourceManifestError(
                        "manifest source hash mismatch: " + str(immutable_copy)
                    )
                results.append(by_hash)
                _record_event(
                    log,
                    status="DUPLICATE",
                    detail="identical source hash already ingested",
                    source=source,
                    document=by_hash,
                    state_revision=state.state_revision,
                    task_status=task_status,
                )
                continue

            if requested_id:
                owner = next(
                    (
                        document
                        for document in manifest.documents
                        if document.source_id == requested_id
                    ),
                    None,
                )
                if owner is not None:
                    raise SourceIdConflict(
                        "source id "
                        + requested_id
                        + " already belongs to "
                        + owner.filename
                        + " ("
                        + owner.sha256
                        + ")"
                    )

            document = _document_for(source, paths.root, digest, requested_id)
            destination = paths.root / document.immutable_path
            if destination.exists():
                if not destination.is_file():
                    raise ImmutableSourcePathConflict(
                        "immutable source path is not a file: " + str(destination)
                    )
                existing_hash = sha256_file(destination)
                if existing_hash != digest:
                    raise ImmutableSourcePathConflict(
                        "immutable source path already contains different content: "
                        + str(destination)
                        + " (existing "
                        + existing_hash
                        + ", incoming "
                        + digest
                        + ")"
                    )
            else:
                _copy_without_overwrite(source, destination, digest)

            manifest.documents.append(document)
            _write_manifest_atomically(manifest_path, manifest)
            results.append(document)
            _record_event(
                log,
                status="PASS",
                detail="source copied and manifest updated",
                source=source,
                document=document,
                state_revision=state.state_revision,
                task_status=task_status,
            )
        except IngestError as exc:
            _record_event(
                log,
                status="REFUSED",
                detail=str(exc),
                source=source,
                state_revision=state.state_revision,
                task_status=task_status,
            )
            raise

    return results


def ingest_file(root: Path, source_path: Path) -> SourceDocument:
    """Convenience entry point for the single-file CLI form."""
    return ingest_sources(root, [source_path])[0]


run_ingest = ingest_sources
ingest = ingest_sources
