from __future__ import annotations

import pytest
import shapely

from amanda_agent.site.geometry import (
    PINNED_SHAPELY_VERSION,
    InvalidBoundaryError,
    build_area_preserving_rectangular_placeholder,
    compute_area_m2,
    polygon_from_geojson,
    polygon_to_geojson,
)
from amanda_agent.site.models import BoundaryKind


def test_geometry_uses_the_exact_tested_shapely_version():
    assert shapely.__version__ == PINNED_SHAPELY_VERSION


def test_area_from_self_intersecting_ring_is_refused():
    with pytest.raises(InvalidBoundaryError, match="self-intersect"):
        compute_area_m2([(0, 0), (10, 10), (0, 10), (10, 0), (0, 0)])


def test_equal_area_rectangle_is_explicitly_a_provisional_placeholder():
    placeholder = build_area_preserving_rectangular_placeholder(24_135)

    assert compute_area_m2(placeholder) == pytest.approx(24_135)
    assert placeholder.kind is BoundaryKind.STUDY_PLACEHOLDER
    assert placeholder.is_provisional is True
    assert placeholder.is_cadastral is False


def test_geojson_round_trip_preserves_the_validated_ring():
    ring = [(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)]

    encoded = polygon_to_geojson(ring)
    decoded = polygon_from_geojson(encoded)

    assert encoded["type"] == "Polygon"
    assert decoded == ring

