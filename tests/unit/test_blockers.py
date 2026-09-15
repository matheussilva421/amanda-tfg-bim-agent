"""Contract tests for durable, scope-aware blocker records."""

from pathlib import Path

from amanda_agent.models.tasks import Blocker, Severity
from amanda_agent.state.blockers import (
    BlockerRecord,
    BlockerRegistry,
    load_registry,
    missing_aps_authorization,
    missing_revit_license,
    missing_site_topography,
)


def test_extended_blocker_keeps_legacy_model_fields_and_describes_scope():
    blocker = BlockerRecord(
        id="SITE_TOPOGRAPHY",
        summary="verified site topography is missing",
        severity=Severity.BLOCKING,
        source="project inputs",
        evidence="no surveyed elevation file was supplied",
        tasks_blocked=["final-grading"],
        tasks_still_allowed=["schematic-macrozoning"],
        resolution_action="provide a verified survey/topography source",
        created_utc="2026-09-15T12:00:00Z",
    )

    assert isinstance(blocker, Blocker)
    assert blocker.affected_tasks == ["final-grading"]
    assert blocker.tasks_blocked == ["final-grading"]
    assert blocker.is_open is True


def test_registry_accepts_the_existing_blocker_model_additively():
    legacy = Blocker(
        id="LEGACY",
        summary="legacy obstacle",
        severity=Severity.BLOCKING,
        affected_tasks=["legacy-task"],
        evidence="legacy evidence",
    )

    stored = BlockerRegistry().add(legacy)

    assert isinstance(stored, BlockerRecord)
    assert stored.tasks_blocked == ["legacy-task"]
    assert stored.evidence == "legacy evidence"


def test_missing_topography_allows_schematic_macrozoning_but_blocks_final_grading():
    blocker = missing_site_topography(created_utc="2026-09-15T12:00:00Z")

    assert "final-grading" in blocker.tasks_blocked
    assert "schematic-macrozoning" in blocker.tasks_still_allowed


def test_missing_aps_authorization_blocks_cloud_but_keeps_cpu_work_allowed():
    blocker = missing_aps_authorization(created_utc="2026-09-15T12:00:00Z")

    assert "cloud-work" in blocker.tasks_blocked
    assert "cpu-only-ingestion" in blocker.tasks_still_allowed
    assert "cpu-only-solver" in blocker.tasks_still_allowed


def test_missing_or_expired_revit_license_blocks_local_revit_only():
    missing = missing_revit_license(created_utc="2026-09-15T12:00:00Z")
    expired = missing_revit_license(
        status="expired", created_utc="2026-09-15T12:00:00Z"
    )

    assert "local-revit-work" in missing.tasks_blocked
    assert "local-revit-work" in expired.tasks_blocked
    assert "cpu-only-ingestion" in missing.tasks_still_allowed
    assert "cpu-only-solver" in expired.tasks_still_allowed


def test_registry_answers_allowed_tasks_and_persists_readable_blockers_yaml(
    tmp_path: Path,
):
    path = tmp_path / "state" / "blockers.yaml"
    registry = BlockerRegistry(
        blockers=[
            missing_site_topography(created_utc="2026-09-15T12:00:00Z"),
            missing_aps_authorization(created_utc="2026-09-15T12:01:00Z"),
        ]
    )

    registry.save(path)
    raw = path.read_text(encoding="utf-8")
    restored = load_registry(path)

    assert raw.startswith("schema_version: 1\nblockers:\n")
    assert "id: SITE_TOPOGRAPHY" in raw
    assert "tasks_still_allowed:" in raw
    assert set(restored.tasks_still_allowed()) >= {
        "schematic-macrozoning",
        "cpu-only-ingestion",
        "cpu-only-solver",
    }
    assert restored.is_task_blocked("final-grading") is True
    assert restored.is_task_blocked("schematic-macrozoning") is False


def test_resolving_a_blocker_keeps_history_but_stops_blocking_tasks(tmp_path: Path):
    path = tmp_path / "state" / "blockers.yaml"
    registry = BlockerRegistry(
        blockers=[missing_site_topography(created_utc="2026-09-15T12:00:00Z")]
    )

    resolved = registry.resolve(
        "SITE_TOPOGRAPHY",
        resolved_utc="2026-09-15T13:00:00Z",
        resolution_action="verified survey received",
    )
    registry.save(path)
    restored = load_registry(path)

    assert resolved.resolved_utc == "2026-09-15T13:00:00Z"
    assert resolved.is_open is False
    assert restored.is_task_blocked("final-grading") is False
    assert len(restored.blockers) == 1
    assert restored.blockers[0].resolution_action == "verified survey received"
