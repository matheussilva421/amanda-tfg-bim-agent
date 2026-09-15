from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter

from amanda_agent.qa.models import QaResult
from amanda_agent.qa.pdf import validate_pdf


def make_pdf(path: Path, pages: int = 2):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=100, height=100)
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def test_missing_and_zero_byte_pdf_are_rejected(tmp_path: Path):
    missing = validate_pdf(tmp_path / "missing.pdf", preview_root=tmp_path / "preview")
    assert missing.result is QaResult.BLOCKED_BY_INPUT

    empty = tmp_path / "empty.pdf"
    empty.write_bytes(b"")
    assert validate_pdf(empty, preview_root=tmp_path / "preview").result is not QaResult.PASS


def test_page_count_and_all_png_previews_are_generated(tmp_path: Path):
    pdf = make_pdf(tmp_path / "plan.pdf", pages=2)
    report = validate_pdf(
        pdf,
        manifest={"pages": {"exact": 2}},
        preview_root=tmp_path / "release" / "preview" / "pdf",
    )
    assert report.result is QaResult.PASS_WITH_WARNINGS
    metrics = report.details["metrics"]
    assert metrics["pages"] == 2
    assert len(metrics["sizes"]) == 2
    assert len(metrics["sha256"]) == 2
    assert sorted((tmp_path / "release" / "preview" / "pdf").glob("page-*.png"))
    assert len(list((tmp_path / "release" / "preview" / "pdf").glob("page-*.png"))) == 2


def test_blank_page_is_a_machine_signal(tmp_path: Path):
    pdf = make_pdf(tmp_path / "blank.pdf", pages=1)
    report = validate_pdf(pdf, preview_root=tmp_path / "preview")
    assert report.details["metrics"]["blank_pages"] == [1]
    assert any(issue.code == "PDF_BLANK_PAGE_SIGNAL" for issue in report.issues)
