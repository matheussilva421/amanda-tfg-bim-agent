"""Advancing project state must be reconcilable, guarded and testable.

The open finding from Phase 01 was that no command could record a finished
task, so the durable state kept claiming ``PENDING`` / ``P01-T01`` while the
work was already implemented, committed and tested. This suite pins the
contract that closes it.
"""

from pathlib import Path

import pytest
import yaml

from amanda_agent.models.state import TaskStatus
from amanda_agent.state.advance import (
    AdvanceRefused,
    complete_phase,
    complete_task,
    set_phase_gate,
)
from amanda_agent.state.store import StateStore
from amanda_agent.state.tasks import load_registry


def _seed_project(tmp_path: Path, *, gate_dependency: bool = True) -> Path:
    """A miniature project: two tasks in one phase plus a durable state."""
    store = StateStore(tmp_path / "PROJECT_STATE.yaml")
    store.save(store.load())

    registry = load_registry(_write_registry(tmp_path, gate_dependency))
    registry.save(tmp_path / "state" / "task-graph.yaml")
    return tmp_path


def _write_registry(tmp_path: Path, gate_dependency: bool) -> Path:
    from amanda_agent.state.tasks import TaskRecord, TaskRegistry

    registry = TaskRegistry()
    registry.add(
        TaskRecord(
            id="P01-T01", phase="PHASE_01", plan_path="plan.md", title="one"
        )
    )
    registry.add(
        TaskRecord(
            id="P01-T02",
            phase="PHASE_01",
            plan_path="plan.md",
            title="two",
            depends_on=["P01-T01"] if gate_dependency else [],
        )
    )
    path = tmp_path / "seed-registry.yaml"
    registry.save(path)
    return path


def test_completing_a_task_updates_state_and_registry_together(tmp_path: Path):
    root = _seed_project(tmp_path)

    result = complete_task(
        root,
        task_id="P01-T01",
        status=TaskStatus.PASS,
        evidence=["pytest tests/unit -q -> 64 passed"],
        next_task="P01-T02",
    )

    state = StateStore(root / "PROJECT_STATE.yaml").load()
    registry = load_registry(root / "state" / "task-graph.yaml")
    assert state.last_completed_task == "P01-T01"
    assert state.next_task == "P01-T02"
    assert state.state_revision == 2
    assert registry.tasks["P01-T01"].status == TaskStatus.PASS
    assert registry.tasks["P01-T01"].evidence == [
        "pytest tests/unit -q -> 64 passed"
    ]
    assert result["state_revision"] == 2


def test_a_task_cannot_be_completed_without_evidence(tmp_path: Path):
    root = _seed_project(tmp_path)

    with pytest.raises(AdvanceRefused, match="evidence"):
        complete_task(
            root, task_id="P01-T01", status=TaskStatus.PASS, evidence=[]
        )


def test_only_pass_like_statuses_record_completion(tmp_path: Path):
    root = _seed_project(tmp_path)

    with pytest.raises(AdvanceRefused, match="status"):
        complete_task(
            root,
            task_id="P01-T01",
            status=TaskStatus.RUNNING,
            evidence=["half done"],
        )


def test_completion_is_refused_for_an_unknown_task(tmp_path: Path):
    root = _seed_project(tmp_path)

    with pytest.raises(AdvanceRefused, match="unknown"):
        complete_task(
            root,
            task_id="P01-T99",
            status=TaskStatus.PASS,
            evidence=["x"],
        )


def test_completing_a_task_whose_dependency_is_unfinished_is_refused(
    tmp_path: Path,
):
    """The registry is a graph, so finishing out of order is a false claim.

    P01-T02 declares a hard dependency on P01-T01. Recording T02 as PASS while
    T01 is still PENDING would make the scheduler and the durable state agree on
    a progress level that never happened.
    """
    root = _seed_project(tmp_path)

    with pytest.raises(AdvanceRefused, match="P01-T01"):
        complete_task(
            root,
            task_id="P01-T02",
            status=TaskStatus.PASS,
            evidence=["looks fine to me"],
        )


def test_the_unready_refusal_changes_neither_registry_nor_state(tmp_path: Path):
    root = _seed_project(tmp_path)
    state_path = root / "PROJECT_STATE.yaml"
    before_state = state_path.read_text(encoding="utf-8")
    graph_path = root / "state" / "task-graph.yaml"
    before_graph = graph_path.read_text(encoding="utf-8")

    with pytest.raises(AdvanceRefused):
        complete_task(
            root,
            task_id="P01-T02",
            status=TaskStatus.PASS,
            evidence=["x"],
        )

    assert state_path.read_text(encoding="utf-8") == before_state
    assert graph_path.read_text(encoding="utf-8") == before_graph


