"""Exact P6 readback reconciliation without rewriting historical acceptance."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

RECONCILIATION_PATH = Path(
    "revit/production/evidence/AMANDA-RUN-003-R04/"
    "p6-readback-fingerprint-reconciliation.json"
)
P6_EVIDENCE_PATH = Path(
    "revit/production/evidence/AMANDA-RUN-003-R04/r04-spatial-model-evidence.json"
)
_EXPECTED_CATEGORIES = {"Massa": 7, "Pisos": 14, "Telhados": 4}


class P6FingerprintReconciliationError(ValueError):
    """A P6 fingerprint addendum or exact readback does not match its evidence."""


class P6FingerprintReconciliation(BaseModel):
    """Additive, checkpoint-specific evidence for the current query projection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    status: Literal["RECONCILED_EXACT_READBACK_ONLY"]
    scope: Literal["RUN003_P6_CHECKPOINT_READBACK_IDENTITY"]
    checkpoint_path: str = Field(min_length=1)
    checkpoint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted_fingerprint: str = Field(min_length=1)
    observed_compact_fingerprint: str = Field(min_length=1)
    observed_detailed_fingerprint: str = Field(min_length=1)
    diagnostic_path: str = Field(min_length=1)
    diagnostic_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    rows_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    row_count: Literal[25]
    category_counts: dict[str, int]
    p6_acceptance_gate_passed: Literal[False]
    model_write_performed: Literal[False]
    root_cause: Literal["UNRESOLVED_QUERY_PROJECTION_OR_SERIALIZATION"]


def canonical_p6_rows(rows: object) -> list[dict]:
    """Select and sort the typed identity/geometry fields used by the digest."""

    if not isinstance(rows, list) or len(rows) != 25:
        raise P6FingerprintReconciliationError("P6 reconciliation requires exactly 25 rows")
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise P6FingerprintReconciliationError("P6 reconciliation row is not an object")
        element_id = row.get("element_id")
        unique_id = row.get("unique_id")
        category = row.get("category")
        name = row.get("name")
        box = row.get("bounding_box")
        if (
            not isinstance(element_id, int)
            or isinstance(element_id, bool)
            or not isinstance(unique_id, str)
            or not unique_id
            or not isinstance(category, str)
            or not isinstance(name, str)
            or not isinstance(box, dict)
        ):
            raise P6FingerprintReconciliationError("P6 reconciliation row identity is malformed")
        bounds = {}
        for bound in ("min", "max"):
            coordinates = box.get(bound)
            if not isinstance(coordinates, (list, tuple)) or len(coordinates) != 3:
                raise P6FingerprintReconciliationError("P6 reconciliation bounding box is malformed")
            try:
                values = [float(value) for value in coordinates]
            except (TypeError, ValueError) as exc:
                raise P6FingerprintReconciliationError(
                    "P6 reconciliation bounding box is not numeric"
                ) from exc
            if not all(math.isfinite(value) for value in values):
                raise P6FingerprintReconciliationError("P6 reconciliation bounding box is not finite")
            bounds[bound] = values
        result.append(
            {
                "element_id": element_id,
                "unique_id": unique_id,
                "category": category,
                "name": name,
                "bounding_box": bounds,
            }
        )
    result.sort(key=lambda item: item["element_id"])
    if len({row["element_id"] for row in result}) != 25:
        raise P6FingerprintReconciliationError("P6 reconciliation ElementIds are not unique")
    if len({row["unique_id"] for row in result}) != 25:
        raise P6FingerprintReconciliationError("P6 reconciliation UniqueIds are not unique")
    return result


