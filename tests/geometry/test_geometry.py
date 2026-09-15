from __future__ import annotations

import pytest

from amanda_agent.design.geometry import (
    InvalidDesignGeometryError,
    area_delta_percent,
    centroid,
    contains,
    load_tolerances,
    minimum_distance,
    overlap_area_m2,
    overlaps,
    validate_polygon,
)


def test_geometry_primitives_use_metric_tolerances_and_shapely():
    site = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    room = [(1, 1), (4, 1), (4, 4), (1, 4), (1, 1)]
    nearby = [(4.2, 1), (7.2, 1), (7.2, 4), (4.2, 4), (4.2, 1)]

    assert contains(site, room) is True
    assert contains(room, site) is False
    assert overlaps(room, nearby) is False
    assert minimum_distance(room, nearby) == pytest.approx(0.2)
    assert area_delta_percent(room, room) == pytest.approx(0)
    assert centroid(room) == pytest.approx((2.5, 2.5))
    assert overlap_area_m2(room, nearby) == pytest.approx(0)


def test_overlap_is_detected_by_intersection_area():
    first = [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]
    second = [(3, 1), (6, 1), (6, 3), (3, 3), (3, 1)]

    assert overlaps(first, second) is True
    assert overlap_area_m2(first, second) == pytest.approx(2)


def test_self_intersecting_polygon_fails_before_measurement():
    bow_tie = [(0, 0), (4, 4), (0, 4), (4, 0), (0, 0)]

    with pytest.raises(InvalidDesignGeometryError, match="self-intersects"):
        validate_polygon(bow_tie)


def test_tolerances_are_explicitly_metric_or_percent_based():
    tolerances = load_tolerances()

    assert tolerances["length_m"] > 0
    assert tolerances["distance_m"] > 0
    assert tolerances["area_delta_percent"] > 0
    assert all("feet" not in key.lower() for key in tolerances)
