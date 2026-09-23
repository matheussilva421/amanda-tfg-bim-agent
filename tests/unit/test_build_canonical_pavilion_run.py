from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from amanda_agent.design.canonical_qa import CanonicalCheck
from amanda_agent.design.canonical_reference import CanonicalReferenceProfile
from scripts import build_canonical_pavilion_run as run_builder

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = json.loads(
    (ROOT / "project/requirements/program.json").read_text(encoding="utf-8")
)
SOURCE_HASHES = ("a" * 64, "b" * 64, "c" * 64)
SOURCE_PATHS = (
    "canonical/01_implantacao_geral_canonica.png",
    "canonical/02_bloco_residencial_canonico.png",
    "canonical/03_bloco_administrativo_canonico.png",
)


def _profile() -> CanonicalReferenceProfile:
    return CanonicalReferenceProfile(
        status="CANONICAL_DESIGN_REFERENCE",
        supersedes=("AMANDA-RUN-001-S01", "COURTYARD_DOUBLE_LOADED_BAR"),
        canonical_images=SOURCE_PATHS,
        source_hashes=SOURCE_HASHES,
        data={
            "program": {
                "people": 20,
                "net_internal_m2": 626.0,
                "external_programmed_m2": 260.0,
                "enclosed_estimate_m2": [783.0, 814.0],
                "covered_estimate_m2": [850.0, 950.0],
            },
            "required_parti": {
                "single_linear_bar_allowed": False,
                "admin_public_edge": True,
                "admin_storeys_target": 2,
                "residential_cluster": {
                    "required": True,
                    "pavilion_count_target": 4,
                    "sleeping_pavilions_target": 3,
                    "communal_pavilions_target": 1,
                    "central_garden_required": True,
                },
                "child_sector_green_interface": True,
                "service_block_separate": True,
                "service_access_separate": True,
                "covered_external_paths_required": True,
                "landscape_is_program": True,
            },
        },
    )


def _files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_script_cli_loads_project_sources_without_external_pythonpath():
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper() != "PYTHONPATH"
    }
    script = ROOT / "scripts/build_canonical_pavilion_run.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert "--repository-root" in completed.stdout
    assert "--output-dir" in completed.stdout


def test_builds_deterministic_offline_run_bound_to_canonical_sources(tmp_path: Path):
    profile = _profile()
    first = run_builder.build_canonical_pavilion_run(
        PROGRAM, profile, tmp_path / "first"
    )
    second = run_builder.build_canonical_pavilion_run(
        PROGRAM, profile, tmp_path / "second"
    )

    solution_path = (
        first
        / "finalists"
        / "AMANDA-RUN-002-PAVILION-S02"
        / "solution.json"
    )
    geometry_path = (
        first
        / "finalists"
        / "AMANDA-RUN-002-PAVILION-S02"
        / "geometry.json"
    )
    qa_path = first / "canonical-qa.json"
    solution = json.loads(solution_path.read_text(encoding="utf-8"))
    geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    run = json.loads((first / "run.json").read_text(encoding="utf-8"))
    manifest = json.loads((first / "artifact-manifest.json").read_text(encoding="utf-8"))

    assert solution["solution_id"] == "AMANDA-RUN-002-PAVILION-S02"
    assert solution["program_person_capacity"] == 20
    assert solution["approval_hash"] == run["approval_hash"]
    assert geometry == solution["geometry"]
    assert geometry["canonical_source_hashes"] == list(SOURCE_HASHES)
    assert [item["sha256"] for item in geometry["canonical_reference"]["images"]] == list(SOURCE_HASHES)
    assert run["bim_eligible"] is False
    assert run["revit_calls"] == 0
    assert qa["summary"]["critical_failures"] == 0
    assert any(item["status"] == "BLOCKED" for item in qa["checks"])
    assert "NOT A SURVEY" in (first / "layout-preview.svg").read_text(encoding="utf-8")
    assert manifest["approval_hash"] == solution["approval_hash"]
    assert _files(first) == _files(second)


def test_critical_canonical_failure_returns_nonzero_without_partial_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    output = tmp_path / "blocked-run"
    monkeypatch.setattr(run_builder, "_load_inputs", lambda _root: (PROGRAM, _profile()))
    monkeypatch.setattr(
        run_builder,
        "run_canonical_checks",
        lambda _layout, _profile: [
            CanonicalCheck(
                "CANON-009",
                "CRITICAL",
                "FAIL",
                "official_program_reconciled",
                "test-injected critical program mismatch",
            )
        ],
    )

    exit_code = run_builder.main(
        ["--repository-root", str(tmp_path), "--output-dir", str(output)]
    )

    assert exit_code != 0
    assert not output.exists()
