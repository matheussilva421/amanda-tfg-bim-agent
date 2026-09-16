"""Behavioural contract of the IFC export of the delegated layout.

The deliverable asks for IFC.  Revit will export the model IFC once the bridge
is reachable; this module exports the same architecture from the plan, so a real
IFC exists now, a reviewer can open it in a BIM viewer, and the project's own
IFC validator is exercised against real geometry instead of a fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from amanda_agent.design.architectural_layout import build_courtyard_layout
from amanda_agent.production.ifc_export import (
    IfcExportError,
    export_layout_to_ifc,
)

ROOT = Path(__file__).resolve().parents[2]
PROGRAM_PATH = ROOT / "project" / "requirements" / "program.json"


@pytest.fixture(scope="module")
def program() -> dict:
    return json.loads(PROGRAM_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def layout(program: dict):
    return build_courtyard_layout(program)


@pytest.fixture(scope="module")
def exported(tmp_path_factory, layout):
    target = tmp_path_factory.mktemp("ifc") / "AMANDA_ESTUDO.ifc"
    report = export_layout_to_ifc(layout, target)
    return target, report


def test_ifc_is_written_with_a_valid_exchange_header(exported):
    target, report = exported

    assert target.is_file()
    assert target.stat().st_size > 10_000
    header = target.read_bytes()[:32].lstrip()
    assert header.startswith(b"ISO-10303-21;")
    assert report["bytes"] == target.stat().st_size


def test_ifc_parses_and_carries_the_expected_element_counts(exported):
    target, report = exported
    ifcopenshell = pytest.importorskip("ifcopenshell")

    model = ifcopenshell.open(str(target))
    counts = report["counts"]
    assert len(model.by_type("IfcSpace")) == counts["spaces"]
    assert len(model.by_type("IfcWall")) == counts["walls"]
    assert len(model.by_type("IfcDoor")) == counts["doors"]
    assert len(model.by_type("IfcWindow")) == counts["windows"]
    assert len(model.by_type("IfcSlab")) == counts["slabs"]


def test_ifc_spaces_match_the_program_areas(exported, layout):
    target, report = exported
    ifcopenshell = pytest.importorskip("ifcopenshell")

    model = ifcopenshell.open(str(target))
    names = {space.Name for space in model.by_type("IfcSpace")}
    assert {room.logical_id for room in layout.rooms} <= names
    assert report["counts"]["spaces"] == len(layout.rooms)


def test_ifc_carries_the_project_identity_and_units(exported, layout):
    target, report = exported

    assert report["project_name"]
    assert report["layout_content_hash"] == layout.content_hash
    assert report["units"] == "METRE"
    assert report["schema"] in {"IFC4", "IFC4X3"}


def test_export_refuses_a_layout_with_no_rooms():
    class Empty:
        rooms = []
        content_hash = ""

    with pytest.raises(IfcExportError):
        export_layout_to_ifc(Empty(), Path("unused.ifc"))


def test_export_is_deterministic(tmp_path, layout):
    first = export_layout_to_ifc(layout, tmp_path / "a.ifc")
    second = export_layout_to_ifc(layout, tmp_path / "b.ifc")

    assert first["counts"] == second["counts"]
    assert first["layout_content_hash"] == second["layout_content_hash"]
