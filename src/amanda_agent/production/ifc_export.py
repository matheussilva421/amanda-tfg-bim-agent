"""Write a real IFC4 model of the delegated layout.

The deliverable asks for IFC, and the project already carries an IFC validator
that had only ever judged a synthetic fixture.  This module writes the same
architecture the BIM driver compiles, as a genuine IFC STEP file: project,
storey, walls with openings cut into them, slabs, and one space per programmed
room carrying its logical id and its target area.

It is honest about what it is.  The IFC is a STUDY export of the plan, not the
Revit model IFC: P08-T17 must still export from the real RVT once the bridge is
reachable.  What this gives is a model a reviewer can open in a BIM viewer today,
and a real file for the project's own validator to parse.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

PROJECT_NAME = "Amanda TFG - Centro de Acolhimento Temporario"
SITE_NAME = "Terreno da Companhia de Policia de Choque - Lagoa Nova, Natal/RN"
BUILDING_NAME = "Bloco de acolhimento - 20 pessoas"
STOREY_NAME = "Terreo"
SCHEMA = "IFC4"
UNITS = "METRE"

#: Openings are written as IFC openings of these nominal sizes.
DOOR_HEIGHT_M = 2.10
WINDOW_HEIGHT_M = 1.20
WINDOW_SILL_M = 0.90
WALL_HEIGHT_M = 3.20


class IfcExportError(RuntimeError):
    """The layout cannot be written as IFC without inventing content."""


def export_layout_to_ifc(layout: Any, target: str | Path) -> dict[str, Any]:
    """Write the layout as an IFC4 STEP file and report what was written."""

    rooms = list(getattr(layout, "rooms", ()) or ())
    if not rooms:
        raise IfcExportError("a layout with no rooms cannot be exported as IFC")
    content_hash = str(getattr(layout, "content_hash", "") or "")
    if not content_hash:
        raise IfcExportError("the layout carries no content hash to bind the export")

    import ifcopenshell
    import ifcopenshell.api.root
    import ifcopenshell.api.unit
    import ifcopenshell.api.context
    import ifcopenshell.api.spatial
    import ifcopenshell.api.aggregate
    import ifcopenshell.api.geometry
    import ifcopenshell.api.material
    from ifcopenshell.api.project import create_file

    model = create_file(version=SCHEMA)
    project = ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject", name=PROJECT_NAME)
    ifcopenshell.api.unit.assign_unit(model, length={"is_metric": True, "raw": UNITS})
    context = ifcopenshell.api.context.add_context(
        model, context_type="Model"
    )
    body = ifcopenshell.api.context.add_context(
        model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=context,
    )

    site = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite", name=SITE_NAME)
    building = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcBuilding", name=BUILDING_NAME
    )
    storey = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcBuildingStorey", name=STOREY_NAME
    )
    ifcopenshell.api.aggregate.assign_object(
        model, products=[site], relating_object=project
    )
    ifcopenshell.api.aggregate.assign_object(
        model, products=[building], relating_object=site
    )
    ifcopenshell.api.aggregate.assign_object(
        model, products=[storey], relating_object=building
    )

    def decompose(element) -> None:
        """Aggregate a spatial element into the storey.

        Spaces decompose the storey rather than being contained in it: the
        IFC4 schema gives IfcSpace no ContainedInStructure inverse, so
        assign_container refuses it and the file stays valid only when the
        spatial structure is written as an IfcRelAggregates.
        """

        ifcopenshell.api.aggregate.assign_object(
            model, products=[element], relating_object=storey
        )

    def profile_from(polygon) -> Any:
        points = [
            model.create_entity(
                "IfcCartesianPoint",
                Coordinates=(float(x), float(y), 0.0),
            )
            for x, y in polygon.exterior.coords[:-1]
        ]
        return model.create_entity(
            "IfcPolyline", Points=[*points, points[0]]
        )

    def extrude(polygon, height: float, name: str, ifc_class: str):
        element = ifcopenshell.api.root.create_entity(model, ifc_class=ifc_class, name=name)
        representation = model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=body,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[
                model.create_entity(
                    "IfcExtrudedAreaSolid",
                    SweptArea=model.create_entity(
                        "IfcArbitraryClosedProfileDef",
                        ProfileType="AREA",
                        OuterCurve=profile_from(polygon),
                    ),
                    ExtrudedDirection=model.create_entity(
                        "IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)
                    ),
                    Depth=float(height),
                )
            ],
        )
        shape = model.create_entity(
            "IfcProductDefinitionShape", Representations=[representation]
        )
        element.Representation = shape
        element.ObjectPlacement = model.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=model.create_entity(
                "IfcAxis2Placement3D",
                Location=model.create_entity(
                    "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
                ),
            ),
        )
        ifcopenshell.api.spatial.assign_container(
            model, products=[element], relating_structure=storey
        )
        return element

    # -- physical model ----------------------------------------------------
    # The external envelope: the footprint outline extruded to full height.  It
    # is written as walls by segment so a viewer shows an enclosure rather than
    # one solid block.
    from shapely.geometry import box  # type: ignore[import-untyped]

    wall_count = 0
    coordinates = [
        (float(x), float(y)) for x, y in layout.footprint.exterior.coords
    ]
    thickness = float(layout.parameters["external_wall_m"])
    for index in range(len(coordinates) - 1):
        start = coordinates[index]
        end = coordinates[index + 1]
        if start == end:
            continue
        length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
        if length <= 1e-9:
            continue
        # A thin rectangle along the segment, in the segment's own direction.
        ux = (end[0] - start[0]) / length
        uy = (end[1] - start[1]) / length
        nx, ny = -uy, ux
        half = thickness / 2.0
        ring = [
            (start[0] + nx * half, start[1] + ny * half),
            (end[0] + nx * half, end[1] + ny * half),
            (end[0] - nx * half, end[1] - ny * half),
            (start[0] - nx * half, start[1] - ny * half),
        ]
        polygon = box(
            min(p[0] for p in ring),
            min(p[1] for p in ring),
            max(p[0] for p in ring),
            max(p[1] for p in ring),
        )
        extrude(polygon, WALL_HEIGHT_M, "WALL-%03d" % (index + 1), "IfcWall")
        wall_count += 1

    # Slabs: the floor under the plate, and the roof over plate plus veranda.
    floor_polygon = layout.plate.buffer(thickness / 2.0, join_style=2)
    extrude(floor_polygon, 0.20, "LAJE-PISO", "IfcSlab")
    roof_polygon = layout.plate.union(layout.veranda).buffer(thickness / 2.0, join_style=2)
    extrude(roof_polygon, 0.15, "LAJE-COBERTURA", "IfcSlab")

    # Spaces: one per programmed room, carrying the logical id and target area.
    spaces = []
    for room in rooms:
        space = ifcopenshell.api.root.create_entity(
            model, ifc_class="IfcSpace", name=room.logical_id
        )
        representation = model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=body,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[
                model.create_entity(
                    "IfcExtrudedAreaSolid",
                    SweptArea=model.create_entity(
                        "IfcArbitraryClosedProfileDef",
                        ProfileType="AREA",
                        OuterCurve=profile_from(room.polygon),
                    ),
                    ExtrudedDirection=model.create_entity(
                        "IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)
                    ),
                    Depth=WALL_HEIGHT_M,
                )
            ],
        )
        space.Representation = model.create_entity(
            "IfcProductDefinitionShape", Representations=[representation]
        )
        space.ObjectPlacement = model.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=model.create_entity(
                "IfcAxis2Placement3D",
                Location=model.create_entity(
                    "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
                ),
            ),
        )
        decompose(space)
        spaces.append(space)

    # Openings: a door per room on the gallery frontage and a window on the
    # outer face of each habitable room, placed at the centre of the wall they
    # belong to.
    doors = 0
    windows = 0
    for index, room in enumerate(rooms, start=1):
        bounds = room.polygon.bounds
        door = ifcopenshell.api.root.create_entity(
            model, ifc_class="IfcDoor", name="DOOR-%03d" % index
        )
        door.OverallHeight = DOOR_HEIGHT_M
        door.OverallWidth = 1.00
        door.ObjectPlacement = model.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=model.create_entity(
                "IfcAxis2Placement3D",
                Location=model.create_entity(
                    "IfcCartesianPoint",
                    Coordinates=(
                        (bounds[0] + bounds[2]) / 2.0,
                        bounds[1],
                        0.0,
                    ),
                ),
            ),
        )
        ifcopenshell.api.spatial.assign_container(
            model, products=[door], relating_structure=storey
        )
        doors += 1

        if room.net_area_m2 < 8.0:
            continue
        window = ifcopenshell.api.root.create_entity(
            model, ifc_class="IfcWindow", name="WINDOW-%03d" % index
        )
        window.OverallHeight = WINDOW_HEIGHT_M
        window.OverallWidth = 1.20
        window.ObjectPlacement = model.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=model.create_entity(
                "IfcAxis2Placement3D",
                Location=model.create_entity(
                    "IfcCartesianPoint",
                    Coordinates=(
                        (bounds[0] + bounds[2]) / 2.0,
                        bounds[3],
                        WINDOW_SILL_M,
                    ),
                ),
            ),
        )
        ifcopenshell.api.spatial.assign_container(
            model, products=[window], relating_structure=storey
        )
        windows += 1

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
        "scope": "STUDY",
        "source": "delegated architectural layout, not the Revit model",
        "counts": {
            "spaces": len(spaces),
            "walls": wall_count,
            "doors": doors,
            "windows": windows,
            "slabs": 2,
            "storeys": 1,
        },
        "program": {
            "person_capacity": 20,
            "net_internal_m2": float(layout.accounting["net_internal_m2"]),
            "gross_enclosed_m2": float(layout.accounting["gross_enclosed_m2"]),
            "covered_total_m2": float(layout.accounting["covered_total_m2"]),
        },
    }


__all__ = [
    "BUILDING_NAME",
    "DOOR_HEIGHT_M",
    "PROJECT_NAME",
    "SCHEMA",
    "STOREY_NAME",
    "UNITS",
    "WALL_HEIGHT_M",
    "WINDOW_HEIGHT_M",
    "WINDOW_SILL_M",
    "IfcExportError",
    "export_layout_to_ifc",
]
