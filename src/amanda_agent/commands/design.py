"""Create immutable-input design runs from the canonical project records."""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

import yaml

from ..design.geometry import validate_polygon
from ..design.archetypes import list_archetypes
from ..design.pipeline import PipelineResult, run_pipeline
from ..ingest.manifest import SourceManifest, sha256_file
from ..site.models import BoundaryPolygon, Topography
from .doctor import project_root

RUNS_ROOT = Path("design-engine") / "runs"
REQUIREMENTS_PATH = Path("project") / "requirements" / "program.json"
SITE_PATH = Path("project") / "site" / "site.json"
MANIFEST_PATH = Path("project") / "provenance" / "source-manifest.yaml"
ENGINE_VERSION = "design-engine-v1"
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
DEFAULT_SEEDS = list(range(24))


class DesignInputError(RuntimeError):
    """Raised when canonical inputs cannot be trusted for a design run."""


def validate_run_id(run_id: str) -> str:
    value = str(run_id).strip()
    if not RUN_ID_PATTERN.fullmatch(value):
        raise DesignInputError(
            "run id must contain only letters, numbers, '.', '_' or '-'"
        )
    return value


def _read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise DesignInputError(f"canonical {label} file is missing or mutable")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DesignInputError(f"canonical {label} state is invalid: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise DesignInputError(f"canonical {label} state must be an object")
    return dict(payload)


def _read_manifest(root: Path) -> SourceManifest:
    path = root / MANIFEST_PATH
    if not path.is_file() or path.is_symlink():
        raise DesignInputError("source state is invalid: source manifest is missing")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        manifest = SourceManifest.model_validate(payload)
    except (OSError, yaml.YAMLError, TypeError, ValueError) as exc:
        raise DesignInputError(
            "source state is invalid: source manifest cannot be trusted"
        ) from exc
    if manifest.schema_version != 1:
        raise DesignInputError("source state is invalid: manifest schema_version")
    return manifest


def _manifest_by_id(root: Path, manifest: SourceManifest) -> dict[str, Any]:
    docs_root = (root / "docs" / "source").resolve()
    if not docs_root.is_dir():
        raise DesignInputError("source state is invalid: docs/source is missing")
    if any(item.is_symlink() for item in docs_root.rglob("*")):
        raise DesignInputError("source state is invalid: docs/source contains a symlink")
    records: dict[str, Any] = {}
    manifest_paths: set[str] = set()
    for document in manifest.documents:
        candidate = root / document.immutable_path
        if candidate.is_symlink():
            raise DesignInputError(
                "source state is invalid: immutable source is mutable"
            )
        candidate = candidate.resolve()
        try:
            relative = candidate.relative_to(docs_root).as_posix()
        except ValueError as exc:
            raise DesignInputError(
                "source state is invalid: immutable source is outside docs/source"
            ) from exc
        if not candidate.is_file():
            raise DesignInputError(
                f"source state is invalid: immutable source is missing: {relative}"
            )
        if sha256_file(candidate) != document.sha256:
            raise DesignInputError(
                f"source state is invalid: hash mismatch for {document.filename}"
            )
        if document.source_id in records or relative in manifest_paths:
            raise DesignInputError("source state is invalid: duplicate manifest entry")
        records[document.source_id] = document
        manifest_paths.add(relative)

    actual_paths = {
        item.relative_to(docs_root).as_posix()
        for item in docs_root.rglob("*")
        if item.is_file()
    }
    if actual_paths != manifest_paths:
        raise DesignInputError(
            "source state is invalid: docs/source differs from the manifest"
        )
    return records


def _validate_program(
    program: Mapping[str, Any], manifest_by_id: Mapping[str, Any]
) -> None:
    if program.get("schema_version") != 1:
        raise DesignInputError("canonical requirements state is invalid: schema_version")
    baseline = program.get("baseline")
    if not isinstance(baseline, Mapping):
        raise DesignInputError("canonical requirements state is invalid: baseline")
    for key in ("source_id", "source_filename", "source_sha256", "person_capacity"):
        if key not in baseline:
            raise DesignInputError(
                f"canonical requirements state is invalid: baseline.{key}"
            )
    if (
        isinstance(baseline["person_capacity"], bool)
        or not isinstance(baseline["person_capacity"], int)
        or baseline["person_capacity"] < 1
    ):
        raise DesignInputError(
            "canonical requirements state is invalid: baseline.person_capacity"
        )
    source = manifest_by_id.get(str(baseline["source_id"]))
    if source is None or source.sha256 != str(baseline["source_sha256"]):
        raise DesignInputError(
            "source state is invalid: requirements baseline provenance diverges"
        )
    if source.filename != str(baseline["source_filename"]):
        raise DesignInputError(
            "source state is invalid: requirements baseline filename diverges"
        )
    sectors = program.get("sectors")
    if not isinstance(sectors, list) or not sectors:
        raise DesignInputError("canonical requirements state is invalid: sectors")
    logical_ids: set[str] = set()
    totals = program.get("totals")
    computed_totals = {"INTERNAL": 0.0, "EXTERNAL": 0.0}
    for sector in sectors:
        if not isinstance(sector, Mapping):
            raise DesignInputError("canonical requirements state is invalid: sector")
        sector_id = str(sector.get("logical_id", ""))
        if not sector_id or sector_id in logical_ids:
            raise DesignInputError(
                "canonical requirements state is invalid: duplicate sector id"
            )
        logical_ids.add(sector_id)
        area_kind = sector.get("area_kind")
        subtotal = sector.get("subtotal_m2")
        if (
            area_kind not in computed_totals
            or not isinstance(subtotal, (int, float))
            or isinstance(subtotal, bool)
            or not math.isfinite(float(subtotal))
            or float(subtotal) <= 0
        ):
            raise DesignInputError(
                f"canonical requirements state is invalid: sector {sector_id}"
            )
        spaces = sector.get("spaces")
        if not isinstance(spaces, list) or not spaces:
            raise DesignInputError(
                f"canonical requirements state is invalid: spaces for {sector_id}"
            )
        sector_total = 0.0
        for space in spaces:
            if not isinstance(space, Mapping):
                raise DesignInputError("canonical requirements state is invalid: space")
            quantity = space.get("quantity")
            area = space.get("target_area_m2")
            if (
                isinstance(quantity, bool)
                or not isinstance(quantity, int)
                or quantity < 1
                or not isinstance(area, (int, float))
                or isinstance(area, bool)
                or not math.isfinite(float(area))
                or area <= 0
            ):
                raise DesignInputError(
                    "canonical requirements state is invalid: space quantity/area"
                )
            space_id = str(space.get("logical_id", ""))
            if not space_id or space_id in logical_ids:
                raise DesignInputError(
                    "canonical requirements state is invalid: duplicate space id"
                )
            logical_ids.add(space_id)
            sector_total += int(quantity) * float(area)
        if not math.isclose(sector_total, float(subtotal), rel_tol=1e-9, abs_tol=1e-6):
            raise DesignInputError(
                f"canonical requirements state is invalid: subtotal for {sector_id}"
            )
        computed_totals[str(area_kind)] += sector_total
    if isinstance(totals, Mapping):
        for key, expected in (
            ("internal_useful_m2", computed_totals["INTERNAL"]),
            ("external_programmed_m2", computed_totals["EXTERNAL"]),
        ):
            value = totals.get(key)
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(float(value))
                or not math.isclose(float(value), expected, rel_tol=1e-9, abs_tol=1e-6)
            ):
                raise DesignInputError(
                    f"canonical requirements state is invalid: totals.{key}"
                )


