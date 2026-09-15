"""R09 accessibility desired-state planning (P05-T17).

This module records measurable accessibility parameters and their evidence
status. It never turns an absent measurement into a normative compliance
claim. Revit is reached only through the injected stage invoker.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..models import BimStage, DesiredElement, DesiredState
from ..provenance import BimProvenance
from ..verification import VerificationResult, verify_write
from . import (
    CheckStatus,
    PreflightReport,
    PreflightRequest,
    StageCheck,
    StageExecutionRecord,
    StageOperation,
    StagePreflightError,
    StageToolInvoker,
    dispatch_operations,
    run_preflight,
    select_capability,
    stage_checkpoint_label,
    with_stage_requirements,
)

ACCESSIBILITY_CAPABILITY = "revit.create_accessibility_element"
ACCESSIBILITY_DESIGN_OPTION = "DELEGATED_DESIGN"


class AccessibilityStatus(StrEnum):
    """Evidence status for a parameter, deliberately separate from a pass."""

    VERIFIED = "VERIFIED"
    STATUS_NAO_VERIFICADO = "STATUS_NAO_VERIFICADO"
    BLOCKED_BY_INPUT = "BLOCKED_BY_INPUT"


class AccessibleRoute(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    from_node: str = Field(min_length=1)
    to_node: str = Field(min_length=1)
    measured_width_m: float | None = Field(default=None, gt=0)
    source_ref: str | None = None


class RampCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    measured_slope: float | None = Field(default=None, ge=0)
    landing_depth_m: float | None = Field(default=None, gt=0)
    source_ref: str | None = None


class WidthCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    location: str = Field(min_length=1)
    measured_width_m: float | None = Field(default=None, gt=0)
    source_ref: str | None = None


class ParkingCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    measured_width_m: float | None = Field(default=None, gt=0)
    side_access_m: float | None = Field(default=None, gt=0)
    source_ref: str | None = None


class SanitaryCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    turning_diameter_m: float | None = Field(default=None, gt=0)
    door_clearance_m: float | None = Field(default=None, gt=0)
    source_ref: str | None = None


class AccessibilityInput(BaseModel):
    """Measured or explicitly unmeasured inputs for the R09 checks."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    entrance_id: str = Field(min_length=1)
    required_space_ids: list[str] = Field(min_length=1)
    routes: list[AccessibleRoute] = Field(default_factory=list)
    ramps: list[RampCheck] = Field(default_factory=list)
    widths: list[WidthCheck] = Field(default_factory=list)
    parking: list[ParkingCheck] = Field(default_factory=list)
    sanitary: list[SanitaryCheck] = Field(default_factory=list)


