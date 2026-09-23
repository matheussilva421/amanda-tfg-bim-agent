from __future__ import annotations

import json
from pathlib import Path

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
CANONICAL_PLAN = "docs/superpowers/plans/08-amanda-production-run.md"
CANONICAL_RUN = "AMANDA-RUN-002-PAVILION"
CANONICAL_SOLUTION = "AMANDA-RUN-002-PAVILION-S02"
LAYOUT_HASH = "20529b1d08c570546641397a4e9fd302a2a23bef917f50bfea6d22824a19f556"
SOLUTION_APPROVAL_HASH = "75afda89d6a18cd2834bdd571e761ea047305465c6579a4a9d0474e409f91bdf"
LINEAR_ARCHIVE_SHA256 = "ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29"
LINEAR_ARCHIVE = (
    "revit/production/archive/superseded-linear/"
    "AMANDA-RUN-001-S01-R12-linear-historical-20260922.rvt"
)


def _yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def _expected_selection():
    profile = CanonicalReferenceProfile.load(ROOT)
    program = json.loads(
        (ROOT / "project/requirements/program.json").read_text(encoding="utf-8")
    )
    layout = build_canonical_pavilion_layout(program, profile)
    return build_canonical_selection(
        layout,
        profile,
        generation_run=CANONICAL_RUN,
        timestamp="2026-09-23T00:00:00Z",
    )


def test_project_state_selects_user_directed_canonical_pavilion_before_r04():
    state = _yaml("PROJECT_STATE.yaml")
    assert state["selected_design"] == CANONICAL_SOLUTION
    assert state["selection_authority"] == "USER_DIRECTED"
    assert state["detailed_variant_authority"] == "AGENT_DELEGATED"
    assert state["selection_approval_hash"] == SOLUTION_APPROVAL_HASH
    assert state["layout_module"] == "src/amanda_agent/design/canonical_pavilion_layout.py"
    assert state["layout_content_hash"] == LAYOUT_HASH
    assert state["layout_net_internal_m2"] == 626.0
    assert state["layout_external_program_m2"] == 260.0
    assert state["layout_gross_enclosed_m2"] is None
    assert state["layout_covered_total_m2"] is None
    assert state["layout_gross_enclosed_estimate_m2"] == "783-814"
    assert state["layout_covered_estimate_m2"] == "850-950"
    assert state["revit_stage"] == "PRE_R04"
    assert state["current_checkpoint"] is None
    assert state["historical_r12_checkpoint"] == (
        "revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/"
        "R12-materials-20260922.rvt"
    )
    assert state["next_task"] == "P08-CAN-T07"
    assert "SITE_TOPOGRAPHY:BLOCKING" in state["blockers"]
    assert "SITE_BOUNDARY:BLOCKING" in state["blockers"]
    assert "SITE_OCCUPANCY:BLOCKING" in state["blockers"]
    assert "SITE_FRONTAGE_COUNT:DEGRADING" in state["blockers"]
    assert "SITE_TRUE_NORTH:DEGRADING" in state["blockers"]
    assert "REVIT_PIPE_SANDBOX_ACCESS:DEGRADING" in state["blockers"]


def test_decision_register_persists_supersedence_and_content_bound_selection():
    register = DecisionRegister.model_validate(
        _yaml("project/requirements/decision-register.yaml")
    )
    expected = _expected_selection()
    supersession = register.get("DEC-CANONICAL-R12-SUPERSESSION-001")
    parti = register.get("DEC-CANONICAL-PARTI-001")
    detail = register.get("DEC-CANONICAL-DETAIL-002")

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
    assert parti.model_dump(mode="json") == expected.parti_decision.model_dump(
        mode="json"
    )
    assert detail.approval_hash == expected.decision.approval_hash
    assert detail.source_refs == expected.decision.source_refs
    assert detail.selection_authority.value == "AGENT_DELEGATED"
    assert all(
        any(reference.endswith(digest) for reference in parti.source_refs)
        for digest in CanonicalReferenceProfile.load(ROOT).source_hashes
    )


def test_task_graph_suspends_linear_tail_and_activates_unique_canonical_chain():
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
    assert next_task.status is TaskStatus.PENDING
    assert next_task.plan_path == CANONICAL_PLAN
    assert registry.unready_dependencies("P08-CAN-T07") == []
    assert next_task.depends_on == ["P08-CAN-T06"]
    assert registry.tasks["P08-CAN-T08"].depends_on == ["P08-CAN-T07"]
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
