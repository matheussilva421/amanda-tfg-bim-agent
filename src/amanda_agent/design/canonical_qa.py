"""Canonical parti checks; normalized-frame tolerances are not site constraints."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from amanda_agent.design.canonical_reference import CanonicalReferenceProfile

CheckStatus = Literal["PASS", "FAIL", "BLOCKED"]


@dataclass(frozen=True)
class CanonicalCheck:
    check_id: str
    severity: str
    status: CheckStatus
    rule: str
    evidence: str


# Relative-distance tolerances apply only to the normalized reference geometry.
_PUBLIC_EDGE_MAX_DISTANCE_M = 15.0
_SERVICE_ACCESS_MIN_SEPARATION_M = 20.0
_GREEN_ADJACENCY_MAX_DISTANCE_M = 5.0
_COURTYARD_CLUSTER_MAX_DISTANCE_M = 15.0
_GEOMETRY_TOLERANCE_M = 1e-6
_REQUIRED_VISUAL_STAGES = ("R04", "R06", "R08", "R12", "R13", "R15")
_ALLOWED_DEVIATION_BASES = {
    "PROGRAM",
    "VERIFIED_SITE",
    "ACCESSIBILITY",
    "REGULATION",
    "CONSTRUCTABILITY",
}


def _blocks(layout: object) -> tuple[object, ...]:
    return tuple(getattr(layout, "blocks", ()))


def _externals(layout: object) -> tuple[object, ...]:
    return tuple(getattr(layout, "external_spaces", ()))


def _parameters(layout: object) -> Mapping[str, object]:
    value = getattr(layout, "parameters", {})
    return value if isinstance(value, Mapping) else {}


def _component(items: Sequence[object], component_id: str) -> object | None:
    return next(
        (item for item in items if getattr(item, "component_id", None) == component_id),
        None,
    )


def _check(
    check_id: str,
    severity: str,
    status: CheckStatus,
    rule: str,
    evidence: str,
) -> CanonicalCheck:
    return CanonicalCheck(check_id, severity, status, rule, evidence)


def _area(item: object) -> float:
    area = getattr(item, "area_m2", None)
    if area is not None:
        return float(area)
    polygon = getattr(item, "polygon", None)
    return float(polygon.area) if polygon is not None else 0.0


def _centerline_is_curved(connector: object) -> bool:
    """Require a measured bend in the normalized connector centerline."""

    points = getattr(connector, "centerline", ())
    if not isinstance(points, (list, tuple)) or len(points) < 3:
        return False
    start_x, start_y = points[0]
    end_x, end_y = points[-1]
    dx = float(end_x) - float(start_x)
    dy = float(end_y) - float(start_y)
    chord_length = math.hypot(dx, dy)
    if chord_length <= _GEOMETRY_TOLERANCE_M:
        return False
    maximum_deviation = max(
        abs(
            dx * (float(point[1]) - float(start_y))
            - dy * (float(point[0]) - float(start_x))
        )
        / chord_length
        for point in points[1:-1]
    )
    return maximum_deviation > 0.25


def run_canonical_checks(
    layout: object, profile: CanonicalReferenceProfile
) -> list[CanonicalCheck]:
    """Return the twelve canonical rubric results without hiding blocked gates."""
    blocks = _blocks(layout)
    externals = _externals(layout)
    parameters = _parameters(layout)
    footprint = getattr(layout, "footprint", None)
    residential = tuple(
        block
        for block in blocks
        if str(getattr(block, "component_id", "")).startswith("RES_PAV_")
    )
    admin = _component(blocks, "ADMIN_ACOLHIMENTO")
    service = _component(blocks, "SERVICE_CAPACITATION")
    child = _component(blocks, "CHILD_SECTOR")
    patio = _component(externals, "PROTECTED_PATIO")

    single_bar = (
        not blocks
        or len(blocks) == 1
        or getattr(footprint, "geom_type", None) == "Polygon"
    )
    results = [
        _check(
            "CANON-001",
            "CRITICAL",
            "FAIL" if single_bar else "PASS",
            "no_single_linear_bar",
            f"building_blocks={len(blocks)}; footprint_type={getattr(footprint, 'geom_type', 'missing')}",
        )
    ]

    public_point = getattr(layout, "public_access_point", None)
    admin_distance = (
        float(public_point.distance(admin.footprint))
        if public_point is not None and admin is not None
        else math.inf
    )
    admin_at_public = admin_distance <= _PUBLIC_EDGE_MAX_DISTANCE_M
    results.append(
        _check(
            "CANON-002",
            "CRITICAL",
            "PASS" if admin_at_public else "FAIL",
            "admin_at_public_interface",
            f"admin_to_public_access_m={admin_distance:.3f}; limit_m={_PUBLIC_EDGE_MAX_DISTANCE_M:.1f}",
        )
    )

    admin_levels = (
        {int(getattr(room, "level", -1)) for room in getattr(admin, "rooms", ())}
        if admin is not None
        else set()
    )
    admin_storeys = int(getattr(admin, "storeys", 0)) if admin is not None else 0
    target_storeys = profile.admin_storeys_target
    two_level = admin_storeys == target_storeys and admin_levels == set(
        range(1, target_storeys + 1)
    )
    results.append(
        _check(
            "CANON-003",
            "HIGH",
            "PASS" if two_level else "FAIL",
            "admin_two_storey_reference_intent",
            f"storeys={admin_storeys}; room_levels={sorted(admin_levels)}; target={target_storeys}",
        )
    )

    residential_ids = {str(getattr(item, "component_id", "")) for item in residential}
    expected_residential = profile.residential_pavilion_count_target
    expected_sleeping = profile.sleeping_pavilions_target
    expected_communal = profile.communal_pavilions_target
    patio_center = patio.polygon.centroid if patio is not None else None
    board_quadrants = {
        "RES_PAV_A": (-1, 1),
        "RES_PAV_B": (-1, -1),
        "RES_PAV_C": (1, -1),
        "RES_PAV_D_COMMUNAL": (1, 1),
    }
    board_arrangement_ok = patio_center is not None and all(
        (block.footprint.centroid.x - patio_center.x) * x_sign > 0.0
        and (block.footprint.centroid.y - patio_center.y) * y_sign > 0.0
        for component_id, (x_sign, y_sign) in board_quadrants.items()
        for block in residential
        if block.component_id == component_id
    ) and all(
        _component(residential, component_id) is not None
        for component_id in board_quadrants
    )
    residential_cluster_ok = (
        len(residential) == expected_residential
        and sum(
            item in residential_ids for item in ("RES_PAV_A", "RES_PAV_B", "RES_PAV_C")
        )
        == expected_sleeping
        and ("RES_PAV_D_COMMUNAL" in residential_ids) == (expected_communal == 1)
        and all(
            first.footprint.distance(second.footprint) > _GEOMETRY_TOLERANCE_M
            for index, first in enumerate(residential)
            for second in residential[index + 1 :]
        )
        and board_arrangement_ok
    )
    results.append(
        _check(
            "CANON-004",
            "CRITICAL",
            "PASS" if residential_cluster_ok else "FAIL",
            "residential_is_pavilion_cluster",
            f"pavilions={len(residential)}; sleeping_target={expected_sleeping}; communal_target={expected_communal}; board_quadrants_match={board_arrangement_ok}",
        )
    )

    garden_access_ok = (
        profile.central_garden_required
        and patio is not None
        and _area(patio) > 0.0
        and len(residential) == expected_residential
        and all(
            getattr(block, "access_point", None) is not None
            and block.access_point.distance(patio.polygon)
            <= _COURTYARD_CLUSTER_MAX_DISTANCE_M
            for block in residential
        )
        and all(patio.polygon.disjoint(block.footprint) for block in blocks)
    )
    results.append(
        _check(
            "CANON-005",
            "CRITICAL",
            "PASS" if garden_access_ok else "FAIL",
            "central_therapeutic_garden_structures_cluster",
            f"protected_patio_area_m2={_area(patio) if patio is not None else 0.0:.3f}; residential_nearby={garden_access_ok}",
        )
    )

    connectors = tuple(
        item
        for item in getattr(layout, "covered_connectors", ())
        if getattr(item, "to_component", None) == "PROTECTED_PATIO"
    )
    connector_sources = {getattr(item, "from_component", None) for item in connectors}
    paths_ok = (
        patio is not None
        and connector_sources == residential_ids
        and len(connectors) == expected_residential
        and all(
            getattr(item, "footprint", None) is not None
            and item.footprint.area > 0.0
            and item.footprint.distance(patio.polygon) <= _GEOMETRY_TOLERANCE_M
            and _centerline_is_curved(item)
            and all(
                item.footprint.intersection(block.footprint).area
                <= _GEOMETRY_TOLERANCE_M
                for block in blocks
            )
            for item in connectors
        )
    )
    results.append(
        _check(
            "CANON-006",
            "HIGH",
            "PASS" if paths_ok else "FAIL",
            "covered_external_paths_connect_pavilions",
            f"patio_connectors={len(connectors)}; residential_pavilions={len(residential)}; curved_routes={all(_centerline_is_curved(item) for item in connectors)}",
        )
    )

    service_access = getattr(layout, "service_access_point", None)
    service_access_separation = (
        float(service_access.distance(public_point))
        if service_access is not None and public_point is not None
        else 0.0
    )
    service_separated = (
        service is not None
        and admin is not None
        and service.footprint.disjoint(admin.footprint)
        and service_access is not None
        and service_access.distance(service.access_point) <= _GEOMETRY_TOLERANCE_M
        and service_access_separation > _SERVICE_ACCESS_MIN_SEPARATION_M
    )
    results.append(
        _check(
            "CANON-007",
            "HIGH",
            "PASS" if service_separated else "FAIL",
            "service_block_and_access_separated",
            f"service_to_public_access_m={service_access_separation:.3f}; required_gt_m={_SERVICE_ACCESS_MIN_SEPARATION_M:.1f}",
        )
    )

    green_spaces = tuple(
        item
        for item in externals
        if getattr(item, "component_id", None)
        in {"THERAPEUTIC_GARDEN", "PLAYGROUND", "HORTA", "EXERCISE"}
    )
    child_green_distance = (
        min(
            (child.footprint.distance(item.polygon) for item in green_spaces),
            default=math.inf,
        )
        if child is not None
        else math.inf
    )
    child_green_ok = (
        child is not None and child_green_distance <= _GREEN_ADJACENCY_MAX_DISTANCE_M
    )
    results.append(
        _check(
            "CANON-008",
            "HIGH",
            "PASS" if child_green_ok else "FAIL",
            "child_sector_interfaces_green",
            f"child_to_programmed_green_m={child_green_distance:.3f}; limit_m={_GREEN_ADJACENCY_MAX_DISTANCE_M:.1f}",
        )
    )

    expected_internal = float(profile.data["program"]["net_internal_m2"])
    expected_external = float(profile.data["program"]["external_programmed_m2"])
    rooms = tuple(getattr(layout, "rooms", ()))
    room_ids = [getattr(room, "logical_id", None) for room in rooms]
    internal_actual = sum(float(getattr(room, "net_area_m2", 0.0)) for room in rooms)
    external_actual = sum(_area(item) for item in externals)
    accounting = getattr(layout, "accounting", {})
    reconciled = (
        isinstance(accounting, Mapping)
        and len(room_ids) == len(set(room_ids))
        and math.isclose(internal_actual, expected_internal, abs_tol=1e-6)
        and math.isclose(external_actual, expected_external, abs_tol=1e-6)
        and math.isclose(
            float(accounting.get("net_internal_m2", math.nan)),
            expected_internal,
            abs_tol=1e-6,
        )
        and math.isclose(
            float(accounting.get("external_programmed_m2", math.nan)),
            expected_external,
            abs_tol=1e-6,
        )
    )
    results.append(
        _check(
            "CANON-009",
            "CRITICAL",
            "PASS" if reconciled else "FAIL",
            "official_program_reconciled",
            f"internal_m2={internal_actual:.3f}/{expected_internal:.3f}; external_m2={external_actual:.3f}/{expected_external:.3f}; unique_room_ids={len(room_ids) == len(set(room_ids))}",
        )
    )

    deviations = parameters.get("canonical_deviations")
    deviations_registered = isinstance(deviations, (list, tuple)) and all(
        isinstance(item, Mapping)
        and all(item.get(key) for key in ("id", "description", "basis", "evidence"))
        and item.get("basis") in _ALLOWED_DEVIATION_BASES
        for item in deviations
    )
    results.append(
        _check(
            "CANON-010",
            "CRITICAL",
            "PASS" if deviations_registered else "FAIL",
            "all_material_deviations_registered",
            f"deviation_register_present={isinstance(deviations, (list, tuple))}; material_deviations={len(deviations) if isinstance(deviations, (list, tuple)) else 'unknown'}",
        )
    )

    visual = parameters.get("visual_regression")
    visual_by_stage = (
        {item.get("stage"): item for item in visual if isinstance(item, Mapping)}
        if isinstance(visual, (list, tuple))
        else {}
    )
    hashes_match = (
        len(profile.source_hashes) == 3
        and len(profile.canonical_images) == 3
        and all(len(value) == 64 for value in profile.source_hashes)
    )
    visual_pass = (
        set(visual_by_stage) >= set(_REQUIRED_VISUAL_STAGES)
        and hashes_match
        and all(
            visual_by_stage[stage].get("status") == "PASS"
            and set(visual_by_stage[stage].get("source_hashes", ()))
            == set(profile.source_hashes)
            for stage in _REQUIRED_VISUAL_STAGES
        )
    )
    visual_status: CheckStatus = "PASS" if visual_pass else "BLOCKED"
    results.append(
        _check(
            "CANON-011",
            "HIGH",
            visual_status,
            "plan_preview_visually_corresponds_to_canonical_references",
            f"reviewed_stages={sorted(set(visual_by_stage) & set(_REQUIRED_VISUAL_STAGES))}; required_stages={list(_REQUIRED_VISUAL_STAGES)}; board_hashes_match={hashes_match}",
        )
    )

    geometry_origin = parameters.get("geometry_origin")
    obsolete_reused = parameters.get("superseded_source_reused")
    no_obsolete_base = (
        geometry_origin == "CANONICAL_PAVILION_RECONSTRUCTION"
        and obsolete_reused is False
    )
    results.append(
        _check(
            "CANON-012",
            "CRITICAL",
            "PASS" if no_obsolete_base else "FAIL",
            "obsolete_linear_geometry_not_used_as_final_base",
            f"geometry_origin={geometry_origin}; superseded_source_reused={obsolete_reused}",
        )
    )
    return results


__all__ = ["CanonicalCheck", "CheckStatus", "run_canonical_checks"]
