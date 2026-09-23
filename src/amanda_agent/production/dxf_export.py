"""Write a 2D R12 DXF study of canonical pavilion geometry.

Rooms, separate blocks, programmed exterior areas and covered connectors are
preserved as outlines. The normalized study frame contains no inferred walls,
openings, elevations, or DWG claims.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

LAYERS = (
    "AMANDA-BLOCOS",
    "AMANDA-INTERIORES-P01",
    "AMANDA-INTERIORES-P02",
    "AMANDA-AREAS-EXTERNAS",
    "AMANDA-PERCURSOS-COBERTOS",
    "AMANDA-IDENTIFICACAO",
)
INSUNITS_METRE = 6
LABEL_HEIGHT_M = 0.45
COORDINATE_BASIS = "NORMALIZED_METRIC_REFERENCE_NOT_SURVEY"


class DxfExportError(RuntimeError):
    """The layout cannot be exported without inventing geometry."""


class _Dxf:
    """Minimal R12 ASCII DXF writer."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def pair(self, code: int, value: Any) -> None:
        self.lines.extend((str(code), str(value)))

    def point(self, x: float, y: float, z: float = 0.0) -> None:
        self.pair(10, f"{x:.6f}")
        self.pair(20, f"{y:.6f}")
        self.pair(30, f"{z:.6f}")

    def entity(self, name: str) -> None:
        self.pair(0, name)

    def polyline(self, points, *, layer: str, colour: int = 256) -> None:
        self.entity("LWPOLYLINE")
        self.pair(8, layer)
        self.pair(62, colour)
        self.pair(90, len(points))
        self.pair(70, 1)
        for x, y in points:
            self.pair(10, f"{float(x):.6f}")
            self.pair(20, f"{float(y):.6f}")

    def text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        layer: str,
        height: float = LABEL_HEIGHT_M,
        colour: int = 256,
    ) -> None:
        self.entity("TEXT")
        self.pair(8, layer)
        self.pair(62, colour)
        self.point(x, y)
        self.pair(40, f"{height:.4f}")
        self.pair(1, value)

    def render(self) -> str:
        return "\n".join(self.lines) + "\n"


def _rings(geometry: Any) -> Iterator[list[tuple[float, float]]]:
    geometry_type = getattr(geometry, "geom_type", "")
    if geometry_type == "Polygon":
        yield [(float(x), float(y)) for x, y in geometry.exterior.coords[:-1]]
        for interior in geometry.interiors:
            yield [(float(x), float(y)) for x, y in interior.coords[:-1]]
    elif hasattr(geometry, "geoms"):
        for part in geometry.geoms:
            yield from _rings(part)
    else:
        raise DxfExportError(f"unsupported study geometry: {geometry_type}")


def _bounds(geometries: list[Any]) -> tuple[float, float, float, float]:
    usable = [
        item.bounds for item in geometries if item is not None and not item.is_empty
    ]
    if not usable:
        raise DxfExportError("layout carries no geometry")
    return (
        min(item[0] for item in usable),
        min(item[1] for item in usable),
        max(item[2] for item in usable),
        max(item[3] for item in usable),
    )


def _write_geometry(dxf: _Dxf, geometry: Any, *, layer: str, colour: int) -> int:
    count = 0
    for ring in _rings(geometry):
        if len(ring) < 3:
            continue
        dxf.polyline(ring, layer=layer, colour=colour)
        count += 1
    return count


