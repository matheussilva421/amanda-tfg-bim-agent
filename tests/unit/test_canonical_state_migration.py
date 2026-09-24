from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from amanda_agent.design.canonical_pavilion_layout import (
    build_canonical_pavilion_layout,
)
from amanda_agent.design.canonical_reference import CanonicalReferenceProfile
from amanda_agent.models.state import TaskStatus
from amanda_agent.production.selection import build_canonical_selection
from amanda_agent.requirements.decisions import DecisionRegister
from amanda_agent.state.tasks import TaskRegistry

ROOT = Path(__file__).resolve().parents[2]
LINEAR_ARCHIVE_SHA256 = "ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29"
LINEAR_ARCHIVE = (
    "revit/production/archive/superseded-linear/"
    "AMANDA-RUN-001-S01-R12-linear-historical-20260922.rvt"
)


def _yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def _expected_selection(profile: CanonicalReferenceProfile):
    program = json.loads(
        (ROOT / "project/requirements/program.json").read_text(encoding="utf-8")
    )
    layout = build_canonical_pavilion_layout(program, profile)
    return build_canonical_selection(
        layout,
        profile,
        generation_run="AMANDA-RUN-002-PAVILION",
        timestamp="2026-09-23T00:00:00Z",
    )


def test_project_state_is_repository_recovery_without_architectural_promotion():
    state = _yaml("PROJECT_STATE.yaml")
    assert state["phase_id"] == "REPOSITORY_RECOVERY"
    assert state["phase_name"] == "repository-recovery"
    assert state["phase_status"] == "RUNNING"
    assert state["last_completed_task"] is None
    assert state["next_task"] == "RECOVERY-VALIDATE"
    assert state["schema_version"] == 1
    assert state["state_revision"] == 173
    assert state["phase_gate"] == "GO_WITH_LIMITATIONS"
    assert state["selected_design"] is None
    assert state["revit_stage"] == "PRE_R04"
    assert state["current_checkpoint"] is None
    assert state["blockers"] == [
        "SITE_TOPOGRAPHY:BLOCKING",
        "SITE_BOUNDARY:BLOCKING",
        "SITE_OCCUPANCY:BLOCKING",
        "SITE_FRONTAGE_COUNT:DEGRADING",
        "SITE_TRUE_NORTH:DEGRADING",
    ]
    assert state["last_verified_commit"] is None
    assert set(state) == {
        "project",
        "phase_id",
        "phase_name",
        "phase_status",
        "last_completed_task",
        "next_task",
        "schema_version",
        "state_revision",
        "phase_gate",
        "selected_design",
        "revit_stage",
        "current_checkpoint",
        "blockers",
        "last_verified_commit",
    }


def test_s02_decisions_remain_historical_while_four_board_layout_is_unimplemented():
    register = DecisionRegister.model_validate(
        _yaml("project/requirements/decision-register.yaml")
    )
    supersession = register.get("DEC-CANONICAL-R12-SUPERSESSION-001")
    parti = register.get("DEC-CANONICAL-PARTI-001")
    detail = register.get("DEC-CANONICAL-DETAIL-002")
    profile = CanonicalReferenceProfile.load(ROOT)
    historical_source_refs = tuple(
        reference
        for reference in parti.source_refs
        if reference.startswith("canonical/")
    )
    historical_images = tuple(
        reference.split("#sha256=", maxsplit=1)[0]
        for reference in historical_source_refs
    )
    historical_hashes = tuple(
        reference.rsplit("#sha256=", maxsplit=1)[1]
        for reference in historical_source_refs
    )
    assert len(profile.source_hashes) == 4
    assert historical_images == profile.canonical_images[:3]
    assert historical_hashes == profile.source_hashes[:3]
    historical_profile = replace(
        profile,
        canonical_images=historical_images,
        source_hashes=historical_hashes,
    )
    expected = _expected_selection(historical_profile)

    assert supersession.selection_authority.value == "USER_DIRECTED"
    assert supersession.selected_option.startswith(
        "AMANDA-RUN-001-S01 is SUPERSEDED_BY_USER_DIRECTION"
    )
    assert supersession.supersedes == "DEC-P08-T09-SELECTION-001"
    assert f"{LINEAR_ARCHIVE}#sha256={LINEAR_ARCHIVE_SHA256}" in supersession.source_refs
    assert any(
        "AMANDA-RUN-001-S01" in rejected
        for rejected in supersession.rejected_options
    )
    assert parti.selection_authority.value == "USER_DIRECTED"
    assert parti.approval_hash == "f8d36c67c37ac7b2a6387d5f186f29756e6e611bf3ffb8590e9b336b4be10542"
    assert "three canonical design boards" in parti.selected_option
    assert parti.model_dump(mode="json") == expected.parti_decision.model_dump(
        mode="json"
    )
    assert detail.approval_hash == "89c57532d9bc215969d36ec0e0d26e1966e7e333adc734e216a3e9f01f4d620c"
    assert detail.approval_hash == expected.decision.approval_hash
    assert detail.source_refs == expected.decision.source_refs
    assert detail.selection_authority.value == "AGENT_DELEGATED"
    assert detail.validation_status.value == "BLOCKED_BY_INPUT"
    assert profile.source_hashes[3] not in parti.source_refs

    program = yaml.safe_load(
        (ROOT / "project/requirements/program.json").read_text(encoding="utf-8")
    )
    with pytest.raises(ValueError, match="all three canonical board hashes must be bound"):
        build_canonical_pavilion_layout(program, profile)


