"""Pure desired-state planning for hosted R07 doors and windows."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..models import BimStage, DesiredElement, DesiredState
from ..verification import VerificationResult, verify_write
from . import (
    PreflightReport,
    PreflightRequest,
    StageError,
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

OPENING_CAPABILITY = "revit.create_opening"
DEFAULT_ACCESSIBILITY_MIN_CLEAR_WIDTH_M = 0.80


class OpeningCatalogError(StageError):
    """The requested family/type is absent or incompatible with the catalog."""


class OpeningStagePlan(BaseModel):
    """R07 hosted opening desired state and its validated intent."""

    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R07
    preflight: PreflightReport
    desired_state: DesiredState
    operations: list[StageOperation] = Field(default_factory=list)
    validation_policy: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    checkpoint_label: str = Field(default="R07_OPENINGS", min_length=1)

    @property
    def desired_elements(self) -> list[DesiredElement]:
        return self.desired_state.elements


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def _identifier(item: Any, default: str = "") -> str:
    return str(_value(item, "logical_id", _value(item, "id", default)))


def _finite_positive(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise StageError(f"opening {label} must be a finite positive number") from exc
    if not math.isfinite(number) or number <= 0:
        raise StageError(f"opening {label} must be a finite positive number")
    return number


def _finite_nonnegative(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise StageError(
            f"opening {label} must be a finite non-negative number"
        ) from exc
    if not math.isfinite(number) or number < 0:
        raise StageError(f"opening {label} must be a finite non-negative number")
    return number


def _position(item: Any) -> tuple[float, float]:
    raw = _value(item, "position")
    if raw is None:
        raw = (_value(item, "x"), _value(item, "y"))
    if isinstance(raw, Mapping):
        raw = (raw.get("x"), raw.get("y"))
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) != 2:
        raise StageError("opening position requires x and y")
    try:
        x, y = float(raw[0]), float(raw[1])
    except (TypeError, ValueError) as exc:
        raise StageError("opening position requires numeric x and y") from exc
    if not math.isfinite(x) or not math.isfinite(y):
        raise StageError("opening position requires finite x and y")
    return x, y


def _host_map(hosts: Any) -> dict[str, Any]:
    if isinstance(hosts, Mapping):
        return {str(key): value for key, value in hosts.items()}
    result: dict[str, Any] = {}
    for host in hosts or ():
        identifier = _identifier(host)
        if identifier:
            result[identifier] = host
    return result


def _host_category(host: Any) -> str:
    return str(_value(host, "category", _value(host, "element_category", ""))).upper()


def _catalog_map(catalog: Any) -> dict[str, Mapping[str, Any]]:
    if catalog is None:
        return {}
    if isinstance(catalog, Mapping):
        result: dict[str, Mapping[str, Any]] = {}
        for key, value in catalog.items():
            if isinstance(value, Mapping):
                result[str(key)] = value
        return result
    result = {}
    for item in catalog:
        if not isinstance(item, Mapping):
            continue
        key = item.get("family_type", item.get("type_id", item.get("id")))
        if key is not None:
            result[str(key)] = item
    return result


def _catalog_entry(
    catalog: dict[str, Mapping[str, Any]], family_type: str, kind: str
) -> Mapping[str, Any]:
    entry = catalog.get(family_type)
    if entry is None:
        entry = catalog.get(f"{kind}:{family_type}")
    if entry is None:
        raise OpeningCatalogError(
            f"opening family/type {family_type!r} is absent from the controlled catalog"
        )
    catalog_kind = str(entry.get("kind", entry.get("category", kind))).upper()
    if catalog_kind != kind:
        raise OpeningCatalogError(
            f"catalog family/type {family_type!r} is catalogued as {catalog_kind}, expected {kind}"
        )
    return entry


def _operation(element: DesiredElement, request: PreflightRequest) -> StageOperation:
    preferred, fallbacks = provider_assignment(request, OPENING_CAPABILITY)
    return StageOperation(
        stage=BimStage.R07,
        logical_id=element.logical_id,
        semantic_capability=OPENING_CAPABILITY,
        payload=element.model_dump(mode="json"),
        verification_rules=[
            "independent_requery",
            "unique_id_present",
            "host_exists",
            "dimensions_match",
            "connectivity_and_collision_checked",
        ],
        preferred_provider=preferred,
        fallback_providers=fallbacks,
    )


def _preflight(request: PreflightRequest) -> tuple[PreflightRequest, PreflightReport]:
    effective = with_stage_requirements(request, extra=(OPENING_CAPABILITY,))
    if effective.stage is not BimStage.R07:
        raise StagePreflightError(
            f"R07 preflight refused: stage_identity: expected R07, got {effective.stage.name}"
        )
    report = run_preflight(effective)
    if not report.ok:
        raise StagePreflightError(
            "R07 preflight refused: " + "; ".join(report.problems)
        )
    return effective, report


def plan_openings_stage(
    request: PreflightRequest,
    openings: Sequence[Any],
    *,
    hosts: Any,
    family_catalog: Any,
    accessibility_min_clear_width_m: float = DEFAULT_ACCESSIBILITY_MIN_CLEAR_WIDTH_M,
    minimum_window_sill_m: float = 0.0,
    maximum_window_sill_m: float | None = None,
    design_option: str | None = None,
) -> OpeningStagePlan:
    """Validate and describe each hosted door/window without touching Revit."""

    effective, report = _preflight(request)
    if accessibility_min_clear_width_m <= 0:
        raise StageError("accessibility minimum clear width must be positive")
    if minimum_window_sill_m < 0:
        raise StageError("minimum window sill must be non-negative")
    if (
        maximum_window_sill_m is not None
        and maximum_window_sill_m < minimum_window_sill_m
    ):
        raise StageError("maximum window sill must be >= minimum window sill")
    host_by_id = _host_map(hosts)
    catalog = _catalog_map(family_catalog)
    if not host_by_id:
        raise StageError("R07 openings require hosted wall elements")
    if not catalog:
        raise OpeningCatalogError(
            "R07 openings require a controlled family/type catalog"
        )

    selected_option = design_option or (
        effective.solution.solution_id
        if effective.solution is not None
        else "SELECTED_DESIGN"
    )
    elements: list[DesiredElement] = []
    seen_ids: set[str] = set()
    seen_positions: set[tuple[str, float, float]] = set()
    for index, opening in enumerate(openings, start=1):
        logical_id = _identifier(opening, f"OPENING-{index:03d}")
        if not logical_id:
            raise StageError("openings require logical_id")
        if logical_id in seen_ids:
            raise StageError(f"duplicate opening logical_id: {logical_id}")
        seen_ids.add(logical_id)
        kind = str(_value(opening, "kind", _value(opening, "category", ""))).upper()
        if kind not in {"DOOR", "WINDOW"}:
            raise StageError(f"opening {logical_id} kind must be DOOR or WINDOW")
        host_id = str(
            _value(opening, "host_logical_id", _value(opening, "host_id", ""))
        )
        if host_id not in host_by_id:
            raise StageError(f"opening {logical_id} host {host_id!r} is missing")
        if _host_category(host_by_id[host_id]) != "WALL":
            raise StageError(f"opening {logical_id} host {host_id!r} is not a WALL")
        family_type = str(
            _value(opening, "family_type", _value(opening, "type_id", ""))
        )
        if not family_type:
            raise OpeningCatalogError(
                f"opening {logical_id} does not select a catalog family/type"
            )
        catalog_entry = _catalog_entry(catalog, family_type, kind)
        position = _position(opening)
        position_key = (host_id, round(position[0], 6), round(position[1], 6))
        if position_key in seen_positions:
            raise StageError(
                f"opening collision: duplicate host/position for {logical_id}"
            )
        seen_positions.add(position_key)
        width = _finite_positive(
            _value(opening, "clear_width_m", _value(opening, "width_m")), "width_m"
        )
        height = _finite_positive(_value(opening, "height_m"), "height_m")
        if kind == "DOOR" and width < accessibility_min_clear_width_m:
            raise StageError(
                f"opening {logical_id} clear width {width:g} m is below the accessibility minimum {accessibility_min_clear_width_m:g} m"
            )
        raw_sill = _value(opening, "sill_m")
        if kind == "WINDOW" and raw_sill is None:
            raise StageError(f"opening {logical_id} window requires an explicit sill_m")
        sill = _finite_nonnegative(raw_sill if raw_sill is not None else 0.0, "sill_m")
        if kind == "WINDOW":
            if sill < minimum_window_sill_m:
                raise StageError(
                    f"opening {logical_id} sill is below the configured minimum"
                )
            if maximum_window_sill_m is not None and sill > maximum_window_sill_m:
                raise StageError(
                    f"opening {logical_id} sill exceeds the configured maximum"
                )
        connectivity = _value(opening, "connects", _value(opening, "connectivity"))
        if kind == "DOOR":
            if (
                not isinstance(connectivity, Sequence)
                or isinstance(connectivity, (str, bytes))
                or len(connectivity) != 2
            ):
                raise StageError(
                    f"opening {logical_id} door requires two intended connectivity room IDs"
                )
            connectivity = [str(item) for item in connectivity]

        geometry = {
            "type": "Point",
            "coordinates": [position[0], position[1]],
        }
        properties = {
            "kind": kind,
            "family_type": family_type,
            "family": str(catalog_entry.get("family", family_type)),
            "type": str(catalog_entry.get("type", family_type)),
            "host_logical_id": host_id,
            "width_m": width,
            "clear_width_m": width,
            "height_m": height,
            "sill_m": sill,
            "connectivity": connectivity,
            "collision_checked": True,
            "host_checked": True,
        }
        element = DesiredElement(
            logical_id=logical_id,
            category=kind,
            geometry=geometry,
            properties=properties,
            requirement_id=str(_value(opening, "requirement_id", "R07-OPENINGS")),
            design_option=selected_option,
            generation_run=effective.generation_run,
        )
        elements.append(element)

    desired_state = DesiredState(
        stage=BimStage.R07,
        generation_run=effective.generation_run,
        model_id=effective.solution.solution_id
        if effective.solution is not None
        else "STUDY",
        elements=elements,
    )
    return OpeningStagePlan(
        preflight=report,
        desired_state=desired_state,
        operations=[_operation(element, effective) for element in elements],
        validation_policy={
            "accessibility_min_clear_width_m": float(accessibility_min_clear_width_m),
            "minimum_window_sill_m": float(minimum_window_sill_m),
            **(
                {"maximum_window_sill_m": float(maximum_window_sill_m)}
                if maximum_window_sill_m is not None
                else {}
            ),
        },
        warnings=[
            "family/type selection is limited to the supplied controlled catalog; no internet family download is performed"
        ],
        checkpoint_label=stage_checkpoint_label(BimStage.R07),
    )


def execute_openings_stage(
    plan: OpeningStagePlan, *, invoker: StageToolInvoker
) -> list[StageExecutionRecord]:
    """Dispatch desired hosted openings through the injected adapter."""

    return dispatch_operations(plan.operations, invoker=invoker)


def verify_openings_stage(
    plan: OpeningStagePlan,
    *,
    tool_reported_success: bool | Mapping[str, bool],
    query_results: Mapping[str, Mapping[str, Any] | None],
    geometry_tolerance: float = 1e-6,
) -> list[VerificationResult]:
    """Verify hosted opening existence, geometry and metadata independently."""

    results: list[VerificationResult] = []
    for element in plan.desired_state.elements:
        success = (
            tool_reported_success.get(element.logical_id, False)
            if isinstance(tool_reported_success, Mapping)
            else tool_reported_success
        )
        results.extend(
            verify_write(
                logical_id=element.logical_id,
                tool_reported_success=success,
                query_result=query_results.get(element.logical_id),
                expected_geometry=element.geometry,
                expected_properties=element.properties,
                geometry_tolerance=geometry_tolerance,
            )
        )
    return results


plan_hosted_openings = plan_openings_stage
plan_opening_stage = plan_openings_stage
execute_hosted_openings = execute_openings_stage


__all__ = [
    "DEFAULT_ACCESSIBILITY_MIN_CLEAR_WIDTH_M",
    "OPENING_CAPABILITY",
    "OpeningCatalogError",
    "OpeningStagePlan",
    "execute_hosted_openings",
    "execute_openings_stage",
    "plan_hosted_openings",
    "plan_opening_stage",
    "plan_openings_stage",
    "verify_openings_stage",
]
