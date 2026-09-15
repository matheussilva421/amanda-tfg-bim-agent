"""Progress must survive the process that wrote it.

The reconciliation of Phase 01 is only credible if the recorded outcome can be
read back by a fresh process: this test writes through the real commands, then
reloads from disk the way the next session will.
"""

from pathlib import Path

from typer.testing import CliRunner

from amanda_agent.cli import app
from amanda_agent.models.state import ProjectState, TaskStatus
from amanda_agent.state.store import StateStore
from amanda_agent.state.tasks import TaskRecord, TaskRegistry, load_registry

runner = CliRunner()


def seed(root: Path) -> None:
    (root / "state").mkdir(parents=True, exist_ok=True)
    StateStore(root / "PROJECT_STATE.yaml").save(ProjectState())
    registry = TaskRegistry()
    registry.add(TaskRecord(id="P01-T01", phase="PHASE_01", plan_path="p1.md"))
    registry.add(
        TaskRecord(
            id="P01-T02",
            phase="PHASE_01",
            plan_path="p1.md",
            depends_on=["P01-T01"],
        )
    )
    registry.save(root / "state" / "task-graph.yaml")


def test_written_progress_is_readable_by_a_later_process(tmp_path: Path, monkeypatch):
    seed(tmp_path)
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))
    result = runner.invoke(
        app,
        [
            "advance",
            "--task",
            "P01-T01",
            "--status",
            "PASS",
            "--evidence",
            "pytest -q -> green",
        ],
    )
    assert result.exit_code == 0, result.stdout

    # A fresh read, as a new session would do it.
    reloaded = load_registry(tmp_path / "state" / "task-graph.yaml")
    assert str(reloaded.tasks["P01-T01"].status) == "PASS"
    assert reloaded.tasks["P01-T01"].evidence == ["pytest -q -> green"]
    assert reloaded.ready_tasks() == ["P01-T02"]

    state = StateStore(tmp_path / "PROJECT_STATE.yaml").load()
    assert state.last_completed_task == "P01-T01"
    assert state.next_task == "P01-T02"


def test_the_registry_survives_a_repeated_write(tmp_path: Path):
    """Saving twice must not duplicate, drop or reorder records."""
    path = tmp_path / "state" / "task-graph.yaml"
    registry = TaskRegistry()
    registry.add(TaskRecord(id="A", phase="P", plan_path="p.md", title="first"))
    registry.add(
        TaskRecord(id="B", phase="P", plan_path="p.md", depends_on=["A"])
    )
    registry.save(path)
    first = load_registry(path)
    first.set_status("A", "PASS")
    first.save(path)

    second = load_registry(path)
    assert sorted(second.tasks) == ["A", "B"]
    assert second.tasks["B"].depends_on == ["A"]
    assert str(second.tasks["A"].status) == "PASS"


def test_a_string_status_is_coerced_to_a_real_enum(tmp_path: Path):
    """A caller passing "PASS" must not leave a bare string in the file."""
    registry = TaskRegistry()
    registry.add(TaskRecord(id="A", phase="P", plan_path="p.md"))

    registry.set_status("A", "PASS_WITH_WARNINGS")
    assert registry.tasks["A"].status is TaskStatus.PASS_WITH_WARNINGS
    path = tmp_path / "state" / "task-graph.yaml"
    registry.save(path)
    assert "PASS_WITH_WARNINGS" in path.read_text(encoding="utf-8")


def test_evidence_for_an_unknown_task_is_refused():
    registry = TaskRegistry()
    try:
        registry.add_evidence("MISSING", "pytest -q -> green")
    except KeyError as exc:
        assert "MISSING" in str(exc)
    else:
        raise AssertionError("evidence must not attach to a task that is absent")
