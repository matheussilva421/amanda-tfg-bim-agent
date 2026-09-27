"""Verified, narrowly scoped authorization to continue RUN-003 after P6.

The canonical identity remains BIM-ineligible. This module validates the saved
P6 evidence, current four-board/program sources, and checkpoint. DEC-010 bounds
the future normalized-STUDY sequence to R05-R13; the current P7-T01 runtime
grant exposes only R05, with later stages gated by their own task.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError

from amanda_agent.bim.checkpoints import CheckpointManifest
from amanda_agent.design.models import DesignSolution
from amanda_agent.production.canonical_identity import (
    CanonicalIdentityError,
    load_canonical_solution_identity,
)
from amanda_agent.production.selection import Selection
from amanda_agent.requirements.decisions import DecisionRecord

RUN003_SOLUTION_ID = "AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"
P6_EVIDENCE_PATH = Path(
    "revit/production/evidence/AMANDA-RUN-003-R04/r04-spatial-model-evidence.json"
)
P6_REPORT_PATH = Path("docs/reports/P6-T01-run003-visual-geometric-acceptance.md")
RUN003_TARGET_PATH = Path(
    "revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt"
)
DECISIONS_PATH = Path("docs/decisions/DECISIONS.md")
TASK_GRAPH_PATH = Path("state/task-graph.yaml")
RUN003_SELECTION_DIR = Path(
    "design-engine/runs/AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C-study-detail-004"
)
_REQUIRED_RELATIONS = (
    "administration_south_public_edge",
    "administration_two_levels",
    "residences_north_interior_four_independent_pavilions",
    "protected_residential_patio_free",
    "covered_external_semiopen_circulation",
    "services_southeast_curved_with_courtyard",
    "child_west_near_playground",
    "therapeutic_garden_central",
    "horta_east",
    "public_and_cargo_access_separate",
    "administrative_floor_levels_aligned",
    "administration_public_route_meets_south_entry",
)
_EXPECTED_MASSES = frozenset(
    {
        "ADMIN_ACOLHIMENTO",
        "CHILD_SECTOR",
        "RES_PAV_A",
        "RES_PAV_B",
        "RES_PAV_C",
        "RES_PAV_D_COMMUNAL",
        "SERVICE_CAPACITATION",
    }
)


class Run003StudyAuthorizationError(ValueError):
    """Current P6 evidence cannot authorize RUN-003 study continuation."""


class Run003StudyAuthorization(BaseModel):
    """P6-bound continuation evidence with the current P7-T01 gate scoped to R05."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["VERIFIED_P6_STUDY_CONTINUATION"]
    solution_id: Literal["AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"]
    start_stage: Literal["R05"]
    max_stage: Literal["R13"]
    scenario: Literal["STUDY"]
    bim_eligible: Literal[False]
    identity_bim_eligible: Literal[False]
    identity_revit_write_authorized: Literal[False]
    canonical_board_sha256: tuple[str, str, str, str]
    official_program_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    approval_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    layout_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    checkpoint_path: str = Field(min_length=1)
    checkpoint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_path: str = Field(min_length=1)
    p6_readback_fingerprint: str = Field(min_length=1)
    mass_bounding_boxes_m: dict[str, dict[str, tuple[float, float, float]]]
    mass_vertical_bounds_m: dict[str, tuple[float, float]]
    administrative_floor_element_ids: dict[str, int]
    administrative_storey_elevations_m: dict[int, float]
    storey_element_ids: dict[int, int]

    def permits_stage(self, stage: object) -> bool:
        """Expose only this task's stage; later stages need their own task gate."""

        name = getattr(stage, "name", stage)
        return name == "R05"

    def permits_target(self, solution_id: str) -> bool:
        return solution_id == self.solution_id

    def permits_target_path(self, target_path: str | Path) -> bool:
        candidate = Path(target_path).resolve()
        expected = (Path(__file__).resolve().parents[3] / self.target_path).resolve()
        return candidate == expected

    def wall_elevations_m(
        self, component_id: str, levels: tuple[int, ...]
    ) -> tuple[tuple[int, float, float], ...]:
        """Derive each floor's wall base/top exclusively from the P6 readback."""

        bounds = self.mass_vertical_bounds_m.get(component_id)
        if bounds is None or not levels:
            raise Run003StudyAuthorizationError(
                f"P6 readback has no vertical envelope for {component_id}"
            )
        base, envelope_top = bounds
        ordered = tuple(sorted(set(levels)))
        if ordered != levels:
            raise Run003StudyAuthorizationError(
                f"layout levels for {component_id} must be unique and ascending"
            )

        result: list[tuple[int, float, float]] = []
        for index, level in enumerate(ordered):
            if component_id == "ADMIN_ACOLHIMENTO":
                floor_elevation = self.administrative_storey_elevations_m.get(level)
                if floor_elevation is None:
                    raise Run003StudyAuthorizationError(
                        f"P6 readback has no administrative datum for level {level}"
                    )
            elif index == 0:
                floor_elevation = base
            else:
                raise Run003StudyAuthorizationError(
                    f"P6 readback does not establish upper floors for {component_id}"
                )
            top = (
                self.administrative_storey_elevations_m[ordered[index + 1]]
                if component_id == "ADMIN_ACOLHIMENTO" and index + 1 < len(ordered)
                else envelope_top
            )
            if not math.isfinite(floor_elevation) or not math.isfinite(top) or top <= floor_elevation:
                raise Run003StudyAuthorizationError(
                    f"P6 readback has an invalid wall height for {component_id} level {level}"
                )
            result.append((level - 1, floor_elevation, top))
        return tuple(result)


