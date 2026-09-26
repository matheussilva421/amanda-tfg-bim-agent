"""Horizun MCP implementation of the BIM stage invoker protocol."""

from __future__ import annotations

import json
from collections.abc import Mapping
from textwrap import dedent
from typing import Any

from ..stages import StageToolCall
from .transport import McpProbeTransport, McpTransport

PROVIDER_NAME = "horizun"
EXPECTED_REVIT_VERSION = "2027"

# These names are copied from the verified semantic toolmap. A capability with
# no typed route is refused instead of being sent to a lookalike tool.
_CAPABILITY_TO_TOOL = {
    "health": "horizun_health",
    "revit.health": "horizun_health",
    "document_info": "get_document_info",
    "revit.document_info": "get_document_info",
    "document_query": "horizun_query_model",
    "revit.query_model": "horizun_query_model",
    "model_scan": "horizun_model_scan",
    "revit.model_scan": "horizun_model_scan",
    "revit.open_document": "horizun_open_document",
    "revit.save_document": "horizun_save_document",
    "revit.create_level": "horizun_create_elements",
    "revit.create_grid": "horizun_create_elements",
    "revit.create_wall": "horizun_create_elements",
    "revit.create_floor": "horizun_create_elements",
    "revit.create_slab": "horizun_create_elements",
    "revit.create_roof": "horizun_create_elements",
    "revit.create_internal_wall": "horizun_create_elements",
    "revit.create_room": "horizun_create_elements",
    "revit.create_opening": "horizun_create_elements",
    "revit.create_project": "horizun_document_session",
    "revit.create_toposolid": "horizun_execute_python",
    "revit.create_mass": "horizun_execute_python",
    "revit.create_reference": "horizun_execute_python",
    "revit.create_accessibility_element": "horizun_execute_python",
    "revit.create_furniture_element": "horizun_execute_python",
    "revit.create_landscape_element": "horizun_execute_python",
    "revit.assign_material": "horizun_execute_python",
    "revit.create_documentation_element": "horizun_execute_python",
}

_ELEMENT_KIND = {
    "revit.create_level": "level",
    "revit.create_grid": "grid",
    "revit.create_wall": "wall",
    "revit.create_floor": "floor",
    "revit.create_slab": "floor",
    "revit.create_roof": "roof",
    "revit.create_internal_wall": "wall",
    "revit.create_room": "room",
    "revit.create_opening": "wall_opening",
}

# Categories that carry no ALL_MODEL_MARK; offering one refuses the whole batch.
_MARKLESS_KINDS = {"level", "grid", "wall_opening"}
# A room carries comments but no mark: the bridge refuses the whole batch when a
# category is offered a parameter it does not own, and a room owns no mark.
_MARK_ONLY_KINDS = {"level", "grid", "room", "wall_opening"}
_MARKLESS_READBACK_CATEGORIES = {
    "level": "OST_Levels",
    "grid": "OST_Grids",
    "room": "OST_Rooms",
}

#: Categories the python routes create that CAN be re-queried by name.  The
#: filter resolves against the model's own localised category names, which is why
#: one identifier works on an English and a localised document.
_PYTHON_READBACK_CATEGORIES = {
    "revit.create_mass": "OST_Mass",
}

#: Categories the python routes create that CAN be re-queried.  The query filter
#: resolves these against the model's own localised category names (a Brazilian
#: Portuguese model reports "Massa", not "OST_Mass"), which is why the same
#: identifier works on an English and a localised document.
_PYTHON_READBACK_CATEGORIES = {
    "revit.create_mass": "OST_Mass",
}
_WALL_OPENING_READBACK_UNAVAILABLE = {
    "type": "HorizunReadbackUnavailable",
    "code": "wall_opening_no_reliable_query_filter",
    "message": "horizun_query_model has no reliable logical_id filter for wall_opening",
}


_ELEMENT_FIELDS = {
    "level": ("name", "elevation", "parameters"),
    "grid": ("name", "start", "end", "parameters"),
    "wall": (
        "start",
        "end",
        "level_id",
        "height",
        "type_id",
        "offset",
        "base_offset",
        "top_level_id",
        "top_offset",
        "arc",
        "flip",
        "structural",
        "parameters",
    ),
    "floor": ("profile", "level_id", "type_id", "offset", "structural", "parameters"),
    "roof": ("profile", "level_id", "type_id", "offset", "structural", "parameters"),
    "room": ("point", "level_id", "name", "number", "parameters"),
    "wall_opening": ("corner_1", "corner_2", "level_id", "host_id", "allow_structural", "parameters"),
}

_READ_ONLY_TOOLS = {
    "horizun_health",
    "get_document_info",
    "horizun_query_model",
    "horizun_model_scan",
    "horizun_list_elements",
    "horizun_audit_model",
    "horizun_quantities",
}

_MUTATING_TOOLS = {
    "horizun_document_session",
    "horizun_open_document",
    "horizun_save_document",
    "horizun_create_elements",
    "horizun_manage_views",
    "horizun_manage_schedules",
    "horizun_transform_elements",
    "horizun_edit_dimensions",
    "horizun_execute_python",
}

StageToolRequest = StageToolCall


class HorizunRequestError(ValueError):
    """The compiler call cannot be safely translated to the Horizun schema."""


class HorizunUnsupportedCapability(HorizunRequestError):
    """The verified Horizun toolmap has no route for a semantic capability."""


class _PreWriteReadFailure(HorizunRequestError):
    """A read failed before a mutation could be attempted."""

    def __init__(self, message: str, *, error: Any) -> None:
        super().__init__(message)
        self.error_payload = error


class StageToolResult(dict[str, Any]):
    """Mapping result compatible with ``dispatch_operations`` and auditable by callers."""

    def __init__(
        self,
        *,
        provider: str,
        tool: str | None,
        reported_success: bool,
        read_payload: Any = None,
        raw: Mapping[str, Any] | None = None,
        error: Any = None,
        idempotency_key: str | None = None,
    ) -> None:
        values: dict[str, Any] = {
            "provider": provider,
            "tool": tool,
            "reported_success": reported_success,
            "tool_success": reported_success,
            "read_payload": read_payload,
            "payload": read_payload,
            "raw": dict(raw or {}),
        }
        if error is not None:
            values["error"] = error
        if idempotency_key is not None:
            values["idempotency_key"] = idempotency_key
        super().__init__(values)

    @property
    def provider(self) -> str:
        return str(self["provider"])

    @property
    def reported_success(self) -> bool:
        return bool(self["reported_success"])

    @property
    def success(self) -> bool:
        return self.reported_success

    @property
    def error(self) -> Any:
        return self.get("error")

    @property
    def read_payload(self) -> Any:
        return self.get("read_payload")


