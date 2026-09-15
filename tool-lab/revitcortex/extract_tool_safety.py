"""Extract per-tool safety declarations from the pinned RevitCortex source.

The Cortex MCP catalog publishes no annotations block, so a toolmap cannot copy
effect flags out of the catalog the way the Horizun toolmap copies them out of
horizun://contract/tools.  The authority for a Cortex tool safety lives in the
source that produced the deployed assembly:

* RevitCortex.Core.Tools.ToolSafetyAttribute declares
  [ToolSafety(readOnly, destructive)] on the tool class;
* CortexRouter.ResolveToolSafety resolves IToolSafetyAware first, then the
  attribute, then falls back to IsReadOnlyTool(name) prefix rules with
  destructive false.

This script parses the pinned checkout under vendor/RevitCortex and writes
tool-lab/revitcortex/tool-safety.json.  It never guesses: a tool whose
declaration cannot be read is reported as unresolved, not filled in.

Usage::

    python tool-lab/revitcortex/extract_tool_safety.py
    python tool-lab/revitcortex/extract_tool_safety.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "vendor" / "RevitCortex"
SOURCE_COMMIT = "8b2556daefb2bf88f0a7a17bf28f2352fe0b0e33"
SOURCE_URL = "https://github.com/LuDattilo/RevitCortex.git"
CATALOG_PATH = ROOT / "tool-lab" / "revitcortex" / "tool-catalog.json"
OUTPUT_PATH = ROOT / "tool-lab" / "revitcortex" / "tool-safety.json"

ATTRIBUTE_RE = re.compile(r"\[ToolSafety\((?P<args>[^)]*)\)\]")
NAME_RE = re.compile(r'public\s+string\s+Name\s*=>\s*"(?P<name>[^"]+)"\s*;')
SAFETY_CLASS_RE = re.compile(r"class\s+ToolSafetyAttribute")
AWARE_RE = re.compile(r":\s*[^\n{]*IToolSafetyAware")

#: Verbatim from CortexRouter.IsReadOnlyTool; recorded so the fallback is
#: auditable instead of retyped from memory.
PREFIX_READ_ONLY = (
    "get_",
    "list_",
    "find_",
    "analyze_",
    "check_",
    "measure_",
    "audit_",
    "export_",
)


def _git(*args):
    result = subprocess.run(
        ["git", *args], cwd=str(SOURCE_ROOT), capture_output=True, text=True
    )
    if result.returncode != 0:
        raise SystemExit("git %s failed: %s" % (" ".join(args), result.stderr.strip()))
    return result.stdout.strip()


def _catalog_names():
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {tool["name"] for tool in payload["tools_list"]["result"]["tools"]}


def _line_of(source, offset):
    return source.count("\n", 0, offset) + 1


def _parse_file(path):
    """Return (tool_name, read_only, destructive, line) rows for one source file."""
    source = path.read_text(encoding="utf-8-sig", errors="replace")
    if SAFETY_CLASS_RE.search(source):
        return []
    if AWARE_RE.search(source):
        return []

    declarations = []
    for match in ATTRIBUTE_RE.finditer(source):
        args = [part.strip() for part in match.group("args").split(",")]
        read_only = bool(args) and args[0].lower() == "true"
        destructive = len(args) > 1 and args[1].lower() == "true"
        declarations.append((match.start(), read_only, destructive, _line_of(source, match.start())))

    rows = []
    for match in NAME_RE.finditer(source):
        name = match.group("name")
        line = _line_of(source, match.start())
        preceding = [item for item in declarations if item[0] < match.start()]
        if not preceding:
            rows.append((name, None, None, line))
            continue
        chosen = max(preceding, key=lambda item: item[0])
        rows.append((name, chosen[1], chosen[2], chosen[3]))
    return rows


def extract():
    source_files = sorted(SOURCE_ROOT.glob("src/**/*.cs"))
    if not source_files:
        raise SystemExit("no C# sources found under %s" % SOURCE_ROOT)

    declared = {}
    conflicts = []
    ambiguous = []
    for path in source_files:
        relative = path.relative_to(ROOT).as_posix()
        rows = _parse_file(path)
        names_in_file = [row[0] for row in rows]
        for name, read_only, destructive, line in rows:
            row = {
                "read_only": read_only,
                "destructive": destructive,
                "source_file": relative,
                "source_line": line,
            }
            if name in declared:
                previous = declared[name]
                if (previous["read_only"], previous["destructive"]) != (read_only, destructive):
                    conflicts.append(name)
                continue
            if names_in_file.count(name) > 1:
                ambiguous.append(name)
                continue
            declared[name] = row

    catalog_names = _catalog_names()
    published = sorted(name for name in declared if name in catalog_names)
    catalog_without_declaration = sorted(catalog_names - set(declared))
    source_only = sorted(set(declared) - catalog_names)

    payload = {
        "schema_version": 1,
        "extracted_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_root": "vendor/RevitCortex",
        "source_url": SOURCE_URL,
        "source_commit": _git("rev-parse", "HEAD"),
        "attribute_definition": "src/RevitCortex.Core/Tools/ToolSafetyAttribute.cs",
        "router_resolution": (
            "CortexRouter.ResolveToolSafety: IToolSafetyAware, then [ToolSafety], "
            "then IsReadOnlyTool(name) with destructive false"
        ),
        "prefix_read_only_rules": list(PREFIX_READ_ONLY),
        "resolution_rule": (
            "a declared [ToolSafety] wins; a catalog tool without a declaration uses the "
            "prefix fallback exactly as CortexRouter does"
        ),
        "declared_tool_count": len(published),
        "catalog_tool_count": len(catalog_names),
        "catalog_tools_without_declaration": catalog_without_declaration,
        "source_tools_absent_from_catalog": source_only,
        "conflicting_declarations": sorted(set(conflicts)),
        "ambiguous_files": sorted(set(ambiguous)),
        "tools": {},
    }

    for name in sorted(catalog_names):
        reading = declared.get(name) or {}
        declared_read_only = reading.get("read_only")
        if declared_read_only is None:
            read_only, destructive = name.startswith(PREFIX_READ_ONLY), False
        else:
            read_only, destructive = declared_read_only, reading.get("destructive")
        payload["tools"][name] = {
            "read_only": read_only,
            "destructive": destructive,
            "declared": declared_read_only is not None,
            "source_file": reading.get("source_file"),
            "source_line": reading.get("source_line"),
        }

    if payload["source_commit"] != SOURCE_COMMIT:
        raise SystemExit(
            "vendor checkout is at %s but the pinned commit is %s"
            % (payload["source_commit"], SOURCE_COMMIT)
        )
    return payload


def _without_timestamp(text):
    return re.sub(r'"extracted_utc": "[^"]*",\n', "", text).strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description="extract Cortex tool safety")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    payload = extract()
    rendered = json.dumps(payload, indent=2) + "\n"

    if args.check:
        if not OUTPUT_PATH.exists():
            print("MISSING %s" % OUTPUT_PATH)
            return 1
        current = OUTPUT_PATH.read_text(encoding="utf-8")
        if _without_timestamp(current) != _without_timestamp(rendered):
            print("STALE %s" % OUTPUT_PATH)
            return 1
        print("OK %s matches a fresh extraction" % OUTPUT_PATH)
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    print(
        "wrote %s (%d declared of %d catalog tools, sha256 %s)"
        % (OUTPUT_PATH, payload["declared_tool_count"], payload["catalog_tool_count"], digest)
    )
    unresolved = len(payload["catalog_tools_without_declaration"])
    print("catalog tools without a declaration (prefix fallback): %d" % unresolved)
    if payload["conflicting_declarations"]:
        print("conflicts: %s" % ", ".join(payload["conflicting_declarations"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