def _digest_rows(rows: list[dict]) -> str:
    canonical = json.dumps(
        rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _contained_path(root: Path, relative: str, label: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise P6FingerprintReconciliationError(f"{label} is outside the repository") from exc
    return candidate


def _same_bounds(actual: object, expected: object) -> bool:
    if not isinstance(actual, dict) or not isinstance(expected, dict):
        return False
    for bound in ("min", "max"):
        left = actual.get(bound)
        right = expected.get(bound)
        if (
            not isinstance(left, (list, tuple))
            or not isinstance(right, (list, tuple))
            or len(left) != 3
            or len(right) != 3
            or any(
                not math.isclose(float(a), float(b), abs_tol=1e-6)
                for a, b in zip(left, right, strict=True)
            )
        ):
            return False
    return True


def _compare_compact_projection_to_detailed_rows(
    compact_payload: dict, detailed_rows: list[dict]
) -> None:
    compact_rows = compact_payload.get("rows")
    if not isinstance(compact_rows, list) or len(compact_rows) != 25:
        raise P6FingerprintReconciliationError(
            "compact/detailed row counts differ"
        )
    compact_by_id = {}
    for row in compact_rows:
        if not isinstance(row, dict):
            raise P6FingerprintReconciliationError(
                "compact/detailed row identity is malformed"
            )
        element_id = row.get("element_id")
        if (
            not isinstance(element_id, int)
            or isinstance(element_id, bool)
            or element_id in compact_by_id
        ):
            raise P6FingerprintReconciliationError(
                "compact/detailed row identities are missing or duplicated"
            )
        compact_by_id[element_id] = row
    detailed_by_id = {row["element_id"]: row for row in detailed_rows}
    if set(compact_by_id) != set(detailed_by_id):
        raise P6FingerprintReconciliationError(
            "compact/detailed row ElementIds differ"
        )
    for element_id, detailed in detailed_by_id.items():
        compact = compact_by_id[element_id]
        if not _same_bounds(compact.get("bounding_box"), detailed["bounding_box"]):
            raise P6FingerprintReconciliationError(
                f"compact/detailed row bounds differ for ElementId {element_id}"
            )
        for field in ("category", "name", "unique_id"):
            observed = compact.get(field)
            if observed is not None and observed != detailed[field]:
                raise P6FingerprintReconciliationError(
                    f"compact/detailed row {field} differs for ElementId {element_id}"
                )


def _validate_geometry_against_current_p6(
    root: Path, authorization, rows: list[dict]
) -> None:
    by_id = {row["element_id"]: row for row in rows}
    categories: dict[str, int] = {}
    for row in rows:
        categories[row["category"]] = categories.get(row["category"], 0) + 1
    if categories != _EXPECTED_CATEGORIES:
        raise P6FingerprintReconciliationError("P6 reconciliation category counts differ")

    mass_rows = {
        row["name"]: row
        for row in rows
        if row["category"] == "Massa" and row["name"].startswith("MASS-")
    }
    expected_mass_names = {f"MASS-{name}" for name in authorization.mass_bounding_boxes_m}
    if set(mass_rows) != expected_mass_names:
        raise P6FingerprintReconciliationError("P6 reconciliation mass identities differ")
    for component, expected in authorization.mass_bounding_boxes_m.items():
        if not _same_bounds(
            mass_rows[f"MASS-{component}"]["bounding_box"], expected
        ):
            raise P6FingerprintReconciliationError(
                f"P6 reconciliation mass geometry differs: {component}"
            )

    for element_id in authorization.administrative_floor_element_ids.values():
        row = by_id.get(element_id)
        if row is None or row["category"] != "Pisos":
            raise P6FingerprintReconciliationError(
                "P6 reconciliation administrative floor IDs differ"
            )

    try:
        evidence = json.loads((root / P6_EVIDENCE_PATH).read_text(encoding="utf-8"))
        readback = evidence["readback"]
        surface_data = readback["site_surfaces"]
        route_data = readback["access_routes"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise P6FingerprintReconciliationError(
            "current P6 spatial evidence is unavailable for readback reconciliation"
        ) from exc

    if evidence.get("p6_acceptance", {}).get("checkpoint_sha256") != authorization.checkpoint_sha256:
        raise P6FingerprintReconciliationError("current P6 evidence checkpoint SHA-256 differs")
    surfaces = surface_data.get("items")
    surface_bounds = surface_data.get("bounds_m")
    expected_surface_areas = {
        "SITE-PROTECTED-PATIO": 80,
        "SITE-THERAPEUTIC-GARDEN": 80,
        "SITE-HORTA": 30,
        "SITE-EXERCISE": 30,
        "SITE-PLAYGROUND": 40,
    }
    if (
        not isinstance(surfaces, list)
        or len(surfaces) != 5
        or not isinstance(surface_bounds, dict)
        or surface_data.get("official_program_total_m2") != 260
        or surface_data.get("official_program_internal_total_m2") != 626
        or surface_data.get("official_capacity_people") != 20
        or surface_data.get("area_authority") != "docs/source/programa_necessidades.pdf"
        or surface_data.get("board_printed_areas_used_as_official") is not False
    ):
        raise P6FingerprintReconciliationError("P6 site surface evidence is incomplete")
    if {
        item.get("mark"): item.get("area_m2")
        for item in surfaces
        if isinstance(item, dict)
    } != expected_surface_areas:
        raise P6FingerprintReconciliationError("P6 official external-area assignments differ")
    for surface in surfaces:
        element_id = surface.get("element_id")
        mark = surface.get("mark")
        row = by_id.get(element_id)
        if (
            row is None
            or row["category"] != "Pisos"
            or not isinstance(mark, str)
            or not _same_bounds(row["bounding_box"], surface_bounds.get(mark))
        ):
            raise P6FingerprintReconciliationError("P6 site surface geometry differs")

    route_bounds = route_data.get("bounds_m")
    if (
        not isinstance(route_bounds, dict)
        or len(route_bounds) != 3
        or set(route_data.get("marks", ()))
        != {"PATH-PUBLIC-ADMIN", "PATH-PUBLIC-SERVICE", "PATH-SERVICE-CARGO"}
        or route_data.get("public_and_cargo_separate") is not True
        or route_data.get("areas_excluded_from_official_program") is not True
    ):
        raise P6FingerprintReconciliationError("P6 access route evidence is incomplete")
    route_ids = set()
    for expected in route_bounds.values():
        match = next(
            (
                row["element_id"]
                for row in rows
                if row["category"] == "Pisos"
                and row["element_id"] not in route_ids
                and _same_bounds(row["bounding_box"], expected)
            ),
            None,
        )
        if match is None:
            raise P6FingerprintReconciliationError("P6 access route geometry differs")
        route_ids.add(match)

    connector_evidence = readback.get("covered_connectors", {})
    if (
        connector_evidence.get("floor_count") != 4
        or connector_evidence.get("roof_count") != 4
        or connector_evidence.get("enclosing_wall_count") != 0
        or connector_evidence.get("patio_intrusion_area_m2") != 0
    ):
        raise P6FingerprintReconciliationError("P6 covered connector evidence differs")
    surface_ids = {item["element_id"] for item in surfaces}
    admin_ids = set(authorization.administrative_floor_element_ids.values())
    connector_floors = [
        row
        for row in rows
        if row["category"] == "Pisos"
        and row["element_id"] not in surface_ids | admin_ids | route_ids
    ]
    connector_roofs = [row for row in rows if row["category"] == "Telhados"]
    if len(connector_floors) != 4 or len(connector_roofs) != 4:
        raise P6FingerprintReconciliationError("P6 covered connector counts differ")
    unmatched_roofs = {row["element_id"]: row for row in connector_roofs}
    for floor in connector_floors:
        floor_box = floor["bounding_box"]
        matching_roofs = []
        for roof_id, roof in unmatched_roofs.items():
            roof_box = roof["bounding_box"]
            same_plan = all(
                math.isclose(
                    floor_box[bound][index], roof_box[bound][index], abs_tol=1e-6
                )
                for bound in ("min", "max")
                for index in (0, 1)
            )
            correct_elevation = (
                math.isclose(floor_box["max"][2], 0.0, abs_tol=1e-6)
                and math.isclose(roof_box["min"][2], 2.9, abs_tol=1e-6)
                and math.isclose(roof_box["max"][2], 3.025, abs_tol=1e-6)
            )
            if same_plan and correct_elevation:
                matching_roofs.append(roof_id)
        if len(matching_roofs) != 1:
            raise P6FingerprintReconciliationError(
                "P6 covered connector floor does not match exactly one roof"
            )
        unmatched_roofs.pop(matching_roofs[0])
    if unmatched_roofs:
        raise P6FingerprintReconciliationError("P6 covered connector roofs are unmatched")


def load_p6_fingerprint_reconciliation(
    repository_root: Path,
    authorization,
    *,
    reconciliation_path: Path | None = None,
) -> P6FingerprintReconciliation:
    """Load the additive record and verify its exact checkpoint/diagnostic chain."""

    root = Path(repository_root).resolve()
    path = (
        Path(reconciliation_path).resolve()
        if reconciliation_path is not None
        else (root / RECONCILIATION_PATH).resolve()
    )
    try:
        path.relative_to(root)
        raw = path.read_bytes()
        data = json.loads(raw)
        record = P6FingerprintReconciliation.model_validate(data)
    except (OSError, ValueError, ValidationError) as exc:
        raise P6FingerprintReconciliationError(
            "P6 fingerprint reconciliation record is unavailable or malformed"
        ) from exc
    if record.checkpoint_path != authorization.checkpoint_path:
        raise P6FingerprintReconciliationError("reconciliation checkpoint path differs")
    if record.checkpoint_sha256 != authorization.checkpoint_sha256:
        raise P6FingerprintReconciliationError("reconciliation checkpoint SHA-256 differs")
    if record.accepted_fingerprint != authorization.p6_readback_fingerprint:
        raise P6FingerprintReconciliationError("reconciliation historical fingerprint differs")
    if (
        record.observed_compact_fingerprint == record.accepted_fingerprint
        or record.observed_detailed_fingerprint == record.accepted_fingerprint
    ):
        raise P6FingerprintReconciliationError("reconciliation does not preserve the fingerprint discrepancy")
    if record.category_counts != _EXPECTED_CATEGORIES:
        raise P6FingerprintReconciliationError("reconciliation category counts are malformed")

    diagnostic_path = _contained_path(root, record.diagnostic_path, "P6 diagnostic")
    try:
        diagnostic_raw = diagnostic_path.read_bytes()
        diagnostic = json.loads(diagnostic_raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise P6FingerprintReconciliationError("P6 fingerprint diagnostic is unavailable") from exc
    if hashlib.sha256(diagnostic_raw).hexdigest() != record.diagnostic_sha256:
        raise P6FingerprintReconciliationError("P6 diagnostic SHA-256 differs")
    if (
        not isinstance(diagnostic, dict)
        or diagnostic.get("status") != "DIAGNOSTIC_ONLY_FINGERPRINT_MISMATCH"
        or diagnostic.get("acceptance_gate_passed") is not False
        or diagnostic.get("model_write_performed") is not False
    ):
        raise P6FingerprintReconciliationError("P6 diagnostic status is not read-only")
    checkpoint = diagnostic.get("checkpoint")
    if (
        not isinstance(checkpoint, dict)
        or Path(checkpoint.get("path", "")).resolve()
        != (root / authorization.checkpoint_path).resolve()
        or checkpoint.get("sha256") != authorization.checkpoint_sha256
        or checkpoint.get("manifest_verified") is not True
        or checkpoint.get("opened_file_version") != "2027"
        or checkpoint.get("upgrade_allowed") is not False
    ):
        raise P6FingerprintReconciliationError("P6 diagnostic checkpoint binding differs")
    fingerprints = diagnostic.get("fingerprints")
    if (
        not isinstance(fingerprints, dict)
        or fingerprints.get("accepted") != record.accepted_fingerprint
        or fingerprints.get("observed_compact") != record.observed_compact_fingerprint
        or fingerprints.get("observed_detailed") != record.observed_detailed_fingerprint
    ):
        raise P6FingerprintReconciliationError("P6 diagnostic fingerprints differ")
    readback = diagnostic.get("readback")
    if (
        not isinstance(readback, dict)
        or readback.get("matched_total") != 25
        or readback.get("returned") != 25
        or readback.get("coverage_complete") is not True
        or readback.get("unreadable_total") != 0
        or readback.get("categories") != _EXPECTED_CATEGORIES
        or readback.get("detailed_categories") != _EXPECTED_CATEGORIES
        or readback.get("row_count") != record.row_count
    ):
        raise P6FingerprintReconciliationError("P6 diagnostic coverage or counts differ")
    rows = canonical_p6_rows(readback.get("rows"))
    digest = _digest_rows(rows)
    if digest != record.rows_sha256 or digest != readback.get("rows_sha256"):
        raise P6FingerprintReconciliationError("P6 diagnostic rows_sha256 differs")
    _validate_geometry_against_current_p6(root, authorization, rows)
    return record


def verify_reconciled_p6_readback(
    repository_root: Path,
    authorization,
    compact_payload: object,
    detailed_payload: object,
    *,
    record: P6FingerprintReconciliation | None = None,
) -> dict:
    """Accept only exact current query fingerprints and all 25 diagnostic rows."""

    if record is None:
        record = load_p6_fingerprint_reconciliation(repository_root, authorization)
    if record.checkpoint_path != authorization.checkpoint_path:
        raise P6FingerprintReconciliationError("reconciliation checkpoint path differs")
    if record.checkpoint_sha256 != authorization.checkpoint_sha256:
        raise P6FingerprintReconciliationError("reconciliation checkpoint SHA-256 differs")
    if record.accepted_fingerprint != authorization.p6_readback_fingerprint:
        raise P6FingerprintReconciliationError("reconciliation historical fingerprint differs")
    compact_fp = compact_payload.get("result_set_fingerprint") if isinstance(compact_payload, dict) else None
    detailed_fp = detailed_payload.get("result_set_fingerprint") if isinstance(detailed_payload, dict) else None
    if compact_fp != record.observed_compact_fingerprint:
        raise P6FingerprintReconciliationError("current compact fingerprint differs")
    if detailed_fp != record.observed_detailed_fingerprint:
        raise P6FingerprintReconciliationError("current detailed fingerprint differs")
    for label, payload in (("compact", compact_payload), ("detailed", detailed_payload)):
        if (
            not isinstance(payload, dict)
            or payload.get("matched_total") != 25
            or payload.get("returned") != 25
            or payload.get("coverage_complete") is not True
            or payload.get("unreadable_total") != 0
            or payload.get("summary", {}).get("by_category") != _EXPECTED_CATEGORIES
        ):
            raise P6FingerprintReconciliationError(f"current {label} readback coverage differs")
    detailed_rows = canonical_p6_rows(detailed_payload.get("rows"))
    if _digest_rows(detailed_rows) != record.rows_sha256:
        raise P6FingerprintReconciliationError("current readback rows_sha256 differs")
    _compare_compact_projection_to_detailed_rows(compact_payload, detailed_rows)
    _validate_geometry_against_current_p6(
        Path(repository_root).resolve(), authorization, detailed_rows
    )
    return {
        "status": record.status,
        "historical_accepted_fingerprint": record.accepted_fingerprint,
        "observed_compact_fingerprint": compact_fp,
        "observed_detailed_fingerprint": detailed_fp,
        "row_count": record.row_count,
        "rows_sha256": record.rows_sha256,
        "p6_acceptance_gate_passed": False,
        "model_write_performed": False,
    }
