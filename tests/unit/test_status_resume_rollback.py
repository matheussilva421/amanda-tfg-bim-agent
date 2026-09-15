"""status is read-only; resume respects blocker severity; rollback is guarded."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from amanda_agent.cli import app
from amanda_agent.commands.rollback import RollbackRefused, restore_checkpoint
from amanda_agent.models.state import ProjectState
from amanda_agent.models.tasks import Blocker, Severity
from amanda_agent.program import phase_graph
from amanda_agent.state.store import StateStore

runner = CliRunner()


def test_status_is_read_only(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))
    target = tmp_path / "PROJECT_STATE.yaml"
    StateStore(target).save(ProjectState())
    before = target.read_bytes()

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "PHASE_01" in result.stdout
    assert target.read_bytes() == before, "status must not modify project state"


def test_status_reports_blockers_and_the_writer_lease(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))
    StateStore(tmp_path / "PROJECT_STATE.yaml").save(
        ProjectState(next_task="P01-T11", blockers=["B-001"])
    )
    (tmp_path / "state").mkdir(exist_ok=True)
    (tmp_path / "state" / "blockers.yaml").write_text(
        "blockers:\n"
        "  - id: B-001\n"
        "    summary: awaiting Amanda review\n"
        "    severity: DEGRADING\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "B-001" in result.stdout


def test_severity_is_never_inferred_from_the_id_prefix():
    informational = Blocker(
        id="BLOCK-1", summary="naming coincidence", severity=Severity.INFORMATIONAL
    )
    blocking = Blocker(id="B-2", summary="real obstacle", severity=Severity.BLOCKING)

    graph = phase_graph()
    assert graph.blocked_tasks([informational]) == set()
    assert graph.blocked_tasks([blocking]) == set()


def test_blocking_a_phase_also_blocks_its_dependents():
    blocker = Blocker(
        id="B-REVIT",
        summary="Revit provider unproven",
        severity=Severity.BLOCKING,
        affected_tasks=["PHASE_02"],
    )

    blocked = phase_graph().blocked_tasks([blocker])

    assert "PHASE_02" in blocked
    assert "PHASE_05" in blocked, "the compiler depends on the provider work"
    assert "PHASE_03" not in blocked, "source intelligence is independent"
    assert "PHASE_04" not in blocked


def test_unknown_dependencies_and_cycles_are_rejected():
    from amanda_agent.models.tasks import TaskGraph, TaskNode

    unknown = TaskGraph()
    unknown.add(TaskNode(id="A", name="a", phase_id="P", depends_on=["MISSING"]))
    with pytest.raises(ValueError):
        unknown.validate_graph()

    cyclic = TaskGraph()
    cyclic.add(TaskNode(id="A", name="a", phase_id="P", depends_on=["B"]))
    cyclic.add(TaskNode(id="B", name="b", phase_id="P", depends_on=["A"]))
    with pytest.raises(ValueError):
        cyclic.validate_graph()


def test_resume_lists_only_unblocked_work(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(tmp_path))
    StateStore(tmp_path / "PROJECT_STATE.yaml").save(ProjectState())

    result = runner.invoke(app, ["resume"])

    assert result.exit_code == 0
    assert "PHASE_03" in result.stdout


def test_rollback_copies_to_a_new_filename(tmp_path: Path):
    checkpoint = tmp_path / "checkpoints" / "R00-lab.rvt"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"checkpoint-payload")
    from amanda_agent.bootstrap.snapshots import sha256_of

    digest = sha256_of(checkpoint)
    target = tmp_path / "work" / "lab-r01.rvt"

    restored = restore_checkpoint(
        checkpoint=checkpoint,
        destination=target,
        expected_sha256=digest,
        writable_roots=[tmp_path],
    )

    assert restored == target
    assert target.read_bytes() == b"checkpoint-payload"
    assert checkpoint.read_bytes() == b"checkpoint-payload", "original stays intact"


def test_rollback_rejects_a_hash_mismatch(tmp_path: Path):
    checkpoint = tmp_path / "R00.rvt"
    checkpoint.write_bytes(b"payload")

    with pytest.raises(RollbackRefused, match="hash"):
        restore_checkpoint(
            checkpoint=checkpoint,
            destination=tmp_path / "new.rvt",
            expected_sha256="0" * 64,
            writable_roots=[tmp_path],
        )


def test_rollback_rejects_an_existing_target_and_outside_roots(tmp_path: Path):
    checkpoint = tmp_path / "R00.rvt"
    checkpoint.write_bytes(b"payload")
    digest = __import__(
        "amanda_agent.bootstrap.snapshots", fromlist=["sha256_of"]
    ).sha256_of(checkpoint)
    existing = tmp_path / "exists.rvt"
    existing.write_bytes(b"do-not-overwrite")

    with pytest.raises(RollbackRefused, match="exists"):
        restore_checkpoint(
            checkpoint=checkpoint,
            destination=existing,
            expected_sha256=digest,
            writable_roots=[tmp_path],
        )
    assert existing.read_bytes() == b"do-not-overwrite"

    outside = tmp_path.parent / "escaped.rvt"
    with pytest.raises(RollbackRefused, match="writable"):
        restore_checkpoint(
            checkpoint=checkpoint,
            destination=outside,
            expected_sha256=digest,
            writable_roots=[tmp_path],
        )
    assert not outside.exists()


def test_rollback_refuses_the_same_file_as_source_and_target(tmp_path: Path):
    checkpoint = tmp_path / "R00.rvt"
    checkpoint.write_bytes(b"payload")
    digest = __import__(
        "amanda_agent.bootstrap.snapshots", fromlist=["sha256_of"]
    ).sha256_of(checkpoint)

    with pytest.raises(RollbackRefused, match="new"):
        restore_checkpoint(
            checkpoint=checkpoint,
            destination=checkpoint,
            expected_sha256=digest,
            writable_roots=[tmp_path],
        )


def test_rollback_requires_a_quiescent_writer_lease(tmp_path: Path):
    from amanda_agent.state.locks import WriterLock

    checkpoint = tmp_path / "R00.rvt"
    checkpoint.write_bytes(b"payload")
    digest = __import__(
        "amanda_agent.bootstrap.snapshots", fromlist=["sha256_of"]
    ).sha256_of(checkpoint)
    lease_path = tmp_path / "state" / "locks" / "revit-writer.lock"
    holder = WriterLock(lease_path, owner="revit-writer")
    holder.acquire()

    with pytest.raises(RollbackRefused, match="lease"):
        restore_checkpoint(
            checkpoint=checkpoint,
            destination=tmp_path / "new.rvt",
            expected_sha256=digest,
            writable_roots=[tmp_path],
            lease_path=lease_path,
        )

    holder.release()
    restore_checkpoint(
        checkpoint=checkpoint,
        destination=tmp_path / "new.rvt",
        expected_sha256=digest,
        writable_roots=[tmp_path],
        lease_path=lease_path,
    )
    assert (tmp_path / "new.rvt").exists()
