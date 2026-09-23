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
from shapely.geometry import LineString, Polygon

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import ExecutionMode, StagePreflightError
from amanda_agent.bim.stages.accessibility import (
    AccessibilityInput,
    AccessibleRoute,
    WidthCheck,
)
from amanda_agent.bim.stages.shell import execute_shell_stage
from amanda_agent.design.architectural_layout import build_courtyard_layout
from amanda_agent.design.models import (
    DesignStatus,
)
from amanda_agent.models.capability import (
    CapabilityRegistry,
    CapabilityStatus,
    EvidenceScope,
    ProviderCapability,
)
from amanda_agent.production import layout_bim
from amanda_agent.production.layout_bim import (
    ProductionBimError,
    _plan_r03,
    _plan_r04,
    _plan_r08,
    _request,
    _stamp,
    build_layout_stage_plans,
    build_walls,
    layout_stage_order,
)
from amanda_agent.production.selection import (
    build_canonical_selection,
    build_legacy_selection,
)

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
    # Explicit legacy fixture for historical linear-plan compiler coverage.
    return build_legacy_selection(
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


def test_rooms_stage_bridges_revit_room_insertion_point(
    registry, program, layout, tmp_path
):
    plans = _plans(registry, program, layout, tmp_path)
    stage = next(plan for plan in plans if plan.stage is BimStage.R08)

    operation = stage.operations[0]
    ring = operation.payload["geometry"]["coordinates"][0]
    centroid = Polygon(ring).centroid

    assert operation.payload["point"] == pytest.approx(
        [centroid.x, centroid.y]
    )


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


@pytest.fixture()
def canonical_test_solution(canonical_layout, canonical_profile):
    """Eligibility-shaped fixture for pure planner tests; never executable evidence."""

    selection = build_canonical_selection(
        canonical_layout,
        canonical_profile,
        generation_run="AMANDA-RUN-002-PAVILION",
        timestamp="2026-09-23T00:00:00Z",
    )
    # The actual candidate remains ineligible until migration evidence passes.
    # This status copy only allows the pure stage planner to be exercised; these
    # tests never call a stage executor or a Revit provider.
    return selection.solution.model_copy(
        update={"status": DesignStatus.AMANDA_REVIEW_PENDING}
    )


def _canonical_stage_request(stage, registry, solution):
    return _request(
        stage,
        registry=registry,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
        generation_run=solution.run_id,
        mode=ExecutionMode.DETAILED_BIM,
        solution=solution,
        expected_approval_hash=solution.approval_hash,
    )


def test_canonical_shell_plan_has_separate_admin_service_and_residential_footprints(
    registry, canonical_layout, canonical_test_solution
):
    planner = getattr(layout_bim, "plan_canonical_shell_stage", None)
    assert callable(planner), "canonical shell stage planner is missing"

    plan = planner(
        _canonical_stage_request(BimStage.R05, registry, canonical_test_solution),
        canonical_layout,
    )
    floor_ids = {
        operation.logical_id
        for operation in plan.operations
        if operation.semantic_capability == "revit.create_floor"
    }

    assert "FLOOR-ADMIN_ACOLHIMENTO-L1" in floor_ids
    assert "FLOOR-ADMIN_ACOLHIMENTO-L2" in floor_ids
    assert "FLOOR-SERVICE_CAPACITATION-L1" in floor_ids
    assert {
        "FLOOR-RES_PAV_A-L1",
        "FLOOR-RES_PAV_B-L1",
        "FLOOR-RES_PAV_C-L1",
        "FLOOR-RES_PAV_D_COMMUNAL-L1",
    } <= floor_ids


def test_canonical_room_operations_keep_admin_level_two_and_residential_ground_level(
    registry, canonical_program, canonical_layout, canonical_test_solution
):
    request = _canonical_stage_request(BimStage.R08, registry, canonical_test_solution)
    plan = _stamp(
        _plan_r08(request, canonical_program, canonical_layout),
        canonical_test_solution.solution_id,
        canonical_test_solution.approval_hash,
    )
    level_by_room = {
        operation.logical_id: operation.payload.get("level_id")
        for operation in plan.operations
    }
    admin_level_two = {
        room.logical_id
        for room in canonical_layout.block("ADMIN_ACOLHIMENTO").rooms
        if room.level == 2
    }
    residential_rooms = {
        room.logical_id
        for block in canonical_layout.residential_pavilions
        for room in block.rooms
    }

    assert admin_level_two
    assert {level_by_room[room_id] for room_id in admin_level_two} == {"LEVEL-02"}
    assert {level_by_room[room_id] for room_id in residential_rooms} == {"LEVEL-01"}


def test_canonical_shell_plan_does_not_create_a_linear_gallery(
    registry, canonical_layout, canonical_test_solution
):
    planner = getattr(layout_bim, "plan_canonical_shell_stage", None)
    assert callable(planner), "canonical shell stage planner is missing"

    plan = planner(
        _canonical_stage_request(BimStage.R05, registry, canonical_test_solution),
        canonical_layout,
    )
    operation_ids = {operation.logical_id for operation in plan.operations}
    floor_ids = {
        operation.logical_id
        for operation in plan.operations
        if operation.semantic_capability == "revit.create_floor"
    }

    assert not any(
        "GALLERY" in logical_id or "CORRIDOR" in logical_id
        for logical_id in operation_ids
    )
    assert "FLOOR-001" not in floor_ids
    assert len(floor_ids) == 8
    assert {
        "SLAB-COVERED-RES_PAV_A-TO-PROTECTED_PATIO",
        "SLAB-COVERED-RES_PAV_B-TO-PROTECTED_PATIO",
        "SLAB-COVERED-RES_PAV_C-TO-PROTECTED_PATIO",
        "SLAB-COVERED-RES_PAV_D_COMMUNAL-TO-PROTECTED_PATIO",
    } <= operation_ids
    assert not any(
        operation.semantic_capability == "revit.create_roof"
        for operation in plan.operations
    )


def test_canonical_r03_labels_local_levels_as_assumptions_and_blocks_writes(
    registry, canonical_layout, canonical_test_solution
):
    request = _canonical_stage_request(BimStage.R03, registry, canonical_test_solution)
    try:
        plan = _plan_r03(request, canonical_layout)
    except ProductionBimError as exc:
        pytest.fail(f"R03 must expose a blocked study plan for visual massing: {exc}")

    levels = {level.logical_id: level for level in plan.levels}
    assert set(levels) == {"LEVEL-01", "LEVEL-02"}
    assert levels["LEVEL-01"].elevation_m == 0.0
    assert levels["LEVEL-02"].elevation_m == layout_bim.FLOOR_HEIGHT_M
    assert all(level.source_kind == "DESIGN_ASSUMPTION" for level in levels.values())
    assert all(not level.is_provable for level in levels.values())
    assert all("BIM-00" in operation.blocked_by for operation in plan.operations)
    assert plan.preflight.get("bim_00").status.value == "BLOCKED"


def test_canonical_r04_plans_distinct_block_masses_as_non_executable_hypotheses(
    registry, canonical_layout, canonical_test_solution
):
    request = _canonical_stage_request(BimStage.R04, registry, canonical_test_solution)
    try:
        plan = _plan_r04(request, canonical_layout)
    except ProductionBimError as exc:
        pytest.fail(f"R04 must expose separate blocked study masses: {exc}")

    masses = {operation.logical_id: operation for operation in plan.operations}
    assert set(masses) == {f"MASS-{block.component_id}" for block in canonical_layout.blocks}
    assert masses["MASS-ADMIN_ACOLHIMENTO"].payload["height_m"] == pytest.approx(
        layout_bim.FLOOR_HEIGHT_M * 2
    )
    assert all(
        operation.payload["properties"]["height_basis"]
        == "PROVISIONAL_ASSUMPTION: 3.20m per floor for R04 visual study only"
        for operation in masses.values()
    )
    assert all("BIM-00" in operation.blocked_by for operation in masses.values())
    assert plan.preflight.get("bim_00").status.value == "BLOCKED"


def test_canonical_preacceptance_r04_accepts_provider_scope_mass_proof(
    registry, canonical_layout, canonical_profile
):
    preacceptance_solution = build_canonical_selection(
        canonical_layout,
        canonical_profile,
        generation_run="AMANDA-RUN-002-PAVILION",
        timestamp="2026-09-23T00:00:00Z",
    )
    preacceptance_solution = preacceptance_solution.solution
    provider_registry = registry.model_copy(
        update={
            "entries": [
                entry.model_copy(update={"evidence_scope": EvidenceScope.PROVIDER})
                if entry.operation == "mass"
                else entry
                for entry in registry.entries
            ]
        }
    )
    request = _request(
        BimStage.R04,
        registry=provider_registry,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
        generation_run=preacceptance_solution.run_id,
        mode=ExecutionMode.CANONICAL_PREACCEPTANCE,
        solution=preacceptance_solution,
        expected_approval_hash=preacceptance_solution.approval_hash,
    )

    plan = _plan_r04(request, canonical_layout)

    assert plan.preflight.get("capability_registry").status.value == "PASS"
    assert request.evidence_scope is EvidenceScope.PROVIDER


def test_planning_only_compiles_candidate_through_r13_without_removing_write_gates(
    registry, program, canonical_layout, canonical_profile, tmp_path
):
    selection = build_canonical_selection(
        canonical_layout,
        canonical_profile,
        generation_run="AMANDA-RUN-002-PAVILION",
        timestamp="2026-09-23T00:00:00Z",
    )
    candidate = selection.solution
    assert candidate.bim_eligible is False


def test_canonical_preacceptance_compiles_only_through_r04_for_unaccepted_solution(
    registry, program, canonical_layout, canonical_profile, tmp_path
):
    selection = build_canonical_selection(
        canonical_layout,
        canonical_profile,
        generation_run="AMANDA-RUN-002-PAVILION",
        timestamp="2026-09-23T00:00:00Z",
    )
    candidate = selection.solution

    plans = build_layout_stage_plans(
        program=program,
        layout=canonical_layout,
        registry=registry,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
        generation_run=candidate.run_id,
        solution_id=candidate.solution_id,
        approval_hash=candidate.approval_hash,
        solution=candidate,
        accessibility_input=None,
        template_root=tmp_path,
        mode=ExecutionMode.CANONICAL_PREACCEPTANCE,
        max_stage=BimStage.R04,
    )

    assert [plan.stage for plan in plans] == [
        BimStage.R01,
        BimStage.R02,
        BimStage.R03,
        BimStage.R04,
    ]
    assert candidate.bim_eligible is False
    assert all(plan.preflight.mode is ExecutionMode.CANONICAL_PREACCEPTANCE for plan in plans)
    assert all("BIM-00" in operation.blocked_by for operation in plans[3].operations)
    assert all(
        "CANONICAL_GEOMETRIC_ACCEPTANCE" in operation.blocked_by
        for operation in build_layout_stage_plans(
            program=program,
            layout=canonical_layout,
            registry=registry,
            revit_build=BUILD,
            tool_schema_hash=SCHEMA,
            generation_run=candidate.run_id,
            solution_id=candidate.solution_id,
            approval_hash=candidate.approval_hash,
            solution=candidate,
            accessibility_input=None,
            template_root=tmp_path,
            mode=ExecutionMode.PLANNING_ONLY,
            max_stage=BimStage.R05,
        )[4].operations
    )


def test_canonical_preacceptance_refuses_planning_beyond_r04(
    registry, program, canonical_layout, canonical_profile, tmp_path
):
    selection = build_canonical_selection(
        canonical_layout,
        canonical_profile,
        generation_run="AMANDA-RUN-002-PAVILION",
        timestamp="2026-09-23T00:00:00Z",
    )
    candidate = selection.solution

    with pytest.raises(ProductionBimError, match="through R04"):
        build_layout_stage_plans(
            program=program,
            layout=canonical_layout,
            registry=registry,
            revit_build=BUILD,
            tool_schema_hash=SCHEMA,
            generation_run=candidate.run_id,
            solution_id=candidate.solution_id,
            approval_hash=candidate.approval_hash,
            solution=candidate,
            accessibility_input=None,
            template_root=tmp_path,
            mode="CANONICAL_PREACCEPTANCE",
            max_stage=BimStage.R05,
        )

    plans = build_layout_stage_plans(
        program=program,
        layout=canonical_layout,
        registry=registry,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
        generation_run=candidate.run_id,
        solution_id=candidate.solution_id,
        approval_hash=candidate.approval_hash,
        solution=candidate,
        accessibility_input=None,
        template_root=tmp_path,
        mode="PLANNING_ONLY",
        max_stage=BimStage.R13,
    )

    assert [plan.stage.name for plan in plans] == [
        f"R{stage:02d}" for stage in range(1, 14)
    ]
    assert all(plan.preflight.mode.value == "PLANNING_ONLY" for plan in plans)
    all_operations = [operation for plan in plans for operation in plan.operations]
    assert all_operations
    assert all("PLANNING_ONLY" in operation.blocked_by for operation in all_operations)
    r04_masses = {
        operation.logical_id
        for operation in plans[3].operations
        if operation.semantic_capability == "revit.create_mass"
    }
    assert r04_masses == {
        f"MASS-{block.component_id}" for block in canonical_layout.blocks
    }
    assert all("BIM-00" in operation.blocked_by for operation in plans[3].operations)
    assert all(
        "CANONICAL_GEOMETRIC_ACCEPTANCE" in operation.blocked_by
        for operation in plans[4].operations
    )
    openings = plans[6]
    assert openings.operations == []
    assert openings.preflight.get("canonical_opening_hosts").status.value == "BLOCKED"
    assert "wall host geometry" in openings.preflight.get(
        "canonical_opening_hosts"
    ).detail
    accessibility = plans[8]
    assert accessibility.operations == []
    assert accessibility.numeric_status.value == "BLOCKED_BY_INPUT"
    assert accessibility.preflight.get("accessibility_inputs").status.value == "BLOCKED"
    assert candidate.bim_eligible is False


def test_planning_only_never_assigns_or_unblocks_operations_with_stale_capability_evidence(
    registry, program, canonical_layout, canonical_profile, tmp_path
):
    selection = build_canonical_selection(
        canonical_layout,
        canonical_profile,
        generation_run="AMANDA-RUN-002-PAVILION",
        timestamp="2026-09-23T00:00:00Z",
    )
    stale_registry = registry.model_copy(
        update={
            "entries": [
                entry.model_copy(
                    update={"evidence": ["missing-evidence.json::sha256=" + "0" * 64]}
                )
                for entry in registry.entries
            ]
        }
    )

    plans = build_layout_stage_plans(
        program=program,
        layout=canonical_layout,
        registry=stale_registry,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
        generation_run=selection.solution.run_id,
        solution_id=selection.solution.solution_id,
        approval_hash=selection.solution.approval_hash,
        solution=selection.solution,
        accessibility_input=None,
        template_root=tmp_path,
        mode=ExecutionMode.PLANNING_ONLY,
        max_stage=BimStage.R13,
    )

    operations = [operation for plan in plans for operation in plan.operations]
    assert operations
    assert all(operation.preferred_provider is None for operation in operations)
    assert all(operation.fallback_providers == [] for operation in operations)
    assert all("PLANNING_ONLY" in operation.blocked_by for operation in operations)
    assert all(
        "CAPABILITY_EVIDENCE_BLOCKED" in operation.blocked_by
        for operation in operations
    )
    r04_masses = {
        operation.logical_id
        for operation in plans[3].operations
        if operation.semantic_capability == "revit.create_mass"
    }
    assert r04_masses == {
        f"MASS-{block.component_id}" for block in canonical_layout.blocks
    }
    assert selection.solution.bim_eligible is False


def test_canonical_wall_planner_does_not_infer_partition_or_gallery_walls(
    canonical_layout,
):
    try:
        result = build_walls(canonical_layout)
    except AttributeError as exc:
        result = exc
    assert result == ([], []), "canonical wall hosts must wait for geometric acceptance"


def test_canonical_shell_translation_does_not_infer_wall_height(
    registry, canonical_layout, canonical_test_solution
):
    plan = layout_bim.plan_canonical_shell_stage(
        _canonical_stage_request(BimStage.R05, registry, canonical_test_solution),
        canonical_layout,
    )
    plan = _stamp(
        plan,
        canonical_test_solution.solution_id,
        canonical_test_solution.approval_hash,
    )
    walls = [
        operation
        for operation in plan.operations
        if operation.semantic_capability == "revit.create_wall"
    ]

    assert walls
    assert all("height" not in operation.payload for operation in walls)


def test_canonical_shell_executor_refuses_before_geometric_acceptance(
    registry, canonical_layout, canonical_test_solution
):
    planner = getattr(layout_bim, "plan_canonical_shell_stage", None)
    assert callable(planner), "canonical shell stage planner is missing"
    plan = planner(
        _canonical_stage_request(BimStage.R05, registry, canonical_test_solution),
        canonical_layout,
    )
    assert all(
        "CANONICAL_GEOMETRIC_ACCEPTANCE" in operation.blocked_by
        for operation in plan.operations
    )

    class UnexpectedInvoker:
        def invoke(self, call):
            pytest.fail("R05 executor dispatched before canonical geometric acceptance")

    with pytest.raises(StagePreflightError, match="canonical geometric acceptance"):
        execute_shell_stage(plan, invoker=UnexpectedInvoker())
