"""Export a canonical STUDY spatial inventory to IFC4.

The normalized plan has no verified vertical geometry. This exporter records
room identities, levels, areas and their 2D source outlines as metadata; it
does not synthesize walls, slabs, doors, windows, heights or 3D solids. Final
geometric IFC must be exported from the accepted and reopened Revit model.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_NAME = "Amanda TFG - Centro de Acolhimento Temporário"
SITE_NAME = "Terreno de referência - implantação não verificada"
BUILDING_NAME = "Inventário espacial do partido canônico - 20 pessoas"
SCHEMA = "IFC4"
UNITS = "METRE"
COORDINATE_BASIS = "NORMALIZED_METRIC_REFERENCE_NOT_SURVEY"


class IfcExportError(RuntimeError):
    """The layout cannot be exported without inventing geometry."""


def _description(**metadata: Any) -> str:
    return json.dumps(
        metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def export_layout_to_ifc(layout: Any, target: str | Path) -> dict[str, Any]:
    """Write an IFC4 spatial inventory, with no unverified physical geometry."""
    rooms = list(getattr(layout, "rooms", ()) or ())
    blocks = list(getattr(layout, "blocks", ()) or ())
    external_spaces = list(getattr(layout, "external_spaces", ()) or ())
    connectors = list(getattr(layout, "covered_connectors", ()) or ())
    content_hash = str(getattr(layout, "content_hash", "") or "")
    coordinate_basis = str(getattr(layout, "coordinate_basis", "") or "")
    if not rooms:
        raise IfcExportError("a layout with no rooms cannot be exported as IFC")
    if not content_hash:
        raise IfcExportError("the layout carries no content hash to bind the export")
    if (
        coordinate_basis != COORDINATE_BASIS
        or not blocks
        or not external_spaces
        or not connectors
    ):
        raise IfcExportError("canonical normalized pavilion geometry is required")

    import ifcopenshell
    import ifcopenshell.api.aggregate
    import ifcopenshell.api.root
    import ifcopenshell.api.unit
    from ifcopenshell.api.project import create_file

    model = create_file(version=SCHEMA)
    project = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcProject", name=PROJECT_NAME
    )
    project.Description = _description(
        scope="STUDY_SPATIAL_INVENTORY",
        layout_content_hash=content_hash,
        coordinate_basis=coordinate_basis,
        geometry_emitted=False,
    )
    ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": UNITS})

    site = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcSite", name=SITE_NAME
    )
    site.Description = _description(site_fit_status="UNVERIFIED")
    building = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcBuilding", name=BUILDING_NAME
    )
    ifcopenshell.api.aggregate.assign_object(
        model, products=[site], relating_object=project
    )
    ifcopenshell.api.aggregate.assign_object(
        model, products=[building], relating_object=site
    )

    levels = sorted({int(room.level) for room in rooms})
    if 1 not in levels:
        levels.insert(0, 1)
    storeys = {}
    for level in levels:
        storey = ifcopenshell.api.root.create_entity(
            model,
            ifc_class="IfcBuildingStorey",
            name=f"Pavimento {level:02d}",
        )
        storey.Description = _description(
            level=level,
            elevation="UNSPECIFIED",
            coordinate_basis=coordinate_basis,
        )
        ifcopenshell.api.aggregate.assign_object(
            model, products=[storey], relating_object=building
        )
        storeys[level] = storey

    def add_space(name: str, metadata: dict[str, Any], level: int) -> Any:
        space = ifcopenshell.api.root.create_entity(
            model, ifc_class="IfcSpace", name=name
        )
        space.Description = _description(**metadata)
        ifcopenshell.api.aggregate.assign_object(
            model, products=[space], relating_object=storeys[level]
        )
        return space

    for room in rooms:
        add_space(
            room.logical_id,
            {
                "category": "internal_program",
                "component_id": room.component_id,
                "sector_id": room.sector_id,
                "level": int(room.level),
                "net_area_m2": float(room.net_area_m2),
                "accessible": bool(room.accessible),
                "geometry_basis": coordinate_basis,
                "polygon_wkt": room.polygon.wkt,
                "geometry_emitted": False,
            },
            int(room.level),
        )

    for space in external_spaces:
        add_space(
            space.logical_id,
            {
                "category": "external_program",
                "component_id": space.component_id,
                "area_m2": float(space.area_m2),
                "geometry_basis": coordinate_basis,
                "polygon_wkt": space.polygon.wkt,
                "geometry_emitted": False,
            },
            1,
        )

    for connector in connectors:
        add_space(
            connector.connector_id,
            {
                "category": "covered_external_circulation",
                "from_component": connector.from_component,
                "to_component": connector.to_component,
                "area_m2": float(connector.area_m2),
                "geometry_basis": coordinate_basis,
                "polygon_wkt": connector.footprint.wkt,
                "geometry_emitted": False,
            },
            1,
        )

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    model.write(str(target))
    return {
        "path": str(target),
        "bytes": target.stat().st_size,
        "schema": model.schema,
        "units": UNITS,
        "project_name": PROJECT_NAME,
        "layout_content_hash": content_hash,
        "coordinate_basis": coordinate_basis,
        "scope": "STUDY_SPATIAL_INVENTORY",
        "source": "canonical normalized layout; no Revit or 3D geometry",
        "counts": {
            "spaces": len(rooms) + len(external_spaces) + len(connectors),
            "internal_spaces": len(rooms),
            "external_spaces": len(external_spaces),
            "covered_connectors": len(connectors),
            "storeys": len(storeys),
            "physical_elements": 0,
        },
        "program": {
            "person_capacity": int(layout.parameters["people"]),
            "net_internal_m2": float(layout.accounting["net_internal_m2"]),
            "external_programmed_m2": float(
                layout.accounting["external_programmed_m2"]
            ),
            "enclosed_estimate_m2": [
                float(layout.accounting["enclosed_estimate_min_m2"]),
                float(layout.accounting["enclosed_estimate_max_m2"]),
            ],
            "covered_estimate_m2": [
                float(layout.accounting["covered_estimate_min_m2"]),
                float(layout.accounting["covered_estimate_max_m2"]),
            ],
        },
        "limitation": (
            "Spatial inventory only. Elevations, walls, openings, floors and "
            "roof geometry remain unspecified; final IFC must come from verified Revit."
        ),
    }


__all__ = [
    "BUILDING_NAME",
    "COORDINATE_BASIS",
    "PROJECT_NAME",
    "SCHEMA",
    "SITE_NAME",
    "UNITS",
    "IfcExportError",
    "export_layout_to_ifc",
]
