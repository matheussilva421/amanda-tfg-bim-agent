from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from amanda_agent.design.canonical_qa import CanonicalCheck
from amanda_agent.design.canonical_reference import CanonicalReferenceProfile
from amanda_agent.design.models import compute_design_approval_hash
from amanda_agent.production.canonical_identity import (
    CanonicalSolutionIdentity,
    assign_canonical_solution_identity,
)
from amanda_agent.requirements.decisions import load_decision_register
from scripts import build_canonical_pavilion_run as run_builder

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = json.loads(
    (ROOT / "project/requirements/program.json").read_text(encoding="utf-8")
)
SOURCE_HASHES = ("a" * 64, "b" * 64, "c" * 64, "d" * 64)
SOURCE_PATHS = (
    "canonical/01_implantacao.png",
    "canonical/02_administrativo.png",
    "canonical/03_residencial.png",
    "canonical/04_servicos.png",
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


def _build_current_run(output: Path) -> tuple[int, Path]:
    exit_code = run_builder.main(
        ["--repository-root", str(ROOT), "--output-dir", str(output)]
    )
    return exit_code, output


def test_p3_loads_p2_identity_and_emits_a_distinct_offline_candidate(tmp_path: Path):
    output = tmp_path / "canonical-candidate"

    exit_code, created = _build_current_run(output)

    assert exit_code == 0
    identity = assign_canonical_solution_identity(ROOT)
    run = json.loads((created / "run.json").read_text(encoding="utf-8"))
    solution = json.loads(
        next(created.glob("finalists/*/solution.json")).read_text(encoding="utf-8")
    )
    selection = json.loads((created / "selection.json").read_text(encoding="utf-8"))
    decision = load_decision_register(
        ROOT / "project/requirements/decision-register.yaml"
    ).get("DEC-CANONICAL-DETAIL-003")
    assert run["solution_id"] == identity.solution_id
    assert run["solution_id"] != "AMANDA-RUN-002-PAVILION-S02"
    assert run["run_id"] == identity.solution_id
    assert "AMANDA-RUN-002" not in run["run_id"]
    assert solution["approval_hash"] == compute_design_approval_hash(solution)
    assert solution["geometry"]["canonical_source_hashes"] == [
        source.sha256 for source in identity.canonical_boards
    ]
    assert run["program_source_sha256"] == identity.program_source.sha256
    assert run["revit_calls"] == 0
    assert run["bim_eligible"] is False
    assert selection["detail_decision"] == decision.model_dump(mode="json")


def test_p3_requires_seventeen_structural_passes_and_keeps_canon_011_blocked(
    tmp_path: Path,
):
    exit_code, created = _build_current_run(tmp_path / "canonical-qa")

    assert exit_code == 0
    qa = json.loads((created / "canonical-qa.json").read_text(encoding="utf-8"))
    assert qa["summary"] == {
        "checks": 18,
        "pass": 17,
        "blocked": 1,
        "fail": 0,
        "critical_failures": 0,
    }
    can011 = next(item for item in qa["checks"] if item["check_id"] == "CANON-011")
    assert can011["status"] == "BLOCKED"
    assert "reviewed_stages=[]" in can011["evidence"]
    assert "required_stages=" in can011["evidence"]


def test_p3_qa_rejects_duplicate_check_id_even_when_status_counts_match():
    profile = CanonicalReferenceProfile.load(ROOT)
    layout = run_builder.build_canonical_pavilion_layout(PROGRAM, profile)
    checks = run_builder.run_canonical_checks(layout, profile)
    checks[-1] = checks[-2]
    qa = run_builder._qa_payload(checks)

    with pytest.raises(run_builder.CanonicalRunError, match="exactly CANON-001 through CANON-018"):
        run_builder._require_p3_qa(checks, qa)


def test_p3_layout_and_approval_hashes_are_repeatable(tmp_path: Path):
    first_exit, first_dir = _build_current_run(tmp_path / "first")
    second_exit, second_dir = _build_current_run(tmp_path / "second")

    assert first_exit == second_exit == 0
    assert _files(first_dir) == _files(second_dir)


def test_p3_hashed_run_artifacts_are_not_line_ending_normalized():
    path = (
        "design-engine/runs/AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C/run.json"
    )
    completed = subprocess.run(
        ["git", "check-attr", "text", "--", path],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert f"{path}: text: unset" in completed.stdout


def test_builder_rejects_identity_mismatched_four_board_profile(tmp_path: Path):
    profile = _profile()
    identity = assign_canonical_solution_identity(ROOT)
    output = tmp_path / "mismatched-source"

    with pytest.raises(run_builder.CanonicalRunError, match="identity.*board hashes"):
        run_builder.build_canonical_pavilion_run(
            PROGRAM, profile, identity, output, repository_root=ROOT
        )

    assert not output.exists()


def test_builder_rejects_self_consistent_identity_with_fabricated_p1_report_hash(
    tmp_path: Path,
):
    profile = CanonicalReferenceProfile.load(ROOT)
    identity = assign_canonical_solution_identity(ROOT)
    payload = identity.model_dump(mode="json")
    payload["reconciliation_report"]["sha256"] = "e" * 64
    material = {
        key: payload[key]
        for key in (
            "canonical_boards",
            "program_source",
            "reconciliation_id",
            "reconciliation_report",
        )
    }
    encoded = json.dumps(
        material, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    fingerprint = hashlib.sha256(encoded).hexdigest()
    payload["identity_fingerprint"] = fingerprint
    payload["solution_id"] = (
        "AMANDA-RUN-003-PAVILION-CANONICAL-" + fingerprint[:12].upper()
    )
    fabricated_identity = CanonicalSolutionIdentity.model_validate(payload)
    output = tmp_path / "fabricated-reconciliation"

    with pytest.raises(run_builder.CanonicalRunError, match="P1-T01 report"):
        run_builder.build_canonical_pavilion_run(
            PROGRAM, profile, fabricated_identity, output, repository_root=ROOT
        )

    assert not output.exists()


def test_critical_canonical_failure_returns_nonzero_without_partial_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    output = tmp_path / "blocked-run"
    monkeypatch.setattr(
        run_builder,
        "_load_inputs",
        lambda _root: (
            PROGRAM,
            CanonicalReferenceProfile.load(ROOT),
            assign_canonical_solution_identity(ROOT),
        ),
    )
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