def export_layout_to_dxf(layout: Any, target: str | Path) -> dict[str, Any]:
    """Write canonical room and site-program outlines as an R12 study DXF."""
    rooms = list(getattr(layout, "rooms", ()) or ())
    blocks = list(getattr(layout, "blocks", ()) or ())
    external_spaces = list(getattr(layout, "external_spaces", ()) or ())
    connectors = list(getattr(layout, "covered_connectors", ()) or ())
    content_hash = str(getattr(layout, "content_hash", "") or "")
    coordinate_basis = str(getattr(layout, "coordinate_basis", "") or "")
    if not rooms or not blocks or not external_spaces or not connectors:
        raise DxfExportError(
            "canonical rooms, blocks, exterior spaces and paths are required"
        )
    if not content_hash:
        raise DxfExportError("the layout carries no content hash to bind the export")
    if coordinate_basis != COORDINATE_BASIS:
        raise DxfExportError("canonical normalized metric geometry is required")

    geometries = (
        [block.footprint for block in blocks]
        + [room.polygon for room in rooms]
        + [space.polygon for space in external_spaces]
        + [item.footprint for item in connectors]
    )
    minx, miny, maxx, maxy = _bounds(geometries)

    dxf = _Dxf()
    dxf.entity("SECTION")
    dxf.pair(2, "HEADER")
    dxf.pair(9, "$ACADVER")
    dxf.pair(1, "AC1009")
    dxf.pair(9, "$INSUNITS")
    dxf.pair(70, INSUNITS_METRE)
    dxf.pair(9, "$EXTMIN")
    dxf.pair(10, f"{minx:.4f}")
    dxf.pair(20, f"{miny:.4f}")
    dxf.pair(30, "0.0")
    dxf.pair(9, "$EXTMAX")
    dxf.pair(10, f"{maxx:.4f}")
    dxf.pair(20, f"{maxy:.4f}")
    dxf.pair(30, "0.0")
    dxf.entity("ENDSEC")

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

    dxf.entity("SECTION")
    dxf.pair(2, "ENTITIES")
    block_rings = 0
    for block in blocks:
        block_rings += _write_geometry(
            dxf, block.footprint, layer="AMANDA-BLOCOS", colour=1
        )
        centre = block.footprint.centroid
        dxf.text(
            float(centre.x),
            float(centre.y),
            block.component_id,
            layer="AMANDA-IDENTIFICACAO",
        )

    for room in rooms:
        level_layer = {
            1: "AMANDA-INTERIORES-P01",
            2: "AMANDA-INTERIORES-P02",
        }.get(int(room.level))
        if level_layer is None:
            raise DxfExportError(f"unsupported room level: {room.level}")
        _write_geometry(dxf, room.polygon, layer=level_layer, colour=4)
        centre = room.polygon.centroid
        dxf.text(
            float(centre.x),
            float(centre.y),
            room.logical_id,
            layer="AMANDA-IDENTIFICACAO",
        )

    for space in external_spaces:
        _write_geometry(dxf, space.polygon, layer="AMANDA-AREAS-EXTERNAS", colour=3)
        centre = space.polygon.centroid
        dxf.text(
            float(centre.x),
            float(centre.y),
            space.logical_id,
            layer="AMANDA-IDENTIFICACAO",
        )

    for connector in connectors:
        _write_geometry(
            dxf,
            connector.footprint,
            layer="AMANDA-PERCURSOS-COBERTOS",
            colour=2,
        )
        centre = connector.footprint.centroid
        dxf.text(
            float(centre.x),
            float(centre.y),
            connector.connector_id,
            layer="AMANDA-IDENTIFICACAO",
        )

    dxf.text(
        minx,
        miny,
        "geometry=2d-study-only; coordinates=normalized-not-survey",
        layer="AMANDA-IDENTIFICACAO",
        height=0.6,
    )
    dxf.entity("ENDSEC")
    dxf.entity("EOF")

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dxf.render(), encoding="utf-8")
    labels = len(blocks) + len(rooms) + len(external_spaces) + len(connectors) + 1
    return {
        "path": str(target),
        "bytes": target.stat().st_size,
        "format": "AutoCAD R12 ASCII DXF",
        "units": "METRE",
        "layers": len(LAYERS),
        "layout_content_hash": content_hash,
        "coordinate_basis": coordinate_basis,
        "scope": "STUDY",
        "geometry_scope": "2D normalized study outlines; no vertical or construction geometry",
        "source": "canonical pavilion layout, not the verified Revit model",
        "counts": {
            "rooms": len(rooms),
            "blocks": len(blocks),
            "block_rings": block_rings,
            "external_spaces": len(external_spaces),
            "covered_connectors": len(connectors),
            "labels": labels,
        },
        "limitation": (
            "This is a 2D study DXF, not a final model export or DWG. "
            "The final IFC/PDF/DWG deliverables must be regenerated from the "
            "accepted and independently verified Revit model."
        ),
    }


__all__ = [
    "COORDINATE_BASIS",
    "INSUNITS_METRE",
    "LABEL_HEIGHT_M",
    "LAYERS",
    "DxfExportError",
    "export_layout_to_dxf",
]
