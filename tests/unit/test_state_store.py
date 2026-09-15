import os
from pathlib import Path

import pytest

from amanda_agent.models.state import ProjectState
from amanda_agent.state.store import StateRevisionConflict, StateStore


def test_roundtrip_persists_revision(tmp_path: Path):
    store = StateStore(tmp_path / "PROJECT_STATE.yaml")
    state = ProjectState(next_task="P01-T04")

    store.save(state)
    loaded = store.load()

    assert loaded.next_task == "P01-T04"
    assert loaded.state_revision == 1


def test_load_missing_file_returns_default_without_writing(tmp_path: Path):
    target = tmp_path / "PROJECT_STATE.yaml"
    store = StateStore(target)

    loaded = store.load()

    assert loaded.next_task == "P01-T01"
    assert not target.exists()


def test_invalid_state_is_preserved_and_never_silently_reset(tmp_path: Path):
    target = tmp_path / "PROJECT_STATE.yaml"
    target.write_text("phase_status: SOMETHING_BOGUS\n", encoding="utf-8")
    store = StateStore(target)

    with pytest.raises(Exception):
        store.load()

    assert "SOMETHING_BOGUS" in target.read_text(encoding="utf-8")


def test_failed_save_keeps_previous_valid_state(tmp_path: Path, monkeypatch):
    target = tmp_path / "PROJECT_STATE.yaml"
    store = StateStore(target)
    store.save(ProjectState(next_task="P01-T04"))
    before = target.read_bytes()

    def exploding_replace(src, dst):
        raise OSError("simulated interruption")

    monkeypatch.setattr(os, "replace", exploding_replace)
    with pytest.raises(OSError):
        store.save(ProjectState(next_task="P01-T05"))

    monkeypatch.undo()
    assert target.read_bytes() == before
    assert StateStore(target).load().next_task == "P01-T04"


def test_stale_revision_is_rejected(tmp_path: Path):
    target = tmp_path / "PROJECT_STATE.yaml"
    store = StateStore(target)
    first = store.save(ProjectState(next_task="A"))

    with pytest.raises(StateRevisionConflict):
        store.save(ProjectState(next_task="B"), expected_revision=0)

    assert store.load().next_task == first.next_task


def test_concurrent_writers_cannot_lose_updates(tmp_path: Path):
    target = tmp_path / "PROJECT_STATE.yaml"
    store = StateStore(target)
    base = store.save(ProjectState(next_task="A"))

    winner = store.save(
        base.model_copy(update={"next_task": "WINNER"}),
        expected_revision=base.state_revision,
    )
    with pytest.raises(StateRevisionConflict):
        store.save(
            base.model_copy(update={"next_task": "LOSER"}),
            expected_revision=base.state_revision,
        )

    assert store.load().next_task == "WINNER"
    assert winner.state_revision == 2


def test_no_temporary_files_left_behind(tmp_path: Path):
    target = tmp_path / "PROJECT_STATE.yaml"
    store = StateStore(target)
    store.save(ProjectState())
    store.save(ProjectState(next_task="B"))

    leftovers = [p.name for p in tmp_path.iterdir() if p.name != target.name]
    assert leftovers == []
