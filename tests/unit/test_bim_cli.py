"""Behavioural contract for the read-only BIM CLI surface."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from amanda_agent.bim.diff import DiffAction
from amanda_agent.bim.plan import BimPlan, PlanOperation
from amanda_agent.commands.bim import bim_app

runner = CliRunner()


def _plan_file(tmp_path: Path) -> Path:
    plan = BimPlan(
        generated_at=datetime(2026, 9, 15, tzinfo=UTC),
        document_id="synthetic-courtyard",
        managed_count=1,
        operations=[
            PlanOperation(
                task_id="T0001:wall-1:CREATE",
                logical_id="wall-1",
                action=DiffAction.CREATE,
                semantic_capability="revit.create_element",
                desired_payload={"category": "wall"},
                verification_rules=["independent_requery", "document_matches"],
                preferred_provider="synthetic",
            )
        ],
    )
    path = tmp_path / "BIM_PLAN.json"
    path.write_text(json.dumps(plan.model_dump(mode="json")), encoding="utf-8")
    return path


def test_bim_help_exposes_plan_verification_and_status_commands():
    result = runner.invoke(bim_app, ["--help"])

    assert result.exit_code == 0
    assert "plan" in result.stdout
    assert "verify-plan" in result.stdout
    assert "status" in result.stdout


def test_bim_plan_inspects_a_plan_without_an_execution_flag(tmp_path: Path):
    plan_path = _plan_file(tmp_path)

    result = runner.invoke(bim_app, ["plan", "--solution", str(plan_path)])

    assert result.exit_code == 0
    assert "synthetic-courtyard" in result.stdout
    assert "wall-1" in result.stdout
    assert "read-only" in result.stdout.lower()


def test_bim_verify_plan_reports_write_read_verify_rules(tmp_path: Path):
    plan_path = _plan_file(tmp_path)

    result = runner.invoke(bim_app, ["verify-plan", str(plan_path)])

    assert result.exit_code == 0
    assert "independent_requery" in result.stdout
    assert "document_matches" in result.stdout
    assert "write-read-verify" in result.stdout.lower()


def test_bim_status_is_read_only_and_does_not_require_a_target():
    result = runner.invoke(bim_app, ["status"])

    assert result.exit_code == 0
    assert "read-only" in result.stdout.lower()
    assert "synthetic_lab" in result.stdout.lower()


def test_bim_execute_requires_explicit_synthetic_lab_and_execute_flags(tmp_path: Path):
    plan_path = _plan_file(tmp_path)

    refused = runner.invoke(
        bim_app,
        ["execute", "--plan", str(plan_path), "--mode", "SYNTHETIC_LAB"],
    )
    assert refused.exit_code != 0
    assert "execute" in (refused.stdout + refused.stderr).lower()

    accepted_help = runner.invoke(bim_app, ["execute", "--help"])
    assert accepted_help.exit_code == 0
    assert "--execute" in accepted_help.stdout
    assert "--mode" in accepted_help.stdout


def test_bim_execute_in_synthetic_lab_reports_write_read_verify(tmp_path: Path):
    plan_path = _plan_file(tmp_path)

    result = runner.invoke(
        bim_app,
        [
            "execute",
            "--plan",
            str(plan_path),
            "--mode",
            "SYNTHETIC_LAB",
            "--fixture",
            "--execute",
        ],
    )

    assert result.exit_code == 0
    assert "SYNTHETIC_LAB" in result.stdout
    assert "write" in result.stdout.lower()
    assert "read" in result.stdout.lower()
    assert "verify" in result.stdout.lower()
    assert "PASS" in result.stdout
