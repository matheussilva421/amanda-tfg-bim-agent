"""Render normalized canonical study plans as SVG and PNG previews.

These are two-dimensional planning schematics. The reference frame is not a
survey, and this script does not infer elevations, sections, roof geometry,
wall construction or openings.
"""

from __future__ import annotations

import csv
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from PIL import Image, ImageDraw, ImageFont

from amanda_agent.design.canonical_pavilion_layout import (
    CanonicalPavilionLayout,
    build_canonical_pavilion_layout,
)
from amanda_agent.design.canonical_reference import (
    CanonicalReferenceProfile,
)

OUT = REPOSITORY_ROOT / "docs" / "reports" / "study-drawings"
STUDY_DRAWINGS = (
    ("01-implantacao", "Implantação esquemática - base canônica normalizada"),
    ("02-planta-pavimento-01", "Planta esquemática - pavimento 01"),
    ("03-planta-pavimento-02", "Planta esquemática - pavimento 02"),
)
FONT_CANDIDATES = (
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
)
COMPONENT_FILL = {
    "ADMIN_ACOLHIMENTO": (198, 222, 244),
    "RES_PAV_A": (206, 232, 206),
    "RES_PAV_B": (206, 232, 206),
    "RES_PAV_C": (206, 232, 206),
    "RES_PAV_D_COMMUNAL": (222, 236, 206),
    "SERVICE_CAPACITATION": (232, 226, 198),
    "CHILD_SECTOR": (236, 214, 222),
}
EXTERNAL_FILL = (224, 241, 220)
GARDEN_FILL = (199, 230, 193)
CONNECTOR_FILL = (247, 227, 178)
OUTLINE = (68, 78, 86)
HIGHLIGHT = (159, 55, 45)


def font(size: int):
    for candidate in FONT_CANDIDATES:
        path = Path(candidate)
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _polygon_parts(geometry: Any) -> Iterable[Any]:
    if getattr(geometry, "geom_type", "") == "Polygon":
        yield geometry
    elif hasattr(geometry, "geoms"):
        for part in geometry.geoms:
            yield from _polygon_parts(part)


def _all_geometries(layout: CanonicalPavilionLayout) -> list[Any]:
    return (
        [block.footprint for block in layout.blocks]
        + [room.polygon for room in layout.rooms]
        + [space.polygon for space in layout.external_spaces]
        + [item.footprint for item in layout.covered_connectors]
    )


