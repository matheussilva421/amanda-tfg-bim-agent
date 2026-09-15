"""P08-T06 finalist refinement and artifact contracts."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image

from amanda_agent.commands import design as design_commands
from amanda_agent.design.models import DesignSolution

REPO_ROOT = Path(__file__).resolve().parents[2]


def _copy_refinement_fixture(tmp_path: Path) -> Path:
    for relative in (
        Path("project/requirements/program.json"),
        Path("project/site/site.json"),
        Path("project/provenance/source-manifest.yaml"),
        Path("design-engine/runs/AMANDA-RUN-001/run.json"),
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)
    source_target = tmp_path / "docs" / "source"
    shutil.copytree(REPO_ROOT / "docs" / "source", source_target)
    return tmp_path


def test_refinement_publishes_schema_valid_distinct_finalist_artifacts(tmp_path: Path):
    root = _copy_refinement_fixture(tmp_path)
    refine = getattr(design_commands, "refine_design_run", None)
    assert refine is not None, "P08-T06 refinement command is missing"

    result = refine(root, run_id="AMANDA-RUN-001")

    assert result["finalist_count"] == 2
    assert result["pareto_frontier_ids"] == [
        "AMANDA-RUN-001-F01",
        "AMANDA-RUN-001-F02",
    ]
    finalists_root = root / "design-engine" / "runs" / "AMANDA-RUN-001" / "finalists"
    finalist_dirs = sorted(path for path in finalists_root.iterdir() if path.is_dir())
    assert [path.name for path in finalist_dirs] == [
        "AMANDA-RUN-001-F01",
        "AMANDA-RUN-001-F02",
    ]

    expected_dimensions = {
        "program_compliance",
        "privacy_security",
        "adjacency",
        "circulation",
        "accessibility",
        "solar_heuristic",
        "ventilation_heuristic",
        "green_integration",
        "compactness",
        "constructability",
        "concept_fidelity",
    }
    expected_files = {
        "solution.json",
        "geometry.geojson",
        "adjacency-graph.json",
        "flow-graphs.json",
        "metrics.json",
        "penalties.json",
        "WHY_THIS_OPTION.md",
        "floorplan.svg",
        "floorplan.png",
        "zoning.svg",
        "zoning.png",
    }
    solution_ids: list[str] = []
    geometry_hashes: list[str] = []
    for finalist_dir in finalist_dirs:
        assert {path.name for path in finalist_dir.iterdir()} >= expected_files
        solution_payload = json.loads(
            (finalist_dir / "solution.json").read_text(encoding="utf-8")
        )
        solution = DesignSolution.model_validate(solution_payload)
        solution_ids.append(solution.solution_id)
        geometry_hashes.append(solution_payload["geometry_hash"])
        assert set(solution.metrics.model_dump(mode="python")) >= expected_dimensions
        assert set(json.loads((finalist_dir / "metrics.json").read_text(encoding="utf-8"))["weights"]) == expected_dimensions
        assert json.loads((finalist_dir / "penalties.json").read_text(encoding="utf-8"))["hard_violations"] == []

        geojson = json.loads(
            (finalist_dir / "geometry.geojson").read_text(encoding="utf-8")
        )
        assert geojson["type"] == "FeatureCollection"
        feature_ids = {
            feature["properties"]["logical_id"]
            for feature in geojson["features"]
        }
        solution_geometry = solution_payload["geometry"]
        for key in ("blocks", "rooms", "external_spaces"):
            assert {item["logical_id"] for item in solution_geometry[key]} <= feature_ids

        for image_name in ("floorplan.png", "zoning.png"):
            with Image.open(finalist_dir / image_name) as image:
                image.verify()
            with Image.open(finalist_dir / image_name) as image:
                assert image.width > 0
                assert image.height > 0
        assert (finalist_dir / "WHY_THIS_OPTION.md").read_text(encoding="utf-8").count("# WHY_THIS_OPTION") == 1

    assert solution_ids == ["AMANDA-RUN-001-F01", "AMANDA-RUN-001-F02"]
    assert len(set(geometry_hashes)) == 2
    run_json_before = (root / "design-engine" / "runs" / "AMANDA-RUN-001" / "run.json").read_bytes()
    assert hashlib.sha256(run_json_before).hexdigest() == hashlib.sha256(
        (REPO_ROOT / "design-engine" / "runs" / "AMANDA-RUN-001" / "run.json").read_bytes()
    ).hexdigest()
