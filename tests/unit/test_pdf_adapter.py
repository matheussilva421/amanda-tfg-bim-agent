"""Behavioral contracts for immutable, selectable PDF extraction."""

from __future__ import annotations

import hashlib
from pathlib import Path

from amanda_agent.ingest.pdf import extract_pdf


def _pdf_with_text(pages: list[str]) -> bytes:
    """Build a tiny selectable-text PDF without a fixture dependency."""
    page_numbers = list(range(3, 3 + len(pages)))
    kids = " ".join(f"{number} 0 R" for number in page_numbers)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        (
            b"<< /Type /Pages /Kids ["
            + kids.encode("ascii")
            + b"] "
            + b"/Count "
            + str(len(pages)).encode("ascii")
            + b" >>"
        ),
    ]
    for index in range(len(pages)):
        content_number = 4 + len(pages) + index
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] "
            b"/Resources << /Font << /F1 "
            + str(3 + len(pages)).encode("ascii")
            + b" 0 R >> >> /Contents "
            + str(content_number).encode("ascii")
            + b" 0 R >>"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for page_text in pages:
        content = (
            "BT /F1 12 Tf 40 200 Td (" + page_text + ") Tj ET"
        ).encode("ascii")
        objects.append(
            b"<< /Length "
            + str(len(content)).encode("ascii")
            + b" >>\nstream\n"
            + content
            + b"\nendstream"
        )

    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{number} 0 obj\n".encode("ascii"))
        payload.extend(obj)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(
        f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii")
    )
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(payload)


def test_extract_pdf_preserves_page_numbers_and_source_hash(tmp_path: Path):
    source = tmp_path / "known-fixture.pdf"
    source.write_bytes(_pdf_with_text(["Page one alpha", "Page two beta"]))

    result = extract_pdf(source, project_root=tmp_path)

    assert [page.page_number for page in result.pages] == [1, 2]
    assert [page.text.strip() for page in result.pages] == [
        "Page one alpha",
        "Page two beta",
    ]
    expected_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert result.source_sha256 == expected_hash
    assert result.output_path.parent == (
        tmp_path / "project" / "provenance" / "extracted"
    )
    assert expected_hash in result.output_path.name
    stored = result.output_path.read_text(encoding="utf-8")
    assert f"source_sha256: {expected_hash}" in stored
    assert "page: 1" in stored and "page: 2" in stored


def test_selectable_text_cannot_be_overridden_by_ocr(tmp_path: Path):
    source = tmp_path / "authoritative.pdf"
    source.write_bytes(_pdf_with_text(["Authoritative selectable text"]))
    calls: list[int] = []

    def conflicting_ocr(page_number: int) -> str:
        calls.append(page_number)
        return "fabricated OCR text"

    result = extract_pdf(
        source,
        project_root=tmp_path,
        ocr_provider=conflicting_ocr,
    )

    assert result.pages[0].text.strip() == "Authoritative selectable text"
    assert calls == []


def test_extraction_records_a_redacted_event(tmp_path: Path):
    source = tmp_path / "logged.pdf"
    source.write_bytes(_pdf_with_text(["Logged page"]))

    extract_pdf(source, project_root=tmp_path)

    event_log = tmp_path / "logs" / "events.jsonl"
    assert event_log.exists()
    assert '"task": "P03-T05"' in event_log.read_text(encoding="utf-8")


def test_empty_pdf_page_may_use_ocr_but_selectable_pages_stay_primary(
    tmp_path: Path,
):
    source = tmp_path / "mixed.pdf"
    source.write_bytes(_pdf_with_text(["Selectable page", ""]))

    result = extract_pdf(
        source,
        project_root=tmp_path,
        ocr_provider=lambda page_number: f"OCR page {page_number}",
    )

    assert result.pages[0].text.strip() == "Selectable page"
    assert result.pages[1].text.strip() == "OCR page 2"
