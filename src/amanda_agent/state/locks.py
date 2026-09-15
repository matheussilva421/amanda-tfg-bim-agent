"""Single-writer lease for the owned Revit process/document.

The lease is an exclusively created file holding JSON metadata. Ownership is
proved by an owner token, so a stray release call cannot free someone else's
lease. Expiry alone never transfers ownership: a lease is only reclaimed when
the recorded process is provably gone on this same host, and the fencing
generation is advanced so stale writers are rejected downstream.
"""

from __future__ import annotations

import json
import os
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path


class LockError(Exception):
    """Base class for writer-lease failures."""


class LockHeldByAnotherOwner(LockError):
    """The lease is held by a live owner and cannot be taken."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _process_started_utc(process_id: int) -> str | None:
    """Best-effort process start time, used to defeat PID reuse."""
    try:
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, process_id
        )
        if not handle:
            return None
        try:
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel_time = wintypes.FILETIME()
            user_time = wintypes.FILETIME()
            ok = kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel_time),
                ctypes.byref(user_time),
            )
            if not ok:
                return None
            ticks = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
            seconds = ticks / 10_000_000 - 11_644_473_600
            return datetime.fromtimestamp(seconds, timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        return None


class WriterLock:
    def __init__(self, path: Path, *, owner: str, process_id: int | None = None):
        self.path = Path(path)
        self.owner = owner
        self.process_id = os.getpid() if process_id is None else process_id
        self.host = socket.gethostname()
        self.owner_token: str | None = None

    # -- inspection ------------------------------------------------------
    def exists(self) -> bool:
        return self.path.exists()

    def inspect(self) -> dict | None:
        if not self.path.exists():
            return None
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def is_held_by_live_owner(self) -> bool:
        info = self.inspect()
        if not info:
            return False
        if info.get("host") != self.host:
            return True  # cannot prove inactivity on a foreign host
        process_id = info.get("process_id")
        if process_id is None:
            return True
        recorded_start = info.get("process_started_utc")
        live_start = _process_started_utc(int(process_id))
        if live_start is None:
            return False  # process is gone
        if recorded_start and live_start != recorded_start:
            return False  # PID was reused by a different process
        return True

    # -- mutation --------------------------------------------------------
    def acquire(
        self,
        *,
        document_identity: str | None = None,
        reclaim_abandoned: bool = False,
    ) -> dict:
        previous = self.inspect()
        generation = 1

        if previous is not None:
            if previous.get("owner_token") == self.owner_token and self.owner_token:
                return previous  # idempotent re-acquire by the same token
            if not (reclaim_abandoned and not self.is_held_by_live_owner()):
                held = previous.get("owner")
                raise LockHeldByAnotherOwner(
                    "writer lease held by " + str(held) + " at " + str(self.path)
                )
            generation = int(previous.get("fencing_generation", 0)) + 1
            self.path.unlink(missing_ok=True)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        token = str(uuid.uuid4())
        payload = {
            "owner": self.owner,
            "owner_token": token,
            "process_id": self.process_id,
            "process_started_utc": _process_started_utc(self.process_id) or _utc_now(),
            "host": self.host,
            "document_identity": document_identity,
            "heartbeat_utc": _utc_now(),
            "fencing_generation": generation,
        }
        try:
            handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise LockHeldByAnotherOwner(
                "writer lease raced by another process at " + str(self.path)
            ) from exc
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        self.owner_token = token
        return payload

    def heartbeat(self, *, document_identity: str | None = None) -> dict:
        info = self.inspect()
        if info is None:
            raise LockError("no active writer lease at " + str(self.path))
        if info.get("owner_token") != self.owner_token:
            raise LockError("heartbeat attempted by a non-owner")
        info["heartbeat_utc"] = _utc_now()
        if document_identity is not None:
            info["document_identity"] = document_identity
        self.path.write_text(
            json.dumps(info, indent=2, sort_keys=True), encoding="utf-8"
        )
        return info

    def release(self) -> bool:
        info = self.inspect()
        if info is None:
            return False
        if info.get("owner_token") != self.owner_token:
            return False
        self.path.unlink(missing_ok=True)
        self.owner_token = None
        return True

    def __enter__(self) -> "WriterLock":
        self.acquire(reclaim_abandoned=True)
        return self

    def __exit__(self, *exc_info) -> None:
        self.release()
