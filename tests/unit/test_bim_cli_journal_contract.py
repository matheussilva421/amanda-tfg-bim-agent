"""Focused CLI contract tests for compiled BIM plans and execution journals."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from amanda_agent.bim.diff import DiffAction
from amanda_agent.bim.plan import BimPlan, PlanOperation
from amanda_agent.commands.bim import bim_app

runner = CliRunner()


def _plan_file(tmp_path: Path, *, operation_count: int = 1) -> Path:
    operations = [
        PlanOperation(
            task_id=f"P05-T07-{index:04d}",
            logical_id=f"wall-{index}",
            action=DiffAction.CREATE,
            semantic_capability="revit.create_element",
            desired_payload={"category": "wall", "index": index},
            verification_rules=["independent_requery", "document_matches"],
            preferred_provider="synthetic-provider",
            revit_build="2027",
            tool_schema_hash="schema-test",
        )
        for index in range(1, operation_count + 1)
    ]
    plan = BimPlan(
        generated_at=datetime(2026, 9, 15, tzinfo=UTC),
        document_id="synthetic-courtyard",
        managed_count=operation_count,
        operations=operations,
        fixture=True,
    )
    path = tmp_path / "BIM_PLAN.json"
    path.write_text(
        json.dumps(plan.model_dump(mode="json"), indent=2), encoding="utf-8"
    )
    return path


def _output(result) -> str:
    return result.stdout + getattr(result, "stderr", "")


def _journal_lines(tmp_path: Path) -> list[dict]:
    path = tmp_path / "BIM_EXECUTION_JOURNAL.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_plan_command_materializes_verifiable_json_and_markdown(tmp_path: Path):
    plan_path = _plan_file(tmp_path)

    result = runner.invoke(bim_app, ["plan", "--solution", str(plan_path)])

    assert result.exit_code == 0
    generated_json = tmp_path / "BIM_PLAN.json"
    generated_markdown = tmp_path / "BIM_PLAN.md"
    assert generated_json.is_file()
    assert generated_markdown.is_file()
    BimPlan.model_validate(json.loads(generated_json.read_text(encoding="utf-8")))
    assert "wall-1" in generated_markdown.read_text(encoding="utf-8")
    assert "read-only" in result.stdout.lower()


def test_claim_creates_durable_journal_and_duplicate_claim_is_refused(tmp_path: Path):
    plan_path = _plan_file(tmp_path)

    claimed = runner.invoke(bim_app, ["claim", "--plan", str(plan_path)])
    duplicate = runner.invoke(bim_app, ["claim", "--plan", str(plan_path)])

    assert claimed.exit_code == 0
    assert "P05-T07-0001" in claimed.stdout
    assert duplicate.exit_code != 0
    assert "already claimed" in _output(duplicate).lower()
    lines = _journal_lines(tmp_path)
    assert len(lines) == 1
    event = lines[0]
    assert event["operation_id"] == "P05-T07-0001"
    assert event["state"] == "CLAIMED"
    assert event["plan_sha256"]
    assert event["input_hashes"]
    assert event["checkpoint_hash"] is None
    assert event["document_hash"] is None
    assert event["lease_token"]
    assert event["provider_version"] == "synthetic-provider"
    assert event["schema_version"] == 1
    assert event["tool_schema_hash"] == "schema-test"
    assert event["dependencies"] == []
    assert event["intended_delta"]["logical_id"] == "wall-1"
    assert event["verifier"] == ["independent_requery", "document_matches"]


def test_record_result_requires_evidence_and_marks_claim_verified(tmp_path: Path):
    plan_path = _plan_file(tmp_path)
    runner.invoke(bim_app, ["claim", "--plan", str(plan_path)])

    missing = runner.invoke(
        bim_app, ["record-result", "--operation-id", "P05-T07-0001"]
    )
    assert missing.exit_code != 0
    assert "evidence" in _output(missing).lower()

    evidence = tmp_path / "result.json"
    evidence.write_text(
        json.dumps(
            {
                "operation_id": "P05-T07-0001",
                "independent_requery": True,
                "unique_id": "uid:wall-1",
            }
        ),
        encoding="utf-8",
    )
    recorded = runner.invoke(
        bim_app,
        [
            "record-result",
            "--operation-id",
            "P05-T07-0001",
            "--evidence",
            str(evidence),
        ],
    )

    assert recorded.exit_code == 0
    assert "PASS" in recorded.stdout
    lines = _journal_lines(tmp_path)
    assert len(lines) == 2
    assert lines[-1]["state"] == "VERIFIED"
    assert lines[-1]["result_status"] == "PASS"
    assert lines[-1]["evidence_sha256"]
    assert lines[-1]["evidence_path"] == str(evidence.resolve())


def test_journal_state_survives_reopening_the_journal(tmp_path: Path):
    from amanda_agent.bim.journal import ExecutionJournal

    plan_path = _plan_file(tmp_path)
    runner.invoke(bim_app, ["claim", "--plan", str(plan_path)])
    evidence = tmp_path / "result.txt"
    evidence.write_text("independent requery PASS\n", encoding="utf-8")
    runner.invoke(
        bim_app,
        [
            "record-result",
            "--operation-id",
            "P05-T07-0001",
            "--evidence",
            str(evidence),
        ],
    )

    reopened = ExecutionJournal(tmp_path / "BIM_EXECUTION_JOURNAL.jsonl")

    assert reopened.state_for("P05-T07-0001") == "VERIFIED"
    assert reopened.event_count == 2


def test_record_result_rejects_an_invalid_evidence_path(tmp_path: Path):
    plan_path = _plan_file(tmp_path)
    runner.invoke(bim_app, ["claim", "--plan", str(plan_path)])

    invalid = runner.invoke(
        bim_app,
        [
            "record-result",
            "--operation-id",
            "P05-T07-0001",
            "--evidence",
            str(tmp_path / "missing-result.json"),
        ],
    )

    assert invalid.exit_code != 0
    assert "evidence" in _output(invalid).lower()
    assert len(_journal_lines(tmp_path)) == 1


def test_synthetic_e2e_report_is_explicitly_labeled_and_has_required_sections():
    report = (
        Path(__file__).resolve().parents[2]
        / "tool-lab"
        / "reports"
        / "bim-compiler-e2e.md"
    )

    text = report.read_text(encoding="utf-8")

    assert "E2E sintético" in text
    assert "execução real" in text
    assert "provider" in text.lower()
    assert "fallback" in text.lower()
    assert "duração" in text.lower()
