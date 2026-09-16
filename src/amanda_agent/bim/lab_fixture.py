"""Deterministic synthetic courtyard plans for the BIM compiler lab."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from shapely.geometry import box  # type: ignore[import-untyped]

from amanda_agent.models.capability import (
    CapabilityRegistry,
    CapabilityStatus,
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

from .models import BimStage, DesiredElement
from .stages import ExecutionMode, PreflightRequest
from .stages.accessibility import (
    AccessibilityInput,
    AccessibleRoute,
    plan_accessibility_stage,
)
from .stages.documentation import plan_documentation_stage
from .stages.furniture import plan_furniture_stage
from .stages.landscape import plan_landscape_stage
from .stages.layout import plan_layout_stage
from .stages.levels import GridAxis, LevelReference, ReferenceMarker, plan_levels_stage
from .stages.massing import MassingBlock, plan_massing_stage
from .stages.materials import (
    MaterialAssignment,
    MaterialCatalogEntry,
    plan_materials_stage,
)
from .stages.openings import plan_openings_stage
from .stages.project import plan_project_initialization
from .stages.rooms import plan_rooms_stage
from .stages.shell import plan_shell_stage
from .stages.site import plan_site_stage

SCHEMA = "synthetic-schema-1"
BUILD = "2027"
RUN = "synthetic-courtyard-run"

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


def build_lab_fixture_registry(
    *, root: Path, revit_build: str = BUILD, tool_schema_hash: str = SCHEMA
) -> CapabilityRegistry:
    """Create the synthetic provider registry and its local evidence files."""

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for operation in CAPABILITIES:
        evidence = root / (operation.replace(".", "-") + ".json")
        evidence.write_text(operation, encoding="utf-8")
        entries.append(
            ProviderCapability(
                provider="synthetic-provider",
                status=CapabilityStatus.PASS,
                priority=1,
                provider_commit="synthetic-commit",
                transport_provider="fixture",
                tool_schema_hash=tool_schema_hash,
                tested_scope={"operation": operation, "writes": True},
                evidence_scope=EvidenceScope.SYNTHETIC,
                revit_build=revit_build,
                save_reopen=True,
                independent_query=True,
                evidence=[
                    f"{evidence}::sha256={hashlib.sha256(evidence.read_bytes()).hexdigest()}"
                ],
            )
        )
    return CapabilityRegistry(entries=entries)


def _request(
    registry: CapabilityRegistry,
    stage: BimStage,
    *,
    revit_build: str,
    tool_schema_hash: str,
    **overrides: Any,
) -> PreflightRequest:
    values: dict[str, Any] = {
        "mode": ExecutionMode.SYNTHETIC_LAB,
        "stage": stage,
        "scenario": DecisionScenario.STUDY,
        "registry": registry,
        "revit_build": revit_build,
        "tool_schema_hash": tool_schema_hash,
        "expected_build": revit_build,
        "expected_tool_schema_hash": tool_schema_hash,
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


def _program() -> dict[str, Any]:
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


def build_lab_fixture_plans(
    *,
    root: Path,
    registry: CapabilityRegistry,
    revit_build: str = BUILD,
    tool_schema_hash: str = SCHEMA,
) -> list[Any]:
    """Build the deterministic synthetic R01-R13 plan chain."""

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    template = root / "synthetic-template.rte"
    template.write_bytes(b"synthetic architectural template")
    site = _site()
    rooms = [
        {"logical_id": "ROOM-A", "geometry": box(0, 0, 4, 4)},
        {"logical_id": "ROOM-B", "geometry": box(4, 0, 8, 4)},
    ]
    shell = box(0, 0, 8, 4)
    request = lambda stage, **overrides: _request(
        registry,
        stage,
        revit_build=revit_build,
        tool_schema_hash=tool_schema_hash,
        **overrides,
    )
    plans: list[Any] = [
        plan_project_initialization(
            request(BimStage.R01),
            amanda_template=template,
            amanda_template_tested=True,
            project_code="SYNTHETIC",
        ),
        plan_site_stage(
            request(BimStage.R02, site=site),
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
            request(BimStage.R03),
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
            request(BimStage.R04),
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
            request(BimStage.R05),
            rooms=rooms,
            gross_shell=shell,
            floor_loops=[shell],
            slab_loops=[shell],
            roof={"geometry": shell, "type": "synthetic-roof"},
        ),
    ]
    wall = next(
        element
        for element in plans[-1].desired_state.elements
        if element.category == "WALL"
    )
    plans.extend(
        [
            plan_layout_stage(request(BimStage.R06), rooms=rooms),
            plan_openings_stage(
                request(BimStage.R07),
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
                request(BimStage.R08),
                program=_program(),
                room_geometries={
                    "ROOM-A": box(0, 0, 4, 4),
                    "ROOM-B": box(4, 0, 8, 4),
                },
            ),
            plan_accessibility_stage(
                request(BimStage.R09),
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
            plan_furniture_stage(request(BimStage.R10), program=_program()),
            plan_landscape_stage(request(BimStage.R11)),
            plan_materials_stage(
                request(BimStage.R12),
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
            plan_documentation_stage(request(BimStage.R13)),
        ]
    )
    return plans


__all__ = [
    "BUILD",
    "CAPABILITIES",
    "RUN",
    "SCHEMA",
    "build_lab_fixture_plans",
    "build_lab_fixture_registry",
]
