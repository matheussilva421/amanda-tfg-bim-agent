"""Progressive site-to-finalist pipeline with no Revit dependency."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shapely.geometry import mapping  # type: ignore[import-untyped]

from .blocks import generate_blocks
from .constraints import hard_violations_only, validate_candidate
from .generate import GeneratedCandidate, generate_designs
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


def run_pipeline(
    requirements: Any,
    site: Any,
    *,
    seeds: list[int] | None = None,
    config: dict[str, int] | None = None,
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
    generation = generate_designs(requirements, site, run_id="pipeline-run", seeds=list(seeds))
    macro = list(generation.candidates[: settings["macro_candidates"]])
    valid: list[GeneratedCandidate] = []
    rejected: list[PipelineRejection] = []
    for candidate in macro:
        values = candidate.to_dict()
        constraint_site = mapping(site) if hasattr(site, "__geo_interface__") else site
        violations = hard_violations_only(validate_candidate(values, requirements, constraint_site)) if candidate.status in {"OPTIMAL", "FEASIBLE"} else []
        if candidate.status not in {"OPTIMAL", "FEASIBLE"}:
            codes = ["solver_infeasible"]
            reason = "; ".join(candidate.hard_violations) or "solver did not produce a feasible candidate"
            rejected.append(PipelineRejection(str(candidate.seed), reason, codes))
        elif violations:
            codes = [item.code for item in violations]
            reason = "; ".join(f"{item.code}: {item.message}" for item in violations)
            rejected.append(PipelineRejection(str(candidate.seed), reason, codes))
        else:
            valid.append(candidate)
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
    return PipelineResult(
        counts={"macro": settings["macro_candidates"], "top_macro": settings["top_macro"], "rooms": settings["top_rooms"], "finalists": settings["top_finalists"]},
        stages={"macro": macro, "hard_filter": valid, "top_macro": top_macro, "rooms": top_rooms, "finalists": finalists, "detailed": finalists},
        rejected=rejected,
        stage_order=["macro", "hard_filter", "top_macro", "rooms", "finalists", "detailed"],
        revit_calls=0,
    )


progressive_pipeline = run_pipeline


__all__ = ["PipelineRejection", "PipelineResult", "progressive_pipeline", "run_pipeline"]
