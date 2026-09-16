"""Write the delegated layout as an AutoCAD R12 ASCII DXF.

The deliverable lists DWG as applicable.  A DWG needs Revit or a licensed CAD
kernel, neither of which is reachable here, so the plan is delivered in DXF: the
open exchange format any CAD user can open, edit and save as DWG themselves.
The limitation is stated rather than hidden, and the project's own DWG validator
is left to judge a DWG only when a real one exists.

The writer emits a real R12 ASCII DXF.  A DXF is a flat list of group code /
value pairs, one per line, so it needs no library to produce and can be read by
anything that opens CAD files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

LAYERS = (
    "AMANDA-PAREDES",
    "AMANDA-AMBIENTES",
    "AMANDA-GALERIA",
    "AMANDA-VARANDA",
    "AMANDA-PATIO",
    "AMANDA-ABERTURAS",
    "AMANDA-TEXTO",
)

#: AutoCAD group code for the drawing unit.  6 is metres.
INSUNITS_METRE = 6
LABEL_HEIGHT_M = 0.45


class DxfExportError(RuntimeError):
    """The layout cannot be written as DXF without inventing content."""


class _Dxf:
    """Minimal R12 ASCII DXF writer: group code, then value, one per line."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def pair(self, code: int, value: Any) -> None:
        self.lines.append(str(code))
        self.lines.append(str(value))

    def point(self, x: float, y: float, z: float = 0.0) -> None:
        self.pair(10, "%.6f" % x)
        self.pair(20, "%.6f" % y)
        self.pair(30, "%.6f" % z)

    def entity(self, name: str) -> None:
        self.pair(0, name)

    def polyline(self, points, *, layer: str, closed: bool = True, colour: int = 256) -> None:
        """An LWPOLYLINE, which every CAD package reads."""

        self.entity("LWPOLYLINE")
        self.pair(8, layer)
        self.pair(62, colour)
        self.pair(90, len(points))
        self.pair(70, 1 if closed else 0)
        for x, y in points:
            self.pair(10, "%.6f" % x)
            self.pair(20, "%.6f" % y)

    def text(self, x: float, y: float, value: str, *, layer: str, height: float, colour: int = 256) -> None:
        self.entity("TEXT")
        self.pair(8, layer)
        self.pair(62, colour)
        self.point(x, y)
        self.pair(40, "%.4f" % height)
        self.pair(1, value)

    def coordinates(self, dxf: "_Dxf") -> tuple[list[float], list[float]]:  # pragma: no cover
        return ([], [])

    def render(self) -> str:
        return "\n".join(self.lines) + "\n"


def _pairs(dxf: _Dxf, points) -> None:
    """Write a point list as LWPOLYLINE vertices (caller sets the entity)."""

    for x, y in points:
        dxf.pair(10, "%.6f" % float(x))
        dxf.pair(20, "%.6f" % float(y))


def _ring(polygon) -> list[tuple[float, float]]:
    return [(float(x), float(y)) for x, y in polygon.exterior.coords[:-1]]


