import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from amanda_agent.state.locks import LockHeldByAnotherOwner, WriterLock


def test_second_writer_cannot_acquire_the_same_lease(tmp_path: Path):
    path = tmp_path / "revit-writer.lock"
    first = WriterLock(path, owner="agent-a", process_id=os.getpid())
    second = WriterLock(path, owner="agent-b", process_id=os.getpid())

    first.acquire()
    with pytest.raises(LockHeldByAnotherOwner):
        second.acquire()


def test_owner_only_release(tmp_path: Path):
    path = tmp_path / "revit-writer.lock"
    holder = WriterLock(path, owner="agent-a", process_id=os.getpid())
    intruder = WriterLock(path, owner="agent-b", process_id=os.getpid())

    holder.acquire()
    intruder.release()
    assert path.exists(), "a non-owner release must not free the lease"

    holder.release()
    assert not path.exists()


def test_lease_records_owner_token_pid_host_and_fencing(tmp_path: Path):
    path = tmp_path / "revit-writer.lock"
    lock = WriterLock(path, owner="agent-a", process_id=os.getpid())
    lock.acquire(document_identity=r"C:\work\lab.rvt")

    info = lock.inspect()

    assert info["owner"] == "agent-a"
    assert info["process_id"] == os.getpid()
    assert info["host"]
    assert info["document_identity"].endswith("lab.rvt")
    assert info["fencing_generation"] == 1
    assert info["owner_token"]


def test_heartbeat_advances_without_changing_fencing_generation(tmp_path: Path):
    path = tmp_path / "revit-writer.lock"
    lock = WriterLock(path, owner="agent-a", process_id=os.getpid())
    lock.acquire()
    first = lock.inspect()

    lock.heartbeat()
    second = lock.inspect()

    assert second["fencing_generation"] == first["fencing_generation"]
    assert second["heartbeat_utc"] >= first["heartbeat_utc"]


def test_abandoned_lease_requires_proof_of_inactivity(tmp_path: Path):
    path = tmp_path / "revit-writer.lock"
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    payload = {
        "owner": "dead-agent",
        "owner_token": "token-x",
        "process_id": dead.pid,
        "process_started_utc": "2000-01-01T00:00:00Z",
        "host": socket.gethostname(),
        "document_identity": None,
        "heartbeat_utc": "2000-01-01T00:00:00Z",
        "fencing_generation": 4,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    lock = WriterLock(path, owner="agent-b", process_id=os.getpid())
    assert lock.is_held_by_live_owner() is False

    lock.acquire(reclaim_abandoned=True)
    info = lock.inspect()
    assert info["owner"] == "agent-b"
    assert info["fencing_generation"] == 5, "fencing must advance on reclamation"


def test_lease_from_another_host_is_never_reclaimed_automatically(tmp_path: Path):
    path = tmp_path / "revit-writer.lock"
    payload = {
        "owner": "remote-agent",
        "owner_token": "token-y",
        "process_id": os.getpid(),
        "process_started_utc": "2000-01-01T00:00:00Z",
        "host": "some-other-host",
        "document_identity": None,
        "heartbeat_utc": "2000-01-01T00:00:00Z",
        "fencing_generation": 1,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    lock = WriterLock(path, owner="agent-b", process_id=os.getpid())
    with pytest.raises(LockHeldByAnotherOwner):
        lock.acquire(reclaim_abandoned=True)
