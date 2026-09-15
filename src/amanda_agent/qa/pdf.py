"""PDF export sanity checks and deterministic local page previews."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from PIL import ImageStat
from pypdf import PdfReader

from .models import QaCheck, QaCheckStatus, QaIssue, QaReport, Severity


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_pages(
    expected_pages: int | Mapping[str, Any] | None,
    manifest: Mapping[str, Any] | None,
) -> tuple[int | None, int | None]:
    value: Any = expected_pages
    if value is None and manifest is not None:
        value = manifest.get(
            "pages",
            manifest.get("expected_pages", manifest.get("expected_page_count")),
        )
    if isinstance(value, Mapping):
        exact = value.get("exact")
        minimum = value.get("min", value.get("minimum"))
        return (int(exact) if exact is not None else None, int(minimum) if minimum is not None else None)
    if value is None:
        return None, None
    return int(value), None


def _report(
    checks: list[QaCheck],
    issues: list[QaIssue],
    *,
    profile: str,
    scope: str,
    details: dict[str, Any] | None = None,
) -> QaReport:
    return QaReport(
        profile=profile,
        scope=scope,
        checks=checks,
        issues=issues,
        required_check_ids=[check.check_id for check in checks],
        details=details or {},
    )


def validate_pdf(
    path: str | Path,
    *,
    expected_pages: int | Mapping[str, Any] | None = None,
    manifest: Mapping[str, Any] | None = None,
    preview_root: str | Path | None = None,
    blank_variance_threshold: float = 1.0,
    profile: str = "STUDY",
    scope: str = "pdf",
) -> QaReport:
    """Validate a PDF and render every page for subsequent visual review."""

    target = Path(path)
    parse_check = QaCheck(
        check_id="pdf.parse", mandatory=True, status=QaCheckStatus.PASS,
        severity_if_failed=Severity.CRITICAL, scope="pdf"
    )
    if not target.is_file():
        parse_check.status = QaCheckStatus.BLOCKED
        return _report(
            [parse_check],
            [QaIssue(
                code="MISSING_INPUT_PDF",
                message=f"PDF file does not exist: {target}",
                severity=Severity.HIGH,
                scope="pdf",
                mandatory=True,
                evidence={"path": str(target)},
                check_id="pdf.parse",
                missing_input=True,
            )],
            profile=profile,
            scope=scope,
        )
    if target.stat().st_size == 0:
        parse_check.status = QaCheckStatus.FAIL
        return _report(
            [parse_check],
            [QaIssue(
                code="INVALID_PDF",
                message="PDF file is zero bytes",
                severity=Severity.CRITICAL,
                scope="pdf",
                mandatory=True,
                evidence={"path": str(target)},
                check_id="pdf.parse",
            )],
            profile=profile,
            scope=scope,
        )

    try:
        reader = PdfReader(str(target))
        page_count = len(reader.pages)
    except (OSError, ValueError) as exc:
        parse_check.status = QaCheckStatus.FAIL
        return _report(
            [parse_check],
            [QaIssue(
                code="INVALID_PDF",
                message=f"PDF could not be parsed: {exc}",
                severity=Severity.CRITICAL,
                scope="pdf",
                mandatory=True,
                evidence={"path": str(target), "error_type": type(exc).__name__},
                check_id="pdf.parse",
            )],
            profile=profile,
            scope=scope,
        )

    checks = [parse_check]
    issues: list[QaIssue] = []
    exact, minimum = _expected_pages(expected_pages, manifest)
    if exact is not None or minimum is not None:
        count_ok = (exact is None or page_count == exact) and (minimum is None or page_count >= minimum)
        checks.append(QaCheck(check_id="pdf.page_count", mandatory=True, status=QaCheckStatus.PASS if count_ok else QaCheckStatus.FAIL, severity_if_failed=Severity.HIGH, scope="pdf"))
        if not count_ok:
            issues.append(QaIssue(
                code="PDF_PAGE_COUNT_MISMATCH",
                message=f"PDF has {page_count} pages but export manifest expectation was not met",
                severity=Severity.HIGH,
                scope="pdf",
                mandatory=True,
                evidence={"pages": page_count, "expected_exact": exact, "expected_minimum": minimum},
                check_id="pdf.page_count",
            ))

    destination = Path(preview_root) if preview_root is not None else Path(__file__).resolve().parents[3] / "release" / "preview" / "pdf"
    destination.mkdir(parents=True, exist_ok=True)
    sizes: list[list[int]] = []
    blank_pages: list[int] = []
    page_hashes: list[str] = []
    render_error: Exception | None = None
    try:
        import pypdfium2 as pdfium  # type: ignore[import-untyped]

        document = pdfium.PdfDocument(str(target))
        try:
            for index in range(len(document)):
                page = document.get_page(index)
                try:
                    image = page.render(scale=1.0).to_pil()
                    image_path = destination / f"page-{index + 1:04d}.png"
                    image.save(image_path, format="PNG")
                    sizes.append([int(image.width), int(image.height)])
                    variance = float(ImageStat.Stat(image.convert("L")).var[0])
                    if variance <= blank_variance_threshold:
                        blank_pages.append(index + 1)
                    page_hashes.append(_sha256(image_path))
                finally:
                    page.close()
        finally:
            document.close()
    except (OSError, RuntimeError, ValueError) as exc:
        render_error = exc

    render_ok = render_error is None and len(sizes) == page_count and len(page_hashes) == page_count
    checks.append(QaCheck(check_id="pdf.render", mandatory=True, status=QaCheckStatus.PASS if render_ok else QaCheckStatus.FAIL, severity_if_failed=Severity.HIGH, scope="pdf"))
    if not render_ok:
        issues.append(QaIssue(
            code="PDF_RENDER_FAILED",
            message=f"not every PDF page could be rendered: {render_error}",
            severity=Severity.HIGH,
            scope="pdf",
            mandatory=True,
            evidence={"pages": page_count, "rendered": len(sizes), "error_type": type(render_error).__name__ if render_error else None},
            check_id="pdf.render",
        ))
    checks.append(QaCheck(check_id="pdf.blank_pages", mandatory=False, status=QaCheckStatus.PASS, severity_if_failed=Severity.MEDIUM, scope="pdf"))
    for page_number in blank_pages:
        issues.append(QaIssue(
            code="PDF_BLANK_PAGE_SIGNAL",
            message=f"page {page_number} has near-zero raster variance; visual review is required",
            severity=Severity.MEDIUM,
            scope="pdf",
            mandatory=False,
            evidence={"page": page_number, "variance_threshold": blank_variance_threshold},
            check_id="pdf.blank_pages",
        ))
    metrics = {
        "pages": page_count,
        "blank_pages": blank_pages,
        "sizes": sizes,
        "sha256": page_hashes,
        "file_sha256": _sha256(target),
    }
    return _report(
        checks,
        issues,
        profile=profile,
        scope=scope,
        details={"metrics": metrics, "preview_root": str(destination)},
    )


validate = validate_pdf
pdf_qa = validate_pdf


__all__ = ["pdf_qa", "validate", "validate_pdf"]
