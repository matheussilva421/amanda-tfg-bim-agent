"""Behavioural contract of the DXF export of the delegated layout.

The deliverable lists DWG as applicable.  A DWG needs Revit or a licensed CAD
kernel; an ASCII DXF is the open exchange format a CAD user can open, edit and
save as DWG themselves, so the plan is delivered in DXF and the limitation is
stated rather than hidden.

The writer is a real R12 ASCII DXF: groups of code/value pairs, one entity per
line, in the order the format requires.  These tests read it back and check the
entities the drawing must contain.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from amanda_agent.design.architectural_layout import build_courtyard_layout
from amanda_agent.production.dxf_export import (
    DxfExportError,
    export_layout_to_dxf,
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
    target = tmp_path_factory.mktemp("dxf") / "AMANDA_ESTUDO.dxf"
    report = export_layout_to_dxf(layout, target)
    return target, report


def _entities(text: str) -> list[str]:
    """Return the entity type of every entity in the ENTITIES section."""

    names: list[str] = []
    lines = text.splitlines()
    in_entities = False
    index = 0
    while index < len(lines) - 1:
        code = lines[index].strip()
        value = lines[index + 1].strip()
        if code == "0" and value == "SECTION":
            section = lines[index + 3].strip() if index + 3 < len(lines) else ""
            in_entities = section == "ENTITIES"
        elif in_entities and code == "0" and value == "ENDSEC":
            break
        elif in_entities and code == "0":
            names.append(value)
        index += 2
    return names


def test_dxf_has_the_r12_structure_a_cad_package_requires(exported):
    target, report = exported

    text = target.read_text(encoding="utf-8")
    assert text.startswith("0\nSECTION")
    assert "HEADER" in text
    assert "TABLES" in text
    assert "ENTITIES" in text
    assert text.rstrip().endswith("EOF")
    assert report["bytes"] == target.stat().st_size


def test_dxf_layers_separate_the_plan_by_discipline(exported):
    target, report = exported
    text = target.read_text(encoding="utf-8")

    for layer in ("AMANDA-PAREDES", "AMANDA-AMBIENTES", "AMANDA-GALERIA",
                  "AMANDA-VARANDA", "AMANDA-PATIO", "AMANDA-ABERTURAS",
                  "AMANDA-TEXTO"):
        assert layer in text, layer
    assert report["layers"] >= 7


def test_dxf_contains_a_closed_polyline_per_room(exported, layout):
    target, report = exported
    names = _entities(target.read_text(encoding="utf-8"))

    closed = 0
    lines = target.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "0" and index + 1 < len(lines) and lines[index + 1].strip() == "LWPOLYLINE":
            closed += 1
    assert closed >= len(layout.rooms)
    assert report["counts"]["rooms"] == len(layout.rooms)
    assert names.count("LWPOLYLINE") >= len(layout.rooms)


def test_dxf_carries_the_logical_ids_as_text(exported, layout):
    target, report = exported
    text = target.read_text(encoding="utf-8")

    sample = layout.rooms[0].logical_id
    assert sample in text
    assert report["counts"]["labels"] >= len(layout.rooms)


def test_dxf_is_in_metres_and_declares_its_units(exported):
    target, report = exported

    assert report["units"] == "METRE"
    assert "$INSUNITS" in target.read_text(encoding="utf-8")


def test_export_refuses_a_layout_with_no_rooms():
    class Empty:
        rooms = []
        content_hash = ""

    with pytest.raises(DxfExportError):
        export_layout_to_dxf(Empty(), Path("unused.dxf"))


def test_export_is_deterministic(tmp_path, layout):
    first = export_layout_to_dxf(layout, tmp_path / "a.dxf")
    second = export_layout_to_dxf(layout, tmp_path / "b.dxf")

    assert first["bytes"] == second["bytes"]
    assert first["counts"] == second["counts"]
