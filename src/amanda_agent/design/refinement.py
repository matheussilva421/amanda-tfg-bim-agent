"""P08-T06 refinement, scoring and reviewable finalist artifacts.

This module consumes an already published macro run.  It never rewrites that
run: the macro record is the immutable input and this stage publishes a
separate refinement summary and one artifact directory per selected finalist.
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import os
import tempfile
from collections.abc import Mapping, Sequence
from itertools import pairwise
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw
from shapely.geometry import LineString, Polygon, mapping, shape
from shapely.ops import unary_union

from .blocks import generate_blocks
from .constraints import hard_violations_only, validate_candidate
from .explain import explain_candidate, explanation_markdown
from .external_spaces import (
    ExternalSpaceViolation,
    generate_external_spaces,
    validate_external_spaces,
)
from .flows import FlowNetwork, FlowPolicy, analyze_route, build_flow_graph
from .generate import canonical_geometry_hash
from .geometry import validate_polygon
from .pareto import pareto_frontier
from .privacy import evaluate_privacy_gradient
from .rooms import refine_rooms
from .scoring import load_weight_config, load_weights, score_candidate

SCORE_DIMENSIONS = (
    "program_compliance",
    "privacy_security",
    "adjacency",
    "circulation",
    "accessibility",
    "solar_heuristic",
    "ventilation_heuristic",
    "green_integration",
    "compactness",
    "constructability",
    "concept_fidelity",
)

_SECTOR_PRIVACY = {
    "SEC-01": 0,
    "SEC-02": 5,
    "SEC-03": 1,
    "SEC-04": 2,
    "SEC-05": 2,
    "SEC-06": 3,
    "SEC-07": 1,
}
_SECTOR_ORDER = {
    "SEC-01": 0,
    "SEC-03": 1,
    "SEC-04": 2,
    "SEC-05": 3,
    "SEC-06": 4,
    "SEC-07": 5,
    "SEC-02": 6,
}
_ALL_FLOWS = [flow.value for flow in FlowNetwork]
_DEFAULT_REQUIREMENTS_VERSION = "requirements-v1"
_DEFAULT_SITE_VERSION = "site-v1"


class RefinementInputError(RuntimeError):
    """Raised when the immutable macro run cannot be refined safely."""


def _json_safe(value: Any) -> Any:
    if hasattr(value, "__geo_interface__"):
        return _json_safe(value.__geo_interface__)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "value") and isinstance(value.value, (str, int, float)):
        return value.value
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump(mode="python"))
    return str(value)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise RefinementInputError(f"{label} is missing or mutable: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RefinementInputError(f"{label} is invalid: {path}") from exc
    if not isinstance(payload, Mapping):
        raise RefinementInputError(f"{label} must be a JSON object")
    return dict(payload)


def _polygon(value: Any) -> Polygon:
    try:
        if isinstance(value, Polygon):
            return validate_polygon(value)
        if isinstance(value, Mapping):
            return validate_polygon(shape(value))
        return validate_polygon(value)
    except (TypeError, ValueError) as exc:
        raise RefinementInputError("candidate contains invalid polygon geometry") from exc


def _sector_value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def _space_area(space: Any) -> float:
    return float(_sector_value(space, "target_area_m2", 0.0)) * int(
        _sector_value(space, "quantity", 1) or 1
    )


def _requirements_by_sector(requirements: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(_sector_value(sector, "logical_id", "")): sector
        for sector in requirements.get("sectors", []) or []
    }


def _site_geometry(site: Mapping[str, Any]) -> Polygon:
    boundary = site.get("boundary")
    if isinstance(boundary, Mapping):
        return _polygon(boundary.get("coordinates", boundary))
    return _polygon(boundary or site)


def _candidate_id(candidate: Mapping[str, Any]) -> str:
    direct = candidate.get("candidate_id")
    if direct:
        return str(direct)
    return f"{candidate.get('archetype', 'UNKNOWN')}:{candidate.get('seed', 'UNKNOWN')}"


def _candidate_records(run: Mapping[str, Any], top_limit: int) -> list[dict[str, Any]]:
    ranking = [item for item in run.get("ranking", []) or [] if isinstance(item, Mapping)]
    by_id: dict[str, dict[str, Any]] = {}
    for item in run.get("finalists", []) or []:
        if not isinstance(item, Mapping):
            continue
        candidate = dict(item)
        identifier = _candidate_id(candidate)
        by_id[identifier] = candidate
    for item in run.get("macro_candidates", []) or []:
        if isinstance(item, Mapping):
            by_id.setdefault(_candidate_id(item), dict(item))

    ordered_ids = [_candidate_id(item) for item in ranking[:top_limit]]
    for identifier in run.get("pareto_frontier_ids", []) or []:
        if str(identifier) not in ordered_ids:
            ordered_ids.append(str(identifier))
    if not ordered_ids:
        ordered_ids = list(by_id)

    records: list[dict[str, Any]] = []
    for identifier in ordered_ids:
        ranked = next(
            (dict(item) for item in ranking if _candidate_id(item) == identifier),
            {"candidate_id": identifier},
        )
        record = dict(ranked)
        record.update(by_id.get(identifier, {}))
        record["candidate_id"] = identifier
        records.append(record)
    return records


def _write_bytes(path: Path, data: bytes) -> None:
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _write_text(path: Path, text: str) -> None:
    _write_bytes(path, text.encode("utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _write_text(path, json.dumps(_json_safe(payload), ensure_ascii=False, indent=2) + "\n")


def _requirements_groups(requirements: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    internal: list[Mapping[str, Any]] = []
    external: list[Mapping[str, Any]] = []
    for sector in requirements.get("sectors", []) or []:
        target = external if str(_sector_value(sector, "area_kind", "INTERNAL")) == "EXTERNAL" else internal
        target.append(sector)
    return internal, external


def _internal_requirements(requirements: Mapping[str, Any]) -> dict[str, Any]:
    """Build the room-validation view without treating outdoor spaces as rooms."""

    internal, _ = _requirements_groups(requirements)
    values = {key: value for key, value in requirements.items() if key != "sectors"}
    values["sectors"] = internal
    return values


def _sector_demand(sector: Mapping[str, Any]) -> float:
    return sum(_space_area(space) for space in sector.get("spaces", []) or [])


def _refine_candidate(
    record: Mapping[str, Any],
    requirements: Mapping[str, Any],
    site: Mapping[str, Any],
) -> dict[str, Any]:
    geometry = record.get("geometry")
    if not isinstance(geometry, Mapping):
        raise RefinementInputError(f"macro geometry is unavailable for {_candidate_id(record)}")
    macro_sectors = geometry.get("sectors", [])
    if not isinstance(macro_sectors, Sequence) or isinstance(macro_sectors, (str, bytes)):
        raise RefinementInputError(f"macro sectors are unavailable for {_candidate_id(record)}")
    requirement_by_id = _requirements_by_sector(requirements)
    macro_by_id = {
        str(_sector_value(item, "logical_id", "")): item
        for item in macro_sectors
        if isinstance(item, Mapping)
    }
    internal_requirements, external_requirements = _requirements_groups(requirements)
    internal_sector_inputs: list[dict[str, Any]] = []
    for sector in internal_requirements:
        sector_id = str(_sector_value(sector, "logical_id", ""))
        macro = macro_by_id.get(sector_id)
        if macro is None:
            raise RefinementInputError(f"required sector {sector_id} is missing from macro geometry")
        internal_sector_inputs.append(
            {
                "logical_id": sector_id,
                "geometry": macro.get("geometry"),
                "demand_m2": _sector_demand(sector),
            }
        )

    block_result = generate_blocks(internal_sector_inputs, min_width_m=1.0)
    block_violations = list(block_result.violations)
    if block_violations:
        return {
            "candidate_id": _candidate_id(record),
            "record": dict(record),
            "rejected": True,
            "reason": "; ".join(item.message for item in block_violations),
            "rejection_codes": [item.code for item in block_violations],
        }

    blocks: list[dict[str, Any]] = []
    rooms: list[dict[str, Any]] = []
    accounting = {
        "internal_net_area_m2": 0.0,
        "gross_footprint_m2": 0.0,
        "wall_area_m2": 0.0,
        "shafts_m2": 0.0,
        "circulation_m2": 0.0,
        "storeys": 1.0,
    }
    for raw_block in block_result.blocks:
        block = dict(raw_block)
        sector_id = str(block["sector_id"])
        refined = refine_rooms(block, list(requirement_by_id[sector_id].get("spaces", [])))
        if not refined.ok:
            return {
                "candidate_id": _candidate_id(record),
                "record": dict(record),
                "rejected": True,
                "reason": "; ".join(item.message for item in refined.violations),
                "rejection_codes": [item.code for item in refined.violations],
            }
        block["geometry"] = mapping(_polygon(block["geometry"]))
        blocks.append(block)
        for key in accounting:
            if key in refined.accounting and key != "storeys":
                accounting[key] += float(refined.accounting[key])
        for room in refined.rooms:
            enriched = dict(room)
            enriched["geometry"] = mapping(_polygon(enriched["geometry"]))
            enriched["block_id"] = str(block["logical_id"])
            enriched["sector_id"] = sector_id
            enriched["privacy_level"] = _SECTOR_PRIVACY.get(sector_id, 2)
            enriched["private_residential"] = sector_id == "SEC-02"
            rooms.append(enriched)

    site_polygon = _site_geometry(site)
    external_zone = site_polygon
    external_sector_id = str(_sector_value(external_requirements[0], "logical_id", "")) if external_requirements else ""
    if external_sector_id in macro_by_id:
        external_zone = _polygon(macro_by_id[external_sector_id].get("geometry"))
    external_result = generate_external_spaces(
        external_zone,
        [space for sector in external_requirements for space in sector.get("spaces", []) or []],
    )
    external_spaces = [dict(item) for item in external_result.spaces]
    for item in external_spaces:
        item["geometry"] = mapping(_polygon(item["geometry"]))
        item["sector_id"] = external_sector_id
    external_validation = validate_external_spaces(external_spaces, mapping(site_polygon))
    external_violations = list(external_result.violations) + list(external_validation.violations)
    for external in external_spaces:
        external_polygon = _polygon(external["geometry"])
        if any(external_polygon.intersection(_polygon(block["geometry"])).area > 1e-6 for block in blocks):
            external_violations.append(
                ExternalSpaceViolation(
                    "external_building_overlap",
                    f"external space {external['logical_id']} overlaps a building block",
                    str(external["logical_id"]),
                )
            )
    if external_violations:
        return {
            "candidate_id": _candidate_id(record),
            "record": dict(record),
            "rejected": True,
            "reason": "; ".join(item.message for item in external_violations),
            "rejection_codes": [item.code for item in external_violations],
        }
    accounting["external_area_m2"] = sum(float(_polygon(item["geometry"]).area) for item in external_spaces)
    accounting["net_area_m2"] = accounting["internal_net_area_m2"]
    accounting["wall_area_m2"] = accounting["gross_footprint_m2"] - accounting["internal_net_area_m2"]
    accounting["net_to_gross_factor"] = accounting["internal_net_area_m2"] / max(
        accounting["gross_footprint_m2"] + accounting["circulation_m2"], 1e-9
    )
    accounting["total_program_area_m2"] = accounting["internal_net_area_m2"] + accounting["external_area_m2"]

    block_candidate = {"resolution": "BLOCK", "blocks": blocks}
    room_candidate = {"resolution": "ROOM", "rooms": rooms}
    internal_requirements = _internal_requirements(requirements)
    block_checks = validate_candidate(block_candidate, internal_requirements, mapping(site_polygon))
    room_checks = validate_candidate(room_candidate, internal_requirements, mapping(site_polygon))
    hard_checks = hard_violations_only([*block_checks, *room_checks])
    if hard_checks:
        return {
            "candidate_id": _candidate_id(record),
            "record": dict(record),
            "rejected": True,
            "reason": "; ".join(item.message for item in hard_checks),
            "rejection_codes": [item.code for item in hard_checks],
        }

    geometry_payload = {
        "type": "DesignGeometry",
        "site": mapping(site_polygon),
        "macrozones": [
            {
                "logical_id": str(_sector_value(item, "logical_id", "")),
                "geometry": mapping(_polygon(item["geometry"])),
                "area_m2": float(_polygon(item["geometry"]).area),
            }
            for item in macro_sectors
            if isinstance(item, Mapping) and item.get("geometry") is not None
        ],
        "blocks": blocks,
        "rooms": rooms,
        "external_spaces": external_spaces,
        "accounting": accounting,
    }
    adjacency = _build_adjacency(blocks, external_spaces, site_polygon)
    flows = _build_flows(rooms)
    metrics, score, penalties, metric_evidence = _score_refined(
        record, requirements, blocks, rooms, external_spaces, accounting, adjacency, flows
    )
    return {
        "candidate_id": _candidate_id(record),
        "record": dict(record),
        "rejected": False,
        "blocks": blocks,
        "rooms": rooms,
        "external_spaces": external_spaces,
        "accounting": accounting,
        "geometry": geometry_payload,
        "adjacency": adjacency,
        "flows": flows,
        "block_checks": block_checks,
        "room_checks": room_checks,
        "external_checks": [*external_result.violations, *external_validation.violations],
        "hard_checks": hard_checks,
        "metrics": metrics,
        "score": score,
        "penalties": penalties,
        "metric_evidence": metric_evidence,
        "geometry_hash": canonical_geometry_hash(geometry_payload),
    }


def _build_adjacency(
    blocks: list[Mapping[str, Any]],
    external_spaces: list[Mapping[str, Any]],
    site_polygon: Polygon,
) -> dict[str, Any]:
    ordered = sorted(
        blocks,
        key=lambda item: (
            _SECTOR_ORDER.get(str(item.get("sector_id", "")), 99),
            str(item.get("logical_id", "")),
        ),
    )
    nodes = [
        {
            "logical_id": str(item["logical_id"]),
            "kind": "block",
            "sector_id": str(item.get("sector_id", "")),
        }
        for item in ordered
    ]
    nodes.extend(
        {
            "logical_id": str(item["logical_id"]),
            "kind": "external_space",
            "sector_id": str(item.get("sector_id", "")),
        }
        for item in external_spaces
    )
    edges: list[dict[str, Any]] = []
    for first, second in pairwise(ordered):
        left = _polygon(first["geometry"])
        right = _polygon(second["geometry"])
        distance = float(left.distance(right))
        edges.append(
            {
                "source": str(first["logical_id"]),
                "target": str(second["logical_id"]),
                "relation": "DERIVED_NEAREST_BLOCK",
                "distance_m": distance,
                "evidence": "actual block polygons evaluated with Shapely",
            }
        )
    diagonal = max(float(site_polygon.length), 1.0)
    mean_distance = sum(float(edge["distance_m"]) for edge in edges) / max(len(edges), 1)
    score = max(0.0, min(1.0, 1.0 - mean_distance / diagonal))
    return {
        "schema_version": 1,
        "nodes": nodes,
        "edges": edges,
        "score": score,
        "mean_interblock_distance_m": mean_distance,
        "evidence": "No canonical relation list is present in program.json; score uses actual nearest block distances.",
    }


def _room_order(rooms: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return sorted(
        rooms,
        key=lambda item: (
            _SECTOR_ORDER.get(str(item.get("sector_id", "")), 99),
            str(item.get("block_id", "")),
            str(item.get("logical_id", "")),
        ),
    )


def _build_flows(rooms: list[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = _room_order(rooms)
    nodes = [
        {
            "id": str(room["logical_id"]),
            "logical_id": str(room["logical_id"]),
            "geometry": room["geometry"],
            "private_residential": bool(room.get("private_residential", False)),
            "privacy_level": int(room.get("privacy_level", 2)),
            "allowed_flows": list(_ALL_FLOWS),
        }
        for room in ordered
    ]
    connections: list[dict[str, Any]] = []
    for index, (first, second) in enumerate(pairwise(ordered), start=1):
        first_polygon = _polygon(first["geometry"])
        second_polygon = _polygon(second["geometry"])
        first_point = first_polygon.centroid
        second_point = second_polygon.centroid
        line = LineString([(first_point.x, first_point.y), (second_point.x, second_point.y)])
        connections.append(
            {
                "id": f"flow-edge-{index:03d}",
                "from": str(first["logical_id"]),
                "to": str(second["logical_id"]),
                "geometry": mapping(line),
                "width_m": 1.2,
                "length_m": float(line.length),
                "allowed_flows": list(_ALL_FLOWS),
            }
        )
    candidate = {"nodes": nodes, "connections": connections}
    entry = next((str(room["logical_id"]) for room in ordered if room.get("sector_id") == "SEC-01"), str(ordered[0]["logical_id"]))
    goal_by_flow = {
        FlowNetwork.RESIDENT: next((str(room["logical_id"]) for room in ordered if room.get("sector_id") == "SEC-02"), entry),
        FlowNetwork.CHILD: next((str(room["logical_id"]) for room in ordered if room.get("sector_id") == "SEC-03"), entry),
        FlowNetwork.STAFF: next((str(room["logical_id"]) for room in ordered if room.get("sector_id") == "SEC-06"), entry),
        FlowNetwork.VISITOR: next((str(room["logical_id"]) for room in ordered if room.get("sector_id") == "SEC-05"), entry),
        FlowNetwork.SERVICE: next((str(room["logical_id"]) for room in ordered if room.get("sector_id") == "SEC-06"), entry),
        FlowNetwork.EMERGENCY: str(ordered[-1]["logical_id"]),
    }
    analyses: dict[str, dict[str, Any]] = {}
    graph_exports: dict[str, Any] = {}
    for flow in FlowNetwork:
        graph = build_flow_graph(candidate, flow, min_width_m=0.9)
        analysis = analyze_route(
            graph,
            entry,
            goal_by_flow[flow],
            policy=FlowPolicy(forbid_private_residential=True),
        )
        analyses[flow.value] = {
            "start": entry,
            "goal": goal_by_flow[flow],
            "path": analysis.path,
            "distance_m": analysis.distance_m,
            "crossings": analysis.crossings,
            "ok": analysis.ok,
            "violations": [_json_safe(item) for item in analysis.violations],
            "evidence": list(analysis.evidence),
        }
        graph_exports[flow.value] = {
            "nodes": list(graph.nodes),
            "edges": [
                {
                    "source": source,
                    "target": target,
                    "edge_id": next(
                        (
                            item["id"]
                            for item in connections
                            if {item["from"], item["to"]} == {source, target}
                        ),
                        f"{source}->{target}",
                    ),
                }
                for source, target in graph.edges
            ],
        }
    return {
        "schema_version": 1,
        "nodes": nodes,
        "connections": connections,
        "graphs": graph_exports,
        "analyses": analyses,
        "evidence": "Six independent graphs were built from the published room polygons and explicit corridor centerlines.",
    }


def _score_refined(
    record: Mapping[str, Any],
    requirements: Mapping[str, Any],
    blocks: list[Mapping[str, Any]],
    rooms: list[Mapping[str, Any]],
    external_spaces: list[Mapping[str, Any]],
    accounting: Mapping[str, float],
    adjacency: Mapping[str, Any],
    flows: Mapping[str, Any],
) -> tuple[dict[str, float | None], Any, dict[str, float], dict[str, Any]]:
    internal_target = sum(
        _sector_demand(sector)
        for sector in requirements.get("sectors", []) or []
        if str(_sector_value(sector, "area_kind", "INTERNAL")) != "EXTERNAL"
    )
    external_target = sum(
        _sector_demand(sector)
        for sector in requirements.get("sectors", []) or []
        if str(_sector_value(sector, "area_kind", "INTERNAL")) == "EXTERNAL"
    )
    program_gap = abs(float(accounting["internal_net_area_m2"]) - internal_target) + abs(
        float(accounting["external_area_m2"]) - external_target
    )
    program_score = round(
        max(0.0, 1.0 - program_gap / max(internal_target + external_target, 1.0)),
        12,
    )

    privacy_sequence = [
        {"id": sector_id, "privacy_level": _SECTOR_PRIVACY[sector_id]}
        for sector_id in ("SEC-01", "SEC-03", "SEC-04", "SEC-05", "SEC-06", "SEC-02")
        if any(str(room.get("sector_id")) == sector_id for room in rooms)
    ]
    privacy = evaluate_privacy_gradient(privacy_sequence)
    flow_analyses = flows["analyses"]
    circulation_score = sum(bool(item["ok"]) for item in flow_analyses.values()) / max(len(flow_analyses), 1)
    required_accessible = sum(
        int(_sector_value(space, "quantity", 1) or 1)
        for sector in requirements.get("sectors", []) or []
        for space in _sector_value(sector, "spaces", []) or []
        if _sector_value(space, "accessible") is True
    )
    accessible_rooms = sum(bool(room.get("accessible")) for room in rooms)
    accessibility_score = min(1.0, accessible_rooms / required_accessible) if required_accessible else 1.0
    footprint = unary_union([_polygon(block["geometry"]) for block in blocks])
    perimeter = float(footprint.length)
    compactness = max(0.0, min(1.0, 4.0 * math.pi * float(footprint.area) / max(perimeter * perimeter, 1e-9)))
    concept_fidelity = 1.0 if record.get("archetype_relationships") else 0.5
    raw_metrics: dict[str, float | None] = {
        "program_compliance": float(program_score),
        "privacy_security": float(privacy.score),
        "adjacency": float(adjacency["score"]),
        "circulation": float(circulation_score),
        "accessibility": float(accessibility_score),
        "solar_heuristic": None,
        "ventilation_heuristic": None,
        "green_integration": min(1.0, float(accounting["external_area_m2"]) / external_target) if external_target else 1.0,
        "compactness": float(compactness),
        "constructability": 1.0,
        "concept_fidelity": float(concept_fidelity),
    }
    score = score_candidate(raw_metrics)
    penalties: dict[str, float] = {}
    if privacy.penalty > 0:
        penalties["privacy_gradient"] = float(privacy.penalty)
    if adjacency["score"] < 1.0:
        penalties["adjacency_distance"] = float(1.0 - adjacency["score"])
    if circulation_score < 1.0:
        penalties["circulation"] = float(1.0 - circulation_score)
    if compactness < 1.0:
        penalties["compactness"] = float(1.0 - compactness)
    evidence = {
        "privacy": privacy.evidence,
        "circulation": flow_analyses,
        "accessibility": {
            "required_accessible_rooms": required_accessible,
            "generated_accessible_rooms": accessible_rooms,
        },
        "environment": {
            "status": "NOT_EVALUATED",
            "reason": "site.true_north is null; P08-T07 owns source-backed environmental heuristics",
        },
        "green_integration": {
            "required_external_area_m2": external_target,
            "generated_external_area_m2": float(accounting["external_area_m2"]),
        },
    }
    return raw_metrics, score, penalties, evidence


def _feature_collection(geometry: Mapping[str, Any]) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    features.append(
        {
            "type": "Feature",
            "properties": {"logical_id": "SITE-BOUNDARY", "kind": "site"},
            "geometry": _json_safe(geometry["site"]),
        }
    )
    for key, kind in (("macrozones", "macrozone"), ("blocks", "block"), ("rooms", "room"), ("external_spaces", "external_space")):
        for item in geometry.get(key, []) or []:
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "logical_id": str(item["logical_id"]),
                        "kind": kind,
                        "sector_id": item.get("sector_id"),
                    },
                    "geometry": _json_safe(item["geometry"]),
                }
            )
    return {"type": "FeatureCollection", "features": features}


def _render_svg(geometry: Mapping[str, Any], *, zoning: bool) -> str:
    site = _polygon(geometry["site"])
    min_x, min_y, max_x, max_y = site.bounds
    canvas_width, canvas_height, margin = 1200, 900, 30
    scale = min((canvas_width - 2 * margin) / max(max_x - min_x, 1e-9), (canvas_height - 2 * margin) / max(max_y - min_y, 1e-9))

    def point(x: float, y: float) -> str:
        return f"{margin + (x - min_x) * scale:.2f},{canvas_height - margin - (y - min_y) * scale:.2f}"

    def polygon_points(item: Mapping[str, Any]) -> str:
        polygon = _polygon(item["geometry"])
        return " ".join(point(float(x), float(y)) for x, y in polygon.exterior.coords)

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900">',
        '<rect width="1200" height="900" fill="#ffffff"/>',
        f'<text x="30" y="24" font-family="Arial" font-size="16" fill="#17202a">Amanda P08-T06 {"zoning" if zoning else "floorplan"} (STUDY)</text>',
        f'<polygon points="{polygon_points({"geometry": geometry["site"]})}" fill="#f3f4f6" stroke="#17202a" stroke-width="2"/>',
    ]
    if zoning:
        for index, item in enumerate(geometry.get("macrozones", []) or []):
            color = ("#dbeafe", "#dcfce7", "#fef3c7", "#fce7f3", "#ede9fe", "#ffedd5", "#cffafe")[index % 7]
            lines.append(f'<polygon points="{polygon_points(item)}" fill="{color}" fill-opacity="0.82" stroke="#64748b" stroke-width="1"/>')
            polygon = _polygon(item["geometry"])
            center = polygon.centroid
            lines.append(f'<text x="{margin + (center.x - min_x) * scale:.2f}" y="{canvas_height - margin - (center.y - min_y) * scale:.2f}" font-family="Arial" font-size="12" text-anchor="middle" fill="#17202a">{html.escape(str(item["logical_id"]))}</text>')
        items = geometry.get("external_spaces", []) or []
    else:
        items = geometry.get("blocks", []) or []
        items = list(items) + list(geometry.get("rooms", []) or [])
        items = list(items) + list(geometry.get("external_spaces", []) or [])
    for item in items:
        kind = "external" if item in (geometry.get("external_spaces", []) or []) else "block"
        fill = "#86efac" if kind == "external" else "#93c5fd"
        lines.append(f'<polygon points="{polygon_points(item)}" fill="{fill}" fill-opacity="0.7" stroke="#1e3a8a" stroke-width="1"/>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _render_png(geometry: Mapping[str, Any], *, zoning: bool) -> bytes:
    site = _polygon(geometry["site"])
    min_x, min_y, max_x, max_y = site.bounds
    width, height, margin = 1200, 900, 30
    scale = min((width - 2 * margin) / max(max_x - min_x, 1e-9), (height - 2 * margin) / max(max_y - min_y, 1e-9))

    def points(item: Mapping[str, Any]) -> list[tuple[int, int]]:
        polygon = _polygon(item["geometry"])
        return [
            (round(margin + (x - min_x) * scale), round(height - margin - (y - min_y) * scale))
            for x, y in polygon.exterior.coords
        ]

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.polygon(points({"geometry": geometry["site"]}), fill="#f3f4f6", outline="#17202a")
    if zoning:
        for index, item in enumerate(geometry.get("macrozones", []) or []):
            colors = ("#dbeafe", "#dcfce7", "#fef3c7", "#fce7f3", "#ede9fe", "#ffedd5", "#cffafe")
            draw.polygon(points(item), fill=colors[index % len(colors)], outline="#64748b")
        items = geometry.get("external_spaces", []) or []
    else:
        items = list(geometry.get("blocks", []) or [])
        items += list(geometry.get("rooms", []) or [])
        items += list(geometry.get("external_spaces", []) or [])
    for item in items:
        is_external = item in (geometry.get("external_spaces", []) or [])
        draw.polygon(points(item), fill="#86efac" if is_external else "#93c5fd", outline="#1e3a8a")
    with tempfile.SpooledTemporaryFile() as output:
        image.save(output, format="PNG")
        output.seek(0)
        return output.read()


def _constraint_payload(items: Sequence[Any]) -> list[dict[str, Any]]:
    return [_json_safe(item.model_dump(mode="python") if hasattr(item, "model_dump") else item) for item in items]


def _publish_finalist(
    finalist: Mapping[str, Any],
    finalist_id: str,
    run_payload: Mapping[str, Any],
    run_directory: Path,
    *,
    requirements_version: str,
    site_version: str,
    engine_version: str,
    weights_config: Mapping[str, Any],
    frozen_weights: Mapping[str, float],
) -> None:
    from .models import DesignSolution

    target = run_directory / "finalists" / finalist_id
    target.mkdir(parents=True, exist_ok=False)
    metrics_result = finalist["score"]
    raw_metrics = dict(finalist["metrics"])
    metric_payload = {
        "schema_version": 1,
        "solution_id": finalist_id,
        "raw_metrics": raw_metrics,
        "normalized_metrics": metrics_result.normalized_metrics,
        "contributions": metrics_result.contributions,
        "weighted_total": metrics_result.weighted_total,
        "rebalanced_weight_total": metrics_result.rebalanced_weight_total,
        "not_evaluated": metrics_result.not_evaluated,
        "weights_version": metrics_result.weights_version,
        "weights": dict(frozen_weights),
        "weight_config": weights_config,
        "evidence": finalist["metric_evidence"],
    }
    hard_violations = _constraint_payload(finalist["hard_checks"])
    penalties_payload = {
        "schema_version": 1,
        "solution_id": finalist_id,
        "hard_violations": hard_violations,
        "soft_penalties": dict(finalist["penalties"]),
        "block_checks": _constraint_payload(finalist["block_checks"]),
        "room_checks": _constraint_payload(finalist["room_checks"]),
        "external_checks": _constraint_payload(finalist["external_checks"]),
        "recheck_status": "PASS" if not hard_violations else "FAIL",
    }
    solution_payload = {
        "solution_id": finalist_id,
        "run_id": str(run_payload["run_id"]),
        "seed": int(finalist["record"].get("seed", 0)),
        "requirements_version": requirements_version,
        "site_version": site_version,
        "engine_version": engine_version,
        "archetype": str(finalist["record"].get("archetype", "UNKNOWN")),
        "geometry": _json_safe(finalist["geometry"]),
        "geometry_hash": str(finalist["geometry_hash"]),
        "metrics": {**raw_metrics, "overall_score": metrics_result.weighted_total, "evidence": ["raw dimensions and frozen weights are in metrics.json"]},
        "hard_violations": hard_violations,
        "soft_penalties": dict(finalist["penalties"]),
        "parents": [str(finalist["candidate_id"])],
        "status": "VALIDATED",
        "program_person_capacity": 20,
    }
    solution = DesignSolution.model_validate(solution_payload)
    solution_payload = solution.model_dump(mode="json")
    geometry_geojson = _feature_collection(finalist["geometry"])
    adjacency_payload = dict(finalist["adjacency"])
    flow_payload = dict(finalist["flows"])
    why_candidate = {
        "id": finalist_id,
        "solution_id": finalist_id,
        "metrics": raw_metrics,
        "soft_penalties": finalist["penalties"],
        "hard_violations": hard_violations,
        "provenance": {
            "source_principles": ["project/requirements/program.json", "project/site/site.json"],
            "hypotheses": ["P08-T04 institutional temporary shelter with controlled public interface", "P08-T04 planar site placeholder"],
            "refs": ["design-engine/config/weights.yaml", "AMANDA-RUN-001/run.json"],
        },
    }
    why = explanation_markdown(explain_candidate(why_candidate), solution_id=finalist_id)
    validation_payload = {
        "schema_version": 1,
        "solution_id": finalist_id,
        "resolution_checks": {
            "BLOCK": _constraint_payload(finalist["block_checks"]),
            "ROOM": _constraint_payload(finalist["room_checks"]),
            "EXTERNAL": _constraint_payload(finalist["external_checks"]),
        },
        "hard_violations": hard_violations,
        "status": "PASS" if not hard_violations else "FAIL",
    }
    artifacts = {
        "solution.json": solution_payload,
        "geometry.geojson": geometry_geojson,
        "adjacency-graph.json": adjacency_payload,
        "flow-graphs.json": flow_payload,
        "metrics.json": metric_payload,
        "penalties.json": penalties_payload,
        "validation.json": validation_payload,
    }
    for filename, payload in artifacts.items():
        _write_json(target / filename, payload)
    _write_text(target / "WHY_THIS_OPTION.md", why)
    _write_text(target / "floorplan.svg", _render_svg(finalist["geometry"], zoning=False))
    _write_bytes(target / "floorplan.png", _render_png(finalist["geometry"], zoning=False))
    _write_text(target / "zoning.svg", _render_svg(finalist["geometry"], zoning=True))
    _write_bytes(target / "zoning.png", _render_png(finalist["geometry"], zoning=True))
    artifact_names = [path.name for path in sorted(target.iterdir()) if path.is_file()]
    manifest = {
        "schema_version": 1,
        "solution_id": finalist_id,
        "files": {
            name: hashlib.sha256((target / name).read_bytes()).hexdigest()
            for name in artifact_names
        },
    }
    _write_json(target / "artifact-manifest.json", manifest)


def refine_run(
    root: Path,
    *,
    run_id: str,
    requirements: Mapping[str, Any],
    site: Mapping[str, Any],
    requirements_sha256: str,
    site_sha256: str,
) -> dict[str, Any]:
    """Refine the immutable macro run and publish up to five final candidates."""

    root = Path(root).resolve()
    run_directory = root / "design-engine" / "runs" / run_id
    run_path = run_directory / "run.json"
    run = _read_json(run_path, "canonical macro run")
    if str(run.get("run_id")) != run_id:
        raise RefinementInputError("macro run id does not match its directory")
    for key, expected in (("requirements_sha256", requirements_sha256), ("site_sha256", site_sha256)):
        if str(run.get(key)) != str(expected):
            raise RefinementInputError(f"macro run {key} does not match canonical input")
    if (run_directory / "finalists").exists():
        raise RefinementInputError(f"finalist artifacts already exist: {run_directory / 'finalists'}")

    run_counts = run.get("counts", {}) if isinstance(run.get("counts"), Mapping) else {}
    top_limit = min(15, len(run.get("ranking", []) or [])) or 15
    records = _candidate_records(run, top_limit)
    refined: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for record in records:
        try:
            candidate = _refine_candidate(record, requirements, site)
        except RefinementInputError as exc:
            candidate = {
                "candidate_id": _candidate_id(record),
                "record": dict(record),
                "rejected": True,
                "reason": str(exc),
                "rejection_codes": ["refinement_input"],
            }
        if candidate.get("rejected"):
            rejected.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "reason": candidate["reason"],
                    "codes": candidate.get("rejection_codes", []),
                }
            )
        else:
            refined.append(candidate)

    refined_records = [
        {
            "candidate_id": item["candidate_id"],
            "geometry_hash": item["geometry_hash"],
            "metrics": item["score"].normalized_metrics,
            "raw_metrics": item["metrics"],
            "weighted_total": item["score"].weighted_total,
            "soft_penalties": item["penalties"],
            "hard_violations": _constraint_payload(item["hard_checks"]),
        }
        for item in refined
    ]
    pareto_records = pareto_frontier(refined_records, dimensions=SCORE_DIMENSIONS)
    pareto_candidate_ids = [str(item["candidate_id"]) for item in pareto_records]
    ranked = sorted(
        refined,
        key=lambda item: (-float(item["score"].weighted_total), records.index(item["record"]), item["candidate_id"]),
    )
    by_candidate = {item["candidate_id"]: item for item in refined}
    selected: list[dict[str, Any]] = []
    selected_hashes: set[str] = set()
    for identifier in pareto_candidate_ids + [item["candidate_id"] for item in ranked]:
        candidate = by_candidate[identifier]
        if candidate["geometry_hash"] in selected_hashes:
            continue
        selected.append(candidate)
        selected_hashes.add(candidate["geometry_hash"])
        if len(selected) == 5:
            break
    finalist_ids = [f"{run_id}-F{index:02d}" for index in range(1, len(selected) + 1)]
    distinct_refined_count = len({str(item["geometry_hash"]) for item in refined})

    weights_path = root / "design-engine" / "config" / "weights.yaml"
    weights_config = load_weight_config(weights_path if weights_path.is_file() else None)
    frozen_weights = load_weights(weights_path if weights_path.is_file() else None)
    engine_version = str(run.get("engine_version", "design-engine-v1"))
    for candidate, finalist_id in zip(selected, finalist_ids):
        _publish_finalist(
            candidate,
            finalist_id,
            run,
            run_directory,
            requirements_version=_DEFAULT_REQUIREMENTS_VERSION,
            site_version=_DEFAULT_SITE_VERSION,
            engine_version=engine_version,
            weights_config=weights_config,
            frozen_weights=frozen_weights,
        )

    low_diversity_reason = (
        f"Only {distinct_refined_count} distinct refined feasible candidate(s) were available for up to 5 finalist slots "
        f"from {len(refined)} feasible refinement result(s); "
        f"the macro run reports {run_counts.get('duplicate', 0)} duplicate attempts and "
        "no additional distinct geometry was fabricated or obtained by relaxing hard constraints."
    )
    selection_reason = (
        f"Selected {len(selected)} distinct feasible finalist(s), with the complete refined Pareto set retained first. "
        + low_diversity_reason
        if len(selected) < 5
        else "Selected 5 distinct feasible finalist(s), retaining the complete refined Pareto set before weighted ordering."
    )
    summary = {
        "schema_version": 1,
        "stage": "P08-T06",
        "run_id": run_id,
        "run_json_sha256": hashlib.sha256(run_path.read_bytes()).hexdigest(),
        "considered_macro_candidates": len(records),
        "refined_candidates": len(records),
        "feasible_refined_candidates": len(refined),
        "rejected_after_refinement": len(rejected),
        "rejected": rejected,
        "pareto_frontier_candidate_ids": pareto_candidate_ids,
        "pareto_frontier_ids": [finalist_ids[pareto_candidate_ids.index(item["candidate_id"])] for item in pareto_records if item["candidate_id"] in pareto_candidate_ids and pareto_candidate_ids.index(item["candidate_id"]) < len(finalist_ids)],
        "finalist_ids": finalist_ids,
        "selection_limit": 5,
        "selection_reason": selection_reason,
        "low_diversity_limitation": low_diversity_reason,
        "weights_version": int(weights_config.get("version", 1)),
        "weights": dict(frozen_weights),
        "environmental_score_status": "NOT_EVALUATED; P08-T07 owns source-backed solar/ventilation heuristics",
        "requirements_sha256": requirements_sha256,
        "site_sha256": site_sha256,
    }
    _write_json(run_directory / "refinement-summary.json", summary)
    return {
        "run_id": run_id,
        "run_directory": run_directory,
        "considered_count": len(records),
        "refined_count": len(refined),
        "finalist_count": len(selected),
        "finalist_ids": finalist_ids,
        "pareto_frontier_ids": [
            finalist_ids[pareto_candidate_ids.index(identifier)]
            for identifier in pareto_candidate_ids
            if identifier in {candidate["candidate_id"] for candidate in selected}
        ],
        "rejected": rejected,
        "selection_reason": selection_reason,
    }


__all__ = ["SCORE_DIMENSIONS", "RefinementInputError", "refine_run"]
