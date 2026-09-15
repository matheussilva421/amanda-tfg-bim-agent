"""TDD contract for deterministic visual-documentation review."""

from __future__ import annotations

import importlib
import struct
import zlib
from pathlib import Path

import pytest


def _visual():
    try:
        return importlib.import_module("amanda_agent.qa.visual")
    except ModuleNotFoundError as exc:
        pytest.fail(f"visual QA is not implemented yet: {exc}")


def _png(path: Path, pixels: list[tuple[int, int, int, int]], width: int = 2, height: int = 2):
    raw = b"".join(
        b"\x00"
        + bytes(
            channel
            for pixel in pixels[row * width : (row + 1) * width]
            for channel in pixel
        )
        for row in range(height)
    )

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def test_human_review_queue_names_exact_previews_when_inspection_unavailable(tmp_path: Path):
    module = _visual()
    first = tmp_path / "sheet-02.png"
    second = tmp_path / "sheet-01.png"
    _png(first, [(255, 255, 255, 255)] * 4)
    _png(second, [(10, 10, 10, 255)] * 4)

    report = module.review_visuals(tmp_path, image_inspection_available=False)

    assert [item.path for item in report.human_review_queue] == [
        "sheet-01.png",
        "sheet-02.png",
    ]
    assert report.normative_visual_pass is False


def test_machine_findings_are_visual_review_only(tmp_path: Path):
    module = _visual()
    page = tmp_path / "page.png"
    _png(page, [(255, 255, 255, 255)] * 4)

    report = module.review_visuals(tmp_path, image_inspection_available=True)

    assert report.findings
    assert all(finding.classification == "VISUAL_REVIEW" for finding in report.findings)
    assert all(finding.normative is False for finding in report.findings)


def test_blank_page_is_detected_by_raster_sanity_check(tmp_path: Path):
    module = _visual()
    blank = tmp_path / "blank.png"
    _png(blank, [(255, 255, 255, 255)] * 4)

    report = module.review_visuals(tmp_path, image_inspection_available=True)

    assert any(finding.code == "blank_page" for finding in report.findings)
