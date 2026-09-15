"""Turn the site gap registry into durable blockers.

The missing-data file is the single description of what the site evidence does
not establish.  This module projects the topology gap onto the typed blocker
registry so the status, resume and task-graph commands can honour it without
re-reading YAML by hand.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..models.tasks import Severity
from ..state.blockers import (
    FINAL_GRADING_TASK,
    SCHEMATIC_MACROZONING_TASK,
    BlockerRecord,
    BlockerRegistry,
)
from .compile import missing_data_payload

# Plan 03 task 11 names these two blocked checks; the registry keeps the
# plan vocabulary so evidence and code use the same words.
FINAL_ALTIMETRIC_ACCESSIBILITY_TASK = "final-altimetric-accessibility-validation"

_SCOPE_TO_TASKS: dict[str, list[str]] = {
    "SITE_TOPOGRAPHY": [
        FINAL_GRADING_TASK,
        FINAL_ALTIMETRIC_ACCESSIBILITY_TASK,
    ],
    "SITE_BOUNDARY": ["final-area-verification"],
    "SITE_OCCUPANCY": ["final-site-availability-claim"],
    "SITE_FRONTAGE_COUNT": ["final-corner-and-setback-designation"],
    "SITE_TRUE_NORTH": ["final-orientation-compliance-statement"],
}

_STILL_ALLOWED: dict[str, list[str]] = {
    "SITE_TOPOGRAPHY": [SCHEMATIC_MACROZONING_TASK, "planar-massing-study"],
    "SITE_BOUNDARY": ["schematic-sectorization", "study-massing"],
    "SITE_OCCUPANCY": ["study-scenario-development"],
    "SITE_FRONTAGE_COUNT": ["preliminary-access-split"],
    "SITE_TRUE_NORTH": ["study-orientation-reasoning"],
}

_SEVERITY: dict[str, Severity] = {
    "MISSING": Severity.BLOCKING,
    "CONFLICTING": Severity.DEGRADING,
    "PARTIAL": Severity.DEGRADING,
}


def blocker_records(payload: dict | None = None) -> list[BlockerRecord]:
    """Project each gap entry into a typed blocker with explicit scope."""

    payload = payload or missing_data_payload()
    records: list[BlockerRecord] = []
    for entry in payload["entries"]:
        gap_id = entry["id"]
        records.append(
            BlockerRecord(
                id=gap_id,
                summary=entry["what_is_missing"],
                severity=_SEVERITY[entry["state"]],
                source=gap_id,
                evidence=entry["evidence"],
                tasks_blocked=_SCOPE_TO_TASKS[gap_id],
                tasks_still_allowed=_STILL_ALLOWED[gap_id],
                resolution_action=entry["resolution_action"],
                created_utc="2026-09-15T00:00:00Z",
            )
        )
    return records


def blockers_payload(payload: dict | None = None) -> dict:
    """Serialize the projected records as a right-shaped registry document."""

    registry = BlockerRegistry()
    for record in blocker_records(payload):
        registry.add(record)
    return registry.model_dump(mode="json")


def sync_blockers(path: Path, payload: dict | None = None) -> dict:
    """Merge the site gaps into an existing blocker registry file."""

    path = Path(path)
    if path.exists():
        registry = BlockerRegistry.load(path)
    else:
        registry = BlockerRegistry()
    existing = {record.id for record in registry.blockers}
    for record in blocker_records(payload):
        if record.id in existing:
            registry.blockers = [
                record if item.id == record.id else item
                for item in registry.blockers
            ]
            continue
        registry.add(record)
    registry.save(path)
    return registry.model_dump(mode="json")


def load_missing_data(root: Path) -> dict:
    """Read the on-disk gap registry, failing loudly when it is absent."""

    path = Path(root) / "project" / "site" / "missing-data.yaml"
    if not path.exists():
        raise FileNotFoundError("missing site gap registry: " + str(path))
    return yaml.safe_load(path.read_text(encoding="utf-8"))


__all__ = [
    "FINAL_ALTIMETRIC_ACCESSIBILITY_TASK",
    "blocker_records",
    "blockers_payload",
    "load_missing_data",
    "sync_blockers",
]
