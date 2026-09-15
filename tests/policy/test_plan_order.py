"""Behavioral contract for the cross-phase plan dependency verifier."""

from amanda_agent.models.state import TaskStatus
from amanda_agent.state.plan_order import diagnose_plan_order
from amanda_agent.state.tasks import TaskRecord, TaskRegistry


def _registry(*, solver_dependency: bool = True, revit_status: TaskStatus | None = None):
    dependencies = {
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


def test_missing_cross_phase_dependency_is_reported():
    report = diagnose_plan_order(_registry(solver_dependency=False))

    missing = [issue for issue in report.issues if issue.code == "MISSING_PHASE_DEPENDENCY"]

    assert report.passed is False
    assert any(
        issue.predecessor_phase == "PHASE_03"
        and issue.successor_phase == "PHASE_04"
        for issue in missing
    )


def test_revit_block_does_not_block_source_and_synthetic_solver_branch():
    report = diagnose_plan_order(
        _registry(revit_status=TaskStatus.BLOCKED_BY_TOOL)
    )

    assert report.branches["revit"].status == "BLOCKED"
    assert report.branches["solver"].status == "PENDING"
    assert report.branches["solver"].blocking_phases == ()
