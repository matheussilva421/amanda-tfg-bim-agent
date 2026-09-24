"""The control plane can move a task forward, and refuses to fake it."""

from pathlib import Path

import yaml
from typer.testing import CliRunner

from amanda_agent.cli import app
from amanda_agent.models.state import ProjectState, TaskStatus
from amanda_agent.state.store import StateStore
from amanda_agent.state.tasks import TaskRecord, TaskRegistry, load_registry

runner = CliRunner()


def build_root(tmp_path: Path, *, tasks: list | None = None) -> Path:
    """A minimal project root with durable state and a task registry."""
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    StateStore(tmp_path / "PROJECT_STATE.yaml").save(ProjectState())
    registry = TaskRegistry()
    for record in tasks or [
        TaskRecord(
            id="P01-T01",
            phase="PHASE_01",
            plan_path="docs/plan/CURRENT.md",
        ),
        TaskRecord(
            id="P01-T02",
            phase="PHASE_01",
            plan_path="docs/plan/CURRENT.md",
            depends_on=["P01-T01"],
        ),
    ]:
        registry.add(record)
    registry.validate()
    registry.save(state_dir / "task-graph.yaml")
    return tmp_path


def test_task_graph_command_reports_progress_without_mutating_state(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(build_root(tmp_path)))
    graph = tmp_path / "state" / "task-graph.yaml"
    state = tmp_path / "PROJECT_STATE.yaml"
    before = (graph.read_bytes(), state.read_bytes())

    result = runner.invoke(app, ["task-graph"])

    assert result.exit_code == 0
    assert "total" in result.stdout
    ready_line = next(
        line for line in result.stdout.splitlines() if line.startswith("ready")
    )
    blocked_line = next(
        line for line in result.stdout.splitlines() if line.startswith("blocked")
    )
    assert "P01-T01" in ready_line, "an unblocked task is ready"
    assert "P01-T02" not in ready_line, "a dependent is not ready yet"
    assert "P01-T02" in blocked_line
    assert (graph.read_bytes(), state.read_bytes()) == before


def test_task_graph_blocks_dependents_until_the_dependency_passes(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(build_root(tmp_path)))

    first = runner.invoke(app, ["task-graph"])
    first_ready = next(
        line for line in first.stdout.splitlines() if line.startswith("ready")
    )
    assert "P01-T01" in first_ready

    done = runner.invoke(
        app,
        [
            "advance",
            "--task",
            "P01-T01",
            "--status",
            "PASS",
            "--evidence",
            "pytest tests/unit -q -> 81 passed",
        ],
    )
    assert done.exit_code == 0, done.stdout

    second = runner.invoke(app, ["task-graph"])
    second_ready = next(
        line for line in second.stdout.splitlines() if line.startswith("ready")
    )
    assert "P01-T02" in second_ready, "the dependent becomes ready on PASS"


def test_advance_refuses_a_task_without_evidence(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(build_root(tmp_path)))
    registry = tmp_path / "state" / "task-graph.yaml"
    before = registry.read_bytes()

    result = runner.invoke(
        app, ["advance", "--task", "P01-T01", "--status", "PASS"]
    )

    assert result.exit_code != 0
    assert "evidence" in (result.stdout + str(result.output)).lower()
    assert registry.read_bytes() == before, "a refused advance changes nothing"


def test_advance_refuses_a_non_completion_status(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(build_root(tmp_path)))

    result = runner.invoke(
        app,
        [
            "advance",
            "--task",
            "P01-T01",
            "--status",
            "RUNNING",
            "--evidence",
            "started",
        ],
    )

    assert result.exit_code != 0
    assert "RUNNING" in (result.stdout + str(result.output))


def test_advance_refuses_a_task_whose_dependency_is_still_open(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(build_root(tmp_path)))
    registry = tmp_path / "state" / "task-graph.yaml"
    before = registry.read_bytes()

    result = runner.invoke(
        app,
        [
            "advance",
            "--task",
            "P01-T02",
            "--status",
            "PASS",
            "--evidence",
            "nothing proved the dependency yet",
        ],
    )

    assert result.exit_code != 0
    text = result.stdout + str(result.output)
    assert "P01-T01" in text
    assert "--allow-unready" in text
    assert registry.read_bytes() == before


def test_the_override_flag_records_the_reason_with_the_completion(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(build_root(tmp_path)))

    result = runner.invoke(
        app,
        [
            "advance",
            "--task",
            "P01-T02",
            "--status",
            "PASS_WITH_WARNINGS",
            "--evidence",
            "capability proven on the disposable fixture",
            "--allow-unready",
            "P01-T01 needs the operator to approve the add-in dialog",
        ],
    )

    assert result.exit_code == 0, result.stdout
    registry = load_registry(tmp_path / "state" / "task-graph.yaml")
    assert registry.tasks["P01-T02"].status == TaskStatus.PASS_WITH_WARNINGS
    assert any(
        "add-in dialog" in reference
        for reference in registry.tasks["P01-T02"].evidence
    )


