"""The task dependency graph gates readiness, not aspiration.

A task becomes READY only when every hard dependency reached PASS or
PASS_WITH_WARNINGS. A branch that lost its input must not drag unrelated
branches down with it, and two independent ready tasks stay explicitly
parallel-ready.
"""

from pathlib import Path

import pytest
import yaml

from amanda_agent.models.state import TaskStatus
from amanda_agent.state import build_task_graph
from amanda_agent.state.build_task_graph import (
    build_registry as build_registry_from_plans,
)
from amanda_agent.state.build_task_graph import (
    regenerate,
)
from amanda_agent.state.plan_order import diagnose_plan_order
from amanda_agent.state.tasks import TaskRecord, TaskRegistry, load_registry


def build_registry() -> TaskRegistry:
    registry = TaskRegistry()
    registry.add(
        TaskRecord(
            id="P03-T01",
            phase="PHASE_03",
            plan_path="docs/plan/CURRENT.md",
            title="Source manifest",
        )
    )
    registry.add(
        TaskRecord(
            id="P03-T02",
            phase="PHASE_03",
            plan_path="docs/plan/CURRENT.md",
            title="Provenance model",
            depends_on=["P03-T01"],
        )
    )
    registry.add(
        TaskRecord(
            id="P07-T01",
            phase="PHASE_07A",
            plan_path="docs/plan/CURRENT.md",
            title="Production AGENTS policy",
        )
    )
    return registry


def test_a_task_is_not_ready_while_a_hard_dependency_is_unfinished():
    registry = build_registry()

    assert "P03-T02" not in registry.ready_tasks()


def test_dependency_pass_unlocks_the_downstream_task():
    registry = build_registry()
    registry.set_status("P03-T01", TaskStatus.PASS)

    assert "P03-T02" in registry.ready_tasks()


def test_pass_with_warnings_still_unlocks_downstream():
    registry = build_registry()
    registry.set_status("P03-T01", TaskStatus.PASS_WITH_WARNINGS)

    assert "P03-T02" in registry.ready_tasks()


def test_blocked_by_input_propagates_only_to_the_dependent_branch():
    registry = build_registry()
    registry.set_status("P03-T01", TaskStatus.BLOCKED_BY_INPUT)

    registry.propagate()

    assert registry.tasks["P03-T02"].status == TaskStatus.BLOCKED_BY_INPUT
    assert registry.tasks["P07-T01"].status == TaskStatus.PENDING
    assert "P07-T01" in registry.ready_tasks()


def test_independent_ready_tasks_are_reported_as_parallel():
    registry = build_registry()

    parallel = registry.parallel_ready_tasks()

    assert "P03-T01" in parallel
    assert "P07-T01" in parallel
    assert registry.parallel_batches()[0] == sorted(parallel)


def test_unknown_dependency_and_cycle_are_rejected():
    registry = build_registry()
    registry.add(
        TaskRecord(
            id="P03-T03",
            phase="PHASE_03",
            plan_path="docs/plan/CURRENT.md",
            title="Ingest command",
            depends_on=["P03-NOPE"],
        )
    )

    with pytest.raises(ValueError):
        registry.validate()


def test_registry_round_trips_through_yaml(tmp_path: Path):
    registry = build_registry()
    registry.set_status("P07-T01", TaskStatus.PASS)
    target = tmp_path / "state" / "task-graph.yaml"

    registry.save(target)
    reloaded = load_registry(target)

    assert reloaded.tasks["P07-T01"].status == TaskStatus.PASS
    assert reloaded.tasks["P03-T02"].depends_on == ["P03-T01"]
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert raw["schema_version"] == 1


