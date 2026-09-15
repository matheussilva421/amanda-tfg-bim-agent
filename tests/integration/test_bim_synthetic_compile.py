"""Synthetic R01-R13 compile regression for the BIM stage contracts."""

from __future__ import annotations

import hashlib
from pathlib import Path

from shapely.geometry import box

from amanda_agent.bim.checkpoints import CheckpointManager
from amanda_agent.bim.current_state import CurrentElement, CurrentState
from amanda_agent.bim.diff import DiffAction, diff_states
from amanda_agent.bim.models import BimStage, DesiredElement, DesiredState
from amanda_agent.bim.stages import ExecutionMode, PreflightRequest
from amanda_agent.bim.stages.accessibility import (
    AccessibilityInput,
    AccessibleRoute,
    plan_accessibility_stage,
)
from amanda_agent.bim.stages.documentation import plan_documentation_stage
from amanda_agent.bim.stages.furniture import plan_furniture_stage
from amanda_agent.bim.stages.landscape import plan_landscape_stage
from amanda_agent.bim.stages.layout import plan_layout_stage
from amanda_agent.bim.stages.levels import (
    GridAxis,
    LevelReference,
    ReferenceMarker,
    plan_levels_stage,
)
from amanda_agent.bim.stages.massing import MassingBlock, plan_massing_stage
from amanda_agent.bim.stages.materials import (
    MaterialAssignment,
    MaterialCatalogEntry,
    plan_materials_stage,
)
from amanda_agent.bim.stages.openings import plan_openings_stage
from amanda_agent.bim.stages.project import plan_project_initialization
from amanda_agent.bim.stages.rooms import plan_rooms_stage
from amanda_agent.bim.stages.shell import plan_shell_stage
from amanda_agent.bim.stages.site import plan_site_stage
from amanda_agent.bim.verification import verify_write
from amanda_agent.models.capability import (
    CapabilityRegistry,
    EvidenceScope,
    ProviderCapability,
)
from amanda_agent.requirements.decisions import DecisionScenario
from amanda_agent.site.models import (
    BoundaryKind,
    BoundaryPolygon,
    SiteModel,
    SourceReference,
    SourceTopographyState,
    SurveyedElevationPoint,
    Topography,
    TopographyRepresentation,
)

SCHEMA = "synthetic-schema-1"
BUILD = "2027"
RUN = "synthetic-courtyard-run"
DOCUMENT = "synthetic-courtyard"

