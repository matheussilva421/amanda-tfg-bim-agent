"""Bind the delegated architectural layout to the BIM stage vocabulary.

The BIM compiler can plan R01-R13, but nothing in the repository turned a real
plan into those stages: the design engine stops at macrozone strips, so no
wall, opening, room or sheet could be described.  This module is that bridge.

It is a pure function.  It reads the canonical programme and the layout the
agent decided, and it returns stage plans in the documented order.  It never
contacts Revit, never promotes a capability, and never plans an operation the
capability registry cannot prove for the exact build and tool schema: a missing
capability raises instead of being approximated, so a bug here cannot become a
silent compromise in the model.

Geometry follows the layout exactly.  Walls are the outer envelope of the
assembled plate plus the partitions between neighbouring rooms, which is also
where doors are cut; windows sit on outer faces of habitable rooms; rooms carry
the programmed areas; landscape carries the external programme; documentation
carries the views, schedules and sheets the deliverable asks for.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
import hashlib
import json
from math import hypot
from pathlib import Path
from typing import Any

from shapely.geometry import LineString, Polygon  # type: ignore[import-untyped]

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import ExecutionMode, PreflightRequest, StageOperation
from amanda_agent.bim.stages import accessibility as accessibility_stage
from amanda_agent.bim.stages import documentation as documentation_stage
from amanda_agent.bim.stages import furniture as furniture_stage
from amanda_agent.bim.stages import landscape as landscape_stage
from amanda_agent.bim.stages import layout as layout_stage
from amanda_agent.bim.stages import levels as levels_stage
from amanda_agent.bim.stages import massing as massing_stage
from amanda_agent.bim.stages import materials as materials_stage
from amanda_agent.bim.stages import openings as openings_stage
from amanda_agent.bim.stages import project as project_stage
from amanda_agent.bim.stages import rooms as rooms_stage
from amanda_agent.bim.stages import shell as shell_stage
from amanda_agent.bim.stages import site as site_stage
from amanda_agent.design.architectural_layout import CourtyardLayout, RoomPlacement
from amanda_agent.models.capability import CapabilityRegistry
from amanda_agent.site.models import (
    BoundaryKind,
    BoundaryPolygon,
    SiteModel,
    SourceTopographyState,
    Topography,
    TopographyRepresentation,
)

#: Height of the single storey, to the underside of the roof structure.
FLOOR_HEIGHT_M = 3.20

#: Wall thicknesses.  The external figure matches the layout envelope band.
EXTERNAL_WALL_M = 0.25
PARTITION_M = 0.12

#: Door and window modules used by the plan.
DOOR_WIDTH_M = 1.00
DOOR_HEIGHT_M = 2.10
WINDOW_WIDTH_M = 1.20
WINDOW_HEIGHT_M = 1.20
WINDOW_SILL_M = 0.90

#: Rooms smaller than this take no separate window of their own; they are
#: served as part of the room group they belong to in the plan.
WINDOW_MIN_ROOM_M2 = 8.0

GALLERY = "GALLERY"

#: Where Revit 2027 installs its project templates on this machine.  The
#: installer puts them in ProgramData, not beside the executable, so the
#: discovery helper in the project stage cannot find them by itself.
DEFAULT_TEMPLATE_ROOTS: tuple[Path, ...] = (
    Path(r"C:\ProgramData\Autodesk\RVT 2027\Templates"),
)

#: The Brazilian Portuguese architectural template of the installed build.
DEFAULT_TEMPLATE_NAME = "Default_M_PTB.rte"

#: The level the plan builds on.  It is the logical id the level carries in the
#: model, which is what the bridge resolves a level reference against.
LEVEL_LOGICAL_ID = "LEVEL-01"

#: The wall types the installed Brazilian template ships, as the ElementIds the
#: model reports for them.  The layout decides thicknesses (250 mm external,
#: 138 mm internal partition) and these are the matching template types, read
#: from the model rather than invented.  The id form is used because a type
#: reference is resolved by the bridge against an instance listing, which cannot
#: hold a type, so resolving a name there always finds nothing.
EXTERNAL_WALL_TYPE_ID = 250  # "Genérico - 250 mm"
INTERNAL_WALL_TYPE_ID = 220  # "Interior - 138 mm Divisória (1-hr)"

#: Operations that Revit refuses unless they name their level.
_NEEDS_LEVEL = (
    "revit.create_wall",
    "revit.create_floor",
    "revit.create_slab",
    "revit.create_roof",
    "revit.create_internal_wall",
    "revit.create_room",
    "revit.create_opening",
)

_STAGE_ORDER: tuple[BimStage, ...] = (
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

_REQUIRED_OPERATIONS: dict[BimStage, tuple[str, ...]] = {
    BimStage.R01: ("revit.create_project",),
    BimStage.R02: (),
    BimStage.R03: (
        "revit.create_level",
        "revit.create_grid",
        "revit.create_reference",
    ),
    BimStage.R04: ("revit.create_mass",),
    BimStage.R05: (
        "revit.create_wall",
        "revit.create_floor",
        "revit.create_slab",
        "revit.create_roof",
    ),
    BimStage.R06: ("revit.create_internal_wall",),
    BimStage.R07: ("revit.create_opening",),
    BimStage.R08: ("revit.create_room",),
    BimStage.R09: ("revit.create_accessibility_element",),
    BimStage.R10: ("revit.create_furniture_element",),
    BimStage.R11: ("revit.create_landscape_element",),
    BimStage.R12: ("revit.assign_material",),
    BimStage.R13: ("revit.create_documentation_element",),
}


class ProductionBimError(RuntimeError):
    """The production chain cannot be planned under the current evidence."""


@dataclass(frozen=True)
class _Wall:
    """One planned wall, in layout coordinates."""

    logical_id: str
    start: tuple[float, float]
    end: tuple[float, float]
    thickness_m: float
    kind: str
    rooms: tuple[str, ...]
    exterior: bool
    on_gallery: bool = False

    @property
    def length_m(self) -> float:
        return hypot(self.end[0] - self.start[0], self.end[1] - self.start[1])

    @property
    def midpoint(self) -> tuple[float, float]:
        return (
            (self.start[0] + self.end[0]) / 2.0,
            (self.start[1] + self.end[1]) / 2.0,
        )


def layout_stage_order() -> tuple[BimStage, ...]:
    """Return the stage progression the driver plans, in order."""

    return _STAGE_ORDER


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def _key(point: Sequence[float]) -> tuple[float, float]:
    return (round(float(point[0]), 6), round(float(point[1]), 6))


def _ordered(a: tuple[float, float], b: tuple[float, float]):
    return (a, b) if a <= b else (b, a)


def _edge_digest(a: tuple[float, float], b: tuple[float, float]) -> str:
    """The digest the BIM stages use for a wall edge.

    The shell stage derives each wall's logical_id from its endpoint pair, so
    the driver has to derive the same identifier for the same edge.  Using a
    different scheme would give a door a host name that no wall in the model
    carries, and the write would fail on a real building.
    """

    first, second = _ordered(_key(a), _key(b))
    payload = json.dumps([list(first), list(second)], separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _wall_id(prefix: str, a: tuple[float, float], b: tuple[float, float]) -> str:
    return "%s-%s" % (prefix, _edge_digest(a, b))


def _producer_wall_id(
    *,
    start: tuple[float, float],
    end: tuple[float, float],
    rooms: tuple[str, ...],
    on_gallery: bool,
    exterior: bool,
) -> str:
    """Return the logical id owned by the stage that creates this wall.

    R05 creates the shell wall namespace, including faces exposed to the
    gallery.  R06 owns only shared boundaries between two rooms.  Consumers
    must use those producer namespaces verbatim because the provider resolves
    logical references by exact string equality.
    """

    prefix = "LAYOUT-WALL" if not exterior and len(rooms) > 1 and not on_gallery else "WALL"
    return _wall_id(prefix, start, end)


def _edges(polygon: Polygon) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    coordinates = [_key(point) for point in polygon.exterior.coords]
    return [
        (coordinates[index], coordinates[index + 1])
        for index in range(len(coordinates) - 1)
        if coordinates[index] != coordinates[index + 1]
    ]


def _on_boundary(edge, boundary) -> bool:
    """Whether an edge runs along a boundary rather than touching it at a point."""

    line = LineString([edge[0], edge[1]])
    return line.intersection(boundary).length >= line.length - 1e-6


def _merge_collinear(walls: list[_Wall]) -> list[_Wall]:
    """Merge wall runs that lie on the same line and overlap.

    Two rooms whose faces step by a few centimetres put two exterior walls on
    the same line, and Revit joins them into a T that it then warns about as an
    overlap and refuses to verify.  Merging the runs into one wall is the same
    boundary stated once, and it is what a person would model.
    """

    merged: list[_Wall] = []
    used = [False] * len(walls)
    ordered = sorted(walls, key=lambda wall: wall.logical_id)
    for index, first in enumerate(ordered):
        if used[index]:
            continue
        group = [first]
        used[index] = True
        changed = True
        while changed:
            changed = False
            for other_index in range(index + 1, len(ordered)):
                if used[other_index]:
                    continue
                other = ordered[other_index]
                if other.kind != first.kind or other.thickness_m != first.thickness_m:
                    continue
                if any(
                    _same_line(existing, other) and _runs_overlap(existing, other)
                    for existing in group
                ):
                    group.append(other)
                    used[other_index] = True
                    changed = True
        if len(group) == 1:
            merged.append(first)
            continue
        points = [point for wall in group for point in (wall.start, wall.end)]
        # The constant coordinate identifies the line; the other coordinate
        # is the interval that can be merged.  Using the constant coordinate
        # here creates zero-length walls and diverges from the shell stage.
        varying_axis = (
            1 if abs(first.start[0] - first.end[0]) < 1e-6 else 0
        )
        low = min(point[varying_axis] for point in points)
        high = max(point[varying_axis] for point in points)
        fixed = first.start[1 - varying_axis]
        start = (fixed, low) if varying_axis == 1 else (low, fixed)
        end = (fixed, high) if varying_axis == 1 else (high, fixed)
        rooms = tuple(sorted({room for wall in group for room in wall.rooms}))
        on_gallery = any(wall.on_gallery for wall in group)
        merged.append(
            _Wall(
                logical_id=_producer_wall_id(
                    start=start,
                    end=end,
                    rooms=rooms,
                    on_gallery=on_gallery,
                    exterior=first.exterior,
                ),
                start=start,
                end=end,
                thickness_m=first.thickness_m,
                kind=first.kind,
                rooms=rooms,
                exterior=first.exterior,
                on_gallery=on_gallery,
            )
        )
    merged.sort(key=lambda wall: wall.logical_id)
    return merged


def _same_line(first: _Wall, second: _Wall) -> bool:
    for axis in (0, 1):
        if (
            abs(first.start[axis] - first.end[axis]) < 1e-6
            and abs(second.start[axis] - second.end[axis]) < 1e-6
            and abs(first.start[axis] - second.start[axis]) < 1e-6
        ):
            return True
    return False


def _runs_overlap(first: _Wall, second: _Wall) -> bool:
    if abs(first.start[0] - first.end[0]) < 1e-6:
        axis = 1
    else:
        axis = 0
    first_low, first_high = sorted((first.start[axis], first.end[axis]))
    second_low, second_high = sorted((second.start[axis], second.end[axis]))
    return second_low < first_high - 1e-6 and first_low < second_high - 1e-6


def build_walls(layout: CourtyardLayout) -> tuple[list[_Wall], list[_Wall]]:
    """Return the exterior envelope and the partitions of a plan.

    A wall is keyed on coordinates a room actually has, not on the buffered
    outline: the envelope is a drawing offset that no room reaches, and keying
    on it would leave every outer face unmatched.  An outer face is an edge
    held by exactly one room that does not front the gallery, which is the same
    thing as the boundary of the assembly without depending on whether a float
    comparison of two unioned outlines happens to agree.
    """

    gallery_boundary = layout.gallery.boundary
    owners: dict[tuple[tuple[float, float], tuple[float, float]], list[str]] = {}
    on_gallery: set[tuple[tuple[float, float], tuple[float, float]]] = set()
    for room in layout.rooms:
        for edge in _edges(room.polygon):
            key = _ordered(*edge)
            owners.setdefault(key, []).append(room.logical_id)
            if _on_boundary(key, gallery_boundary):
                on_gallery.add(key)

    exterior: list[_Wall] = []
    partitions: list[_Wall] = []
    for key, room_ids in sorted(owners.items()):
        shared = len(room_ids) > 1
        gallery_frontage = key in on_gallery
        if not shared and not gallery_frontage:
            exterior.append(
                _Wall(
                    logical_id=_wall_id("WALL", key[0], key[1]),
                    start=key[0],
                    end=key[1],
                    thickness_m=EXTERNAL_WALL_M,
                    kind="external",
                    rooms=tuple(room_ids),
                    exterior=True,
                )
            )
            continue
        partitions.append(
            _Wall(
                logical_id=_producer_wall_id(
                    start=key[0],
                    end=key[1],
                    rooms=tuple(room_ids),
                    on_gallery=gallery_frontage,
                    exterior=False,
                ),
                start=key[0],
                end=key[1],
                thickness_m=PARTITION_M,
                kind="internal",
                rooms=tuple(room_ids),
                exterior=False,
                on_gallery=gallery_frontage,
            )
        )
    exterior.sort(key=lambda wall: wall.logical_id)
    gallery_partitions = [wall for wall in partitions if wall.on_gallery]
    shared_partitions = [wall for wall in partitions if not wall.on_gallery]
    # R05 owns the gallery frontage and applies the same collinear merge as the
    # shell stage.  R06 owns each shared room boundary as an individual element;
    # preserving those exact segments keeps its LAYOUT-WALL ids referentially
    # stable for later material assignments.
    merged_partitions = [
        *_merge_collinear(gallery_partitions),
        *shared_partitions,
    ]
    merged_partitions.sort(key=lambda wall: wall.logical_id)
    return _merge_collinear(exterior), merged_partitions


def _request(
    stage,
    *,
    registry,
    revit_build,
    tool_schema_hash,
    generation_run,
    mode,
    required=(),
    solution=None,
    site=None,
    expected_approval_hash=None,
):
    merged = []
    for operation in (*_REQUIRED_OPERATIONS.get(stage, ()), *required):
        if operation not in merged:
            merged.append(operation)
    selected_inputs = {"generation_run": generation_run}
    expected_inputs = {"generation_run": generation_run}
    if solution is not None:
        # Detailed BIM must select the versions the approved solution pinned.
        selected_inputs.update(
            {
                "requirements_version": solution.requirements_version,
                "site_version": str(solution.site_version),
                "engine_version": solution.engine_version,
            }
        )
        expected_inputs.update(selected_inputs)
    return PreflightRequest(
        mode=mode,
        stage=stage,
        registry=registry,
        revit_build=revit_build,
        tool_schema_hash=tool_schema_hash,
        expected_build=revit_build,
        expected_tool_schema_hash=tool_schema_hash,
        selected_inputs=selected_inputs,
        expected_inputs=expected_inputs,
        required_operations=tuple(merged),
        solution=solution,
        site=site,
        expected_approval_hash=expected_approval_hash,
        generation_run=generation_run,
    )


def _site_model(layout):
    """A study site the stages can carry; the boundary is explicitly planar."""

    bounds = layout.footprint.bounds
    margin = 12.0
    ring = [
        (bounds[0] - margin, bounds[1] - margin),
        (bounds[2] + margin, bounds[1] - margin),
        (bounds[2] + margin, bounds[3] + margin),
        (bounds[0] - margin, bounds[3] + margin),
        (bounds[0] - margin, bounds[1] - margin),
    ]
    return SiteModel(
        site_version=1,
        boundary=BoundaryPolygon(
            kind=BoundaryKind.STUDY_PLACEHOLDER, coordinates=ring
        ),
        topography=Topography(
            source_state=SourceTopographyState.MISSING,
            representation=TopographyRepresentation.PLANAR_PLACEHOLDER,
        ),
    )


def _plan_r01(request, *, template_root):
    template = find_project_template(template_root)
    if template is None:
        raise ProductionBimError(
            "no installed Revit project template was found; R01 cannot be planned "
            "without a real template to copy"
        )
    return project_stage.plan_project_initialization(
        request,
        template_roots=(template.parent,),
        project_code="AMANDA",
    )


def _template_roots(template_root):
    """Return the template folders to search, most specific first.

    An explicit root wins; otherwise the installed Revit template folder is
    searched, because the project stage only looks beside the executable and the
    installer keeps the templates in ProgramData.
    """

    roots = []
    if template_root is not None:
        roots.append(Path(template_root))
    roots.extend(DEFAULT_TEMPLATE_ROOTS)
    return tuple(roots)


def find_project_template(template_root=None):
    """Return the installed project template this build should start from."""

    for root in _template_roots(template_root):
        candidate = Path(root) / DEFAULT_TEMPLATE_NAME
        if candidate.is_file():
            return candidate
    for root in _template_roots(template_root):
        base = Path(root)
        if not base.is_dir():
            continue
        matches = sorted(base.glob("*.rte"))
        if matches:
            return matches[0]
    return None


def _plan_r02(request, layout):
    request = request.model_copy(update={"site": _site_model(layout)})
    return site_stage.plan_site_stage(request)


def _plan_r03(request, layout):
    bounds = layout.footprint.bounds
    storeys = int(layout.parameters["storeys"])
    if storeys != 1:
        raise ProductionBimError(
            "the delegated layout is single storey; R03 will not invent a second "
            "level for a storey the plan does not contain"
        )
    level = levels_stage.LevelReference(
        logical_id="LEVEL-01",
        # A level is read back by the name it carries in the model, so the name
        # is the logical id.  A display name such as "Térreo" would be matched
        # against nothing and the write would be reported as unverified.
        name="LEVEL-01",
        elevation_m=0.0,
        evidence=[
            "the adopted layout is single storey by construction "
            "(architectural_layout parameters storeys=1) and places every room on "
            "level 0, so this level exists in verified design data",
            "the elevation 0.0 is the local project origin, NOT a surveyed "
            "elevation: no topographic source exists for this lot",
        ],
        source_kind="VERIFIED_SOURCE",
    )
    grids = [
        levels_stage.GridAxis(
            logical_id=name,
            # Same contract as the level: the grid's name in the model is what
            # the independent read matches, so the logical id travels as the
            # name and a letter alone would not identify it.
            name=name,
            start=(position, bounds[1]),
            end=(position, bounds[3]),
            assumption="PROVISIONAL_ASSUMPTION",
        )
        for name, position in (
            ("GRID-01", bounds[0]),
            ("GRID-02", bounds[2]),
        )
    ]
    # A project-origin reference plane is deliberately NOT planned yet.
    #
    # Measured against the installed contract (Horizun 1.3.3, build 27.2.0.39):
    # the create_reference python route commits the plane but returns
    # host_verified=false with evidence_status "completed_unverified", and
    # horizun_query_model answers OST_ReferencePlanes with no matched_total at
    # all, so there is no independent read that could verify it.  Planning it
    # anyway would either fail the stage on a missing read or force the
    # verification contract to be weakened, and a write nobody can re-read is
    # exactly what this project refuses to call verified.
    #
    # It is not needed for the architecture: the level datum at 0.00 is carried
    # by LEVEL-01, which is written and independently re-read.  The origin plane
    # returns when the contract can query it.
    return levels_stage.plan_levels_stage(
        request, levels=[level], grids=grids, references=[]
    )


def _plan_r04(request, layout):
    # The footprint polygon repeats its first point to close the ring, and the
    # massing script closes the loop itself by wrapping to index 0.  Passing the
    # repeated point would append a zero-length line, which Revit refuses with
    # "Curve length is too small for Revit's tolerance", so the duplicate is
    # dropped here.
    ring = [
        (float(x), float(y)) for x, y in layout.footprint.exterior.coords[:-1]
    ]
    blocks = [
        massing_stage.MassingBlock(
            logical_id="MASS-01",
            # The independent read matches a created element by the name it
            # carries in the model, so the name is the logical id.  A display
            # name would leave the mass unverifiable, exactly as it did for the
            # level and the grids.
            name="MASS-01",
            footprint=ring,
            base_elevation_m=0.0,
            height_m=FLOOR_HEIGHT_M + 0.30,
            source_area_m2=float(layout.footprint.area),
        )
    ]
    return massing_stage.plan_massing_stage(request, blocks=blocks)


def _plan_r05(request, layout):
    ring = [[x, y] for x, y in layout.footprint.exterior.coords]
    loops = [{"type": "Polygon", "coordinates": [ring]}]
    # The covered external walkway is part of the shell, not a linked model, so
    # it travels as an extra slab loop.  The roof spans it too, which is what
    # makes the covered total the plan reports a surface the model contains.
    veranda_ring = [[float(x), float(y)] for x, y in layout.veranda.exterior.coords]
    roof_ring = [
        [float(x), float(y)]
        for x, y in layout.plate.union(layout.veranda).buffer(
            EXTERNAL_WALL_M / 2, join_style=2, mitre_limit=5.0
        ).exterior.coords
    ]
    roof = {
        "geometry": {"type": "Polygon", "coordinates": [roof_ring]},
        "type": "single-storey-flat",
        "elevation_m": FLOOR_HEIGHT_M,
        "covers_veranda": True,
    }
    return shell_stage.plan_shell_stage(
        request,
        layout.rooms,
        gross_shell=layout.footprint,
        floor_loops=loops,
        slab_loops=[*loops, {"type": "Polygon", "coordinates": [veranda_ring]}],
        roof=roof,
        # The wall type is a template asset, so the plan names the ones this
        # installed template actually carries.  The ids are written as decimal
        # strings because the stage catalog is typed as text, and the provider
        # translation turns a numeric string back into the integer ElementId it
        # resolves directly.
        wall_types={
            "external": str(EXTERNAL_WALL_TYPE_ID),
            "internal": str(INTERNAL_WALL_TYPE_ID),
        },
        # These are real ids read off the installed template, and the stage asks
        # a caller that supplies real types to say where they came from.
        wall_type_source=(
            "read from the installed template Default_M_PTB.rte on Revit 2027 "
            "build 27.2.0.39: element 250 is 'Generico - 250 mm', element 220 is "
            "'Interior - 138 mm Divisoria (1-hr)'"
        ),
    )


def _plan_r06(request, layout):
    return layout_stage.plan_layout_stage(
        request, layout.rooms, wall_thickness_m=PARTITION_M
    )


def _diagonal_corners(wall, properties):
    """A diagonal corner pair for one opening, in metres.

    The bridge builds a rectangular opening from two corners that must differ in
    height, so the pair spans the opening's own width along the wall and its own
    height above the sill.
    """

    width = float(properties["clear_width_m"])
    sill = float(properties["sill_m"])
    height = float(properties["height_m"])
    length = wall.length_m
    if length <= 0:
        raise ProductionBimError("wall %s has no length" % wall.logical_id)
    ux = (wall.end[0] - wall.start[0]) / length
    uy = (wall.end[1] - wall.start[1]) / length
    half = min(width, max(length - 1e-3, 1e-3)) / 2.0
    middle = length / 2.0
    near = [
        wall.start[0] + ux * (middle - half),
        wall.start[1] + uy * (middle - half),
        sill,
    ]
    far = [
        wall.start[0] + ux * (middle + half),
        wall.start[1] + uy * (middle + half),
        sill + height,
    ]
    return {"corner_1": near, "corner_2": far}


def _gallery_host(room, by_id):
    for edge in _edges(room.polygon):
        candidate = by_id.get(_wall_id("WALL", edge[0], edge[1]))
        if candidate is not None and candidate.on_gallery:
            return candidate
    return None


def _exterior_host(room, by_id):
    for edge in _edges(room.polygon):
        candidate = by_id.get(_wall_id("WALL", edge[0], edge[1]))
        if candidate is not None and candidate.exterior:
            return candidate
    return None


def _host_records(walls):
    """Present the planned walls to the openings stage as hostable records.

    The stage only accepts a host that declares itself a WALL, and it reads that
    from the host record rather than from the plan that produced it.  The
    records keep the wall geometry, so a door is still positioned on the wall it
    belongs to rather than at a coordinate invented for the call.
    """

    return [
        {
            "logical_id": wall.logical_id,
            "category": "WALL",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [wall.start[0], wall.start[1]],
                    [wall.end[0], wall.end[1]],
                ],
            },
            "properties": {
                "kind": wall.kind,
                "thickness_m": wall.thickness_m,
                "exterior": wall.exterior,
                "on_gallery": wall.on_gallery,
                "rooms": list(wall.rooms),
            },
        }
        for wall in walls
    ]


def _plan_r07(request, layout, walls):
    by_id = {wall.logical_id: wall for wall in walls}
    openings = []

    for index, room in enumerate(layout.rooms, start=1):
        host = _gallery_host(room, by_id)
        if host is None:
            continue
        midpoint = host.midpoint
        openings.append(
            {
                "logical_id": "DOOR-ROOM-%03d" % index,
                "kind": "DOOR",
                "host_logical_id": host.logical_id,
                "family_type": "DOOR-SINGLE-0.90",
                "position": [midpoint[0], midpoint[1]],
                "width_m": DOOR_WIDTH_M,
                "height_m": DOOR_HEIGHT_M,
                "connects": [room.logical_id, GALLERY],
                "requirement_id": "P05-T14:DOOR",
            }
        )

    for index, room in enumerate(layout.rooms, start=1):
        if room.net_area_m2 < WINDOW_MIN_ROOM_M2:
            continue
        host = _exterior_host(room, by_id)
        if host is None:
            continue
        midpoint = host.midpoint
        openings.append(
            {
                "logical_id": "WINDOW-%03d" % index,
                "kind": "WINDOW",
                "host_logical_id": host.logical_id,
                "family_type": "WINDOW-FIXED-1.20x1.20",
                "position": [midpoint[0], midpoint[1]],
                "width_m": WINDOW_WIDTH_M,
                "height_m": WINDOW_HEIGHT_M,
                "sill_m": WINDOW_SILL_M,
                "requirement_id": "P05-T14:WINDOW",
            }
        )

    catalog = [
        {
            "family_type": "DOOR-SINGLE-0.90",
            "kind": "DOOR",
            "family": "Porta de giro simples",
            "type": "0.90 x 2.10",
            "clear_width_m": DOOR_WIDTH_M,
            "catalog_source": "PROVISIONAL_ASSUMPTION: controlled study catalog",
        },
        {
            "family_type": "WINDOW-FIXED-1.20x1.20",
            "kind": "WINDOW",
            "family": "Janela fixa",
            "type": "1.20 x 1.20",
            "catalog_source": "PROVISIONAL_ASSUMPTION: controlled study catalog",
        },
    ]
    plan = openings_stage.plan_openings_stage(
        request,
        openings,
        hosts=_host_records(walls),
        family_catalog=catalog,
        accessibility_min_clear_width_m=0.80,
        minimum_window_sill_m=0.30,
        maximum_window_sill_m=1.50,
    )
    enriched = []
    for operation in plan.operations:
        properties = operation.payload["properties"]
        wall = by_id[str(properties["host_logical_id"])]
        enriched.append(
            operation.model_copy(
                update={
                    "payload": {
                        **operation.payload,
                        **_diagonal_corners(wall, properties),
                    }
                }
            )
        )
    return plan.model_copy(update={"operations": enriched})


def _plan_r08(request, program, layout):
    return rooms_stage.plan_rooms_stage(request, program=program, rooms=layout.rooms)


def _plan_r09(request, accessibility_input):
    if accessibility_input is None:
        raise ProductionBimError(
            "R09 needs explicit accessibility input; it is never inferred"
        )
    return accessibility_stage.plan_accessibility_stage(
        request, inputs=accessibility_input
    )


def _plan_r10(request, program):
    return furniture_stage.plan_furniture_stage(
        request, program=program, max_people=20
    )


def _landscape_spaces():
    return [
        landscape_stage.LandscapeSpace(
            logical_id="REQ-07-01",
            name="Patio interno protegido",
            target_area_m2=80.0,
            privacy="protected",
            adjacent_to=["residential"],
        ),
        landscape_stage.LandscapeSpace(
            logical_id="REQ-07-02",
            name="Jardim terapeutico",
            target_area_m2=80.0,
            privacy="protected",
            adjacent_to=["technical", "residential"],
        ),
        landscape_stage.LandscapeSpace(
            logical_id="REQ-07-03",
            name="Horta comunitaria",
            target_area_m2=30.0,
            privacy="semi-public",
            adjacent_to=["community"],
        ),
        landscape_stage.LandscapeSpace(
            logical_id="REQ-07-04",
            name="Exercicios e alongamento",
            target_area_m2=30.0,
            privacy="semi-public",
            adjacent_to=["residential", "therapeutic"],
        ),
        landscape_stage.LandscapeSpace(
            logical_id="REQ-07-05",
            name="Playground",
            target_area_m2=40.0,
            privacy="protected",
            adjacent_to=["child-area"],
        ),
    ]


def _plan_r11(request):
    return landscape_stage.plan_landscape_stage(request, spaces=_landscape_spaces())


def _material_assignments(walls):
    assignments = []
    for wall in walls:
        if wall.exterior:
            assignments.append(
                materials_stage.MaterialAssignment(
                    element_logical_id=wall.logical_id,
                    material_name="Alvenaria ceramica revestida",
                    material_type="EXTERNAL_WALL",
                    requirement_id="P05-T15:MATERIAL-EXTERNAL",
                    design_intent="durabilidade e manutencao simples",
                    source_ref="PROVISIONAL_ASSUMPTION: study material intent",
                    justification="sistema construtivo corrente e reparavel localmente",
                )
            )
        else:
            assignments.append(
                materials_stage.MaterialAssignment(
                    element_logical_id=wall.logical_id,
                    material_name="Divisoria leve",
                    material_type="INTERNAL_PARTITION",
                    requirement_id="P05-T15:MATERIAL-INTERNAL",
                    design_intent="conforto acustico entre ambientes",
                    source_ref="PROVISIONAL_ASSUMPTION: study material intent",
                    justification="permite revisao de layout sem obra estrutural",
                )
            )
    return assignments


def _plan_r12(request, walls):
    catalog = [
        {
            "material_name": "Alvenaria ceramica revestida",
            "material_type": "EXTERNAL_WALL",
            "source_ref": "PROVISIONAL_ASSUMPTION: study material intent",
        },
        {
            "material_name": "Divisoria leve",
            "material_type": "INTERNAL_PARTITION",
            "source_ref": "PROVISIONAL_ASSUMPTION: study material intent",
        },
    ]
    return materials_stage.plan_materials_stage(
        request, assignments=_material_assignments(walls), catalog=catalog
    )


def _plan_r13(request):
    return documentation_stage.plan_documentation_stage(request)


def _stamp(plan, solution_id, approval_hash):
    """Bind every operation to the solution that produced it."""

    def _bridge_fields(operation):
        """The provider fields the bridge reads, derived from the element.

        The stage payload speaks the compiler's vocabulary: geometry holds a
        GeoJSON LineString or Polygon.  The bridge reads start/end/height for a
        wall and profile for a floor, slab or roof, so those are derived here
        from the geometry the stage already fixed rather than invented.
        """

        geometry = operation.payload.get("geometry")
        if not isinstance(geometry, Mapping):
            return {}
        kind = geometry.get("type")
        coordinates = geometry.get("coordinates")
        capability = operation.semantic_capability
        if kind == "LineString" and capability in {
            "revit.create_wall",
            "revit.create_internal_wall",
        }:
            if not isinstance(coordinates, list) or len(coordinates) < 2:
                return {}
            start = [float(v) for v in coordinates[0]]
            end = [float(v) for v in coordinates[1]]
            while len(start) < 3:
                start.append(0.0)
            while len(end) < 3:
                end.append(0.0)
            fields = {
                "start": start,
                "end": end,
                "height": float(FLOOR_HEIGHT_M),
            }
            # The provider resolves a wall type by NAME through the type_id
            # field, so the template's real type name travels there.  The stage
            # keeps its own wall_type_id for the accounting, and the bridge is
            # given the field it reads.
            properties = operation.payload.get("properties")
            properties = dict(properties) if isinstance(properties, Mapping) else {}
            # The shell stage names the wall's type in properties.type_id.
            type_name = properties.get("type_id")
            if isinstance(type_name, str) and type_name.strip():
                # A numeric string is an ElementId and travels as an int, which
                # the bridge resolves directly instead of searching by name.
                fields["type_id"] = (
                    int(type_name) if type_name.strip().isdigit() else type_name
                )
            elif isinstance(type_name, int):
                fields["type_id"] = type_name
            return fields
        if kind == "Polygon" and capability in {
            "revit.create_floor",
            "revit.create_slab",
            "revit.create_roof",
        }:
            ring = coordinates[0] if isinstance(coordinates, list) and coordinates else None
            if not isinstance(ring, list) or len(ring) < 4:
                return {}
            fields = {"profile": [[float(p[0]), float(p[1])] for p in ring]}
            properties = operation.payload.get("properties")
            properties = dict(properties) if isinstance(properties, Mapping) else {}
            type_name = properties.get("slab_type_id") or properties.get("type_id")
            if isinstance(type_name, str) and type_name.strip():
                fields["type_id"] = (
                    int(type_name) if type_name.strip().isdigit() else type_name
                )
            return fields
        return {}

    operations = [
        operation.model_copy(
            update={
                "payload": {
                    **operation.payload,
                    "solution_id": solution_id,
                    "approval_hash": approval_hash,
                    **_bridge_fields(operation),
                    # Revit refuses a wall, floor, slab, roof, room or opening
                    # that does not name the level it belongs to, and the bridge
                    # resolves that reference by the logical id the level
                    # carries in the model. R03 has already written LEVEL-01 by
                    # the time these stages run, so the reference is attached for
                    # every operation that needs one and does not carry it yet.
                    **(
                        {"level_id": LEVEL_LOGICAL_ID}
                        if operation.semantic_capability in _NEEDS_LEVEL
                        and operation.payload.get("level_id") is None
                        else {}
                    ),
                }
            }
        )
        for operation in plan.operations
    ]
    note = "BIT_IDENTITY: solution_id=%s; approval_hash=%s" % (
        solution_id,
        approval_hash,
    )
    updates = {"operations": operations}
    preflight = getattr(plan, "preflight", None)
    if preflight is not None:
        updates["preflight"] = preflight.model_copy(
            update={"notes": [*preflight.notes, note]}
        )
    if hasattr(plan, "notes"):
        updates["notes"] = [*plan.notes, note]
    return plan.model_copy(update=updates)


def build_layout_stage_plans(
    *,
    program,
    layout,
    registry,
    revit_build,
    tool_schema_hash,
    generation_run,
    solution_id,
    approval_hash,
    solution=None,
    accessibility_input=None,
    template_root=None,
    mode=ExecutionMode.DETAILED_BIM,
    max_stage=BimStage.R13,
):
    """Return the ordered stage plans for the adopted layout.

    Every stage is planned against the capability registry the caller supplies,
    so a missing capability raises here instead of reaching Revit.  The identity
    of the solution travels in every operation payload, which is what lets a
    later audit prove which plan produced which element.

    The solution argument is the approved selection record.  DETAILED_BIM
    requires one: the stage preflight refuses a detailed run whose selection is
    not content bound, and this driver does not synthesize a selection just to
    get past that gate.
    """

    if mode is ExecutionMode.CONCEPT_ONLY:
        raise ProductionBimError(
            "the detailed production chain is not available under CONCEPT_ONLY; "
            "use the concept compiler for R01-R04"
        )
    if mode is ExecutionMode.DETAILED_BIM:
        if solution is None:
            raise ProductionBimError(
                "DETAILED_BIM requires the approved selection record; no plan is "
                "produced without a content-bound approval"
            )
        if not solution.bim_eligible:
            raise ProductionBimError(
                "the selection record is not BIM eligible under the current evidence"
            )
        if solution.approval_hash != approval_hash:
            raise ProductionBimError(
                "the requested approval_hash is not the one the selection carries"
            )
    if not layout.rooms:
        raise ProductionBimError("the layout carries no rooms")

    exterior, partitions = build_walls(layout)
    walls = [*exterior, *partitions]
    if not walls:
        raise ProductionBimError("the layout produces no walls")

    site = _site_model(layout) if solution is not None else None

    def stage_request(stage):
        return _request(
            stage,
            registry=registry,
            revit_build=revit_build,
            tool_schema_hash=tool_schema_hash,
            generation_run=generation_run,
            mode=mode,
            solution=solution,
            site=site,
            expected_approval_hash=(approval_hash if solution is not None else None),
        )

    handlers = {
        BimStage.R01: lambda: _plan_r01(
            stage_request(BimStage.R01), template_root=template_root
        ),
        BimStage.R02: lambda: _plan_r02(stage_request(BimStage.R02), layout),
        BimStage.R03: lambda: _plan_r03(stage_request(BimStage.R03), layout),
        BimStage.R04: lambda: _plan_r04(stage_request(BimStage.R04), layout),
        BimStage.R05: lambda: _plan_r05(stage_request(BimStage.R05), layout),
        BimStage.R06: lambda: _plan_r06(stage_request(BimStage.R06), layout),
        BimStage.R07: lambda: _plan_r07(stage_request(BimStage.R07), layout, walls),
        BimStage.R08: lambda: _plan_r08(stage_request(BimStage.R08), program, layout),
        BimStage.R09: lambda: _plan_r09(
            stage_request(BimStage.R09), accessibility_input
        ),
        BimStage.R10: lambda: _plan_r10(stage_request(BimStage.R10), program),
        BimStage.R11: lambda: _plan_r11(stage_request(BimStage.R11)),
        BimStage.R12: lambda: _plan_r12(stage_request(BimStage.R12), walls),
        BimStage.R13: lambda: _plan_r13(stage_request(BimStage.R13)),
    }

    plans = []
    for stage in _STAGE_ORDER:
        plans.append(handlers[stage]())
        if stage is max_stage:
            break
    return [_stamp(plan, solution_id, approval_hash) for plan in plans]


__all__ = [
    "DOOR_HEIGHT_M",
    "DOOR_WIDTH_M",
    "EXTERNAL_WALL_M",
    "FLOOR_HEIGHT_M",
    "PARTITION_M",
    "WINDOW_HEIGHT_M",
    "WINDOW_SILL_M",
    "WINDOW_WIDTH_M",
    "ProductionBimError",
    "build_layout_stage_plans",
    "build_walls",
    "layout_stage_order",
]
