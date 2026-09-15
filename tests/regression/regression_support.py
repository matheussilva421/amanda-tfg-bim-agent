"""Shared harness for the P04-T19 core regression fixtures.

Each fixture directory is pure data: input.json describes the scenario,
seed.json the seed declaration, expected_invariants.json the observed values
that must hold and expected_hash.json the canonical digest.  This module runs
the real engine in src/amanda_agent/design over a fixture and returns the
observed values together with the canonical payload that is hashed.

Nothing here re-implements the solver: every scenario calls the shipped modules
(macrozones, blocks, rooms, external spaces, environmental, scoring, pareto,
generation, pipeline, explain, constraints, flows, privacy) directly.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from shapely.geometry import box, mapping, shape  # type: ignore[import-untyped]

from amanda_agent.design.archetypes import generate_macro_seed
from amanda_agent.design.blocks import generate_blocks
from amanda_agent.design.constraints import hard_violations_only, validate_candidate
from amanda_agent.design.environmental import evaluate_environmental_heuristics
from amanda_agent.design.explain import explain_candidate
from amanda_agent.design.external_spaces import (
    generate_external_spaces,
    validate_external_spaces,
)
from amanda_agent.design.flows import FlowPolicy, analyze_route, build_flow_graph
from amanda_agent.design.generate import canonical_geometry_hash
from amanda_agent.design.pareto import pareto_frontier
from amanda_agent.design.pipeline import run_pipeline
from amanda_agent.design.privacy import evaluate_privacy_gradient
from amanda_agent.design.rooms import refine_rooms
from amanda_agent.design.scoring import score_candidate
from amanda_agent.requirements.relations import FlowNetwork

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"

FIXTURE_NAMES: tuple[str, ...] = (
    "simple-3-room",
    "courtyard",
    "two-access",
    "privacy-gradient",
    "accessible-route",
)

#: Engine areas the regression set is required to exercise (plan P04-T19).
REQUIRED_ENGINE_AREAS: frozenset[str] = frozenset(
    {
        "macrozones",
        "blocks",
        "rooms",
        "external_spaces",
        "scoring",
        "pareto",
        "environmental",
        "generation",
        "pipeline",
        "explain",
    }
)

FIXTURE_FILES: tuple[str, ...] = (
    "input.json",
    "seed.json",
    "expected_invariants.json",
    "expected_hash.json",
)


def fixture_dir(name: str) -> Path:
    return FIXTURE_ROOT / name


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return payload


def load_input(name: str) -> dict[str, Any]:
    return _read_json(fixture_dir(name) / "input.json")


def load_seed(name: str) -> dict[str, Any]:
    return _read_json(fixture_dir(name) / "seed.json")


def load_invariants(name: str) -> dict[str, Any]:
    return _read_json(fixture_dir(name) / "expected_invariants.json")


def load_expected_hash(name: str) -> dict[str, Any]:
    return _read_json(fixture_dir(name) / "expected_hash.json")


def site_polygon(spec: dict[str, Any]):
    """Build the site polygon from the fixture's declarative site spec."""

    bounds = spec.get("bounds")
    if not isinstance(bounds, list) or len(bounds) != 4:
        raise ValueError("site spec requires four numeric bounds")
    return box(*(float(value) for value in bounds))


def _route_report(analysis: Any) -> dict[str, Any]:
    return {
        "flow": analysis.flow.value,
        "connected": bool(analysis.connected),
        "ok": bool(analysis.ok),
        "path": [str(item) for item in analysis.path],
        "distance_m": (
            None
            if analysis.distance_m is None
            else round(float(analysis.distance_m), 6)
        ),
        "crossings": int(analysis.crossings),
        "violation_codes": sorted({item.code for item in analysis.violations}),
        "soft_penalty": round(float(analysis.soft_penalty), 6),
    }


