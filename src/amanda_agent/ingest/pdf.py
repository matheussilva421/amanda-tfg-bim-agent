"""Selectable-text PDF extraction with immutable source provenance.

The adapter deliberately keeps extraction and OCR separate.  A page's
selectable text wins whenever it exists; an OCR provider can only fill a page
that has no selectable text at all.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from ..logging import EventLog
from ..paths import ProjectPaths
from ..redaction import redact

PYPDF_PINNED_VERSION = "6.0.0"
PARSER_REQUIREMENT = f"pypdf=={PYPDF_PINNED_VERSION}"


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str
    extraction_method: str


@dataclass(frozen=True)
class PdfExtraction:
    source_path: Path
    source_sha256: str
    pages: list[ExtractedPage]
    output_path: Path
    parser: str = PARSER_REQUIREMENT


def sha256_file(path: Path) -> str:
    """Hash a source without loading the whole file into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_stem(path: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", path.stem).strip("._")
    return stem or "source"


def _write_extracted_text(
    output_path: Path,
    *,
    source_path: Path,
    source_sha256: str,
    pages: list[ExtractedPage],
) -> None:
    lines = [
        f"source_sha256: {source_sha256}",
        f"source_filename: {source_path.name}",
        f"parser: {PARSER_REQUIREMENT}",
        "",
    ]
    for page in pages:
        lines.extend(
            [
                f"page: {page.page_number}",
                f"extraction_method: {page.extraction_method}",
                page.text.rstrip("\n"),
                "",
            ]
        )
    payload = "\n".join(lines)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=str(output_path.parent),
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, output_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def extract_pdf(
    source_path: Path,
    *,
    project_root: Path | None = None,
    paths: ProjectPaths | None = None,
    ocr_provider: Callable[[int], str | None] | None = None,
    event_log: EventLog | None = None,
) -> PdfExtraction:
    """Extract a PDF and persist a page-numbered text artifact.

    ``ocr_provider`` is intentionally a fallback only.  It is called for a
    page only when pypdf returns no selectable text for that page, so OCR can
    never replace or modify authoritative selectable text.
    """
    source = Path(source_path).resolve()
    if paths is not None and project_root is not None:
        raise ValueError("pass either paths or project_root, not both")
    resolved_paths = paths or ProjectPaths.from_root(project_root or Path.cwd())
    log = event_log or EventLog(
        resolved_paths.logs / "events.jsonl",
        task="P03-T05",
        provider="pypdf",
    )

    try:
        if not source.is_file():
            raise FileNotFoundError(f"PDF source not found: {source}")
        source_sha256 = sha256_file(source)
        reader = PdfReader(str(source), strict=False)
        pages: list[ExtractedPage] = []
        for page_number, page in enumerate(reader.pages, start=1):
            selectable_text = page.extract_text() or ""
            if selectable_text.strip():
                text = selectable_text
                method = "selectable_text"
            elif ocr_provider is not None:
                text = ocr_provider(page_number) or ""
                method = "ocr_fallback" if text else "selectable_text"
            else:
                text = ""
                method = "selectable_text"
            pages.append(
                ExtractedPage(
                    page_number=page_number,
                    text=text,
                    extraction_method=method,
                )
            )

        output_path = (
            resolved_paths.root
            / "project"
            / "provenance"
            / "extracted"
            / f"{_safe_stem(source)}.{source_sha256}.txt"
        )
        _write_extracted_text(
            output_path,
            source_path=source,
            source_sha256=source_sha256,
            pages=pages,
        )
        log.record(
            operation="extract_pdf",
            status="PASS",
            data=redact(
                {
                    "source_path": str(source),
                    "source_sha256": source_sha256,
                    "pages": len(pages),
                    "output_path": str(output_path),
                    "parser": PARSER_REQUIREMENT,
                }
            ),
        )
        return PdfExtraction(
            source_path=source,
            source_sha256=source_sha256,
            pages=pages,
            output_path=output_path,
        )
    except BaseException as error:
        log.record_exception(operation="extract_pdf", error=error)
        raise


__all__ = [
    "PARSER_REQUIREMENT",
    "PYPDF_PINNED_VERSION",
    "ExtractedPage",
    "PdfExtraction",
    "extract_pdf",
    "sha256_file",
]
