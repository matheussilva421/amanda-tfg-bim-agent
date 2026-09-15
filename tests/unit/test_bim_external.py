"""Behavioural contract for the typed external Revit artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest

from amanda_agent.bim.external import (
    compute_georeference,
    compute_true_north,
    place_link,
    place_toposolid,
)
from amanda_agent.bim.models import DesiredElement
from amanda_agent.bim.units import meters_to_feet


def test_place_link_returns_a_metric_and_revit_unit_desired_element(tmp_path: Path):
    model = tmp_path / "context.rvt"
    model.write_bytes(b"synthetic rvt")

    element = place_link(model, name="Contexto", insertion=(1.0, 2.0, 3.0))

    assert isinstance(element, DesiredElement)
    assert element.category == "external_model_link"
    assert element.properties["name"] == "Contexto"
    assert element.geometry["insertion_m"] == [1.0, 2.0, 3.0]
    assert element.geometry["insertion_ft"] == pytest.approx(
        [meters_to_feet(value) for value in (1.0, 2.0, 3.0)]
    )
    assert element.provenance is not None
    assert element.provenance.source_refs == [str(model.resolve())]


def test_place_link_rejects_a_missing_model_file(tmp_path: Path):
    with pytest.raises(ValueError, match="model file"):
        place_link(tmp_path / "missing.rvt", name="Missing", insertion=(0, 0, 0))


def test_place_link_accepts_the_stage_mapping_insertion_shape(tmp_path: Path):
    model = tmp_path / "context.rvt"
    model.write_bytes(b"synthetic rvt")

    element = place_link(
        model,
        name="Contexto",
        insertion={"x": 1.0, "y": 2.0, "z": 3.0},
    )

    assert element.geometry["insertion_m"] == [1.0, 2.0, 3.0]


def test_place_toposolid_converts_footprint_and_preserves_unproven_reference_level():
    element = place_toposolid(
        [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0)],
        elevation=1.5,
        name="Terreno de estudo",
    )

    assert element.category == "toposolid"
    assert element.geometry["footprint_m"] == [
        [0.0, 0.0],
        [4.0, 0.0],
        [4.0, 3.0],
        [0.0, 0.0],
    ]
    assert element.geometry["elevation_ft"] == pytest.approx(meters_to_feet(1.5))
    assert element.properties["reference_level"] is None
    assert element.properties["reference_level_status"] == "NOT_PROVEN"
    assert element.provenance is not None
    assert element.provenance.notes["reference_level_proven"] is False


def test_place_toposolid_rejects_short_and_zero_area_footprints():
    with pytest.raises(ValueError, match="at least three"):
        place_toposolid([(0.0, 0.0), (1.0, 0.0)], elevation=0.0, name="short")

    with pytest.raises(ValueError, match="area"):
        place_toposolid(
            [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)], elevation=0.0, name="line"
        )


def test_true_north_keeps_degrees_and_computes_radians():
    element = compute_true_north(90.0)

    assert element.category == "true_north"
    assert element.geometry["azimuth_degrees"] == 90.0
    assert element.geometry["azimuth_radians"] == pytest.approx(1.57079632679)
    assert element.properties["angle_unit"] == "degrees_to_radians"


def test_georeference_rejects_coordinates_outside_geographic_ranges():
    with pytest.raises(ValueError, match="latitude"):
        compute_georeference(91.0, -38.0, 10.0)
    with pytest.raises(ValueError, match="longitude"):
        compute_georeference(-5.0, 181.0, 10.0)


def test_georeference_converts_elevation_and_keeps_epsg():
    element = compute_georeference(-5.0, -38.5, 12.0)

    assert element.category == "georeference"
    assert element.geometry["latitude"] == -5.0
    assert element.geometry["longitude"] == -38.5
    assert element.geometry["elevation_ft"] == pytest.approx(meters_to_feet(12.0))
    assert element.properties["epsg"] == 4674
