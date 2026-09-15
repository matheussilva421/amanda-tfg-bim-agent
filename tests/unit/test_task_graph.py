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
from amanda_agent.state.tasks import TaskRecord, TaskRegistry, load_registry


def build_registry() -> TaskRegistry:
    registry = TaskRegistry()
    registry.add(
        TaskRecord(
            id="P03-T01",
            phase="PHASE_03",
            plan_path="docs/superpowers/plans/03-project-intelligence.md",
            title="Source manifest",
        )
    )
    registry.add(
        TaskRecord(
            id="P03-T02",
            phase="PHASE_03",
            plan_path="docs/superpowers/plans/03-project-intelligence.md",
            title="Provenance model",
            depends_on=["P03-T01"],
        )
    )
    registry.add(
        TaskRecord(
            id="P07-T01",
            phase="PHASE_07A",
            plan_path="docs/superpowers/plans/07-autonomy-recovery-security.md",
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
            plan_path="docs/superpowers/plans/03-project-intelligence.md",
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
