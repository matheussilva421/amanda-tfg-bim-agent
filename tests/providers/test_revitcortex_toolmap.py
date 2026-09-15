"""Contract tests for the RevitCortex provider toolmap.

Plan 02, Task 6 requires the toolmap to be generated from the actual catalog
instead of guessed tool names, and Task 14 repeats it for the Cortex bridge.
These tests are the enforcement for the second provider:

* every tool name has to exist in the catalog captured from the published
  server (tool-lab/revitcortex/tool-catalog.json);
* the Cortex MCP catalog publishes no 'annotations' block, so the effect flags
  are copied from tool-lab/revitcortex/tool-safety.json, which is parsed out of
  the pinned source checkout the deployed assembly was built from;
* anything the provider cannot do has to carry a justification and a verified
  alternative instead of a plausible-looking tool name.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOLMAP_PATH = ROOT / "state" / "providers" / "revitcortex-toolmap.yaml"
CATALOG_PATH = ROOT / "tool-lab" / "revitcortex" / "tool-catalog.json"
SAFETY_PATH = ROOT / "tool-lab" / "revitcortex" / "tool-safety.json"

SOURCE_COMMIT = "8b2556daefb2bf88f0a7a17bf28f2352fe0b0e33"
SOURCE_URL = "https://github.com/LuDattilo/RevitCortex.git"

#: The semantic capabilities Plan 02 Task 6 requires, plus the spreadsheet
#: export the Cortex provider actually publishes a tool for.
REQUIRED_CAPABILITIES = frozenset(
    {
        "health",
        "document_info",
        "document_query",
        "model_scan",
        "level",
        "wall",
        "floor",
        "room",
        "door",
        "window",
        "views",
        "section_elevation",
        "sheets",
        "schedules",
        "dimensions",
        "site_toposolid",
        "save",
        "export_pdf",
        "export_ifc",
        "export_dwg",
        "export_image",
        "export_excel",
        "python",
    }
)

#: Capabilities the catalog and the source agree the bridge does not publish.
KNOWN_ABSENCES = ("site_toposolid", "save", "python")

PLACEHOLDER_PATTERNS = (
    re.compile(r"<[A-Za-z_][^<>\n]*>"),
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bTBD\b"),
    re.compile(r"\bUNKNOWN\b"),
    re.compile(r"\bPLACEHOLDER\b"),
    re.compile(r"\?\?\?"),
)


def _load_yaml(path):
    if not path.exists():
        raise FileNotFoundError(str(path))
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _catalog_tools():
    return _catalog()["tools_list"]["result"]["tools"]


def _catalog_names():
    return {tool["name"] for tool in _catalog_tools()}


def _safety():
    return json.loads(SAFETY_PATH.read_text(encoding="utf-8"))


def _iter_scalars(node, path="$"):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _iter_scalars(value, path + "." + str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _iter_scalars(value, "%s[%d]" % (path, index))
    else:
        yield path, node


def _walk_strings(node):
    for path, value in _iter_scalars(node):
        if isinstance(value, str):
            yield path, value


def _mapped_tools(capability):
    """Every tool name a capability declares, primary and alternatives.

    Keys holding a non-tool meaning are deliberately not read here, so a
    capability that is NOT_AVAILABLE cannot smuggle in a tool name through a
    free-form field.
    """
    names = []
    primary = capability.get("tool")
    if isinstance(primary, str):
        names.append(primary)
    sequence = capability.get("tools")
    if isinstance(sequence, list):
        for entry in sequence:
            if isinstance(entry, str):
                names.append(entry)
            elif isinstance(entry, dict) and isinstance(entry.get("tool"), str):
                names.append(entry["tool"])
    for entry in capability.get("operations") or []:
        if isinstance(entry, dict) and isinstance(entry.get("tool"), str):
            names.append(entry["tool"])
    for key in ("alternatives", "fallbacks", "supports"):
        sequence = capability.get(key)
        if isinstance(sequence, list):
            for entry in sequence:
                if isinstance(entry, str):
                    names.append(entry)
                elif isinstance(entry, dict) and isinstance(entry.get("tool"), str):
                    names.append(entry["tool"])
    return names


def test_the_toolmap_file_exists_and_is_valid_yaml():
    payload = _load_yaml(TOOLMAP_PATH)

    assert payload["schema_version"] == 1
    assert payload["provider"] == "revitcortex"


def test_the_toolmap_pins_the_verified_provenance():
    toolmap = _load_yaml(TOOLMAP_PATH)
    catalog = _catalog()
    provenance = toolmap["provenance"]

    on_disk = hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()
    assert provenance["catalog_sha256"] == on_disk
    assert provenance["catalog_tool_count"] == len(_catalog_tools())
    assert provenance["protocol_version"] == catalog["initialize"]["result"]["protocolVersion"]
    assert provenance["server_version"] == catalog["initialize"]["result"]["serverInfo"]["version"]
    assert provenance["source_commit"] == SOURCE_COMMIT
    assert provenance["source_url"] == SOURCE_URL
    assert provenance["catalog_path"] == "tool-lab/revitcortex/tool-catalog.json"
    assert provenance["tool_safety_path"] == "tool-lab/revitcortex/tool-safety.json"


def test_the_effect_flags_come_from_the_pinned_source_not_the_catalog():
    """The Cortex catalog ships no annotations, so safety is source-derived."""
    toolmap = _load_yaml(TOOLMAP_PATH)
    safety = _safety()

    assert "annotations" not in _catalog_tools()[0], (
        "if the published catalog ever starts carrying annotations, the toolmap "
        "should read them from there and this test must change"
    )
    assert safety["source_commit"] == SOURCE_COMMIT
    assert safety["declared_tool_count"] == len(_catalog_names())
    assert safety["tools"], "tool-safety.json must describe every catalog tool"
    assert set(safety["tools"]) == _catalog_names()

    declared = toolmap["provenance"]["tool_safety_declared_count"]
    assert declared == safety["declared_tool_count"]


def test_every_capability_maps_only_to_tools_the_server_publishes():
    toolmap = _load_yaml(TOOLMAP_PATH)
    known = _catalog_names()

    referenced = set()
    for capability in toolmap["capabilities"].values():
        referenced.update(_mapped_tools(capability))

    assert referenced, "the toolmap must reference at least one discovered tool"
    unknown = sorted(name for name in referenced if name not in known)
    assert unknown == [], (
        "these tool names are not in the published Cortex catalog: " + ", ".join(unknown)
    )
    assert referenced < known, (
        "the mapped tools are expected to be a strict subset of the 288 published "
        "tools; a full-coverage claim would mean the names were not selected"
    )


def test_the_plan_capabilities_are_all_resolved():
    toolmap = _load_yaml(TOOLMAP_PATH)

    assert REQUIRED_CAPABILITIES <= set(toolmap["capabilities"])


def test_capabilities_declare_a_supported_or_an_explained_absence():
    toolmap = _load_yaml(TOOLMAP_PATH)

    for name, capability in toolmap["capabilities"].items():
        assert capability["availability"] in {
            "AVAILABLE",
            "PARTIAL",
            "NOT_AVAILABLE",
        }, name
        if capability["availability"] == "NOT_AVAILABLE":
            justification = capability.get("justification", "")
            assert justification.strip(), name + " needs a justification"
            alternative = capability.get("verified_alternative", "")
            assert alternative.strip(), name + " needs a verified alternative"
            assert not _mapped_tools(capability), (
                name + " is NOT_AVAILABLE but still names tools"
            )
        else:
            assert _mapped_tools(capability), name + " needs a tool"


def test_recorded_effect_flags_match_the_source_declaration():
    """No flag is typed by hand: each one is read back off the source parse."""
    toolmap = _load_yaml(TOOLMAP_PATH)
    safety = _safety()["tools"]

    checked = 0
    for name, capability in toolmap["capabilities"].items():
        flags = capability.get("effect_flags") or {}
        for tool_name in _mapped_tools(capability):
            if tool_name not in safety:
                continue
            recorded = flags.get(tool_name)
            assert recorded is not None, (
                name + " maps " + tool_name + " without recording its flags"
            )
            published = safety[tool_name]
            assert recorded["read_only"] == published["read_only"], tool_name
            assert recorded["destructive"] == published["destructive"], tool_name
            assert recorded["declared"] is True, (
                tool_name + " would fall back to a prefix guess instead of a declaration"
            )
            checked += 1

    assert checked > 0


def test_the_absent_capabilities_are_the_ones_the_sources_agree_are_missing():
    """A missing capability is a finding, not an oversight to be papered over."""
    toolmap = _load_yaml(TOOLMAP_PATH)
    capabilities = toolmap["capabilities"]

    for name in KNOWN_ABSENCES:
        capability = capabilities[name]
        assert capability["availability"] == "NOT_AVAILABLE", (
            name + " must stay NOT_AVAILABLE while no tool covers it"
        )
        justification = capability["justification"]
        assert len(justification) > 80, name + " needs a substantive justification"
        assert capability["verified_alternative"].strip(), name

    published = _catalog_names()
    for absent in ("save_document", "open_document", "execute_python"):
        assert absent not in published


def test_the_typed_creation_capabilities_record_their_units_and_dry_run_behaviour():
    """Cortex mixes preview-first and immediate semantics and works in mm."""
    toolmap = _load_yaml(TOOLMAP_PATH)
    capabilities = toolmap["capabilities"]

    for name in ("level", "wall", "floor", "room"):
        capability = capabilities[name]
        assert capability["units"] == "mm", name
        assert capability["dry_run_default"] in {True, False, "mixed"}, name

    level = capabilities["level"]
    assert level["dry_run_default"] is True
    assert "dryRun" in level["note"]


def test_the_door_and_window_capability_records_the_hosted_path():
    toolmap = _load_yaml(TOOLMAP_PATH)
    capabilities = toolmap["capabilities"]

    for name in ("door", "window"):
        capability = capabilities[name]
        assert capability["tool"] == "create_point_based_element"
        assert capability["hosted"] is True
        fields = capability["required_fields"]
        assert "hostWallId" in fields, (
            name + " must record the host field the tool actually reads"
        )
        assert "locationPoint" in fields, (
            name + " must record locationPoint, which is the field the code reads"
        )


def test_the_document_query_and_scan_capabilities_stay_read_only():
    toolmap = _load_yaml(TOOLMAP_PATH)
    capabilities = toolmap["capabilities"]

    for name in ("health", "document_info", "document_query", "model_scan"):
        for tool_name in _mapped_tools(capabilities[name]):
            flags = capabilities[name]["effect_flags"][tool_name]
            assert flags["read_only"] is True, name + " must stay read-only"


def test_no_placeholder_marker_survives_in_any_scalar():
    toolmap = _load_yaml(TOOLMAP_PATH)

    offenders = []
    for path, value in _walk_strings(toolmap):
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(value):
                offenders.append(path + " -> " + value[:80])
                break

    assert offenders == [], "placeholder markers found: " + "; ".join(offenders)

