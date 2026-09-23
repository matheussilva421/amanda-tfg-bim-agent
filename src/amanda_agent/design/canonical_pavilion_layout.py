from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from shapely.affinity import translate
from shapely.geometry import LineString, Point, box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from amanda_agent.design.canonical_reference import CanonicalReferenceProfile
from amanda_agent.design.layout_protocol import ExternalSpace


@dataclass(frozen=True)
class CanonicalRoom:
    logical_id: str
    sector_id: str
    component_id: str
    name: str
    level: int
    net_area_m2: float
    polygon: BaseGeometry
    accessible: bool = False


@dataclass(frozen=True)
class BuildingBlock:
    component_id: str
    role: str
    storeys: int
    rooms: tuple[CanonicalRoom, ...]
    footprint: BaseGeometry
    floor_footprints: dict[int, BaseGeometry]
    access_point: Point


@dataclass(frozen=True)
class CoveredConnector:
    connector_id: str
    from_component: str
    to_component: str
    footprint: BaseGeometry

    @property
    def area_m2(self) -> float:
        return float(self.footprint.area)


@dataclass(frozen=True)
class CanonicalPavilionLayout:
    rooms: tuple[CanonicalRoom, ...]
    blocks: tuple[BuildingBlock, ...]
    footprint: BaseGeometry
    external_spaces: tuple[ExternalSpace, ...]
    covered_connectors: tuple[CoveredConnector, ...]
    central_garden: ExternalSpace
    content_hash: str
    accounting: dict[str, float]
    parameters: dict[str, Any]
    public_access_point: Point
    service_access_point: Point
    coordinate_basis: str = "NORMALIZED_METRIC_REFERENCE_NOT_SURVEY"
    site_fit_status: str = "UNVERIFIED"

    def block(self, component_id: str) -> BuildingBlock:
        for item in self.blocks:
            if item.component_id == component_id:
                return item
        raise KeyError(component_id)

    @property
    def residential_pavilions(self) -> tuple[BuildingBlock, ...]:
        return tuple(
            item for item in self.blocks if item.component_id.startswith("RES_PAV_")
        )


_ROOM_COMPONENTS: dict[str, tuple[str, int]] = {}
for _room_id, _component in {
    "REQ-01-01": "ADMIN_ACOLHIMENTO",
    "REQ-01-02": "ADMIN_ACOLHIMENTO",
    "REQ-01-03": "ADMIN_ACOLHIMENTO",
    "REQ-01-04": "ADMIN_ACOLHIMENTO",
    "REQ-01-05": "ADMIN_ACOLHIMENTO",
    "REQ-02-01#1": "RES_PAV_A",
    "REQ-02-01#2": "RES_PAV_A",
    "REQ-02-02#1": "RES_PAV_A",
    "REQ-02-06#1": "RES_PAV_A",
    "REQ-02-06#2": "RES_PAV_A",
    "REQ-02-02#2": "RES_PAV_B",
    "REQ-02-02#3": "RES_PAV_B",
    "REQ-02-03#1": "RES_PAV_B",
    "REQ-02-06#3": "RES_PAV_B",
    "REQ-02-06#4": "RES_PAV_B",
    "REQ-02-03#2": "RES_PAV_C",
    "REQ-02-04": "RES_PAV_C",
    "REQ-02-05": "RES_PAV_C",
    "REQ-02-06#5": "RES_PAV_C",
    "REQ-02-07": "RES_PAV_C",
    "REQ-02-08": "RES_PAV_D_COMMUNAL",
    "REQ-02-09": "RES_PAV_D_COMMUNAL",
    "REQ-02-10": "RES_PAV_D_COMMUNAL",
}.items():
    _ROOM_COMPONENTS[_room_id] = (_component, 1)

for _room_id in (
    "REQ-01-01",
    "REQ-01-02",
    "REQ-01-03",
    "REQ-01-04",
    "REQ-01-05",
    "REQ-06-04",
    "REQ-06-05",
):
    _ROOM_COMPONENTS[_room_id] = ("ADMIN_ACOLHIMENTO", 1)
for _room_id in (
    "REQ-04-01",
    "REQ-04-02",
    "REQ-04-03",
    "REQ-04-04",
    "REQ-04-05",
    "REQ-04-06",
    "REQ-06-01",
    "REQ-06-02",
    "REQ-06-03",
):
    _ROOM_COMPONENTS[_room_id] = ("ADMIN_ACOLHIMENTO", 2)
