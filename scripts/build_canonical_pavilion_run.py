"""Build a deterministic, offline and content-bound canonical pavilion run."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from shapely.geometry.base import BaseGeometry

from amanda_agent.design.canonical_pavilion_layout import (
    CanonicalPavilionLayout,
    build_canonical_pavilion_layout,
)
from amanda_agent.design.canonical_qa import CanonicalCheck, run_canonical_checks
from amanda_agent.design.canonical_reference import (
    CanonicalReferenceError,
    CanonicalReferenceProfile,
)
from amanda_agent.production.selection import (
    SELECTION_SOLUTION_ID,
    SelectionError,
    build_selection,
)

GENERATION_RUN = "AMANDA-RUN-002-PAVILION"
GENERATION_TIMESTAMP = "2026-09-23T00:00:00Z"


class CanonicalRunError(RuntimeError):
    """The canonical offline run cannot be emitted safely."""


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _polygon_parts(geometry: BaseGeometry) -> tuple[BaseGeometry, ...]:
    if geometry.geom_type == "Polygon":
        return (geometry,)
    if hasattr(geometry, "geoms"):
        return tuple(
            item for item in geometry.geoms if item.geom_type == "Polygon"
        )
    return ()


def _svg_path(geometry: BaseGeometry, transform) -> str:
    paths: list[str] = []
    for polygon in _polygon_parts(geometry):
        commands = []
        for index, (x, y) in enumerate(polygon.exterior.coords):
            px, py = transform(float(x), float(y))
            commands.append(f"{'M' if index == 0 else 'L'}{px:.2f},{py:.2f}")
        commands.append("Z")
        paths.append(" ".join(commands))
    return " ".join(paths)


def _layout_svg(layout: CanonicalPavilionLayout) -> str:
    geometries = [block.footprint for block in layout.blocks]
    geometries.extend(item.polygon for item in layout.external_spaces)
    geometries.extend(item.footprint for item in layout.covered_connectors)
    min_x = min(item.bounds[0] for item in geometries)
    min_y = min(item.bounds[1] for item in geometries)
    max_x = max(item.bounds[2] for item in geometries)
    max_y = max(item.bounds[3] for item in geometries)
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)
    margin = 36.0
    scale = min(1000.0 / span_x, 760.0 / span_y)
    width = span_x * scale + margin * 2
    height = span_y * scale + margin * 2

    def transform(x: float, y: float) -> tuple[float, float]:
        return margin + (x - min_x) * scale, margin + (max_y - y) * scale

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-labelledby="title description">',
        "<title id=\"title\">Canonical pavilion normalized study</title>",
        '<desc id="description">Offline normalized block and landscape schematic; not a surveyed site plan.</desc>',
        '<rect width="100%" height="100%" fill="#fbfaf6"/>',
    ]
    external_colors = {
        "THERAPEUTIC_GARDEN": "#d9ead0",
        "PROTECTED_PATIO": "#b9d9ad",
        "HORTA": "#cce5bd",
        "EXERCISE": "#e5ecd4",
        "PLAYGROUND": "#f0e2bc",
    }
    for space in layout.external_spaces:
        color = external_colors.get(space.logical_id, "#e6ecd9")
        elements.append(
            f'<path d="{_svg_path(space.polygon, transform)}" fill="{color}" stroke="#8a9a7c" stroke-width="1.5"/>'
        )
    for connector in layout.covered_connectors:
        elements.append(
            f'<path d="{_svg_path(connector.footprint, transform)}" fill="#e8c879" stroke="#aa8d49" stroke-width="1.2"/>'
        )
    role_colors = {
        "ADMIN_ACOLHIMENTO": "#c9def4",
        "RESIDENTIAL_SLEEPING": "#cce6cd",
        "RESIDENTIAL_COMMUNAL": "#d9e8c6",
        "SERVICE_CAPACITATION": "#e7e2c5",
        "CHILD_SECTOR": "#efd7e1",
    }
    for block in layout.blocks:
        color = role_colors.get(block.role, "#d9e4d3")
        elements.append(
            f'<path d="{_svg_path(block.footprint, transform)}" fill="{color}" stroke="#39434a" stroke-width="2"/>'
        )
        px, py = transform(block.footprint.centroid.x, block.footprint.centroid.y)
        elements.append(
            f'<text x="{px:.2f}" y="{py:.2f}" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#20272b">{escape(block.component_id)}</text>'
        )
    elements.extend(
        [
            f'<text x="{margin:.0f}" y="{height - 12:.0f}" font-family="sans-serif" font-size="12" fill="#4d5559">NORMALIZED STUDY — NOT A SURVEY — NOT A REVIT MODEL</text>',
            "</svg>",
        ]
    )
    return "\n".join(elements) + "\n"


def _qa_payload(checks: list[CanonicalCheck]) -> dict:
    critical_failures = [
        item
        for item in checks
        if item.severity == "CRITICAL" and item.status == "FAIL"
    ]
    return {
        "schema_version": 1,
        "summary": {
            "checks": len(checks),
            "pass": sum(item.status == "PASS" for item in checks),
            "blocked": sum(item.status == "BLOCKED" for item in checks),
            "fail": sum(item.status == "FAIL" for item in checks),
            "critical_failures": len(critical_failures),
        },
        "checks": [
            {
                "check_id": item.check_id,
                "severity": item.severity,
                "status": item.status,
                "rule": item.rule,
                "evidence": item.evidence,
            }
            for item in checks
        ],
    }


def _existing_outputs_match(output_dir: Path, expected: dict[str, bytes]) -> bool:
    existing = {
        path.relative_to(output_dir).as_posix(): path.read_bytes()
        for path in output_dir.rglob("*")
        if path.is_file()
    }
    return existing == expected


def build_canonical_pavilion_run(
    program: dict,
    profile: CanonicalReferenceProfile,
    output_dir: Path,
) -> Path:
    """Write deterministic run, selection, geometry, QA, and SVG evidence offline."""
    output_dir = Path(output_dir)
    layout = build_canonical_pavilion_layout(program, profile)
    checks = run_canonical_checks(layout, profile)
    qa = _qa_payload(checks)
    if qa["summary"]["critical_failures"]:
        failed = [
            item["check_id"]
            for item in qa["checks"]
            if item["severity"] == "CRITICAL" and item["status"] == "FAIL"
        ]
        raise CanonicalRunError(
            "critical canonical QA failures: " + ", ".join(failed)
        )

    try:
        selection = build_selection(
            layout,
            generation_run=GENERATION_RUN,
            timestamp=GENERATION_TIMESTAMP,
            profile=profile,
        )
    except SelectionError as exc:
        raise CanonicalRunError(str(exc)) from exc

    solution = selection.solution.model_dump(mode="json")
    geometry = selection.solution.geometry
    solution_dir = f"finalists/{selection.solution.solution_id}"
    files: dict[str, bytes] = {
        f"{solution_dir}/solution.json": _json_bytes(solution),
        f"{solution_dir}/geometry.json": _json_bytes(geometry),
        "canonical-qa.json": _json_bytes(qa),
        "layout-preview.svg": _layout_svg(layout).encode("utf-8"),
        "selection.json": _json_bytes(
            {
                "schema_version": 1,
                "run_id": GENERATION_RUN,
                "solution_id": selection.solution.solution_id,
                "layout_hash": selection.layout_hash,
                "approval_hash": selection.approval_hash,
                "parti_decision": selection.parti_decision.model_dump(mode="json"),
                "detail_decision": selection.decision.model_dump(mode="json"),
            }
        ),
    }
    program_sha256 = _sha256(_json_bytes(program))
    run_value = {
        "schema_version": 1,
        "run_id": GENERATION_RUN,
        "solution_id": selection.solution.solution_id,
        "run_status": "OFFLINE_CANDIDATE",
        "generated_utc": GENERATION_TIMESTAMP,
        "program_person_capacity": selection.solution.program_person_capacity,
        "internal_useful_m2": layout.accounting["net_internal_m2"],
        "external_programmed_m2": layout.accounting["external_programmed_m2"],
        "program_json_sha256": program_sha256,
        "program_source_sha256": layout.parameters["program_source_sha256"],
        "canonical_images": [
            {"path": path, "sha256": digest}
            for path, digest in zip(
                profile.canonical_images, profile.source_hashes, strict=True
            )
        ],
        "layout_hash": selection.layout_hash,
        "approval_hash": selection.approval_hash,
        "bim_eligible": selection.solution.bim_eligible,
        "canonical_qa_summary": qa["summary"],
        "revit_calls": 0,
    }
    files["run.json"] = _json_bytes(run_value)
    files["artifact-manifest.json"] = _json_bytes(
        {
            "schema_version": 1,
            "run_id": GENERATION_RUN,
            "solution_id": selection.solution.solution_id,
            "approval_hash": selection.approval_hash,
            "layout_hash": selection.layout_hash,
            "canonical_source_hashes": list(profile.source_hashes),
            "artifacts": [
                {
                    "path": name,
                    "bytes": len(contents),
                    "sha256": _sha256(contents),
                }
                for name, contents in sorted(files.items())
            ],
        }
    )

    if output_dir.exists():
        if _existing_outputs_match(output_dir, files):
            return output_dir
        raise CanonicalRunError(
            f"run output already exists with different content: {output_dir}"
        )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(
            prefix=f".{output_dir.name}.staging-", dir=output_dir.parent
        ) as staging_name:
            staging = Path(staging_name)
            for name, contents in files.items():
                path = staging / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(contents)
            staging.rename(output_dir)
    except FileExistsError as exc:
        if output_dir.exists() and _existing_outputs_match(output_dir, files):
            return output_dir
        raise CanonicalRunError(
            f"run output was created concurrently: {output_dir}"
        ) from exc
    except OSError as exc:
        raise CanonicalRunError(f"cannot persist canonical run: {output_dir}") from exc
    return output_dir


def _load_inputs(repository_root: Path) -> tuple[dict, CanonicalReferenceProfile]:
    program_path = Path(repository_root) / "project/requirements/program.json"
    try:
        program = json.loads(program_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CanonicalRunError(f"cannot load official program: {program_path}") from exc
    return program, CanonicalReferenceProfile.load(Path(repository_root))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    output_dir = args.output_dir or (
        args.repository_root / "design-engine" / "runs" / GENERATION_RUN
    )
    try:
        program, profile = _load_inputs(args.repository_root)
        created = build_canonical_pavilion_run(program, profile, output_dir)
    except (CanonicalRunError, CanonicalReferenceError, ValueError) as exc:
        print(f"canonical run blocked: {exc}", file=sys.stderr)
        return 2
    print(f"offline canonical run: {created}")
    print(f"solution id: {SELECTION_SOLUTION_ID}")
    print("BIM eligible: false; Revit calls: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
