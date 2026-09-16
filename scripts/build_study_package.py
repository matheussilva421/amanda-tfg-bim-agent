"""Assemble the STUDY sheet package as a single PDF, with real page previews.

The deliverable asks for PDF and previews.  This builds them from the sheets
scripts/render_study_sheets.py already produced, so the PDF and the SVG/PNG set
can never drift apart, and it validates what it wrote rather than assuming.

The sheet size is A1 landscape at 300 dpi for the drawings, and each page is
checked for ink: a blank page is a failed page, not a small one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from pypdf import PdfReader, PdfWriter  # noqa: E402

SHEETS = REPOSITORY_ROOT / "docs" / "reports" / "study-drawings"
OUT = REPOSITORY_ROOT / "docs" / "reports" / "study-package"
PDF_PATH = OUT / "Amanda_TFG_ESTUDO_pranchas.pdf"
PREVIEW_DIR = OUT / "previews"

#: A1 landscape at 300 dpi, which is the usual architectural sheet size here.
A1_W_PX = 9933
A1_H_PX = 7016
PREVIEW_W = 1400
INK_THRESHOLD = 0.001  # any page with less than this fraction of non-white ink fails

ORDER = (
    ("01-implantacao", "IMPLANTAÇÃO - divisa de estudo, recuos de 5,00 m"),
    ("02-planta-terreo", "PLANTA BAIXA - pavimento térreo"),
    ("03-elevacao-sul", "ELEVAÇÃO SUL - face da rua"),
    ("04-elevacao-norte", "ELEVAÇÃO NORTE - face do pátio"),
    ("05-elevacao-oeste", "ELEVAÇÃO OESTE - empena"),
    ("06-elevacao-leste", "ELEVAÇÃO LESTE - empena"),
    ("07-corte-transversal", "CORTE TRANSVERSAL AA"),
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


def compose_sheet(source: Path, title: str, index: int, total: int, layout_hash: str) -> Image.Image:
    """Place one drawing on an A1 sheet with a title block."""

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

    # Title block along the bottom, separated by a rule.
    top = A1_H_PX - margin - block_h
    draw.line([(margin, top), (A1_W_PX - margin, top)], fill=(40, 40, 40), width=6)
    draw.text((margin + 24, top + 40), title, font=font(120), fill=(20, 30, 40))
    draw.text(
        (margin + 24, top + 200),
        "AMANDA TFG - CENTRO DE ACOLHIMENTO TEMPORÁRIO - 20 PESSOAS",
        font=font(74),
        fill=(60, 60, 60),
    )
    draw.text(
        (margin + 24, top + 300),
        "ESTUDO - layout delegado - hash %s" % layout_hash[:16],
        font=font(62),
        fill=(90, 90, 90),
    )
    right = A1_W_PX - margin - 24
    draw.text((right, top + 40), "PRANCHA %02d/%02d" % (index, total), font=font(120), anchor="ra", fill=(20, 30, 40))
    draw.text((right, top + 200), "esc. variável", font=font(74), anchor="ra", fill=(60, 60, 60))
    draw.text((right, top + 300), "A1 - 841 x 594 mm", font=font(62), anchor="ra", fill=(90, 90, 90))
    return sheet


def ink_fraction(image: Image.Image) -> float:
    """Fraction of pixels that are not near-white, as a blank-page guard."""

    grey = image.convert("L").resize((600, 424))
    pixels = list(grey.getdata())
    inked = sum(1 for value in pixels if value < 245)
    return inked / max(len(pixels), 1)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    manifest_source = json.loads(
        (REPOSITORY_ROOT / "docs" / "reports" / "p08-layout-qa.json").read_text(encoding="utf-8")
    )
    layout_hash = manifest_source["layout_content_hash"]

    missing = [name for name, _ in ORDER if not (SHEETS / (name + ".png")).is_file()]
    if missing:
        print("refusing: sheets missing:", ", ".join(missing), file=sys.stderr)
        return 2

    writer = PdfWriter()
    pages = []
    total = len(ORDER)
    for index, (name, title) in enumerate(ORDER, start=1):
        page = compose_sheet(SHEETS / (name + ".png"), title, index, total, layout_hash)
        page_path = PREVIEW_DIR / ("page-%02d.png" % index)
        page.save(page_path, optimize=True)
        fraction = ink_fraction(page)
        printable = page.convert("RGB")
        # pypdf writes the composed sheet as a single full-page image, so the
        # PDF carries exactly what was previewed.
        import io

        buffer = io.BytesIO()
        printable.save(buffer, format="PDF", resolution=300.0)
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
        print("page %02d %-24s ink=%.4f %s" % (index, name, fraction, "OK" if fraction >= INK_THRESHOLD else "BLANK"))

    blank = [page for page in pages if not page["nonblank"]]
    if blank:
        print("refusing to publish: blank pages:", ", ".join(p["sheet"] for p in blank), file=sys.stderr)
        return 3

    with PDF_PATH.open("wb") as handle:
        writer.write(handle)

    reader = PdfReader(str(PDF_PATH))
    report = {
        "schema_version": 1,
        "scope": "STUDY",
        "layout_content_hash": layout_hash,
        "pdf": PDF_PATH.name,
        "pdf_bytes": PDF_PATH.stat().st_size,
        "page_count": len(reader.pages),
        "expected_page_count": total,
        "pages": pages,
        "all_blank_check": "PASS" if not blank else "FAIL",
    }
    (OUT / "package-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print()
    print("pdf:", PDF_PATH.name, PDF_PATH.stat().st_size, "bytes,", len(reader.pages), "pages")
    print("previews:", len(pages))
    print("blank check:", report["all_blank_check"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

