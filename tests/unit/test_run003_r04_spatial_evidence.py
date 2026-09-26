from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = (
    ROOT
    / "revit"
    / "production"
    / "evidence"
    / "AMANDA-RUN-003-R04"
    / "r04-spatial-model-evidence.json"
)
SOLUTION_ID = "AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"
LAYOUT_HASH = "7fde3e34a162167ce27fe2e3158a38f446882816a7c81bb326d486bdfaaae2e2"
MASS_NAMES = {
    "MASS-ADMIN_ACOLHIMENTO",
    "MASS-CHILD_SECTOR",
    "MASS-RES_PAV_A",
    "MASS-RES_PAV_B",
    "MASS-RES_PAV_C",
    "MASS-RES_PAV_D_COMMUNAL",
    "MASS-SERVICE_CAPACITATION",
}
SITE_REQUIREMENTS = {
    "SITE-PROTECTED-PATIO": "REQ-07-01",
    "SITE-THERAPEUTIC-GARDEN": "REQ-07-02",
    "SITE-HORTA": "REQ-07-03",
    "SITE-EXERCISE": "REQ-07-04",
    "SITE-PLAYGROUND": "REQ-07-05",
}
CONNECTORS = {
    "COVERED-RES_PAV_A-TO-PROTECTED_PATIO",
    "COVERED-RES_PAV_B-TO-PROTECTED_PATIO",
    "COVERED-RES_PAV_C-TO-PROTECTED_PATIO",
    "COVERED-RES_PAV_D_COMMUNAL-TO-PROTECTED_PATIO",
}
ACCESS_ROUTES = {
    "PATH-PUBLIC-ADMIN",
    "PATH-PUBLIC-SERVICE",
    "PATH-SERVICE-CARGO",
}


def _bbox_disjoint(first: dict, second: dict) -> bool:
    return any(
        first["max"][axis] <= second["min"][axis]
        or second["max"][axis] <= first["min"][axis]
        for axis in (0, 1)
    )