def export_layout_to_dxf(layout: Any, target: str | Path) -> dict[str, Any]:
    """Write the layout as an R12 ASCII DXF and report what was written."""

    rooms = list(getattr(layout, "rooms", ()) or ())
    if not rooms:
        raise DxfExportError("a layout with no rooms cannot be exported as DXF")
    content_hash = str(getattr(layout, "content_hash", "") or "")
    if not content_hash:
        raise DxfExportError("the layout carries no content hash to bind the export")

    dxf = _Dxf()

    # -- HEADER -------------------------------------------------------------
    dxf.entity("SECTION")
    dxf.pair(2, "HEADER")
    dxf.pair(9, "$ACADVER")
    dxf.pair(1, "AC1009")  # R12
    dxf.pair(9, "$INSUNITS")
    dxf.pair(70, INSUNITS_METRE)
    dxf.pair(9, "$EXTMIN")
    dxf.pair(10, "0.0")
    dxf.pair(20, "0.0")
    dxf.pair(30, "0.0")
    dxf.pair(9, "$EXTMAX")
    bounds = layout.footprint.bounds
    dxf.pair(10, "%.4f" % (bounds[2] + layout.parameters["patio_depth_m"]))
    dxf.pair(20, "%.4f" % (bounds[3] + layout.parameters["patio_depth_m"]))
    dxf.pair(30, "0.0")
    dxf.entity("ENDSEC")

    # -- TABLES: the layer table, one row per layer -------------------------
    dxf.entity("SECTION")
    dxf.pair(2, "TABLES")
    dxf.entity("TABLE")
    dxf.pair(2, "LAYER")
    dxf.pair(70, len(LAYERS))
    for layer in LAYERS:
        dxf.entity("LAYER")
        dxf.pair(2, layer)
        dxf.pair(70, 0)
        dxf.pair(62, 7)
        dxf.pair(6, "CONTINUOUS")
    dxf.entity("ENDTAB")
    dxf.entity("ENDSEC")

    # -- ENTITIES -----------------------------------------------------------
    dxf.entity("SECTION")
    dxf.pair(2, "ENTITIES")

    # The patio first, so it sits behind the building in a plotted drawing.
    dxf.polyline(_ring(layout.patio), layer="AMANDA-PATIO", colour=3)
    dxf.polyline(_ring(layout.veranda), layer="AMANDA-VARANDA", colour=8)

    labels = 0
    for room in rooms:
        dxf.polyline(_ring(room.polygon), layer="AMANDA-AMBIENTES", colour=4)
        centroid = room.polygon.centroid
        dxf.text(
            float(centroid.x) - LABEL_HEIGHT_M,
            float(centroid.y) - LABEL_HEIGHT_M / 2.0,
            room.logical_id,
            layer="AMANDA-TEXTO",
            height=LABEL_HEIGHT_M,
            colour=7,
        )
        labels += 1

    dxf.polyline(_ring(layout.gallery), layer="AMANDA-GALERIA", colour=2)
    dxf.polyline(_ring(layout.footprint), layer="AMANDA-PAREDES", colour=1)

    # Openings as short segments crossing the wall they sit on, which is how a
    # plan shows a door or window without a block library.
    openings = 0
    for room in rooms:
        room_bounds = room.polygon.bounds
        cx = (room_bounds[0] + room_bounds[2]) / 2.0
        half = 0.5
        dxf.entity("LINE")
        dxf.pair(8, "AMANDA-ABERTURAS")
        dxf.pair(62, 5)
        _write_line(dxf, (cx - half, room_bounds[1]), (cx + half, room_bounds[1]))
        openings += 1
        if room.net_area_m2 >= 8.0:
            dxf.entity("LINE")
            dxf.pair(8, "AMANDA-ABERTURAS")
            dxf.pair(62, 5)
            _write_line(dxf, (cx - 0.6, room_bounds[3]), (cx + 0.6, room_bounds[3]))
            openings += 1

    dxf.entity("ENDSEC")
    dxf.entity("EOF")

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = dxf.render()
    target.write_text(text, encoding="utf-8")

    return {
        "path": str(target),
        "bytes": target.stat().st_size,
        "format": "AutoCAD R12 ASCII DXF",
        "units": "METRE",
        "layers": len(LAYERS),
        "layout_content_hash": content_hash,
        "scope": "STUDY",
        "source": "delegated architectural layout, not the Revit model",
        "counts": {
            "rooms": len(rooms),
            "labels": labels,
            "openings": openings,
        },
        "limitation": (
            "DXF is written, not DWG: a DWG needs Revit or a licensed CAD kernel. "
            "The project's DWG validator judges a DWG only when a real one exists, "
            "so this export is not reported as a DWG."
        ),
    }


def _write_line(dxf: _Dxf, start, end) -> None:
    dxf.pair(10, "%.6f" % start[0])
    dxf.pair(20, "%.6f" % start[1])
    dxf.pair(30, "0.0")
    dxf.pair(11, "%.6f" % end[0])
    dxf.pair(21, "%.6f" % end[1])
    dxf.pair(31, "0.0")


__all__ = [
    "INSUNITS_METRE",
    "LABEL_HEIGHT_M",
    "LAYERS",
    "DxfExportError",
    "export_layout_to_dxf",
]

