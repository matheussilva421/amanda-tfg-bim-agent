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
        "## Current state — P7-T01/R05 blocked at partial recovery"
        in handoff.splitlines()[:8]
    )
    assert "Authorization remains limited to P7-T01/R05 on RUN-003." in handoff
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


def test_elevated_runner_resolves_transport_and_records_resume_dispatch_blocker():
    project_state = yaml.safe_load(
        (ROOT / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    )
    transport_blocker = next(
        item
        for item in load_blockers(ROOT / "state")
        if item.id == "RUNNER_TRANSPORT_UNREACHABLE"
    )
    partial_recovery_blocker = next(
        item
        for item in load_blockers(ROOT / "state")
        if item.id == "R05_PARTIAL_RECOVERY_UNVERIFIED"
    )
    dispatch_blocker = next(
        item
        for item in load_blockers(ROOT / "state")
        if item.id == "R05_RESUME_DISPATCH_UNVERIFIED"
    )

    assert "RUNNER_TRANSPORT_UNREACHABLE:BLOCKING" not in project_state["blockers"]
    assert "R05_PARTIAL_RECOVERY_UNVERIFIED:BLOCKING" not in project_state["blockers"]
    assert "R05_RESUME_DISPATCH_UNVERIFIED:BLOCKING" in project_state["blockers"]
    assert transport_blocker.severity.value == "BLOCKING"
    assert transport_blocker.affected_tasks == ["P7-T01"]
    assert not transport_blocker.is_open
    assert partial_recovery_blocker.severity.value == "BLOCKING"
    assert partial_recovery_blocker.affected_tasks == ["P7-T01"]
    assert not partial_recovery_blocker.is_open
    assert dispatch_blocker.severity.value == "BLOCKING"
    assert dispatch_blocker.affected_tasks == ["P7-T01"]
    assert dispatch_blocker.is_open
