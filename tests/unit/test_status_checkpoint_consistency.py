import json
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


def test_current_handoff_records_modal_health_blocker_and_matches_p6_report_time():
    handoff = (ROOT / "state" / "HANDOFF.md").read_text(encoding="utf-8")
    current_heading = "## Current state — P7-T01/R05 blocked by Revit modal health gate"
    assert current_heading in handoff.splitlines()[:8]
    current = handoff.split(current_heading, 1)[1].split("\n## Previous update", 1)[0]
    assert "Authorization remains limited to P7-T01/R05 on RUN-003." in current
    assert "The former transport and resume-dispatch blockers are resolved." in current
    assert "`R05_STAGE_OPERATIONS_UNRECONCILED:BLOCKING` is the active blocker." in current
    assert "horizun_get_dimension_references" in current
    assert "courtyard void" in current
    assert "complete OST_Views inventory" in current
    assert "latest live recovery stopped at the incomplete view-inventory gate" in current
    assert "cursor-paged complete OST_Views inventory" in current
    assert "did not return exactly one `{3D}` view" in current
    assert "missing/untyped `horizun_document_session` replies fail with a bounded diagnostic" in current
    assert "R05-2f373fcb3511-p6-readback-diagnostic-1bfe69b64324.json" in current
    assert "No R05 geometry operation, save, or checkpoint occurred" in current
    assert "RUN-003 live model no longer matches the accepted P6 element count" in current
    assert "RUN-003 partial target could not be reactivated for comparison" in current
    assert "RUN-003 P6 checkpoint close was not verified: None" in current
    assert "R05-2f373fcb3511-p6-readback-diagnostic-1bfe69b64324.json" in current
    assert "PID 12660" in current
    assert "close status remains unverified" in current
    assert "03:46:36Z" in current
    assert "BLOCKED_BY_TOOL_MODAL_DIALOG" in current
    assert "R05-modal-health-blocker-20260929-0350.json" in current
    assert "before readiness, lease acquisition, or R05 dispatch" in current
    assert "model write, save, or checkpoint was dispatched" in current
    assert "04:02:56Z" in current
    assert "R05_PARTIAL_RECOVERY_UNVERIFIED:BLOCKING" not in current
    assert "R06 and later remain NOT STARTED." in current

    report = (
        ROOT / "docs" / "reports" / "P6-T01-run003-visual-geometric-acceptance.md"
    ).read_text(encoding="utf-8")
    report_time = next(
        line.removeprefix("**Atualização:** ").removesuffix(" UTC")
        for line in report.splitlines()
        if line.startswith("**Atualização:**")
    )
    report_minute = datetime.strptime(report_time, "%Y-%m-%d %H:%M").replace(
        tzinfo=timezone.utc
    )
    history = yaml.safe_load(
        (ROOT / "state" / "task-history.yaml").read_text(encoding="utf-8")
    )
    current_p6 = [
        entry for entry in history["entries"] if entry["task_id"] == "P6-T01"
    ][-1]
    assert current_p6["status"] == "PASS"
    recorded = datetime.fromisoformat(
        current_p6["recorded_utc"].replace("Z", "+00:00")
    )
    assert report_minute == recorded.replace(second=0, microsecond=0)


def test_latest_modal_health_retry_is_recorded_without_lease_or_write():
    journal_path = (
        ROOT
        / "revit"
        / "production"
        / "journals"
        / "R05-modal-health-blocker-20260929-0405.json"
    )
    journal = json.loads(journal_path.read_text(encoding="utf-8"))

    assert journal["status"] == "BLOCKED_BY_TOOL_MODAL_DIALOG"
    assert journal["runner_exit_code"] == 1
    assert journal["provider_tool"] == "horizun_health"
    assert journal["runner_start_after_utc_check"] == "2026-09-29T04:05:34Z"
    assert journal["provider_ready"] is False
    assert journal["lease_acquired"] is False
    assert journal["stage_dispatch_started"] is False
    assert journal["geometry_write_dispatched"] is False
    assert journal["save_or_checkpoint_dispatched"] is False
    assert journal["postrun_state"]["modal_disposition"] == "unresolved"
    assert journal["postrun_state"]["writer_lock_present"] is False
    processes = {
        process["pid"]: process
        for process in journal["postrun_state"]["revit_processes"]
    }
    assert processes[3364]["horizun_module_loaded"] is False
    assert processes[12660]["horizun_module_loaded"] is True
    assert processes[12660]["main_window_handle"] == 0
    assert journal["quiet_deadline_utc"] == "2026-09-29T04:16:00Z"


def test_official_runner_dispatches_r05_and_records_stage_operation_blocker():
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
    stage_operations_blocker = next(
        item
        for item in load_blockers(ROOT / "state")
        if item.id == "R05_STAGE_OPERATIONS_UNRECONCILED"
    )

    assert "RUNNER_TRANSPORT_UNREACHABLE:BLOCKING" not in project_state["blockers"]
    assert "R05_PARTIAL_RECOVERY_UNVERIFIED:BLOCKING" not in project_state["blockers"]
    assert "R05_RESUME_DISPATCH_UNVERIFIED:BLOCKING" not in project_state["blockers"]
    assert "R05_STAGE_OPERATIONS_UNRECONCILED:BLOCKING" in project_state["blockers"]
    assert transport_blocker.severity.value == "BLOCKING"
    assert transport_blocker.affected_tasks == ["P7-T01"]
    assert not transport_blocker.is_open
    assert partial_recovery_blocker.severity.value == "BLOCKING"
    assert partial_recovery_blocker.affected_tasks == ["P7-T01"]
    assert not partial_recovery_blocker.is_open
    assert dispatch_blocker.severity.value == "BLOCKING"
    assert dispatch_blocker.affected_tasks == ["P7-T01"]
    assert not dispatch_blocker.is_open
    assert stage_operations_blocker.severity.value == "BLOCKING"
    assert stage_operations_blocker.affected_tasks == ["P7-T01"]
    assert stage_operations_blocker.is_open
