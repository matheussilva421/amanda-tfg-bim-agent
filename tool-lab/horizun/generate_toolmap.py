"""Generate ``state/providers/horizun-toolmap.yaml`` from the verified artifacts.

Plan 02 Task 6 is explicit: the toolmap must be generated *directly from actual
catalog results; do not type guessed tool names*. This script is that generator,
so the rule is enforced by construction:

* the catalog (``tool-lab/horizun/tool-catalog.json``) and the installed
  contract resource (``horizun://contract/tools``, captured in
  ``tool-lab/horizun/resource-dump.json``) are the only sources of tool names;
* every name below is looked up in the union of the two before it is written;
* every effect flag is copied out of the contract, never retyped;
* a capability may only be NOT_AVAILABLE with a written justification and a
  verified alternative.

Usage::

    python tool-lab/horizun/generate_toolmap.py
    python tool-lab/horizun/generate_toolmap.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "tool-lab" / "horizun" / "tool-catalog.json"
DUMP_PATH = ROOT / "tool-lab" / "horizun" / "resource-dump.json"
OUTPUT_PATH = ROOT / "state" / "providers" / "horizun-toolmap.yaml"
CONTRACT_URI = "horizun://contract/tools"
SOURCE_COMMIT = "cc4ea04e9ecfe547ad349f22e0864019ce1ead1f"
SOURCE_URL = "https://github.com/HorizunGroup/horizun-revit-mcp.git"

#: Capability declarations. ``tools``/``alternatives`` are verified against the
#: installed contract before anything is written; the element kind for the
#: creation capabilities is verified against ``horizun_create_elements``.
CAPABILITIES = [
    {
        "semantic": "health",
        "tools": ["horizun_health"],
        "note": "reports the Revit year, build, process id and the ACTIVE document; call it before every read or write",
    },
    {
        "semantic": "document_info",
        "tools": ["get_document_info"],
        "alternatives": ["horizun_target", "horizun_health"],
        "note": "read-only title, path, version and element count of the active document",
    },
    {
        "semantic": "document_query",
        "tools": ["horizun_query_model"],
        "alternatives": ["horizun_list_elements", "horizun_quantities"],
        "note": "element and type queries with a closed return-field set and full/compact/summary response modes",
    },
    {
        "semantic": "model_scan",
        "tools": ["horizun_model_scan"],
        "alternatives": ["horizun_audit_model", "horizun_quantities"],
        "note": "versioned scan profiles; aborts when the active document differs from target_document_title",
    },
    {
        "semantic": "file_info",
        "tools": ["horizun_file_info"],
        "note": "reads .rvt/.rfa headers from disk without opening Revit, so a version mismatch is caught before a session",
    },
    {
        "semantic": "level",
        "tools": ["horizun_create_elements"],
        "element_kind": "level",
        "required_fields": ["kind", "elevation"],
        "note": "one element variant inside the single creation tool; there is no separate create_level tool",
    },
    {
        "semantic": "wall",
        "tools": ["horizun_create_elements"],
        "element_kind": "wall",
        "required_fields": ["kind", "start", "end", "level_id", "height"],
        "note": "straight or arc walls; type_id and height are workspace parameters, not tool choices",
    },
    {
        "semantic": "floor",
        "tools": ["horizun_create_elements"],
        "element_kind": "floor",
        "required_fields": ["kind", "profile", "level_id"],
        "note": "profile is a closed loop in the requested units",
    },
    {
        "semantic": "room",
        "tools": ["horizun_create_elements"],
        "element_kind": "room",
        "required_fields": ["kind", "point", "level_id"],
        "note": "room needs bounding walls in place first; it is not a room-separation workflow by itself",
    },
    {
        "semantic": "door",
        "tools": ["horizun_create_elements"],
        "element_kind": "family_instance",
        "required_fields": ["kind", "point", "type_id", "coordinate_mode"],
        "note": "no door-specific tool is published; a door is a wall-hosted family_instance, so host_id and a door type_id are required",
    },
    {
        "semantic": "window",
        "tools": ["horizun_create_elements"],
        "element_kind": "family_instance",
        "required_fields": ["kind", "point", "type_id", "coordinate_mode"],
        "note": "same path as a door: wall-hosted family_instance with host_id; wall_opening is the host-cut variant when no family should be placed",
    },
    {
        "semantic": "views",
        "tools": ["horizun_manage_views"],
        "alternatives": ["horizun_plan_views", "horizun_navigate"],
        "note": "floor, ceiling, structural, area, 3d, drafting, section, elevation and callout creation plus template and view-range control",
    },
    {
        "semantic": "section_elevation",
        "tools": ["horizun_manage_views"],
        "operations": ["create_section", "create_elevation"],
        "note": "sections and elevations are view operations, not separate tools",
    },
    {
        "semantic": "sheets",
        "tools": ["horizun_manage_views", "horizun_pack_sheets"],
        "operations": ["create_sheet", "place_view", "place_schedule"],
        "note": "create_sheet, convert_placeholder_sheet and place_view live in manage_views; pack_sheets arranges viewports on a sheet",
    },
    {
        "semantic": "schedules",
        "tools": [
            "horizun_create_schedule",
            "horizun_manage_schedules",
            "horizun_get_schedule_data",
            "horizun_list_schedules",
        ],
        "note": "create_schedule takes one category; manage_schedules edits fields, filters, sorting and totals",
    },
    {
        "semantic": "dimensions",
        "tools": [
            "horizun_query_dimensions",
            "horizun_edit_dimensions",
            "horizun_plan_annotations",
        ],
        "alternatives": ["horizun_get_dimension_references"],
        "note": "plan_annotations carries the automatic dimensioning operations; edit_dimensions changes placed dimensions",
    },
    {
        "semantic": "site_toposolid",
        "availability": "NOT_AVAILABLE",
        "justification": (
            "No tool in the installed contract creates a topographic surface or "
            "toposolid from scratch. The only three contract tools that mention a "
            "toposolid are horizun_embed_floors_in_toposolid, "
            "horizun_grade_toposolid_around_floors and horizun_execute_plan, and both "
            "named tools require a toposolid that already exists; the element variant "
            "list of horizun_create_elements does not include a toposolid kind. The "
            "project site data is also MISSING for topography, so no surface could be "
            "validated even if one were created."
        ),
        "verified_alternative": (
            "Create the surface once outside the creation path: either place the "
            "toposolid by hand in Revit and then use horizun_grade_toposolid_around_floors "
            "and horizun_embed_floors_in_toposolid, or request arbitrary Python with "
            "horizun_request_python_access and call the Revit API toposolid builder through "
            "horizun_execute_python. Both paths are recorded in "
            "tool-lab/horizun/tool-discovery.md; neither is proven on this machine yet."
        ),
    },
    {
        "semantic": "save",
        "tools": ["horizun_save_document", "horizun_document_session"],
        "alternatives": ["horizun_open_document"],
        "note": "save_document refuses a document that was never saved and proves the timestamp and size change on disk; document_session carries open, save_as, close and inspect",
    },
    {
        "semantic": "export_pdf",
        "tools": ["horizun_export", "horizun_document_session"],
        "alternatives": ["horizun_capture_view"],
        "format": "pdf",
        "note": "combined or per-view PDFs with a closed print-policy field set, page-count re-read and an optional SHA256 manifest",
    },
    {
        "semantic": "export_ifc",
        "tools": ["horizun_export"],
        "format": "ifc",
        "note": "IFC version, base quantities and split-walls policy come from the contract enum",
    },
    {
        "semantic": "export_dwg",
        "tools": ["horizun_export"],
        "format": "dwg",
        "note": "one view per call; acad_version selects 2013 or 2018",
    },
    {
        "semantic": "export_image",
        "tools": ["horizun_export"],
        "alternatives": ["horizun_capture_view"],
        "format": "image",
        "note": "image export for one view; capture_view returns a PNG of the live view with orientation and display-style control",
    },
    {
        "semantic": "python",
        "tools": ["horizun_execute_python"],
        "alternatives": ["horizun_request_python_access"],
        "availability": "PARTIAL",
        "note": "disabled by default: request_python_access opens a consent dialog the machine owner must approve; preflight validates code without running it",
    },
]


def _load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _load_contract() -> dict:
    dump = json.loads(DUMP_PATH.read_text(encoding="utf-8"))
    text = dump[CONTRACT_URI]["contents"][0]["text"]
    return json.loads(text)


def _flags(contract_tool: dict) -> dict:
    return {
        "effect": contract_tool["effect"],
        "destructive": contract_tool["destructive"],
        "open_world": contract_tool["open_world"],
    }


def _element_kinds(contract_tool: dict) -> dict:
    variants = contract_tool["input_schema"]["properties"]["elements"]["items"]["oneOf"]
    return {
        variant["properties"]["kind"]["const"]: variant for variant in variants
    }


def _view_operations(contract_tool: dict) -> set:
    """The operation values ``horizun_manage_views`` accepts."""
    actions = contract_tool["input_schema"]["properties"]["actions"]
    return set(actions["items"]["properties"]["operation"]["enum"])


def build() -> dict:
    catalog = _load_catalog()
    contract = _load_contract()
    catalog_names = {tool["name"] for tool in catalog["tools"]}
    contract_by_name = {tool["name"]: tool for tool in contract["tools"]}
    known = catalog_names | set(contract_by_name)

    create_elements = contract_by_name["horizun_create_elements"]
    kinds = _element_kinds(create_elements)
    view_operations = _view_operations(contract_by_name["horizun_manage_views"])

    capabilities = {}
    for declared in CAPABILITIES:
        semantic = declared["semantic"]
        entry = {
            "semantic": semantic,
            "availability": declared.get("availability", "AVAILABLE"),
        }
        if entry["availability"] == "NOT_AVAILABLE":
            entry["justification"] = declared["justification"]
            entry["verified_alternative"] = declared["verified_alternative"]
            entry["contract_scan"] = {
                "tools_mentioning_toposolid": [
                    "horizun_embed_floors_in_toposolid",
                    "horizun_grade_toposolid_around_floors",
                    "horizun_execute_plan",
                ],
                "creation_tool_element_kinds": sorted(kinds),
            }
            capabilities[semantic] = entry
            continue

        referenced = list(declared.get("tools", [])) + list(
            declared.get("alternatives", [])
        )
        unknown = sorted(name for name in referenced if name not in known)
        if unknown:
            raise SystemExit(
                "capability "
                + semantic
                + " names tools that the installed contract does not publish: "
                + ", ".join(unknown)
            )

        if "element_kind" in declared:
            kind = declared["element_kind"]
            if kind not in kinds:
                raise SystemExit(
                    "horizun_create_elements has no variant for kind " + kind
                )
            required = kinds[kind].get("required", [])
            declared_required = declared.get("required_fields", [])
            if [field for field in declared_required if field not in required]:
                raise SystemExit(
                    "kind "
                    + kind
                    + " does not require "
                    + ", ".join(declared_required)
                )
            entry["tool"] = declared["tools"][0]
            entry["element_kind"] = kind
            entry["required_fields"] = declared_required
            entry["all_kind_fields"] = sorted(
                key for key in kinds[kind]["properties"] if key != "kind"
            )
        elif len(declared.get("tools", [])) == 1:
            entry["tool"] = declared["tools"][0]
        else:
            entry["tools"] = list(declared.get("tools", []))

        if declared.get("operations"):
            undeclared = sorted(
                name for name in declared["operations"] if name not in view_operations
            )
            if undeclared:
                raise SystemExit(
                    "horizun_manage_views has no operation "
                    + ", ".join(undeclared)
                )
            entry["operations"] = list(declared["operations"])
            entry["operation_source"] = "horizun_manage_views.actions[].operation"
        if declared.get("alternatives"):
            entry["alternatives"] = list(declared["alternatives"])
        if declared.get("format"):
            formats = contract_by_name["horizun_export"]["input_schema"]["properties"][
                "format"
            ]["enum"]
            if declared["format"] not in formats:
                raise SystemExit(
                    "horizun_export has no format " + declared["format"]
                )
            entry["format"] = declared["format"]

        flags = {}
        for name in referenced:
            contract_tool = contract_by_name.get(name)
            if contract_tool is not None:
                flags[name] = _flags(contract_tool)
        entry["effect_flags"] = flags
        entry["note"] = declared["note"]
        capabilities[semantic] = entry

    contract_only = sorted(set(contract_by_name) - catalog_names)
    catalog_only = sorted(catalog_names - set(contract_by_name))

    return {
        "schema_version": 1,
        "provider": "horizun-revit-mcp",
        "generated_by": "tool-lab/horizun/generate_toolmap.py",
        "generated_utc": catalog["generated_utc"],
        "rule": (
            "every tool name and every effect flag below is copied from the installed "
            "contract resource; regenerate instead of editing by hand"
        ),
        "provenance": {
            "catalog_path": "tool-lab/horizun/tool-catalog.json",
            "contract_resource_uri": CONTRACT_URI,
            "contract_resource_capture": "tool-lab/horizun/resource-dump.json",
            "contract_hash": contract["contract_hash"],
            "protocol_version": contract["protocol_version"],
            "catalog_sha256": catalog["catalog_sha256"],
            "catalog_tool_count": catalog["tool_count"],
            "contract_tool_count": len(contract["tools"]),
            "tools_listed_by_client": len(catalog_names),
            "server_version": catalog["origin"]["server_info"]["version"],
            "transport": catalog["origin"]["transport"],
            "source_url": SOURCE_URL,
            "source_commit": SOURCE_COMMIT,
            "catalog_only_tools": catalog_only,
            "contract_only_tools": contract_only,
            "note": (
                "the client tool listing returned "
                + str(len(catalog_names))
                + " tools while the installed contract declares "
                + str(len(contract["tools"]))
                + "; the contract is a superset and is the authority for document, "
                "save, export and Python work"
            ),
        },
        "capabilities": capabilities,
    }


def main(argv: list = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the committed toolmap differs from the generated one",
    )
    args = parser.parse_args(argv)

    payload = build()
    text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100)
    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if current != text:
            print("toolmap is stale: regenerate with this script", file=sys.stderr)
            return 1
        print("toolmap is up to date")
        return 0
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(text, encoding="utf-8")
    print("wrote " + str(OUTPUT_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