def _validate_site(site: Mapping[str, Any], manifest_by_id: Mapping[str, Any]) -> None:
    if site.get("schema_version") != 1:
        raise DesignInputError("canonical site state is invalid: schema_version")
    boundary = site.get("boundary")
    if not isinstance(boundary, Mapping):
        raise DesignInputError("canonical site state is invalid: boundary")
    coordinates = boundary.get("coordinates")
    try:
        validate_polygon(coordinates)
        BoundaryPolygon.model_validate(
            {
                key: boundary[key]
                for key in ("coordinates", "kind", "placeholder_area_m2", "source_ref")
                if key in boundary
            }
        )
    except (TypeError, ValueError, KeyError) as exc:
        raise DesignInputError("canonical site state is invalid: boundary") from exc
    provenance = site.get("provenance")
    if not isinstance(provenance, list) or not provenance:
        raise DesignInputError("canonical site state is invalid: provenance")
    for reference in provenance:
        if not isinstance(reference, Mapping):
            raise DesignInputError("canonical site state is invalid: provenance entry")
        source = manifest_by_id.get(str(reference.get("source_id", "")))
        if source is None or source.sha256 != str(reference.get("sha256", "")):
            raise DesignInputError("source state is invalid: site provenance diverges")
    topography = site.get("topography")
    if not isinstance(topography, Mapping):
        raise DesignInputError("canonical site state is invalid: topography")
    if topography.get("source_state") not in {"MISSING", "VERIFIED_TOPOGRAPHY"}:
        raise DesignInputError("canonical site state is invalid: topography state")
    try:
        Topography.model_validate(dict(topography))
    except (TypeError, ValueError) as exc:
        raise DesignInputError("canonical site state is invalid: topography") from exc


