from __future__ import annotations

import pytest
from shapely.geometry import box

from amanda_agent.design.external_spaces import (
    generate_external_spaces,
    validate_external_spaces,
)

SITE = box(0, 0, 30, 20)


def test_required_external_logical_ids_are_first_class_and_area_targets_are_met():
    result = generate_external_spaces(
        SITE,
        [
            {"logical_id": "courtyard", "target_area_m2": 80, "kind": "protected_courtyard"},
            {"logical_id": "therapeutic", "target_area_m2": 80, "kind": "therapeutic_garden", "privacy_level": 4},
            {"logical_id": "playground", "target_area_m2": 40, "kind": "playground"},
        ],
    )

    assert result.ok is True
    assert [item["logical_id"] for item in result.spaces] == ["courtyard", "therapeutic", "playground"]
    assert all(SITE.covers(item["geometry"]) for item in result.spaces)
    assert all(item["geometry"].area == pytest.approx(item["target_area_m2"]) for item in result.spaces)
    assert result.used_leftover_as_garden is False


def test_therapeutic_space_must_satisfy_protection_policy():
    result = validate_external_spaces(
        [{"logical_id": "therapeutic", "geometry": box(0, 0, 8, 10), "kind": "therapeutic_garden", "privacy_level": 1}],
        SITE,
        privacy_policy={"protected_min_privacy_level": 3},
    )

    assert result.ok is False
    assert any(item.code == "external_privacy" for item in result.violations)


def test_playground_child_relation_is_checked_geometrically():
    result = validate_external_spaces(
        [{"logical_id": "playground", "geometry": box(0, 0, 4, 4), "kind": "playground", "child_relation": "child-zone"}],
        SITE,
        related_geometries={"child-zone": box(20, 15, 22, 17)},
    )

    assert result.ok is False
    assert any(item.code == "playground_child_relation" for item in result.violations)