def test_missing_registry_file_is_not_silently_invented(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_registry(tmp_path / "absent.yaml")


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_phase_level_plan_edges_exist_as_task_dependencies(tmp_path: Path):
    """The master plan states its graph at phase level, not task level.

    ``01 -> 07A -> 02`` and ``01 -> 03 -> 04`` therefore cannot come from the
    within-phase sequential default: nothing in the plan text makes P03-T01
    or P07-T01 follow the last Phase 01 task. If the derivation forgets them,
    the graph silently allows Phase 03 and Phase 07A to start before the
    foundation they consume finished.
    """
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "structured-plan.md").write_text(
        "### Task 13: Foundation complete [P01-T13]\n\n"
        "### Task 1: Project intelligence [P03-T01]\n\n"
        "### Task 1: Autonomy [P07-T01]\n",
        encoding="utf-8",
    )
    registry = build_registry_from_plans(plans, relative_to=tmp_path)

    assert "P01-T13" in registry.tasks["P03-T01"].depends_on
    assert "P01-T13" in registry.tasks["P07-T01"].depends_on


def test_committed_task_graph_satisfies_the_reviewed_phase_contract():
    """The graph on disk must match the phase order the plan review approved.

    A green derivation is not enough: the committed registry is what the
    scheduler actually reads.
    """
    report = diagnose_plan_order(REPO_ROOT / "state" / "task-graph.yaml")

    assert report.passed is True, report.as_dict()["issues"]


def test_regenerating_the_graph_keeps_recorded_outcomes(tmp_path: Path):
    """A plan edit must refresh dependencies without erasing history.

    The derivation is the only writer of ``state/task-graph.yaml`` that reads
    the plans directly, so it is also the one place able to silently reset a
    finished phase to PENDING and drop the evidence behind it.
    """
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "plan.md").write_text(
        "### Task 1: First [P01-T01]\n\n### Task 2: Second [P01-T02]\n",
        encoding="utf-8",
    )
    target = tmp_path / "state" / "task-graph.yaml"
    first = regenerate(plans, target)
    first.set_status("P01-T01", TaskStatus.PASS)
    first.add_evidence("P01-T01", "pytest -q -> 9 passed")
    first.save(target)

    second = regenerate(plans, target)

    assert second.tasks["P01-T01"].status == TaskStatus.PASS
    assert second.tasks["P01-T01"].evidence == ["pytest -q -> 9 passed"]
    assert second.tasks["P01-T02"].depends_on == ["P01-T01"]
    assert second.tasks["P01-T02"].status == TaskStatus.PENDING


def test_regenerating_from_scratch_needs_no_existing_file(tmp_path: Path):
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "plan.md").write_text("### Task 1: First [P01-T01]\n", encoding="utf-8")
    target = tmp_path / "state" / "task-graph.yaml"

    registry = regenerate(plans, target)

    assert registry.tasks["P01-T01"].status == TaskStatus.PENDING
    assert load_registry(target).tasks["P01-T01"].title == "First"


def test_main_refuses_to_overwrite_durable_graph_from_narrative_plan(
    tmp_path: Path, monkeypatch, capsys
):
    script = tmp_path / "repo" / "src" / "amanda_agent" / "state" / "build_task_graph.py"
    script.parent.mkdir(parents=True)
    target = tmp_path / "repo" / "state" / "task-graph.yaml"
    target.parent.mkdir(parents=True)
    durable_state = (
        "schema_version: 1\n"
        "tasks:\n"
        "  P01-T01:\n"
        "    id: P01-T01\n"
        "    phase: PHASE_01\n"
        "    plan_path: docs/plan/CURRENT.md\n"
        "    title: Preserve task outcome\n"
        "    depends_on: []\n"
        "    status: PASS\n"
        "    evidence:\n"
        "    - retained evidence\n"
    )
    target.write_text(durable_state, encoding="utf-8")
    current_plan = tmp_path / "repo" / "docs" / "plan" / "CURRENT.md"
    current_plan.parent.mkdir(parents=True)
    current_plan.write_text("Narrative project plan\n", encoding="utf-8")
    monkeypatch.setattr(build_task_graph, "__file__", str(script))

    exit_code = build_task_graph.main()

    assert exit_code != 0
    assert target.read_text(encoding="utf-8") == durable_state
    assert "refus" in capsys.readouterr().out.lower()
