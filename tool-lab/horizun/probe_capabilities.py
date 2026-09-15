"""Disposable LAB probe for the Amanda-to-Horizun provider routes.

This script is intentionally separate from the provider and is not executed by
unit tests.  The Revit lease owner may run it against a disposable ``LAB_*``
document after supplying an explicit confirmation and, for R01, a template.
Every reported ``PROVEN`` result includes an independent query by the returned
ElementId (or an independent document-info read for project creation).
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.providers.horizun import HorizunInvoker
from amanda_agent.bim.providers.transport import McpProbeTransport
from amanda_agent.bim.stages import StageToolCall

ROUTES = {
    "revit.create_project": "horizun_document_session",
    "revit.create_toposolid": "horizun_execute_python",
    "revit.create_mass": "horizun_execute_python",
    "revit.create_reference": "horizun_execute_python",
    "revit.create_accessibility_element": "horizun_execute_python",
    "revit.create_furniture_element": "horizun_execute_python",
    "revit.create_landscape_element": "horizun_execute_python",
    "revit.assign_material": "horizun_execute_python",
    "revit.create_documentation_element": "horizun_execute_python",
    "revit.create_level": "horizun_create_elements",
    "revit.create_grid": "horizun_create_elements",
    "revit.create_wall": "horizun_create_elements",
    "revit.create_floor": "horizun_create_elements",
    "revit.create_slab": "horizun_create_elements",
    "revit.create_roof": "horizun_create_elements",
    "revit.create_internal_wall": "horizun_create_elements",
    "revit.create_room": "horizun_create_elements",
    "revit.create_opening": "horizun_create_elements",
}

STAGES = {
    "revit.create_project": BimStage.R01,
    "revit.create_toposolid": BimStage.R02,
    "revit.create_reference": BimStage.R03,
    "revit.create_level": BimStage.R03,
    "revit.create_grid": BimStage.R03,
    "revit.create_mass": BimStage.R04,
    "revit.create_wall": BimStage.R05,
    "revit.create_floor": BimStage.R06,
    "revit.create_slab": BimStage.R06,
    "revit.create_roof": BimStage.R08,
    "revit.create_internal_wall": BimStage.R05,
    "revit.create_room": BimStage.R08,
    "revit.create_opening": BimStage.R07,
    "revit.create_accessibility_element": BimStage.R09,
    "revit.create_furniture_element": BimStage.R10,
    "revit.create_landscape_element": BimStage.R11,
    "revit.assign_material": BimStage.R12,
    "revit.create_documentation_element": BimStage.R13,
}


_PROBE_REFERENCES = ("PROBE-WALL", "PROBE-ROOM")
_RUN_TAG = uuid.uuid4().hex[:6].upper()


def _with_run_tag(value: Any) -> Any:
    """Suffix probe logical references so a rerun never collides with the previous one."""

    if isinstance(value, str) and value.strip() in _PROBE_REFERENCES:
        return f"{value.strip()}-{_RUN_TAG}"
    if isinstance(value, str) and value.strip().startswith("AMANDA_PROBE_"):
        # Live probe evidence, .tmp-probe-live7.log: a level and a grid are named
        # in the model and Revit refuses the whole atomic batch when the name
        # already exists ("Revit refused the name 'AMANDA_PROBE_LEVEL'", "the grid
        # was created and Revit refused the name 'AMANDA_PROBE_GRID': Name must be
        # unique"), so a rerun needs its own name. The room number is unique per
        # level for the same reason.
        return f"{value.strip()}-{_RUN_TAG}"
    if isinstance(value, str) and value.strip() == "P-001":
        return f"P-{_RUN_TAG}"
    if isinstance(value, Mapping):
        return {key: _with_run_tag(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_with_run_tag(item) for item in value]
    return value


def _rows(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, Mapping)]
    if not isinstance(payload, Mapping):
        return []
    for key in ("rows", "elements", "items", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, Mapping)]
    return []


def _element_id(row: Mapping[str, Any]) -> int | None:
    for key in ("element_id", "id", "ElementId", "revit_id"):
        value = row.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value)
    return None


def _returned_element_id(payload: Any) -> int | None:
    if isinstance(payload, Mapping):
        direct = _element_id(payload)
        if direct is not None:
            return direct
        created = payload.get("created_ids")
        if isinstance(created, list):
            for value in created:
                if isinstance(value, int) and not isinstance(value, bool):
                    return value
        for key in ("payload", "read_payload", "result", "data"):
            nested = payload.get(key)
            if isinstance(nested, Mapping):
                direct = _element_id(nested)
                if direct is not None:
                    return direct
        # A Python route reports what it created in the script's own __output__,
        # which the bridge carries at structuredContent.output as a structure or as
        # a JSON string; without reading it every Python route looks id-less even
        # when Revit committed the element (live: wall id 328666, api7 opening id
        # 328864).
        output = payload.get("output")
        if isinstance(output, str) and output.strip().startswith("{"):
            try:
                output = json.loads(output)
            except ValueError:
                output = None
        if isinstance(output, Mapping):
            direct = _element_id(output)
            if direct is not None:
                return direct
            for row in _rows(output):
                direct = _element_id(row)
                if direct is not None:
                    return direct
        for row in _rows(payload):
            direct = _element_id(row)
            if direct is not None:
                return direct
        for row in _rows(payload.get("readback_rows")):
            direct = _element_id(row)
            if direct is not None:
                return direct
    return None


def _first_category_id(transport: McpProbeTransport, invoker: HorizunInvoker, category: str) -> int | None:
    reply = transport.call(
        "horizun_list_elements",
        {"category": category, "include_links": False, "max_rows": 2000},
    )
    result = invoker._result("horizun_list_elements", reply, None)
    if not result.reported_success:
        return None
    for row in _rows(result.read_payload):
        value = _element_id(row)
        if value is not None:
            return value
    return None


def _call(
    *,
    target: str,
    capability: str,
    logical_id: str,
    payload: Mapping[str, Any],
) -> StageToolCall:
    key = f"probe-{capability.replace('.', '-')}-{_RUN_TAG.lower()}-{logical_id.lower()}"
    # A probe proves a route only if the route really runs: the bridge treats a
    # missing dry_run as a rehearsal, and a rehearsal writes nothing.
    values = {"target_document": target, "idempotency_key": key, "dry_run": False}
    values.update(payload)
    return StageToolCall(
        stage=STAGES[capability],
        logical_id=f"{logical_id}-{_RUN_TAG}",
        semantic_capability=capability,
        provider="horizun",
        payload=_with_run_tag(values),
    )


def _independent_query(
    transport: McpProbeTransport,
    invoker: HorizunInvoker,
    element_id: int,
) -> tuple[bool, str]:
    reply = transport.call(
        "horizun_query_model",
        {
            "element_ids": [element_id],
            "response_mode": "full",
            "cache_mode": "bypass",
            "include_types": True,
        },
    )
    result = invoker._result("horizun_query_model", reply, None)
    if not result.reported_success:
        return False, f"independent query failed: {result.error or result.read_payload}"
    rows = _rows(result.read_payload)
    if not rows:
        return False, "independent query returned no row for the returned ElementId"
    return True, f"independent query returned {len(rows)} row(s) for ElementId {element_id}"


def _record(
    transport: McpProbeTransport,
    invoker: HorizunInvoker,
    call: StageToolCall,
) -> dict[str, Any]:
    capability = call.semantic_capability
    route = ROUTES[capability]
    try:
        result = invoker.invoke(call)
    except Exception as exc:  # noqa: BLE001 - a probe records route failures
        return {
            "capability": capability,
            "route": route,
            "status": "UNPROVEN",
            "reason": f"adapter raised {type(exc).__name__}: {exc}",
        }
    if not result.reported_success:
        return {
            "capability": capability,
            "route": route,
            "status": "UNPROVEN",
            "reason": f"provider returned failure: {result.error or result.read_payload}",
        }
    if capability == "revit.create_project":
        reply = transport.call("get_document_info", {})
        info = invoker._result("get_document_info", reply, None)
        if info.reported_success:
            # Live probe evidence, .tmp-ds-open.log: open really opened the project
            # (title Default_M_PTB, is_family_document false, element_count 3230).
            # Reporting PROVEN off any successful read would also accept a read of
            # the document that was already open, which proves nothing about R01, so
            # the read has to be the requested project or the route is not proven.
            info_payload = info.read_payload if isinstance(info.read_payload, Mapping) else {}
            requested = Path(str(call.payload.get("template_path") or "")).name
            opened = str(info_payload.get("path") or "")
            opened_title = str(info_payload.get("title") or "")
            opened_name = Path(opened).name if opened else opened_title
            if requested and requested.casefold() not in (
                opened_name.casefold(),
                f"{opened_title.casefold()}.rte",
                opened_title.casefold(),
            ):
                return {
                    "capability": capability,
                    "route": route,
                    "status": "UNPROVEN",
                    "reason": (
                        "document readback succeeded but reports "
                        f"{opened_title or opened!r}, not the requested {requested!r}"
                    ),
                }
            if info_payload.get("is_family_document") is True:
                return {
                    "capability": capability,
                    "route": route,
                    "status": "UNPROVEN",
                    "reason": "the opened document is a family document, not a project",
                }
            return {
                "capability": capability,
                "route": route,
                "status": "PROVEN",
                "evidence": (
                    "independent get_document_info reports the requested project "
                    f"{info_payload.get('title')!r} at {opened!r} after document_session.open"
                ),
            }
        return {
            "capability": capability,
            "route": route,
            "status": "UNPROVEN",
            "reason": f"document readback failed: {info.error or info.read_payload}",
        }
    element_id = _returned_element_id(result.read_payload)
    if element_id is None:
        return {
            "capability": capability,
            "route": route,
            "status": "UNPROVEN",
            "reason": "provider succeeded without a returned integer ElementId",
        }
    proven, evidence = _independent_query(transport, invoker, element_id)
    return {
        "capability": capability,
        "route": route,
        "status": "PROVEN" if proven else "UNPROVEN",
        "element_id": element_id,
        "evidence": evidence if proven else None,
        "reason": None if proven else evidence,
    }


def _guard_target(target: str) -> None:
    normalized = target.casefold()
    if "lab_" not in normalized and "lab-" not in normalized:
        raise ValueError("probe refuses a target without LAB_ or LAB- in its document identity")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-document", required=True, help="disposable LAB document identity")
    parser.add_argument(
        "--run-tag",
        default=None,
        help="stable suffix for this run; defaults to a random tag so reruns never collide",
    )
    parser.add_argument(
        "--template-path",
        type=Path,
        help="architectural template for the optional R01 project route",
    )
    parser.add_argument(
        "--confirm-live-lab",
        action="store_true",
        help="required acknowledgement that this probe commits disposable LAB elements",
    )
    parser.add_argument(
        "--only",
        default=None,
        choices=sorted(ROUTES),
        help="run just this route (used to prove R01 in isolation)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    global _RUN_TAG
    parser = _parser()
    args = parser.parse_args(argv)
    if getattr(args, "run_tag", None):
        _RUN_TAG = str(args.run_tag).strip().upper()
    try:
        _guard_target(args.target_document)
    except ValueError as exc:
        parser.error(str(exc))
    if not args.confirm_live_lab:
        parser.error("refusing to run without --confirm-live-lab")

    report: list[dict[str, Any]] = []
    with McpProbeTransport() as transport:
        invoker = HorizunInvoker(transport=transport, target_document=args.target_document)
        level_id = _first_category_id(transport, invoker, "OST_Levels")
        furniture_type_id = _first_category_id(transport, invoker, "OST_Furniture")

        operations = [
            _call(
                target=args.target_document,
                capability="revit.create_level",
                logical_id="PROBE-LEVEL",
                payload={"geometry": {"elevation_m": 0.0}, "properties": {"name": "AMANDA_PROBE_LEVEL"}},
            ),
            _call(
                target=args.target_document,
                capability="revit.create_grid",
                logical_id="PROBE-GRID",
                payload={"geometry": {"start": [0.0, 0.0], "end": [5.0, 0.0]}, "properties": {"name": "AMANDA_PROBE_GRID"}},
            ),
            _call(
                target=args.target_document,
                capability="revit.create_wall",
                logical_id="PROBE-WALL",
                payload={
                    "geometry": {"start": [0.0, 0.0], "end": [3.0, 0.0], "level_id": level_id or 311, "height": 2.8},
                },
            ),
            _call(
                target=args.target_document,
                capability="revit.create_floor",
                logical_id="PROBE-FLOOR",
                payload={"geometry": {"footprint": [[0.0, 0.0], [3.0, 0.0], [3.0, 3.0], [0.0, 3.0]], "level_id": level_id or 311}},
            ),
            _call(
                target=args.target_document,
                capability="revit.create_slab",
                logical_id="PROBE-SLAB",
                payload={"geometry": {"footprint": [[4.0, 0.0], [7.0, 0.0], [7.0, 3.0], [4.0, 3.0]], "level_id": level_id or 311}},
            ),
            _call(
                target=args.target_document,
                capability="revit.create_roof",
                logical_id="PROBE-ROOF",
                payload={"geometry": {"footprint": [[0.0, 4.0], [3.0, 4.0], [3.0, 7.0], [0.0, 7.0]], "level_id": level_id or 311}},
            ),
            _call(
                target=args.target_document,
                capability="revit.create_internal_wall",
                logical_id="PROBE-INTERNAL-WALL",
                payload={"geometry": {"start": [0.0, 1.0], "end": [3.0, 1.0], "level_id": level_id or 311, "height": 2.8}},
            ),
            _call(
                target=args.target_document,
                capability="revit.create_room",
                logical_id="PROBE-ROOM",
                payload={"geometry": {"point": [1.0, 1.0], "level_id": level_id or 311}, "properties": {"name": "AMANDA_PROBE_ROOM", "number": "P-001"}},
            ),
            _call(
                target=args.target_document,
                capability="revit.create_opening",
                logical_id="PROBE-OPENING",
                # Live probe evidence, probe-api7-live.json: an opening whose diagonal
                # corners share a height is refused by Revit ("Failed to create an
                # opening on the wall.") after the request was already sent, so the
                # probe asks for the pair that really commits: 0.1 m and 2.1 m.
                payload={
                    "geometry": {
                        "corner_1": [1.0, 0.0, 0.1],
                        "corner_2": [1.8, 0.0, 2.1],
                        "host_logical_id": "PROBE-WALL",
                    }
                },
            ),
            _call(
                target=args.target_document,
                capability="revit.create_toposolid",
                logical_id="PROBE-TOPOSOLID",
                payload={"points": [[0.0, 0.0, 0.0], [3.0, 0.0, 0.2], [3.0, 3.0, 0.4], [0.0, 3.0, 0.1]]},
            ),
            _call(
                target=args.target_document,
                capability="revit.create_mass",
                logical_id="PROBE-MASS",
                payload={"geometry": {"footprint": [[5.0, 0.0], [7.0, 0.0], [7.0, 2.0], [5.0, 2.0]], "height_m": 2.5}, "properties": {"name": "AMANDA_PROBE_MASS"}},
            ),
            _call(
                target=args.target_document,
                capability="revit.create_reference",
                logical_id="PROBE-REFERENCE",
                payload={"geometry": {"coordinate": [0.0, 0.0, 0.0]}, "properties": {"name": "AMANDA_PROBE_REFERENCE"}},
            ),
            _call(
                target=args.target_document,
                capability="revit.create_accessibility_element",
                logical_id="PROBE-ACCESSIBILITY",
                payload={"geometry": {"location": [1.0, 1.0, 0.0]}, "properties": {"from_node": "PROBE-ROOM", "to_node": "PROBE-ROOM"}},
            ),
            _call(
                target=args.target_document,
                capability="revit.create_furniture_element",
                logical_id="PROBE-FURNITURE",
                payload={
                    "geometry": {"host_space_id": "PROBE-ROOM", "location": [1.5, 1.5, 0.0]},
                    "properties": {"type_id": furniture_type_id} if furniture_type_id is not None else {},
                },
            ),
            _call(
                target=args.target_document,
                capability="revit.create_landscape_element",
                logical_id="PROBE-LANDSCAPE",
                payload={"geometry": {"host_zone": "PROBE-ROOM", "target_area_m2": 9.0}},
            ),
            _call(
                target=args.target_document,
                capability="revit.assign_material",
                logical_id="PROBE-WALL",
                payload={
                    "geometry": {"host_element": "PROBE-WALL"},
                    "host_category": "OST_Walls",
                    "properties": {"material_name": "AMANDA_PROBE_MATERIAL"},
                },
            ),
            _call(
                target=args.target_document,
                capability="revit.create_documentation_element",
                logical_id="PROBE-SHEET",
                payload={"geometry": {"documentation_kind": "sheet"}, "properties": {"documentation_kind": "sheet", "sheet_id": "A-PROBE"}},
            ),
        ]
        for call in operations:
            if args.only is not None and call.semantic_capability != args.only:
                continue
            item = _record(transport, invoker, call)
            report.append(item)
            print(f"{item['status']} {item['capability']}: {item.get('reason') or item.get('evidence')}")

        if args.template_path is None:
            if args.only in (None, "revit.create_project"):
                item = {
                    "capability": "revit.create_project",
                    "route": ROUTES["revit.create_project"],
                    "status": "UNPROVEN",
                    "reason": "--template-path was not supplied; no project open was attempted",
                }
                report.append(item)
                print(f"{item['status']} {item['capability']}: {item['reason']}")
        else:
            item = _record(
                transport,
                invoker,
                _call(
                    target=args.target_document,
                    capability="revit.create_project",
                    logical_id="PROBE-PROJECT",
                    payload={"template_path": str(args.template_path)},
                ),
            )
            report.append(item)
            print(f"{item['status']} {item['capability']}: {item.get('reason') or item.get('evidence')}")

    print(json.dumps({"target_document": args.target_document, "routes": report}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
