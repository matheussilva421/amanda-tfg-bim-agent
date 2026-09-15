"""Contract tests for the committed provider toolmaps.

Plan 02, Task 6 asks for ``state/providers/horizun-toolmap.yaml`` generated
*from the actual catalog*, never from guessed tool names. These tests are the
enforcement: every tool name in the toolmap has to exist in the verified
artifacts under ``tool-lab/horizun/``, the recorded effect flags have to match
the published contract, and no placeholder marker may survive into a commit.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOLMAP_PATH = ROOT / "state" / "providers" / "horizun-toolmap.yaml"
CATALOG_PATH = ROOT / "tool-lab" / "horizun" / "tool-catalog.json"
RESOURCE_DUMP_PATH = ROOT / "tool-lab" / "horizun" / "resource-dump.json"
CONTRACT_URI = "horizun://contract/tools"

#: The semantic capabilities Plan 02 Task 6 requires the toolmap to resolve.
REQUIRED_CAPABILITIES = frozenset(
    {
        "health",
        "document_info",
        "document_query",
        "model_scan",
        "file_info",
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
        "python",
    }
)

#: Markers that mean "somebody typed a shape instead of a discovered name".
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


def _catalog_names():
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {tool["name"] for tool in payload["tools"]}


def _contract():
    dump = json.loads(RESOURCE_DUMP_PATH.read_text(encoding="utf-8"))
    text = dump[CONTRACT_URI]["contents"][0]["text"]
    return json.loads(text)


def _contract_names():
    return {tool["name"] for tool in _contract()["tools"]}


def _contract_by_name():
    return {tool["name"]: tool for tool in _contract()["tools"]}


def _iter_scalars(node, path="$"):
    """Yield ``(path, value)`` for every scalar anywhere in the structure."""
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

    ``operations`` holds operation values *inside* the named tool, so only
    dictionary entries carrying an explicit ``tool`` key count as tool names.
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
    assert payload["provider"] == "horizun-revit-mcp"


def test_the_toolmap_pins_the_verified_provenance():
    toolmap = _load_yaml(TOOLMAP_PATH)
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    contract = _contract()

    provenance = toolmap["provenance"]
    assert provenance["contract_hash"] == contract["contract_hash"]
    assert provenance["protocol_version"] == 2
    assert provenance["catalog_sha256"] == catalog["catalog_sha256"]
    assert provenance["catalog_tool_count"] == catalog["tool_count"]
    assert provenance["contract_tool_count"] == len(contract["tools"])
    assert provenance["server_version"] == catalog["origin"]["server_info"]["version"]
    assert re.fullmatch(r"[0-9a-f]{40}", provenance["source_commit"])
    assert provenance["catalog_path"] == "tool-lab/horizun/tool-catalog.json"
    assert provenance["contract_resource_uri"] == CONTRACT_URI


def test_every_capability_maps_only_to_tools_discovered_in_the_artifacts():
    toolmap = _load_yaml(TOOLMAP_PATH)
    known = _catalog_names() | _contract_names()

    referenced = set()
    for capability in toolmap["capabilities"].values():
        referenced.update(_mapped_tools(capability))

    assert referenced, "the toolmap must reference at least one discovered tool"
    unknown = sorted(name for name in referenced if name not in known)
    assert unknown == [], (
        "these tool names are not in the verified catalog or contract: "
        + ", ".join(unknown)
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


def test_recorded_effect_flags_come_from_the_published_contract():
    """No flag is typed by hand: each one is read back off the contract."""
    toolmap = _load_yaml(TOOLMAP_PATH)
    contract = _contract_by_name()

    checked = 0
    for name, capability in toolmap["capabilities"].items():
        flags = capability.get("effect_flags") or {}
        for tool_name in _mapped_tools(capability):
            if tool_name not in contract:
                continue
            recorded = flags.get(tool_name)
            assert recorded is not None, (
                name + " maps " + tool_name + " without recording its flags"
            )
            published = contract[tool_name]
            assert recorded["effect"] == published["effect"]
            assert recorded["destructive"] == published["destructive"]
            assert recorded["open_world"] == published["open_world"]
            checked += 1

    assert checked > 0


def test_no_placeholder_marker_survives_in_any_scalar():
    toolmap = _load_yaml(TOOLMAP_PATH)

    offenders = []
    for path, value in _walk_strings(toolmap):
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(value):
                offenders.append(path + " -> " + value[:80])
                break

    assert offenders == [], "placeholder markers found: " + "; ".join(offenders)


def test_the_toolmap_uses_the_contract_only_document_tools():
    toolmap = _load_yaml(TOOLMAP_PATH)
    capabilities = toolmap["capabilities"]
    contract = _contract_names()

    for name in ("save", "export_pdf", "export_ifc", "export_dwg", "export_image"):
        tools = set(_mapped_tools(capabilities[name]))
        assert tools, name + " must name at least one tool"
        assert tools <= contract, name + " must use contract tools"
        assert tools & {
            "horizun_save_document",
            "horizun_export",
            "horizun_document_session",
        }


def test_export_capabilities_carry_the_export_format_from_the_contract():
    toolmap = _load_yaml(TOOLMAP_PATH)
    contract = _contract_by_name()
    export_schema = contract["horizun_export"]["input_schema"]
    allowed = set(export_schema["properties"]["format"]["enum"])

    for name, expected in (
        ("export_pdf", "pdf"),
        ("export_ifc", "ifc"),
        ("export_dwg", "dwg"),
        ("export_image", "image"),
    ):
        capability = toolmap["capabilities"][name]
        assert expected in allowed
        assert capability["format"] == expected


def test_the_proven_toolmap_entries_record_their_host_evidence():
    """P02-T12: the recorded proof is real and points at a real artifact."""
    toolmap = _load_yaml(TOOLMAP_PATH)
    capabilities = toolmap["capabilities"]

    site = capabilities["site_toposolid"]
    assert site["availability"] == "NOT_AVAILABLE"
    assert "horizun_execute_python" in site["proven_alternative"]
    assert "t12-toposolid.json" in site["proven_alternative"]

    python = capabilities["python"]
    assert python["availability"] == "PARTIAL"
    assert "t12-toposolid.json" in python["proven"]
    assert python["proven_utc"] == "2026-09-15"

    artifact = ROOT / "tool-lab" / "horizun" / "results" / "t12-toposolid.json"
    evidence = json.loads(artifact.read_text(encoding="utf-8"))
    assert evidence["task"] == "P02-T12"
    assert evidence["mapped_capability"]["semantic"] == "site_toposolid"
    assert evidence["mapped_capability"]["typed_creation_kind"] is None

    applied = evidence["apply"]["output"]
    assert applied["status"] == "verified"
    assert applied["created_ids"]
    assert all(check["ok"] for check in applied["verified_checks"])

    persistence = evidence["persistence"]
    assert persistence["save"]["saved"] is True
    assert persistence["close"]["closed"] is True
    assert persistence["reopen"]["opened_now"] is True
    assert persistence["bytes_before_save"] != persistence["bytes_after_reopen"]
    reopened = [row["element_id"] for row in persistence["query_after_reopen"]["rows"]]
    assert reopened == applied["created_ids"]

def test_the_toposolid_task_meets_the_plan_geometry_and_independent_read():
    """P02-T12's plan asks for the four synthetic points, an independent
    extents read, and a save/reopen cycle.  Each of those is asserted here
    against the recorded host transcript, not against prose."""
    artifact = ROOT / "tool-lab" / "horizun" / "results" / "t12-toposolid.json"
    evidence = json.loads(artifact.read_text(encoding="utf-8"))

    # The plan fixes the synthetic plane in metres.
    assert evidence["fixture"]["synthetic_points_m"] == [
        [0, 0, 0.0],
        [20, 0, 0.5],
        [20, 20, 1.0],
        [0, 20, 0.5],
    ]

    # The rehearsal had to prove the technique and leave nothing behind.
    rehearsal = evidence["rehearsal"]["output"]
    assert rehearsal["rollback_ok"] is True
    assert rehearsal["count_inside_tx"] == 1
    assert rehearsal["after_rollback_count"] == 0
    assert rehearsal["after_rollback_ids"] == []
    assert rehearsal["rollback_absent"] is True

    applied = evidence["apply"]["output"]
    assert applied["requested_points_m"] == rehearsal["requested_points_m"]
    assert applied["before_count"] == 0
    assert applied["after_count"] == len(applied["created_ids"])
    assert applied["doc_is_modifiable_after"] is False

    # Extents through the typed model query, the strongest independent read
    # available here.  Y came back as -2.2e-15, so compare with a tolerance.
    read = evidence["independent_reads"]
    by_id = read["by_id"]["reply"]
    assert by_id["matched_total"] == 1
    assert by_id["coverage_complete"] is True
    row = by_id["rows"][0]
    assert row["element_id"] == applied["created_ids"][0]
    assert row["unique_id"]
    extents = row["bounding_box"]
    low = [round(value) for value in extents["min"][:2]]
    high = [round(value) for value in extents["max"][:2]]
    assert low == [0, 0]
    assert high == [20, 20]
    assert extents["max"][2] <= 1.0 and extents["min"][2] >= -1.0

    # A second and third query, neither of them by element id.
    assert read["by_category"]["reply"]["matched_total"] == 1
    assert read["list_elements"]["reply"]["total"] == 1
    # The request names the English category while the reply echoes the
    # localized one, so both sides are recorded instead of assumed equal.
    assert read["list_elements"]["arguments"]["category"] == "OST_Toposolid"
    assert read["list_elements"]["reply"]["category"] == "Sólido topográfico"

    # Save/reopen moved the file and the element survived it unchanged.
    persistence = evidence["persistence"]
    assert persistence["sha256_before_save"] == evidence["fixture"]["sha256_at_copy"]
    assert persistence["sha256_after_reopen"] != persistence["sha256_before_save"]
    assert persistence["save"]["mtime_changed"] is True
    after = persistence["query_after_reopen"]["rows"][0]
    assert after["unique_id"] == row["unique_id"]
