"""CLI contracts for the deterministic Revit Tool Lab surface."""

import os
import subprocess
import sys
from pathlib import Path

import yaml
from typer.testing import CliRunner

from amanda_agent.cli import app

runner = CliRunner()


def write_tool_lab_state(
    root: Path,
    *,
    capabilities: dict | None = None,
    provider_status: str = "PASS",
) -> None:
    state = root / "state"
    (state / "providers").mkdir(parents=True)
    (state / "tool-health.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "tools": {},
                "providers": {"horizun": {"status": "HEALTHY"}},
                "revit": {"status": "DETECTED", "selected": "27.2.0.39"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (state / "providers" / "horizun-toolmap.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "provider": "horizun",
                "provenance": {"source_commit": "abc123"},
                "capabilities": capabilities or {},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (state / "bim-environment.lock.yaml").write_text(
        yaml.safe_dump(
            {
                "revit": {"selected_build": "27.2.0.39"},
                "providers": {
                    "horizun": {
                        "source_commit": "abc123",
                        "status": provider_status,
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (state / "task-graph.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "tasks": {
                    "P02-T01": {
                        "id": "P02-T01",
                        "phase": "PHASE_02",
                        "plan_path": "docs/plan/CURRENT.md",
                        "title": "read capability",
                        "status": "PASS",
                        "evidence": [],
                    },
                    "P02-T02": {
                        "id": "P02-T02",
                        "phase": "PHASE_02",
                        "plan_path": "docs/plan/CURRENT.md",
                        "title": "failed capability",
                        "status": "FAIL",
                        "evidence": [],
                    },
                    "P02-T03": {
                        "id": "P02-T03",
                        "phase": "PHASE_02",
                        "plan_path": "docs/plan/CURRENT.md",
                        "title": "pending capability",
                        "status": "PENDING",
                        "evidence": [],
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_status_reads_provider_health_commit_and_task_counts(
    tmp_path: Path, monkeypatch
):
    write_tool_lab_state(tmp_path)
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["tool-lab", "status"])

    assert result.exit_code == 0, result.output
    assert "provider horizun" in result.stdout
    assert "commit abc123" in result.stdout
    assert "health HEALTHY" in result.stdout
    assert "PASS 1" in result.stdout
    assert "FAIL 1" in result.stdout
    assert "UNTESTED 1" in result.stdout


def test_module_invocation_renders_tool_lab_status(
    tmp_path: Path, monkeypatch
):
    write_tool_lab_state(tmp_path)
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))
    environment = os.environ.copy()
    environment["AMANDA_PROJECT_ROOT"] = str(tmp_path)
    environment["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, "-m", "amanda_agent.cli", "tool-lab", "status"],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "provider horizun" in result.stdout
    assert "PASS 1" in result.stdout


def test_queue_puts_required_untested_capabilities_first_without_paths(
    tmp_path: Path, monkeypatch
):
    write_tool_lab_state(
        tmp_path,
        capabilities={
            "level": {"required": True, "status": "UNTESTED", "writes": True},
            "wall": {"required": True, "status": "PASS", "writes": True},
            "optional": {"required": False, "status": "UNTESTED"},
        },
    )
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["tool-lab", "queue"])

    assert result.exit_code == 0, result.output
    assert result.stdout.index("level") < result.stdout.index("wall")
    assert "optional" not in result.stdout
    assert "AmandaProduction.rvt" not in result.stdout
    assert str(tmp_path) not in result.stdout


def test_verify_registry_fails_for_an_untested_preferred_provider(
    tmp_path: Path, monkeypatch
):
    write_tool_lab_state(
        tmp_path,
        capabilities={
            "level": {
                "required": True,
                "status": "UNTESTED",
                "writes": True,
                "save_reopen": True,
            }
        },
        provider_status="UNTESTED",
    )
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["tool-lab", "verify-registry"])

    assert result.exit_code != 0
    assert "UNTESTED" in result.output


def test_verify_registry_fails_when_write_capability_lacks_save_reopen(
    tmp_path: Path, monkeypatch
):
    write_tool_lab_state(
        tmp_path,
        capabilities={
            "wall": {
                "required": True,
                "status": "PASS",
                "writes": True,
                "save_reopen": False,
            }
        },
    )
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["tool-lab", "verify-registry"])

    assert result.exit_code != 0
    assert "save/reopen" in result.output


def test_verify_registry_reads_the_capability_registry_when_present(
    tmp_path: Path, monkeypatch
):
    write_tool_lab_state(tmp_path, capabilities={})
    (tmp_path / "state" / "capabilities.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "provider": "horizun",
                        "status": "PASS",
                        "priority": 1,
                        "tested_scope": {
                            "operation": "create_wall",
                            "writes": True,
                        },
                        "save_reopen": False,
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["tool-lab", "verify-registry"])

    assert result.exit_code != 0
    assert "create_wall" in result.output
    assert "save/reopen" in result.output


def test_verify_registry_honors_an_explicit_preferred_provider(
    tmp_path: Path, monkeypatch
):
    write_tool_lab_state(tmp_path, capabilities={})
    lock_path = tmp_path / "state" / "bim-environment.lock.yaml"
    lock = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    lock["preferred_provider"] = "revitcortex"
    lock["providers"]["revitcortex"] = {
        "source_commit": "def456",
        "status": "FAIL",
    }
    lock_path.write_text(yaml.safe_dump(lock, sort_keys=False), encoding="utf-8")
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["tool-lab", "verify-registry"])

    assert result.exit_code != 0
    assert "preferred revitcortex" in result.output
    assert "status FAIL" in result.output


def test_verify_registry_treats_provider_health_failure_as_failure(
    tmp_path: Path, monkeypatch
):
    write_tool_lab_state(
        tmp_path,
        capabilities={
            "wall": {
                "required": True,
                "status": "PASS",
                "writes": True,
                "save_reopen": True,
            }
        },
    )
    health_path = tmp_path / "state" / "tool-health.yaml"
    health = yaml.safe_load(health_path.read_text(encoding="utf-8"))
    health["providers"]["horizun"] = {"health": "FAIL"}
    health_path.write_text(yaml.safe_dump(health, sort_keys=False), encoding="utf-8")
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["tool-lab", "verify-registry"])

    assert result.exit_code != 0
    assert "preferred provider horizun status FAIL" in result.output


def test_verify_registry_requires_both_save_and_reopen_evidence(
    tmp_path: Path, monkeypatch
):
    write_tool_lab_state(
        tmp_path,
        capabilities={
            "wall": {
                "required": True,
                "status": "PASS",
                "writes": True,
                "evidence": [{"reopened": True}],
            }
        },
    )
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["tool-lab", "verify-registry"])

    assert result.exit_code != 0
    assert "save/reopen" in result.output