def _read_repository_bytes(
    path: Path, label: str, *, repository_root: Path | None = None
) -> bytes:
    path = Path(path)
    try:
        return path.read_bytes()
    except PermissionError as exc:
        if repository_root is None:
            raise Run003StudyAuthorizationError(
                f"cannot read {label}: {path}"
            ) from exc
        root = Path(repository_root).resolve()
        try:
            relative_path = path.resolve().relative_to(root).as_posix()
        except (OSError, ValueError) as path_error:
            raise Run003StudyAuthorizationError(
                f"cannot read {label}: {path}"
            ) from path_error
        try:
            result = subprocess.run(
                ["git", "show", f"HEAD:{relative_path}"],
                cwd=root,
                capture_output=True,
                check=False,
            )
        except OSError as git_error:
            raise Run003StudyAuthorizationError(
                f"cannot read committed {label}: {relative_path}"
            ) from git_error
        if result.returncode != 0:
            raise Run003StudyAuthorizationError(
                f"cannot read committed {label}: {relative_path}"
            ) from exc
        return result.stdout
    except OSError as exc:
        raise Run003StudyAuthorizationError(f"cannot read {label}: {path}") from exc


def _read_json(
    path: Path, label: str, *, repository_root: Path | None = None
) -> dict:
    try:
        content = _read_repository_bytes(
            path, label, repository_root=repository_root
        ).decode("utf-8")
        value = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Run003StudyAuthorizationError(f"cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise Run003StudyAuthorizationError(f"{label} must be a JSON object")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Run003StudyAuthorizationError(message)


def load_run003_study_authorization(
    repository_root: Path, *, evidence_path: Path | None = None
) -> Run003StudyAuthorization:
    """Verify P6 and current sources before granting the bounded study stages."""

    root = Path(repository_root).resolve()
    path = Path(evidence_path) if evidence_path is not None else root / P6_EVIDENCE_PATH
    evidence = _read_json(path, "P6 spatial evidence", repository_root=root)
    try:
        identity = load_canonical_solution_identity(root)
    except (CanonicalIdentityError, OSError, ValueError) as exc:
        raise Run003StudyAuthorizationError(
            "current canonical identity or source bindings are invalid"
        ) from exc

    _require(identity.solution_id == RUN003_SOLUTION_ID, "solution ID is not RUN-003")
    _require(identity.bim_eligible is False, "canonical identity must remain BIM-ineligible")
    _require(identity.revit_write_authorized is False, "identity write authorization must remain false")
    _require(evidence.get("run") == "RUN-003", "P6 evidence is not RUN-003")
    _require(evidence.get("stage") == "R04", "P6 evidence is not bound to R04")
    _require(evidence.get("write", {}).get("r05_performed") is False, "R05 must not predate P6")
    approval_hash = evidence.get("source", {}).get("approval_hash")
    _require(
        isinstance(approval_hash, str)
        and len(approval_hash) == 64
        and all(character in "0123456789abcdef" for character in approval_hash),
        "P6 selection approval hash is invalid",
    )
    _require(
        isinstance(evidence.get("source", {}).get("layout_hash"), str)
        and len(evidence["source"]["layout_hash"]) == 64,
        "P6 layout hash is invalid",
    )

    p6 = evidence.get("p6_acceptance")
    _require(isinstance(p6, dict), "P6 acceptance receipt is missing")
    _require(p6.get("status") == "PASS", "P6 status must be PASS")
    _require(p6.get("gate") == "CANON-011", "P6 gate must be CANON-011")
    _require(
        p6.get("scope") == "NORMALIZED_STUDY_SPATIAL_TOPOLOGY",
        "P6 scope is not normalized-study spatial topology",
    )
    _require(p6.get("solution_id") == identity.solution_id, "P6 solution ID differs from current identity")
    _require(p6.get("rooms_deferred_to") == "R06", "P6 must defer internal layout to R06")
    _require(p6.get("room_area_readback_deferred_to") == "R08", "P6 room area readback must be deferred to R08")
    _require(
        p6.get("authorization_basis")
        == "DEC-010_USER_DIRECTED_CONDITIONAL_R05_R13_AFTER_P6_PASS",
        "DEC-010 authorization basis is missing or mismatched",
    )
    _require(
        evidence.get("independent_review", {}).get("status")
        == "SUPERSEDED_BY_SCOPED_P6_ACCEPTANCE",
        "historical review conclusion is not marked superseded",
    )
    _require(
        p6.get("independent_review", {}).get("status")
        == "PASS_NORMALIZED_STUDY_TOPOLOGY",
        "current independent P6 review is missing",
    )

    expected_board_hashes = tuple(item.sha256 for item in identity.canonical_boards)
    _require(
        tuple(p6.get("canonical_board_sha256", ())) == expected_board_hashes,
        "P6 canonical board hashes do not match the current four boards",
    )
    _require(
        tuple(p6.get("canonical_board_order", ()))
        == tuple(Path(item.path).name for item in identity.canonical_boards),
        "P6 canonical board order does not match the current four boards",
    )
    _require(
        p6.get("official_program_sha256") == identity.program_source.sha256,
        "P6 official program PDF hash does not match the current identity",
    )
    _require(evidence.get("source", {}).get("canonical_board_sha256") == list(expected_board_hashes), "source record board hashes differ from identity")
    _require(
        evidence.get("source", {}).get("official_program_sha256")
        == identity.program_source.sha256,
        "source record program hash differs from identity",
    )
    _require(evidence.get("source", {}).get("s02_status") == "STALE_BY_CANONICAL_REFERENCE_EXPANSION", "S02 must remain stale")
    _require(evidence.get("source", {}).get("s02_lease_reclaimed") is False, "S02 lease must not be reused")

    relations = p6.get("canonical_relations")
    _require(isinstance(relations, dict), "P6 canonical relation checks are missing")
    _require(all(relations.get(key) is True for key in _REQUIRED_RELATIONS), "one or more required P6 spatial relations are not PASS")
    _require(p6.get("site_claims_status") == "LIMITED_TO_SURVEYED_DATA", "site claims must remain limited")

    persistence = evidence.get("persistence", {})
    checkpoint_rel = persistence.get("checkpoint_path")
    manifest_rel = persistence.get("checkpoint_manifest_path")
    checkpoint_sha = p6.get("checkpoint_sha256")
    _require(
        checkpoint_rel == "revit/production/evidence/AMANDA-RUN-003-R04/P6-T01-CANON-011-RECONCILED-20260926.rvt",
        "P6 checkpoint path is not the accepted RUN-003 checkpoint",
    )
    _require(checkpoint_sha == persistence.get("checkpoint_sha256") == persistence.get("model_sha256"), "P6 checkpoint hashes disagree")
    checkpoint = root / checkpoint_rel
    manifest_path = root / manifest_rel
    try:
        manifest = CheckpointManifest.load(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise Run003StudyAuthorizationError("P6 checkpoint manifest cannot be loaded") from exc
    _require(manifest.checkpoint_path.resolve() == checkpoint.resolve(), "P6 manifest points to another checkpoint")
    _require(manifest.sha256 == checkpoint_sha, "P6 checkpoint manifest hash differs")
    _require(manifest.verify(), "P6 checkpoint bytes do not verify")
    _require(
        evidence.get("persistence", {}).get("checkpoint_manager_verify_checkpoint") is True,
        "P6 CheckpointManager verification is missing",
    )

    readback = evidence.get("readback", {})
    _require(readback.get("phase") == "POST_P6_SAVE_COLD_REOPEN", "P6 readback is not post-reopen")
    _require(readback.get("coverage_complete") is True, "P6 typed readback is incomplete")
    _require(readback.get("unreadable_total") == 0, "P6 typed readback has unreadable elements")
    _require(readback.get("post_reopen_object_count") == p6.get("r04_readback_count") == 25, "P6 readback count is not the accepted 25 elements")
    _require(readback.get("result_set_fingerprint") == p6.get("r04_readback_fingerprint"), "P6 readback fingerprint differs")
    mass_bounds = readback.get("mass_bboxes_m", {})
    _require(set(name.removeprefix("MASS-") for name in mass_bounds) == _EXPECTED_MASSES, "P6 mass vertical readback is incomplete")

    vertical: dict[str, tuple[float, float]] = {}
    mass_boxes: dict[str, dict[str, tuple[float, float, float]]] = {}
    for name, bounds in mass_bounds.items():
        try:
            minimum = tuple(float(value) for value in bounds["min"])
            maximum = tuple(float(value) for value in bounds["max"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise Run003StudyAuthorizationError(f"P6 vertical bounds are invalid for {name}") from exc
        _require(len(minimum) == 3 and len(maximum) == 3, f"P6 bounds are invalid for {name}")
        _require(
            all(math.isfinite(value) for value in (*minimum, *maximum))
            and all(high > low for low, high in zip(minimum, maximum, strict=True)),
            f"P6 bounding box is invalid for {name}",
        )
        bottom, top = minimum[2], maximum[2]
        _require(math.isfinite(bottom) and math.isfinite(top) and top > bottom, f"P6 vertical envelope is invalid for {name}")
        component = name.removeprefix("MASS-")
        vertical[component] = (bottom, top)
        mass_boxes[component] = {"min": minimum, "max": maximum}

    storeys = readback.get("administrative_storey_levels", {})
    try:
        admin_levels = {
            int(level): float(value["elevation_m"])
            for level, value in storeys.items()
        }
        storey_element_ids = {
            int(level): int(value["level_id"])
            for level, value in storeys.items()
        }
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise Run003StudyAuthorizationError("P6 administrative storey levels are invalid") from exc
    _require(admin_levels == {1: 0.0, 2: 4.0}, "P6 admin level datums do not match the accepted readback")
    _require(
        set(storey_element_ids) == {1, 2}
        and len(set(storey_element_ids.values())) == 2
        and all(value > 0 for value in storey_element_ids.values()),
        "P6 level IDs are missing or duplicated",
    )
    _require(
        storey_element_ids
        == {
            1: int(
                evidence["write"]["p6_administration_reconciliation"]
                ["replacement_elements"]["floors"][0]["level_id"]
            ),
            2: int(
                evidence["write"]["p6_administration_reconciliation"]
                ["replacement_elements"]["floors"][1]["level_id"]
            ),
        },
        "P6 level IDs do not match the independently recorded floor references",
    )
    try:
        admin_floor_ids = {
            str(mark): int(element_id)
            for mark, element_id in readback["administrative_floor_element_ids"].items()
        }
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise Run003StudyAuthorizationError("P6 administrative floor IDs are invalid") from exc
    expected_admin_floor_ids = {
        str(floor["mark"]): int(floor["id"])
        for floor in evidence["write"]["p6_administration_reconciliation"]
        ["replacement_elements"]["floors"]
    }
    _require(
        admin_floor_ids == expected_admin_floor_ids
        and set(admin_floor_ids) == {"R04-ADMIN-FLOOR-L1", "R04-ADMIN-FLOOR-L2"}
        and all(element_id > 0 for element_id in admin_floor_ids.values()),
        "P6 admin floor IDs do not match the independent typed write record",
    )
    target = root / RUN003_TARGET_PATH
    _require(target.is_file(), "the exact RUN-003 working target is missing")

    try:
        task_graph = yaml.safe_load((root / TASK_GRAPH_PATH).read_text(encoding="utf-8"))
        p6_task_status = task_graph["tasks"]["P6-T01"]["status"]
        decisions = (root / DECISIONS_PATH).read_text(encoding="utf-8")
        report = (root / P6_REPORT_PATH).read_text(encoding="utf-8")
    except (OSError, yaml.YAMLError, KeyError, TypeError) as exc:
        raise Run003StudyAuthorizationError("current P6 task/decision/report records are unavailable") from exc
    _require(p6_task_status == "PASS", "task graph P6-T01 must be PASS")
    _require("## DEC-010 — RUN-003 detailed STUDY continuation after P6" in decisions, "DEC-010 is not active in the current decision record")
    _require("without asking for confirmation between green stage gates" in decisions, "DEC-010 does not authorize the bounded sequence")
    _require("**Status:** `PASS`" in report, "current P6 report is not PASS")

    try:
        return Run003StudyAuthorization(
            status="VERIFIED_P6_STUDY_CONTINUATION",
            solution_id=identity.solution_id,
            start_stage="R05",
            max_stage="R13",
            scenario="STUDY",
            bim_eligible=False,
            identity_bim_eligible=identity.bim_eligible,
            identity_revit_write_authorized=identity.revit_write_authorized,
            canonical_board_sha256=expected_board_hashes,
            official_program_sha256=identity.program_source.sha256,
            approval_hash=evidence["source"]["approval_hash"],
            layout_hash=evidence["source"]["layout_hash"],
            checkpoint_path=checkpoint_rel,
            checkpoint_sha256=checkpoint_sha,
            target_path=RUN003_TARGET_PATH.as_posix(),
            p6_readback_fingerprint=readback["result_set_fingerprint"],
            mass_bounding_boxes_m=mass_boxes,
            mass_vertical_bounds_m=vertical,
            administrative_floor_element_ids=admin_floor_ids,
            administrative_storey_elevations_m=admin_levels,
            storey_element_ids=storey_element_ids,
        )
    except (KeyError, ValueError) as exc:
        raise Run003StudyAuthorizationError("verified P6 study authorization is invalid") from exc


def load_run003_study_selection(
    repository_root: Path,
    authorization: Run003StudyAuthorization,
) -> Selection:
    """Load the persisted P6-bound selection instead of regenerating its hash."""

    root = Path(repository_root).resolve()
    try:
        identity = load_canonical_solution_identity(root)
    except (CanonicalIdentityError, OSError, ValueError) as exc:
        raise Run003StudyAuthorizationError(
            "current canonical identity cannot validate the persisted selection"
        ) from exc

    run_dir = root / RUN003_SELECTION_DIR
    manifest = _read_json(
        run_dir / "artifact-manifest.json",
        "RUN-003 artifact manifest",
        repository_root=root,
    )
    selection_path = run_dir / "selection.json"
    solution_path = (
        run_dir / "finalists" / authorization.solution_id / "solution.json"
    )
    selection_data = _read_json(
        selection_path, "RUN-003 persisted selection", repository_root=root
    )
    solution_data = _read_json(
        solution_path, "RUN-003 persisted solution", repository_root=root
    )

    _require(
        identity.solution_id == authorization.solution_id,
        "persisted selection and P6 authorization solution IDs differ",
    )
    _require(
        manifest.get("identity_fingerprint") == identity.identity_fingerprint,
        "RUN-003 artifact manifest identity fingerprint is stale",
    )
    _require(
        manifest.get("canonical_source_hashes")
        == [item.sha256 for item in identity.canonical_boards],
        "RUN-003 artifact manifest does not bind the current four boards",
    )
    _require(
        manifest.get("program_source_sha256") == identity.program_source.sha256,
        "RUN-003 artifact manifest does not bind the official program PDF",
    )
    _require(
        manifest.get("approval_hash") == authorization.approval_hash
        and manifest.get("layout_hash") == authorization.layout_hash,
        "RUN-003 artifact manifest differs from the P6-bound approval or layout",
    )
    _require(
        selection_data.get("identity_fingerprint") == identity.identity_fingerprint
        and selection_data.get("solution_id") == authorization.solution_id
        and selection_data.get("approval_hash") == authorization.approval_hash
        and selection_data.get("layout_hash") == authorization.layout_hash,
        "persisted RUN-003 selection differs from the P6-bound identity",
    )
    expected_artifacts = {
        "selection.json": selection_path,
        solution_path.relative_to(run_dir).as_posix(): solution_path,
    }
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise Run003StudyAuthorizationError("RUN-003 artifact manifest has no artifact list")
    indexed = {entry.get("path"): entry for entry in artifacts if isinstance(entry, dict)}
    for relative, path in expected_artifacts.items():
        record = indexed.get(relative)
        data = _read_repository_bytes(
            path,
            f"persisted RUN-003 selection artifact {relative}",
            repository_root=root,
        )
        _require(
            record is not None
            and record.get("bytes") == len(data)
            and record.get("sha256") == hashlib.sha256(data).hexdigest(),
            f"persisted RUN-003 artifact hash mismatch: {relative}",
        )

    try:
        detail_decision = DecisionRecord.model_validate(selection_data["detail_decision"])
        parti_decision = DecisionRecord.model_validate(selection_data["parti_decision"])
        solution = DesignSolution.model_validate(solution_data)
    except (KeyError, ValidationError, ValueError) as exc:
        raise Run003StudyAuthorizationError(
            "persisted RUN-003 decision or solution is invalid"
        ) from exc
    _require(
        solution.solution_id == authorization.solution_id
        and solution.approval_hash == authorization.approval_hash
        and solution.geometry.get("layout_hash") == authorization.layout_hash,
        "persisted RUN-003 solution differs from the P6-bound approval or layout",
    )
    return Selection(
        decision=detail_decision,
        solution=solution,
        layout_hash=authorization.layout_hash,
        parti_decision=parti_decision,
    )


__all__ = [
    "RUN003_SOLUTION_ID",
    "Run003StudyAuthorization",
    "Run003StudyAuthorizationError",
    "load_run003_study_authorization",
    "load_run003_study_selection",
]
