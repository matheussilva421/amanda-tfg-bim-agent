from pathlib import Path

import pytest

from amanda_agent.models.state import ProjectState, TaskStatus
from amanda_agent.paths import ProjectPaths
from amanda_agent.session.end import SessionEndRefused, end_session
from amanda_agent.state.store import StateStore
from amanda_agent.state.tasks import TaskRecord, TaskRegistry


def _seed_end_project(
    tmp_path: Path, *, task_status: TaskStatus = TaskStatus.PENDING
) -> Path:
    paths = ProjectPaths.from_root(tmp_path)
    paths.state.mkdir(parents=True)
    StateStore(paths.project_state).save(
        ProjectState(
            phase_id="PHASE_03",
            phase_name="project-intelligence",
            phase_status=TaskStatus.PENDING,
            next_task="P03-T01",
        )
    )
    registry = TaskRegistry()
    registry.add(
        TaskRecord(
            id="P03-T01",
            phase="PHASE_03",
            plan_path="docs/superpowers/plans/03-project-intelligence.md",
            status=task_status,
        )
    )
    registry.save(paths.state / "task-graph.yaml")
    (paths.state / "blockers.yaml").write_text(
        "schema_version: 1\nblockers: []\n", encoding="utf-8"
    )
    return paths.root


def _end(root: Path, **overrides):
    payload = {
        "scope": "session-end",
        "changes": ["implemented session protocols"],
        "evidence": ["focused checks exercised"],
        "test_evidence": [
            {"command": "pytest tests/unit/test_session_end.py -q", "result": "7 passed"}
        ],
        "github_status": "not committed or pushed by instruction",
        "blockers": [],
        "resume_instructions": ["run the focused suite, then inspect the next READY task"],
        "next_task_id": "P03-T01",
        "project_state_update": {"phase_status": TaskStatus.PENDING},
    }
    payload.update(overrides)
    return end_session(root, **payload)


def test_ending_running_task_is_refused(tmp_path: Path):
    root = _seed_end_project(tmp_path, task_status=TaskStatus.RUNNING)

    with pytest.raises(SessionEndRefused, match="RUNNING"):
        _end(root, project_state_update={"phase_status": TaskStatus.RUNNING})


def test_suspending_running_task_is_allowed_and_recorded(tmp_path: Path):
    root = _seed_end_project(tmp_path, task_status=TaskStatus.RUNNING)

    result = _end(
        root,
        project_state_update={"phase_status": TaskStatus.SUSPENDED},
        resume_instructions=["resume P03-T01 after the external dependency is available"],
    )

    assert result["status"] == "SUSPENDED"
    assert StateStore(root / "PROJECT_STATE.yaml").load().phase_status == TaskStatus.SUSPENDED
    assert "SUSPENDED" in Path(result["handoff_path"]).read_text(encoding="utf-8")


def test_ending_without_test_evidence_is_refused(tmp_path: Path):
    root = _seed_end_project(tmp_path)

    with pytest.raises(SessionEndRefused, match="test"):
        _end(root, test_evidence=[])


def test_ending_without_next_task_is_refused(tmp_path: Path):
    root = _seed_end_project(tmp_path)

    with pytest.raises(SessionEndRefused, match="next task"):
        _end(root, next_task_id="")


def test_handoff_contains_all_required_sections(tmp_path: Path):
    root = _seed_end_project(tmp_path)

    result = _end(root)
    handoff = Path(result["handoff_path"])
    text = handoff.read_text(encoding="utf-8")

    assert handoff.parent == root / "docs" / "notes"
    assert handoff.name.endswith("-session-end-handoff.md")
    for section in (
        "## Changes",
        "## Evidence",
        "## Tests",
        "## GitHub status",
        "## Blockers",
        "## Resume instructions",
    ):
        assert section in text


def test_bim_mutation_without_checkpoint_is_refused(tmp_path: Path):
    root = _seed_end_project(tmp_path)

    with pytest.raises(SessionEndRefused, match="checkpoint"):
        _end(root, bim_mutated=True, checkpoint_reference=None)


def test_existing_handoff_is_preserved_when_new_entry_is_appended(tmp_path: Path):
    root = _seed_end_project(tmp_path)
    target = root / "docs" / "notes" / "2026-09-15-session-end-handoff.md"
    target.parent.mkdir(parents=True)
    target.write_text("previous durable entry\n", encoding="utf-8")

    _end(root, date="2026-09-15")

    text = target.read_text(encoding="utf-8")
    assert text.startswith("previous durable entry\n")
    assert "## Changes" in text
