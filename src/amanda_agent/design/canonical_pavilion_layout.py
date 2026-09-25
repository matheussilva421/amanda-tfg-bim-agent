from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from shapely.affinity import translate
from shapely.geometry import LineString, Point, box
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points, unary_union

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
    centerline: tuple[tuple[float, float], ...] = ()

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
    service_courtyard: BaseGeometry
    content_hash: str
    accounting: dict[str, float]
    parameters: dict[str, Any]
    public_access_point: Point
    service_public_access_point: Point
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
    "REQ-02-02#2": "RES_PAV_A",
    "REQ-02-06#1": "RES_PAV_A",
    "REQ-02-06#2": "RES_PAV_A",
    "REQ-02-03#1": "RES_PAV_B",
    "REQ-02-03#2": "RES_PAV_B",
    "REQ-02-04": "RES_PAV_B",
    "REQ-02-06#3": "RES_PAV_B",
    "REQ-02-06#4": "RES_PAV_B",
    "REQ-02-02#3": "RES_PAV_C",
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
    "REQ-04-01",
    "REQ-04-02",
    "REQ-04-03",
    "REQ-04-04",
    "REQ-04-06",
    "REQ-05-03",
    "REQ-05-04",
):
    _ROOM_COMPONENTS[_room_id] = ("ADMIN_ACOLHIMENTO", 1)
for _room_id in (
    "REQ-04-05",
    "REQ-06-01",
    "REQ-06-02",
    "REQ-06-03",
    "REQ-06-04",
    "REQ-06-05",
):
    _ROOM_COMPONENTS[_room_id] = ("ADMIN_ACOLHIMENTO", 2)
for _num in range(1, 3):
    _ROOM_COMPONENTS[f"REQ-05-{_num:02d}"] = ("SERVICE_CAPACITATION", 1)
for _num in range(6, 16):
    _ROOM_COMPONENTS[f"REQ-06-{_num:02d}"] = ("SERVICE_CAPACITATION", 1)
for _num in range(1, 5):
    _ROOM_COMPONENTS[f"REQ-03-{_num:02d}"] = ("CHILD_SECTOR", 1)


