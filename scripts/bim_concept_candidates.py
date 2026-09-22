"""Prepare offline conceptual finalist bundles without claiming live Revit evidence.

This module is the safe, testable seam for P08-T08. It compiles a finalist
through R04, writes deterministic planning/metric/preview artifacts under a
new lab candidate directory, and records the live Revit persistence boundary as
pending. It never acquires the shared production lease or writes an RVT.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from math import isclose
from pathlib import Path
from typing import Any

from shapely.geometry import shape

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.solution_compiler import SolutionCompilerError, compile_solution
from amanda_agent.bim.stages import EvidenceScope, ExecutionMode
from amanda_agent.design.models import DesignSolution
from amanda_agent.models.capability import CapabilityRegistry

_CANDIDATE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_PROTECTED = frozenset(
    {"golden", "master", "source", "baseline", "checkpoint", "checkpoints", "release"}
)
_CONCEPT_STAGES = (BimStage.R01, BimStage.R02, BimStage.R03, BimStage.R04)


class CandidatePreparationError(RuntimeError):
    """An offline conceptual candidate cannot be prepared safely."""


@dataclass(frozen=True)
class ConceptCandidatePreparation:
    """Offline artifacts and explicit evidence boundary for one finalist."""

    solution_id: str
    solution_path: Path
    output_directory: Path
    plans: tuple[Any, ...]
    execution_mode: str
    live_revit_evidence: bool
    writer_lease_acquired: bool
    status: str
    rejected_stages: tuple[str, ...]
    metrics_verification: dict[str, Any]

    @property
    def plan_paths(self) -> tuple[Path, ...]:
        return tuple(
            self.output_directory / "plans" / f"{plan.stage.name}.json"
            for plan in self.plans
        )


def _safe_solution(path: str | Path) -> tuple[Path, DesignSolution]:
    source = Path(path).resolve(strict=False)
    if not source.is_file() or source.is_symlink():
        raise CandidatePreparationError(f"solution.json is missing or mutable: {source}")
    try:
        solution = DesignSolution.model_validate_json(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise CandidatePreparationError(f"invalid solution.json: {source}") from exc
    return source, solution


def _safe_candidate_root(root: str | Path) -> Path:
    candidate_root = Path(root).resolve(strict=False)
    if any(component.casefold() in _PROTECTED for component in candidate_root.parts):
        raise CandidatePreparationError(
            f"candidate output root contains a protected path component: {candidate_root}"
        )
    return candidate_root


def _safe_candidate_id(solution_id: str) -> str:
    if not _CANDIDATE_ID.fullmatch(solution_id):
        raise CandidatePreparationError(f"unsafe solution_id for candidate directory: {solution_id!r}")
    return solution_id


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _source_metrics(solution: DesignSolution) -> dict[str, float | int]:
    geometry = solution.geometry
    blocks = geometry.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise CandidatePreparationError("solution geometry has no blocks")
    try:
        source_block_area = sum(float(item["area_m2"]) for item in blocks)
    except (KeyError, TypeError, ValueError) as exc:
        raise CandidatePreparationError("solution blocks have invalid area_m2 values") from exc
    site = geometry.get("site")
    if not isinstance(site, dict):
        raise CandidatePreparationError("solution geometry has no site")
    try:
        site_area = float(shape(site).area)
    except (TypeError, ValueError) as exc:
        raise CandidatePreparationError("solution site geometry is invalid") from exc
    return {
        "block_count": len(blocks),
        "source_block_area_m2": source_block_area,
        "site_area_m2": site_area,
    }


def _verify_metrics(solution: DesignSolution, plans: list[Any]) -> dict[str, Any]:
    r04 = next((plan for plan in plans if plan.stage is BimStage.R04), None)
    if r04 is None:
        raise CandidatePreparationError("compiled conceptual chain has no R04 plan")
    source = _source_metrics(solution)
    compiled_area = sum(float(block.area_projection_m2) for block in r04.blocks)
    compiled_site = shape(solution.geometry["site"])
    checks = {
        "block_count": len(r04.blocks) == source["block_count"],
        "block_area_matches": isclose(
            compiled_area,
            float(source["source_block_area_m2"]),
            rel_tol=0.0,
            abs_tol=1e-6,
        ),
        "site_area_finite": isclose(
            float(compiled_site.area),
            float(source["site_area_m2"]),
            rel_tol=0.0,
            abs_tol=1e-6,
        ),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "source": source,
        "compiled": {
            "block_count": len(r04.blocks),
            "block_area_m2": compiled_area,
            "site_area_m2": float(compiled_site.area),
        },
        "solution_metrics": solution.metrics.model_dump(mode="json"),
    }


def _polygon_points(value: Any) -> list[tuple[float, float]]:
    coordinates = value["coordinates"][0]
    return [(float(point[0]), float(point[1])) for point in coordinates]


def _svg_preview(solution: DesignSolution) -> str:
    site = _polygon_points(solution.geometry["site"])
    blocks = [
        _polygon_points(item["geometry"])
        for item in solution.geometry.get("blocks", [])
    ]
    points = [point for polygon in [site, *blocks] for point in polygon]
    min_x = min(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_x = max(point[0] for point in points)
    max_y = max(point[1] for point in points)
    width = max(max_x - min_x, 1.0)
    height = max(max_y - min_y, 1.0)
    margin = max(width, height) * 0.04
    view_x = min_x - margin
    view_y = min_y - margin
    view_w = width + 2 * margin
    view_h = height + 2 * margin

    def polygon(points: list[tuple[float, float]], **attrs: str) -> str:
        value = " ".join(f"{x:.6f},{y:.6f}" for x, y in points)
        rendered = " ".join(f'{key}="{value}"' for key, value in attrs.items())
        return f'    <polygon points="{value}" {rendered} />'

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"',
        f'     viewBox="{view_x:.6f} {view_y:.6f} {view_w:.6f} {view_h:.6f}"',
        f'     data-solution-id="{solution.solution_id}" data-scope="CONCEPT_ONLY">',
        f'  <title>{solution.solution_id} conceptual site and massing preview</title>',
        polygon(site, fill="none", stroke="#334155", **{"stroke-width": "0.8"}),
    ]
    for index, item in enumerate(blocks, start=1):
        lines.append(
            polygon(
                item,
                fill="#93c5fd",
                stroke="#1d4ed8",
                **{"stroke-width": "0.5", "data-block-index": str(index)},
            )
        )
    lines.extend(
        [
            '  <text x="0" y="0" font-family="sans-serif" font-size="2">CONCEPT_ONLY / STUDY</text>',
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def _manifest(directory: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        if path.name == "manifest.json":
            continue
        values[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


def prepare_concept_candidate(
    solution_path: str | Path,
    *,
    output_root: str | Path,
    registry: CapabilityRegistry,
    revit_build: str,
    tool_schema_hash: str,
    amanda_template: str | Path,
    amanda_template_tested: bool,
    max_stage: BimStage | str = BimStage.R04,
) -> ConceptCandidatePreparation:
    """Compile and publish a new offline R01-R04 candidate bundle.

    The function deliberately has no invoker and no lease parameter. Live BIM
    writes belong to a separately verified adapter boundary.
    """

    source, solution = _safe_solution(solution_path)
    candidate_root = _safe_candidate_root(output_root)
    solution_id = _safe_candidate_id(solution.solution_id)
    target = candidate_root / solution_id
    if target.exists():
        raise CandidatePreparationError(f"candidate directory already exists: {target}")
    try:
        requested = max_stage if isinstance(max_stage, BimStage) else BimStage(max_stage)
    except ValueError as exc:
        raise CandidatePreparationError(f"unknown conceptual stage: {max_stage!r}") from exc
    if list(BimStage).index(requested) > list(BimStage).index(BimStage.R04):
        raise CandidatePreparationError(
            f"CONCEPT_ONLY permits stages through R04; requested stage is {requested.name}"
        )

    try:
        plans = compile_solution(
            source,
            registry=registry,
            revit_build=revit_build,
            tool_schema_hash=tool_schema_hash,
            mode=ExecutionMode.CONCEPT_ONLY,
            scenario="STUDY",
            fixture=False,
            evidence_scope=EvidenceScope.SYNTHETIC,
            amanda_template=Path(amanda_template),
            amanda_template_tested=amanda_template_tested,
            max_stage=requested,
        )
    except (OSError, SolutionCompilerError, TypeError, ValueError) as exc:
        raise CandidatePreparationError(f"concept compilation refused: {exc}") from exc
    if tuple(plan.stage for plan in plans) != _CONCEPT_STAGES:
        raise CandidatePreparationError("concept compiler did not produce exactly R01-R04")

    metrics = _verify_metrics(solution, plans)
    if metrics["status"] != "PASS":
        raise CandidatePreparationError("concept metric verification failed")
    rejected = tuple(
        stage.name for stage in BimStage
        if list(BimStage).index(stage) > list(BimStage).index(BimStage.R04)
    )

    target.mkdir(parents=True)
    (target / "plans").mkdir()
    for plan in plans:
        _write_json(target / "plans" / f"{plan.stage.name}.json", plan.model_dump(mode="json"))
    (target / "preview.svg").write_text(_svg_preview(solution), encoding="utf-8")
    _write_json(target / "metrics-verification.json", metrics)
    bundle = {
        "schema_version": 1,
        "status": "OFFLINE_PLAN_READY",
        "solution_id": solution.solution_id,
        "solution_path": str(source),
        "approval_hash": solution.approval_hash,
        "execution_mode": ExecutionMode.CONCEPT_ONLY.value,
        "stages": [stage.name for stage in _CONCEPT_STAGES],
        "rejected_stages": list(rejected),
        "provider_evidence_scope": EvidenceScope.SYNTHETIC.value,
        "live_revit_evidence": False,
        "writer_lease_acquired": False,
        "save_close_reopen": "PENDING_LIVE_REVIT",
        "metrics_verification": metrics,
        "template": {
            "path": str(Path(amanda_template).resolve(strict=False)),
            "tested": bool(amanda_template_tested),
        },
    }
    _write_json(target / "candidate-bundle.json", bundle)
    _write_json(target / "manifest.json", _manifest(target))
    return ConceptCandidatePreparation(
        solution_id=solution.solution_id,
        solution_path=source,
        output_directory=target,
        plans=tuple(plans),
        execution_mode=ExecutionMode.CONCEPT_ONLY.value,
        live_revit_evidence=False,
        writer_lease_acquired=False,
        status="OFFLINE_PLAN_READY",
        rejected_stages=rejected,
        metrics_verification=metrics,
    )



def prepare_concept_candidates(
    solution_paths: Iterable[str | Path],
    **kwargs: Any,
) -> tuple[ConceptCandidatePreparation, ...]:
    """Prepare multiple finalists in deterministic solution-id order."""

    paths = [Path(path) for path in solution_paths]
    if not paths:
        raise CandidatePreparationError("at least one finalist solution is required")
    return tuple(
        prepare_concept_candidate(path, **kwargs)
        for path in sorted(paths, key=lambda item: item.as_posix())
    )


__all__ = [
    "CandidatePreparationError",
    "ConceptCandidatePreparation",
    "prepare_concept_candidate",
    "prepare_concept_candidates",
]
