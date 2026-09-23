"""Contract for a 2D study DXF of the canonical pavilion layout.

The export preserves room, block, external-space and covered-path outlines.
It does not invent walls, openings, elevations or a DWG representation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from amanda_agent.production.dxf_export import (
    LAYERS,
    DxfExportError,
    export_layout_to_dxf,
)


@pytest.fixture(scope="module")
def layout(canonical_layout):
    return canonical_layout


@pytest.fixture(scope="module")
def exported(tmp_path_factory, layout):
    target = tmp_path_factory.mktemp("dxf") / "AMANDA_ESTUDO.dxf"
    report = export_layout_to_dxf(layout, target)
    return target, report


def _entities(text: str) -> list[str]:
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
    assert report["scope"] == "STUDY"


def test_dxf_layers_separate_canonical_plan_content(exported):
    target, report = exported
    text = target.read_text(encoding="utf-8")

    for layer in LAYERS:
        assert layer in text, layer
    assert report["layers"] == len(LAYERS)
    assert "AMANDA-ABERTURAS" not in text


def test_dxf_contains_rooms_blocks_external_program_and_covered_paths(exported, layout):
    target, report = exported
    text = target.read_text(encoding="utf-8")
    names = _entities(text)

    assert names.count("LWPOLYLINE") >= len(layout.rooms) + len(layout.blocks)
    assert report["counts"]["rooms"] == len(layout.rooms)
    assert report["counts"]["blocks"] == len(layout.blocks) == 7
    assert report["counts"]["external_spaces"] == len(layout.external_spaces) == 5
    assert report["counts"]["covered_connectors"] == len(layout.covered_connectors) == 4
    assert "RES_PAV_D_COMMUNAL" in text
    assert "REQ-07-01" in text
    assert "COVERED-RES_PAV_A-TO-PROTECTED_PATIO" in text


def test_dxf_separates_room_geometry_by_level(exported):
    target, _ = exported
    text = target.read_text(encoding="utf-8")

    assert "AMANDA-INTERIORES-P01" in text
    assert "AMANDA-INTERIORES-P02" in text
    assert "geometry=2d-study-only" in text


def test_dxf_is_in_metres_and_declares_its_units(exported):
    target, report = exported

    assert report["units"] == "METRE"
    assert "$INSUNITS" in target.read_text(encoding="utf-8")


def test_export_refuses_a_layout_with_no_rooms():
    class Empty:
        rooms = ()
        content_hash = ""

    with pytest.raises(DxfExportError):
        export_layout_to_dxf(Empty(), Path("unused.dxf"))


def test_export_is_deterministic(tmp_path, layout):
    first = export_layout_to_dxf(layout, tmp_path / "a.dxf")
    second = export_layout_to_dxf(layout, tmp_path / "b.dxf")

    assert first["bytes"] == second["bytes"]
    assert first["counts"] == second["counts"]
