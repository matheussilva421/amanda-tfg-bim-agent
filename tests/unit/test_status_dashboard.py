import json
from pathlib import Path

from typer.testing import CliRunner

from amanda_agent.cli import app
from amanda_agent.models.state import ProjectState, TaskStatus
from amanda_agent.state.store import StateStore
from amanda_agent.state.tasks import TaskRecord, TaskRegistry
from amanda_agent.status_dashboard import (
    build_status_dashboard,
    render_status_markdown,
)

runner = CliRunner()


def _seed(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True)
    StateStore(tmp_path / "PROJECT_STATE.yaml").save(
        ProjectState(
            phase_id="PHASE_07B",
            phase_name="production-hardening",
            phase_status=TaskStatus.SUSPENDED,
            last_completed_task="P07-T15",
            next_task="P07-T17",
            selected_design="DESIGN-001",
            revit_stage="R13_DOCUMENTATION",
            current_checkpoint="revit/lab/R13.rvt",
            blockers=["SITE_TOPOGRAPHY"],
            last_verified_commit="abc1234",
        )
    )
    registry = TaskRegistry()
    registry.add(
        TaskRecord(
            id="P07-T15",
            phase="PHASE_07B",
            plan_path="p7.md",
            status=TaskStatus.PASS,
        )
    )
    registry.add(
        TaskRecord(
            id="P07-T17",
            phase="PHASE_07B",
            plan_path="p7.md",
            status=TaskStatus.PENDING,
            depends_on=["P07-T15"],
        )
    )
    registry.add(
        TaskRecord(
            id="P07-T18",
            phase="PHASE_07B",
            plan_path="p7.md",
            status=TaskStatus.CRITICAL_FAILURE,
        )
    )
    registry.save(state_dir / "task-graph.yaml")
    (state_dir / "bim-environment.lock.yaml").write_text(
        "revit:\n  selected_build: 27.2.0.39\n"
        "preferred_provider: horizun\n"
        "providers:\n  horizun:\n    status: VERIFIED\n",
        encoding="utf-8",
    )
    (state_dir / "tool-health.yaml").write_text(
        "providers:\n  horizun:\n    status: HEALTHY\n  fallback:\n    status: UNKNOWN\n",
        encoding="utf-8",
    )
    (state_dir / "blockers.yaml").write_text(
        "blockers:\n  - id: SITE_TOPOGRAPHY\n"
        "    summary: elevations missing\n    severity: BLOCKING\n",
        encoding="utf-8",
    )
    (state_dir / "capabilities.yaml").write_text(
        "schema_version: 1\nentries:\n"
        "  - provider: horizun\n    status: PASS\n    priority: 1\n"
        "    tested_scope: {operation: read, writes: false}\n"
        "  - provider: fallback\n    status: FAIL\n    priority: 2\n"
        "    tested_scope: {operation: write, writes: true}\n"
        "  - provider: future\n    status: UNTESTED\n    priority: 3\n"
        "    tested_scope: {operation: future, writes: false}\n",
        encoding="utf-8",
    )
    lease = state_dir / "locks" / "revit-writer.lock"
    lease.parent.mkdir()
    lease.write_text(
        json.dumps({"owner": "hades", "fencing_generation": 4}),
        encoding="utf-8",
    )


def test_dashboard_reads_state_and_all_required_operational_fields(tmp_path: Path):
    _seed(tmp_path)

    data = build_status_dashboard(tmp_path)
    markdown = render_status_markdown(data)

    assert "PHASE_07B" in markdown
    assert "P07-T17" in markdown
    assert "27.2.0.39" in markdown
    assert "horizun" in markdown
    assert "PASS: 1" in markdown
    assert "FAIL: 1" in markdown
    assert "UNTESTED: 1" in markdown
    assert "SITE_TOPOGRAPHY" in markdown
    assert "DESIGN-001" in markdown
    assert "R13_DOCUMENTATION" in markdown
    assert "revit/lab/R13.rvt" in markdown
    assert "hades" in markdown
    assert "abc1234" in markdown


def test_status_command_preserves_stdout_and_writes_dashboard(tmp_path: Path, monkeypatch):
    _seed(tmp_path)
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0, result.stdout
    assert "phase        PHASE_07B" in result.stdout
    assert (tmp_path / "state" / "status.md").is_file()
    assert "P07-T17" in (tmp_path / "state" / "status.md").read_text(encoding="utf-8")


def test_dashboard_reports_missing_evidence_without_inventing_green_state(
    tmp_path: Path,
):
    StateStore(tmp_path / "PROJECT_STATE.yaml").save(ProjectState())

    markdown = render_status_markdown(build_status_dashboard(tmp_path))

    assert "not recorded" in markdown.lower() or "unknown" in markdown.lower()
    assert "27.2.0.39" not in markdown