def test_advance_records_history_and_advances_the_state(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(build_root(tmp_path)))

    result = runner.invoke(
        app,
        [
            "advance",
            "--task",
            "P01-T01",
            "--status",
            "PASS",
            "--evidence",
            "pytest tests/unit tests/bootstrap -q -> 81 passed",
        ],
    )

    assert result.exit_code == 0, result.stdout
    state = StateStore(tmp_path / "PROJECT_STATE.yaml").load()
    assert state.last_completed_task == "P01-T01"
    assert state.next_task == "P01-T02"
    assert state.state_revision == 2

    history = yaml.safe_load(
        (tmp_path / "state" / "task-history.yaml").read_text(encoding="utf-8")
    )
    entry = history["entries"][-1]
    assert entry["task_id"] == "P01-T01"
    assert entry["status"] == "PASS"
    assert "81 passed" in entry["evidence"][0]


def test_advance_reports_a_stale_revision_instead_of_overwriting(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(build_root(tmp_path)))

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
            "--expected-revision",
            "7",
        ],
    )

    assert result.exit_code != 0
    assert "revision" in (result.stdout + str(result.output)).lower()


def test_advance_refuses_an_unknown_task(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(build_root(tmp_path)))

    result = runner.invoke(
        app,
        [
            "advance",
            "--task",
            "P99-T99",
            "--status",
            "PASS",
            "--evidence",
            "nothing",
        ],
    )

    assert result.exit_code != 0
    assert "P99-T99" in (result.stdout + str(result.output))


def test_phase_gate_command_records_the_gate(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(build_root(tmp_path)))

    result = runner.invoke(
        app,
        [
            "phase-gate",
            "--gate",
            "GO_WITH_LIMITATIONS",
            "--reason",
            "Revit licence unchecked; phases 03/04 proceed",
        ],
    )

    assert result.exit_code == 0, result.stdout
    state = StateStore(tmp_path / "PROJECT_STATE.yaml").load()
    assert str(state.phase_gate) == "GO_WITH_LIMITATIONS"


def test_task_graph_without_a_registry_fails_closed(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))
    StateStore(tmp_path / "PROJECT_STATE.yaml").save(ProjectState())

    result = runner.invoke(app, ["task-graph"])

    assert result.exit_code != 0
    assert "task-graph" in (result.stdout + str(result.output)).lower()


def test_advance_phase_refuses_while_tasks_are_still_open(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(build_root(tmp_path)))

    result = runner.invoke(
        app,
        [
            "advance-phase",
            "--gate",
            "GO",
            "--next-phase",
            "PHASE_03",
            "--next-phase-name",
            "project-intelligence",
            "--next-task",
            "P03-T01",
            "--reason",
            "foundation verified",
        ],
    )

    assert result.exit_code != 0
    assert "P01-T01" in (result.stdout + str(result.output))
    state = StateStore(tmp_path / "PROJECT_STATE.yaml").load()
    assert state.phase_id == "PHASE_01", "a refused close must not move the phase"


def test_advance_phase_closes_a_finished_phase(tmp_path: Path, monkeypatch):
    monkeypatch.setenv(
        "AMANDA_PROJECT_ROOT",
        str(
            build_root(
                tmp_path,
                tasks=[
                    TaskRecord(id="P01-T01", phase="PHASE_01", plan_path="p1.md"),
                    TaskRecord(
                        id="P01-T02",
                        phase="PHASE_01",
                        plan_path="p1.md",
                        depends_on=["P01-T01"],
                    ),
                    TaskRecord(id="P03-T01", phase="PHASE_03", plan_path="p3.md"),
                ],
            )
        ),
    )
    for task_id in ("P01-T01", "P01-T02"):
        done = runner.invoke(
            app,
            [
                "advance",
                "--task",
                task_id,
                "--status",
                "PASS",
                "--evidence",
                "pytest -q -> green",
            ],
        )
        assert done.exit_code == 0, done.stdout

    result = runner.invoke(
        app,
        [
            "advance-phase",
            "--gate",
            "GO_WITH_LIMITATIONS",
            "--next-phase",
            "PHASE_03",
            "--next-phase-name",
            "project-intelligence",
            "--next-task",
            "P03-T01",
            "--reason",
            "Revit licence unchecked; source intelligence proceeds",
        ],
    )

    assert result.exit_code == 0, result.stdout
    state = StateStore(tmp_path / "PROJECT_STATE.yaml").load()
    assert state.phase_id == "PHASE_03"
    assert state.phase_name == "project-intelligence"
    assert state.next_task == "P03-T01"
    assert str(state.phase_gate) == "GO_WITH_LIMITATIONS"
    assert str(state.phase_status) == "PENDING"


def test_advance_phase_refuses_an_unknown_next_task(tmp_path: Path, monkeypatch):
    root = build_root(tmp_path)
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(root))
    for task_id in ("P01-T01", "P01-T02"):
        runner.invoke(
            app,
            ["advance", "--task", task_id, "--status", "PASS", "--evidence", "ok"],
        )

    result = runner.invoke(
        app,
        [
            "advance-phase",
            "--gate",
            "GO",
            "--next-phase",
            "PHASE_03",
            "--next-phase-name",
            "project-intelligence",
            "--next-task",
            "P03-T99",
            "--reason",
            "foundation verified",
        ],
    )

    assert result.exit_code != 0
    assert "P03-T99" in (result.stdout + str(result.output))