class HorizunInvoker:
    """Translate compiler stage calls into verified Horizun MCP calls."""

    provider = PROVIDER_NAME

    def __init__(
        self,
        *,
        transport: McpTransport | None = None,
        target_document: str | None = None,
        expected_version: str = EXPECTED_REVIT_VERSION,
    ) -> None:
        if not expected_version.strip():
            raise ValueError("expected_version must not be empty")
        self.transport = transport or McpProbeTransport()
        self.target_document = target_document
        self.expected_version = expected_version
        self._stage_read_cache: dict[Any, dict[str, list[Mapping[str, Any]]]] = {}
        self._stage_resolution_cache: dict[Any, dict[str, int]] = {}
        self._logical_ids: dict[str, int] = {}
        self._pending_readbacks: dict[str, dict[str, Any]] = {}
        self._plan_evidence: dict[str, dict[str, Any]] = {}

    def invoke(self, call: StageToolRequest) -> StageToolResult:
        """Invoke exactly one provider tool; the caller remains the model writer."""

        tool = _CAPABILITY_TO_TOOL.get(call.semantic_capability)
        if tool is None:
            raise HorizunUnsupportedCapability(
                f"Horizun has no verified typed route for {call.semantic_capability!r}"
            )
        payload = dict(call.payload)
        key = payload.get("idempotency_key")
        self._require_idempotency_if_mutating(tool, payload, key)
        try:
            if self._is_mutating(tool, payload):
                self._prepare_write(call, tool, payload)
        except _PreWriteReadFailure as exc:
            return StageToolResult(
                provider=self.provider,
                tool=tool,
                reported_success=False,
                read_payload={"error": exc.error_payload},
                error=exc.error_payload,
                idempotency_key=key if isinstance(key, str) else None,
            )
        tool, arguments = self._translate(call)
        try:
            arguments = self._resolve_confirmation(tool, arguments)
        except HorizunRequestError as exc:
            return StageToolResult(
                provider=self.provider,
                tool=tool,
                reported_success=False,
                read_payload={"error": {"type": "HorizunRequestError", "message": str(exc)}},
                error={"type": "HorizunRequestError", "message": str(exc)},
                idempotency_key=(arguments.get("idempotency_key") if isinstance(arguments.get("idempotency_key"), str) else None),
            )
        key = arguments.get("idempotency_key")
        self._require_idempotency_if_mutating(tool, arguments, key)
        try:
            reply = self.transport.call(tool, arguments)
        except Exception as exc:  # noqa: BLE001 - provider boundary must return a failed result
            error = {"type": type(exc).__name__, "message": str(exc)}
            return StageToolResult(
                provider=self.provider,
                tool=tool,
                reported_success=False,
                read_payload={"error": error},
                error=error,
            )
        result = self._result(tool, reply, key)
        self._remember_created_id(call, result.read_payload)
        self._merge_readback(result, key)
        return result

    def _prepare_write(
        self,
        call: StageToolRequest,
        tool: str,
        arguments: Mapping[str, Any],
    ) -> None:
        """Re-read the active document and the relevant model scope before a write."""

        document = self._read_tool("get_document_info", {})
        target = arguments.get("target_document") or self.target_document
        self._check_target_document(document, target)
        if tool != "horizun_execute_python":
            return
        category = {
            "revit.create_toposolid": "OST_Toposolid",
            "revit.create_mass": "OST_Mass",
            "revit.create_reference": "OST_ReferencePlanes",
            "revit.create_accessibility_element": "OST_GenericModel",
            "revit.create_furniture_element": "OST_Furniture",
            "revit.create_landscape_element": "OST_GenericModel",
            "revit.assign_material": "OST_GenericModel",
            "revit.create_documentation_element": "OST_Views",
        }.get(call.semantic_capability)
        if category is not None:
            self._read_tool(
                "horizun_query_model",
                {
                    "categories": [category],
                    "response_mode": "compact",
                    "cache_mode": "bypass",
                    "include_types": True,
                },
            )

    @staticmethod
    def _check_target_document(document: Any, target: Any) -> None:
        """Refuse an explicitly named target when the read identifies another document."""

        if not isinstance(target, str) or not target.strip() or not isinstance(document, Mapping):
            return
        observed: list[str] = []
        for key in ("title", "path", "document", "target_document", "active_document"):
            value = document.get(key)
            if isinstance(value, str) and value.strip():
                observed.append(value.strip())
            elif isinstance(value, Mapping):
                for nested in ("title", "path", "name"):
                    nested_value = value.get(nested)
                    if isinstance(nested_value, str) and nested_value.strip():
                        observed.append(nested_value.strip())
        if not observed:
            return
        wanted = target.strip().casefold()
        if any(wanted == value.casefold() or wanted in value.casefold() for value in observed):
            return
        raise HorizunRequestError(
            f"active document does not match target_document {target!r}; observed {observed!r}"
        )

    def _read_tool(self, tool: str, arguments: Mapping[str, Any]) -> Any:
        try:
            reply = self.transport.call(tool, arguments)
        except Exception as exc:
            error = {"type": type(exc).__name__, "message": str(exc)}
            raise _PreWriteReadFailure(
                f"pre-write read {tool!r} failed: {exc}", error=error
            ) from exc
        result = self._result(tool, reply, None)
        if not result.reported_success:
            error = result.error or result.read_payload
            raise _PreWriteReadFailure(
                f"pre-write read {tool!r} was not successful: {error}", error=error
            )
        return result.read_payload

    def _remember_created_id(self, call: StageToolRequest, payload: Any) -> None:
        """Keep returned ElementIds available for later stage translations."""

        if not isinstance(payload, Mapping):
            return
        candidates: list[Any] = [payload.get("element_id")]
        created = payload.get("created_ids")
        if isinstance(created, list):
            candidates.extend(created)
        candidates.extend(row.get("element_id") for row in self._rows(payload))
        for value in candidates:
            if isinstance(value, int) and not isinstance(value, bool):
                self._logical_ids[call.logical_id] = value
                return

    def _translate(self, call: StageToolRequest) -> tuple[str, dict[str, Any]]:
        semantic = call.semantic_capability
        tool = _CAPABILITY_TO_TOOL.get(semantic)
        if tool is None:
            raise HorizunUnsupportedCapability(
                f"Horizun has no verified typed route for {semantic!r}"
            )
        payload = dict(call.payload)
        if tool == "horizun_create_elements":
            return tool, self._create_elements_arguments(call, payload)
        if tool == "horizun_query_model":
            return tool, self._query_arguments(payload)
        if tool == "horizun_open_document":
            return tool, self._open_arguments(payload)
        if tool == "horizun_save_document":
            return tool, self._save_arguments(payload)
        if tool == "horizun_execute_python":
            return tool, self._python_arguments(call, payload)
        if tool == "horizun_document_session":
            return tool, self._document_session_arguments(payload)
        if tool in {"horizun_health", "get_document_info"}:
            return tool, {}
        raise HorizunUnsupportedCapability(
            f"Horizun route {tool!r} is not implemented by this adapter"
        )

    def _python_arguments(
        self, call: StageToolRequest, payload: Mapping[str, Any]
    ) -> dict[str, Any]:
        target = payload.get("target_document") or self.target_document
        if not isinstance(target, str) or not target.strip():
            raise HorizunRequestError(
                "horizun_execute_python requires target_document on the call or invoker"
            )
        key = payload.get("idempotency_key")
        if not isinstance(key, str) or not key.strip():
            raise HorizunRequestError("horizun_execute_python requires idempotency_key")
        # A python route answers with its own execution evidence and no
        # ElementId, so the independent read has to find the element by the
        # category and the name it carries.  Scheduling it here is what lets the
        # stage verify what it wrote instead of trusting the write; a route with
        # no queryable category is left to report a missing read, which is
        # honest, rather than being declared verified without a read.
        readback_category = _PYTHON_READBACK_CATEGORIES.get(call.semantic_capability)
        if readback_category is not None and payload.get("dry_run") is False:
            if call.semantic_capability == "revit.create_mass":
                self._pending_readbacks[key] = {
                    "logical_id": call.logical_id,
                    "tool": "horizun_execute_python",
                    "arguments": {"target_document": target, "response_mode": "compact"},
                    "geometry_readback": True,
                }
            else:
                self._pending_readbacks[key] = {
                    "logical_id": call.logical_id,
                    "tool": "horizun_query_model",
                    "arguments": {
                        "categories": [readback_category],
                        # unique_id proves the read found one specific element
                        # rather than a name, and the default field set omits it.
                        "return_fields": list(self._READBACK_FIELDS),
                        "response_mode": "compact",
                        "cache_mode": "bypass",
                    },
                    "match_by_logical_id": True,
                }
        request = dict(payload)
        request.setdefault("logical_id", call.logical_id)
        request.setdefault("semantic_capability", call.semantic_capability)
        self._translate_python_references(call, request)
        encoded = json.dumps(request, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        code = self._python_script(call.semantic_capability, encoded)
        return {
            "target_document": target,
            "code": code,
            "idempotency_key": key,
            "response_mode": "compact",
        }

    @staticmethod
    def _python_script(semantic: str, encoded_request: str) -> str:
        """Build one deterministic, idempotent Revit API script per capability."""

        route_bodies = {
            "revit.create_toposolid": """
points = geometry.get('points') or request.get('points') or geometry.get('footprint')
if not points or len(points) < 3:
    raise ValueError('create_toposolid requires at least three metric points')
point_list = List[XYZ]()
for value in points:
    point_list.Add(to_xyz(value))
level_id = request.get('level_id')
if level_id is None:
    levels = list(FilteredElementCollector(document).OfClass(Level))
    levels = sorted(levels, key=lambda item: element_id_value(item.Id))
    if not levels:
        raise RuntimeError('create_toposolid could not find a Revit level')
    level_id = element_id_value(levels[0].Id)
type_id = request.get('revit_type_id')
if type_id is None:
    types = list(FilteredElementCollector(document).OfClass(ToposolidType))
    types = sorted(types, key=lambda item: element_id_value(item.Id))
    if not types:
        raise RuntimeError('create_toposolid could not find a ToposolidType')
    type_id = element_id_value(types[0].Id)
created = Toposolid.Create(document, point_list, ElementId(int(type_id)), ElementId(int(level_id)))
""",
            "revit.create_mass": """
footprint = geometry.get('footprint')
interior_rings = geometry.get('interior_rings') or []
base_elevation_m = float(geometry.get('base_elevation_m') or 0.0)

def mass_xyz(value):
    point = to_xyz(value)
    return XYZ(point.X, point.Y, point.Z + base_elevation_m * M_TO_FT)

if footprint:
    profile_rings = [footprint, *interior_rings]
else:
    profile = geometry.get('profile')
    if profile and profile[0] and isinstance(profile[0][0], (list, tuple)):
        profile_rings = profile
    else:
        profile_rings = [profile] if profile else []
if not profile_rings or any(not ring or len(ring) < 3 for ring in profile_rings):
    raise ValueError('create_mass requires a closed metric footprint')
profile_loops = List[CurveLoop]()
for ring in profile_rings:
    loop = CurveLoop()
    for index in range(len(ring)):
                    loop.Append(Line.CreateBound(mass_xyz(ring[index]), mass_xyz(ring[(index + 1) % len(ring)])))
    profile_loops.Add(loop)
height_m = float(geometry.get('height_m') or geometry.get('height') or request.get('height_m') or 0.01)
if height_m <= 0:
    raise ValueError('create_mass height must be positive')
solid = GeometryCreationUtilities.CreateExtrusionGeometry(profile_loops, XYZ.BasisZ, height_m * M_TO_FT)
created = make_direct_shape(BuiltInCategory.OST_Mass, solid)
set_name(created, property_value('name', logical_id))
""",
            "revit.create_reference": """
coordinate = geometry.get('coordinate') or geometry.get('location') or [0.0, 0.0, 0.0]
origin = to_xyz(coordinate)
view = None
for candidate in sorted(list(FilteredElementCollector(document).OfClass(ViewPlan)), key=lambda item: element_id_value(item.Id)):
    if not candidate.IsTemplate:
        view = candidate
        break
if view is None:
    raise RuntimeError('create_reference could not find a non-template plan view')
created = document.Create.NewReferencePlane(origin, origin + XYZ.BasisX, XYZ.BasisZ, view)
set_name(created, property_value('name', logical_id))
""",
            "revit.create_accessibility_element": """
location = geometry.get('location') or geometry.get('coordinate') or [0.0, 0.0, 0.0]
solid = metric_box(location, geometry.get('width_m') or 0.1, geometry.get('depth_m') or 0.1, geometry.get('height_m') or 0.02)
created = make_direct_shape(BuiltInCategory.OST_GenericModel, solid)
""",
            "revit.create_furniture_element": """
location = geometry.get('location') or geometry.get('coordinate') or [0.0, 0.0, 0.0]
symbol_id = request.get('revit_type_id')
if symbol_id is None:
    # Live probe evidence, probe-api6-live.json and .tmp-probe-live7.log: the
    # document carries real furniture symbols ('1525 x 762mm' 99774, '1830 x
    # 915mm' 99776) and NewFamilyInstance committed an instance from one, so a
    # request without a catalog type resolves the first OST_Furniture symbol of
    # the document instead of failing a route the model can actually satisfy.
    symbols = list(FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_Furniture).OfClass(FamilySymbol))
    symbols = sorted(symbols, key=lambda item: element_id_value(item.Id))
    if not symbols:
        raise RuntimeError('create_furniture_element found no furniture symbol in this document')
    symbol_id = element_id_value(symbols[0].Id)
symbol = document.GetElement(ElementId(int(symbol_id)))
if symbol is None:
    raise RuntimeError('resolved furniture type is absent from the document')
if isinstance(symbol, FamilyInstance):
    # Live probe evidence, .tmp-probe-live9.log: the id lookup returns the first
    # OST_Furniture element of the category, and that element can be a placed
    # instance rather than a loadable type. Reading IsActive straight from it
    # raised "AttributeError: 'FamilyInstance' object has no attribute
    # 'IsActive'", so the route resolves the instance to its type instead.
    symbol = symbol.Symbol
if not isinstance(symbol, FamilySymbol):
    raise RuntimeError('resolved furniture element is not a loadable family type')
if not symbol.IsActive:
    symbol.Activate()
document.Regenerate()
created = document.Create.NewFamilyInstance(to_xyz(location), symbol, StructuralType.NonStructural)
""",
            "revit.create_landscape_element": """
location = geometry.get('location') or geometry.get('coordinate') or [0.0, 0.0, 0.0]
area = float(geometry.get('target_area_m2') or 1.0)
side = max(area ** 0.5, 0.1)
solid = metric_box(location, side, side, geometry.get('height_m') or 0.02)
created = make_direct_shape(BuiltInCategory.OST_GenericModel, solid)
""",
            "revit.assign_material": """
host_id = request.get('revit_host_id')
if host_id is None:
    raise RuntimeError('assign_material requires a resolved host element')
host = document.GetElement(ElementId(int(host_id)))
if host is None:
    raise RuntimeError('resolved material host is absent from the document')
material_name = property_value('material_name') or property_value('material')
if not material_name:
    raise ValueError('assign_material requires material_name')
material = None
for candidate in FilteredElementCollector(document).OfClass(Material):
    if candidate.Name == str(material_name):
        material = candidate
        break
if material is None:
    # Live probe evidence, probe-api7-live.json: Material.Create returns an
    # ElementId in this build, not a Material, so the created material has to be
    # re-read before anything can use its Id.
    material = document.GetElement(Material.Create(document, str(material_name)))
if material is None:
    raise RuntimeError('assign_material could not create or find material ' + str(material_name))
assigned = False
host_type = document.GetElement(host.GetTypeId())
# Live probe evidence, probe-api7-live.json: a wall carries no writable material
# parameter of its own, and the assignment that really commits is layer 0 of the
# type's compound structure. The parameter scan stays as a second resort for the
# categories that do expose one.
if not assigned and host_type is not None and hasattr(host_type, 'GetCompoundStructure'):
    structure = host_type.GetCompoundStructure()
    if structure is not None and getattr(structure, 'LayerCount', 0) > 0 and hasattr(structure, 'SetMaterialId'):
        structure.SetMaterialId(0, material.Id)
        host_type.SetCompoundStructure(structure)
        assigned = True
for candidate in [host, host_type]:
    if candidate is None:
        continue
    for parameter in candidate.Parameters:
        definition = parameter.Definition
        name = definition.Name if definition is not None else ''
        if 'material' in name.lower() and parameter.StorageType == StorageType.ElementId and not parameter.IsReadOnly:
            parameter.Set(material.Id)
            assigned = True
            break
    if assigned:
        break
if not assigned:
    raise RuntimeError('assign_material found no writable material parameter on host or type')
created = host
mark_created = False
created_id = element_id_value(host.Id)
""",
            "revit.create_documentation_element": """
kind = str(property_value('documentation_kind') or geometry.get('documentation_kind') or 'view').lower()
if kind == 'sheet':
    created = ViewSheet.Create(document, ElementId.InvalidElementId)
    set_name(created, property_value('sheet_id') or logical_id)
elif kind in ('schedule', 'table'):
    created = ViewSchedule.CreateSchedule(document, ElementId(BuiltInCategory.OST_Rooms))
    set_name(created, property_value('table_name') or logical_id)
else:
    level_id = request.get('level_id')
    if level_id is None:
        levels = sorted(list(FilteredElementCollector(document).OfClass(Level)), key=lambda item: element_id_value(item.Id))
        if not levels:
            raise RuntimeError('create_documentation_element could not find a Revit level')
        level_id = element_id_value(levels[0].Id)
    view_type = None
    for candidate in sorted(list(FilteredElementCollector(document).OfClass(ViewFamilyType)), key=lambda item: element_id_value(item.Id)):
        if candidate.ViewFamily == ViewFamily.FloorPlan:
            view_type = candidate
            break
    if view_type is None:
        raise RuntimeError('create_documentation_element could not find a floor plan type')
    created = ViewPlan.Create(document, view_type.Id, ElementId(int(level_id)))
    set_name(created, property_value('view_name') or logical_id)
""",
        }
        body = route_bodies.get(semantic)
        if body is None:
            raise HorizunUnsupportedCapability(
                f"Horizun has no verified Python route for {semantic!r}"
            )
        indented_body = "\n".join(
            f"        {line}" if line else "" for line in body.strip("\n").splitlines()
        )
        return (
            "import json\n"
            "import clr\n"
            "clr.AddReference('RevitAPI')\n"
            "from System.Collections.Generic import List\n"
            "from Autodesk.Revit.DB import *\n"
            "from Autodesk.Revit.DB.Structure import StructuralType\n"
            f"request = json.loads({encoded_request!r})\n"
            "logical_id = request['logical_id']\n"
            "semantic_capability = request['semantic_capability']\n"
            "geometry = request.get('geometry') or {}\n"
            "properties = request.get('properties') or {}\n"
            "M_TO_FT = 3.280839895013123\n"
            "def element_id_value(element_id):\n"
            "    return int(element_id.Value)\n"
            "def property_value(name, default=None):\n"
            "    return properties.get(name, request.get(name, default))\n"
            "def to_xyz(value):\n"
            "    values = list(value)\n"
            "    while len(values) < 3:\n"
            "        values.append(0.0)\n"
            "    return XYZ(float(values[0]) * M_TO_FT, float(values[1]) * M_TO_FT, float(values[2]) * M_TO_FT)\n"
            "def metric_box(origin, width_m, depth_m, height_m):\n"
            "    p = to_xyz(origin)\n"
            "    x = float(width_m) * M_TO_FT\n"
            "    y = float(depth_m) * M_TO_FT\n"
            "    z = max(float(height_m) * M_TO_FT, 0.001)\n"
            "    loop = CurveLoop()\n"
            "    loop.Append(Line.CreateBound(p, p + XYZ(x, 0, 0)))\n"
            "    loop.Append(Line.CreateBound(p + XYZ(x, 0, 0), p + XYZ(x, y, 0)))\n"
            "    loop.Append(Line.CreateBound(p + XYZ(x, y, 0), p + XYZ(0, y, 0)))\n"
            "    loop.Append(Line.CreateBound(p + XYZ(0, y, 0), p))\n"
            "    return GeometryCreationUtilities.CreateExtrusionGeometry(List[CurveLoop]([loop]), XYZ.BasisZ, z)\n"
            "def make_direct_shape(category, solid):\n"
            "    shape = DirectShape.CreateElement(document, ElementId(category))\n"
            "    shapes = List[GeometryObject]()\n"
            "    shapes.Add(solid)\n"
            "    shape.SetShape(shapes)\n"
            "    return shape\n"
            "def built_in_parameter(element, built_in):\n"
            "    # The bridge projects some document elements as plain Element, Material\n"
            "    # or View, and those projections carry no get_Parameter attribute; an\n"
            "    # unguarded read killed every Python route with AttributeError.\n"
            "    reader = getattr(element, 'get_Parameter', None)\n"
            "    if reader is None:\n"
            "        return None\n"
            "    try:\n"
            "        return reader(built_in)\n"
            "    except Exception:\n"
            "        return None\n"
            "def built_in_string(element, built_in):\n"
            "    parameter = built_in_parameter(element, built_in)\n"
            "    if parameter is None:\n"
            "        return None\n"
            "    try:\n"
            "        return parameter.AsString()\n"
            "    except Exception:\n"
            "        return None\n"
            "def set_mark(element):\n"
            "    parameter = built_in_parameter(element, BuiltInParameter.ALL_MODEL_MARK)\n"
            "    if parameter is not None and not parameter.IsReadOnly:\n"
            "        parameter.Set(logical_id)\n"
            "def set_name(element, value):\n"
            "    if value is None:\n"
            "        return\n"
            "    try:\n"
            "        element.Name = str(value)\n"
            "    except Exception:\n"
            "        pass\n"
            "document = globals().get('doc') or globals().get('document') or globals().get('__document__')\n"
            "if document is None:\n"
            "    raise RuntimeError('Horizun Python context did not expose the active Document')\n"
            "existing = []\n"
            "if semantic_capability != 'revit.assign_material':\n"
            "    expected_name = property_value('view_name') or property_value('sheet_id') or property_value('table_name') or property_value('name')\n"
            "    for candidate in FilteredElementCollector(document).WhereElementIsNotElementType():\n"
            "        marked = built_in_string(candidate, BuiltInParameter.ALL_MODEL_MARK) == logical_id\n"
            "        named = expected_name is not None and hasattr(candidate, 'Name') and candidate.Name == str(expected_name)\n"
            "        if marked or named:\n"
            "            existing.append(candidate)\n"
            "if existing:\n"
            "    __output__ = {'status': 'self_reported_verified', 'logical_id': logical_id, 'element_id': element_id_value(existing[0].Id), 'created': False, 'semantic_capability': semantic_capability}\n"
            "else:\n"
            "    transaction = Transaction(document, 'Amanda ' + semantic_capability + ' ' + logical_id)\n"
            "    transaction.Start()\n"
            "    try:\n"
            "        created = None\n"
            "        created_id = None\n"
            "        mark_created = True\n"
            f"{indented_body}\n"
            "        if created is None:\n"
            "            raise RuntimeError('route did not create a Revit element')\n"
            "        if mark_created:\n"
            "            set_mark(created)\n"
            "        if created_id is None:\n"
            "            created_id = element_id_value(created.Id)\n"
            "        transaction.Commit()\n"
            "    finally:\n"
            "        if transaction.GetStatus() == TransactionStatus.Started:\n"
            "            transaction.RollBack()\n"
            "    __output__ = {'status': 'self_reported_verified', 'logical_id': logical_id, 'element_id': created_id, 'created': True, 'semantic_capability': semantic_capability}\n"
        )

    @staticmethod
    def _mass_geometry_readback_script(element_id: int) -> str:
        """Extract the solid profile in a separate, read-only Revit call."""

        if isinstance(element_id, bool) or element_id < 0:
            raise ValueError("mass geometry readback requires a non-negative element id")
        script = """
            import clr
            clr.AddReference('RevitAPI')
            from Autodesk.Revit.DB import ElementId, Options, PlanarFace, Solid

            document = globals().get('doc') or globals().get('document') or globals().get('__document__')
            if document is None:
                raise RuntimeError('Horizun Python context did not expose the active Document')
            expected_element_id = __ELEMENT_ID__
            element = document.GetElement(ElementId(expected_element_id))
            if element is None:
                raise RuntimeError('mass geometry readback could not find the written element')

            M_TO_FT = 3.280839895013123
            solids = [
                item for item in element.get_Geometry(Options())
                if isinstance(item, Solid) and item.Faces.Size > 0
            ]
            if len(solids) != 1:
                raise RuntimeError('mass geometry readback requires exactly one non-empty solid')
            horizontal_faces = [
                face for face in solids[0].Faces
                if isinstance(face, PlanarFace)
                and abs(abs(face.FaceNormal.Z) - 1.0) < 1e-8
            ]
            if len(horizontal_faces) < 2:
                raise RuntimeError('mass geometry readback found no horizontal base and top faces')

            bottom_face = min(horizontal_faces, key=lambda face: face.Origin.Z)
            top_face = max(horizontal_faces, key=lambda face: face.Origin.Z)
            base_elevation_m = float(bottom_face.Origin.Z) / M_TO_FT
            height_m = (float(top_face.Origin.Z) - float(bottom_face.Origin.Z)) / M_TO_FT
            if height_m <= 0:
                raise RuntimeError('mass geometry readback returned a non-positive extrusion height')

            rings = []
            for curve_loop in bottom_face.GetEdgesAsCurveLoops():
                ring = []
                for curve in curve_loop:
                    for point in curve.Tessellate():
                        xy = [float(point.X) / M_TO_FT, float(point.Y) / M_TO_FT]
                        if not ring or abs(ring[-1][0] - xy[0]) > 1e-9 or abs(ring[-1][1] - xy[1]) > 1e-9:
                            ring.append(xy)
                if len(ring) < 3:
                    raise RuntimeError('mass geometry readback found an incomplete profile ring')
                if abs(ring[0][0] - ring[-1][0]) > 1e-9 or abs(ring[0][1] - ring[-1][1]) > 1e-9:
                    ring.append(list(ring[0]))
                if len(ring) < 4:
                    raise RuntimeError('mass geometry readback found a degenerate closed profile ring')
                rings.append(ring)

            def signed_area(ring):
                return sum(
                    ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
                    for i in range(len(ring) - 1)
                ) / 2.0

            def canonical_ring(ring, clockwise):
                points = ring[:-1]
                if (signed_area(ring) < 0) != clockwise:
                    points = list(reversed(points))
                start = min(
                    range(len(points)),
                    key=lambda index: (points[index][0], points[index][1]),
                )
                points = points[start:] + points[:start]
                return points + [list(points[0])]

            if not rings:
                raise RuntimeError('mass geometry readback returned no profile rings')
            rings.sort(key=lambda ring: abs(signed_area(ring)), reverse=True)
            footprint = canonical_ring(rings[0], False)
            interior_rings = [canonical_ring(ring, True) for ring in rings[1:]]
            interior_rings.sort(key=lambda ring: (ring[0][0], ring[0][1]))
            __output__ = {
                'status': 'self_reported_verified',
                'element_id': int(element.Id.Value),
                'unique_id': str(element.UniqueId),
                'geometry': {
                    'footprint': footprint,
                    'interior_rings': interior_rings,
                    'base_elevation_m': base_elevation_m,
                    'height_m': height_m,
                },
            }
        """
        return dedent(script).replace("__ELEMENT_ID__", str(int(element_id))).lstrip()

    def _translate_python_references(
        self, call: StageToolRequest, request: dict[str, Any]
    ) -> None:
        """Resolve logical host/level references before embedding a Python request."""

        geometry = request.get("geometry")
        geometry = dict(geometry) if isinstance(geometry, Mapping) else {}
        properties = request.get("properties")
        properties = dict(properties) if isinstance(properties, Mapping) else {}
        resolved: dict[str, int] = {}
        references: list[tuple[Any, str, str]] = []

        def add_reference(value: Any, category: str, destination: str) -> None:
            if value is not None and destination not in resolved:
                references.append((value, category, destination))

        def first_value(*names: str) -> Any:
            for name in names:
                for source in (geometry, properties, request):
                    if name in source and source[name] is not None:
                        return source[name]
            return None

        add_reference(first_value("level_id"), "OST_Levels", "level_id")
        add_reference(first_value("top_level_id"), "OST_Levels", "top_level_id")
        if call.semantic_capability == "revit.assign_material":
            host = geometry.get("host_element")
            if host is not None:
                add_reference(
                    host,
                    str(request.get("host_category") or "OST_Walls"),
                    "revit_host_id",
                )
        elif call.semantic_capability == "revit.create_furniture_element":
            host = geometry.get("host_space_id")
            if host is not None:
                add_reference(host, "OST_Rooms", "revit_host_id")
            furniture_type = first_value("type_id", "family_type", "type", "family")
            add_reference(furniture_type, "OST_Furniture", "revit_type_id")
        elif call.semantic_capability == "revit.create_landscape_element":
            add_reference(geometry.get("host_zone"), "OST_Rooms", "revit_host_zone_id")
        elif call.semantic_capability == "revit.create_accessibility_element":
            add_reference(first_value("from", "from_node"), "OST_Rooms", "revit_from_id")
            add_reference(first_value("to", "to_node"), "OST_Rooms", "revit_to_id")
            add_reference(
                first_value("space_logical_id", "space_id"),
                "OST_Rooms",
                "revit_space_logical_id_id",
            )
        elif call.semantic_capability == "revit.create_documentation_element":
            add_reference(first_value("view_id"), "OST_Views", "revit_view_id")
            add_reference(
                first_value("view_or_table_id"),
                "OST_Views",
                "revit_view_or_table_id",
            )
        for source, category, destination_key in references:
            value = self._resolve_element_id(call, source, category=category)
            resolved[destination_key] = value
        if resolved:
            request.update(resolved)
            self._read_tool(
                "horizun_query_model",
                {
                    "element_ids": sorted(set(resolved.values())),
                    "response_mode": "compact",
                    "cache_mode": "bypass",
                },
            )

    def _document_session_arguments(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        arguments: dict[str, Any] = {"operation": "open", "expected_version": self.expected_version}
        template = payload.get("template_path")
        if template is not None:
            # Live bridge evidence, run 2026-09-15: the installed
            # horizun_document_session answers "template_path is not applicable to
            # operation 'open'. Nothing ran." Its schema fixes additionalProperties
            # to false and names file_path, not template_path, for open;
            # template_path belongs to horizun_create_family. Opening the template
            # through file_path really opened the project (title Default_M_PTB,
            # is_family_document false, element_count 3230), so the template travels
            # as the file to open instead of as an argument the bridge refuses.
            arguments["file_path"] = template
        elif payload.get("file_path") is not None:
            arguments["file_path"] = payload["file_path"]
        self._copy_optional(payload, arguments, ("idempotency_key", "audit", "on_open_dialog"))
        return arguments

    def _create_elements_arguments(
        self, call: StageToolRequest, payload: dict[str, Any]
    ) -> dict[str, Any]:
        target = payload.get("target_document") or self.target_document
        if not isinstance(target, str) or not target.strip():
            raise HorizunRequestError(
                "horizun_create_elements requires target_document on the call or invoker"
            )
        elements = payload.get("elements")
        if elements is None:
            elements = [self._element_from_stage(call, payload)]
        elif isinstance(elements, Mapping):
            elements = [dict(elements)]
        elif not isinstance(elements, list) or not all(
            isinstance(element, Mapping) for element in elements
        ):
            raise HorizunRequestError("elements must be a list of objects")
        translated_elements: list[dict[str, Any]] = []
        referenced_ids: set[int] = set()
        for element in elements:
            translated, ids = self._translate_typed_element(call, dict(element))
            translated_elements.append(translated)
            referenced_ids.update(ids)
        if referenced_ids:
            self._read_tool(
                "horizun_query_model",
                {
                    "element_ids": sorted(referenced_ids),
                    "response_mode": "compact",
                    "cache_mode": "bypass",
                },
            )
        arguments: dict[str, Any] = {
            "target_document": target,
            "units": payload.get("units", "m"),
            "elements": translated_elements,
        }
        self._copy_optional(
            payload,
            arguments,
            (
                "dry_run",
                "confirmation_token",
                "transaction_name",
                "idempotency_key",
                "validation_mode",
                "tabular_source",
            ),
        )
        self._schedule_readback(call, elements, translated_elements, arguments)
        return arguments

    def _translate_typed_element(
        self, call: StageToolRequest, element: dict[str, Any]
    ) -> tuple[dict[str, Any], set[int]]:
        """Normalize coordinates and replace every compiler reference with an ElementId."""

        kind = str(element.get("kind") or _ELEMENT_KIND[call.semantic_capability])
        element["kind"] = kind
        logical_id = str(element.pop("logical_id", call.logical_id))
        self._normalize_coordinates(element)
        if kind == "wall_opening":
            self._require_diagonal_corners(element, logical_id)
        referenced_ids: set[int] = set()
        for field in ("level_id", "top_level_id", "host_id", "type_id"):
            if field not in element or element[field] is None:
                continue
            value = element[field]
            category = self._reference_category(call.semantic_capability, field)
            if category is None:
                continue
            element[field] = self._resolve_element_id(
                call,
                value,
                category=category,
            )
            referenced_ids.add(int(element[field]))
        parameters = element.get("parameters")
        parameters = dict(parameters) if isinstance(parameters, Mapping) else {}
        # Revit refuses a parameter name that does not exist on the element, so only
        # real built-in parameters are written: the mark carries the logical ID and
        # the instance comments carry the semantic capability that produced it.
        # A level and a grid carry no mark at all, and the bridge refuses the whole
        # batch when one is offered (live probe: "parameters.ALL_MODEL_MARK:
        # BuiltInParameter exists but is not present on this type"), so the mark is
        # written where the category really has it and the comments still identify
        # the element everywhere.
        # A room reports the same refusal for the mark, and it also has no instance
        # comments, so a room receives comments alone.
        if kind not in _MARK_ONLY_KINDS:
            parameters.setdefault("ALL_MODEL_MARK", logical_id)
        if kind not in _MARKLESS_KINDS:
            parameters.setdefault(
                "ALL_MODEL_INSTANCE_COMMENTS",
                f"Amanda {logical_id} ({call.semantic_capability})",
            )
        if parameters:
            element["parameters"] = parameters
        elif "parameters" in element:
            element.pop("parameters")
        return element, referenced_ids

    _READBACK_FIELDS = (
        "unique_id",
        "name",
        "category",
        "type",
        "type_id",
        "level",
        "source_kind",
        "source_model",
        "source_reference",
    )

    def _schedule_readback(
        self,
        call: StageToolRequest,
        elements: list[Any],
        translated_elements: list[dict[str, Any]],
        arguments: Mapping[str, Any],
    ) -> None:
        """Plan the independent READ that recovers what a typed create wrote."""

        key = arguments.get("idempotency_key")
        if not isinstance(key, str) or not key.strip():
            return
        if arguments.get("dry_run") is not False:
            return
        if len(elements) != 1 or len(translated_elements) != 1:
            return
        parameters = translated_elements[0].get("parameters")
        mark = parameters.get("ALL_MODEL_MARK") if isinstance(parameters, Mapping) else None
        if isinstance(mark, str) and mark.strip():
            self._pending_readbacks[key] = {
                "logical_id": call.logical_id,
                "tool": "horizun_query_model",
                "arguments": {
                    "parameters": [
                        {"name": "ALL_MODEL_MARK", "operator": "equals", "value": mark}
                    ],
                    "return_fields": list(self._READBACK_FIELDS),
                    "response_mode": "compact",
                    "cache_mode": "bypass",
                },
            }
            return
        kind = translated_elements[0].get("kind")
        category = _MARKLESS_READBACK_CATEGORIES.get(kind)
        if category is not None:
            self._pending_readbacks[key] = {
                "logical_id": call.logical_id,
                "tool": "horizun_query_model",
                "arguments": {
                    "categories": [category],
                    "return_fields": list(self._READBACK_FIELDS),
                    "response_mode": "compact",
                    "cache_mode": "bypass",
                },
                "match_by_logical_id": True,
            }
            return
        if kind == "wall_opening":
            # The accepted query filters (including category, level and bounding
            # box) cannot identify a newly created opening by its logical ID. The
            # opening also cannot carry mark or comments, so an invented query
            # would make verification look stronger than the evidence permits.
            self._pending_readbacks[key] = {
                "logical_id": call.logical_id,
                "readback_unavailable": dict(_WALL_OPENING_READBACK_UNAVAILABLE),
            }
            return

    def _resolve_confirmation(
        self, tool: str, arguments: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Spend the bridge's own two-step confirmation instead of inventing a token.

        The Horizun bridge refuses a real typed creation without a token it issued
        from a dry run of the very same request, so the invoker asks for the plan
        first, keeps its fingerprint as evidence and then applies it.
        """

        resolved = dict(arguments)
        if tool != "horizun_create_elements" or resolved.get("dry_run") is not False:
            return resolved
        if resolved.get("confirmation_token"):
            return resolved
        plan = dict(resolved)
        plan["dry_run"] = True
        key = plan.get("idempotency_key")
        if isinstance(key, str) and key.strip():
            plan["idempotency_key"] = f"{key}:dry-run"
        try:
            reply = self.transport.call(tool, plan)
        except Exception as exc:  # noqa: BLE001 - the provider boundary reports failures
            raise HorizunRequestError(
                f"horizun_create_elements dry run could not be requested: {exc}"
            ) from exc
        result = self._result(tool, reply, None)
        payload = result.read_payload
        token = payload.get("confirmation_token") if isinstance(payload, Mapping) else None
        if not result.reported_success or not isinstance(token, str) or not token.strip():
            raise HorizunRequestError(
                "horizun_create_elements dry run did not return a confirmation token: "
                f"{result.error or payload}"
            )
        resolved["confirmation_token"] = token
        if isinstance(key, str) and key.strip():
            plan_resolved = payload.get("plan_resolved") if isinstance(payload, Mapping) else None
            preview = payload.get("change_preview") if isinstance(payload, Mapping) else None
            self._plan_evidence[key] = {
                "dry_run_tool": tool,
                "dry_run_key": plan.get("idempotency_key"),
                "plan_resolved": plan_resolved if isinstance(plan_resolved, Mapping) else None,
                "change_preview_fingerprint": (
                    preview.get("fingerprint") if isinstance(preview, Mapping) else None
                ),
                "confirmation_expires_utc": (
                    payload.get("confirmation_expires_utc")
                    if isinstance(payload, Mapping)
                    else None
                ),
            }
        return resolved

    def _merge_readback(self, result: StageToolResult, key: Any) -> None:
        """Attach the independent read to the write payload; never invent a result."""

        if not isinstance(key, str):
            return
        plan = self._pending_readbacks.pop(key, None)
        if plan is None:
            return
        memo: dict[str, Any] = {
            "write_tool": result.get("tool"),
            "logical_id": plan["logical_id"],
        }
        if plan.get("geometry_readback"):
            self._merge_mass_geometry_readback(result, key, plan, memo)
            return
        unavailable_reason = plan.get("readback_unavailable")
        if unavailable_reason is None:
            memo["readback_tool"] = plan["tool"]
            memo["readback_query"] = plan["arguments"]
        confirmation = self._plan_evidence.pop(key, None)
        if confirmation is not None:
            memo["plan"] = confirmation
        if not result.reported_success:
            memo["readback_verified"] = False
            memo["readback_error"] = "write did not report success; the model was not read back"
        elif unavailable_reason is not None:
            memo["readback_verified"] = False
            memo["readback_error"] = dict(unavailable_reason)
        else:
            try:
                payload = self._read_tool(plan["tool"], plan["arguments"])
            except Exception as exc:  # noqa: BLE001 - a failed read never becomes a pass
                memo["readback_verified"] = False
                memo["readback_error"] = f"{type(exc).__name__}: {exc}"
            else:
                rows = self._rows(payload)
                memo["readback_rows"] = rows
                matching_rows = rows
                if plan.get("match_by_logical_id"):
                    matching_rows = [
                        row
                        for row in rows
                        if self._row_matches(row, plan["logical_id"])
                    ]
                element_id = (
                    self._row_element_id(matching_rows[0])
                    if len(matching_rows) == 1
                    else None
                )
                if element_id is not None:
                    memo["element_id"] = element_id
                    self._logical_ids[plan["logical_id"]] = element_id
                if len(matching_rows) == 1:
                    for field in self._READBACK_FIELDS:
                        value = matching_rows[0].get(field)
                        if value is not None:
                            memo.setdefault(field, value)
                unique_id = memo.get("unique_id")
                stable_unique_id = isinstance(unique_id, str) and bool(unique_id.strip())
                memo["readback_verified"] = bool(
                    len(matching_rows) == 1
                    and (not plan.get("match_by_logical_id") or stable_unique_id)
                    and memo.get("unique_id")
                    and element_id is not None
                )
        payload = result.read_payload
        merged = dict(payload) if isinstance(payload, Mapping) else {}
        for name, value in memo.items():
            merged.setdefault(name, value)
        result["read_payload"] = merged
        result["payload"] = merged

    def _merge_mass_geometry_readback(
        self,
        result: StageToolResult,
        key: str,
        plan: Mapping[str, Any],
        memo: dict[str, Any],
    ) -> None:
        """Read the created DirectShape solid after the write call has returned."""

        memo["readback_tool"] = plan["tool"]
        element_id = self._row_element_id(result.read_payload)
        if element_id is None:
            element_id = self._logical_ids.get(str(plan["logical_id"]))
        if not result.reported_success:
            memo["readback_verified"] = False
            memo["readback_error"] = "write did not report success; the model was not read back"
        elif element_id is None:
            memo["readback_verified"] = False
            memo["readback_error"] = "mass write returned no element id for geometric readback"
        else:
            read_key = f"{key}:mass-geometry-readback"
            arguments = {
                **dict(plan["arguments"]),
                "code": self._mass_geometry_readback_script(element_id),
                "idempotency_key": read_key,
            }
            try:
                payload = self._read_tool(plan["tool"], arguments)
            except Exception as exc:  # noqa: BLE001 - a failed read never becomes a pass
                memo["readback_verified"] = False
                memo["readback_error"] = f"{type(exc).__name__}: {exc}"
            else:
                if isinstance(payload, Mapping):
                    observed_id = self._row_element_id(payload)
                    unique_id = payload.get("unique_id")
                    geometry = payload.get("geometry")
                    memo["geometry_readback_provenance"] = "SELF_REPORTED_PYTHON_READBACK"
                    memo["geometry_readback_element_id"] = observed_id
                    if isinstance(unique_id, str) and unique_id.strip():
                        memo["unique_id"] = unique_id
                    if isinstance(geometry, Mapping):
                        memo["geometry"] = dict(geometry)
                    memo["readback_verified"] = bool(
                        str(payload.get("status", "")).casefold() == "self_reported_verified"
                        and observed_id == element_id
                        and isinstance(unique_id, str)
                        and bool(unique_id.strip())
                        and isinstance(geometry, Mapping)
                        and isinstance(geometry.get("footprint"), list)
                        and isinstance(geometry.get("interior_rings"), list)
                        and geometry.get("base_elevation_m") is not None
                        and geometry.get("height_m") is not None
                    )
                    if not memo["readback_verified"]:
                        memo["readback_error"] = "mass readback omitted stable identity or solid geometry"
                else:
                    memo["readback_verified"] = False
                    memo["readback_error"] = "mass readback returned no structured geometry"
        original = result.read_payload
        merged = dict(original) if isinstance(original, Mapping) else {}
        for name, value in memo.items():
            if name in {
                "readback_tool",
                "readback_verified",
                "readback_error",
                "geometry_readback_provenance",
                "geometry_readback_element_id",
            }:
                merged[name] = value
            else:
                merged.setdefault(name, value)
        if memo.get("readback_verified"):
            if "geometry" in memo:
                merged["geometry"] = memo["geometry"]
            if "unique_id" in memo:
                merged["unique_id"] = memo["unique_id"]
            observed_id = memo.get("geometry_readback_element_id")
            if observed_id is not None:
                merged["element_id"] = observed_id
        else:
            # A stale write response cannot stand in for missing post-write
            # geometry. Remove its self-reported shape so verification fails closed.
            merged.pop("geometry", None)
            merged.pop("unique_id", None)
        result["read_payload"] = merged
        result["payload"] = merged

    def _resolve_element_id(
        self,
        call: StageToolRequest,
        value: Any,
        *,
        category: str,
    ) -> int:
        if isinstance(value, bool):
            raise HorizunRequestError(f"{category} reference must be an integer or logical ID")
        if isinstance(value, int):
            return value
        if not isinstance(value, str) or not value.strip():
            raise HorizunRequestError(f"{category} reference must be an integer or logical ID")
        cache_key = f"{category}:{value.strip()}"
        stage_cache = self._stage_read_cache.setdefault(call.stage, {})
        resolution_cache = self._stage_resolution_cache.setdefault(call.stage, {})
        cached_id = resolution_cache.get(cache_key)
        if cached_id is not None:
            return cached_id
        logical_cached = self._logical_ids.get(value.strip())
        if logical_cached is not None:
            resolution_cache[cache_key] = logical_cached
            return logical_cached
        catalog_path = call.payload.get("type_catalog_path") or call.payload.get("catalog_path")
        if catalog_path is not None and category != "OST_Levels":
            catalog = self._read_tool(
                "horizun_catalog_lookup",
                {
                    "catalog_path": catalog_path,
                    "code": value.strip(),
                    **(
                        {"separator": call.payload["catalog_separator"]}
                        if call.payload.get("catalog_separator") is not None
                        else {}
                    ),
                },
            )
            if isinstance(catalog, Mapping) and catalog.get("exists") is False:
                raise HorizunRequestError(
                    f"logical type {value!r} is absent from catalog {catalog_path!r}"
                )
        rows = stage_cache.get(category)
        if rows is None:
            raw = self._read_tool(
                "horizun_list_elements",
                {"category": category, "include_links": False, "max_rows": 2000},
            )
            rows = self._rows(raw)
            # horizun_list_elements answers with instances, and a wall TYPE is
            # not an instance, so on a real model that listing answers zero rows
            # for a type the template really has.  When it comes back empty the
            # type-aware query is asked instead, which the live bridge answers
            # with the type of each element in the category.  Nothing about the
            # declared-catalog check above changes.
            if not rows and category != "OST_Levels":
                raw = self._read_tool(
                    "horizun_query_model",
                    {
                        "categories": [category],
                        "response_mode": "compact",
                        "cache_mode": "bypass",
                        "include_links": False,
                        "include_types": True,
                        "max_rows": 2000,
                    },
                )
                rows = self._rows(raw)
            stage_cache[category] = rows
        matches = [row for row in rows if self._row_matches(row, value)]
        if len(matches) != 1:
            raise HorizunRequestError(
                f"could not resolve logical ID {value!r} in {category}: "
                f"expected exactly one match, found {len(matches)}"
            )
        resolved = self._row_element_id(matches[0])
        if resolved is None:
            raise HorizunRequestError(
                f"resolved logical ID {value!r} in {category} has no integer element_id"
            )
        resolution_cache[cache_key] = resolved
        return resolved

    @staticmethod
    def _reference_category(semantic: str, field: str) -> str | None:
        if field in {"level_id", "top_level_id"}:
            return "OST_Levels"
        if field == "host_id":
            return "OST_Walls"
        if field != "type_id":
            return None
        if semantic in {"revit.create_wall", "revit.create_internal_wall", "revit.create_opening"}:
            return "OST_Walls"
        if semantic in {"revit.create_floor", "revit.create_slab"}:
            return "OST_Floors"
        if semantic == "revit.create_roof":
            return "OST_Roofs"
        return "OST_GenericModel"

    @staticmethod
    def _rows(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [dict(row) for row in payload if isinstance(row, Mapping)]
        if not isinstance(payload, Mapping):
            return []
        for key in ("rows", "elements", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [dict(row) for row in value if isinstance(row, Mapping)]
        return []

    @staticmethod
    def _row_element_id(row: Mapping[str, Any]) -> int | None:
        for key in ("element_id", "id", "ElementId", "revit_id"):
            value = row.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                return value
            if isinstance(value, str) and value.strip().lstrip("-").isdigit():
                return int(value)
        return None

    @classmethod
    def _row_matches(cls, row: Mapping[str, Any], logical_id: str) -> bool:
        wanted = logical_id.strip().casefold()
        values: list[Any] = []
        for key in (
            "logical_id",
            "logicalId",
            "name",
            "type_id",
            "type_name",
            "type",
            "family_type",
            "family",
            "code",
            "key",
        ):
            values.append(row.get(key))
        parameters = row.get("parameters")
        if isinstance(parameters, Mapping):
            values.extend(parameters.values())
            for key, value in parameters.items():
                if str(key).casefold() in {"amanda_logical_id", "logical_id"}:
                    values.append(value)
        return any(isinstance(value, (str, int, float)) and str(value).strip().casefold() == wanted for value in values)

    @staticmethod
    def _normalize_coordinates(element: dict[str, Any]) -> None:
        # A room insertion ignores Z, and the bridge refuses the whole batch when a
        # two-dimensional point is lifted to three, so a room point stays flat.
        for field in ("start", "end", "center", "corner_1", "corner_2"):
            value = element.get(field)
            if isinstance(value, (list, tuple)) and len(value) == 2:
                element[field] = [float(value[0]), float(value[1]), 0.0]
        profile = element.get("profile")
        if not isinstance(profile, list) or not profile:
            return
        loops = HorizunInvoker._closed_profile(profile)
        if loops is not None:
            element["profile"] = loops

    @staticmethod
    def _require_diagonal_corners(element: Mapping[str, Any], logical_id: str) -> None:
        """Refuse a wall opening whose diagonal corners share a height.

        Live probe evidence, tool-lab/horizun/results/probe-api7-live.json:
        document.Create.NewOpening refused the flat pair with "Failed to create an
        opening on the wall." and committed the same wall with corners at 0.1 m and
        2.1 m. A flat pair cannot be recognized as a bad request after the fact,
        because Revit only refuses it once it has already been asked, so the
        request is refused here, with the cause named, before any tool call.
        """

        def corner(field: str) -> list[float] | None:
            raw = element.get(field)
            if not isinstance(raw, (list, tuple)) or len(raw) != 3:
                return None
            try:
                return [float(value) for value in raw]
            except (TypeError, ValueError):
                return None

        first = corner("corner_1")
        second = corner("corner_2")
        if first is None or second is None:
            raise HorizunRequestError(
                f"wall opening {logical_id!r} requires corner_1 and corner_2 as "
                "three-dimensional points"
            )
        if abs(first[2] - second[2]) <= 1e-9:
            raise HorizunRequestError(
                f"wall opening {logical_id!r} requires diagonal corners at different "
                f"heights: corner_1 z={first[2]:g} and corner_2 z={second[2]:g} are equal, "
                "and Revit refuses a flat pair with 'Failed to create an opening on "
                "the wall.'"
            )

    @staticmethod
    def _closed_profile(profile: list[Any]) -> list[list[list[float]]] | None:
        """Return the bridge shape for a slab outline: closed loops of 3D points.

        Live probe evidence: a flat ring of XY pairs is refused with
        "profile[0][0] must contain exactly three coordinates."  The bridge wants
        a list of closed loops, so a bare ring becomes one closed loop and every
        point carries three coordinates.
        """

        def is_point(value: Any) -> bool:
            return (
                isinstance(value, (list, tuple))
                and len(value) in {2, 3}
                and all(
                    isinstance(coordinate, (int, float))
                    and not isinstance(coordinate, bool)
                    for coordinate in value
                )
            )

        if all(is_point(point) for point in profile):
            rings: list[list[Any]] = [profile]
        elif all(
            isinstance(loop, (list, tuple)) and loop and all(is_point(p) for p in loop)
            for loop in profile
        ):
            rings = [list(loop) for loop in profile]
        else:
            return None
        loops: list[list[list[float]]] = []
        for ring in rings:
            points = [
                [float(p[0]), float(p[1]), float(p[2]) if len(p) == 3 else 0.0]
                for p in ring
            ]
            if len(points) >= 3 and points[0] != points[-1]:
                points.append(list(points[0]))
            loops.append(points)
        return loops

    def _element_from_stage(
        self, call: StageToolRequest, payload: Mapping[str, Any]
    ) -> dict[str, Any]:
        kind = _ELEMENT_KIND[call.semantic_capability]
        explicit = payload.get("element")
        if isinstance(explicit, Mapping):
            element = dict(explicit)
            element.setdefault("kind", kind)
            return element
        geometry = payload.get("geometry")
        geometry = dict(geometry) if isinstance(geometry, Mapping) else {}
        properties = payload.get("properties")
        properties = dict(properties) if isinstance(properties, Mapping) else {}
        element: dict[str, Any] = {"kind": kind}
        for field in _ELEMENT_FIELDS[kind]:
            value = self._first_value(field, payload, geometry, properties)
            if value is not None:
                element[field] = value
        required = {
            "level": ("elevation",),
            "grid": ("start", "end"),
            "wall": ("start", "end", "level_id", "height"),
            "floor": ("profile", "level_id"),
            "roof": ("profile", "level_id"),
            "room": ("point", "level_id"),
"wall_opening": ("host_id",),
"wall_opening": ("host_id", "corner_1", "corner_2"),
        }[kind]
        missing = [field for field in required if field not in element]
        if missing:
            raise HorizunRequestError(
                f"{call.semantic_capability} is missing provider fields: {', '.join(missing)}"
            )
        return element

    @staticmethod
    def _first_value(
        field: str, *sources: Mapping[str, Any]
    ) -> Any:
        for source in sources:
            if field in source:
                return source[field]
        aliases = {
            "elevation": ("elevation_m",),
            "profile": ("footprint",),
            "point": ("location",),
            "level_id": ("level",),
            "host_id": ("host_logical_id", "host_element_id"),
        }
        for alias in aliases.get(field, ()):
            for source in sources:
                if alias in source:
                    return source[alias]
        return None

    def _query_arguments(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        allowed = {
            "element_ids",
            "response_mode",
            "cache_mode",
            "include_diagnostics",
            "categories",
            "family",
            "type",
            "name",
            "level",
            "parameters",
            "bounding_box",
            "scope",
            "view_id",
            "include_links",
            "return_parameters",
            "include_bounding_box",
            "include_mep",
            "coordinate_units",
            "include_types",
            "cursor",
            "max_rows",
            "group_by",
            "parameter_format",
            "return_fields",
            "sum_parameters",
        }
        return {key: value for key, value in payload.items() if key in allowed}

    def _open_arguments(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        arguments: dict[str, Any] = {}
        self._copy_optional(
            payload,
            arguments,
            (
                "path",
                "cloud_project_guid",
                "cloud_model_guid",
                "cloud_region",
                "allow_upgrade",
                "detach",
                "open_central",
                "open_all_worksets",
                "audit",
                "on_open_dialog",
                "idempotency_key",
            ),
        )
        if "path" not in arguments and payload.get("template_path") is not None:
            arguments["path"] = payload["template_path"]
        arguments.setdefault("expected_version", self.expected_version)
        return arguments

    def _save_arguments(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        target = payload.get("target_document") or self.target_document
        if not isinstance(target, str) or not target.strip():
            raise HorizunRequestError(
                "horizun_save_document requires target_document on the call or invoker"
            )
        arguments = {"target_document": target}
        if payload.get("expected_document") is not None:
            arguments["expected_document"] = payload["expected_document"]
        if payload.get("require_gate") is not None:
            arguments["require_gate"] = payload["require_gate"]
        if payload.get("idempotency_key") is not None:
            arguments["idempotency_key"] = payload["idempotency_key"]
        return arguments

    @staticmethod
    def _copy_optional(
        source: Mapping[str, Any], target: dict[str, Any], names: tuple[str, ...]
    ) -> None:
        for name in names:
            if source.get(name) is not None:
                target[name] = source[name]

    @staticmethod
    def _is_mutating(tool: str, arguments: Mapping[str, Any]) -> bool:
        if tool not in _MUTATING_TOOLS:
            return False
        if tool in _READ_ONLY_TOOLS:
            return False
        if arguments.get("dry_run") is True:
            return False
        return not (
            tool == "horizun_document_session" and arguments.get("operation") == "inspect"
        )

    def _require_idempotency_if_mutating(
        self, tool: str, arguments: Mapping[str, Any], key: Any
    ) -> None:
        if not self._is_mutating(tool, arguments):
            return
        if not isinstance(key, str) or not key.strip():
            raise HorizunRequestError(
                f"{tool} mutation requires the orchestrator idempotency_key"
            )

    def _result(
        self, tool: str, reply: Mapping[str, Any] | None, key: Any
    ) -> StageToolResult:
        if reply is None:
            error = {"type": "McpTimeout", "message": "Horizun MCP returned no reply"}
            return StageToolResult(
                provider=self.provider,
                tool=tool,
                reported_success=False,
                read_payload={"error": error},
                raw={},
                error=error,
                idempotency_key=key if isinstance(key, str) else None,
            )
        raw = dict(reply)
        error = raw.get("error")
        result = raw.get("result")
        if not isinstance(result, Mapping):
            result = raw
        nested_error = result.get("error")
        if error is None and nested_error is not None:
            error = nested_error
        read_payload = result.get("structuredContent")
        if read_payload is None:
            read_payload = self._text_payload(result.get("content"))
        if read_payload is None and error is not None:
            read_payload = {"error": error}
        success = error is None and not bool(result.get("isError", False))
        # The bridge reports a failed Python route with isError and puts the Revit
        # traceback in content[0].text, so keep that text where a caller can read
        # the cause instead of seeing only a failure code.
        diagnostic = self._text_diagnostic(result.get("content"))
        if diagnostic is not None:
            if isinstance(read_payload, Mapping):
                read_payload = dict(read_payload)
                read_payload.setdefault("diagnostic", diagnostic)
            else:
                read_payload = {"payload": read_payload, "diagnostic": diagnostic}
            if error is None:
                error = {"type": "PythonExecutionFailed", "diagnostic": diagnostic}
            elif isinstance(error, Mapping):
                error = dict(error)
                error.setdefault("diagnostic", diagnostic)
        if (
            tool == "horizun_execute_python"
            and isinstance(read_payload, Mapping)
            and str(read_payload.get("status", "")).casefold() in {"failed", "error"}
        ):
            error = dict(read_payload)
            success = False
        return StageToolResult(
            provider=self.provider,
            tool=tool,
            reported_success=success,
            read_payload=read_payload,
            raw=raw,
            error=error,
            idempotency_key=key if isinstance(key, str) else None,
        )

    @staticmethod
    def _text_payload(content: Any) -> Any:
        if not isinstance(content, list):
            return None
        for item in content:
            if not isinstance(item, Mapping) or item.get("type") != "text":
                continue
            text = item.get("text")
            if not isinstance(text, str):
                continue
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _text_diagnostic(content: Any) -> str | None:
        """Return the raw non-JSON text of a failed call, which is the traceback."""

        if not isinstance(content, list):
            return None
        for item in content:
            if not isinstance(item, Mapping) or item.get("type") != "text":
                continue
            text = item.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            try:
                json.loads(text)
            except json.JSONDecodeError:
                return text
        return None


__all__ = [
    "EXPECTED_REVIT_VERSION",
    "PROVIDER_NAME",
    "HorizunInvoker",
    "HorizunRequestError",
    "HorizunUnsupportedCapability",
    "StageToolRequest",
    "StageToolResult",
]