def test_an_explicit_override_records_the_completion_and_its_reason(
    tmp_path: Path,
):
    """An operator may still close a task whose dependency is stuck.

    The override has to be deliberate: it is a parameter, not an accident, and
    it is echoed in the returned record so the history keeps the reason.
    """
    root = _seed_project(tmp_path)

    result = complete_task(
        root,
        task_id="P01-T02",
        status=TaskStatus.PASS,
        evidence=["capability proven without the fixture P01-T01 creates"],
        allow_unready="P01-T01 blocked by operator action, T02 does not consume it",
    )

    registry = load_registry(root / "state" / "task-graph.yaml")
    assert registry.tasks["P01-T02"].status == TaskStatus.PASS
    assert result["unready_dependencies"] == ["P01-T01"]
    assert result["override_reason"] in result["evidence"][-1]


def test_a_dependency_that_passed_with_warnings_still_unlocks_the_task(
    tmp_path: Path,
):
    root = _seed_project(tmp_path)
    complete_task(
        root,
        task_id="P01-T01",
        status=TaskStatus.PASS_WITH_WARNINGS,
        evidence=["a"],
    )

    outcome = complete_task(
        root,
        task_id="P01-T02",
        status=TaskStatus.PASS,
        evidence=["b"],
    )

    assert outcome["unready_dependencies"] == []


def test_a_stale_state_revision_is_rejected_rather_than_lost(tmp_path: Path):
    root = _seed_project(tmp_path)

    with pytest.raises(AdvanceRefused, match="revision"):
        complete_task(
            root,
            task_id="P01-T01",
            status=TaskStatus.PASS,
            evidence=["x"],
            expected_revision=7,
        )


def test_completing_a_phase_sets_the_gate_and_names_the_next_phase(tmp_path: Path):
    root = _seed_project(tmp_path)
    complete_task(root, task_id="P01-T01", status=TaskStatus.PASS, evidence=["a"])

    outcome = complete_phase(
        root,
        gate="GO_WITH_LIMITATIONS",
        next_phase_id="PHASE_03",
        next_phase_name="project-intelligence",
        next_task="P03-T01",
        reason="source work does not depend on the Revit provider",
    )

    state = StateStore(root / "PROJECT_STATE.yaml").load()
    assert state.phase_id == "PHASE_03"
    assert state.phase_name == "project-intelligence"
    assert state.phase_status == TaskStatus.PENDING
    assert state.phase_gate == "GO_WITH_LIMITATIONS"
    assert state.next_task == "P03-T01"
    assert outcome["phase_gate"] == "GO_WITH_LIMITATIONS"


def test_phase_gate_records_a_verification_commit(tmp_path: Path):
    root = _seed_project(tmp_path)

    set_phase_gate(
        root,
        gate="GO_WITH_LIMITATIONS",
        reason="scoped limitation",
        verified_commit="abc1234",
    )

    state = StateStore(root / "PROJECT_STATE.yaml").load()
    assert state.phase_gate == "GO_WITH_LIMITATIONS"
    assert state.last_verified_commit == "abc1234"


def test_completion_never_rewrites_the_canonical_plans(tmp_path: Path):
    root = _seed_project(tmp_path)
    plan = root / "plan.md"
    plan.write_text("canonical plan", encoding="utf-8")

    complete_task(root, task_id="P01-T01", status=TaskStatus.PASS, evidence=["a"])

    assert plan.read_text(encoding="utf-8") == "canonical plan"


def test_history_is_appended_so_a_later_reader_can_reconcile(tmp_path: Path):
    root = _seed_project(tmp_path)

    complete_task(root, task_id="P01-T01", status=TaskStatus.PASS, evidence=["a"])
    complete_task(
        root,
        task_id="P01-T02",
        status=TaskStatus.PASS_WITH_WARNINGS,
        evidence=["b"],
    )

    history = yaml.safe_load(
        (root / "state" / "task-history.yaml").read_text(encoding="utf-8")
    )
    assert [entry["task_id"] for entry in history["entries"]] == [
        "P01-T01",
        "P01-T02",
    ]
    assert history["entries"][1]["status"] == "PASS_WITH_WARNINGS"
