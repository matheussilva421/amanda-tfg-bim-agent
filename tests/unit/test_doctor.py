"""doctor is phase aware: a missing Revit blocks BIM work, not all work."""

import json
from pathlib import Path

from typer.testing import CliRunner

from amanda_agent.bootstrap.environment import CommandResult, ToolProbe
from amanda_agent.cli import app
from amanda_agent.commands.doctor import build_environment_report, evaluate_health

runner = CliRunner()


def make_probe(name, status, critical=False):
    return ToolProbe(name=name, status=status, critical=critical)


def test_missing_revit_blocks_only_the_bim_branch(tmp_path: Path):
    report = build_environment_report(
        revit={"probe_status": "NOT_FOUND", "installation_count": 0},
        probes=[make_probe("codex", "AVAILABLE", True)],
        root=tmp_path,
    )

    health = evaluate_health(report)

    assert health["critical_failure"] is False
    assert "PHASE_02" in health["blocked_phases"]
    assert "PHASE_03" not in health["blocked_phases"]
    assert "PHASE_04" not in health["blocked_phases"]


def test_missing_codex_is_critical(tmp_path: Path):
    report = build_environment_report(
        revit={"probe_status": "DETECTED", "installation_count": 1},
        probes=[make_probe("codex", "MISSING", True)],
        root=tmp_path,
    )

    health = evaluate_health(report)

    assert health["critical_failure"] is True
    assert health["exit_code"] != 0


def test_sdk_inventory_is_not_a_universal_failure(tmp_path: Path):
    report = build_environment_report(
        revit={"probe_status": "DETECTED", "installation_count": 1},
        probes=[
            make_probe("codex", "AVAILABLE", True),
            make_probe("dotnet", "MISSING"),
        ],
        root=tmp_path,
    )

    health = evaluate_health(report)

    assert health["critical_failure"] is False
    assert any(
        item["name"] == "dotnet" for item in report["inventory"]
    )


def test_doctor_writes_the_report_and_exits_nonzero_on_critical(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(
        "amanda_agent.commands.doctor.run_revit_detection",
        lambda: {"probe_status": "DETECTED", "installation_count": 1},
    )
    monkeypatch.setattr(
        "amanda_agent.commands.doctor.run_probes",
        lambda: [make_probe("codex", "MISSING", True)],
    )

    result = runner.invoke(app, ["doctor"])

    report_path = tmp_path / "state" / "environment-report.json"
    assert report_path.exists()
    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert written["schema_version"] == 1
    assert written["health"]["critical_failure"] is True
    assert result.exit_code != 0


def test_doctor_exits_zero_when_core_tools_are_present(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(
        "amanda_agent.commands.doctor.run_revit_detection",
        lambda: {"probe_status": "DETECTED", "installation_count": 1},
    )
    monkeypatch.setattr(
        "amanda_agent.commands.doctor.run_probes",
        lambda: [make_probe("codex", "AVAILABLE", True)],
    )

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0


def test_doctor_never_invokes_a_mutating_command(tmp_path: Path):
    """The probe runner is exercised through the real default path once."""
    issued = []

    def runner_fn(argv):
        issued.append(list(argv))
        return CommandResult(1, "", "missing")

    from amanda_agent.bootstrap.environment import probe_tools

    probe_tools(runner=runner_fn, which=lambda name: None)

    forbidden = {"install", "add", "update", "upgrade", "uninstall", "winget"}
    assert not any(forbidden & set(argv) for argv in issued), issued