class Sheet:
    """Fixed pixel frame for normalized metric coordinates."""

    def __init__(
        self,
        name: str,
        title: str,
        bounds: tuple[float, float, float, float],
        width: int = 1500,
        height: int = 1050,
    ):
        self.name = name
        self.title = title
        self.width = width
        self.height = height
        minx, miny, maxx, maxy = bounds
        span_x = max(maxx - minx, 1.0)
        span_y = max(maxy - miny, 1.0)
        self.scale = min((width - 100) / span_x, (height - 150) / span_y)
        self.offsets = (minx - 40 / self.scale, miny - 80 / self.scale)
        self.image = Image.new("RGB", (width, height), (252, 252, 249))
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#fcfcf9"/>',
        ]

    def point(self, x: float, y: float) -> tuple[float, float]:
        ox, oy = self.offsets
        return ((x - ox) * self.scale, self.height - (y - oy) * self.scale)

    def polygon(
        self, geometry: Any, *, fill: tuple[int, int, int], outline=OUTLINE, width=2
    ):
        for polygon in _polygon_parts(geometry):
            pixels = [self.point(x, y) for x, y in polygon.exterior.coords]
            self.draw.polygon(pixels, fill=fill, outline=outline, width=width)
            points = " ".join(f"{x:.2f},{y:.2f}" for x, y in pixels)
            fill_hex = "".join(f"{channel:02x}" for channel in fill)
            outline_hex = "".join(f"{channel:02x}" for channel in outline)
            self.svg.append(
                f'<polygon points="{points}" fill="#{fill_hex}" stroke="#{outline_hex}" stroke-width="{width}"/>'
            )

    def outline(self, geometry: Any, *, colour=HIGHLIGHT, width=3):
        for polygon in _polygon_parts(geometry):
            pixels = [self.point(x, y) for x, y in polygon.exterior.coords]
            self.draw.line(pixels, fill=colour, width=width, joint="curve")
            points = " ".join(f"{x:.2f},{y:.2f}" for x, y in pixels)
            colour_hex = "".join(f"{channel:02x}" for channel in colour)
            self.svg.append(
                f'<polygon points="{points}" fill="none" stroke="#{colour_hex}" stroke-width="{width}"/>'
            )

    def text(self, x: float, y: float, message: str, *, size=12, fill=(25, 35, 45)):
        px, py = self.point(x, y)
        self.draw.text((px, py), message, font=font(size), anchor="mm", fill=fill)
        escaped = (
            message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        fill_hex = "".join(f"{channel:02x}" for channel in fill)
        self.svg.append(
            f'<text x="{px:.2f}" y="{py:.2f}" font-family="Segoe UI,Arial" font-size="{size}" text-anchor="middle" fill="#{fill_hex}">{escaped}</text>'
        )

    def finish(self, layout: CanonicalPavilionLayout, note: str):
        self.draw.text((22, 16), self.title, font=font(21), fill=(25, 35, 45))
        self.svg.append(
            '<text x="22" y="32" font-family="Segoe UI,Arial" font-size="21" fill="#19232d">{}</text>'.format(
                self.title.replace("&", "&amp;").replace("<", "&lt;")
            )
        )
        footer = f"ESTUDO NORMALIZADO - NÃO É LEVANTAMENTO - hash {layout.content_hash[:16]} - {note}"
        self.draw.text((16, self.height - 25), footer, font=font(12), fill=(90, 90, 90))
        self.svg.append(
            f'<text x="16" y="{self.height - 12}" font-family="Segoe UI,Arial" font-size="12" fill="#5a5a5a">{footer}</text>'
        )
        OUT.mkdir(parents=True, exist_ok=True)
        self.image.save(OUT / (self.name + ".png"))
        self.svg.append("</svg>")
        (OUT / (self.name + ".svg")).write_text("\n".join(self.svg), encoding="utf-8")


def _bounds(geometries: Iterable[Any]) -> tuple[float, float, float, float]:
    available = [
        geometry.bounds
        for geometry in geometries
        if geometry is not None and not geometry.is_empty
    ]
    if not available:
        raise ValueError("no geometry to render")
    return (
        min(item[0] for item in available),
        min(item[1] for item in available),
        max(item[2] for item in available),
        max(item[3] for item in available),
    )


def draw_implantation(layout: CanonicalPavilionLayout) -> Sheet:
    sheet = Sheet(
        "01-implantacao",
        "Implantação esquemática - pavilhões, jardim e percursos",
        _bounds(_all_geometries(layout)),
    )
    for space in layout.external_spaces:
        colour = (
            GARDEN_FILL if space.component_id == "PROTECTED_PATIO" else EXTERNAL_FILL
        )
        sheet.polygon(space.polygon, fill=colour, outline=(46, 125, 50), width=2)
        centre = space.polygon.centroid
        sheet.text(float(centre.x), float(centre.y), space.logical_id, size=10)
    for connector in layout.covered_connectors:
        sheet.polygon(
            connector.footprint, fill=CONNECTOR_FILL, outline=(138, 106, 26), width=1
        )
    for block in layout.blocks:
        sheet.polygon(block.footprint, fill=COMPONENT_FILL[block.component_id])
        centre = block.footprint.centroid
        sheet.text(float(centre.x), float(centre.y), block.component_id, size=11)
    sheet.finish(
        layout,
        "coordenadas normalizadas; sem divisas, norte ou recuos verificados",
    )
    return sheet


def draw_floor(layout: CanonicalPavilionLayout, level: int) -> Sheet:
    rooms = [room for room in layout.rooms if room.level == level]
    if not rooms:
        raise ValueError(f"no canonical rooms at level {level}")
    blocks = [block for block in layout.blocks if level in block.floor_footprints]
    geometries = [room.polygon for room in rooms] + [
        block.floor_footprints[level] for block in blocks
    ]
    if level == 1:
        geometries += [space.polygon for space in layout.external_spaces]
        geometries += [item.footprint for item in layout.covered_connectors]
    sheet = Sheet(
        "02-planta-pavimento-01" if level == 1 else "03-planta-pavimento-02",
        f"Planta esquemática - pavimento {level:02d}",
        _bounds(geometries),
    )
    if level == 1:
        for space in layout.external_spaces:
            colour = (
                GARDEN_FILL
                if space.component_id == "PROTECTED_PATIO"
                else EXTERNAL_FILL
            )
            sheet.polygon(space.polygon, fill=colour, outline=(46, 125, 50), width=1)
        for connector in layout.covered_connectors:
            sheet.polygon(
                connector.footprint,
                fill=CONNECTOR_FILL,
                outline=(138, 106, 26),
                width=1,
            )
    for room in rooms:
        sheet.polygon(
            room.polygon,
            fill=COMPONENT_FILL.get(room.component_id, (230, 230, 230)),
            width=1,
        )
        centre = room.polygon.centroid
        sheet.text(
            float(centre.x),
            float(centre.y),
            room.logical_id,
            size=8,
        )
    for block in blocks:
        sheet.outline(block.floor_footprints[level], width=2)
    sheet.finish(
        layout,
        f"pavimento {level:02d}; contornos de estudo sem paredes ou vãos",
    )
    return sheet


def write_tables(layout: CanonicalPavilionLayout, program: dict[str, Any]):
    OUT.mkdir(parents=True, exist_ok=True)
    schedule = OUT / "tabela-ambientes.csv"
    with schedule.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(
            [
                "ambiente",
                "setor",
                "componente",
                "pavimento",
                "area_liquida_m2",
                "acessivel",
            ]
        )
        for room in layout.rooms:
            writer.writerow(
                [
                    room.logical_id,
                    room.sector_id,
                    room.component_id,
                    room.level,
                    f"{room.net_area_m2:.2f}",
                    "sim" if room.accessible else "nao",
                ]
            )

    program["totals"]
    summary = OUT / "resumo-de-areas.md"
    lines = [
        "# Resumo de áreas - STUDY canônico",
        "",
        "Hash do layout: " + layout.content_hash,
        "",
        "Base de coordenadas: " + layout.coordinate_basis,
        "",
        "| grandeza | programa oficial | geometria deste estudo |",
        "| --- | --- | --- |",
        "| pessoas | 20 | 20 |",
        "| área útil interna | 626 m² | {:.2f} m² |".format(
            layout.accounting["net_internal_m2"]
        ),
        "| áreas externas programadas | 260 m² | {:.2f} m² |".format(
            layout.accounting["external_programmed_m2"]
        ),
        "| área fechada | 783–814 m² estimados | NÃO MEDIDA |",
        "| área coberta | 850–950 m² estimados | NÃO MEDIDA |",
        "",
        "O ajuste ao terreno está UNVERIFIED. As plantas não incluem divisas,",
        "norte, recuos, alturas, paredes ou aberturas. Não usar como prancha",
        "final nem como regressão visual aprovada.",
        "",
    ]
    summary.write_text("\n".join(lines), encoding="utf-8")
    scope = OUT / "escopo-do-estudo.md"
    scope.write_text(
        "# Escopo dos previews canônicos\n\n"
        "Inclui implantação esquemática e plantas normalizadas dos pavimentos "
        "01 e 02. Não há dados verificados para elevações, cortes, paredes, "
        "aberturas ou cobertura. O terreno ainda não foi levantado. As pranchas "
        "finais e os cortes/elevações devem vir do modelo Revit após a aceitação "
        "geométrica canônica e as regressões visuais obrigatórias.\n",
        encoding="utf-8",
    )
    return schedule, summary, scope


def main() -> int:
    program = json.loads(
        (REPOSITORY_ROOT / "project" / "requirements" / "program.json").read_text(
            encoding="utf-8"
        )
    )
    profile = CanonicalReferenceProfile.load(REPOSITORY_ROOT)
    layout = build_canonical_pavilion_layout(program, profile)
    OUT.mkdir(parents=True, exist_ok=True)
    draw_implantation(layout)
    draw_floor(layout, 1)
    draw_floor(layout, 2)
    outputs = write_tables(layout, program)
    print("layout hash:", layout.content_hash)
    print("canonical source hashes:", ", ".join(profile.source_hashes))
    print("png:", len(list(OUT.glob("*.png"))), "svg:", len(list(OUT.glob("*.svg"))))
    print("tables:", ", ".join(path.name for path in outputs))
    print("site fit:", layout.site_fit_status, "- vertical geometry not specified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
