from pathlib import Path

import pytest

from amanda_agent.models.state import ProjectState, TaskStatus
from amanda_agent.paths import ProjectPaths
from amanda_agent.session.start import start_session
from amanda_agent.state.store import StateStore
from amanda_agent.state.tasks import TaskRecord, TaskRegistry


def _seed_start_project(
    tmp_path: Path,
    *,
    phase_id: str = "PHASE_03",
    phase_name: str = "project-intelligence",
    next_task: str = "P03-T02",
) -> Path:
    paths = ProjectPaths.from_root(tmp_path)
    (paths.root / "AGENTS.md").write_text("session contract", encoding="utf-8")
    plan = paths.root / "docs" / "plan" / "CURRENT.md"
    plan.parent.mkdir(parents=True)
    plan.write_text("child plan", encoding="utf-8")
    paths.state.mkdir(parents=True)
    StateStore(paths.project_state).save(
        ProjectState(
            phase_id=phase_id,
            phase_name=phase_name,
            phase_status=TaskStatus.PENDING,
            next_task=next_task,
        )
    )
    registry = TaskRegistry()
    registry.add(
        TaskRecord(
            id="P03-T01",
            phase=phase_id,
            plan_path="docs/plan/CURRENT.md",
            status=TaskStatus.PENDING,
        )
    )
    registry.add(
        TaskRecord(
            id="P03-T02",
            phase=phase_id,
            plan_path="docs/plan/CURRENT.md",
            depends_on=["P03-T01"],
            status=TaskStatus.PENDING,
        )
    )
    registry.save(paths.state / "task-graph.yaml")
    (paths.state / "bim-environment.lock.yaml").write_text(
        "schema_version: 1\nrevit:\n  selected_build: fixture\n",
        encoding="utf-8",
    )
    (paths.state / "blockers.yaml").write_text(
        "schema_version: 1\nblockers: []\n", encoding="utf-8"
    )
    return paths.root


def _clean_git(_argv: list[str], _cwd: Path) -> tuple[int, str, str]:
    return 0, "", ""


def test_dirty_worktree_is_a_problem_before_execution(tmp_path: Path):
    root = _seed_start_project(tmp_path)

    report = start_session(
        root,
        git_runner=lambda argv, cwd: (0, " M user-work.py\n", ""),
    )

    assert report["can_execute"] is False
    assert any("dirty" in problem.lower() for problem in report["problems"])
    names = [entry["name"] for entry in report["checks"]]
    assert names.index("git_status") < names.index("resolve_next_ready_task")
    git_entry = next(entry for entry in report["checks"] if entry["name"] == "git_status")
    assert git_entry["status"] == "PROBLEM"


def test_non_bim_phase_does_not_require_revit(tmp_path: Path):
    root = _seed_start_project(tmp_path)

    report = start_session(
        root,
        git_runner=_clean_git,
        revit_probe=lambda: pytest.fail("Revit must not be probed for PHASE_03"),
        provider_health_probe=lambda: pytest.fail("provider must not be probed"),
    )

    assert report["can_execute"] is True
    revit_entry = next(
        entry for entry in report["checks"] if entry["name"] == "revit_provider_health"
    )
    assert revit_entry["status"] == "SKIPPED"


def test_missing_agents_is_reported_without_raising(tmp_path: Path):
    root = _seed_start_project(tmp_path)
    (root / "AGENTS.md").unlink()

    report = start_session(root, git_runner=_clean_git)

    entry = next(entry for entry in report["checks"] if entry["name"] == "read_agents")
    assert entry["status"] == "PROBLEM"
    assert any("AGENTS.md" in problem for problem in report["problems"])


def test_missing_task_registry_is_reported_without_raising(tmp_path: Path):
    root = _seed_start_project(tmp_path)
    (root / "state" / "task-graph.yaml").unlink()

    report = start_session(root, git_runner=_clean_git)

    entry = next(
        entry for entry in report["checks"] if entry["name"] == "resolve_next_ready_task"
    )
    assert entry["status"] == "PROBLEM"
    assert report["next_task"] is None


def test_corrupt_project_state_is_reported_without_raising(tmp_path: Path):
    root = _seed_start_project(tmp_path)
    (root / "PROJECT_STATE.yaml").write_text("phase_status: [", encoding="utf-8")

    report = start_session(root, git_runner=_clean_git)

    entry = next(
        entry for entry in report["checks"] if entry["name"] == "load_project_state"
    )
    assert entry["status"] == "PROBLEM"
    assert any("PROJECT_STATE.yaml" in problem for problem in report["problems"])


def test_next_task_is_resolved_from_registry_ready_set(tmp_path: Path):
    root = _seed_start_project(tmp_path, next_task="P03-T02")

    report = start_session(root, git_runner=_clean_git)

    assert report["ready_tasks"] == ["P03-T01"]
    assert report["next_task"] == "P03-T01"


def test_unregistered_recovery_task_loads_the_current_plan_fallback(tmp_path: Path):
    root = _seed_start_project(
        tmp_path,
        phase_id="REPOSITORY_RECOVERY",
        phase_name="repository-recovery",
        next_task="RECOVERY-VALIDATE",
    )

    report = start_session(root, git_runner=_clean_git)

    plan_check = next(
        entry for entry in report["checks"] if entry["name"] == "load_current_child_plan"
    )
    assert plan_check["status"] == "OK"
    assert plan_check["path"] == str(root / "docs" / "plan" / "CURRENT.md")
