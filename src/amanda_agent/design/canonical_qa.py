"""Canonical parti checks; normalized-frame tolerances are not site constraints."""

from __future__ import annotations

import math
import re
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
_SERVICE_ENTRY_MIN_SEPARATION_M = 12.0
_SERVICE_COURTYARD_MAX_DISTANCE_M = 2.0
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
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


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


def _deviations_are_well_formed(
    layout: object,
    profile: CanonicalReferenceProfile,
    deviations: object,
) -> bool:
    if not isinstance(deviations, (list, tuple)):
        return False
    parameters = _parameters(layout)
    program_hash = parameters.get("program_source_sha256")
    output_hash = getattr(layout, "content_hash", None)
    if not isinstance(program_hash, str) or not _SHA256_PATTERN.fullmatch(program_hash):
        return False
    if not isinstance(output_hash, str) or not _SHA256_PATTERN.fullmatch(output_hash):
        return False
    current_board_hashes = {
        image.rsplit("/", maxsplit=1)[-1]: digest
        for image, digest in zip(
            profile.canonical_images, profile.source_hashes, strict=True
        )
    }
    expected_program_ref = (
        "docs/source/programa_necessidades.pdf#sha256=" + program_hash
    )
    required_fields = (
        "id",
        "description",
        "basis",
        "evidence",
        "affected_element",
        "reason",
        "impact",
        "decision_status",
    )
    for item in deviations:
        if not isinstance(item, Mapping):
            return False
        if not all(item.get(field) for field in required_fields):
            return False
        if item.get("basis") not in _ALLOWED_DEVIATION_BASES:
            return False
        alternatives = item.get("alternatives_considered")
        if not isinstance(alternatives, (list, tuple)) or not alternatives or not all(
            isinstance(value, str) and value.strip() for value in alternatives
        ):
            return False
        board_references = item.get("board_reference")
        if not isinstance(board_references, (list, tuple)) or not board_references:
            return False
        board_hashes: list[str] = []
        for reference in board_references:
            if not isinstance(reference, str) or "#sha256=" not in reference:
                return False
            board_name, digest = reference.rsplit("#sha256=", maxsplit=1)
            image_name = board_name.rsplit("/", maxsplit=1)[-1]
            if current_board_hashes.get(image_name) != digest:
                return False
            board_hashes.append(digest)
        input_hashes = item.get("input_hashes")
        if not isinstance(input_hashes, (list, tuple)) or not all(
            isinstance(value, str) and _SHA256_PATTERN.fullmatch(value)
            for value in input_hashes
        ):
            return False
        if set(input_hashes) != {*board_hashes, program_hash}:
            return False
        if item.get("program_reference") != expected_program_ref:
            return False
        if item.get("output_hash") != output_hash:
            return False
        if item.get("id") == "BOARD03-SCHEMATIC-BATHROOM-COUNT" and not (
            item.get("board_common_cell_count") == 6
            and item.get("official_common_room_count") == 5
            and item.get("modeled_common_room_count") == 5
        ):
            return False
    return True


