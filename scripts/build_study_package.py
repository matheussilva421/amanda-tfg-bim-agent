"""Assemble the normalized canonical STUDY previews into a draft PDF.

This package is explicitly not the final drawing set. It carries only the
implantation schematic and plan diagrams because verified elevations, sections,
construction geometry and site survey are not available yet.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter

SHEETS = REPOSITORY_ROOT / "docs" / "reports" / "study-drawings"
OUT = REPOSITORY_ROOT / "docs" / "reports" / "study-package"
PDF_PATH = OUT / "Amanda_TFG_ESTUDO_pranchas.pdf"
PREVIEW_DIR = OUT / "previews"
A1_W_PX = 9933
A1_H_PX = 7016
INK_THRESHOLD = 0.001

ORDER = (
    ("01-implantacao", "IMPLANTAÇÃO ESQUEMÁTICA - BASE CANÔNICA NORMALIZADA"),
    ("02-planta-pavimento-01", "PLANTA ESQUEMÁTICA - PAVIMENTO 01"),
    ("03-planta-pavimento-02", "PLANTA ESQUEMÁTICA - PAVIMENTO 02"),
)


def font(size: int):
    for candidate in (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"):
        path = Path(candidate)
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def compose_sheet(
    source: Path, title: str, index: int, total: int, layout_hash: str
) -> Image.Image:
    """Place one preview on an A1 study page with a clear draft label."""
    sheet = Image.new("RGB", (A1_W_PX, A1_H_PX), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    margin = 220
    block_h = 420
    draw_area_w = A1_W_PX - margin * 2
    draw_area_h = A1_H_PX - margin * 2 - block_h

    drawing = Image.open(source).convert("RGB")
    ratio = min(draw_area_w / drawing.width, draw_area_h / drawing.height)
    scaled = drawing.resize(
        (max(1, int(drawing.width * ratio)), max(1, int(drawing.height * ratio))),
        Image.LANCZOS,
    )
    sheet.paste(scaled, (margin, margin))

    top = A1_H_PX - margin - block_h
    draw.line([(margin, top), (A1_W_PX - margin, top)], fill=(40, 40, 40), width=6)
    draw.text((margin + 24, top + 40), title, font=font(120), fill=(20, 30, 40))
    draw.text(
        (margin + 24, top + 200),
        "AMANDA TFG - 20 PESSOAS - ESTUDO NORMALIZADO - NÃO FINAL",
        font=font(74),
        fill=(60, 60, 60),
    )
    draw.text(
        (margin + 24, top + 300),
        f"Hash do layout: {layout_hash[:16]}",
        font=font(62),
        fill=(90, 90, 90),
    )
    right = A1_W_PX - margin - 24
    draw.text(
        (right, top + 40),
        f"PREVIEW {index:02d}/{total:02d}",
        font=font(120),
        anchor="ra",
        fill=(20, 30, 40),
    )
    draw.text(
        (right, top + 200),
        "sem levantamento ou aceitação visual",
        font=font(74),
        anchor="ra",
        fill=(60, 60, 60),
    )
    draw.text(
        (right, top + 300),
        "A1 - 841 x 594 mm",
        font=font(62),
        anchor="ra",
        fill=(90, 90, 90),
    )
    return sheet


def ink_fraction(image: Image.Image) -> float:
    grey = image.convert("L").resize((600, 424))
    pixels = list(grey.getdata())
    inked = sum(1 for value in pixels if value < 245)
    return inked / max(len(pixels), 1)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    qa_path = REPOSITORY_ROOT / "docs" / "reports" / "p08-layout-qa.json"
    manifest_source = json.loads(qa_path.read_text(encoding="utf-8"))
    if (
        manifest_source.get("stage") != "CANONICAL_PRE_MODEL"
        or len(manifest_source.get("canonical_source_hashes", [])) != 4
    ):
        print(
            "refusing: QA report is stale or not bound to canonical references",
            file=sys.stderr,
        )
        return 2
    if manifest_source.get("verdict") == "FAIL":
        print("refusing: canonical pre-model QA has failures", file=sys.stderr)
        return 3

    layout_hash = manifest_source["layout_content_hash"]
    missing = [name for name, _ in ORDER if not (SHEETS / (name + ".png")).is_file()]
    if missing:
        print("refusing: study previews missing:", ", ".join(missing), file=sys.stderr)
        return 2

    writer = PdfWriter()
    pages = []
    total = len(ORDER)
    for index, (name, title) in enumerate(ORDER, start=1):
        page = compose_sheet(SHEETS / (name + ".png"), title, index, total, layout_hash)
        page_path = PREVIEW_DIR / f"page-{index:02d}.png"
        page.save(page_path, optimize=True)
        fraction = ink_fraction(page)
        import io

        buffer = io.BytesIO()
        page.save(buffer, format="PDF", resolution=300.0)
        buffer.seek(0)
        for pdf_page in PdfReader(buffer).pages:
            writer.add_page(pdf_page)
        pages.append(
            {
                "sheet": name,
                "title": title,
                "preview": str(page_path.relative_to(OUT).as_posix()),
                "preview_px": list(page.size),
                "ink_fraction": round(fraction, 4),
                "nonblank": fraction >= INK_THRESHOLD,
            }
        )
        status = "OK" if fraction >= INK_THRESHOLD else "BLANK"
        print(f"page {index:02d} {name:<28} ink={fraction:.4f} {status}")

    blank = [page for page in pages if not page["nonblank"]]
    if blank:
        print(
            "refusing to package blank previews:",
            ", ".join(item["sheet"] for item in blank),
            file=sys.stderr,
        )
        return 3

    with PDF_PATH.open("wb") as handle:
        writer.write(handle)
    reader = PdfReader(str(PDF_PATH))
    blocked = manifest_source.get("verdict") == "BLOCKED"
    report = {
        "schema_version": 2,
        "scope": "STUDY",
        "delivery_status": "DRAFT_GATES_BLOCKED" if blocked else "STUDY_PREVIEW",
        "qa_verdict": manifest_source["verdict"],
        "layout_content_hash": layout_hash,
        "canonical_source_hashes": manifest_source["canonical_source_hashes"],
        "coordinate_basis": manifest_source.get("coordinate_basis"),
        "pdf": PDF_PATH.name,
        "pdf_bytes": PDF_PATH.stat().st_size,
        "page_count": len(reader.pages),
        "expected_page_count": total,
        "pages": pages,
        "all_blank_check": "PASS",
        "not_final": True,
    }
    (OUT / "package-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        "pdf:",
        PDF_PATH.name,
        PDF_PATH.stat().st_size,
        "bytes,",
        len(reader.pages),
        "pages",
    )
    print("previews:", len(pages), "QA:", report["qa_verdict"])
    print("delivery status:", report["delivery_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
