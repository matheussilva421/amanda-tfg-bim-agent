from pathlib import Path
from datetime import datetime, timezone

import yaml


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
        "## Current state — P7-T01/R05 blocked at P6 checkpoint-open verification"
        in handoff.splitlines()[:8]
    )
    assert "P7-T01 stays `PENDING`; this continuation is restricted to R05." in handoff
    assert "authorized live R05 runner attempt" in handoff
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
