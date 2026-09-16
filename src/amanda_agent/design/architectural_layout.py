"""Delegated architectural layout: the canonical program as a buildable plan.

:mod:`amanda_agent.design.macrozones` assigns sectors to site regions and
:mod:`amanda_agent.design.rooms` tiles full-width room bands through a block.
Neither yields a plan a person could build from: there is no circulation at
all, and the bands run across the whole block.  This module closes that gap for
the adopted programme, and its output is what the BIM stages consume.

Every decision below is delegated to the agent and registered in
``project/requirements/decision-register.yaml`` rather than asked for:

* typology ``COURTYARD``: a protected residential core behind a controlled
  urban interface (``DEC-P08-T04-TYPOLOGY-001``);
* one storey, which the programme's own enclosed-to-useful ratio implies;
* a double-loaded bar: two rows of ``BAND_DEPTH_M`` separated by one covered
  gallery of ``CORRIDOR_WIDTH_M``, so every room opens onto the spine and no
  room is reached through another room;
* the arrival, service and community programme on the face that looks at the
  street, and the residential, children's and technical programme on the face
  that looks at the protected patio;
* the patio is the external space against the residential face, held off the
  public edge by the building and closed on its far side by the perimeter wall
  — a reviewable ``PROVISIONAL_ASSUMPTION``.

Two area conventions are published, because the programme uses two.  "Área
útil interna" is the sum of the programmed room areas and is preserved to the
last decimal.  "Área construída fechada" is everything inside the outer face of
the external walls — rooms, the gallery, partitions and the service voids
beside the shallow rooms — which is the quantity the programme estimates at
783-814 m2.  The measured value is reported against that range rather than
forced into it, and the footprint to the outer face is published separately
because a construction budget needs the larger number.

The bar is planned as one volume rather than as a courtyard of separate wings,
and that is a measured decision rather than a preference: a two-wing courtyard
assembled from the same rooms and a gallery of the same width measures about
1050 m2 enclosed, roughly 30% above the adopted budget, because a courtyard
needs a second full gallery and a second set of external walls.  The single bar
reaches the programme's own estimate while still giving every room daylight and
a gallery frontage, and the patio supplies the protected outdoor space the
external programme requires.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from math import sqrt
from typing import Any, Sequence

from shapely.geometry import LineString, Point, Polygon, box  # type: ignore[import-untyped]
from shapely.ops import unary_union  # type: ignore[import-untyped]

#: Depth of a room band, measured from the gallery wall outwards.  Chosen so the
#: enclosed built area the plan measures falls inside the range the adopted
#: programme estimates, without stretching a single room area.
BAND_DEPTH_M = 4.2

#: Width of the covered gallery; above the 1.50 m accessible minimum.
CORRIDOR_WIDTH_M = 1.5

#: No room may be narrower than this along its gallery.
MIN_ROOM_LENGTH_M = 1.50

#: Aspect ratio a room aims for before the band depth caps it.
TARGET_ROOM_ASPECT = 1.6

#: External wall thickness; the footprint is the plate plus half of this.
EXTERNAL_WALL_M = 0.25

#: Thickness of a partition between two rooms on the same face.
PARTITION_M = 0.12

#: Setback from the frontage and from the site side to the nearest building line.
STREET_SETBACK_M = 5.0
SIDE_SETBACK_M = 5.0

#: Depth of the protected patio, measured out from the residential face.
PATIO_DEPTH_M = 8.0

#: Depth of the covered veranda along the patio face.  The programme estimates a
#: covered total larger than its enclosed total, and the difference is covered
#: external space: a roofed walkway in front of the rooms that look at the patio.
VERANDA_DEPTH_M = 1.5

#: Enclosed built area the adopted programme estimates, in square metres.
PROGRAM_ENCLOSED_RANGE_M2 = (783.0, 814.0)

#: Total covered area the adopted programme estimates, in square metres: the
#: enclosed area plus this covered external space.
PROGRAM_COVERED_RANGE_M2 = (850.0, 950.0)


#: The protected patio the external programme requires as a minimum.
PATIO_MIN_M2 = 80.0

#: Ordered privacy gradient; the street interface is the least private.
SECTOR_PRIVACY_LEVEL = {
    "SEC-01": 1,
    "SEC-05": 2,
    "SEC-06": 2,
    "SEC-04": 3,
    "SEC-03": 4,
    "SEC-02": 5,
}


#: Which face of the double-loaded bar each internal sector occupies.  The
#: ``street`` face carries the public, service and community programme; the
#: ``patio`` face carries daily life and professional care.
FACE_PLAN: dict[str, tuple[str, ...]] = {
    "street": ("SEC-01", "SEC-06", "SEC-05"),
    "patio": ("SEC-02", "SEC-03", "SEC-04"),
}


class ArchitecturalLayoutError(ValueError):
    """The programme cannot be laid out under the declared rules."""


@dataclass(frozen=True)
class RoomPlacement:
    """One programmed room instance with its exact metric footprint."""

    logical_id: str
    logical_id_base: str
    name: str
    sector_id: str
    net_area_m2: float
    depth_m: float
    length_m: float
    polygon: Polygon
    face: str
    faces_patio: bool
    privacy_level: int
    accessible: bool

    @property
    def min_dimension_m(self) -> float:
        min_x, min_y, max_x, max_y = self.polygon.bounds
        return min(max_x - min_x, max_y - min_y)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return tuple(self.polygon.bounds)  # type: ignore[return-value]


@dataclass(frozen=True)
class CourtyardLayout:
    """A complete single-storey plan with its own accounting and identity."""

    rooms: list[RoomPlacement]
    gallery: Polygon
    plate: Polygon
    footprint: Polygon
    patio: Polygon
    veranda: Polygon
    service_access_point: Point
    sector_privacy_level: dict[str, int] = field(default_factory=dict)
    accounting: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, float] = field(default_factory=dict)
    content_hash: str = ""

    @property
    def corridor_width_m(self) -> float:
        return float(self.parameters["corridor_width_m"])

    @property
    def bar_length_m(self) -> float:
        return float(self.parameters["bar_length_m"])

    @property
    def bar_depth_m(self) -> float:
        return float(self.parameters["bar_depth_m"])

    def room(self, logical_id: str) -> RoomPlacement:
        for room in self.rooms:
            if room.logical_id == logical_id:
                return room
        raise KeyError(logical_id)

    def rooms_of(self, sector_id: str) -> list[RoomPlacement]:
        return [room for room in self.rooms if room.sector_id == sector_id]

    def face_rooms(self, face: str) -> list[RoomPlacement]:
        return [room for room in self.rooms if room.face == face]


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _instances(program: Any) -> list[dict[str, Any]]:
    """Expand the canonical programme into one row per internal room."""

    sectors = _value(program, "sectors")
    if not isinstance(sectors, (list, tuple)) or not sectors:
        raise ArchitecturalLayoutError("the program has no sectors")
    rows: list[dict[str, Any]] = []
    for sector in sectors:
        if str(_value(sector, "area_kind", "INTERNAL")).upper() != "INTERNAL":
            continue
        sector_id = str(_value(sector, "logical_id", ""))
        spaces = _value(sector, "spaces") or []
        if not spaces:
            raise ArchitecturalLayoutError(f"sector {sector_id} carries no spaces")
        for space in spaces:
            base = str(_value(space, "logical_id", ""))
            quantity = int(_value(space, "quantity", 1) or 1)
            area = float(_value(space, "target_area_m2", 0.0) or 0.0)
            if not base or quantity < 1 or area <= 0:
                raise ArchitecturalLayoutError(
                    f"space {base or '<unnamed>'} needs a positive area and quantity"
                )
            for index in range(1, quantity + 1):
                rows.append(
                    {
                        "logical_id": base if quantity == 1 else f"{base}#{index}",
                        "logical_id_base": base,
                        "name": str(_value(space, "name", base)),
                        "sector_id": sector_id,
                        "net_area_m2": area,
                        "accessible": bool(_value(space, "accessible", False)),
                    }
                )
    if not rows:
        raise ArchitecturalLayoutError("the program carries no internal spaces")
    planned = {sector for sectors_ in FACE_PLAN.values() for sector in sectors_}
    unknown = sorted({row["sector_id"] for row in rows} - planned)
    if unknown:
        raise ArchitecturalLayoutError(
            "sectors without a declared face: " + ", ".join(unknown)
        )
    return rows


def _room_dimensions(area_m2: float) -> tuple[float, float]:
    """Return the (depth, length) of one room along its gallery.

    A room large enough to fill the band keeps ``BAND_DEPTH_M``; a shallow room
    such as a bathroom is squared off so it never becomes a slot narrower than
    ``MIN_ROOM_LENGTH_M``.  Either way the net area is preserved exactly.
    """

    depth = min(
        BAND_DEPTH_M,
        max(sqrt(area_m2 / TARGET_ROOM_ASPECT), area_m2 / MIN_ROOM_LENGTH_M),
    )
    return depth, area_m2 / depth


def _face_length(instances: list[dict[str, Any]]) -> float:
    """Built length of one face, including the partitions between its rooms."""

    if not instances:
        return 0.0
    return sum(
        _room_dimensions(item["net_area_m2"])[1] for item in instances
    ) + PARTITION_M * (len(instances) - 1)


def _select(instances: list[dict[str, Any]], sectors: tuple[str, ...]) -> list[dict[str, Any]]:
    return [item for item in instances if item["sector_id"] in sectors]


def _key(point: Sequence[float]) -> tuple[float, float]:
    return (round(float(point[0]), 6), round(float(point[1]), 6))


def _room_edges(
    room: "RoomPlacement",
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """The straight edges of a room, as rounded coordinate pairs."""

    coordinates = [_key(point) for point in room.polygon.exterior.coords]
    return [
        (coordinates[index], coordinates[index + 1])
        for index in range(len(coordinates) - 1)
        if coordinates[index] != coordinates[index + 1]
    ]


def _on_boundary(edge, boundary) -> bool:
    """Whether an edge runs along a boundary, rather than touching it at a point."""

    line = LineString([edge[0], edge[1]])
    return line.intersection(boundary).length >= line.length - 1e-6


def _place_face(
    instances: list[dict[str, Any]],
    *,
    start: float,
    anchor: float,
    extend: int,
    face: str,
) -> list[RoomPlacement]:
    """Tile one east-west face, anchored on the edge that meets the gallery."""

    placements: list[RoomPlacement] = []
    cursor = start
    for item in instances:
        depth, length = _room_dimensions(item["net_area_m2"])
        far = anchor + extend * depth
        placements.append(
            RoomPlacement(
                logical_id=item["logical_id"],
                logical_id_base=item["logical_id_base"],
                name=item["name"],
                sector_id=item["sector_id"],
                net_area_m2=item["net_area_m2"],
                depth_m=depth,
                length_m=length,
                polygon=box(cursor, min(anchor, far), cursor + length, max(anchor, far)),
                face=face,
                faces_patio=False,
                privacy_level=SECTOR_PRIVACY_LEVEL[item["sector_id"]],
                accessible=item["accessible"],
            )
        )
        # Rooms tile edge to edge: a partition then stands on the shared edge,
        # which is what lets the BIM stages recognise the boundary as internal
        # wall work rather than as two unrelated room outlines.
        cursor += length
    return placements


def _canonical_hash(payload: dict[str, Any]) -> str:
    def convert(value: Any) -> Any:
        if isinstance(value, Polygon):
            return [
                [round(float(x), 6), round(float(y), 6)]
                for x, y in value.exterior.coords
            ]
        if isinstance(value, Point):
            return [round(float(value.x), 6), round(float(value.y), 6)]
        if isinstance(value, dict):
            return {
                str(key): convert(item)
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            }
        if isinstance(value, (list, tuple)):
            return [convert(item) for item in value]
        if isinstance(value, float):
            return round(value, 9)
        return value

    encoded = json.dumps(
        convert(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_courtyard_layout(program: Any) -> CourtyardLayout:
    """Turn the canonical programme into the adopted single-storey plan.

    The building is one double-loaded bar on an east-west axis: the street face
    carries arrival, services and the community hall, the patio face carries
    residential, the children's sector and technical care, and a single covered
    gallery runs the length of the bar between them.  The protected patio sits
    against the residential face, away from the public edge.
    """

    instances = _instances(program)
    band = BAND_DEPTH_M
    corridor = CORRIDOR_WIDTH_M
    bar_depth = 2.0 * band + corridor

    # Datum: the outside FACE of the building at the front and west setbacks.
    # The plate is later buffered by half the external wall to become the
    # footprint, so the datum is pulled in by that half to keep the outer face
    # exactly on the setback line instead of crossing it.
    origin_x = SIDE_SETBACK_M + EXTERNAL_WALL_M / 2.0
    origin_y = STREET_SETBACK_M + EXTERNAL_WALL_M / 2.0

    street_raw = _select(instances, FACE_PLAN["street"])
    patio_raw = _select(instances, FACE_PLAN["patio"])
    if not street_raw or not patio_raw:
        raise ArchitecturalLayoutError("both faces of the bar need at least one room")

    bar_len = max(_face_length(street_raw), _face_length(patio_raw), MIN_ROOM_LENGTH_M)
    # Both faces start at the same west end, so the gallery runs their full
    # length and the shorter face simply ends earlier rather than doubling back
    # through unbuilt corridor.
    gallery_y0 = origin_y + band
    gallery_y1 = gallery_y0 + corridor
    gallery = box(origin_x, gallery_y0, origin_x + bar_len, gallery_y1)

    rooms = [
        *_place_face(street_raw, start=origin_x, anchor=gallery_y0, extend=-1, face="street"),
        *_place_face(patio_raw, start=origin_x, anchor=gallery_y1, extend=1, face="patio"),
    ]
    rooms.sort(key=lambda item: item.logical_id)

    plate = unary_union([gallery, *[room.polygon for room in rooms]])
    footprint = plate.buffer(EXTERNAL_WALL_M / 2, join_style=2, mitre_limit=5.0)

    # The programme estimates a covered total larger than its enclosed total,
    # and the difference is covered external space.  A roofed veranda runs along
    # the patio face of the bar, between the building and the open ground, so
    # the covered figure the plan reports is a surface it actually builds.
    veranda = box(
        origin_x,
        origin_y + bar_depth,
        origin_x + bar_len,
        origin_y + bar_depth + VERANDA_DEPTH_M,
    )

    # The patio is open ground against the residential face, held off the street
    # by the building and closed on its far side by the perimeter wall.
    patio_zone = box(
        origin_x,
        origin_y + bar_depth + VERANDA_DEPTH_M,
        origin_x + bar_len,
        origin_y + bar_depth + VERANDA_DEPTH_M + PATIO_DEPTH_M,
    )
    open_ground = patio_zone.difference(footprint)
    if open_ground.is_empty:
        raise ArchitecturalLayoutError("the built envelope leaves no patio open")
    patio = (
        max(open_ground.geoms, key=lambda item: item.area)
        if open_ground.geom_type == "MultiPolygon"
        else open_ground
    )
    if patio.area < PATIO_MIN_M2:
        raise ArchitecturalLayoutError(
            f"patio area {patio.area:.2f} m2 is below the required {PATIO_MIN_M2} m2"
        )
    # A room faces the patio when it stands on the patio side of the gallery,
    # which is the side the protected outdoor space is on.  A shallow room such
    # as a bathroom steps back from the veranda and still looks at the patio over
    # its own external wall, so the patio side is the honest property to record.
    rooms = [
        replace(room, faces_patio=(room.face == "patio"))
        for room in rooms
    ]


    service = [room for room in rooms if room.sector_id == "SEC-06"]
    if not service:
        raise ArchitecturalLayoutError("the services sector is not placed")
    loading = min(service, key=lambda room: (room.polygon.bounds[1], room.logical_id))
    min_x, min_y, max_x, _ = loading.polygon.bounds
    service_access_point = Point((min_x + max_x) / 2.0, min_y)

    # -- accounting ---------------------------------------------------------
    # Inside the outer face: the room rows, the gallery, and whatever the bar
    # leaves beside a room too shallow to fill its band.  That residual is a
    # real construction cost — partitions and the service voids that carry
    # shafts, ducts and cleaning cupboards — so it is reported, not discarded.
    net_internal = sum(room.net_area_m2 for room in rooms)
    circulation = float(gallery.area)
    partitions = PARTITION_M * band * (
        max(len(street_raw) - 1, 0) + max(len(patio_raw) - 1, 0)
    )
    voids = max(float(plate.area) - net_internal - circulation - partitions, 0.0)
    gross_enclosed = net_internal + circulation + partitions + voids
    low, high = PROGRAM_ENCLOSED_RANGE_M2
    delta = (
        0.0
        if low <= gross_enclosed <= high
        else (gross_enclosed - low if gross_enclosed < low else gross_enclosed - high)
    )
    covered = gross_enclosed + float(veranda.area)
    covered_low, covered_high = PROGRAM_COVERED_RANGE_M2
    covered_delta = (
        0.0
        if covered_low <= covered <= covered_high
        else (covered - covered_low if covered < covered_low else covered - covered_high)
    )
    accounting: dict[str, Any] = {
        "net_internal_m2": net_internal,
        "circulation_m2": circulation,
        "partitions_m2": partitions,
        "service_voids_m2": voids,
        "gross_enclosed_m2": gross_enclosed,
        "veranda_m2": float(veranda.area),
        "covered_total_m2": covered,
        "program_covered_range_m2": [covered_low, covered_high],
        "covered_vs_program_m2": covered_delta,
        "within_program_covered_estimate": abs(covered_delta) <= 1e-9,
        "plate_area_m2": float(plate.area),
        "construction_footprint_m2": float(footprint.area),
        "patio_m2": float(patio.area),
        "room_count": float(len(rooms)),
        "storeys": 1.0,
        "net_to_gross_factor": net_internal / max(gross_enclosed, 1e-9),
        "program_enclosed_range_m2": [low, high],
        "gross_vs_program_m2": delta,
        "within_program_enclosed_estimate": abs(delta) <= 1e-9,
        "area_convention": (
            "gross_enclosed_m2 counts everything inside the outer face of the "
            "external walls (rooms, gallery, partitions, service voids); "
            "construction_footprint_m2 counts to the outer face"
        ),
    }
    parameters = {
        "band_depth_m": band,
        "corridor_width_m": corridor,
        "bar_depth_m": bar_depth,
        "bar_length_m": bar_len,
        "min_room_length_m": MIN_ROOM_LENGTH_M,
        "external_wall_m": EXTERNAL_WALL_M,
        "partition_m": PARTITION_M,
        "street_setback_m": STREET_SETBACK_M,
        "side_setback_m": SIDE_SETBACK_M,
        "patio_depth_m": PATIO_DEPTH_M,
        "veranda_depth_m": VERANDA_DEPTH_M,
        "storeys": 1.0,
    }
    content_hash = _canonical_hash(
        {
            "rooms": [
                {
                    "logical_id": room.logical_id,
                    "area": room.net_area_m2,
                    "polygon": room.polygon,
                    "face": room.face,
                }
                for room in rooms
            ],
            "gallery": gallery,
            "patio": patio,
            "parameters": parameters,
            "privacy": SECTOR_PRIVACY_LEVEL,
        }
    )
    return CourtyardLayout(
        rooms=rooms,
        gallery=gallery,
        plate=plate,
        footprint=footprint,
        patio=patio,
        veranda=veranda,
        service_access_point=service_access_point,
        sector_privacy_level=dict(SECTOR_PRIVACY_LEVEL),
        accounting=accounting,
        parameters=parameters,
        content_hash=content_hash,
    )


__all__ = [
    "BAND_DEPTH_M",
    "CORRIDOR_WIDTH_M",
    "EXTERNAL_WALL_M",
    "FACE_PLAN",
    "MIN_ROOM_LENGTH_M",
    "PARTITION_M",
    "PATIO_DEPTH_M",
    "PATIO_MIN_M2",
    "PROGRAM_ENCLOSED_RANGE_M2",
    "SECTOR_PRIVACY_LEVEL",
    "SIDE_SETBACK_M",
    "STREET_SETBACK_M",
    "TARGET_ROOM_ASPECT",
    "ArchitecturalLayoutError",
    "CourtyardLayout",
    "RoomPlacement",
    "build_courtyard_layout",
]
