"""Contratos da validacao one-command da ingestao."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from amanda_agent.cli import app

ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner()


def _copy_validation_fixture(target: Path) -> Path:
    shutil.copytree(ROOT / "docs" / "source", target / "docs" / "source")
    shutil.copytree(ROOT / "project", target / "project")
    (target / "state").mkdir(parents=True)
    shutil.copy2(ROOT / "state" / "blockers.yaml", target / "state" / "blockers.yaml")
    return target


def test_validation_accepts_missing_topography_as_a_limited_study(tmp_path: Path):
    root = _copy_validation_fixture(tmp_path / "valid")

    result = runner.invoke(app, ["ingest", "--validate-only"], env={"AMANDA_PROJECT_ROOT": str(root)})

    assert result.exit_code == 0, result.stdout
    assert "GO_WITH_LIMITATIONS" in result.stdout
    report = (root / "docs" / "reports" / "ingest-report.md").read_text(encoding="utf-8")
    assert "GO_WITH_LIMITATIONS" in report
    for blocker_id in (
        "SITE_TOPOGRAPHY",
        "SITE_BOUNDARY",
        "SITE_OCCUPANCY",
        "SITE_FRONTAGE_COUNT",
        "SITE_TRUE_NORTH",
    ):
        assert f"- {blocker_id}" in report


def test_validation_report_is_short_portuguese_and_lists_exact_blockers(
    tmp_path: Path,
):
    root = _copy_validation_fixture(tmp_path / "valid")
    result = runner.invoke(app, ["ingest", "--validate-only"], env={"AMANDA_PROJECT_ROOT": str(root)})
    report_path = root / "docs" / "reports" / "ingest-report.md"
    report = report_path.read_text(encoding="utf-8")

    assert result.exit_code == 0, result.stdout
    assert "# Relatorio de validacao da ingestao" in report
    assert "Comando" in report
    assert "Data" in report
    assert "GO_WITH_LIMITATIONS" in report
    for blocker_id in (
        "SITE_TOPOGRAPHY",
        "SITE_BOUNDARY",
        "SITE_OCCUPANCY",
        "SITE_FRONTAGE_COUNT",
        "SITE_TRUE_NORTH",
    ):
        assert f"- {blocker_id}" in report
    assert "PASS" in report
    assert "FAIL" in report


def test_malformed_canonical_program_is_no_go(tmp_path: Path):
    root = _copy_validation_fixture(tmp_path / "corrupt")
    program_path = root / "project" / "requirements" / "program.json"
    program_path.write_text("{\"schema_version\":", encoding="utf-8")

    result = runner.invoke(app, ["ingest", "--validate-only"], env={"AMANDA_PROJECT_ROOT": str(root)})

    assert result.exit_code != 0
    assert "NO_GO" in result.stdout
    assert "program.json" in (result.stdout + (root / "docs" / "reports" / "ingest-report.md").read_text(encoding="utf-8"))


def test_validate_only_cli_returns_nonzero_for_malformed_canonical(
    tmp_path: Path, monkeypatch
):
    root = _copy_validation_fixture(tmp_path / "corrupt-cli")
    program_path = root / "project" / "requirements" / "program.json"
    payload = json.loads(program_path.read_text(encoding="utf-8"))
    payload["reconciliation"]["ok"] = False
    program_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(root))

    result = runner.invoke(app, ["ingest", "--validate-only"])

    assert result.exit_code != 0
    assert "NO_GO" in result.stdout
    assert (root / "docs" / "reports" / "ingest-report.md").exists()