def test_run003_r04_spatial_readback_matches_canonical_mass_and_site_geometry():
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    program_sha = hashlib.sha256(
        (ROOT / "docs" / "source" / "programa_necessidades.pdf").read_bytes()
    ).hexdigest()
    identity = json.loads(
        (ROOT / "project" / "requirements" / "program.json").read_text(
            encoding="utf-8"
        )
    )
    official_external_areas = {
        space["logical_id"]: float(space["total_area_m2"])
        for sector in identity["sectors"]
        for space in sector["spaces"]
        if space["area_kind"] == "EXTERNAL"
    }
    canonical_board_paths = [
        ROOT / "docs" / "source" / "canonical" / name
        for name in evidence["source"]["canonical_board_order"]
    ]
    canonical_board_hashes = [
        hashlib.sha256(path.read_bytes()).hexdigest() for path in canonical_board_paths
    ]
    geometry_path = ROOT / evidence["source"]["source_geometry_path"]

    assert evidence["status"] == "PASS_WITH_WARNINGS"
    assert evidence["run"] == "RUN-003"
    assert evidence["stage"] == "R04"
    assert evidence["source"]["solution_id"] == SOLUTION_ID
    assert evidence["source"]["layout_hash"] == LAYOUT_HASH
    assert evidence["source"]["official_program_sha256"] == program_sha
    assert evidence["source"]["official_program_sha256"] == identity["baseline"]["source_sha256"]
    assert len(evidence["source"]["canonical_board_sha256"]) == 4
    assert evidence["source"]["canonical_board_order"] == [
        "01_implantacao.png",
        "02_administrativo.png",
        "03_residencial.png",
        "04_servicos.png",
    ]
    assert evidence["source"]["canonical_board_sha256"] == canonical_board_hashes
    assert hashlib.sha256(geometry_path.read_bytes()).hexdigest() == evidence["source"]["source_geometry_sha256"]
    assert evidence["source"]["coordinate_mode"] == "LOCAL_NORMALIZED_STUDY_NOT_SURVEYED"
    assert evidence["source"]["historical_geometry_reused"] is False

    live = evidence["live"]
    assert live["provider"] == "horizun"
    assert live["provider_status"] == "healthy"
    assert live["registry_clean"] is True
    assert live["registry_registered_commands"] == 73
    assert live["registry_contract_commands"] == 73
    assert live["tools_visible"] == live["tools_total"] == 80
    assert live["revit_build"] == "27.2.0.39"
    assert live["target_document"].endswith(
        "AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt"
    )
    assert live["writer_lease_owner"] == "amanda-P6-T01-RUN003-CANON-011"
    assert live["writer_lease_status"] == "released_after_verification"
    assert live["other_clients_connected"] == 0
    assert evidence["write"]["transaction_status"] == "Committed"
    assert evidence["write"]["committed_and_independently_re_read"] == 18
    assert evidence["write"]["additions"] == {"floors": 14, "roofs": 4, "total": 18}
    assert evidence["write"]["r05_performed"] is False
    assert evidence["write"]["rc01_modified"] is False

    readback = evidence["readback"]
    assert readback["phase"] == "POST_P6_SAVE_COLD_REOPEN"
    assert readback["coverage_complete"] is True
    assert readback["unreadable_total"] == 0
    assert readback["post_reopen_object_count"] == 25
    assert set(readback["mass_names"]) == MASS_NAMES
    assert readback["mass_count"] == 7
    assert readback["administrative_storey_levels"] == {
        "1": {"level_id": 311, "elevation_m": pytest.approx(0.0)},
        "2": {"level_id": 694, "elevation_m": pytest.approx(4.0)},
    }
    assert readback["administrative_floor_reference_elevations_m"] == {
        "R04-ADMIN-FLOOR-L1": pytest.approx(0.0),
        "R04-ADMIN-FLOOR-L2": pytest.approx(4.0),
    }
    assert readback["administrative_floor_element_ids"] == {
        "R04-ADMIN-FLOOR-L1": 331163,
        "R04-ADMIN-FLOOR-L2": 331170,
    }
    assert readback["administrative_mass_element_id"] == 328657
    assert readback["administrative_public_route_element_id"] == 331177
    assert readback["administrative_floor_l2_level_offset_m"] == pytest.approx(0.0)
    assert readback["administrative_function_assignments_modeled"] is False
    assert readback["administrative_footprint_per_floor_m2"] == pytest.approx(200.0)
    assert readback["administrative_footprint_measurement"]["method"] == "HOST_AREA_COMPUTED"
    assert readback["administrative_footprint_measurement"]["area_m2"] == pytest.approx(200.0)
    assert readback["administrative_board_approx_area_per_floor_m2"] == pytest.approx(200.0)
    admin_bounds = readback["mass_bboxes_m"]["MASS-ADMIN_ACOLHIMENTO"]
    assert admin_bounds["min"][0] == pytest.approx(-5.0)
    assert admin_bounds["max"][0] == pytest.approx(5.0)
    assert admin_bounds["min"][1] == pytest.approx(-52.0)
    assert admin_bounds["max"][1] == pytest.approx(-32.0)
    assert readback["access_routes"]["bounds_m"]["PATH-PUBLIC-ADMIN"]["max"][1] == pytest.approx(
        admin_bounds["min"][1]
    )
    assert set(readback["administrative_floor_marks"]) == {
        "R04-ADMIN-FLOOR-L1",
        "R04-ADMIN-FLOOR-L2",
    }
    assert readback["residential_pavilion_count"] == 4
    assert readback["residential_pavilion_names"] == sorted(
        ["MASS-RES_PAV_A", "MASS-RES_PAV_B", "MASS-RES_PAV_C", "MASS-RES_PAV_D_COMMUNAL"]
    )
    assert readback["service_form"] == "CURVED_COURTYARD"
    assert readback["service_interior_ring_count"] == 6

    site_surfaces = readback["site_surfaces"]
    assert {row["mark"] for row in site_surfaces["items"]} == set(SITE_REQUIREMENTS)
    assert {
        row["mark"]: row["requirement_id"] for row in site_surfaces["items"]
    } == SITE_REQUIREMENTS
    measured_external_areas = {
        row["requirement_id"]: row["area_m2"] for row in site_surfaces["items"]
    }
    assert measured_external_areas.keys() == official_external_areas.keys()
    for requirement_id, official_area in official_external_areas.items():
        assert measured_external_areas[requirement_id] == pytest.approx(official_area)
    assert site_surfaces["official_program_total_m2"] == pytest.approx(
        identity["totals"]["external_programmed_m2"]
    )
    assert sum(row["area_m2"] for row in site_surfaces["items"]) == pytest.approx(
        site_surfaces["official_program_total_m2"]
    )
    assert site_surfaces["official_program_total_m2"] == pytest.approx(260.0)
    assert site_surfaces["area_authority"] == "docs/source/programa_necessidades.pdf"
    assert site_surfaces["board_printed_areas_used_as_official"] is False
    assert readback["child_functional_rooms_modeled"] is False
    assert readback["service_functional_area_assignments_modeled"] is False

    connectors = readback["covered_connectors"]
    assert set(connectors["ids"]) == CONNECTORS
    assert connectors["floor_count"] == 4
    assert connectors["roof_count"] == 4
    assert connectors["enclosing_wall_count"] == 0
    assert len(connectors["floor_marks"]) == 4
    assert len(connectors["roof_marks"]) == 4
    assert set(connectors["patio_interfaces_m"]) == CONNECTORS
    assert all(
        width == pytest.approx(2.0)
        for width in connectors["patio_interfaces_m"].values()
    )
    assert connectors["patio_intrusion_area_m2"] == pytest.approx(0.0, abs=1e-7)

    routes = readback["access_routes"]
    assert set(routes["marks"]) == ACCESS_ROUTES
    assert len(routes["marks"]) == 3
    assert _bbox_disjoint(
        routes["bounds_m"]["PATH-PUBLIC-SERVICE"],
        routes["bounds_m"]["PATH-SERVICE-CARGO"],
    )
    assert _bbox_disjoint(
        routes["bounds_m"]["PATH-PUBLIC-ADMIN"],
        routes["bounds_m"]["PATH-SERVICE-CARGO"],
    )
    assert routes["public_and_cargo_separate"] is True
    assert routes["widths_are_study_assumptions"] is True
    assert routes["widths_m"] == {
        "PATH_PUBLIC_ADMIN": pytest.approx(2.0),
        "PATH_PUBLIC_SERVICE": pytest.approx(2.0),
        "PATH_SERVICE_CARGO": pytest.approx(3.0),
    }
    assert routes["areas_excluded_from_official_program"] is True

    # Assert the cardinal relationships from measured post-reopen mass bounds,
    # rather than accepting booleans supplied by the evidence producer.
    bboxes = readback["mass_bboxes_m"]

    def center(name: str) -> tuple[float, float]:
        bounds = bboxes[name]
        return (
            (bounds["min"][0] + bounds["max"][0]) / 2,
            (bounds["min"][1] + bounds["max"][1]) / 2,
        )

    admin_center = center("MASS-ADMIN_ACOLHIMENTO")
    residential_centers = [center(name) for name in MASS_NAMES if name.startswith("MASS-RES_")]
    child_center = center("MASS-CHILD_SECTOR")
    service_center = center("MASS-SERVICE_CAPACITATION")
    patio_bounds = site_surfaces["bounds_m"]["SITE-PROTECTED-PATIO"]
    garden_center = (
        (site_surfaces["bounds_m"]["SITE-THERAPEUTIC-GARDEN"]["min"][0]
         + site_surfaces["bounds_m"]["SITE-THERAPEUTIC-GARDEN"]["max"][0]) / 2,
        (site_surfaces["bounds_m"]["SITE-THERAPEUTIC-GARDEN"]["min"][1]
         + site_surfaces["bounds_m"]["SITE-THERAPEUTIC-GARDEN"]["max"][1]) / 2,
    )
    horta_center = (
        (site_surfaces["bounds_m"]["SITE-HORTA"]["min"][0]
         + site_surfaces["bounds_m"]["SITE-HORTA"]["max"][0]) / 2,
        (site_surfaces["bounds_m"]["SITE-HORTA"]["min"][1]
         + site_surfaces["bounds_m"]["SITE-HORTA"]["max"][1]) / 2,
    )
    playground_center = (
        (site_surfaces["bounds_m"]["SITE-PLAYGROUND"]["min"][0]
         + site_surfaces["bounds_m"]["SITE-PLAYGROUND"]["max"][0]) / 2,
        (site_surfaces["bounds_m"]["SITE-PLAYGROUND"]["min"][1]
         + site_surfaces["bounds_m"]["SITE-PLAYGROUND"]["max"][1]) / 2,
    )
    child_bounds = bboxes["MASS-CHILD_SECTOR"]
    playground_bounds = site_surfaces["bounds_m"]["SITE-PLAYGROUND"]
    child_playground_gap_x = max(
        0.0,
        child_bounds["min"][0] - playground_bounds["max"][0],
        playground_bounds["min"][0] - child_bounds["max"][0],
    )
    child_playground_gap_y = max(
        0.0,
        child_bounds["min"][1] - playground_bounds["max"][1],
        playground_bounds["min"][1] - child_bounds["max"][1],
    )
    child_playground_clearance_m = math.hypot(
        child_playground_gap_x,
        child_playground_gap_y,
    )
    assert admin_center[1] < min(y for _, y in residential_centers)
    assert all(
        bboxes[name]["min"][1] > 0
        for name in MASS_NAMES
        if name.startswith("MASS-RES_")
    )
    assert child_center[0] < 0 < service_center[0]
    assert child_playground_clearance_m == pytest.approx(2.975765385825232)
    assert child_playground_clearance_m <= 3.0
    assert math.dist(child_center, playground_center) < 20
    assert min(x for x, _ in residential_centers) < 0 < max(x for x, _ in residential_centers)
    patio_center_y = (patio_bounds["min"][1] + patio_bounds["max"][1]) / 2
    assert min(y for _, y in residential_centers) < patio_center_y < max(
        y for _, y in residential_centers
    )
    assert min(child_center[0], service_center[0]) < garden_center[0] < max(
        child_center[0], service_center[0]
    )
    assert horta_center[0] > bboxes["MASS-SERVICE_CAPACITATION"]["max"][0]

    relations = readback["canonical_relations"]
    assert relations == {
        "administration_south_public_edge": True,
        "administration_two_levels": True,
        "residences_north_interior_four_independent_pavilions": True,
        "protected_residential_patio_free": True,
        "covered_external_semiopen_circulation": True,
        "services_southeast_curved_with_courtyard": True,
        "child_west_near_playground": True,
        "therapeutic_garden_central": True,
        "horta_east": True,
        "public_and_cargo_access_separate": True,
        "administrative_board_area_difference_open": False,
        "administrative_floor_levels_aligned": True,
        "administration_public_route_meets_south_entry": True,
    }
    assert evidence["open_gaps"]["canon_011"] is False
    assert evidence["open_gaps"]["r05_authorized"] is True
    assert evidence["p6_acceptance"]["status"] == "PASS"
    assert evidence["p6_acceptance"]["scope"] == "NORMALIZED_STUDY_SPATIAL_TOPOLOGY"
    assert evidence["p6_acceptance"]["rooms_deferred_to"] == "R06"
    assert evidence["p6_acceptance"]["room_area_readback_deferred_to"] == "R08"
    assert evidence["p6_acceptance"]["site_claims_status"] == "LIMITED_TO_SURVEYED_DATA"
    prior_review = evidence["independent_review"]
    assert prior_review["status"] == "SUPERSEDED_BY_SCOPED_P6_ACCEPTANCE"
    assert "room layout to R06" in prior_review["conclusion"]
    assert "area readback to R08" in prior_review["conclusion"]
    assert evidence["p6_acceptance"]["independent_review"]["status"] == (
        "PASS_NORMALIZED_STUDY_TOPOLOGY"
    )
    assert evidence["open_gaps"]["administrative_board_area_difference"] is False
    assert evidence["open_gaps"]["administrative_level_vs_plate_elevation"] is False
    assert evidence["open_gaps"]["service_function_reconciliation"] is False
    assert evidence["open_gaps"]["child_function_reconciliation"] is False
    assert evidence["persistence"]["saved"] is True
    assert evidence["persistence"]["checkpoint_manifest_verified"] is True
    assert evidence["persistence"]["closed_and_reopened_exact_target"] is True
    assert evidence["persistence"]["model_sha256"] == "8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326"
    assert evidence["persistence"]["checkpoint_path"].endswith(
        "P6-T01-CANON-011-RECONCILED-20260926.rvt"
    )
    manifest = json.loads(
        (ROOT / evidence["persistence"]["checkpoint_manifest_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert manifest["sha256"] == evidence["persistence"]["checkpoint_sha256"]
    assert manifest["source_sha256"] == evidence["persistence"]["model_sha256"]
    assert manifest["provenance"]["save_sha256"] == evidence["persistence"]["model_sha256"]
    visual = evidence["visual_evidence"]
    assert visual["capture_status"] == "CAPTURED_SUPPORTING_ONLY"
    image_path = ROOT / visual["path"]
    assert hashlib.sha256(image_path.read_bytes()).hexdigest() == visual["sha256"]
    capture_manifest_path = ROOT / visual["capture_manifest_path"]
    capture_manifest = json.loads(capture_manifest_path.read_text(encoding="utf-8"))
    assert capture_manifest["source_checkpoint"]["sha256"] == evidence["persistence"]["checkpoint_sha256"]
    assert capture_manifest["source_readback"]["result_set_fingerprint"] == readback["result_set_fingerprint"]
    captures = {item["role"]: item for item in capture_manifest["captures"]}
    assert {"implantation_top", "administration_mass", "administration_ground_route", "administration_upper_floor", "residential", "services", "child_sector"} <= captures.keys()
    for item in captures.values():
        capture_path = ROOT / item["path"]
        assert hashlib.sha256(capture_path.read_bytes()).hexdigest() == item["sha256"]
        assert item["capture_checkpoint_sha256"] == evidence["persistence"]["checkpoint_sha256"]
        if item["temporary_options_used"]:
            assert item["view_restored"] is True
    relation = capture_manifest["reference_captures"]["child_playground_relation"]
    assert relation["source_checkpoint_sha256"] == "33a99c7c760125da434017210b7ea2d506a3914ae59e002769a14138cca27b49"
    assert set(relation["visible_element_ids"]) == {328658, 329971}
    relation_path = ROOT / relation["path"]
    assert hashlib.sha256(relation_path.read_bytes()).hexdigest() == relation["sha256"]
