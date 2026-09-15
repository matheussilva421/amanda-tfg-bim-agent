"""Generate state/providers/revitcortex-toolmap.yaml from the verified artifacts.

Plan 02, Task 6 states the rule plainly: the toolmap must be generated from
actual catalog results, never from typed guesses.  Task 14 repeats it for the
Cortex provider.  This script is that generator, so the rule holds by
construction:

* tool-lab/revitcortex/tool-catalog.json, captured from the published server
  over the same stdio JSON-RPC transport a client uses, is the only source of
  tool names and of input fields;
* tool-lab/revitcortex/tool-safety.json supplies the effect flags, because the
  Cortex catalog publishes no 'annotations' block; that file is parsed out of
  the pinned vendor checkout by extract_tool_safety.py;
* a capability may only be NOT_AVAILABLE with a written justification and a
  verified alternative;
* every declared tool name is resolved against the catalog before anything is
  written, so a stale name fails the generator instead of shipping.

Usage::

    python tool-lab/revitcortex/generate_toolmap.py
    python tool-lab/revitcortex/generate_toolmap.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "tool-lab" / "revitcortex" / "tool-catalog.json"
SAFETY_PATH = ROOT / "tool-lab" / "revitcortex" / "tool-safety.json"
OUTPUT_PATH = ROOT / "state" / "providers" / "revitcortex-toolmap.yaml"

SOURCE_COMMIT = "8b2556daefb2bf88f0a7a17bf28f2352fe0b0e33"
SOURCE_TOOLS_DIR = ROOT / "vendor" / "RevitCortex" / "src" / "RevitCortex.Tools"
SOURCE_URL = "https://github.com/LuDattilo/RevitCortex.git"

#: Capability declarations.  Every tool name is resolved against the catalog and
#: every effect flag is read from the source parse before anything is written.
CAPABILITIES = [
    {
        "semantic": "health",
        "tools": ["say_hello", "check_model_health"],
        "note": (
            "say_hello reports the server and bridge handshake; check_model_health "
            "returns a health score for the ACTIVE document, so call it before a write"
        ),
    },
    {
        "semantic": "document_info",
        "tool": "get_project_info",
        "alternatives": ["get_current_view_info"],
        "note": (
            "project name, address, levels, phases, worksets and links of the active "
            "document; the levels list is what the creation tools resolve against"
        ),
    },
    {
        "semantic": "document_query",
        "tools": [
            "ai_element_filter",
            "get_elements_by_unique_id",
            "get_current_view_elements",
            "filter_by_parameter_value",
        ],
        "note": (
            "element queries by category, class, family, bounding box, level and "
            "parameter value with combineWith/invert for AND/OR/NOT"
        ),
    },
    {
        "semantic": "model_scan",
        "tools": [
            "workflow_model_audit",
            "analyze_model_statistics",
            "audit_families",
        ],
        "note": (
            "workflow_model_audit carries warnings and families; "
            "analyze_model_statistics is the cheapest whole-model census"
        ),
    },
    {
        "semantic": "level",
        "tool": "create_level",
        "units": "mm",
        "dry_run_default": True,
        "required_fields": ["name", "elevation"],
        "actions": ["create", "set", "rename", "delete"],
        "note": (
            "preview-first: dryRun defaults to true, so a real level needs "
            "dryRun=false in the same call. One tool carries create/set/rename/delete; "
            "there is no separate element_kind field the way the Horizun provider has. "
            "Elevation is read and written in mm"
        ),
    },
    {
        "semantic": "wall",
        "tool": "create_line_based_element",
        "units": "mm",
        "dry_run_default": False,
        "required_fields": ["specs"],
        "spec_required_fields": ["category", "locationLine"],
        "note": (
            "specs is a JSON array carried as a string: "
            "[{category, locationLine:{p0,p1,pMid?}, typeId?, height?, baseLevel?, "
            "baseOffset?}]. height defaults to 3000 mm and baseLevel is an elevation "
            "in mm used to pick the nearest level, not an element id"
        ),
    },
    {
        "semantic": "floor",
        "tool": "create_floor",
        "units": "mm",
        "dry_run_default": False,
        "required_fields": ["boundaryPoints"],
        "alternatives": ["create_surface_based_element"],
        "note": (
            "boundaryPoints is a JSON array of {x,y} in mm with at least three points, "
            "or pass roomId to take the boundary from an existing room; holes is a JSON "
            "array of inner loops and levelElevation in mm picks the nearest level"
        ),
    },
    {
        "semantic": "room",
        "tool": "create_room",
        "units": "mm",
        "dry_run_default": False,
        "required_fields": ["levelId", "x", "y"],
        "schema_divergence": (
            "the published schema documents levelId/x/y as three flat arguments, but "
            "CreateRoomTool.cs reads input[location] as an {x, y, z} object in mm "
            "and only levelId by name; a call built from the schema alone fails with "
            "'location {x, y, z} in mm is required'"
        ),
        "note": (
            "the room needs bounding walls in place first, otherwise the documented "
            "failure is 'location may not be inside enclosed walls'"
        ),
    },
    {
        "semantic": "door",
        "tool": "create_point_based_element",
        "units": "mm",
        "dry_run_default": False,
        "hosted": True,
        "required_fields": ["specs", "hostWallId", "locationPoint"],
        "spec_required_fields": ["hostWallId", "locationPoint", "typeId"],
        "note": (
            "no door-specific tool exists: a door is a wall-hosted family instance. "
            "Set hostWallId to the wall element id and pass locationPoint; the tool then "
            "calls NewFamilyInstance(locationPoint, symbol, hostWall, level, ...) and "
            "auto-detects door/window facing, with facingFlipped and rotation available"
        ),
    },
    {
        "semantic": "window",
        "tool": "create_point_based_element",
        "units": "mm",
        "dry_run_default": False,
        "hosted": True,
        "required_fields": ["specs", "hostWallId", "locationPoint"],
        "spec_required_fields": ["hostWallId", "locationPoint", "typeId"],
        "note": (
            "same hosted path as a door: without hostWallId the tool falls back to "
            "NewFamilyInstance(locationPoint, symbol, level, ...), which places an "
            "unhosted instance rather than a window in a wall"
        ),
    },
    {
        "semantic": "views",
        "tool": "create_view",
        "units": "mm",
        "dry_run_default": False,
        "required_fields": ["viewType"],
        "view_types": ["FloorPlan", "CeilingPlan", "Section", "Elevation", "Drafting", "ThreeD"],
        "note": (
            "one tool covers floor, ceiling, section, elevation, drafting and 3D views; "
            "levelName is preferred over levelId for plans and originX/Y/Z in mm position "
            "the view"
        ),
    },
    {
        "semantic": "section_elevation",
        "tool": "create_view",
        "units": "mm",
        "dry_run_default": False,
        "required_fields": ["viewType"],
        "alternatives": ["section_box_from_selection"],
        "note": (
            "sections and elevations are viewType values of create_view, not separate "
            "tools; section_box_from_selection crops an existing 3D view around a "
            "selection instead of creating a section view"
        ),
    },
    {
        "semantic": "sheets",
        "tools": ["create_sheet", "batch_create_sheets", "place_viewport"],
        "alternatives": ["create_placeholder_sheets"],
        "units": "mm",
        "dry_run_default": False,
        "note": (
            "create_sheet takes sheetNumber and sheetName; batch_create_sheets carries a "
            "JSON array of {number, name, titleBlockName?, viewIds?} and can place views "
            "in the same call; place_viewport positions a viewport with positionX/Y in mm"
        ),
    },
    {
        "semantic": "schedules",
        "tools": ["create_schedule", "create_preset_schedule"],
        "alternatives": ["export_schedule", "get_schedule_data"],
        "dry_run_default": False,
        "presets": ["RoomFinish", "DoorHardware", "WallQuantities", "WindowSchedule"],
        "note": (
            "create_schedule takes one category plus fields; create_preset_schedule "
            "covers the four room/door/wall/window presets, which is the shorter route "
            "for the core fixture"
        ),
    },
    {
        "semantic": "dimensions",
        "tool": "create_dimensions",
        "units": "mm",
        "dry_run_default": False,
        "required_fields": ["dimensions"],
        "alternatives": ["find_undimensioned_elements"],
        "note": (
            "dimensions is a JSON array carried as a string; element mode uses "
            "referenceIds and point-to-point mode uses startPoint/endPoint, both with "
            "viewId and an optional linePoint in mm"
        ),
    },
    {
        "semantic": "site_toposolid",
        "availability": "NOT_AVAILABLE",
        "justification": (
            "No published Cortex tool mentions a toposolid, topographic surface, site, "
            "grading, terrain or mass in its name or description: a scan of all 288 tool "
            "names and descriptions returns zero matches. The only surface-based creation "
            "tool, create_surface_based_element, is documented as floors and ceilings. "
            "The project site data is also MISSING for topography, so no surface could be "
            "validated even if one were created."
        ),
        "verified_alternative": (
            "Ask the machine owner to create or grade the surface by hand in Revit, then "
            "use the Cortex tools that already work on levels, walls, floors and rooms, or "
            "use the Horizun route that is PROVEN on this machine (P02-T12, 2026-09-15): "
            "horizun_execute_python called the Revit API Toposolid.Create for a synthetic "
            "20x20 m surface and the result survived save/close/reopen "
            "(tool-lab/horizun/results/t12-toposolid.json). Cortex has no Python surface "
            "of its own, so this capability is owned by the Horizun provider."
        ),
        "catalog_scan": {
            "tools_matching_topo_site_grading_terrain_mass": [],
            "surface_based_tool_documented_for": "floors and ceilings",
        },
    },
    {
        "semantic": "save",
        "availability": "NOT_AVAILABLE",
        "justification": (
            "The published catalog has no document save tool. Every tool name and "
            "description was searched for save and close words: the only matches are "
            "save_selection, which stores a named selection filter, and "
            "sync_csv_parameters, which writes parameter values into the model. The "
            "pinned source confirms it: the only SaveAs calls in RevitCortex.Tools write "
            "family documents in a temporary folder (ExportFamiliesTool, "
            "ListFamilySizesTool) or an Excel workbook (ExportToExcelTool, "
            "WorkflowDataRoundtripTool); no tool calls Document.Save on the project, so a "
            "session through Cortex alone cannot prove disk persistence."
        ),
        "verified_alternative": (
            "The Horizun provider owns save and document session on this machine: "
            "horizun_save_document preserves the file and re-reads the on-disk timestamp "
            "and size, and horizun_document_session carries open, save_as, close and "
            "inspect. Both are already proven in tool-lab/horizun/results/ (P02-T08, "
            "P02-T12). A Cortex-only fixture must stay in memory and therefore cannot be "
            "used to claim persistence; the A/B smoke in P02-T15 has to record save and "
            "reopen as an explicit Cortex limitation rather than pick a lookalike tool."
        ),
        "catalog_scan": {
            "tools_matching_save_or_close": ["save_selection", "sync_csv_parameters"],
            "project_save_calls_in_pinned_source": 0,
        },
    },
    {
        "semantic": "export_pdf",
        "tool": "batch_export",
        "format": "PDF",
        "dry_run_default": False,
        "note": (
            "batch_export exports views or sheets by element id into outputDirectory; "
            "format PDF prints the sheet set the caller names"
        ),
    },
    {
        "semantic": "export_ifc",
        "tools": ["ifc_export_basic", "ifc_export_with_configuration"],
        "format": "ifc",
        "dry_run_default": False,
        "note": (
            "ifc_export_basic takes outputDirectory plus an optional fileVersion and "
            "base-quantity flags; ifc_export_with_configuration selects a named "
            "configuration with key/value overrides"
        ),
    },
    {
        "semantic": "export_dwg",
        "tool": "batch_export",
        "format": "DWG",
        "dry_run_default": False,
        "note": "same tool as the PDF route; the format field selects DWG, DXF or DGN",
    },
    {
        "semantic": "export_image",
        "tool": "batch_export",
        "format": "IMAGE",
        "dry_run_default": False,
        "note": (
            "batch_export with format IMAGE writes PNG; there is no live-view capture "
            "tool comparable to the Horizun capture_view"
        ),
    },
    {
        "semantic": "export_excel",
        "tools": ["export_to_excel", "export_elements_data", "export_room_data"],
        "dry_run_default": False,
        "note": (
            "export_to_excel is read-classified and writes a workbook; export_room_data "
            "covers the room schedule the program brief needs"
        ),
    },
    {
        "semantic": "python",
        "availability": "NOT_AVAILABLE",
        "justification": (
            "There is no Python surface. A scan of all 288 names and descriptions for "
            "python, code or script returns exactly one tool, send_code_to_revit, which "
            "executes C# through a sandbox rather than Python. RevitCortex.Core also "
            "carries no IronPython or Python runtime reference. The nearest surface is "
            "therefore not equivalent, and CodeSandboxV2 additionally strips comments and "
            "string literals before matching a denylist of System.IO, System.Net, "
            "System.Diagnostics.Process, Microsoft.Win32, System.Reflection, "
            "System.Runtime.InteropServices, dynamic, Invoke( and GetTypes(."
        ),
        "verified_alternative": (
            "The Horizun provider owns arbitrary-code execution on this machine: "
            "horizun_execute_python is granted and was exercised for real in P02-T12 "
            "(tool-lab/horizun/results/t12-toposolid.json). For Cortex, an equivalent "
            "capability would be send_code_to_revit, which is disabled by decision "
            "(EnableCodeExecution is false in the settings file) and must stay disabled; "
            "it also cannot be reached through the settings file without the owner. The "
            "P02-T15 A/B smoke must therefore compare the typed Cortex tools against the "
            "typed Horizun tools and record that the Python route has no Cortex twin."
        ),
        "disabled_nearest_surface": "send_code_to_revit",
        "catalog_scan": {
            "tools_matching_python_code_script": ["send_code_to_revit"],
            "language": "C#",
            "sandbox_denylist": [
                "System.IO",
                "System.Net",
                "System.Diagnostics.Process",
                "Microsoft.Win32",
                "System.Reflection",
                "System.Runtime.InteropServices",
                "dynamic",
                "Invoke(",
                "GetTypes(",
            ],
        },
    },
]


def _load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _load_safety() -> dict:
    return json.loads(SAFETY_PATH.read_text(encoding="utf-8"))


def _catalog_tools(catalog: dict) -> list:
    return catalog["tools_list"]["result"]["tools"]


def _source_fields(tool_name: str) -> set:
    """Field names the pinned source reads for a tool, taken from its own file.

    The batch creation tools document a short summary inside specs and then
    read extra keys straight off the JSON object, so hostWallId and
    locationPoint belong to the contract the deployed code implements even
    though the published schema never lists them. A declared field is accepted
    when the schema advertises it or the pinned source reads it.
    """
    if not SOURCE_TOOLS_DIR.is_dir():
        return set()
    marker = 'public string Name => "' + tool_name + '"'
    for path in SOURCE_TOOLS_DIR.rglob("*.cs"):
        source = path.read_text(encoding="utf-8-sig", errors="replace")
        if marker not in source:
            continue
        return set(re.findall('item\\[\\s*"([A-Za-z_][A-Za-z0-9_]*)"\\s*\\]', source))
    return set()


def _declared_fields(schema: dict) -> list:
    """Field names the schema advertises, read from schema and prose alike.

    The Cortex batch tools wrap their real arguments inside one string
    property called specs, so field names also live in description text,
    for example "[{category, locationLine:{p0, p1, pMid?}, typeId?}]". A
    declared field is accepted when the schema names it as a property or
    mentions it in a description, because both are part of the contract a
    caller reads.
    """
    names = set(schema.get("properties") or {})
    for value in (schema.get("properties") or {}).values():
        if not isinstance(value, dict):
            continue
        description = value.get("description")
        if not description:
            continue
        for token in re.findall("[A-Za-z_][A-Za-z0-9_]*", description):
            names.add(token)
    return names


def _schema_summary(tool: dict) -> dict:
    """The input fields the published schema advertises, copied verbatim."""
    schema = tool.get("inputSchema") or {}
    properties = schema.get("properties") or {}
    enums = {}
    for key, value in properties.items():
        if isinstance(value, dict) and isinstance(value.get("enum"), list):
            enums[key] = list(value["enum"])
    return {
        "required": list(schema.get("required") or []),
        "properties": sorted(properties),
        "enums": enums,
    }


def build() -> dict:
    catalog = _load_catalog()
    safety = _load_safety()
    tools = _catalog_tools(catalog)
    catalog_by_name = {tool["name"]: tool for tool in tools}
    safety_tools = safety["tools"]

    if set(safety_tools) != set(catalog_by_name):
        raise SystemExit(
            "tool-safety.json and the catalog disagree about which tools exist; "
            "re-run extract_tool_safety.py"
        )

    capabilities = {}
    for declared in CAPABILITIES:
        semantic = declared["semantic"]
        entry = {
            "semantic": semantic,
            "availability": declared.get("availability", "AVAILABLE"),
        }

        referenced = []
        primary = declared.get("tool")
        if primary:
            referenced.append(primary)
        referenced.extend(declared.get("tools", []))
        referenced.extend(declared.get("alternatives", []))

        if entry["availability"] == "NOT_AVAILABLE":
            entry["justification"] = declared["justification"]
            entry["verified_alternative"] = declared["verified_alternative"]
            if declared.get("disabled_nearest_surface"):
                entry["disabled_nearest_surface"] = declared["disabled_nearest_surface"]
            if declared.get("catalog_scan"):
                entry["catalog_scan"] = declared["catalog_scan"]
            capabilities[semantic] = entry
            continue

        unknown = sorted(name for name in referenced if name not in catalog_by_name)
        if unknown:
            raise SystemExit(
                "capability "
                + semantic
                + " names tools the published catalog does not have: "
                + ", ".join(unknown)
            )

        if primary:
            entry["tool"] = primary
        elif len(declared.get("tools", [])) == 1:
            entry["tool"] = declared["tools"][0]
        else:
            entry["tools"] = list(declared.get("tools", []))

        if declared.get("alternatives"):
            entry["alternatives"] = list(declared["alternatives"])

        if declared.get("format"):
            entry["format"] = declared["format"]

        # Any declared field has to exist in the schema of the tool that reads it.
        declaring_tool = catalog_by_name.get(primary) or catalog_by_name[
            declared["tools"][0]
        ]
        properties = _declared_fields(declaring_tool.get("inputSchema") or {})
        source_fields = _source_fields(declaring_tool["name"])
        accepted = properties | source_fields
        for key in (
            "required_fields",
            "spec_required_fields",
            "view_types",
            "presets",
            "actions",
        ):
            declared_value = declared.get(key)
            if declared_value is None:
                continue
            if key in ("view_types", "presets", "actions"):
                entry[key] = declared_value
                continue
            missing = [field for field in declared_value if field not in accepted]
            if missing:
                raise SystemExit(
                    semantic
                    + " declares fields "
                    + ", ".join(missing)
                    + " that "
                    + declaring_tool["name"]
                    + " does not advertise"
                )
            entry[key] = list(declared_value)

        for key in ("units", "hosted", "schema_divergence"):
            if declared.get(key) is not None:
                entry[key] = declared[key]

        if declared.get("dry_run_default") is not None:
            entry["dry_run_default"] = declared["dry_run_default"]

        flags = {}
        for name in referenced:
            reading = safety_tools[name]
            flags[name] = {
                "read_only": reading["read_only"],
                "destructive": reading["destructive"],
                "declared": reading["declared"],
            }
        entry["effect_flags"] = flags

        entry["tool_schemas"] = {
            name: _schema_summary(catalog_by_name[name]) for name in sorted(set(referenced))
        }
        entry["note"] = declared["note"]
        capabilities[semantic] = entry

    digest = hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()
    initialize = catalog["initialize"]["result"]

    return {
        "schema_version": 1,
        "provider": "revitcortex",
        "generated_by": "tool-lab/revitcortex/generate_toolmap.py",
        "generated_utc": catalog["started_utc"],
        "rule": (
            "every tool name and every input field is copied from the catalog captured "
            "from the published server; every effect flag is copied from the [ToolSafety] "
            "parse of the pinned source, because the Cortex catalog publishes no "
            "annotations block. Regenerate instead of editing by hand"
        ),
        "provenance": {
            "catalog_path": "tool-lab/revitcortex/tool-catalog.json",
            "tool_safety_path": "tool-lab/revitcortex/tool-safety.json",
            "tool_safety_extractor": "tool-lab/revitcortex/extract_tool_safety.py",
            "tool_safety_declared_count": safety["declared_tool_count"],
            "catalog_sha256": digest,
            "catalog_tool_count": len(tools),
            "tools_listed_by_client": len(catalog_by_name),
            "protocol_version": initialize["protocolVersion"],
            "server_version": initialize["serverInfo"]["version"],
            "server_name": initialize["serverInfo"]["name"],
            "transport": "stdio JSON-RPC 2.0 to the published RevitCortex.Server.exe",
            "source_url": SOURCE_URL,
            "source_commit": SOURCE_COMMIT,
            "source_commit_verified_by": "tool-lab/revitcortex/extract_tool_safety.py",
            "note": (
                "the README of the pinned source advertises 173 tools while the published "
                "server lists 288 over MCP; the binary and its 288-tool listing are the "
                "authority, and the documentation count is recorded here only so the "
                "divergence is not mistaken for a capture error"
            ),
        },
        "capabilities": capabilities,
    }


def main(argv: list = None) -> int:
    parser = argparse.ArgumentParser(description="generate the Cortex toolmap")
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the committed toolmap differs from the generated one",
    )
    args = parser.parse_args(argv)

    payload = build()
    rendered = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100)
    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if current != rendered:
            print("toolmap is stale: regenerate with this script", file=sys.stderr)
            return 1
        print("toolmap is up to date")
        return 0
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print("wrote " + str(OUTPUT_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

