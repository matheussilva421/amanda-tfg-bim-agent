"""Behavioural contract of the production BIM driver for the Amanda TFG.

The driver is the bridge that was missing between the delegated architectural
layout and the Revit stage vocabulary.  These tests fix what it must produce and
what it must refuse, without touching Revit.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from shapely.geometry import LineString

from amanda_agent.design.models import (
    DesignSolution,
    DesignStatus,
    compute_design_approval_hash,
)
from amanda_agent.requirements.decisions import (
    DecisionRecord,
    ReviewStatus,
    SelectionAuthority,
    SelectionKind,
    ValidationStatus,
    compute_approval_hash as compute_decision_hash,
)
from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import ExecutionMode
from amanda_agent.bim.stages.accessibility import (
    AccessibleRoute,
    AccessibilityInput,
    WidthCheck,
)
from amanda_agent.design.architectural_layout import build_courtyard_layout
from amanda_agent.models.capability import (
    CapabilityRegistry,
    CapabilityStatus,
    EvidenceScope,
    ProviderCapability,
)
from amanda_agent.production.layout_bim import (
    ProductionBimError,
    build_layout_stage_plans,
    build_walls,
    layout_stage_order,
)
from amanda_agent.production.selection import build_selection

ROOT = Path(__file__).resolve().parents[2]
PROGRAM_PATH = ROOT / "project" / "requirements" / "program.json"

BUILD = "27.2.0.39"
SCHEMA = "8b9600f5274d7dffb6e5bd5f"
RUN = "AMANDA-RUN-001"
SOLUTION = "AMANDA-RUN-001-F01"
APPROVAL = "67e502d8d224c069320bbaa8faacb704f1a29dc75440b711442df1abd621c08b"

#: Every operation the production chain must be able to reach.
REQUIRED_OPERATIONS = (
    "revit.create_project",
    "revit.create_wall",
    "revit.create_floor",
    "revit.create_slab",
    "revit.create_roof",
    "revit.create_internal_wall",
    "revit.create_opening",
    "revit.create_room",
    "revit.create_accessibility_element",
    "revit.create_furniture_element",
    "revit.create_landscape_element",
    "revit.assign_material",
    "revit.create_documentation_element",
)

#: Operations the registry records under a provider name and the crosswalk
#: aliases into the semantic vocabulary the stages ask for.
ALIASED_OPERATIONS = {
    "level": ("revit.create_level",),
    "grid": ("revit.create_grid",),
    "reference": ("revit.create_reference",),
    "mass": ("revit.create_mass",),
}


def _evidence(tmp_path: Path, name: str) -> str:
    path = tmp_path / name
    path.write_text('{"proven": true}\n', encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{path.as_posix()}::sha256={digest}"


def _entry(tmp_path: Path, operation: str) -> ProviderCapability:
    return ProviderCapability(
        provider="horizun",
        status=CapabilityStatus.PASS,
        priority=10,
        provider_commit="cc4ea04e9ecfe547ad349f22e0864019ce1ead1f",
        transport_provider="horizun-revit-mcp",
        tool_schema_hash=SCHEMA,
        tested_scope={"operation": operation, "writes": True},
        tested_scope_aliases=ALIASED_OPERATIONS.get(operation, ()),
        evidence_scope=EvidenceScope.PRODUCTION,
        revit_build=BUILD,
        save_reopen=True,
        independent_query=True,
        evidence=[_evidence(tmp_path, f"{operation}.json")],
    )


@pytest.fixture(scope="module")
def program() -> dict:
    return json.loads(PROGRAM_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def layout(program: dict):
    return build_courtyard_layout(program)


@pytest.fixture()
def registry(tmp_path: Path) -> CapabilityRegistry:
    return CapabilityRegistry(
        preferred_provider="horizun",
        entries=[
            *[_entry(tmp_path, operation) for operation in REQUIRED_OPERATIONS],
            *[_entry(tmp_path, operation) for operation in ALIASED_OPERATIONS],
        ],
    )


@pytest.fixture(scope="module")
def selection(layout):
    return build_selection(
        layout, generation_run=RUN, timestamp="2026-09-16T15:00:00Z"
    )


def _accessibility(layout) -> AccessibilityInput:
    """Describe the access the plan actually provides, with measured widths."""

    entrance = layout.face_rooms("street")[0].logical_id
    accessible = [room.logical_id for room in layout.rooms if room.accessible] or [
        entrance
    ]
    return AccessibilityInput(
        entrance_id=entrance,
        required_space_ids=accessible,
        routes=[
            AccessibleRoute(
                logical_id="ROUTE-ENTRANCE-%s" % room.logical_id,
                from_node=entrance,
                to_node=room.logical_id,
                measured_width_m=layout.corridor_width_m,
                source_ref="measured gallery width from the adopted layout",
            )
            for room in layout.rooms
        ],
        widths=[
            WidthCheck(
                logical_id="WIDTH-GALLERY",
                location="circulation spine",
                measured_width_m=layout.corridor_width_m,
                source_ref="measured gallery width from the adopted layout",
            )
        ],
    )


def _plans(registry, program, layout, tmp_path: Path, **overrides):
    """Build the stage plans with the approved selection by default."""

    solution = overrides.pop("solution", _DEFAULT_SELECTION["value"])
    kwargs = dict(
        program=program,
        layout=layout,
        registry=registry,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
        generation_run=RUN,
        solution_id=solution.solution_id,
        approval_hash=solution.approval_hash,
        solution=solution,
        accessibility_input=_accessibility(layout),
        template_root=tmp_path,
    )
    kwargs.update(overrides)
    return build_layout_stage_plans(**kwargs)


#: Filled by the module-scoped selection fixture so every helper can reach it.
_DEFAULT_SELECTION: dict = {}


@pytest.fixture(scope="module", autouse=True)
def _bind_selection(selection):
    _DEFAULT_SELECTION["value"] = selection.solution
    yield
    _DEFAULT_SELECTION.clear()


def test_stage_order_is_the_documented_progression():
    assert layout_stage_order() == (
        BimStage.R01,
        BimStage.R02,
        BimStage.R03,
        BimStage.R04,
        BimStage.R05,
        BimStage.R06,
        BimStage.R07,
        BimStage.R08,
        BimStage.R09,
        BimStage.R10,
        BimStage.R11,
        BimStage.R12,
        BimStage.R13,
    )


def test_every_stage_is_planned_with_bound_operations(registry, program, layout, tmp_path):
    plans = _plans(registry, program, layout, tmp_path)

    assert [plan.stage for plan in plans] == list(layout_stage_order())
    for plan in plans:
        assert plan.preflight.ok, plan.preflight.problems
        if plan.stage is BimStage.R02:
            # No verified topography exists for this lot, so the site stage
            # deliberately plans no write and records the blockers instead of
            # inventing a ground surface.
            assert plan.operations == []
            assert plan.blockers
            assert plan.representation.value == "PLANAR_PLACEHOLDER"
            continue
        assert plan.operations, plan.stage.name
        for operation in plan.operations:
            assert operation.preferred_provider == "horizun"
            assert operation.payload["solution_id"] == _DEFAULT_SELECTION[
                "value"
            ].solution_id
            assert operation.payload["approval_hash"] == _DEFAULT_SELECTION[
                "value"
            ].approval_hash


def test_plans_refuse_a_capability_the_registry_cannot_prove(program, layout, tmp_path):
    thin = CapabilityRegistry(
        preferred_provider="horizun",
        entries=[_entry(tmp_path, "revit.create_project")],
    )
    # The stage preflight names the missing capability rather than approximating
    # it, so the refusal arrives as a stage error, not as a silent downgrade.
    with pytest.raises(Exception) as refused:
        _plans(thin, program, layout, tmp_path)
    message = str(refused.value)
    assert "capability" in message.lower() or "registry" in message.lower()


def test_shell_carries_the_envelope_floor_roof_and_partitions(registry, program, layout, tmp_path):
    plans = _plans(registry, program, layout, tmp_path)
    shell = next(plan for plan in plans if plan.stage is BimStage.R05)
    categories = {element.category for element in shell.desired_state.elements}

    assert {"WALL", "FLOOR", "ROOF"} <= categories
    assert shell.area_reconciliation["net_room_area_m2"] == pytest.approx(626.0, abs=1e-6)
    assert shell.area_reconciliation["gross_shell_area_m2"] == pytest.approx(
        layout.footprint.area, rel=1e-6
    )
    exterior, partitions = build_walls(layout)
    assert all(wall.length_m > 1e-6 for wall in [*exterior, *partitions])
    wall_ids = {
        element.logical_id
        for element in shell.desired_state.elements
        if element.category == "WALL"
    }
    assert {wall.logical_id for wall in exterior} <= wall_ids
    assert partitions


def test_layout_stage_builds_internal_walls_for_every_partition(registry, program, layout, tmp_path):
    plans = _plans(registry, program, layout, tmp_path)
    stage = next(plan for plan in plans if plan.stage is BimStage.R06)
    _, partitions = build_walls(layout)
    shared = [
        wall for wall in partitions if len(wall.rooms) > 1 and not wall.on_gallery
    ]

    # R06 builds the walls between two rooms.  A gallery frontage is carried by
    # the shell and the room itself (an opening), not as a second internal wall.
    assert len(stage.operations) == len(shared)
    for operation in stage.operations:
        assert operation.semantic_capability == "revit.create_internal_wall"


def test_layout_stage_bridges_template_internal_wall_type(
    registry, program, layout, tmp_path
):
    plans = _plans(registry, program, layout, tmp_path)
    stage = next(plan for plan in plans if plan.stage is BimStage.R06)

    assert stage.operations
    assert {operation.payload["type_id"] for operation in stage.operations} == {220}


def test_shell_does_not_duplicate_shared_boundaries_owned_by_r06(
    registry, program, layout, tmp_path
):
    plans = _plans(registry, program, layout, tmp_path)
    by_stage = {plan.stage: plan for plan in plans}

    def body(operation):
        coordinates = operation.payload["geometry"]["coordinates"]
        thickness = float(operation.payload["properties"]["thickness_m"])
        return LineString(coordinates).buffer(thickness / 2.0, cap_style=2)

    r05_walls = [
        operation
        for operation in by_stage[BimStage.R05].operations
        if operation.semantic_capability == "revit.create_wall"
    ]
    r06_walls = by_stage[BimStage.R06].operations

    for shell_wall in r05_walls:
        for layout_wall in r06_walls:
            overlap_area = body(shell_wall).intersection(body(layout_wall)).area
            assert overlap_area <= 1e-8, (
                shell_wall.logical_id,
                layout_wall.logical_id,
                overlap_area,
            )


def test_openings_are_hosted_on_real_walls_with_diagonal_corners(registry, program, layout, tmp_path):
    plans = _plans(registry, program, layout, tmp_path)
    stage = next(plan for plan in plans if plan.stage is BimStage.R07)
    exterior, partitions = build_walls(layout)
    wall_ids = {wall.logical_id for wall in [*exterior, *partitions]}

    assert stage.operations
    for operation in stage.operations:
        host = str(operation.payload["properties"]["host_logical_id"])
        assert host in wall_ids, operation.logical_id
        first, second = operation.payload["corner_1"], operation.payload["corner_2"]
        assert first[2] != second[2], operation.logical_id
    kinds = {operation.payload["properties"]["kind"] for operation in stage.operations}
    assert {"DOOR", "WINDOW"} <= kinds


def test_later_wall_consumers_reference_ids_created_by_r05_or_r06(
    registry, program, layout, tmp_path
):
    plans = _plans(registry, program, layout, tmp_path)
    by_stage = {plan.stage: plan for plan in plans}
    created_wall_ids = {
        operation.logical_id
        for stage in (BimStage.R05, BimStage.R06)
        for operation in by_stage[stage].operations
        if operation.semantic_capability
        in {"revit.create_wall", "revit.create_internal_wall"}
    }

    opening_hosts = {
        str(operation.payload["properties"]["host_logical_id"])
        for operation in by_stage[BimStage.R07].operations
    }
    material_targets = {
        operation.logical_id for operation in by_stage[BimStage.R12].operations
    }

    assert opening_hosts <= created_wall_ids
    assert material_targets <= created_wall_ids


def test_rooms_stage_reconciles_the_program_area_exactly(registry, program, layout, tmp_path):
    plans = _plans(registry, program, layout, tmp_path)
    stage = next(plan for plan in plans if plan.stage is BimStage.R08)

    assert len(stage.operations) == len(layout.rooms)
    assert {op.logical_id for op in stage.operations} == {
        room.logical_id for room in layout.rooms
    }
    assert stage.program_reconciliation["target_internal_useful_m2"] == pytest.approx(
        626.0, abs=1e-6
    )
    assert stage.program_reconciliation["status"] == "MATCH"
    assert stage.program_reconciliation["divergence"] is False
    assert stage.program_reconciliation["person_capacity"] == 20


def test_landscape_stage_places_the_whole_external_programme(registry, program, layout, tmp_path):
    plans = _plans(registry, program, layout, tmp_path)
    stage = next(plan for plan in plans if plan.stage is BimStage.R11)

    # A zone owns an outdoor element and an external floor, and the floor of a
    # zone that sits on the storey level is repeated per storey, so the
    # programme is counted once per zone rather than once per element.
    zones = {}
    for operation in stage.operations:
        properties = operation.payload["properties"]
        zones.setdefault(
            properties["zone_logical_id"], float(properties["target_area_m2"])
        )
    assert set(zones) == {
        "REQ-07-01",
        "REQ-07-02",
        "REQ-07-03",
        "REQ-07-04",
        "REQ-07-05",
    }
    assert sum(zones.values()) == pytest.approx(260.0, abs=1e-6)


def test_materials_stage_assigns_a_material_to_every_wall(registry, program, layout, tmp_path):
    plans = _plans(registry, program, layout, tmp_path)
    stage = next(plan for plan in plans if plan.stage is BimStage.R12)
    exterior, partitions = build_walls(layout)

    assigned = {op.logical_id for op in stage.operations}
    assert {wall.logical_id for wall in [*exterior, *partitions]} <= assigned


def test_documentation_stage_plans_views_schedules_and_sheets(registry, program, layout, tmp_path):
    plans = _plans(registry, program, layout, tmp_path)
    stage = next(plan for plan in plans if plan.stage is BimStage.R13)
    ids = {op.logical_id for op in stage.operations}

    assert any("VIEW" in value or "PLAN" in value for value in ids)
    assert any("SCHEDULE" in value or "TABLE" in value for value in ids)
    assert any("SHEET" in value for value in ids)


def test_plans_are_deterministic(registry, program, layout, tmp_path):
    first = _plans(registry, program, layout, tmp_path)
    second = _plans(registry, program, layout, tmp_path)

    for left, right in zip(first, second):
        assert left.stage is right.stage
        assert [op.logical_id for op in left.operations] == [
            op.logical_id for op in right.operations
        ]
        assert [op.payload for op in left.operations] == [
            op.payload for op in right.operations
        ]


def test_max_stage_shortens_the_chain_for_concept_work(registry, program, layout, tmp_path):
    plans = _plans(registry, program, layout, tmp_path, max_stage=BimStage.R04)
    assert [plan.stage for plan in plans] == [
        BimStage.R01,
        BimStage.R02,
        BimStage.R03,
        BimStage.R04,
    ]


def test_concept_only_cap_never_emits_detailed_stages(registry, program, layout, tmp_path):
    with pytest.raises(ProductionBimError):
        _plans(registry, program, layout, tmp_path, mode=ExecutionMode.CONCEPT_ONLY)


def test_no_plan_claims_a_final_validation(registry, program, layout, tmp_path):
    """A STUDY run must never present a blocked check as verified."""

    plans = _plans(registry, program, layout, tmp_path)
    for plan in plans:
        for note in plan.preflight.notes:
            assert "FINAL" not in note or "no FINAL claim" in note
