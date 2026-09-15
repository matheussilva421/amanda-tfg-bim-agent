"""Seeded candidate generation and semantic geometry hashing."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from shapely.geometry import mapping  # type: ignore[import-untyped]

from .archetypes import get_archetype
from .macrozones import solve_macrozones


@dataclass(frozen=True)
class GeneratedCandidate:
    run_id: str
    seed: int
    status: str
    geometry: dict[str, Any]
    geometry_hash: str
    solver_status: str
    hard_violations: list[str] = field(default_factory=list)
    archetype: str = "DEFAULT"
    archetype_initialization: dict[str, Any] = field(default_factory=dict)
    archetype_relationships: list[Any] = field(default_factory=list)
    exploration_tags: list[str] = field(default_factory=list)
    solver_seed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "seed": self.seed,
            "archetype": self.archetype,
            "archetype_initialization": self.archetype_initialization,
            "archetype_relationships": self.archetype_relationships,
            "exploration_tags": self.exploration_tags,
            "status": self.status,
            "resolution": "MACRO",
            "geometry": self.geometry,
            "sectors": self.geometry.get("sectors", []),
            "geometry_hash": self.geometry_hash,
            "solver_status": self.solver_status,
            "solver_seed": self.solver_seed,
            "hard_violations": self.hard_violations,
        }


@dataclass(frozen=True)
class GenerationResult:
    candidates: list[GeneratedCandidate]
    candidate_count: int
    generated_count: int
    seed_list: list[int]
    engine_version: str
    archetype_list: list[str] = field(default_factory=list)


_VOLATILE_KEYS = {"run_id", "timestamp", "generated_at", "duration_s", "solver_duration_s", "paths", "path"}


def _canonical(value: Any) -> Any:
    if hasattr(value, "__geo_interface__"):
        return _canonical(mapping(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0])) if str(key) not in _VOLATILE_KEYS}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, float):
        return round(value, 6)
    return value


def canonical_geometry_payload(candidate: Any) -> Any:
    if isinstance(candidate, Mapping):
        geometry = candidate.get("geometry", candidate)
    else:
        geometry = getattr(candidate, "geometry", candidate)
    return _canonical(geometry)


def canonical_geometry_hash(candidate: Any) -> str:
    encoded = json.dumps(canonical_geometry_payload(candidate), ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def generate_designs(
    requirements: Any,
    site: Any,
    *,
    run_id: str,
    seeds: list[int],
    engine_version: str = "design-engine-v1",
    archetypes: list[Any] | tuple[Any, ...] | None = None,
) -> GenerationResult:
    """Generate one ordered macro candidate per archetype and requested seed."""

    if not run_id:
        raise ValueError("run_id is required")
    seed_list = [int(seed) for seed in seeds]
    configured_archetypes = ["DEFAULT"] if archetypes is None else [
        str(getattr(item, "value", item)) for item in archetypes
    ]
    if not configured_archetypes:
        raise ValueError("at least one archetype is required")
    candidates: list[GeneratedCandidate] = []
    for archetype in configured_archetypes:
        configuration = {} if archetype == "DEFAULT" else get_archetype(archetype)
        for seed in seed_list:
            result = solve_macrozones(requirements, site, seed=seed)
            geometry = {"sectors": result.sectors, "assignment": result.assignment, "assignment_order": result.assignment_order}
            candidate = GeneratedCandidate(
                run_id=run_id,
                seed=seed,
                status=result.status,
                geometry=geometry,
                geometry_hash=canonical_geometry_hash(geometry),
                solver_status=result.solver_status,
                hard_violations=list(result.infeasibility_evidence),
                archetype=archetype,
                archetype_initialization=dict(configuration.get("initialization", {})),
                archetype_relationships=list(configuration.get("relationships", [])),
                exploration_tags=list(configuration.get("exploration_tags", [])),
                solver_seed=result.solver_seed,
            )
            candidates.append(candidate)
    return GenerationResult(
        candidates=candidates,
        candidate_count=len({item.geometry_hash for item in candidates}),
        generated_count=len(candidates),
        seed_list=seed_list,
        engine_version=engine_version,
        archetype_list=configured_archetypes,
    )


generate_candidates = generate_designs


__all__ = ["GeneratedCandidate", "GenerationResult", "canonical_geometry_hash", "canonical_geometry_payload", "generate_candidates", "generate_designs"]