for _num in range(1, 5):
    _ROOM_COMPONENTS[f"REQ-05-{_num:02d}"] = ("SERVICE_CAPACITATION", 1)
for _num in range(6, 16):
    _ROOM_COMPONENTS[f"REQ-06-{_num:02d}"] = ("SERVICE_CAPACITATION", 1)
for _num in range(1, 5):
    _ROOM_COMPONENTS[f"REQ-03-{_num:02d}"] = ("CHILD_SECTOR", 1)


_BLOCK_CENTERS = {
    "ADMIN_ACOLHIMENTO": (0.0, -36.0),
    "RES_PAV_A": (-15.0, 0.0),
    "RES_PAV_B": (0.0, 16.0),
    "RES_PAV_C": (15.0, 0.0),
    "RES_PAV_D_COMMUNAL": (0.0, -16.0),
    "SERVICE_CAPACITATION": (30.0, -10.0),
    "CHILD_SECTOR": (-30.0, 16.0),
}


def _expand_program(program: dict[str, Any]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for sector in program["sectors"]:
        for space in sector["spaces"]:
            quantity = int(space.get("quantity", 1))
            for index in range(1, quantity + 1):
                logical_id = (
                    space["logical_id"]
                    if quantity == 1
                    else f"{space['logical_id']}#{index}"
                )
                expanded.append(
                    {
                        "logical_id": logical_id,
                        "sector_id": sector["logical_id"],
                        "name": space["name"],
                        "area": float(space["target_area_m2"]),
                        "area_kind": space["area_kind"],
                        "accessible": space.get("accessible") is True,
                    }
                )
    return expanded


def _pack_rooms(
    items: list[dict[str, Any]], max_width: float = 12.0
) -> tuple[list[tuple[dict[str, Any], BaseGeometry]], BaseGeometry]:
    placed: list[tuple[dict[str, Any], BaseGeometry]] = []
    x = 0.0
    y = 0.0
    row_height = 0.0
    for item in items:
        width = min(max_width, max(2.0, math.sqrt(item["area"])))
        depth = item["area"] / width
        if x > 0 and x + width > max_width:
            x = 0.0
            y -= row_height + 1.2
            row_height = 0.0
        polygon = box(x, y - depth, x + width, y)
        placed.append((item, polygon))
        x += width + 0.8
        row_height = max(row_height, depth)
    return placed, unary_union([polygon for _, polygon in placed]).buffer(
        0.25, join_style="mitre"
    )


def _external(
    logical_id: str,
    component_id: str,
    name: str,
    area: float,
    center: tuple[float, float],
    width: float,
) -> ExternalSpace:
    height = area / width
    cx, cy = center
    return ExternalSpace(
        logical_id=logical_id,
        name=name,
        polygon=box(cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2),
        component_id=component_id,
    )


def build_canonical_pavilion_layout(
    program: dict[str, Any], profile: CanonicalReferenceProfile
) -> CanonicalPavilionLayout:
    """Build the canonical multi-pavilion parti in normalized metric coordinates.

    Coordinates are a deterministic design frame. They are not a cadastral or
    topographic survey and cannot be used to claim site fit.
    """
    if profile.status != "CANONICAL_DESIGN_REFERENCE":
        raise ValueError("canonical reference profile is required")
    parti = profile.data.get("required_parti", {})
    if parti.get("single_linear_bar_allowed") is not False:
        raise ValueError("the canonical parti must reject a single linear bar")
    if len(profile.source_hashes) != 3:
        raise ValueError("all three canonical board hashes must be bound")

    internal = [
        item for item in _expand_program(program) if item["area_kind"] == "INTERNAL"
    ]
    external_rows = [
        item for item in _expand_program(program) if item["area_kind"] == "EXTERNAL"
    ]
    expected_internal = float(program["totals"]["internal_useful_m2"])
    expected_external = float(program["totals"]["external_programmed_m2"])
    if not math.isclose(
        sum(item["area"] for item in internal), expected_internal, abs_tol=1e-8
    ):
        raise ValueError(
            "expanded internal rooms do not match the official program total"
        )
    if not math.isclose(
        sum(item["area"] for item in external_rows), expected_external, abs_tol=1e-8
    ):
        raise ValueError(
            "expanded external spaces do not match the official program total"
        )

    rooms_by_component: dict[str, list[dict[str, Any]]] = {
        key: [] for key in _BLOCK_CENTERS
    }
    for item in internal:
        assignment = _ROOM_COMPONENTS.get(item["logical_id"])
        if assignment is None:
            raise ValueError(f"no canonical component assigned to {item['logical_id']}")
        component_id, level = assignment
        rooms_by_component[component_id].append({**item, "level": level})

    blocks: list[BuildingBlock] = []
    for component_id, center in _BLOCK_CENTERS.items():
        component_rooms: list[CanonicalRoom] = []
        floor_shapes: dict[int, BaseGeometry] = {}
        floor_placements: dict[int, list[tuple[dict[str, Any], BaseGeometry]]] = {}
        for level in sorted(
            {item["level"] for item in rooms_by_component[component_id]}
        ):
            level_items = [
                item
                for item in rooms_by_component[component_id]
                if item["level"] == level
            ]
            placements, _ = _pack_rooms(
                level_items,
                max_width=13.0
                if component_id in {"ADMIN_ACOLHIMENTO", "SERVICE_CAPACITATION"}
                else 10.0,
            )
            floor_placements[level] = placements
            floor_shapes[level] = unary_union([polygon for _, polygon in placements])

        projected = unary_union(list(floor_shapes.values()))
        minx, miny, maxx, maxy = projected.bounds
        offset_x = center[0] - (minx + maxx) / 2
        offset_y = center[1] - (miny + maxy) / 2
        translated_floors: dict[int, BaseGeometry] = {}
        for level, placements in floor_placements.items():
            for item, polygon in placements:
                placed = translate(polygon, xoff=offset_x, yoff=offset_y)
                component_rooms.append(
                    CanonicalRoom(
                        logical_id=item["logical_id"],
                        sector_id=item["sector_id"],
                        component_id=component_id,
                        name=item["name"],
                        level=level,
                        net_area_m2=item["area"],
                        polygon=placed,
                        accessible=item["accessible"],
                    )
                )
            translated_floors[level] = translate(
                floor_shapes[level], xoff=offset_x, yoff=offset_y
            ).buffer(0.25, join_style="mitre")
        all_floor_shells = unary_union(list(translated_floors.values()))
        bounds = all_floor_shells.bounds
        footprint = box(*bounds)
        minx, miny, maxx, maxy = footprint.bounds
        if component_id == "RES_PAV_A":
            access = Point(maxx, center[1])
        elif component_id == "RES_PAV_B":
            access = Point(center[0], miny)
        elif component_id == "RES_PAV_C":
            access = Point(minx, center[1])
        elif component_id == "RES_PAV_D_COMMUNAL":
            access = Point(center[0], maxy)
        elif (
            component_id == "SERVICE_CAPACITATION"
            or component_id == "ADMIN_ACOLHIMENTO"
        ):
            access = Point(center[0], miny)
        else:
            access = Point(center)
        role = {
            "ADMIN_ACOLHIMENTO": "public_administration_two_levels",
            "RES_PAV_A": "residential_sleeping",
            "RES_PAV_B": "residential_sleeping",
            "RES_PAV_C": "residential_sleeping",
            "RES_PAV_D_COMMUNAL": "residential_communal_dining",
            "SERVICE_CAPACITATION": "separate_services_and_capacity_building",
            "CHILD_SECTOR": "child_green_interface",
        }[component_id]
        blocks.append(
            BuildingBlock(
                component_id=component_id,
                role=role,
                storeys=2 if component_id == "ADMIN_ACOLHIMENTO" else 1,
                rooms=tuple(component_rooms),
                footprint=footprint,
                floor_footprints=translated_floors,
                access_point=access,
            )
        )

    block_map = {item.component_id: item for item in blocks}
    external_by_id = {item["logical_id"]: item for item in external_rows}
    external_specs = (
        ("REQ-07-01", "PROTECTED_PATIO", (0.0, 0.0), 8.0),
        ("REQ-07-02", "THERAPEUTIC_GARDEN", (-24.0, 25.0), 10.0),
        ("REQ-07-03", "HORTA", (30.0, -35.0), 6.0),
        ("REQ-07-04", "EXERCISE", (28.0, 18.0), 6.0),
        ("REQ-07-05", "PLAYGROUND", (-32.0, 0.0), 8.0),
    )
    external_spaces = tuple(
        _external(
            logical_id,
            component_id,
            external_by_id[logical_id]["name"],
            external_by_id[logical_id]["area"],
            center,
            width,
        )
        for logical_id, component_id, center, width in external_specs
    )
    patio = next(
        item for item in external_spaces if item.component_id == "PROTECTED_PATIO"
    )
    patio_minx, patio_miny, patio_maxx, patio_maxy = patio.polygon.bounds
    connector_specs = (
        (
            "RES_PAV_A",
            (block_map["RES_PAV_A"].footprint.bounds[2], 0.0),
            (patio_minx, 0.0),
        ),
        (
            "RES_PAV_B",
            (0.0, block_map["RES_PAV_B"].footprint.bounds[1]),
            (0.0, patio_maxy),
        ),
        (
            "RES_PAV_C",
            (block_map["RES_PAV_C"].footprint.bounds[0], 0.0),
            (patio_maxx, 0.0),
        ),
        (
            "RES_PAV_D_COMMUNAL",
            (0.0, block_map["RES_PAV_D_COMMUNAL"].footprint.bounds[3]),
            (0.0, patio_miny),
        ),
    )
    covered_connectors: list[CoveredConnector] = []
    for component_id, start, end in connector_specs:
        path = LineString([start, end]).buffer(
            1.0, cap_style="flat", join_style="mitre"
        )
        covered_connectors.append(
            CoveredConnector(
                connector_id=f"COVERED-{component_id}-TO-PROTECTED_PATIO",
                from_component=component_id,
                to_component="PROTECTED_PATIO",
                footprint=path,
            )
        )

    public_access = Point(0.0, -47.0)
    source_payload = {
        "program": program,
        "canonical_source_hashes": sorted(profile.source_hashes),
        "components": list(_BLOCK_CENTERS.items()),
        "geometry": {
            "blocks": [(item.component_id, item.footprint.wkt) for item in blocks],
            "external_spaces": [
                (item.component_id, item.polygon.wkt) for item in external_spaces
            ],
            "covered_connectors": [
                (item.connector_id, item.footprint.wkt) for item in covered_connectors
            ],
        },
        "coordinate_basis": "NORMALIZED_METRIC_REFERENCE_NOT_SURVEY",
        "selection_authority": "USER_DIRECTED",
    }
    content_hash = hashlib.sha256(
        json.dumps(
            source_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()
    net_area = sum(room.net_area_m2 for block in blocks for room in block.rooms)
    external_area = sum(space.area_m2 for space in external_spaces)
    footprint_union = unary_union([block.footprint for block in blocks])
    return CanonicalPavilionLayout(
        rooms=tuple(room for block in blocks for room in block.rooms),
        blocks=tuple(blocks),
        footprint=footprint_union,
        external_spaces=external_spaces,
        covered_connectors=tuple(covered_connectors),
        central_garden=patio,
        content_hash=content_hash,
        accounting={
            "net_internal_m2": net_area,
            "external_programmed_m2": external_area,
            "enclosed_estimate_min_m2": float(
                program["totals"]["enclosed_estimate_m2"][0]
            ),
            "enclosed_estimate_max_m2": float(
                program["totals"]["enclosed_estimate_m2"][1]
            ),
            "covered_estimate_min_m2": float(
                program["totals"]["covered_estimate_m2"][0]
            ),
            "covered_estimate_max_m2": float(
                program["totals"]["covered_estimate_m2"][1]
            ),
        },
        parameters={
            "selection_authority": "USER_DIRECTED",
            "canonical_deviations": [],
            "geometry_origin": "CANONICAL_PAVILION_RECONSTRUCTION",
            "superseded_source_reused": False,
            "superseded_solution_id": "AMANDA-RUN-001-S01",
            "canonical_source_hashes": list(profile.source_hashes),
            "people": int(program["baseline"]["person_capacity"]),
            "coordinate_basis": "NORMALIZED_METRIC_REFERENCE_NOT_SURVEY",
            "site_fit_status": "UNVERIFIED",
            "external_links_are_covered": True,
        },
        public_access_point=public_access,
        service_access_point=block_map["SERVICE_CAPACITATION"].access_point,
    )
