"""Behavioral contract for the cross-phase plan dependency verifier."""

import pytest

from amanda_agent.models.state import TaskStatus
from amanda_agent.state.plan_order import diagnose_plan_order
from amanda_agent.state.tasks import TaskRecord, TaskRegistry


def _registry(*, solver_dependency: bool = True, revit_status: TaskStatus | None = None):
    dependencies = {
        "P2-T01": ["P1-T01"],
        "P3-T01": ["P2-T01"],
        "P4-T01": ["P3-T01"],
        "P07-T01": ["P01-T01"],
        "P02-T01": ["P07-T01"],
        "P03-T01": ["P01-T01"],
        "P04-T01": ["P03-T01"] if solver_dependency else [],
        "P05-T01": ["P02-T01", "P04-T01"],
        "P06-T01": ["P05-T01"],
        "P07-T07": ["P06-T01"],
        "P08-T01": ["P07-T07"],
    }
    phases = {
        "P1-T01": "P1",
        "P2-T01": "P2",
        "P3-T01": "P3",
        "P4-T01": "P4",
        "P01-T01": "PHASE_01",
        "P07-T01": "PHASE_07A",
        "P02-T01": "PHASE_02",
        "P03-T01": "PHASE_03",
        "P04-T01": "PHASE_04",
        "P05-T01": "PHASE_05",
        "P06-T01": "PHASE_06",
        "P07-T07": "PHASE_07B",
        "P08-T01": "PHASE_08",
    }
    registry = TaskRegistry()
    for task_id, phase in phases.items():
        registry.add(
            TaskRecord(
                id=task_id,
                phase=phase,
                plan_path=f"plans/{phase}.md",
                title=task_id,
                depends_on=dependencies.get(task_id, []),
                status=(
                    revit_status
                    if task_id == "P02-T01" and revit_status is not None
                    else TaskStatus.PENDING
                ),
            )
        )
    return registry


def test_well_formed_phase_contract_passes_without_mutating_registry():
    registry = _registry()
    before = registry.model_dump(mode="json")

    report = diagnose_plan_order(registry)

    assert report.passed is True
    assert report.issues == ()
    assert report.phase_edges == (
        ("P1", "P2"),
        ("P2", "P3"),
        ("P3", "P4"),
        ("PHASE_01", "PHASE_03"),
        ("PHASE_01", "PHASE_07A"),
        ("PHASE_02", "PHASE_05"),
        ("PHASE_03", "PHASE_04"),
        ("PHASE_04", "PHASE_05"),
        ("PHASE_05", "PHASE_06"),
        ("PHASE_06", "PHASE_07B"),
        ("PHASE_07A", "PHASE_02"),
        ("PHASE_07B", "PHASE_08"),
    )
    assert registry.model_dump(mode="json") == before


@pytest.mark.parametrize(
    ("task_id", "predecessor", "successor"),
    [
        ("P2-T01", "P1", "P2"),
        ("P3-T01", "P2", "P3"),
        ("P4-T01", "P3", "P4"),
    ],
)
def test_missing_current_canonical_phase_dependency_is_reported(
    task_id: str, predecessor: str, successor: str
):
    registry = _registry()
    registry.tasks[task_id].depends_on = []

    report = diagnose_plan_order(registry)

    assert report.passed is False
    assert any(
        issue.code == "MISSING_PHASE_DEPENDENCY"
        and issue.predecessor_phase == predecessor
        and issue.successor_phase == successor
        for issue in report.issues
    )


def test_missing_cross_phase_dependency_is_reported():
    report = diagnose_plan_order(_registry(solver_dependency=False))

    missing = [issue for issue in report.issues if issue.code == "MISSING_PHASE_DEPENDENCY"]

    assert report.passed is False
    assert any(
        issue.predecessor_phase == "PHASE_03"
        and issue.successor_phase == "PHASE_04"
        for issue in missing
    )


def test_run003_revit_gate_to_geometry_to_acceptance_chain_is_allowed():
    registry = _registry()
    registry.add(
        TaskRecord(
            id="P5-T01",
            phase="P5",
            plan_path="docs/plan/CURRENT.md",
            title="RUN-003 R04 Revit geometry",
            depends_on=["P4-T01"],
        )
    )
    registry.add(
        TaskRecord(
            id="P6-T01",
            phase="P6",
            plan_path="docs/plan/CURRENT.md",
            title="RUN-003 canonical acceptance",
            depends_on=["P5-T01"],
        )
    )

    report = diagnose_plan_order(registry)

    assert report.passed is True, report.as_dict()["issues"]
    assert ("P4", "P5") in report.phase_edges
    assert ("P5", "P6") in report.phase_edges


def test_revit_block_does_not_block_source_and_synthetic_solver_branch():
    report = diagnose_plan_order(
        _registry(revit_status=TaskStatus.BLOCKED_BY_TOOL)
    )

    assert report.branches["revit"].status == "BLOCKED"
    assert report.branches["solver"].status == "PENDING"
    assert report.branches["solver"].blocking_phases == ()
