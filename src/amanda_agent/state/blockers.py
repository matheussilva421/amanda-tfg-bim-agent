"""Durable, scope-aware blocker records.

The existing :class:`amanda_agent.models.tasks.Blocker` is the compatibility
model used by the status and task-graph code.  ``BlockerRecord`` subclasses it
and adds scope and provenance fields, so old ``affected_tasks`` and
``resolution`` payloads remain readable while the registry can answer what
work is still allowed.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from ..models.tasks import Blocker as BaseBlocker
from ..models.tasks import Severity

SCHEMA_VERSION = 1

FINAL_GRADING_TASK = "final-grading"
SCHEMATIC_MACROZONING_TASK = "schematic-macrozoning"
CLOUD_WORK_TASK = "cloud-work"
LOCAL_REVIT_WORK_TASK = "local-revit-work"
CPU_INGESTION_TASK = "cpu-only-ingestion"
CPU_SOLVER_TASK = "cpu-only-solver"


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class BlockerRecord(BaseBlocker):
    """Additive blocker model with explicit blocked/allowed task scope."""

    source: str | None = None
    tasks_blocked: list[str] = Field(default_factory=list)
    tasks_still_allowed: list[str] = Field(default_factory=list)
    # ``allowed_tasks`` is emitted by the existing human-gate integration.
    allowed_tasks: list[str] = Field(default_factory=list)
    resolution_action: str | None = None
    reason: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _sync_legacy_scope_fields(cls, value):
        if isinstance(value, BaseModel):
            data = value.model_dump()
        elif isinstance(value, Mapping):
            data = dict(value)
        else:
            return value

        affected = data.get("affected_tasks") or []
        blocked = data.get("tasks_blocked") or affected
        data["affected_tasks"] = list(affected or blocked)
        data["tasks_blocked"] = list(blocked)

        allowed = data.get("tasks_still_allowed") or data.get("allowed_tasks") or []
        data["tasks_still_allowed"] = list(allowed)
        data["allowed_tasks"] = list(allowed)

        evidence = data.get("evidence")
        source = data.get("source")
        if evidence is None and source is not None:
            data["evidence"] = source
        if source is None and evidence is not None:
            data["source"] = evidence

        resolution = data.get("resolution")
        action = data.get("resolution_action")
        if resolution is None and action is not None:
            data["resolution"] = action
        if action is None and resolution is not None:
            data["resolution_action"] = resolution
        return data

    @property
    def blocked_tasks(self) -> list[str]:
        return list(self.tasks_blocked or self.affected_tasks)


# Public aliases make the extended model discoverable without creating a
# second unrelated blocker type.
RegisteredBlocker = BlockerRecord
Blocker = BlockerRecord


class BlockerRegistry(BaseModel):
    """In-memory registry with YAML persistence and resolution history."""

    schema_version: int = SCHEMA_VERSION
    blockers: list[BlockerRecord] = Field(default_factory=list)

    def add(self, blocker: BlockerRecord | BaseBlocker | Mapping) -> BlockerRecord:
        if isinstance(blocker, BlockerRecord):
            record = blocker
        elif isinstance(blocker, BaseBlocker):
            record = BlockerRecord(**blocker.model_dump())
        else:
            record = BlockerRecord(**dict(blocker))
        if any(existing.id == record.id and existing.is_open for existing in self.blockers):
            raise ValueError("open blocker already exists: " + record.id)
        self.blockers.append(record)
        return record

    register = add

    def get(self, blocker_id: str) -> BlockerRecord:
        for blocker in self.blockers:
            if blocker.id == blocker_id:
                return blocker
        raise KeyError("unknown blocker: " + blocker_id)

    def open_blockers(self) -> list[BlockerRecord]:
        return [blocker for blocker in self.blockers if blocker.is_open]

    def blocked_tasks(self) -> list[str]:
        blocked: set[str] = set()
        for blocker in self.open_blockers():
            if blocker.severity is Severity.BLOCKING:
                blocked.update(blocker.blocked_tasks)
        return sorted(blocked)

    def tasks_still_allowed(self) -> list[str]:
        allowed: set[str] = set()
        for blocker in self.open_blockers():
            allowed.update(blocker.tasks_still_allowed or blocker.allowed_tasks)
        return sorted(allowed)

    # The noun phrase is useful at call sites and keeps the query explicit.
    allowed_tasks = tasks_still_allowed

    def is_task_blocked(self, task_id: str) -> bool:
        return task_id in self.blocked_tasks()

    def resolve(
        self,
        blocker_id: str,
        *,
        resolved_utc: str | None = None,
        resolution_action: str | None = None,
    ) -> BlockerRecord:
        blocker = self.get(blocker_id)
        blocker.resolved_utc = resolved_utc or _utc_now()
        if resolution_action is not None:
            blocker.resolution_action = resolution_action
            blocker.resolution = resolution_action
        return blocker

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "blockers": [blocker.model_dump(mode="json") for blocker in self.blockers],
        }
        path.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> BlockerRegistry:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError("blocker registry not found: " + str(path))
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, Mapping):
            raise TypeError("blocker registry is not a mapping: " + str(path))
        return cls(**raw)


def load_registry(path: Path) -> BlockerRegistry:
    return BlockerRegistry.load(path)


def missing_site_topography(*, created_utc: str | None = None) -> BlockerRecord:
    """Missing survey elevations limit grading but leave schematic work open."""
    return BlockerRecord(
        id="SITE_TOPOGRAPHY",
        summary="verified site topography is missing",
        severity=Severity.BLOCKING,
        source="SITE_TOPOGRAPHY",
        evidence="no verified survey/topographic elevation source was supplied",
        tasks_blocked=[FINAL_GRADING_TASK],
        tasks_still_allowed=[
            SCHEMATIC_MACROZONING_TASK,
            CPU_INGESTION_TASK,
            CPU_SOLVER_TASK,
        ],
        resolution_action="provide and validate a verified site topography source",
        created_utc=created_utc or _utc_now(),
    )


def missing_aps_authorization(*, created_utc: str | None = None) -> BlockerRecord:
    """APS authorization is a cloud gate, not a CPU pipeline gate."""
    return BlockerRecord(
        id="APS_AUTHORIZATION",
        summary="Autodesk APS authorization is missing",
        severity=Severity.BLOCKING,
        source="APS_AUTHORIZATION",
        evidence="no authorized APS login or application credentials are available",
        tasks_blocked=[CLOUD_WORK_TASK],
        tasks_still_allowed=[CPU_INGESTION_TASK, CPU_SOLVER_TASK],
        resolution_action="complete the human APS authorization boundary",
        created_utc=created_utc or _utc_now(),
    )


def missing_revit_license(
    *, status: str = "missing", created_utc: str | None = None
) -> BlockerRecord:
    """Missing or expired licensing gates local Revit work only."""
    if status not in {"missing", "expired"}:
        raise ValueError("status must be 'missing' or 'expired'")
    label = "expired" if status == "expired" else "missing"
    return BlockerRecord(
        id="REVIT_LICENSE_" + status.upper(),
        summary="Revit licence is " + label,
        severity=Severity.BLOCKING,
        source="REVIT_LICENSE",
        evidence="Revit installation files do not prove an active licence",
        tasks_blocked=[LOCAL_REVIT_WORK_TASK],
        tasks_still_allowed=[CPU_INGESTION_TASK, CPU_SOLVER_TASK],
        resolution_action="validate an active Autodesk Revit licence",
        created_utc=created_utc or _utc_now(),
    )


def expired_revit_license(*, created_utc: str | None = None) -> BlockerRecord:
    return missing_revit_license(status="expired", created_utc=created_utc)
