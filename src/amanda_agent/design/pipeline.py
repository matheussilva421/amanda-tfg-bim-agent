"""Progressive site-to-finalist pipeline with no Revit dependency."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from shapely.geometry import mapping  # type: ignore[import-untyped]

from .blocks import generate_blocks
from .constraints import hard_violations_only, validate_candidate
from .generate import GeneratedCandidate, generate_designs
from .pareto import pareto_frontier
from .rooms import refine_rooms


@dataclass(frozen=True)
class PipelineRejection:
    candidate_id: str
    reason: str
    codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineResult:
    counts: dict[str, int]
    stages: dict[str, list[Any]]
    rejected: list[PipelineRejection]
    stage_order: list[str]
    revit_calls: int = 0
    attempts: list[dict[str, Any]] = field(default_factory=list)
    hard_rejections_by_rule: dict[str, int] = field(default_factory=dict)
    ranking: list[dict[str, Any]] = field(default_factory=list)
    pareto_frontier: list[dict[str, Any]] = field(default_factory=list)
    pareto_frontier_ids: list[str] = field(default_factory=list)


def run_pipeline(
    requirements: Any,
    site: Any,
    *,
    seeds: list[int] | None = None,
    config: dict[str, int] | None = None,
    archetypes: list[Any] | tuple[Any, ...] | None = None,
    input_versions: Mapping[str, Any] | None = None,
) -> PipelineResult:
    """Run configured progressive filtering and keep exact hard rejection text."""

    settings = {
        "macro_candidates": 120,
        "top_macro": 15,
        "top_rooms": 5,
        "top_finalists": 3,
    }
    settings.update(config or {})
    if seeds is None:
        seeds = list(range(settings["macro_candidates"]))
    generation = generate_designs(
        requirements,
        site,
        run_id="pipeline-run",
        seeds=list(seeds),
        archetypes=archetypes,
    )
    macro = list(generation.candidates[: settings["macro_candidates"]])
    valid: list[GeneratedCandidate] = []
    rejected: list[PipelineRejection] = []
    attempts: list[dict[str, Any]] = []
    hard_rejections_by_rule: dict[str, int] = {}
    seen_geometry_hashes: set[str] = set()
    for candidate in macro:
        candidate_id = f"{candidate.archetype}:{candidate.seed}"
        values = candidate.to_dict()
        constraint_site = mapping(site) if hasattr(site, "__geo_interface__") else site
        violations = hard_violations_only(validate_candidate(values, requirements, constraint_site)) if candidate.status in {"OPTIMAL", "FEASIBLE"} else []
        hard_invalid = False
        rejection_codes: list[str] = []
        if candidate.status not in {"OPTIMAL", "FEASIBLE"}:
            outcome = "unknown" if candidate.status == "UNKNOWN" else "invalid"
            codes = ["solver_unknown"] if outcome == "unknown" else ["solver_infeasible"]
            reason = "; ".join(candidate.hard_violations) or "solver did not produce a feasible candidate"
            rejection_codes = codes
            hard_invalid = outcome == "invalid"
            rejected.append(PipelineRejection(candidate_id, reason, codes))
            if hard_invalid:
                for code in codes:
                    hard_rejections_by_rule[code] = hard_rejections_by_rule.get(code, 0) + 1
        elif violations:
            codes = [item.code for item in violations]
            reason = "; ".join(f"{item.code}: {item.message}" for item in violations)
            rejection_codes = codes
            hard_invalid = True
            rejected.append(PipelineRejection(candidate_id, reason, codes))
            for code in codes:
                hard_rejections_by_rule[code] = hard_rejections_by_rule.get(code, 0) + 1
        else:
            if candidate.geometry_hash in seen_geometry_hashes:
                outcome = "duplicate"
            else:
                outcome = "valid"
                seen_geometry_hashes.add(candidate.geometry_hash)
                valid.append(candidate)
        if candidate.status in {"OPTIMAL", "FEASIBLE"} and violations:
            outcome = "invalid"
        elif candidate.status not in {"OPTIMAL", "FEASIBLE"}:
            outcome = "unknown" if candidate.status == "UNKNOWN" else "invalid"
        attempts.append(
            {
                "candidate_id": candidate_id,
                "archetype": candidate.archetype,
                "seed": candidate.seed,
                "engine_version": generation.engine_version,
                "input_versions": dict(input_versions or {"engine_version": generation.engine_version}),
                "status": candidate.status,
                "solver_status": candidate.solver_status,
                "solver_seed": candidate.solver_seed,
                "geometry_hash": candidate.geometry_hash,
                "outcome": outcome,
                "hard_invalid": hard_invalid,
                "rejection_codes": rejection_codes,
            }
        )
    top_macro = valid[: settings["top_macro"]]
    top_rooms: list[dict[str, Any]] = []
    requirement_sectors = requirements.get("sectors", []) if isinstance(requirements, dict) else getattr(requirements, "sectors", [])
    requirement_by_id = {str(item.get("logical_id") if isinstance(item, dict) else item.logical_id): item for item in requirement_sectors}
    for candidate in top_macro[: settings["top_rooms"]]:
        macro_sectors = candidate.geometry.get("sectors", [])
        blocks = generate_blocks([
            {"logical_id": item["logical_id"], "geometry": item["geometry"], "demand_m2": item.get("demand_m2", item["geometry"].area)}
            for item in macro_sectors
        ], min_width_m=0.5)
        if not blocks.ok:
            rejected.extend(PipelineRejection(str(candidate.seed), f"{item.code}: {item.message}", [item.code]) for item in blocks.violations)
            continue
        rooms: list[dict[str, Any]] = []
        accounting: dict[str, float] = {}
        room_error: PipelineRejection | None = None
        for block in blocks.blocks:
            sector = requirement_by_id.get(block["sector_id"])
            spaces = (sector.get("spaces", []) if isinstance(sector, dict) else getattr(sector, "spaces", [])) if sector is not None else []
            refined = refine_rooms(block, list(spaces))
            if not refined.ok:
                first = refined.violations[0]
                room_error = PipelineRejection(str(candidate.seed), f"{first.code}: {first.message}", [first.code])
                break
            rooms.extend(refined.rooms)
            for key, value in refined.accounting.items():
                accounting[key] = accounting.get(key, 0.0) + value
        if room_error is not None:
            rejected.append(room_error)
            continue
        top_rooms.append({"candidate": candidate, "blocks": blocks.blocks, "rooms": rooms, "accounting": accounting})
    finalists = top_rooms[: settings["top_finalists"]]
    ranking = [
        next(item for item in attempts if item["candidate_id"] == f"{candidate.archetype}:{candidate.seed}")
        for candidate in valid
    ]
    frontier = pareto_frontier(ranking, dimensions=[])
    return PipelineResult(
        counts={"macro": settings["macro_candidates"], "top_macro": settings["top_macro"], "rooms": settings["top_rooms"], "finalists": settings["top_finalists"]},
        stages={"macro": macro, "hard_filter": valid, "top_macro": top_macro, "rooms": top_rooms, "finalists": finalists, "detailed": finalists},
        rejected=rejected,
        stage_order=["macro", "hard_filter", "top_macro", "rooms", "finalists", "detailed"],
        revit_calls=0,
        attempts=attempts,
        hard_rejections_by_rule=hard_rejections_by_rule,
        ranking=ranking,
        pareto_frontier=frontier,
        pareto_frontier_ids=[str(item["candidate_id"]) for item in frontier],
    )


progressive_pipeline = run_pipeline


__all__ = ["PipelineRejection", "PipelineResult", "progressive_pipeline", "run_pipeline"]
