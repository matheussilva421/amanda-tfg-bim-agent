"""Render the STUDY drawing set from the verified layout geometry.

Everything here is derived from the same content-hashed plan the BIM driver
compiles, so a drawing and a model stage can never disagree about the
architecture.  The set is a study set: it is drawn from the delegated layout and
a study boundary, and it says so on every sheet.

Sheets produced: implantation, ground floor plan, four elevations, one section,
plus the room schedule and the area summary as tables.

Outputs are SVG (vector, for the deliverable) and PNG (for review), and every
sheet carries the layout content hash so a drawing can be traced to its plan.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from amanda_agent.design.architectural_layout import build_courtyard_layout  # noqa: E402
from amanda_agent.production.layout_bim import FLOOR_HEIGHT_M  # noqa: E402

OUT = REPOSITORY_ROOT / "docs" / "reports" / "study-drawings"
BOUNDARY_M = 155.3544334739115  # the equal-area study square of site-v1
FONT_CANDIDATES = (
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
)

SECTOR_FILL = {
    "SEC-01": (198, 222, 244),
    "SEC-02": (206, 232, 206),
    "SEC-03": (222, 236, 206),
    "SEC-04": (232, 226, 198),
    "SEC-05": (236, 214, 222),
    "SEC-06": (226, 226, 226),
}
GALLERY_FILL = (247, 227, 178)
VERANDA_FILL = (238, 236, 226)
PATIO_FILL = (233, 245, 233)
PLATE_LINE = (60, 60, 60)
HIGHLIGHT = (192, 57, 43)


def font(size: int):
    for candidate in FONT_CANDIDATES:
        path = Path(candidate)
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _ring(polygon):
    return [(float(x), float(y)) for x, y in polygon.exterior.coords]


def _hex(rgb):
    return "#%02x%02x%02x" % rgb


class Sheet:
    """One drawing sheet with a fixed frame, a title and a title block."""

    def __init__(self, name: str, title: str, width: int, height: int, scale: float, offsets=(0.0, 0.0)):
        self.name = name
        self.title = title
        self.width = width
        self.height = height
        self.scale = scale
        self.offsets = offsets
        self.image = Image.new("RGB", (width, height), (252, 252, 249))
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
            % (width, height, width, height),
            '<rect width="100%" height="100%" fill="#fcfcf9"/>',
        ]

    def point(self, x: float, y: float):
        """Model metres with y up, to sheet pixels with y down."""

        ox, oy = self.offsets
        return ((x - ox) * self.scale, self.height - (y - oy) * self.scale)

    def polygon(self, points, *, fill=None, outline=None, width=1):
        pixels = [self.point(x, y) for x, y in points]
        self.draw.polygon(pixels, fill=fill, outline=outline, width=width)
        self.svg.append(
            '<polygon points="%s" fill="%s" stroke="%s" stroke-width="%d"/>'
            % (
                " ".join("%.2f,%.2f" % p for p in pixels),
                _hex(fill) if fill else "none",
                _hex(outline) if outline else "none",
                width,
            )
        )

    def line(self, first, second, *, fill=(40, 40, 40), width=1, dash=False):
        a = self.point(*first)
        b = self.point(*second)
        self.draw.line([a, b], fill=fill, width=width)
        self.svg.append(
            '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%d"%s/>'
            % (a[0], a[1], b[0], b[1], _hex(fill), width,
               ' stroke-dasharray="6 4"' if dash else "")
        )

    def text(self, x: float, y: float, message: str, *, size=13, anchor="mm", fill=(25, 35, 45)):
        px, py = self.point(x, y)
        self.draw.text((px, py), message, font=font(size), anchor=anchor, fill=fill)
        self.svg.append(
            '<text x="%.2f" y="%.2f" font-family="Segoe UI,Arial" font-size="%d" '
            'text-anchor="%s" fill="%s">%s</text>'
            % (px, py, size,
               {"mm": "middle", "lm": "start", "rm": "end"}.get(anchor, "middle"),
               _hex(fill),
               message.replace("&", "&amp;").replace("<", "&lt;"))
        )

    def finish(self, layout, note: str):
        self.text(
            (self.offsets[0] + 1.0),
            (self.height / self.scale) + self.offsets[1] - 1.4,
            self.title,
            size=19,
            anchor="lm",
        )
        footer = "STUDY - delegated layout - hash %s - %s" % (layout.content_hash[:16], note)
        px, py = (12, self.height - 22)
        self.draw.text((px, py), footer, font=font(12), fill=(90, 90, 90))
        self.svg.append(
            '<text x="%d" y="%d" font-family="Segoe UI,Arial" font-size="12" fill="#5a5a5a">%s</text>'
            % (px, py, footer)
        )
        self.image.save(OUT / (self.name + ".png"))
        self.svg.append("</svg>")
        (OUT / (self.name + ".svg")).write_text("\n".join(self.svg), encoding="utf-8")


def draw_implantation(layout):
    pad = 10.0
    total = BOUNDARY_M + pad * 2
    scale = 1450 / total
    sheet = Sheet(
        "01-implantacao",
        "Implantação sobre divisa de estudo - recuos de 5,00 m",
        1450,
        int(total * scale),
        scale,
        offsets=(-pad, -pad),
    )
    sheet.polygon(
        [(0.0, 0.0), (BOUNDARY_M, 0.0), (BOUNDARY_M, BOUNDARY_M), (0.0, BOUNDARY_M)],
        fill=(247, 247, 242),
        outline=(120, 120, 120),
        width=2,
    )
    sheet.polygon(_ring(layout.patio), fill=PATIO_FILL, outline=(46, 125, 50), width=2)
    sheet.polygon(_ring(layout.veranda), fill=VERANDA_FILL, outline=(150, 148, 138), width=1)
    sheet.polygon(_ring(layout.footprint), fill=(214, 214, 208), outline=HIGHLIGHT, width=3)
    sheet.polygon(_ring(layout.gallery), fill=GALLERY_FILL, outline=(138, 106, 26), width=1)
    bounds = layout.footprint.bounds
    sheet.text((bounds[0] + bounds[2]) / 2, bounds[3] + 9, "BLOCO PRINCIPAL - pavimento térreo", size=15)
    sheet.text((bounds[0] + bounds[2]) / 2, bounds[1] - 7, "face da rua - serviços, chegada e uso comunitário", size=12)
    sheet.text((bounds[0] + bounds[2]) / 2, layout.patio.bounds[1] + layout.accounting["patio_m2"] * 0 + 16, "pátio protegido %.0f m2" % layout.accounting["patio_m2"], size=13)
    sheet.text(3.0, 3.0, "divisa de estudo: 24.135 m2 (não verificada)", size=11, anchor="lm")
    sheet.text(3.0, BOUNDARY_M - 4.0, "quadrado de área equivalente - sem polígono cadastral", size=11, anchor="lm")
    sheet.finish(layout, "implantação sobre base de estudo; recuos de 5,00 m")
    return sheet


def draw_ground_floor(layout):
    bounds = layout.footprint.bounds
    margin = 7.0
    x0, y0 = bounds[0] - margin, bounds[1] - margin
    x1 = bounds[2] + margin
    y1 = bounds[3] + layout.parameters["patio_depth_m"] + margin
    scale = 1450 / (x1 - x0)
    height = int((y1 - y0) * scale) + 44
    sheet = Sheet(
        "02-planta-terreo",
        "Planta baixa - pavimento térreo - ambientes e áreas líquidas",
        1450,
        height,
        scale,
        offsets=(x0, y0),
    )
    sheet.polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill=(250, 250, 246), outline=(206, 206, 200))
    sheet.polygon(_ring(layout.patio), fill=PATIO_FILL, outline=(46, 125, 50), width=2)
    sheet.polygon(_ring(layout.veranda), fill=VERANDA_FILL, outline=(150, 148, 138), width=1)
    for room in layout.rooms:
        sheet.polygon(
            _ring(room.polygon),
            fill=SECTOR_FILL.get(room.sector_id, (230, 230, 230)),
            outline=(96, 106, 116),
            width=1,
        )
    sheet.polygon(_ring(layout.gallery), fill=GALLERY_FILL, outline=(138, 106, 26), width=2)
    sheet.polygon(_ring(layout.footprint), fill=None, outline=HIGHLIGHT, width=3)

    seen = {}
    for room in layout.rooms:
        entry = seen.setdefault(room.sector_id, [0.0, 0.0, 0])
        entry[0] += room.polygon.centroid.x
        entry[1] += room.polygon.centroid.y
        entry[2] += 1
    for sector_id, (sx, sy, n) in sorted(seen.items()):
        sheet.text(sx / n, sy / n, sector_id, size=15)

    sheet.text((bounds[0] + bounds[2]) / 2, y0 + 2.0, "face da rua - chegada, serviços e uso comunitário", size=11, anchor="lm")
    sheet.text((bounds[0] + bounds[2]) / 2, bounds[3] + layout.parameters["veranda_depth_m"] * 0.5, "varanda coberta - %.2f m de profundidade" % layout.parameters["veranda_depth_m"], size=11, anchor="lm")
    sheet.text((bounds[0] + bounds[2]) / 2, layout.patio.bounds[3] - 3.0, "pátio protegido - %.0f m2" % layout.accounting["patio_m2"], size=13)
    sheet.text(layout.gallery.bounds[0] + 5.0, layout.gallery.centroid.y, "galeria %.2f m" % layout.corridor_width_m, size=11, anchor="lm")
    sheet.text(x1 - 2.0, y0 + 2.0, "%d ambientes | %.2f m2 úteis | %.2f m2 fechados" % (len(layout.rooms), layout.accounting["net_internal_m2"], layout.accounting["gross_enclosed_m2"]), size=12, anchor="rm")
    sheet.finish(layout, "áreas líquidas exatas por ambiente; nenhuma área foi ajustada")
    return sheet


def _elevation_marks(layout, side):
    """Openings visible on one elevation, taken from the real plan."""

    marks = []
    for room in layout.rooms:
        if room.net_area_m2 < 8.0:
            continue
        along = room.polygon.bounds[1] if side else room.polygon.bounds[0]
        span = room.depth_m if side else room.length_m
        marks.append((along + span / 2.0, span))
    marks.sort()
    return marks


def draw_elevation(layout, name, title, *, side=False):
    bounds = layout.footprint.bounds
    width_m = (bounds[3] - bounds[1]) if side else (bounds[2] - bounds[0])
    height_m = FLOOR_HEIGHT_M
    pad = 3.0
    total_w = width_m + pad * 2
    total_h = height_m + pad * 3.6
    scale = 1400 / total_w
    sheet = Sheet(name, title, 1400, int(total_h * scale), scale, offsets=(-pad, -pad))
    sheet.line((0.0, 0.0), (width_m, 0.0), fill=(90, 90, 90), width=3)
    sheet.line((0.0, height_m), (width_m, height_m), fill=HIGHLIGHT, width=3)
    for mark in _elevation_marks(layout, side):
        pass
    x = 0.0
    for centre, span in _elevation_marks(layout, side):
        left = min(x, width_m - 1.4)
        right = min(left + 1.2, width_m)
        if right - left > 0.2:
            sheet.polygon(
                [(left, 0.9), (right, 0.9), (right, 2.1), (left, 2.1)],
                fill=(198, 222, 244),
                outline=(60, 90, 120),
                width=1,
            )
        x += span
    sheet.text(width_m / 2, height_m + 1.3, "cobertura plana - laje sobre o bloco e a varanda", size=12)
    sheet.text(width_m / 2, -1.6, "extensão %.2f m | pé-direito %.2f m | nível 0,00 = datum local" % (width_m, height_m), size=12)
    sheet.finish(layout, "elevação derivada da planta; altura de piso %.2f m" % height_m)
    return sheet


def draw_section(layout):
    band = layout.parameters["band_depth_m"]
    corridor = layout.parameters["corridor_width_m"]
    veranda = layout.parameters["veranda_depth_m"]
    total_depth = band * 2 + corridor + veranda
    height_m = FLOOR_HEIGHT_M
    pad = 2.5
    scale = 980 / (total_depth + pad * 2)
    sheet = Sheet(
        "07-corte-transversal",
        "Corte transversal AA - bloco, galeria e varanda",
        980,
        int((height_m + pad * 3.2) * scale),
        scale,
        offsets=(-pad, -pad),
    )
    blocks = [
        ("residencial e atendimento", band, (206, 232, 206)),
        ("galeria coberta", corridor, GALLERY_FILL),
        ("serviços e uso comunitário", band, (198, 222, 244)),
        ("varanda coberta", veranda, VERANDA_FILL),
    ]
    y = 0.0
    for label, depth, fill in blocks:
        sheet.polygon(
            [(y, 0.0), (y + depth, 0.0), (y + depth, height_m), (y, height_m)],
            fill=fill,
            outline=(96, 106, 116),
            width=1,
        )
        sheet.text(y + depth / 2, height_m / 2, label, size=10)
        y += depth
    sheet.line((0.0, 0.0), (y, 0.0), fill=(90, 90, 90), width=3)
    sheet.line((0.0, height_m), (y, height_m), fill=HIGHLIGHT, width=3)
    sheet.text(y / 2, -1.4, "corte na menor dimensão do bloco | pé-direito %.2f m | base de estudo" % height_m, size=11)
    sheet.finish(layout, "corte derivado da planta; profundidade total %.2f m" % y)
    return sheet


def write_tables(layout):
    schedule = OUT / "tabela-ambientes.csv"
    with schedule.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["ambiente", "setor", "face", "area_liquida_m2", "nivel_privacidade", "acessivel"])
        for room in layout.rooms:
            writer.writerow([
                room.logical_id,
                room.sector_id,
                room.face,
                "%.2f" % room.net_area_m2,
                room.privacy_level,
                "sim" if room.accessible else "nao",
            ])
    summary = OUT / "resumo-de-areas.md"
    a = layout.accounting
    lines = [
        "# Resumo de áreas - STUDY",
        "",
        "Derivado de src/amanda_agent/design/architectural_layout.py.",
        "",
        "Hash de conteúdo: " + layout.content_hash,
        "",
        "| grandeza | medido | estimativa do programa |",
        "| --- | --- | --- |",
        "| área útil interna | %.2f m2 | 626 m2 |" % a["net_internal_m2"],
        "| área construída fechada | %.2f m2 | 783-814 m2 |" % a["gross_enclosed_m2"],
        "| varanda coberta | %.2f m2 | parte da área coberta |" % a["veranda_m2"],
        "| área coberta total | %.2f m2 | 850-950 m2 |" % a["covered_total_m2"],
        "| circulação (galeria) | %.2f m2 | - |" % a["circulation_m2"],
        "| divisórias | %.2f m2 | - |" % a["partitions_m2"],
        "| pátio protegido | %.2f m2 | 80 m2 de área externa protegida |" % a["patio_m2"],
        "| projeção até a face externa | %.2f m2 | - |" % a["construction_footprint_m2"],
        "",
        "Capacidade do programa: 20 pessoas. Ambientes colocados: %d." % len(layout.rooms),
        "",
        "O pátio e a varanda são espaços externos: não entram na área construída",
        "fechada, e a varanda entra na área coberta porque é coberta.",
        "",
        "Base de estudo: a divisa é um quadrado de área equivalente, não um",
        "polígono cadastral; o pátio é fechado pela parede de divisa como",
        "PROVISIONAL_ASSUMPTION.",
        "",
    ]
    summary.write_text("\n".join(lines), encoding="utf-8")
    return schedule, summary


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    program = json.loads(
        (REPOSITORY_ROOT / "project" / "requirements" / "program.json").read_text(encoding="utf-8")
    )
    layout = build_courtyard_layout(program)
    print("layout hash:", layout.content_hash)
    draw_implantation(layout)
    draw_ground_floor(layout)
    draw_elevation(layout, "03-elevacao-sul", "Elevação sul - face da rua", side=False)
    draw_elevation(layout, "04-elevacao-norte", "Elevação norte - face do pátio", side=False)
    draw_elevation(layout, "05-elevacao-oeste", "Elevação oeste - empena", side=True)
    draw_elevation(layout, "06-elevacao-leste", "Elevação leste - empena", side=True)
    draw_section(layout)
    schedule, summary = write_tables(layout)
    print("png:", len(list(OUT.glob("*.png"))), "svg:", len(list(OUT.glob("*.svg"))))
    print("tables:", schedule.name, "/", summary.name)
    print("enclosed %.2f  covered %.2f" % (layout.accounting["gross_enclosed_m2"], layout.accounting["covered_total_m2"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