def _evaluate_pipeline(
    data: dict[str, Any], seed_data: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    requirements = data["requirements"]
    site = site_polygon(data["site"])
    seeds = [int(value) for value in seed_data["seeds"]]

    result = run_pipeline(requirements, site, seeds=seeds, config=data.get("config"))

    finalists = list(result.stages["finalists"])
    finalist = finalists[0]
    final_rooms = list(finalist["rooms"])
    room_report = validate_candidate(
        {"resolution": "ROOM", "rooms": final_rooms}, requirements, mapping(site)
    )
    hard_codes = sorted({item.code for item in hard_violations_only(room_report)})
    macro_statuses = sorted({candidate.status for candidate in result.stages["macro"]})
    macro_hashes = [candidate.geometry_hash for candidate in result.stages["macro"]]

    observed = {
        "stage_order": list(result.stage_order),
        "counts": dict(result.counts),
        "revit_calls": int(result.revit_calls),
        "macro_candidate_statuses": macro_statuses,
        "macro_candidate_hash_count": len(set(macro_hashes)),
        "rejected_count": len(result.rejected),
        "rejections_all_have_reason": all(item.reason for item in result.rejected),
        "finalist_count": len(finalists),
        "finalist_room_ids": [str(room["logical_id"]) for room in final_rooms],
        "finalist_room_count": len(final_rooms),
        "finalist_accessible_room_ids": sorted(
            str(room["logical_id"]) for room in final_rooms if room["accessible"]
        ),
        "finalist_hard_violation_codes": hard_codes,
        "net_area_total_m2": round(
            sum(float(room["net_area_m2"]) for room in final_rooms), 6
        ),
        "seeds": seeds,
        "engine_evidence": {
            "generation": {
                "candidates": len(result.stages["macro"]),
                "distinct_geometry_hashes": len(set(macro_hashes)),
            },
            "pipeline": {
                "stage_order": list(result.stage_order),
                "stage_count": len(result.stages),
            },
            "macrozones": {"solver_statuses": macro_statuses},
            "blocks": {"block_count": len(finalist["blocks"])},
            "rooms": {
                "room_count": len(final_rooms),
                "accounting_keys": sorted(finalist["accounting"]),
            },
            "constraints": {
                "checked_rooms": len(final_rooms),
                "hard_violation_codes": hard_codes,
            },
        },
    }
    payload = {
        "fixture": data["fixture"],
        "stage_order": list(result.stage_order),
        "counts": dict(result.counts),
        "macro_candidate_hashes": macro_hashes,
        "finalist_rooms": [
            {
                "logical_id": str(room["logical_id"]),
                "net_area_m2": float(room["net_area_m2"]),
                "accessible": bool(room["accessible"]),
                "geometry": room["geometry"],
            }
            for room in final_rooms
        ],
    }
    return observed, payload


def _evaluate_courtyard(
    data: dict[str, Any], seed_data: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    site = site_polygon(data["site"])
    seed = int(seed_data["archetype_seed"])
    macro = generate_macro_seed(data["archetype"], site, seed=seed)
    external = generate_external_spaces(
        site, data["external_spaces"], privacy_policy=data["privacy_policy"]
    )
    external_check = validate_external_spaces(
        external.spaces, site, privacy_policy=data["privacy_policy"]
    )

    environmental_spec = data["environmental"]
    heuristics = evaluate_environmental_heuristics(
        environmental_spec,
        true_north_deg=float(environmental_spec["true_north_deg"]),
        preferred_solar_orientation_deg=float(
            environmental_spec["preferred_solar_orientation_deg"]
        ),
        wind_direction_deg=float(environmental_spec["wind_direction_deg"]),
    )

    green_area_m2 = sum(float(space["geometry"].area) for space in external.spaces)
    metrics = dict(data["metrics"])
    metrics["solar_heuristic"] = heuristics.solar_score
    metrics["ventilation_heuristic"] = heuristics.ventilation_score
    metrics["green_integration"] = green_area_m2 / float(site.area)
    score = score_candidate(metrics)

    frontier = pareto_frontier(
        data["pareto_candidates"], dimensions=data["pareto_dimensions"]
    )
    explanation = explain_candidate(data["explanation_candidate"])

    sectors = list(macro.sectors)
    courtyards = list(macro.courtyards)
    observed = {
        "archetype": macro.archetype.value,
        "archetype_seed": int(macro.seed),
        "sector_ids": [str(item["logical_id"]) for item in sectors],
        "sector_privacy_levels": [int(item["privacy_level"]) for item in sectors],
        "courtyard_count": len(courtyards),
        "courtyard_ids": [str(item["logical_id"]) for item in courtyards],
        "sectors_inside_site": all(
            site.covers(shape(item["geometry"])) for item in sectors
        ),
        "courtyards_inside_site": all(
            site.covers(shape(item["geometry"])) for item in courtyards
        ),
        "external_space_ids": [str(space["logical_id"]) for space in external.spaces],
        "external_space_kinds": [str(space["kind"]) for space in external.spaces],
        "external_space_areas_m2": [
            round(float(space["geometry"].area), 6) for space in external.spaces
        ],
        "external_violation_codes": sorted(
            {item.code for item in external.violations}
        ),
        "external_validation_codes": sorted(
            {item.code for item in external_check.violations}
        ),
        "used_leftover_as_garden": bool(external.used_leftover_as_garden),
        "heuristic_labels": dict(heuristics.labels),
        "solar_score": round(float(heuristics.solar_score), 6),
        "ventilation_score": round(float(heuristics.ventilation_score), 6),
        "weighted_total": round(float(score.weighted_total), 6),
        "not_evaluated_dimensions": sorted(score.not_evaluated),
        "scored_dimensions": sorted(score.contributions),
        "pareto_frontier_ids": [str(item["id"]) for item in frontier],
        "explanation_strengths": list(explanation.strengths),
        "explanation_tradeoffs": list(explanation.tradeoffs),
        "explanation_hard_violations": list(explanation.hard_violations),
        "engine_evidence": {
            "archetypes": {
                "archetype": macro.archetype.value,
                "sectors": len(sectors),
                "courtyards": len(courtyards),
            },
            "external_spaces": {
                "spaces": len(external.spaces),
                "violation_codes": sorted({item.code for item in external.violations}),
            },
            "environmental": {
                "labels": dict(heuristics.labels),
                "solar_score": round(float(heuristics.solar_score), 6),
            },
            "scoring": {
                "weighted_total": round(float(score.weighted_total), 6),
                "dimensions": len(score.contributions),
            },
            "pareto": {"frontier_size": len(frontier)},
            "explain": {
                "strengths": len(explanation.strengths),
                "tradeoffs": len(explanation.tradeoffs),
            },
        },
    }
    payload = {
        "fixture": data["fixture"],
        "archetype": macro.archetype.value,
        "sectors": [
            {
                "logical_id": str(item["logical_id"]),
                "privacy_level": int(item["privacy_level"]),
                "geometry": item["geometry"],
            }
            for item in sectors
        ],
        "courtyards": [
            {"logical_id": str(item["logical_id"]), "geometry": item["geometry"]}
            for item in courtyards
        ],
        "external_spaces": [
            {
                "logical_id": str(space["logical_id"]),
                "kind": str(space["kind"]),
                "privacy_level": space["privacy_level"],
                "target_area_m2": float(space["target_area_m2"]),
                "geometry": mapping(space["geometry"]),
            }
            for space in external.spaces
        ],
        "heuristics": {
            "solar": round(float(heuristics.solar_score), 6),
            "ventilation": round(float(heuristics.ventilation_score), 6),
        },
        "weighted_total": round(float(score.weighted_total), 6),
        "pareto_frontier_ids": [str(item["id"]) for item in frontier],
    }
    return observed, payload


def _evaluate_flows(
    data: dict[str, Any], seed_data: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    del seed_data  # flow routing is seed-independent
    layout = data["layout"]
    routes: dict[str, dict[str, Any]] = {}
    for spec in data["routes"]:
        graph = build_flow_graph(
            layout,
            FlowNetwork(spec["flow"]),
            min_width_m=float(spec.get("min_width_m", 0.9)),
        )
        analysis = analyze_route(
            graph,
            str(spec["start"]),
            str(spec["goal"]),
            policy=FlowPolicy(**spec.get("policy", {})),
        )
        routes[str(spec["id"])] = _route_report(analysis)

    observed = {
        "entry_nodes": [str(item) for item in data["entry_nodes"]],
        "entry_node_count": len(set(data["entry_nodes"])),
        "route_ids": sorted(routes),
        "routes": routes,
        "engine_evidence": {
            "flows": {
                "routes": len(routes),
                "visitor_route_ok": routes["visitor"]["ok"],
                "default_service_route_ok": routes["service-default-policy"]["ok"],
            }
        },
    }
    payload = {"fixture": data["fixture"], "routes": routes}
    return observed, payload


def _evaluate_privacy(
    data: dict[str, Any], seed_data: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    del seed_data  # privacy scoring is a pure function of the sequence
    sequences: dict[str, dict[str, Any]] = {}
    for spec in data["sequences"]:
        analysis = evaluate_privacy_gradient(spec["sequence"])
        sequences[str(spec["id"])] = {
            "valid": bool(analysis.valid),
            "penalty": round(float(analysis.penalty), 6),
            "score": round(float(analysis.score), 6),
            "transition_sequence": list(analysis.transition_sequence),
            "node_ids": [str(item) for item in analysis.evidence["node_ids"]],
            "direct_public_to_residential": bool(
                analysis.evidence["direct_public_to_residential"]
            ),
        }
    invalid = sorted(name for name, item in sequences.items() if not item["valid"])
    observed = {
        "sequence_ids": sorted(sequences),
        "sequences": sequences,
        "engine_evidence": {
            "privacy": {"sequences": len(sequences), "invalid_sequences": invalid}
        },
    }
    payload = {"fixture": data["fixture"], "sequences": sequences}
    return observed, payload


def _evaluate_accessible(
    data: dict[str, Any], seed_data: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    del seed_data  # deterministic geometry operations, no seed input
    site = site_polygon(data["site"])
    sector = data["sector"]
    demand = float(sector["demand_m2"])
    blocks = generate_blocks(
        [
            {
                "logical_id": str(sector["logical_id"]),
                "geometry": site,
                "demand_m2": demand,
            }
        ],
        min_width_m=0.5,
    )
    block = blocks.blocks[0]
    refined = refine_rooms(block, list(sector["spaces"]))
    requirements = {
        "sectors": [
            {
                "logical_id": str(sector["logical_id"]),
                "spaces": list(sector["spaces"]),
            }
        ]
    }
    room_report = validate_candidate(
        {"resolution": "ROOM", "rooms": refined.rooms}, requirements, mapping(site)
    )
    hard_codes = sorted({item.code for item in hard_violations_only(room_report)})

    routes: dict[str, dict[str, Any]] = {}
    for spec in data["accessible_routes"]:
        graph = build_flow_graph(
            data["layout"],
            FlowNetwork(spec["flow"]),
            min_width_m=float(spec["min_width_m"]),
        )
        analysis = analyze_route(graph, str(spec["start"]), str(spec["goal"]))
        routes[str(spec["id"])] = {
            "min_width_m": float(spec["min_width_m"]),
            **_route_report(analysis),
        }

    observed = {
        "block_count": len(blocks.blocks),
        "block_violation_codes": sorted({item.code for item in blocks.violations}),
        "room_ids": [str(room["logical_id"]) for room in refined.rooms],
        "room_count": len(refined.rooms),
        "accessible_room_ids": sorted(
            str(room["logical_id"]) for room in refined.rooms if room["accessible"]
        ),
        "room_net_area_total_m2": round(
            sum(float(room["net_area_m2"]) for room in refined.rooms), 6
        ),
        "room_refinement_violation_codes": sorted(
            {item.code for item in refined.violations}
        ),
        "room_hard_violation_codes": hard_codes,
        "routes": routes,
        "engine_evidence": {
            "blocks": {
                "block_count": len(blocks.blocks),
                "violation_codes": sorted({item.code for item in blocks.violations}),
            },
            "rooms": {
                "room_count": len(refined.rooms),
                "accounting_keys": sorted(refined.accounting),
            },
            "constraints": {
                "checked_rooms": len(refined.rooms),
                "hard_violation_codes": hard_codes,
            },
            "flows": {
                "routes": len(routes),
                "accessible_width_route_ok": routes["to-therapy-accessible-width"]["ok"],
            },
        },
    }
    payload = {
        "fixture": data["fixture"],
        "rooms": [
            {
                "logical_id": str(room["logical_id"]),
                "net_area_m2": float(room["net_area_m2"]),
                "accessible": bool(room["accessible"]),
                "geometry": room["geometry"],
            }
            for room in refined.rooms
        ],
        "routes": routes,
    }
    return observed, payload


ScenarioEvaluator = Callable[
    [dict[str, Any], dict[str, Any]], tuple[dict[str, Any], dict[str, Any]]
]

_EVALUATORS: dict[str, ScenarioEvaluator] = {
    "pipeline": _evaluate_pipeline,
    "courtyard": _evaluate_courtyard,
    "flows": _evaluate_flows,
    "privacy": _evaluate_privacy,
    "accessible": _evaluate_accessible,
}


def evaluate_fixture(name: str) -> dict[str, Any]:
    """Run one fixture through the real engine and return observed evidence."""

    data = load_input(name)
    seed_data = load_seed(name)
    scenario = str(data["scenario"])
    if scenario not in _EVALUATORS:
        raise ValueError(f"unknown fixture scenario: {scenario}")
    observed, payload = _EVALUATORS[scenario](data, seed_data)
    return {
        "name": name,
        "scenario": scenario,
        "exercises": [str(item) for item in data["exercises"]],
        "observed": observed,
        "canonical_hash": canonical_geometry_hash(payload),
    }


__all__ = [
    "FIXTURE_FILES",
    "FIXTURE_NAMES",
    "FIXTURE_ROOT",
    "REQUIRED_ENGINE_AREAS",
    "evaluate_fixture",
    "fixture_dir",
    "load_expected_hash",
    "load_input",
    "load_invariants",
    "load_seed",
    "site_polygon",
]
