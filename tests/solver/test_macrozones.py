from __future__ import annotations

from shapely.geometry import box

from amanda_agent.design.macrozones import solve_macrozones

SITE = box(0, 0, 30, 20)
REQUIREMENTS = {
    "sectors": [
        {"logical_id": "public", "spaces": [{"target_area_m2": 80, "quantity": 1}]},
        {"logical_id": "controlled", "spaces": [{"target_area_m2": 80, "quantity": 1}]},
        {"logical_id": "residential", "spaces": [{"target_area_m2": 80, "quantity": 1}]},
    ],
    "relations": [
        {"source_logical_id": "public", "target_logical_id": "controlled", "relation": "MUST_ADJOIN", "weight": 1},
        {"source_logical_id": "controlled", "target_logical_id": "residential", "relation": "MUST_ADJOIN", "weight": 1},
    ],
}


def test_three_sector_cp_sat_solution_is_revalidated_as_shapely_geometry():
    result = solve_macrozones(REQUIREMENTS, SITE, seed=17, region_count=3)

    assert result.status in {"OPTIMAL", "FEASIBLE"}
    assert set(result.assignment) == {"public", "controlled", "residential"}
    assert result.assignment_order == sorted(result.assignment_order)
    assert all(SITE.covers(item["geometry"]) for item in result.sectors)
    assert result.geometry_valid is True
    assert result.solver_seed == 17


def test_same_seed_produces_same_assignment_and_order():
    first = solve_macrozones(REQUIREMENTS, SITE, seed=29, region_count=3)
    second = solve_macrozones(REQUIREMENTS, SITE, seed=29, region_count=3)

    assert first.assignment == second.assignment
    assert first.assignment_order == second.assignment_order
    assert first.geometry_hash == second.geometry_hash


def test_infeasible_capacity_keeps_solver_evidence_separate_from_geometry_checks():
    result = solve_macrozones(REQUIREMENTS, box(0, 0, 10, 10), seed=3, region_count=3)

    assert result.status == "INFEASIBLE"
    assert result.infeasibility_evidence
    assert result.geometry_valid is None


def test_wall_clock_unknown_is_not_reported_as_infeasibility(monkeypatch):
    from ortools.sat.python import cp_model

    from amanda_agent.design import macrozones

    monkeypatch.setattr(cp_model.CpSolver, "Solve", lambda self, model: cp_model.UNKNOWN)

    result = macrozones.solve_macrozones(REQUIREMENTS, SITE, seed=5, region_count=3)

    assert result.status == "UNKNOWN"
    assert result.solver_status == "UNKNOWN"
    assert result.infeasibility_evidence == []
    assert result.solver_evidence