def test_task_graph_keeps_completed_s02_history_and_blocks_its_stale_tail():
    graph_data = _yaml("state/task-graph.yaml")
    registry = TaskRegistry.model_validate(graph_data)
    linear_task = registry.tasks["P08-T13"]
    assert linear_task.status is TaskStatus.SUSPENDED
    assert any("R12" in evidence and LINEAR_ARCHIVE_SHA256 in evidence for evidence in linear_task.evidence)
    for task_id in (f"P08-T{i:02}" for i in range(14, 20)):
        assert registry.tasks[task_id].status is TaskStatus.SUSPENDED

    canonical_ids = [f"P08-CAN-T{i:02}" for i in range(1, 20)]
    assert all(task_id in registry.tasks for task_id in canonical_ids)
    assert [registry.tasks[task_id].status for task_id in canonical_ids[:6]] == [
        TaskStatus.PASS_WITH_WARNINGS,
        TaskStatus.PASS,
        TaskStatus.PASS_WITH_WARNINGS,
        TaskStatus.PASS_WITH_WARNINGS,
        TaskStatus.PASS,
        TaskStatus.PASS_WITH_WARNINGS,
    ]
    next_task = registry.tasks["P08-CAN-T07"]
    assert next_task.status is TaskStatus.PASS_WITH_WARNINGS
    assert registry.unready_dependencies("P08-CAN-T07") == []
    assert next_task.depends_on == ["P08-CAN-T06"]
    assert registry.tasks["P08-CAN-T08"].status is TaskStatus.BLOCKED_BY_TOOL
    assert registry.tasks["P08-CAN-T08"].depends_on == ["P08-CAN-T07"]
    assert registry.tasks["P08-CAN-T09"].status is TaskStatus.PENDING
    assert registry.tasks["P08-CAN-T18"].depends_on == ["P08-CAN-T17"]
    assert registry.tasks["P08-CAN-T19"].depends_on == ["P08-CAN-T18"]
    registry.validate()


def test_migration_history_preserves_existing_entries_and_records_transition():
    history = _yaml("state/task-history.yaml")["entries"]
    expected_historical_statuses = {
        "P08-T01": "PASS_WITH_WARNINGS",
        "P08-T02": "PASS",
        "P08-T03": "PASS",
        "P08-T04": "PASS",
        "P08-T05": "PASS",
        "P08-T06": "PASS",
        "P08-T07": "PASS",
    }
    for task_id, status in expected_historical_statuses.items():
        assert any(
            entry["task_id"] == task_id and entry["status"] == status
            for entry in history
        )
    for old_task_id in (f"P08-T{i:02}" for i in range(13, 20)):
        entries = [entry for entry in history if entry["task_id"] == old_task_id]
        assert entries and entries[-1]["status"] == "SUSPENDED"
    for new_task_id in (f"P08-CAN-T{i:02}" for i in range(1, 7)):
        entries = [entry for entry in history if entry["task_id"] == new_task_id]
        assert entries and entries[-1]["status"] in {"PASS", "PASS_WITH_WARNINGS"}