CAPABILITIES = (
    "revit.create_project",
    "revit.create_toposolid",
    "revit.create_level",
    "revit.create_grid",
    "revit.create_reference",
    "revit.create_mass",
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


class DeterministicInvoker:
    """Synthetic provider double: records calls and never opens Revit."""

    def __init__(self) -> None:
        self.calls = []

    def invoke(self, call):
        self.calls.append(call)
        return {
            "reported_success": True,
            "unique_id": f"uid:{call.stage.name}:{call.logical_id}",
        }


def _registry(root: Path) -> CapabilityRegistry:
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for operation in CAPABILITIES:
        evidence = root / (operation.replace(".", "-") + ".json")
        evidence.write_text(operation, encoding="utf-8")
        entries.append(
            ProviderCapability(
                provider="synthetic-provider",
                status="PASS",
                priority=1,
                provider_commit="synthetic-commit",
                transport_provider="fixture",
                tool_schema_hash=SCHEMA,
                tested_scope={"operation": operation, "writes": True},
                evidence_scope=EvidenceScope.SYNTHETIC,
                revit_build=BUILD,
                save_reopen=True,
                independent_query=True,
                evidence=[
                    f"{evidence}::sha256={hashlib.sha256(evidence.read_bytes()).hexdigest()}"
                ],
            )
        )
    return CapabilityRegistry(entries=entries)


def _request(
    root: Path, registry: CapabilityRegistry, stage: BimStage, **overrides
) -> PreflightRequest:
    values = {
        "mode": ExecutionMode.SYNTHETIC_LAB,
        "stage": stage,
        "scenario": DecisionScenario.STUDY,
        "registry": registry,
        "revit_build": BUILD,
        "tool_schema_hash": SCHEMA,
        "expected_build": BUILD,
        "expected_tool_schema_hash": SCHEMA,
        "fixture": True,
        "evidence_scope": EvidenceScope.SYNTHETIC,
        "generation_run": RUN,
    }
    values.update(overrides)
    return PreflightRequest(**values)


def _site() -> SiteModel:
    boundary = BoundaryPolygon(
        coordinates=[(0.0, 0.0), (8.0, 0.0), (8.0, 4.0), (0.0, 4.0), (0.0, 0.0)],
        kind=BoundaryKind.STUDY_PLACEHOLDER,
        placeholder_area_m2=32.0,
    )
    source = SourceReference(
        source_id="SYNTHETIC-TOPO",
        locator="fixture:topography",
        sha256="a" * 64,
    )
    points = [
        (0.0, 0.0, 0.0),
        (8.0, 0.0, 0.2),
        (8.0, 4.0, 0.4),
        (0.0, 4.0, 0.1),
    ]
    return SiteModel(
        boundary=boundary,
        topography=Topography(
            source_state=SourceTopographyState.VERIFIED_TOPOGRAPHY,
            representation=TopographyRepresentation.VERIFIED_TOPOGRAPHY,
            elevation_points=[
                SurveyedElevationPoint(coordinate=point, source_ref=source)
                for point in points
            ],
            provenance=[source],
        ),
    )


def _program() -> dict:
    return {
        "baseline": {"person_capacity": 20},
        "sectors": [
            {
                "logical_id": "SEC-COURTYARD",
                "name": "Pátio sintético",
                "spaces": [
                    {
                        "logical_id": "ROOM-A",
                        "name": "Quarto",
                        "quantity": 1,
                        "target_area_m2": 16.0,
                        "area_kind": "INTERNAL",
                        "privacy": 4,
                        "accessible": True,
                        "source_page": 1,
                    },
                    {
                        "logical_id": "ROOM-B",
                        "name": "Refeitório",
                        "quantity": 1,
                        "target_area_m2": 16.0,
                        "area_kind": "INTERNAL",
                        "privacy": 2,
                        "accessible": True,
                        "source_page": 1,
                    },
                ],
            }
        ],
    }


def _plans(root: Path):
    registry = _registry(root)
    template = root / "synthetic-template.rte"
    template.write_bytes(b"synthetic architectural template")
    site = _site()
    rooms = [
        {"logical_id": "ROOM-A", "geometry": box(0, 0, 4, 4)},
        {"logical_id": "ROOM-B", "geometry": box(4, 0, 8, 4)},
    ]
    shell = box(0, 0, 8, 4)
    plans = [
        plan_project_initialization(
            _request(root, registry, BimStage.R01),
            amanda_template=template,
            amanda_template_tested=True,
            project_code="SYNTHETIC",
        ),
        plan_site_stage(
            _request(root, registry, BimStage.R02, site=site),
            toposolid_planner=lambda footprint, *, elevation, name: DesiredElement(
                logical_id=name,
                category="Toposolid",
                geometry={"footprint": footprint, "elevation_m": elevation},
                properties={"name": name},
                requirement_id="SYNTHETIC-TOPO",
                design_option="SYNTHETIC",
                generation_run=RUN,
            ),
        ),
        plan_levels_stage(
            _request(root, registry, BimStage.R03),
            levels=[
                LevelReference(
                    logical_id="LEVEL-01",
                    name="Térreo",
                    elevation_m=0.0,
                    evidence=["synthetic:level"],
                )
            ],
            grids=[
                GridAxis(
                    logical_id="GRID-A",
                    name="A",
                    start=(0.0, 0.0),
                    end=(8.0, 0.0),
                    assumption="PROVISIONAL_ASSUMPTION",
                )
            ],
            references=[
                ReferenceMarker(
                    logical_id="REF-ORIGIN",
                    name="Project Origin",
                    kind="PROJECT_ORIGIN",
                    coordinate=(0.0, 0.0, 0.0),
                )
            ],
        ),
        plan_massing_stage(
            _request(root, registry, BimStage.R04),
            blocks=[
                MassingBlock(
                    logical_id="MASS-01",
                    name="Courtyard block",
                    footprint=[(0.0, 0.0), (8.0, 0.0), (8.0, 4.0), (0.0, 4.0)],
                    height_m=3.2,
                )
            ],
        ),
        plan_shell_stage(
            _request(root, registry, BimStage.R05),
            rooms=rooms,
            gross_shell=shell,
            floor_loops=[shell],
            slab_loops=[shell],
            roof={"geometry": shell, "type": "synthetic-roof"},
        ),
    ]
    wall = next(
        element for element in plans[-1].desired_state.elements if element.category == "WALL"
    )
    plans.extend(
        [
            plan_layout_stage(
                _request(root, registry, BimStage.R06),
                rooms=rooms,
            ),
            plan_openings_stage(
                _request(root, registry, BimStage.R07),
                openings=[
                    {
                        "logical_id": "DOOR-01",
                        "kind": "DOOR",
                        "host_logical_id": wall.logical_id,
                        "family_type": "DOOR_INT_01",
                        "position": (1.0, 0.0),
                        "width_m": 0.9,
                        "height_m": 2.1,
                        "connects": ["ROOM-A", "ROOM-B"],
                    }
                ],
                hosts=[
                    {
                        "logical_id": wall.logical_id,
                        "category": "WALL",
                        "geometry": wall.geometry,
                    }
                ],
                family_catalog={
                    "DOOR_INT_01": {
                        "kind": "DOOR",
                        "family": "Door-Interior",
                        "type": "Single-090",
                    }
                },
            ),
            plan_rooms_stage(
                _request(root, registry, BimStage.R08),
                program=_program(),
                room_geometries={"ROOM-A": box(0, 0, 4, 4), "ROOM-B": box(4, 0, 8, 4)},
            ),
            plan_accessibility_stage(
                _request(root, registry, BimStage.R09),
                inputs=AccessibilityInput(
                    entrance_id="ROOM-A",
                    required_space_ids=["ROOM-A", "ROOM-B"],
                    routes=[
                        AccessibleRoute(
                            logical_id="ROUTE-A-B",
                            from_node="ROOM-A",
                            to_node="ROOM-B",
                        )
                    ],
                ),
            ),
            plan_furniture_stage(_request(root, registry, BimStage.R10), program=_program()),
            plan_landscape_stage(_request(root, registry, BimStage.R11)),
            plan_materials_stage(
                _request(root, registry, BimStage.R12),
                assignments=[
                    MaterialAssignment(
                        element_logical_id=wall.logical_id,
                        material_name="MAT-WALL",
                        material_type="paint",
                        requirement_id="SYNTHETIC-MATERIAL",
                        design_intent="washable courtyard interior",
                    )
                ],
                catalog=[
                    MaterialCatalogEntry(
                        material_name="MAT-WALL",
                        material_type="paint",
                        source_ref="synthetic:material",
                        justification="fixture material",
                    )
                ],
            ),
            plan_documentation_stage(_request(root, registry, BimStage.R13)),
        ]
    )
    return plans


def _execute_and_verify(plans, invoker: DeterministicInvoker):
    all_verifications = []
    for plan in plans:
        # Stage dispatchers are called through their public module functions in
        # the test below; this helper performs only generic write verification.
        if hasattr(plan, "desired_state"):
            elements = plan.desired_state.by_logical_id()
            for operation in plan.operations:
                element = elements[operation.logical_id]
                all_verifications.extend(
                    verify_write(
                        logical_id=element.logical_id,
                        tool_reported_success=True,
                        query_result={
                            "unique_id": f"uid:{plan.stage.name}:{element.logical_id}",
                            "geometry": element.geometry,
                            "properties": element.properties,
                        },
                        expected_geometry=element.geometry,
                        expected_properties=element.properties,
                    )
                )
    return all_verifications


def test_synthetic_pipeline_runs_r01_to_r13_in_order_and_is_idempotent(tmp_path: Path):
    first_plans = _plans(tmp_path / "first")
    second_plans = _plans(tmp_path / "second")

    assert [plan.stage for plan in first_plans] == list(BimStage)[1:14]
    assert [
        plan.desired_state.model_dump(mode="json")
        for plan in first_plans
        if hasattr(plan, "desired_state")
    ] == [
        plan.desired_state.model_dump(mode="json")
        for plan in second_plans
        if hasattr(plan, "desired_state")
    ]

    first_invoker = DeterministicInvoker()
    second_invoker = DeterministicInvoker()
    assert len(first_plans) == 13

    from amanda_agent.bim.stages.accessibility import execute_accessibility_stage
    from amanda_agent.bim.stages.documentation import execute_documentation_stage
    from amanda_agent.bim.stages.furniture import execute_furniture_stage
    from amanda_agent.bim.stages.landscape import execute_landscape_stage
    from amanda_agent.bim.stages.layout import execute_layout_stage
    from amanda_agent.bim.stages.levels import execute_levels_stage
    from amanda_agent.bim.stages.massing import execute_massing_stage
    from amanda_agent.bim.stages.materials import execute_materials_stage
    from amanda_agent.bim.stages.openings import execute_openings_stage
    from amanda_agent.bim.stages.project import execute_project_initialization
    from amanda_agent.bim.stages.rooms import execute_rooms_stage
    from amanda_agent.bim.stages.shell import execute_shell_stage
    from amanda_agent.bim.stages.site import execute_site_stage

    execute_by_stage = {
        BimStage.R01: execute_project_initialization,
        BimStage.R02: execute_site_stage,
        BimStage.R03: execute_levels_stage,
        BimStage.R04: execute_massing_stage,
        BimStage.R05: execute_shell_stage,
        BimStage.R06: execute_layout_stage,
        BimStage.R07: execute_openings_stage,
        BimStage.R08: execute_rooms_stage,
        BimStage.R09: execute_accessibility_stage,
        BimStage.R10: execute_furniture_stage,
        BimStage.R11: execute_landscape_stage,
        BimStage.R12: execute_materials_stage,
        BimStage.R13: execute_documentation_stage,
    }
    first_records = []
    second_records = []
    for first, second in zip(first_plans, second_plans):
        first_records.extend(execute_by_stage[first.stage](first, invoker=first_invoker))
        second_records.extend(execute_by_stage[second.stage](second, invoker=second_invoker))

    assert [record.stage for record in first_records] == sorted(
        (record.stage for record in first_records), key=lambda stage: list(BimStage).index(stage)
    )
    assert [
        (record.stage, record.logical_id, record.semantic_capability, record.provider)
        for record in first_records
    ] == [
        (record.stage, record.logical_id, record.semantic_capability, record.provider)
        for record in second_records
    ]
    verification = _execute_and_verify(first_plans, first_invoker)
    assert verification and all(result.passed for result in verification)

    manager = CheckpointManager()
    source = tmp_path / "model.rvt"
    source.write_bytes(b"synthetic model baseline")
    manifests = []
    for index, plan in enumerate(first_plans, start=1):
        manifest = manager.create_checkpoint(
            source,
            tmp_path / f"stage-{index:02d}.rvt",
            stage=plan.checkpoint_label,
            document_id=DOCUMENT,
            reopen_verify=True,
        )
        manifests.append(manifest)
    assert len(manifests) == 13
    assert all(manifest.verify() for manifest in manifests)
    assert [manifest.stage for manifest in manifests] == [
        plan.checkpoint_label for plan in first_plans
    ]

    final_elements = {}
    for plan in first_plans:
        if hasattr(plan, "desired_state"):
            final_elements.update(
                {element.logical_id: element for element in plan.desired_state.elements}
            )
    elements = list(final_elements.values())
    desired = DesiredState(stage=BimStage.R13, generation_run=RUN, elements=elements)
    current = CurrentState(
        document_id=DOCUMENT,
        elements=[
            CurrentElement(
                logical_id=element.logical_id,
                category=element.category,
                geometry=element.geometry,
                properties=element.properties,
                unique_id=f"uid-current-{index:04d}",
                document_id=DOCUMENT,
            )
            for index, element in enumerate(elements, start=1)
        ],
    )
    diff = diff_states(desired, current, expected_document_id=DOCUMENT)
    assert diff.operations
    assert all(operation.action is DiffAction.NOOP for operation in diff.operations)
    assert len(invoker_write_ids := first_invoker.calls) > 0
    assert all(call.provider == "synthetic-provider" for call in invoker_write_ids)