_BLOCK_CENTERS = {
    "ADMIN_ACOLHIMENTO": (0.0, -44.0),
    "RES_PAV_A": (-13.0, 37.0),
    "RES_PAV_B": (-13.0, 7.0),
    "RES_PAV_C": (13.0, 7.0),
    "RES_PAV_D_COMMUNAL": (13.0, 37.0),
    "SERVICE_CAPACITATION": (32.0, -22.0),
    "CHILD_SECTOR": (-33.0, -10.0),
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


def _pack_rooms_centered(
    items: list[dict[str, Any]], max_width: float, center: tuple[float, float]
) -> list[tuple[dict[str, Any], BaseGeometry]]:
    placements, _ = _pack_rooms(items, max_width=max_width)
    bounds = unary_union([polygon for _, polygon in placements]).bounds
    offset_x = center[0] - (bounds[0] + bounds[2]) / 2.0
    offset_y = center[1] - (bounds[1] + bounds[3]) / 2.0
    return [
        (item, translate(polygon, xoff=offset_x, yoff=offset_y))
        for item, polygon in placements
    ]


def _curved_service_spine(center: tuple[float, float]) -> BaseGeometry:
    cx, cy = center
    local_points = (
        (-12.5, -7.0), (-15.0, -7.0), (-16.0, -4.0), (-16.0, 4.0),
        (-14.5, 8.0), (-11.0, 12.0), (-7.0, 16.0), (-3.5, 18.0),
        (0.0, 18.5), (3.5, 18.0), (7.0, 16.0), (11.0, 12.0),
        (14.5, 8.0), (16.0, 4.0), (16.0, -4.0), (15.0, -7.0),
        (12.5, -7.0),
    )
    points = [(cx + x, cy + y) for x, y in local_points]
    return LineString(points).buffer(1.5, cap_style="round", join_style="round")


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


def _deviation_record(
    profile: CanonicalReferenceProfile,
    program_sha256: str,
    *,
    deviation_id: str,
    affected_element: str,
    board_indices: tuple[int, ...],
    reason: str,
    alternatives_considered: tuple[str, ...],
    impact: str,
    extra: dict[str, int] | None = None,
) -> dict[str, Any]:
    board_references = [
        "docs/source/canonical/"
        + image.rsplit("/", maxsplit=1)[-1]
        + f"#sha256={profile.source_hashes[index]}"
        for index, image in enumerate(profile.canonical_images)
        if index in board_indices
    ]
    program_reference = (
        "docs/source/programa_necessidades.pdf#sha256=" + program_sha256
    )
    input_hashes = [
        *(profile.source_hashes[index] for index in board_indices),
        program_sha256,
    ]
    record: dict[str, Any] = {
        "id": deviation_id,
        "description": reason,
        "basis": "PROGRAM",
        "evidence": "; ".join([*board_references, program_reference]),
        "affected_element": affected_element,
        "board_reference": board_references,
        "program_reference": program_reference,
        "reason": reason,
        "alternatives_considered": list(alternatives_considered),
        "impact": impact,
        "decision_status": "RECONCILED_P1_T01; AMANDA_REVIEW_PENDING",
        "input_hashes": input_hashes,
    }
    if extra:
        record.update(extra)
    return record


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
    if len(profile.source_hashes) != 4:
        raise ValueError("all four canonical board hashes must be bound")

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
            if component_id == "SERVICE_CAPACITATION":
                service_items = {
                    item["logical_id"]: item for item in level_items
                }
                community = [
                    item for item in level_items if item["sector_id"] == "SEC-05"
                ]
                kitchen_and_laundry = [
                    service_items[f"REQ-06-{number:02}"]
                    for number in range(6, 10)
                ]
                cargo_and_storage = [
                    service_items[logical_id]
                    for logical_id in (
                        "REQ-06-14",
                        "REQ-06-10",
                        "REQ-06-11",
                        "REQ-06-12",
                        "REQ-06-13",
                        "REQ-06-15",
                    )
                ]
                placements = [
                    *_pack_rooms_centered(community, 14.0, (0.0, 11.0)),
                    *_pack_rooms_centered(kitchen_and_laundry, 8.0, (-12.5, 0.0)),
                    *_pack_rooms_centered(cargo_and_storage, 8.0, (12.5, 0.0)),
                ]
            else:
                placements, _ = _pack_rooms(
                    level_items,
                    max_width=13.0
                    if component_id == "ADMIN_ACOLHIMENTO"
                    else 10.0,
                )
            floor_placements[level] = placements
            floor_shapes[level] = unary_union([polygon for _, polygon in placements])

        projected = unary_union(list(floor_shapes.values()))
        minx, miny, maxx, maxy = projected.bounds
        if component_id == "SERVICE_CAPACITATION":
            offset_x, offset_y = center
        else:
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
            translated_floor = translate(
                floor_shapes[level], xoff=offset_x, yoff=offset_y
            )
            if component_id.startswith("RES_PAV_"):
                # The residential reference uses compact, softened pavilion
                # envelopes around the garden rather than square bar plates.
                translated_floors[level] = translated_floor.buffer(
                    0.8, quad_segs=8, join_style="round"
                )
            elif component_id == "SERVICE_CAPACITATION":
                translated_floors[level] = translated_floor.buffer(
                    0.65, quad_segs=8, join_style="round"
                )
            else:
                translated_floors[level] = translated_floor.buffer(
                    0.25, join_style="mitre"
                )
        all_floor_shells = unary_union(list(translated_floors.values()))
        bounds = all_floor_shells.bounds
        if component_id.startswith("RES_PAV_"):
            footprint = all_floor_shells
        elif component_id == "SERVICE_CAPACITATION":
            footprint = unary_union(
                [all_floor_shells, _curved_service_spine(center)]
            )
            translated_floors[1] = footprint
        else:
            footprint = box(*bounds)
        minx, miny, maxx, maxy = footprint.bounds
        if component_id.startswith("RES_PAV_"):
            access = nearest_points(footprint, Point(0.0, 0.0))[0]
        elif component_id == "ADMIN_ACOLHIMENTO":
            access = Point(center[0], miny)
        elif component_id == "SERVICE_CAPACITATION":
            access = Point(center[0] - 18.0, center[1] - 7.0)
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
    footprint_union = unary_union([item.footprint for item in blocks])
    service_center = _BLOCK_CENTERS["SERVICE_CAPACITATION"]
    service_courtyard = box(
        service_center[0] - 7.0,
        service_center[1] - 6.0,
        service_center[0] + 7.0,
        service_center[1] + 4.0,
    )
    external_by_id = {item["logical_id"]: item for item in external_rows}
    external_specs = (
        ("REQ-07-01", "PROTECTED_PATIO", (0.0, 22.0), 8.0),
        ("REQ-07-02", "THERAPEUTIC_GARDEN", (0.0, -10.0), 10.0),
        ("REQ-07-03", "HORTA", (58.0, 0.0), 6.0),
        ("REQ-07-04", "EXERCISE", (0.0, -24.0), 6.0),
        ("REQ-07-05", "PLAYGROUND", (-33.0, -20.0), 8.0),
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
    patio_center = patio.polygon.centroid
    covered_connectors: list[CoveredConnector] = []
    for component_id in (
        "RES_PAV_A",
        "RES_PAV_B",
        "RES_PAV_C",
        "RES_PAV_D_COMMUNAL",
    ):
        block = block_map[component_id]
        start = block.access_point
        garden_edge, _ = nearest_points(patio.polygon, block.footprint)
        midpoint_x = (start.x + garden_edge.x) / 2.0
        midpoint_y = (start.y + garden_edge.y) / 2.0
        outward_x = block.footprint.centroid.x - patio_center.x
        outward_y = block.footprint.centroid.y - patio_center.y
        outward_length = math.hypot(outward_x, outward_y)
        control = (
            midpoint_x - outward_y / outward_length * 2.5,
            midpoint_y + outward_x / outward_length * 2.5,
        )
        curve_points = []
        for step in range(13):
            t = step / 12.0
            inverse = 1.0 - t
            curve_points.append(
                (
                    inverse * inverse * start.x
                    + 2.0 * inverse * t * control[0]
                    + t * t * garden_edge.x,
                    inverse * inverse * start.y
                    + 2.0 * inverse * t * control[1]
                    + t * t * garden_edge.y,
                )
            )
        corridor = LineString(curve_points).buffer(
            1.0, cap_style="flat", join_style="round"
        )
        path = corridor.difference(footprint_union)
        covered_connectors.append(
            CoveredConnector(
                connector_id=f"COVERED-{component_id}-TO-PROTECTED_PATIO",
                from_component=component_id,
                to_component="PROTECTED_PATIO",
                footprint=path,
                centerline=tuple(
                    (float(x), float(y)) for x, y in curve_points
                ),
            )
        )

    public_access = Point(0.0, -62.0)
    service_public_access = block_map["SERVICE_CAPACITATION"].access_point
    loading_room = next(
        room
        for room in block_map["SERVICE_CAPACITATION"].rooms
        if room.logical_id == "REQ-06-14"
    )
    service_cargo_access = nearest_points(
        loading_room.polygon,
        block_map["SERVICE_CAPACITATION"].footprint.boundary,
    )[1]
    program_sha256 = str(program["baseline"]["source_sha256"])
    canonical_deviations = [
        _deviation_record(
            profile,
            program_sha256,
            deviation_id="BOARD02-SEC05-SUPPORT-PLACEMENT",
            affected_element="SEC-05 REQ-05-03/04 locations and Board-04 repeated labels",
            board_indices=(1, 3),
            reason="Board 02 shows the official 8 m² community copa and 5 m² accessible toilet in the administrative ground floor. Their SEC-05 IDs/areas stay unchanged there; Board 04's larger/multiple depictions do not create duplicates.",
            alternatives_considered=(
                "Keep both official rooms in the southeast services block, contrary to Board 02 placement.",
                "Duplicate the Board-04 labels as extra rooms, exceeding official quantities.",
                "Use the exact Board-02 ground-floor locations once at official areas.",
            ),
            impact="No change to official room count or area; 13 m² of official SEC-05 support remains in the administrative footprint.",
        ),
        _deviation_record(
            profile,
            program_sha256,
            deviation_id="BOARD02-ARCHIVE-DUPLICATE-LABEL",
            affected_element="SEC-04 REQ-04-06 archive/support repeated on Board 02",
            board_indices=(1,),
            reason="Board 02 labels a 5 m² archive on the ground floor and a 5 m² support/archive upstairs, while the program has one 5 m² REQ-04-06.",
            alternatives_considered=(
                "Model both board labels as rooms, doubling the official archive area.",
                "Keep the single official room on the ground floor beside public intake; treat the upper label as repeated graphic notation.",
            ),
            impact="One official 5 m² room remains on the ground floor; no second archive area is added upstairs.",
        ),
        _deviation_record(
            profile,
            program_sha256,
            deviation_id="BOARD03-SCHEMATIC-BATHROOM-COUNT",
            affected_element="Common bathroom cells in the three sleeping pavilions",
            board_indices=(2,),
            reason="Board 03 depicts six common bathroom cells; the official program requires five common bathrooms and one accessible bathroom.",
            alternatives_considered=(
                "Model all six common cells, exceeding the official quantity by one.",
                "Keep the five official rooms distributed 2/2/1 across the sleeping pavilions; leave the extra board symbol non-additive.",
            ),
            impact="Exactly five 3.5 m² common bathrooms and one 4.5 m² accessible bathroom are modeled; the sixth common cell is not an additional programmed room.",
            extra={
                "board_common_cell_count": 6,
                "official_common_room_count": 5,
                "modeled_common_room_count": 5,
            },
        ),
        _deviation_record(
            profile,
            program_sha256,
            deviation_id="BOARD04-UNPRICED-FUNCTIONS",
            affected_element="Board-04 training and reception functions without official room rows",
            board_indices=(3,),
            reason="Informatics, sewing/handicraft, practical entrepreneurship, and orientation appear on Board 04 without matching official room rows or individual official areas.",
            alternatives_considered=(
                "Create four extra official rooms/areas from the board labels.",
                "Retain them as unpriced operational uses pending later assignment within approved rooms.",
            ),
            impact="No new room or area enters the official 626 m² internal program; exact functional attribution remains open.",
        ),
        _deviation_record(
            profile,
            program_sha256,
            deviation_id="BOARD04-AREA-AND-QUANTITY-MISMATCHES",
            affected_element="Board-04 printed area and quantity labels",
            board_indices=(3,),
            reason="Board 04 areas differ from the PDF for multiuse (50/60 m²), reception (25/10 m²), accessible toilets (2x18/1x5 m²), support/deposit (12 m² versus official 8 or 6 m² candidates), DML (6/3 m²), combined linen/store (15/6+8 m²), laundry (20/12 m²), and support copa (15/8 m²).",
            alternatives_considered=(
                "Use the printed Board-04 areas/quantities as official, changing the accepted program.",
                "Keep every PDF area/quantity and report Board-04 figures as unresolved graphic deltas.",
            ),
            impact="All modeled room counts and areas remain those of the official PDF; printed Board-04 deltas do not change 626 m² internal or 260 m² external totals.",
        ),
        _deviation_record(
            profile,
            program_sha256,
            deviation_id="BOARD04-OFFICIAL-SUPPORT-ROOMS",
            affected_element="Official SEC-05/SEC-06 support rooms without a unique Board-04 label",
            board_indices=(3,),
            reason="The PDF requires chair/material storage 8 m², production kitchen 25 m², dry pantry 6 m², freezer/refrigerated storage 4 m², waste 4 m², and loading/unloading 15 m²; Board 04 does not give each a unique room label and area.",
            alternatives_considered=(
                "Infer official areas from the service-access or generic support labels.",
                "Keep the PDF-defined rooms and areas distinct; treat the service access as circulation, not as the 15 m² loading room.",
            ),
            impact="Official support-room counts/areas stay intact; the loading access point does not substitute for the loading room.",
        ),
        _deviation_record(
            profile,
            program_sha256,
            deviation_id="BOARD04-GARDEN-LABEL-IS-UNMETERED",
            affected_element="Board-04 Pátio de Convivência/Jardim Central label",
            board_indices=(3,),
            reason="The Board-04 garden label has no area, while the PDF lists separate 80 m² protected patio and 80 m² therapeutic garden.",
            alternatives_considered=(
                "Merge the two official 80 m² spaces into one garden.",
                "Represent the protected patio and therapeutic garden separately at their official areas.",
            ),
            impact="Both official 80 m² external spaces remain distinct and included once in the 260 m² external total.",
        ),
    ]
    source_payload = {
        "program": program,
        "canonical_source_hashes": sorted(profile.source_hashes),
        "canonical_deviations": canonical_deviations,
        "components": list(_BLOCK_CENTERS.items()),
        "geometry": {
            "blocks": [(item.component_id, item.footprint.wkt) for item in blocks],
            "external_spaces": [
                (item.component_id, item.polygon.wkt) for item in external_spaces
            ],
            "service_courtyard": service_courtyard.wkt,
            "public_access": public_access.wkt,
            "service_public_access": service_public_access.wkt,
            "service_cargo_access": service_cargo_access.wkt,
            "covered_connectors": [
                (item.connector_id, item.footprint.wkt, item.centerline)
                for item in covered_connectors
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
    return CanonicalPavilionLayout(
        rooms=tuple(room for block in blocks for room in block.rooms),
        blocks=tuple(blocks),
        footprint=footprint_union,
        external_spaces=external_spaces,
        covered_connectors=tuple(covered_connectors),
        central_garden=patio,
        service_courtyard=service_courtyard,
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
            "canonical_deviations": [
                {**item, "output_hash": content_hash}
                for item in canonical_deviations
            ],
            "geometry_origin": "CANONICAL_PAVILION_RECONSTRUCTION",
            "superseded_source_reused": False,
            "superseded_solution_id": "AMANDA-RUN-001-S01",
            "canonical_source_hashes": list(profile.source_hashes),
            "program_source_sha256": str(program["baseline"]["source_sha256"]),
            "people": int(program["baseline"]["person_capacity"]),
            "coordinate_basis": "NORMALIZED_METRIC_REFERENCE_NOT_SURVEY",
            "site_fit_status": "UNVERIFIED",
            "external_links_are_covered": True,
        },
        public_access_point=public_access,
        service_public_access_point=service_public_access,
        service_access_point=service_cargo_access,
    )
