"""bootstrap is idempotent and never overwrites established state."""

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from amanda_agent.cli import app
from amanda_agent.commands.bootstrap import bootstrap_environment

runner = CliRunner()


def test_bootstrap_creates_the_foundation_once(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["bootstrap"])

    assert result.exit_code == 0, result.output
    for relative in (
        "PROJECT_STATE.yaml",
        "state/environment-report.json",
        "state/bim-environment.lock.yaml",
        "state/blockers.yaml",
        "state/tool-health.yaml",
    ):
        assert (tmp_path / relative).exists(), relative


def test_second_run_preserves_existing_values(tmp_path: Path):
    bootstrap_environment(tmp_path)
    state_path = tmp_path / "PROJECT_STATE.yaml"
    edited = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    edited["next_task"] = "P01-T13-EDITED-BY-HAND"
    state_path.write_text(
        yaml.safe_dump(edited, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    before = state_path.read_bytes()

    second = bootstrap_environment(tmp_path)

    assert state_path.read_bytes() == before, "a second run must not rewrite state"
    assert "PROJECT_STATE.yaml" not in second["created"]
    assert "state/blockers.yaml" not in second["created"]


REFRESHABLE = {"state/environment-report.json"}


def test_second_run_creates_no_duplicate_configuration(tmp_path: Path):
    first = bootstrap_environment(tmp_path)
    second = bootstrap_environment(tmp_path)

    assert first["created"], "the first run must create something"
    durable = [item for item in second["created"] if item not in REFRESHABLE]
    assert durable == [], durable


def test_environment_report_is_a_live_refresh_not_configuration(tmp_path: Path):
    bootstrap_environment(tmp_path)
    report_path = tmp_path / "state" / "environment-report.json"
    stale = json.loads(report_path.read_text(encoding="utf-8"))
    stale["probes"] = []
    report_path.write_text(json.dumps(stale), encoding="utf-8")

    bootstrap_environment(tmp_path)

    refreshed = json.loads(report_path.read_text(encoding="utf-8"))
    assert refreshed["probes"], "the report must reflect the current host"


def test_bootstrap_installs_no_revit_provider(tmp_path: Path):
    result = bootstrap_environment(tmp_path)

    lock = yaml.safe_load(
        (tmp_path / "state" / "bim-environment.lock.yaml").read_text(encoding="utf-8")
    )
    assert "provider" not in lock
    assert result["report"]["revit"]["probe_status"] in {
        "DETECTED",
        "NOT_FOUND",
    }