def run_canonical_checks(
    layout: object, profile: CanonicalReferenceProfile
) -> list[CanonicalCheck]:
    """Return canonical reconciliation results without hiding blocked gates."""
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
        and service_access.distance(service.footprint) <= _GEOMETRY_TOLERANCE_M
        and service_access.distance(service.access_point)
        > _SERVICE_ENTRY_MIN_SEPARATION_M
        and service_access_separation > _SERVICE_ACCESS_MIN_SEPARATION_M
    )
    results.append(
        _check(
            "CANON-007",
            "HIGH",
            "PASS" if service_separated else "FAIL",
            "service_block_and_access_separated",
            f"cargo_to_campus_public_m={service_access.distance(service.access_point) if service_access is not None and service is not None else math.inf:.3f}; cargo_to_site_public_m={service_access_separation:.3f}; required_cargo_to_site_public_gt_m={_SERVICE_ACCESS_MIN_SEPARATION_M:.1f}",
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
    deviations_registered = _deviations_are_well_formed(layout, profile, deviations)
    expected_deviation_ids = {
        "BOARD02-SEC05-SUPPORT-PLACEMENT",
        "BOARD02-ARCHIVE-DUPLICATE-LABEL",
        "BOARD03-SCHEMATIC-BATHROOM-COUNT",
        "BOARD04-UNPRICED-FUNCTIONS",
        "BOARD04-AREA-AND-QUANTITY-MISMATCHES",
        "BOARD04-OFFICIAL-SUPPORT-ROOMS",
        "BOARD04-GARDEN-LABEL-IS-UNMETERED",
    }
    registered_deviation_ids = (
        {
            str(item.get("id"))
            for item in deviations
            if isinstance(item, Mapping)
        }
        if isinstance(deviations, (list, tuple))
        else set()
    )
    all_known_differences_registered = expected_deviation_ids <= registered_deviation_ids
    results.append(
        _check(
            "CANON-010",
            "CRITICAL",
            "PASS"
            if deviations_registered and all_known_differences_registered
            else "FAIL",
            "all_material_deviations_registered",
            f"registered={sorted(registered_deviation_ids)}; required={sorted(expected_deviation_ids)}",
        )
    )

    visual = parameters.get("visual_regression")
    visual_by_stage = (
        {item.get("stage"): item for item in visual if isinstance(item, Mapping)}
        if isinstance(visual, (list, tuple))
        else {}
    )
    hashes_match = (
        len(profile.source_hashes) == 4
        and len(profile.canonical_images) == 4
        and len(set(profile.source_hashes)) == 4
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

    hashes_bound = (
        len(profile.source_hashes) == 4
        and len(profile.canonical_images) == 4
        and len(set(profile.source_hashes)) == 4
        and all(len(value) == 64 for value in profile.source_hashes)
        and tuple(parameters.get("canonical_source_hashes", ()))
        == tuple(profile.source_hashes)
    )
    results.append(
        _check(
            "CANON-013",
            "CRITICAL",
            "PASS" if hashes_bound else "FAIL",
            "exactly_four_canonical_sources_are_bound",
            f"images={len(profile.canonical_images)}; hashes={len(profile.source_hashes)}; layout_matches_profile={tuple(parameters.get('canonical_source_hashes', ())) == tuple(profile.source_hashes)}",
        )
    )

    therapeutic = _component(externals, "THERAPEUTIC_GARDEN")
    horta = _component(externals, "HORTA")
    residential_y = (
        sum(float(block.footprint.centroid.y) for block in residential)
        / len(residential)
        if residential
        else -math.inf
    )
    implantation_ok = (
        admin is not None
        and service is not None
        and child is not None
        and therapeutic is not None
        and horta is not None
        and admin.footprint.centroid.y < therapeutic.polygon.centroid.y
        < residential_y
        and abs(float(therapeutic.polygon.centroid.x)) <= 10.0
        and child.footprint.centroid.x < therapeutic.polygon.centroid.x
        and service.footprint.centroid.x > therapeutic.polygon.centroid.x
        and service.footprint.centroid.y < therapeutic.polygon.centroid.y
        and horta.polygon.centroid.x > service.footprint.centroid.x
        and public_point is not None
        and public_point.y < admin.footprint.centroid.y
    )
    results.append(
        _check(
            "CANON-014",
            "CRITICAL",
            "PASS" if implantation_ok else "FAIL",
            "four_board_implantation_zones_and_access_gradient",
            f"admin_y={admin.footprint.centroid.y if admin is not None else math.nan:.3f}; garden_y={therapeutic.polygon.centroid.y if therapeutic is not None else math.nan:.3f}; residential_mean_y={residential_y:.3f}; child_west={child is not None and child.footprint.centroid.x < 0}; services_southeast={service is not None and service.footprint.centroid.x > 0 and service.footprint.centroid.y < 0}; horta_east={horta is not None and horta.polygon.centroid.x > 0}; public_entry_south={public_point is not None and admin is not None and public_point.y < admin.footprint.centroid.y}",
        )
    )

    admin_levels_by_room = {
        str(room.logical_id): int(room.level)
        for room in getattr(admin, "rooms", ())
    } if admin is not None else {}
    ground_admin_ids = {
        *(f"REQ-01-{number:02}" for number in range(1, 6)),
        *(f"REQ-04-{number:02}" for number in range(1, 5)),
        "REQ-04-06",
        "REQ-05-03",
        "REQ-05-04",
    }
    upper_admin_ids = {
        "REQ-04-05",
        *(f"REQ-06-{number:02}" for number in range(1, 6)),
    }
    admin_program_ok = (
        set(admin_levels_by_room) == ground_admin_ids | upper_admin_ids
        and all(admin_levels_by_room.get(room_id) == 1 for room_id in ground_admin_ids)
        and all(admin_levels_by_room.get(room_id) == 2 for room_id in upper_admin_ids)
    )
    results.append(
        _check(
            "CANON-015",
            "CRITICAL",
            "PASS" if admin_program_ok else "FAIL",
            "administrative_program_matches_official_floor_schedule",
            f"ground_expected={len(ground_admin_ids)}; upper_expected={len(upper_admin_ids)}; room_ids_exact={set(admin_levels_by_room) == ground_admin_ids | upper_admin_ids}",
        )
    )

    residential_membership = {
        "RES_PAV_A": {
            "REQ-02-01#1", "REQ-02-01#2", "REQ-02-02#1", "REQ-02-02#2",
            "REQ-02-06#1", "REQ-02-06#2",
        },
        "RES_PAV_B": {
            "REQ-02-03#1", "REQ-02-03#2", "REQ-02-04", "REQ-02-06#3", "REQ-02-06#4",
        },
        "RES_PAV_C": {
            "REQ-02-02#3", "REQ-02-05", "REQ-02-06#5", "REQ-02-07",
        },
        "RES_PAV_D_COMMUNAL": {"REQ-02-08", "REQ-02-09", "REQ-02-10"},
    }
    actual_residential = {
        str(block.component_id): {
            str(room.logical_id) for room in getattr(block, "rooms", ())
        }
        for block in residential
    }
    residential_program_ok = actual_residential == residential_membership
    results.append(
        _check(
            "CANON-016",
            "CRITICAL",
            "PASS" if residential_program_ok else "FAIL",
            "four_residential_pavilions_have_official_sleeping_and_communal_rooms",
            f"room_membership_exact={residential_program_ok}; sleeping_pavilions={sum(component_id in actual_residential for component_id in ('RES_PAV_A', 'RES_PAV_B', 'RES_PAV_C'))}; communal_rooms={sorted(actual_residential.get('RES_PAV_D_COMMUNAL', set()))}",
        )
    )

    service_courtyard = getattr(layout, "service_courtyard", None)
    service_public_access = getattr(layout, "service_public_access_point", None)
    service_ids = {
        "REQ-05-01",
        "REQ-05-02",
        *(f"REQ-06-{number:02}" for number in range(6, 16)),
    }
    actual_service_ids = {
        str(room.logical_id) for room in getattr(service, "rooms", ())
    } if service is not None else set()
    loading_room = next(
        (
            room
            for room in getattr(service, "rooms", ())
            if getattr(room, "logical_id", None) == "REQ-06-14"
        ),
        None,
    ) if service is not None else None
    service_shape_ok = (
        service is not None
        and getattr(service.footprint, "geom_type", None) == "Polygon"
        and len(service.footprint.exterior.coords) > 20
    )
    service_court_ok = (
        service_courtyard is not None
        and not service_courtyard.is_empty
        and service_courtyard.area > 0.0
        and service is not None
        and service_courtyard.disjoint(service.footprint)
        and service_courtyard.distance(service.footprint)
        <= _SERVICE_COURTYARD_MAX_DISTANCE_M
    )
    separate_service_entries = (
        service_access is not None
        and service_public_access is not None
        and service is not None
        and service_public_access.distance(service.footprint)
        <= 15.0
        and service_access.distance(service.footprint)
        <= _GEOMETRY_TOLERANCE_M
        and service_access.distance(service_public_access)
        > _SERVICE_ENTRY_MIN_SEPARATION_M
        and loading_room is not None
        and service_access.distance(loading_room.polygon) <= 8.0
    )
    courtyard_excluded_from_program = (
        service_courtyard is not None
        and all(not service_courtyard.equals(item.polygon) for item in externals)
    )
    service_program_ok = (
        actual_service_ids == service_ids
        and service_shape_ok
        and service_court_ok
        and separate_service_entries
        and courtyard_excluded_from_program
    )
    results.append(
        _check(
            "CANON-017",
            "CRITICAL",
            "PASS" if service_program_ok else "FAIL",
            "curved_service_court_official_program_and_split_entries",
            f"official_service_room_ids_exact={actual_service_ids == service_ids}; curved_shape={service_shape_ok}; court_disjoint_nearby={service_court_ok}; campus_and_cargo_entries_separate={separate_service_entries}; court_excluded_from_external_program={courtyard_excluded_from_program}",
        )
    )

    child_ids = {"REQ-03-01", "REQ-03-02", "REQ-03-03", "REQ-03-04"}
    actual_child_ids = {
        str(room.logical_id) for room in getattr(child, "rooms", ())
    } if child is not None else set()
    child_playground_distance = (
        float(child.footprint.distance(_component(externals, "PLAYGROUND").polygon))
        if child is not None and _component(externals, "PLAYGROUND") is not None
        else math.inf
    )
    child_content_ok = (
        actual_child_ids == child_ids
        and child_playground_distance <= _GREEN_ADJACENCY_MAX_DISTANCE_M
    )
    results.append(
        _check(
            "CANON-018",
            "HIGH",
            "PASS" if child_content_ok else "FAIL",
            "child_sector_program_and_playground_relation",
            f"official_child_room_ids_exact={actual_child_ids == child_ids}; child_to_playground_m={child_playground_distance:.3f}; limit_m={_GREEN_ADJACENCY_MAX_DISTANCE_M:.1f}",
        )
    )
    return results


__all__ = ["CanonicalCheck", "CheckStatus", "run_canonical_checks"]