class VerifiedNumericRule(BaseModel):
    """A numeric rule accepted only from a VERIFIED registry row."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    numeric_value: float
    unit: str = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)


def load_verified_numeric_rules(
    registry: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> dict[str, VerifiedNumericRule]:
    """Extract numeric rules only when status and provenance are explicit."""

    rows = registry.get("rules", []) if isinstance(registry, Mapping) else registry
    result: dict[str, VerifiedNumericRule] = {}
    for raw in rows:
        if raw.get("status") != "VERIFIED":
            continue
        if raw.get("numeric_value") is None or not raw.get("source_refs"):
            continue
        rule = VerifiedNumericRule(
            logical_id=raw.get("logical_id", ""),
            numeric_value=raw["numeric_value"],
            unit=raw.get("unit", "unspecified"),
            source_refs=list(raw["source_refs"]),
        )
        result[rule.logical_id] = rule
    return result


class RouteGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: set[str] = Field(default_factory=set)
    edges: list[tuple[str, str]] = Field(default_factory=list)


class AccessibilityCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    status: AccessibilityStatus
    measured_values: dict[str, float | None] = Field(default_factory=dict)
    source_ref: str | None = None
    note: str = Field(min_length=1)


class AccessibilityStagePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R09
    preflight: PreflightReport
    route_graph: RouteGraph
    checks: list[AccessibilityCheck] = Field(default_factory=list)
    numeric_status: AccessibilityStatus
    desired_state: DesiredState
    operations: list[StageOperation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    checkpoint_label: str = "R09_ACCESSIBILITY"

    @property
    def compliance_claim_allowed(self) -> bool:
        """Normative compliance is never emitted by this stage."""

        return False

    @property
    def desired_elements(self) -> list[DesiredElement]:
        return self.desired_state.elements


def _report_refusal(report: PreflightReport) -> str:
    problems = [
        f"{check.name}: {check.detail}"
        for check in report.checks
        if check.status is not CheckStatus.PASS
    ]
    return "; ".join(problems) or "unsupported accessibility evidence"


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


def _status(*values: float | None) -> AccessibilityStatus:
    return (
        AccessibilityStatus.VERIFIED
        if all(value is not None for value in values)
        else AccessibilityStatus.STATUS_NAO_VERIFICADO
    )


def _desired(
    *,
    logical_id: str,
    category: str,
    geometry: Mapping[str, Any],
    properties: Mapping[str, Any],
    requirement_id: str,
    generation_run: str,
    source_ref: str | None,
) -> DesiredElement:
    return DesiredElement(
        logical_id=logical_id,
        category=category,
        geometry=dict(geometry),
        properties=dict(properties),
        requirement_id=requirement_id,
        design_option=ACCESSIBILITY_DESIGN_OPTION,
        generation_run=generation_run,
        provenance=BimProvenance(
            requirement_id=requirement_id,
            design_option=ACCESSIBILITY_DESIGN_OPTION,
            generation_run=generation_run,
            source_refs=[source_ref] if source_ref else [],
            notes={"evidence_status": properties["status"]},
        ),
    )


def _operation(
    element: DesiredElement, provider: str, fallbacks: Sequence[str]
) -> StageOperation:
    return StageOperation(
        stage=BimStage.R09,
        logical_id=element.logical_id,
        semantic_capability=ACCESSIBILITY_CAPABILITY,
        payload=element.model_dump(mode="json"),
        verification_rules=[
            "independent_requery",
            "parameter_status_preserved",
            "no_compliance_claim",
        ],
        preferred_provider=provider,
        fallback_providers=list(fallbacks),
    )


def plan_accessibility_stage(
    request: PreflightRequest,
    *,
    inputs: AccessibilityInput,
    regulation_registry: Mapping[str, Any] | Sequence[Mapping[str, Any]] = (),
    external_elements: Sequence[DesiredElement | Mapping[str, Any]] = (),
    external_planner: Callable[[], Sequence[DesiredElement | Mapping[str, Any]]]
    | None = None,
) -> AccessibilityStagePlan:
    """Build the R09 desired-state and stop unsupported FINAL claims."""

    effective = with_stage_requirements(request, extra=(ACCESSIBILITY_CAPABILITY,))
    report = run_preflight(effective)
    rules = load_verified_numeric_rules(regulation_registry)
    numeric_check = StageCheck(
        name="normative_numeric_data",
        status=CheckStatus.PASS if rules else CheckStatus.BLOCKED,
        detail=(
            f"{len(rules)} numeric rules loaded from VERIFIED registry rows"
            if rules
            else "no VERIFIED numeric accessibility rule is available"
        ),
    )
    report = report.model_copy(update={"checks": [*report.checks, numeric_check]})
    if not report.ok:
        raise StagePreflightError("R09 preflight refused: " + _report_refusal(report))

    route_nodes = {inputs.entrance_id, *inputs.required_space_ids}
    edges: list[tuple[str, str]] = []
    checks: list[AccessibilityCheck] = []
    owned: list[DesiredElement] = []

    for route in inputs.routes:
        route_nodes.update((route.from_node, route.to_node))
        edges.append((route.from_node, route.to_node))
        status = _status(route.measured_width_m)
        checks.append(
            AccessibilityCheck(
                logical_id=route.logical_id,
                kind="accessible_route",
                status=status,
                measured_values={"width_m": route.measured_width_m},
                source_ref=route.source_ref,
                note="route width is measured input"
                if status is AccessibilityStatus.VERIFIED
                else "STATUS_NAO_VERIFICADO: route width not measured",
            )
        )
        owned.append(
            _desired(
                logical_id=route.logical_id,
                category="accessible_route",
                geometry={"from": route.from_node, "to": route.to_node},
                properties={
                    "from_node": route.from_node,
                    "to_node": route.to_node,
                    "measured_width_m": route.measured_width_m,
                    "status": status.value,
                },
                requirement_id="R09-ROUTE",
                generation_run=effective.generation_run,
                source_ref=route.source_ref,
            )
        )

    def add_check(
        *,
        logical_id: str,
        category: str,
        kind: str,
        values: dict[str, float | None],
        requirement_id: str,
        geometry: Mapping[str, Any] | None = None,
        source_ref: str | None,
    ) -> None:
        status = _status(*values.values())
        checks.append(
            AccessibilityCheck(
                logical_id=logical_id,
                kind=kind,
                status=status,
                measured_values=values,
                source_ref=source_ref,
                note="parameters are measured inputs"
                if status is AccessibilityStatus.VERIFIED
                else "STATUS_NAO_VERIFICADO: one or more parameters lack measurement",
            )
        )
        owned.append(
            _desired(
                logical_id=logical_id,
                category=category,
                geometry=geometry or {},
                properties={**values, "status": status.value},
                requirement_id=requirement_id,
                generation_run=effective.generation_run,
                source_ref=source_ref,
            )
        )

    for ramp in inputs.ramps:
        add_check(
            logical_id=ramp.logical_id,
            category="accessible_ramp",
            kind="ramp_and_landing",
            values={
                "slope": ramp.measured_slope,
                "landing_depth_m": ramp.landing_depth_m,
            },
            requirement_id="R09-RAMP",
            source_ref=ramp.source_ref,
        )
    for width in inputs.widths:
        add_check(
            logical_id=width.logical_id,
            category="accessible_circulation_width",
            kind="circulation_width",
            values={"width_m": width.measured_width_m},
            requirement_id="R09-WIDTH",
            geometry={"location": width.location},
            source_ref=width.source_ref,
        )
    for parking in inputs.parking:
        add_check(
            logical_id=parking.logical_id,
            category="accessible_parking",
            kind="parking_space",
            values={
                "width_m": parking.measured_width_m,
                "side_access_m": parking.side_access_m,
            },
            requirement_id="R09-PARKING",
            source_ref=parking.source_ref,
        )
    for sanitary in inputs.sanitary:
        add_check(
            logical_id=sanitary.logical_id,
            category="accessible_sanitary",
            kind="sanitary_space",
            values={
                "turning_diameter_m": sanitary.turning_diameter_m,
                "door_clearance_m": sanitary.door_clearance_m,
            },
            requirement_id="R09-SANITARY",
            source_ref=sanitary.source_ref,
        )

    all_values = [value for check in checks for value in check.measured_values.values()]
    measured = bool(checks) and all(value is not None for value in all_values)
    measured_check = StageCheck(
        name="measured_parameters",
        status=CheckStatus.PASS if measured else CheckStatus.BLOCKED,
        detail=(
            "all requested accessibility parameters have measurements"
            if measured
            else "one or more requested accessibility parameters lack measurement"
        ),
    )
    reachable = {inputs.entrance_id}
    changed = True
    while changed:
        changed = False
        for from_node, to_node in edges:
            if from_node in reachable and to_node not in reachable:
                reachable.add(to_node)
                changed = True
    missing_nodes = sorted(set(inputs.required_space_ids) - reachable)
    route_check = StageCheck(
        name="route_graph",
        status=CheckStatus.PASS if not missing_nodes else CheckStatus.BLOCKED,
        detail=(
            "entrance route reaches every required accessible space"
            if not missing_nodes
            else "required spaces are not connected from entrance: "
            + ", ".join(missing_nodes)
        ),
    )
    report = report.model_copy(
        update={"checks": [*report.checks, measured_check, route_check]}
    )
    if not report.ok:
        raise StagePreflightError("R09 preflight refused: " + _report_refusal(report))
    numeric_status = (
        AccessibilityStatus.VERIFIED
        if rules and measured and not missing_nodes
        else AccessibilityStatus.STATUS_NAO_VERIFICADO
    )
    note = (
        "STATUS_NAO_VERIFICADO: accessibility parameters are recorded without a normative compliance claim"
        if numeric_status is not AccessibilityStatus.VERIFIED
        else "measured parameters are recorded; normative compliance remains outside this stage"
    )
    desired = [*owned, *_external_elements(external_elements, external_planner)]
    desired_state = DesiredState(
        stage=BimStage.R09,
        generation_run=effective.generation_run,
        elements=desired,
    )
    preferred, fallbacks = select_capability(
        effective.registry,
        ACCESSIBILITY_CAPABILITY,
        revit_build=effective.revit_build,
        tool_schema_hash=effective.tool_schema_hash,
        scope=effective.evidence_scope,
    )
    operations = [
        _operation(element, preferred.provider, [entry.provider for entry in fallbacks])
        for element in owned
    ]
    return AccessibilityStagePlan(
        preflight=report,
        route_graph=RouteGraph(nodes=route_nodes, edges=edges),
        checks=checks,
        numeric_status=numeric_status,
        desired_state=desired_state,
        operations=operations,
        notes=[note],
        checkpoint_label=stage_checkpoint_label(BimStage.R09),
    )


def execute_accessibility_stage(
    plan: AccessibilityStagePlan,
    *,
    invoker: StageToolInvoker,
) -> list[StageExecutionRecord]:
    return dispatch_operations(plan.operations, invoker=invoker)


def verify_accessibility_stage(
    plan: AccessibilityStagePlan,
    *,
    tool_reported_success: bool,
    query_result: Mapping[str, Mapping[str, Any]],
) -> list[VerificationResult]:
    results: list[VerificationResult] = []
    for element in plan.desired_state.elements:
        if element.logical_id not in {
            operation.logical_id for operation in plan.operations
        }:
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
    "ACCESSIBILITY_CAPABILITY",
    "AccessibilityCheck",
    "AccessibilityInput",
    "AccessibilityStagePlan",
    "AccessibilityStatus",
    "AccessibleRoute",
    "ParkingCheck",
    "RampCheck",
    "RouteGraph",
    "SanitaryCheck",
    "VerifiedNumericRule",
    "WidthCheck",
    "execute_accessibility_stage",
    "load_verified_numeric_rules",
    "plan_accessibility_stage",
    "verify_accessibility_stage",
]
