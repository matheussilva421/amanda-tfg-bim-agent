"""Contract for the canonical STUDY spatial inventory IFC.

No wall thickness, floor height, doors, windows or slabs are inferred from a
normalized 2D parti. The IFC preserves space identities and 2D source outlines
as metadata; final geometric IFC comes from the verified Revit model.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from amanda_agent.production.ifc_export import (
    IfcExportError,
    export_layout_to_ifc,
)


@pytest.fixture(scope="module")
def layout(canonical_layout):
    return canonical_layout


@pytest.fixture(scope="module")
def exported(tmp_path_factory, layout):
    target = tmp_path_factory.mktemp("ifc") / "AMANDA_ESTUDO.ifc"
    report = export_layout_to_ifc(layout, target)
    return target, report


def test_ifc_is_written_with_a_valid_exchange_header(exported):
    target, report = exported

    assert target.is_file()
    assert target.stat().st_size > 1_000
    assert target.read_bytes()[:32].lstrip().startswith(b"ISO-10303-21;")
    assert report["bytes"] == target.stat().st_size
    assert report["scope"] == "STUDY_SPATIAL_INVENTORY"


def test_ifc_parses_spaces_and_does_not_invent_physical_elements(exported, layout):
    target, report = exported
    ifcopenshell = pytest.importorskip("ifcopenshell")

    model = ifcopenshell.open(str(target))
    counts = report["counts"]
    assert len(model.by_type("IfcSpace")) == counts["spaces"]
    assert len(model.by_type("IfcBuildingStorey")) == 2
    for forbidden in ("IfcWall", "IfcDoor", "IfcWindow", "IfcSlab"):
        assert len(model.by_type(forbidden)) == 0
    assert counts["physical_elements"] == 0
    assert counts["internal_spaces"] == len(layout.rooms)
    assert counts["external_spaces"] == len(layout.external_spaces) == 5
    assert counts["covered_connectors"] == len(layout.covered_connectors) == 4


def test_ifc_spaces_match_canonical_ids_and_keep_level_geometry_metadata(
    exported, layout
):
    target, report = exported
    ifcopenshell = pytest.importorskip("ifcopenshell")

    model = ifcopenshell.open(str(target))
    spaces = {space.Name: space for space in model.by_type("IfcSpace")}
    assert {room.logical_id for room in layout.rooms} <= set(spaces)
    assert report["counts"]["internal_spaces"] == len(layout.rooms)

    room = layout.rooms[0]
    metadata = json.loads(spaces[room.logical_id].Description)
    assert metadata["component_id"] == room.component_id
    assert metadata["sector_id"] == room.sector_id
    assert metadata["level"] == room.level
    assert metadata["net_area_m2"] == pytest.approx(room.net_area_m2)
    assert metadata["geometry_basis"] == "NORMALIZED_METRIC_REFERENCE_NOT_SURVEY"
    assert metadata["polygon_wkt"]


def test_ifc_carries_project_identity_and_units(exported, layout):
    _, report = exported

    assert report["project_name"]
    assert report["layout_content_hash"] == layout.content_hash
    assert report["units"] == "METRE"
    assert report["schema"] == "IFC4"
    assert report["coordinate_basis"] == "NORMALIZED_METRIC_REFERENCE_NOT_SURVEY"


def test_export_refuses_a_layout_with_no_rooms():
    class Empty:
        rooms = ()
        content_hash = ""

    with pytest.raises(IfcExportError):
        export_layout_to_ifc(Empty(), Path("unused.ifc"))


def test_export_is_deterministic_in_semantics(tmp_path, layout):
    first = export_layout_to_ifc(layout, tmp_path / "a.ifc")
    second = export_layout_to_ifc(layout, tmp_path / "b.ifc")

    assert first["counts"] == second["counts"]
    assert first["layout_content_hash"] == second["layout_content_hash"]