def load_canonical_inputs(root: Path) -> dict[str, Any]:
    """Read and validate the canonical JSON inputs and immutable source store."""

    root = Path(root).resolve()
    manifest = _read_manifest(root)
    manifest_by_id = _manifest_by_id(root, manifest)
    requirements_path = root / REQUIREMENTS_PATH
    site_path = root / SITE_PATH
    requirements = _read_json(requirements_path, "requirements")
    site = _read_json(site_path, "site")
    _validate_program(requirements, manifest_by_id)
    _validate_site(site, manifest_by_id)
    return {
        "requirements": requirements,
        "site": site,
        "requirements_path": REQUIREMENTS_PATH.as_posix(),
        "site_path": SITE_PATH.as_posix(),
        "requirements_sha256": sha256_file(requirements_path),
        "site_sha256": sha256_file(site_path),
    }


def _json_safe(value: Any) -> Any:
    if hasattr(value, "__geo_interface__"):
        return _json_safe(value.__geo_interface__)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_safe(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "value") and isinstance(value.value, (str, int, float)):
        return value.value
    return str(value)


def _finalist_records(result: PipelineResult, run_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, finalist in enumerate(result.stages.get("finalists", []), start=1):
        values = _json_safe(finalist)
        if not isinstance(values, dict):
            values = {"candidate": values}
        candidate = values.pop("candidate", None)
        if isinstance(candidate, Mapping):
            record = dict(candidate)
            record.update({key: values[key] for key in ("blocks", "rooms", "accounting") if key in values})
        else:
            record = values
        record["finalist_id"] = f"{run_id}-F{index:02d}"
        record["run_id"] = run_id
        records.append(record)
    return records


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _assert_inputs_unchanged(root: Path, inputs: Mapping[str, Any]) -> None:
    """Refuse publication if a canonical JSON changed while the run executed."""

    try:
        current_requirements_hash = sha256_file(Path(root) / REQUIREMENTS_PATH)
        current_site_hash = sha256_file(Path(root) / SITE_PATH)
    except OSError as exc:
        raise DesignInputError("source state changed during design run") from exc
    if (
        current_requirements_hash != inputs["requirements_sha256"]
        or current_site_hash != inputs["site_sha256"]
    ):
        raise DesignInputError("source state changed during design run")


def run_design(root: Path, *, run_id: str) -> dict[str, Any]:
    """Validate canonical state, execute the deterministic pipeline and persist a run."""

    safe_run_id = validate_run_id(run_id)
    inputs = load_canonical_inputs(Path(root))
    run_directory = Path(root).resolve() / RUNS_ROOT / safe_run_id
    if run_directory.exists():
        raise DesignInputError(f"design run already exists: {safe_run_id}")

    site_for_engine = dict(inputs["site"])
    boundary = site_for_engine.get("boundary")
    if isinstance(boundary, Mapping):
        site_for_engine.pop("buildable_area", None)
        site_for_engine["boundary"] = boundary.get("coordinates")

    configured_archetypes = list(list_archetypes())
    settings = {
        "macro_candidates": len(DEFAULT_SEEDS) * len(configured_archetypes),
        "top_macro": min(15, len(DEFAULT_SEEDS)),
        "top_rooms": min(5, len(DEFAULT_SEEDS)),
        "top_finalists": 3,
    }
    try:
        pipeline = run_pipeline(
            inputs["requirements"],
            site_for_engine,
            seeds=list(DEFAULT_SEEDS),
            config=settings,
            archetypes=configured_archetypes,
            input_versions={
                "requirements_sha256": inputs["requirements_sha256"],
                "site_sha256": inputs["site_sha256"],
            },
        )
    except (TypeError, ValueError, KeyError, IndexError, RuntimeError) as exc:
        raise DesignInputError(f"design pipeline refused canonical inputs: {exc}") from exc

    _assert_inputs_unchanged(Path(root), inputs)
    finalists = _finalist_records(pipeline, safe_run_id)
    run_counts = dict(pipeline.counts)
    run_counts.update(
        {
            "macro": len(pipeline.stages.get("macro", [])),
            "top_macro": len(pipeline.stages.get("top_macro", [])),
            "rooms": len(pipeline.stages.get("rooms", [])),
            "finalists": len(finalists),
            "initial_attempts": len(pipeline.attempts),
            "valid": sum(item["outcome"] == "valid" for item in pipeline.attempts),
            "invalid": sum(item["outcome"] == "invalid" for item in pipeline.attempts),
            "unknown": sum(item["outcome"] == "unknown" for item in pipeline.attempts),
            "duplicate": sum(item["outcome"] == "duplicate" for item in pipeline.attempts),
            "hard_invalid_ranked": sum(item["hard_invalid"] for item in pipeline.ranking),
        }
    )
    run_payload = {
        "schema_version": 1,
        "run_id": safe_run_id,
        "engine_version": ENGINE_VERSION,
        "source_state": "VALID",
        "requirements_path": inputs["requirements_path"],
        "site_path": inputs["site_path"],
        "requirements_sha256": inputs["requirements_sha256"],
        "site_sha256": inputs["site_sha256"],
        "seeds": list(DEFAULT_SEEDS),
        "archetypes": [str(item.value) for item in configured_archetypes],
        "counts": _json_safe(run_counts),
        "stage_order": list(pipeline.stage_order),
        "revit_calls": pipeline.revit_calls,
        "inputs": {
            "requirements": inputs["requirements"],
            "site": inputs["site"],
        },
        "attempts": _json_safe(pipeline.attempts),
        "hard_rejections_by_rule": _json_safe(pipeline.hard_rejections_by_rule),
        "ranking": _json_safe(pipeline.ranking),
        "pareto_frontier": _json_safe(pipeline.pareto_frontier),
        "pareto_frontier_ids": list(pipeline.pareto_frontier_ids),
        "finalists": finalists,
        "rejected": _json_safe(pipeline.rejected),
    }
    run_directory.mkdir(parents=True, exist_ok=False)
    _write_json(run_directory / "run.json", run_payload)
    return {
        "run_id": safe_run_id,
        "run_directory": run_directory,
        "finalist_count": len(finalists),
        "candidate_count": len(pipeline.attempts),
    }


def design_command(run_id: str, root: Path | None = None) -> dict[str, Any]:
    return run_design(root or project_root(), run_id=run_id)


__all__ = [
    "ENGINE_VERSION",
    "RUNS_ROOT",
    "DesignInputError",
    "design_command",
    "load_canonical_inputs",
    "run_design",
    "validate_run_id",
]
