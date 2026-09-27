from datetime import datetime, timezone
from pathlib import Path

import yaml

from amanda_agent.commands.status import load_blockers

ROOT = Path(__file__).resolve().parents[2]


def test_status_dashboard_checkpoint_matches_project_state():
    project_state = yaml.safe_load(
        (ROOT / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    )
    dashboard = (ROOT / "state" / "status.md").read_text(encoding="utf-8")

    expected = f"- Current checkpoint: `{project_state['current_checkpoint']}`"
    assert expected in dashboard


def test_current_handoff_is_unambiguous_and_matches_p6_report_time():
    handoff = (ROOT / "state" / "HANDOFF.md").read_text(encoding="utf-8")
    assert (
        "## Current state — P7-T01/R05 blocked at production runner transport"
        in handoff.splitlines()[:8]
    )
    assert "Current authorization is R05 only." in handoff
    assert "RUNNER_TRANSPORT_UNREACHABLE:BLOCKING" in handoff
    assert "direct Horizun health reports HEALTHY" in handoff
    assert "captured window content was Chrome" in handoff
    assert "The third health-first retry at about 13:32Z" in handoff
    assert "RUN-003 lease was retained" in handoff
    assert "## Prior closeout — P4-T01 R04" in handoff
    assert "## Historical continuation — 2026-09-26 (P4-T01 / RUN-003 R04 geometry completion)" in handoff
    assert "## Current continuation — 2026-09-26 (P4-T01 / RUN-003 R04 geometry completion)" not in handoff

    report = (ROOT / "docs" / "reports" / "P6-T01-run003-visual-geometric-acceptance.md").read_text(encoding="utf-8")
    report_time = next(line.removeprefix("**Atualização:** ").removesuffix(" UTC") for line in report.splitlines() if line.startswith("**Atualização:**"))
    report_minute = datetime.strptime(report_time, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    history = yaml.safe_load((ROOT / "state" / "task-history.yaml").read_text(encoding="utf-8"))
    current_p6 = [entry for entry in history["entries"] if entry["task_id"] == "P6-T01"][-1]
    assert current_p6["status"] == "PASS"
    recorded = datetime.fromisoformat(current_p6["recorded_utc"].replace("Z", "+00:00"))
    assert report_minute == recorded.replace(second=0, microsecond=0)


def test_unreachable_production_runner_transport_is_a_formal_p7_blocker():
    project_state = yaml.safe_load(
        (ROOT / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    )
    blocker = next(
        item
        for item in load_blockers(ROOT / "state")
        if item.id == "RUNNER_TRANSPORT_UNREACHABLE"
    )

    assert "RUNNER_TRANSPORT_UNREACHABLE:BLOCKING" in project_state["blockers"]
    assert blocker.severity.value == "BLOCKING"
    assert blocker.affected_tasks == ["P7-T01"]
    assert blocker.is_open
