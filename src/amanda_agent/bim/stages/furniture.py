"""R10 functional furniture desired-state planning (P05-T18)."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from math import ceil
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

FURNITURE_CAPABILITY = "revit.create_furniture_element"
FURNITURE_DESIGN_OPTION = "DELEGATED_DESIGN"


class FurnitureCatalogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    family: str = Field(min_length=1)
    type: str = Field(min_length=1)


class FurnitureItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    family: str = Field(min_length=1)
    type: str = Field(min_length=1)
    furniture_set: str = Field(min_length=1)
    sector_id: str = Field(min_length=1)
    space_id: str = Field(min_length=1)
    quantity: int = Field(default=1, ge=1)


class FurnitureStagePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: BimStage = BimStage.R10
    preflight: PreflightReport
    person_capacity: int = Field(ge=1, le=20)
    desired_state: DesiredState
    items: list[FurnitureItem] = Field(default_factory=list)
    operations: list[StageOperation] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    checkpoint_label: str = "R10_FURNITURE"

    @property
    def desired_elements(self) -> list[DesiredElement]:
        return self.desired_state.elements


DEFAULT_FURNITURE_CATALOG: dict[str, FurnitureCatalogEntry] = {
    "bed": FurnitureCatalogEntry(family="Furniture-Bed", type="Bed"),
    "bedside": FurnitureCatalogEntry(family="Furniture-Bedside", type="BedsideTable"),
    "dining_table": FurnitureCatalogEntry(
        family="Furniture-Dining", type="DiningTable4"
    ),
    "dining_chair": FurnitureCatalogEntry(
        family="Furniture-Dining", type="DiningChair"
    ),
    "desk": FurnitureCatalogEntry(family="Furniture-Workstation", type="Desk"),
    "office_chair": FurnitureCatalogEntry(
        family="Furniture-Workstation", type="OfficeChair"
    ),
    "meeting_chair": FurnitureCatalogEntry(
        family="Furniture-Meeting", type="MeetingChair"
    ),
    "child_table": FurnitureCatalogEntry(family="Furniture-Child", type="ChildTable"),
    "child_chair": FurnitureCatalogEntry(family="Furniture-Child", type="ChildChair"),
    "low_storage": FurnitureCatalogEntry(family="Furniture-Storage", type="LowStorage"),
    "storage": FurnitureCatalogEntry(family="Furniture-Storage", type="StorageUnit"),
}


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


def _kind(space_name: str) -> str:
    name = space_name.casefold()
    if "quarto" in name or "dorm" in name:
        return "bedroom"
    if "refeitorio" in name or "copa" in name or "cozinha" in name:
        return "dining"
    if "psicologia" in name:
        return "psychology"
    if any(
        token in name
        for token in (
            "servico social",
            "juridico",
            "atendimento",
            "reuniao",
            "multiuso e grupos",
        )
    ):
        return "technical"
    if any(token in name for token in ("brinquedoteca", "pedagogico", "infantil")):
        return "child-area"
    if any(
        token in name
        for token in (
            "coordenacao",
            "secretaria",
            "administrativo",
            "equipe",
            "arquivo",
        )
    ):
        return "office"
    return "support"


def _catalog_entry(
    catalog: Mapping[str, FurnitureCatalogEntry | Mapping[str, str]], key: str
) -> FurnitureCatalogEntry:
    raw = catalog.get(key)
    if raw is None:
        raise ValueError(f"controlled furniture catalog has no entry for {key}")
    return (
        raw
        if isinstance(raw, FurnitureCatalogEntry)
        else FurnitureCatalogEntry.model_validate(raw)
    )


def _append_item(
    items: list[FurnitureItem],
    *,
    desired: list[DesiredElement],
    catalog: Mapping[str, FurnitureCatalogEntry | Mapping[str, str]],
    sector_id: str,
    space_id: str,
    set_name: str,
    key: str,
    ordinal: int,
    person_capacity: int,
    generation_run: str,
) -> None:
    entry = _catalog_entry(catalog, key)
    logical_id = f"FUR-{space_id}-{key.upper()}-{ordinal:02d}"
    item = FurnitureItem(
        logical_id=logical_id,
        family=entry.family,
        type=entry.type,
        furniture_set=set_name,
        sector_id=sector_id,
        space_id=space_id,
    )
    properties = {
        "family": item.family,
        "type": item.type,
        "furniture_set": set_name,
        "sector_id": sector_id,
        "space_id": space_id,
        "occupancy_limit": person_capacity,
        "spatial_qa_role": "functional_placeholder",
    }
    desired.append(
        DesiredElement(
            logical_id=logical_id,
            category="furniture",
            geometry={"host_space_id": space_id},
            properties=properties,
            requirement_id=f"R10-{set_name.upper()}",
            design_option=FURNITURE_DESIGN_OPTION,
            generation_run=generation_run,
            provenance=BimProvenance(
                requirement_id=f"R10-{set_name.upper()}",
                design_option=FURNITURE_DESIGN_OPTION,
                generation_run=generation_run,
                notes={"family": item.family, "type": item.type},
            ),
        )
    )
    items.append(item)


def plan_furniture_stage(
    request: PreflightRequest,
    *,
    program: Mapping[str, Any],
    catalog: Mapping[str, FurnitureCatalogEntry | Mapping[str, str]] | None = None,
    max_people: int = 20,
    external_elements: Sequence[DesiredElement | Mapping[str, Any]] = (),
    external_planner: Callable[[], Sequence[DesiredElement | Mapping[str, Any]]]
    | None = None,
) -> FurnitureStagePlan:
    """Expand the fixed program into functional, catalog-bound placeholders."""

    capacity = int(program.get("baseline", {}).get("person_capacity", 0))
    if capacity < 1 or capacity > max_people or capacity > 20:
        raise ValueError(
            f"furniture program capacity must be between 1 and 20 people, got {capacity}"
        )
    effective = with_stage_requirements(request, extra=(FURNITURE_CAPABILITY,))
    report = run_preflight(effective)
    if not report.ok:
        raise StagePreflightError(
            "R10 preflight refused: " + "; ".join(report.problems)
        )
    selected_catalog = catalog or DEFAULT_FURNITURE_CATALOG
    desired: list[DesiredElement] = []
    items: list[FurnitureItem] = []
    for sector in program.get("sectors", []):
        if str(sector.get("area_kind", "INTERNAL")).upper() == "EXTERNAL":
            continue
        sector_id = str(sector.get("logical_id", ""))
        if not sector_id:
            raise ValueError("furniture sector requires logical_id")
        for space in sector.get("spaces", []):
            space_id = str(space.get("logical_id", ""))
            space_name = str(space.get("name", ""))
            quantity = int(space.get("quantity", 1))
            if not space_id or not space_name or quantity < 1:
                raise ValueError(
                    "furniture space requires logical_id, name and positive quantity"
                )
            kind = _kind(space_name)
            for unit in range(1, quantity + 1):
                prefix = f"{unit:02d}"
                if kind == "bedroom":
                    beds = int(
                        space.get("beds_per_unit")
                        or (
                            3
                            if "triplo" in space_name.casefold()
                            else 2
                            if "duplo" in space_name.casefold()
                            else 1
                        )
                    )
                    for ordinal in range(1, beds + 1):
                        _append_item(
                            items,
                            desired=desired,
                            catalog=selected_catalog,
                            sector_id=sector_id,
                            space_id=f"{space_id}-{prefix}",
                            set_name="bedroom",
                            key="bed",
                            ordinal=ordinal,
                            person_capacity=capacity,
                            generation_run=effective.generation_run,
                        )
                    _append_item(
                        items,
                        desired=desired,
                        catalog=selected_catalog,
                        sector_id=sector_id,
                        space_id=f"{space_id}-{prefix}",
                        set_name="bedroom",
                        key="bedside",
                        ordinal=1,
                        person_capacity=capacity,
                        generation_run=effective.generation_run,
                    )
                elif kind == "dining":
                    for ordinal in range(1, ceil(capacity / 4) + 1):
                        _append_item(
                            items,
                            desired=desired,
                            catalog=selected_catalog,
                            sector_id=sector_id,
                            space_id=f"{space_id}-{prefix}",
                            set_name="dining",
                            key="dining_table",
                            ordinal=ordinal,
                            person_capacity=capacity,
                            generation_run=effective.generation_run,
                        )
                    for ordinal in range(1, capacity + 1):
                        _append_item(
                            items,
                            desired=desired,
                            catalog=selected_catalog,
                            sector_id=sector_id,
                            space_id=f"{space_id}-{prefix}",
                            set_name="dining",
                            key="dining_chair",
                            ordinal=ordinal,
                            person_capacity=capacity,
                            generation_run=effective.generation_run,
                        )
                elif kind in {"psychology", "technical"}:
                    _append_item(
                        items,
                        desired=desired,
                        catalog=selected_catalog,
                        sector_id=sector_id,
                        space_id=f"{space_id}-{prefix}",
                        set_name=kind,
                        key="desk",
                        ordinal=1,
                        person_capacity=capacity,
                        generation_run=effective.generation_run,
                    )
                    for ordinal in range(1, 3):
                        _append_item(
                            items,
                            desired=desired,
                            catalog=selected_catalog,
                            sector_id=sector_id,
                            space_id=f"{space_id}-{prefix}",
                            set_name=kind,
                            key="meeting_chair",
                            ordinal=ordinal,
                            person_capacity=capacity,
                            generation_run=effective.generation_run,
                        )
                elif kind == "child-area":
                    for ordinal in range(1, 5):
                        _append_item(
                            items,
                            desired=desired,
                            catalog=selected_catalog,
                            sector_id=sector_id,
                            space_id=f"{space_id}-{prefix}",
                            set_name=kind,
                            key="child_table",
                            ordinal=ordinal,
                            person_capacity=capacity,
                            generation_run=effective.generation_run,
                        )
                    for ordinal in range(1, 9):
                        _append_item(
                            items,
                            desired=desired,
                            catalog=selected_catalog,
                            sector_id=sector_id,
                            space_id=f"{space_id}-{prefix}",
                            set_name=kind,
                            key="child_chair",
                            ordinal=ordinal,
                            person_capacity=capacity,
                            generation_run=effective.generation_run,
                        )
                    _append_item(
                        items,
                        desired=desired,
                        catalog=selected_catalog,
                        sector_id=sector_id,
                        space_id=f"{space_id}-{prefix}",
                        set_name=kind,
                        key="low_storage",
                        ordinal=1,
                        person_capacity=capacity,
                        generation_run=effective.generation_run,
                    )
                elif kind == "office":
                    _append_item(
                        items,
                        desired=desired,
                        catalog=selected_catalog,
                        sector_id=sector_id,
                        space_id=f"{space_id}-{prefix}",
                        set_name=kind,
                        key="desk",
                        ordinal=1,
                        person_capacity=capacity,
                        generation_run=effective.generation_run,
                    )
                    _append_item(
                        items,
                        desired=desired,
                        catalog=selected_catalog,
                        sector_id=sector_id,
                        space_id=f"{space_id}-{prefix}",
                        set_name=kind,
                        key="office_chair",
                        ordinal=1,
                        person_capacity=capacity,
                        generation_run=effective.generation_run,
                    )
                else:
                    _append_item(
                        items,
                        desired=desired,
                        catalog=selected_catalog,
                        sector_id=sector_id,
                        space_id=f"{space_id}-{prefix}",
                        set_name="support",
                        key="storage",
                        ordinal=1,
                        person_capacity=capacity,
                        generation_run=effective.generation_run,
                    )
    desired_state = DesiredState(
        stage=BimStage.R10,
        generation_run=effective.generation_run,
        elements=[*desired, *_external_elements(external_elements, external_planner)],
    )
    preferred, fallbacks = provider_assignment(effective, FURNITURE_CAPABILITY)
    operations = [
        StageOperation(
            stage=BimStage.R10,
            logical_id=element.logical_id,
            semantic_capability=FURNITURE_CAPABILITY,
            payload=element.model_dump(mode="json"),
            verification_rules=[
                "independent_requery",
                "family_and_type_present",
                "functional_placeholder",
            ],
            preferred_provider=preferred,
            fallback_providers=fallbacks,
        )
        for element in desired
    ]
    return FurnitureStagePlan(
        preflight=report,
        person_capacity=capacity,
        desired_state=desired_state,
        items=items,
        operations=operations,
        notes=[
            "functional placeholders are used for spatial QA; no decorative randomization"
        ],
        checkpoint_label=stage_checkpoint_label(BimStage.R10),
    )


def execute_furniture_stage(
    plan: FurnitureStagePlan, *, invoker: StageToolInvoker
) -> list[StageExecutionRecord]:
    return dispatch_operations(plan.operations, invoker=invoker)


def verify_furniture_stage(
    plan: FurnitureStagePlan,
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
    "DEFAULT_FURNITURE_CATALOG",
    "FURNITURE_CAPABILITY",
    "FurnitureCatalogEntry",
    "FurnitureItem",
    "FurnitureStagePlan",
    "execute_furniture_stage",
    "plan_furniture_stage",
    "verify_furniture_stage",
]
