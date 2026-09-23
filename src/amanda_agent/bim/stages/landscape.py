"""R11 programmed landscape desired-state planning (P05-T19)."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..models import BimStage, DesiredElement, DesiredState
from ..provenance import BimProvenance
from ..verification import VerificationResult, verify_write
from . import (
    PreflightReport,
    PreflightRequest,
    StageExecutionRecord,
    StageOperation,
    StagePreflightError,
    StageToolInvoker,
    dispatch_operations,
    provider_assignment,
    run_preflight,
    stage_checkpoint_label,
    with_stage_requirements,
)

LANDSCAPE_CAPABILITY = "revit.create_landscape_element"
PROGRAMMED_EXTERNAL_AREA_M2 = 260.0
LANDSCAPE_DESIGN_OPTION = "DELEGATED_DESIGN"


class LandscapeSpace(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    target_area_m2: float = Field(gt=0)
    privacy: str = Field(min_length=1)
    adjacent_to: list[str] = Field(min_length=1)


DEFAULT_LANDSCAPE_PROGRAM: tuple[LandscapeSpace, ...] = (
    LandscapeSpace(
        logical_id="REQ-07-01",
        name="Patio interno protegido",
        target_area_m2=80.0,
        privacy="protected",
        adjacent_to=["residential"],
    ),
    LandscapeSpace(
        logical_id="REQ-07-02",
        name="Jardim terapeutico",
        target_area_m2=80.0,
        privacy="protected",
        adjacent_to=["technical", "residential"],
    ),
    LandscapeSpace(
        logical_id="REQ-07-03",
        name="Horta comunitaria",
        target_area_m2=30.0,
        privacy="semi-public",
        adjacent_to=["community"],
    ),
    LandscapeSpace(
        logical_id="REQ-07-04",
        name="Exercicios e alongamento",
        target_area_m2=30.0,
        privacy="semi-public",
        adjacent_to=["residential", "therapeutic"],
    ),
    LandscapeSpace(
        logical_id="REQ-07-05",
        name="Playground",
        target_area_m2=40.0,
        privacy="protected",
        adjacent_to=["child-area"],
    ),
)


class LandscapeStagePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R11
    preflight: PreflightReport
    programmed_area_m2: float = Field(ge=0)
    desired_state: DesiredState
    operations: list[StageOperation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    checkpoint_label: str = "R11_LANDSCAPE"

    @property
    def desired_elements(self) -> list[DesiredElement]:
        return self.desired_state.elements


def _as_space(value: LandscapeSpace | Mapping[str, Any]) -> LandscapeSpace:
    return (
        value
        if isinstance(value, LandscapeSpace)
        else LandscapeSpace.model_validate(value)
    )


def _as_desired(value: DesiredElement | Mapping[str, Any]) -> DesiredElement:
    return (
        value
        if isinstance(value, DesiredElement)
        else DesiredElement.model_validate(value)
    )


def _external_elements(
    external_elements: Sequence[DesiredElement | Mapping[str, Any]],
    external_planner: Callable[[], Sequence[DesiredElement | Mapping[str, Any]]] | None,
) -> list[DesiredElement]:
    values = list(external_elements)
    if external_planner is not None:
        values.extend(external_planner())
    return [_as_desired(value) for value in values]


def _element(
    *,
    logical_id: str,
    category: str,
    kind: str,
    space: LandscapeSpace,
    generation_run: str,
    geometry: Mapping[str, Any],
    approved_design_option: bool,
) -> DesiredElement:
    requirement_id = f"R11-{space.logical_id}"
    properties = {
        "landscape_kind": kind,
        "zone_logical_id": space.logical_id,
        "target_area_m2": space.target_area_m2,
        "privacy": space.privacy,
        "adjacent_to": list(space.adjacent_to),
        "approved_design_option": approved_design_option,
    }
    return DesiredElement(
        logical_id=logical_id,
        category=category,
        geometry=dict(geometry),
        properties=properties,
        requirement_id=requirement_id,
        design_option=LANDSCAPE_DESIGN_OPTION,
        generation_run=generation_run,
        provenance=BimProvenance(
            requirement_id=requirement_id,
            design_option=LANDSCAPE_DESIGN_OPTION,
            generation_run=generation_run,
            notes={"programmed_external_area_m2": space.target_area_m2},
        ),
    )


def plan_landscape_stage(
    request: PreflightRequest,
    *,
    spaces: Sequence[LandscapeSpace | Mapping[str, Any]] = DEFAULT_LANDSCAPE_PROGRAM,
    include_west_privacy_strategy: bool = False,
    approved_design_option: bool = False,
    external_elements: Sequence[DesiredElement | Mapping[str, Any]] = (),
    external_planner: Callable[[], Sequence[DesiredElement | Mapping[str, Any]]]
    | None = None,
) -> LandscapeStagePlan:
    """Keep all programmed external zones and their landscape QA layers."""

    normalized = [_as_space(space) for space in spaces]
    if include_west_privacy_strategy and not approved_design_option:
        raise ValueError(
            "west/privacy vegetation strategy requires an approved design option"
        )
    total = sum(space.target_area_m2 for space in normalized)
    if abs(total - PROGRAMMED_EXTERNAL_AREA_M2) > 1e-6:
        raise ValueError(
            f"programmed external landscape area must be {PROGRAMMED_EXTERNAL_AREA_M2:g} m2, got {total:g}"
        )
    effective = with_stage_requirements(request, extra=(LANDSCAPE_CAPABILITY,))
    report = run_preflight(effective)
    if not report.ok:
        raise StagePreflightError(
            "R11 preflight refused: " + "; ".join(report.problems)
        )
    owned: list[DesiredElement] = []
    for space in normalized:
        prefix = f"LAND-{space.logical_id}"
        owned.append(
            _element(
                logical_id=prefix,
                category="landscape_zone",
                kind="external_zone",
                space=space,
                generation_run=effective.generation_run,
                geometry={"target_area_m2": space.target_area_m2},
                approved_design_option=approved_design_option,
            )
        )
        owned.append(
            _element(
                logical_id=f"{prefix}-FLOOR",
                category="external_floor",
                kind="external_floor",
                space=space,
                generation_run=effective.generation_run,
                geometry={"host_zone": space.logical_id},
                approved_design_option=approved_design_option,
            )
        )
        vegetation = _element(
            logical_id=f"{prefix}-VEGETATION",
            category="vegetation",
            kind="vegetation",
            space=space,
            generation_run=effective.generation_run,
            geometry={"host_zone": space.logical_id},
            approved_design_option=approved_design_option,
        )
        if include_west_privacy_strategy:
            vegetation.properties["strategy"] = "west_privacy"
        owned.append(vegetation)
        owned.append(
            _element(
                logical_id=f"{prefix}-FURNITURE",
                category="outdoor_furniture",
                kind="outdoor_furniture",
                space=space,
                generation_run=effective.generation_run,
                geometry={"host_zone": space.logical_id},
                approved_design_option=approved_design_option,
            )
        )
        owned.append(
            _element(
                logical_id=f"{prefix}-SHADE",
                category="shading",
                kind="shading",
                space=space,
                generation_run=effective.generation_run,
                geometry={"host_zone": space.logical_id},
                approved_design_option=approved_design_option,
            )
        )
    desired_state = DesiredState(
        stage=BimStage.R11,
        generation_run=effective.generation_run,
        elements=[*owned, *_external_elements(external_elements, external_planner)],
    )
    preferred, fallbacks = provider_assignment(effective, LANDSCAPE_CAPABILITY)
    operations = [
        StageOperation(
            stage=BimStage.R11,
            logical_id=element.logical_id,
            semantic_capability=LANDSCAPE_CAPABILITY,
            payload=element.model_dump(mode="json"),
            verification_rules=[
                "independent_requery",
                "programmed_area_preserved",
                "privacy_and_adjacency_preserved",
            ],
            preferred_provider=preferred,
            fallback_providers=fallbacks,
        )
        for element in owned
    ]
    return LandscapeStagePlan(
        preflight=report,
        programmed_area_m2=total,
        desired_state=desired_state,
        operations=operations,
        notes=[
            "260 m2 is represented by five first-class external program zones; sublayers carry zero extra area"
        ],
        checkpoint_label=stage_checkpoint_label(BimStage.R11),
    )


def execute_landscape_stage(
    plan: LandscapeStagePlan, *, invoker: StageToolInvoker
) -> list[StageExecutionRecord]:
    return dispatch_operations(plan.operations, invoker=invoker)


def verify_landscape_stage(
    plan: LandscapeStagePlan,
    *,
    query_result: Mapping[str, Mapping[str, Any]],
    tool_reported_success: bool = True,
) -> list[VerificationResult]:
    results: list[VerificationResult] = []
    owned_ids = {operation.logical_id for operation in plan.operations}
    for element in plan.desired_state.elements:
        if element.logical_id not in owned_ids:
            continue
        results.extend(
            verify_write(
                logical_id=element.logical_id,
                tool_reported_success=tool_reported_success,
                query_result=query_result.get(element.logical_id),
                expected_geometry=element.geometry,
                expected_properties=element.properties,
            )
        )
    return results


__all__ = [
    "DEFAULT_LANDSCAPE_PROGRAM",
    "LANDSCAPE_CAPABILITY",
    "PROGRAMMED_EXTERNAL_AREA_M2",
    "LandscapeSpace",
    "LandscapeStagePlan",
    "execute_landscape_stage",
    "plan_landscape_stage",
    "verify_landscape_stage",
]
