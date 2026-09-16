"""Synthetic R14 to R16 release drill.

The drill is deliberately local and synthetic.  Its default mode only prints
the planned gates.  ``--execute`` creates a disposable candidate, runs the
typed QA and persistence contracts, verifies hashes, and exercises the
fail-closed promotion boundary.  It never starts Revit or an MCP provider.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pypdf import PdfWriter

from amanda_agent.bim.lab_fixture import (
    BUILD,
    SCHEMA,
    build_lab_fixture_plans,
    build_lab_fixture_registry,
)
from amanda_agent.bim.safety import SafetyError, assert_writable_target
from amanda_agent.commands.export import verify_exports
from amanda_agent.commands.qa import run_qa
from amanda_agent.qa import (
    QaCheckStatus,
    QaReport,
    create_minimal_ifc,
    qa_accessibility,
    qa_architecture,
    qa_model,
    render_report_markdown,
    validate_dwg,
    validate_ifc,
    validate_pdf,
)
from amanda_agent.qa.models import PROFILE_MANDATORY_CHECKS
from amanda_agent.qa.persistence import (
    REQUIRED_SEQUENCE,
    PersistenceCoordinator,
    PersistenceStatus,
    PersistenceStep,
    sha256_file,
)
from amanda_agent.release.manifest import (
    ArtifactRecord,
    ReleaseCheck,
    ReleaseManifest,
    ReleaseProfile,
    verify_manifest,
    write_manifest,
)
from amanda_agent.release.promote import (
    REQUIRED_REPORTS,
    PromotionRefused,
    promote,
    verify_release,
)

PROJECT_NAME = "Amanda TFG BIM Agent"
SYNTHETIC_BUILD = "2027"
SYNTHETIC_SOURCE_PLAN = "P05"
PROTECTED_TOKENS = frozenset(
    {"golden", "master", "source", "baseline", "checkpoint", "release"}
)

PersistenceAction = Callable[[], Any]


class ReleaseDrillError(RuntimeError):
    """The synthetic drill cannot establish a safe lab target."""


@dataclass(frozen=True)
class ReleaseDrillPlan:
    """Read-only paths and gates that an execution would exercise."""

    release_root: Path
    release_id: str
    release_directory: Path
    golden_root: Path
    golden_target: Path
    steps: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "release_root": str(self.release_root),
            "release_id": self.release_id,
            "release_directory": str(self.release_directory),
            "golden_root": str(self.golden_root),
            "golden_target": str(self.golden_target),
            "steps": list(self.steps),
        }


@dataclass(frozen=True)
class ReleaseDrillResult:
    """Outcome and evidence pointers returned by the harness."""

    plan: ReleaseDrillPlan
    executed: bool
    success: bool
    reasons: tuple[str, ...] = ()
    release_directory: Path | None = None
    golden_target: Path | None = None
    second_promotion_refused: bool = False
    qa_status: str | None = None
    persistence_complete: bool = False
    manifest_valid: bool = False
    exports_valid: bool = False


def _safe_release_id(release_id: str) -> str:
    value = str(release_id).strip()
    candidate = Path(value)
    if not value or candidate.is_absolute() or len(candidate.parts) != 1:
        raise ReleaseDrillError("release-id must be one relative path component")
    if value in {".", ".."}:
        raise ReleaseDrillError("release-id must identify a new lab candidate")
    return value


def _assert_safe_lab_root(release_root: str | Path) -> Path:
    root = Path(release_root).resolve(strict=False)
    for component in root.parts:
        lowered = component.casefold()
        if any(token in lowered for token in PROTECTED_TOKENS):
            raise ReleaseDrillError(
                f"release-root contains a protected path token: {component}"
            )
    probe = root / ".amanda-rd-probe"
    try:
        assert_writable_target(probe, writable_roots=[root])
    except SafetyError as exc:
        raise ReleaseDrillError(f"release-root refused by safety sentinel: {exc}") from exc
    return root


def _plan(release_root: str | Path, release_id: str) -> ReleaseDrillPlan:
    root = _assert_safe_lab_root(release_root)
    selected_id = _safe_release_id(release_id)
    candidate = root / selected_id
    return ReleaseDrillPlan(
        release_root=root,
        release_id=selected_id,
        release_directory=candidate,
        # This directory is passed only to promote(); the harness never
        # creates it directly because the publication API owns that boundary.
        golden_root=root / "GOLDEN",
        golden_target=root / "GOLDEN" / selected_id,
        steps=(
            "R14: run typed QA and export validators",
            "R15: create synthetic candidate and complete persistence sequence",
            "manifest: hash every candidate artifact and verify hashes",
            "R16: promote through release.promote.promote",
            "R16: assert a second promotion to the same target is refused",
        ),
    )


def _assert_safe_file(path: Path, root: Path) -> Path:
    try:
        return assert_writable_target(path, writable_roots=[root])
    except SafetyError as exc:
        raise ReleaseDrillError(f"artifact path refused by safety sentinel: {exc}") from exc


def _write_bytes(path: Path, payload: bytes, *, root: Path) -> Path:
    target = _assert_safe_file(path, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return target


def _write_text(path: Path, payload: str, *, root: Path) -> Path:
    return _write_bytes(path, payload.encode("utf-8"), root=root)


def _write_json(path: Path, payload: Mapping[str, Any], *, root: Path) -> Path:
    return _write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        root=root,
    )


def _create_pdf(path: Path, *, root: Path) -> Path:
    target = _assert_safe_file(path, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    with target.open("wb") as stream:
        writer.write(stream)
    return target


def _synthetic_model_manifest(release_id: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "model_id": f"synthetic-{release_id}",
        "stage": "R13_DOCUMENTATION",
        "source_plan": SYNTHETIC_SOURCE_PLAN,
        "fixture": True,
        "qa_checks": [],
        "elements": [
            {
                "logical_id": "ROOM-A",
                "category": "room",
                "is_room": True,
                "positioned": True,
                "enclosed": True,
                "within_site": True,
                "level": "LEVEL-01",
            },
            {
                "logical_id": "ROOM-B",
                "category": "room",
                "is_room": True,
                "positioned": True,
                "enclosed": True,
                "within_site": True,
                "level": "LEVEL-01",
            },
        ],
    }


def _run_qa_validators(source: Path) -> dict[str, QaReport]:
    exports = source / "exports"
    ifc = validate_ifc(
        exports / "model.ifc",
        expected_counts={"storeys": 1, "spaces": 1, "walls": 1, "doors": 1},
        profile="R14",
    )
    pdf = validate_pdf(
        exports / "documentation.pdf",
        expected_pages=1,
        preview_root=exports / "previews",
        profile="R14",
    )
    dwg = validate_dwg(exports / "documentation.dwg", profile="R14")
    model = qa_model(
        {
            "elements": _synthetic_model_manifest("QA")["elements"],
            "counts": {"before": 2, "after": 2},
        },
        config={
            "room_categories": ["room"],
            "expected_levels": {"ROOM-A": "LEVEL-01", "ROOM-B": "LEVEL-01"},
            "prohibit_outside_site": True,
        },
        stage="R14",
        profile="R14",
    )
    architecture = qa_architecture(
        {
            "edges": [
                {
                    "source": "ROOM-A",
                    "target": "ROOM-B",
                    "flow": "internal",
                    "relation": "adjacency",
                }
            ]
        },
        {
            "edges": [
                {
                    "source": "ROOM-A",
                    "target": "ROOM-B",
                    "flow": "internal",
                    "relation": "adjacency",
                }
            ]
        },
        profile="R14",
    )
    accessibility = qa_accessibility(
        {
            "routes": [
                {
                    "check_id": "accessibility.route.ROOM-A-ROOM-B",
                    "path": ["ROOM-A", "ROOM-B"],
                    "edges": [{"source": "ROOM-A", "target": "ROOM-B"}],
                }
            ]
        },
        profile="R14",
    )
    return {
        "model": model,
        "architecture": architecture,
        "accessibility": accessibility,
        "ifc": ifc,
        "pdf": pdf,
        "dwg": dwg,
    }


def _mandatory_pass(report: QaReport) -> bool:
    mandatory = [check for check in report.checks if check.mandatory]
    return bool(mandatory) and all(
        check.status is QaCheckStatus.PASS for check in mandatory
    )


def _report_status(report: QaReport) -> str:
    return "PASS" if _mandatory_pass(report) else report.result.value


def _report_payload(report: QaReport) -> dict[str, Any]:
    return report.to_dict()


def _qa_checks(reports: Mapping[str, QaReport]) -> list[dict[str, Any]]:
    required_ids = PROFILE_MANDATORY_CHECKS["FINAL"]
    statuses = {
        "program": "PASS",
        "model": _report_status(reports["model"]),
        "architecture": _report_status(reports["architecture"]),
        "accessibility": _report_status(reports["accessibility"]),
        "ifc": _report_status(reports["ifc"]),
        "pdf": _report_status(reports["pdf"]),
        "dwg": _report_status(reports["dwg"]),
    }
    return [
        {
            "id": check_id,
            "status": statuses[check_id],
            "mandatory": True,
            "detail": "synthetic Plan 05 evidence and R14 validator result",
        }
        for check_id in required_ids
    ]


def _render_qa_report(
    release_id: str,
    command_report: Mapping[str, Any],
    reports: Mapping[str, QaReport],
) -> str:
    lines = [
        "# QA Report",
        "",
        f"Release: {release_id}",
        "Stage: R14 (synthetic)",
        f"Command QA status: {command_report['status']}",
        "",
        "## Supported validators",
        "",
    ]
    for name in ("model", "architecture", "accessibility", "ifc", "pdf", "dwg"):
        lines.append(f"- {name}: {_report_status(reports[name])}")
    lines.extend(
        [
            "",
            (
                "The model is a disposable synthetic Plan 05 R13 fixture."
                " No Revit process or MCP provider was started."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _render_export_report(reports: Mapping[str, QaReport]) -> str:
    lines = ["# Export Report", "", "| Artifact | Validation |", "| --- | --- |"]
    for name, filename in (
        ("IFC", "exports/model.ifc"),
        ("PDF", "exports/documentation.pdf"),
        ("DWG", "exports/documentation.dwg"),
    ):
        lines.append(f"| `{filename}` | {_report_status(reports[name.casefold()])} |")
    lines.extend(
        [
            "",
            "PDF previews were rendered into `exports/previews` for visual review.",
            "DWG validation is limited to the registered signature and size validator.",
            "",
        ]
    )
    return "\n".join(lines)


def _persistence_evidence(
    status: PersistenceStatus,
    *,
    detail: str,
    **evidence: Any,
) -> dict[str, Any]:
    return {
        "status": status.value,
        "detail": detail,
        "evidence": {"runtime": "synthetic-lab", **evidence},
    }


def build_persistence_actions(model_path: str | Path) -> dict[PersistenceStep, PersistenceAction]:
    """Build typed synthetic actions for all ten persistence steps."""

    target = Path(model_path)
    return {
        PersistenceStep.SAVE_RC: lambda: _persistence_evidence(
            PersistenceStatus.PASS,
            detail="synthetic R15 candidate save recorded",
            path=str(target),
            saved=True,
        ),
        PersistenceStep.WAIT_SAVE_COMPLETION: lambda: _persistence_evidence(
            PersistenceStatus.PASS,
            detail="synthetic save completion observed",
            completed=True,
        ),
        PersistenceStep.CLOSE_AND_HASH: lambda: (
            _persistence_evidence(
                PersistenceStatus.PASS,
                detail="synthetic candidate closed and hashed",
                closed=True,
                sha256=sha256_file(target),
            )
            if target.is_file()
            else _persistence_evidence(
                PersistenceStatus.BLOCKED,
                detail="synthetic candidate file is missing",
                path=str(target),
            )
        ),
        PersistenceStep.PROCESS_EXIT: lambda: _persistence_evidence(
            PersistenceStatus.PASS,
            detail="synthetic process exit boundary recorded",
            exited=True,
        ),
        PersistenceStep.START_REVIT_2027: lambda: _persistence_evidence(
            PersistenceStatus.PASS,
            detail="synthetic cold-start boundary recorded; Revit was not started",
            cold_start=True,
            simulated=True,
        ),
        PersistenceStep.OPEN_RC: lambda: _persistence_evidence(
            PersistenceStatus.PASS,
            detail="synthetic candidate reopen boundary recorded",
            reopened=True,
            simulated=True,
        ),
        PersistenceStep.RECONNECT_PROVIDER: lambda: _persistence_evidence(
            PersistenceStatus.PASS,
            detail="synthetic provider reconnect boundary recorded",
            reconnected=True,
            simulated=True,
        ),
        PersistenceStep.PROVIDER_HEALTH: lambda: _persistence_evidence(
            PersistenceStatus.PASS,
            detail="synthetic provider health boundary recorded",
            healthy=True,
            simulated=True,
        ),
        PersistenceStep.CRITICAL_QA: lambda: _persistence_evidence(
            PersistenceStatus.PASS,
            detail="synthetic critical QA boundary recorded",
            passed=True,
        ),
        PersistenceStep.SEMANTIC_STATE: lambda: _persistence_evidence(
            PersistenceStatus.PASS,
            detail="synthetic semantic state comparison recorded",
            matched=True,
        ),
    }


def build_blocked_persistence_actions() -> dict[PersistenceStep, PersistenceAction]:
    """Return no-op actions suitable for describing a dry-run boundary."""

    def blocked_action(step: PersistenceStep) -> PersistenceAction:
        def action() -> dict[str, Any]:
            return _persistence_evidence(
                PersistenceStatus.BLOCKED,
                detail=f"dry-run does not execute {step.value}",
            )

        return action

    return {
        step: blocked_action(step)
        for step in REQUIRED_SEQUENCE
    }


def _build_plan05_evidence(source: Path) -> dict[str, Any]:
    fixture_root = source / "plan-evidence"
    _assert_safe_file(fixture_root / "synthetic-template.rte", source.parent)
    registry = build_lab_fixture_registry(
        root=fixture_root,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
    )
    plans = build_lab_fixture_plans(
        root=fixture_root,
        registry=registry,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
    )
    return {
        "stages": [str(plan.stage.value) for plan in plans],
        "operation_counts": [len(plan.operations) for plan in plans],
        "plan_count": len(plans),
        "final_stage": str(plans[-1].stage.value),
    }


def _create_candidate(plan: ReleaseDrillPlan) -> tuple[Path, dict[str, QaReport], dict[str, Any]]:
    source = plan.release_directory
    if source.exists():
        raise ReleaseDrillError(f"lab candidate already exists: {source}")

    model_path = _write_bytes(
        source / "model.rvt",
        (
            "AMANDA-SYNTHETIC-R13\n"
            f"source-plan={SYNTHETIC_SOURCE_PLAN}\n"
            f"release-id={plan.release_id}\n"
        ).encode(),
        root=plan.release_root,
    )
    exports = source / "exports"
    ifc_path = exports / "model.ifc"
    _assert_safe_file(ifc_path, plan.release_root)
    create_minimal_ifc(ifc_path)
    pdf_path = _create_pdf(exports / "documentation.pdf", root=plan.release_root)
    dwg_path = _write_bytes(
        exports / "documentation.dwg",
        b"AC1032\nAMANDA SYNTHETIC DWG\n",
        root=plan.release_root,
    )

    plan05_evidence = _build_plan05_evidence(source)
    reports = _run_qa_validators(source)
    model_manifest = _synthetic_model_manifest(plan.release_id)
    model_manifest["plan_05"] = plan05_evidence
    model_manifest["qa_checks"] = _qa_checks(reports)
    model_manifest_path = source / "model-manifest.json"
    _write_json(model_manifest_path, model_manifest, root=plan.release_root)
    qa_result = run_qa(
        model_manifest_path,
        release_id=plan.release_id,
        profile="FINAL",
        output_directory=source / "qa-reports",
    )
    _write_text(
        source / "QA_REPORT.md",
        _render_qa_report(plan.release_id, qa_result.report, reports),
        root=plan.release_root,
    )
    _write_text(
        source / "PROGRAM_COMPLIANCE.md",
        "# Program Compliance\n\n- program: PASS\n"
        "- evidence: synthetic Plan 05 fixture\n",
        root=plan.release_root,
    )
    _write_text(
        source / "ACCESSIBILITY_REPORT.md",
        "# Accessibility Report\n\n"
        + render_report_markdown(reports["accessibility"]),
        root=plan.release_root,
    )
    _write_text(
        source / "CAPABILITY_REPORT.md",
        "# Capability Report\n\n- provider: synthetic-lab\n- scope: synthetic\n"
        "- Revit/MCP invoked: no\n",
        root=plan.release_root,
    )
    _write_text(
        source / "EXPORT_REPORT.md",
        _render_export_report(reports),
        root=plan.release_root,
    )
    _write_json(
        source / "provenance.json",
        {
            "project": PROJECT_NAME,
            "release_id": plan.release_id,
            "source_plan": SYNTHETIC_SOURCE_PLAN,
            "source_stage": "R13_DOCUMENTATION",
            "qa_stage": "R14",
            "runtime": "synthetic-lab",
            "revit_started": False,
            "mcp_invoked": False,
        },
        root=plan.release_root,
    )
    missing_reports = [
        relative for relative in REQUIRED_REPORTS if not (source / relative).is_file()
    ]
    if missing_reports:
        raise ReleaseDrillError(
            "required report generation failed: " + ", ".join(missing_reports)
        )
    return source, reports, {
        "model": model_path,
        "ifc": ifc_path,
        "pdf": pdf_path,
        "dwg": dwg_path,
        "qa_result": qa_result,
    }


def _artifact_kind(path: Path) -> str:
    return {
        ".rvt": "model",
        ".ifc": "ifc",
        ".pdf": "pdf",
        ".dwg": "dwg",
        ".json": "evidence",
        ".md": "report",
        ".png": "preview",
    }.get(path.suffix.casefold(), "artifact")


def _manifest_for(
    source: Path,
    *,
    release_id: str,
    reports: Mapping[str, QaReport],
    qa_result: Any,
    persistence_record: Any,
    exports: Mapping[str, Path],
) -> ReleaseManifest:
    artifacts: list[ArtifactRecord] = []
    content_hashes: dict[str, str] = {}
    for path in sorted(item for item in source.rglob("*") if item.is_file()):
        relative = path.relative_to(source).as_posix()
        if relative == "manifest.json":
            continue
        digest = sha256_file(path)
        content_hashes[relative] = digest
        artifacts.append(
            ArtifactRecord(
                path=relative,
                kind=_artifact_kind(path),
                required=True,
                sha256=digest,
                size_bytes=path.stat().st_size,
            )
        )

    export_entries = [
        {
            "path": exports["ifc"].relative_to(source).as_posix(),
            "kind": "ifc",
            "mandatory": True,
            "validation_status": _report_status(reports["ifc"]),
        },
        {
            "path": exports["pdf"].relative_to(source).as_posix(),
            "kind": "pdf",
            "mandatory": True,
            "validation_status": _report_status(reports["pdf"]),
        },
        {
            "path": exports["dwg"].relative_to(source).as_posix(),
            "kind": "dwg",
            "mandatory": True,
            "validation_status": _report_status(reports["dwg"]),
        },
    ]
    report_status = str(qa_result.report["status"])
    return ReleaseManifest(
        project=PROJECT_NAME,
        release=release_id,
        timestamp=datetime.now(UTC).isoformat(),
        revit={
            "build": SYNTHETIC_BUILD,
            "stage": "R15_RELEASE_CANDIDATE",
            "runtime": "synthetic-lab",
            "started": False,
        },
        providers=[
            {
                "provider": "synthetic-lab",
                "status": "PASS",
                "evidence_scope": "SYNTHETIC",
            }
        ],
        qa_summary={
            "status": report_status,
            "stage": "R14",
            "command_report": qa_result.report,
            "validators": {
                key: _report_payload(value) for key, value in reports.items()
            },
        },
        persistence_summary=persistence_record.model_dump(mode="json"),
        exports=export_entries,
        release_profile=ReleaseProfile.FINAL,
        required_checks=[
            ReleaseCheck(
                id=check["id"],
                status=check["status"],
                mandatory=True,
                evidence=["QA_REPORT.md", "qa-reports/"],
            )
            for check in qa_result.report["checks"]
        ],
        optional_checks=[],
        required_artifacts=sorted(content_hashes),
        optional_artifacts=[],
        accepted_limitations=[],
        approval_evidence={
            "mode": "synthetic-lab",
            "revit_started": False,
            "mcp_invoked": False,
        },
        artifacts=artifacts,
        content_hashes=content_hashes,
        source_export_map={
            "model.rvt": [entry["path"] for entry in export_entries],
        },
    )


def _append_errors(target: list[str], values: Any) -> None:
    for value in values:
        text = str(value)
        if text not in target:
            target.append(text)


def run_release_drill(
    release_root: str | Path,
    release_id: str,
    *,
    execute: bool = False,
    persistence_actions: Mapping[PersistenceStep | str, PersistenceAction] | None = None,
) -> ReleaseDrillResult:
    """Plan or execute the synthetic R14 to R16 drill."""

    plan = _plan(release_root, release_id)
    if not execute:
        PersistenceCoordinator(
            plan.release_id,
            build_blocked_persistence_actions(),
        ).run()
        return ReleaseDrillResult(
            plan=plan,
            executed=False,
            success=False,
            release_directory=plan.release_directory,
            golden_target=plan.golden_target,
        )

    source, reports, paths = _create_candidate(plan)
    actions = (
        dict(persistence_actions)
        if persistence_actions is not None
        else build_persistence_actions(paths["model"])
    )
    persistence_record = PersistenceCoordinator(
        plan.release_id,
        actions,
        release_directory=source,
    ).run()
    manifest = _manifest_for(
        source,
        release_id=plan.release_id,
        reports=reports,
        qa_result=paths["qa_result"],
        persistence_record=persistence_record,
        exports={
            "ifc": paths["ifc"],
            "pdf": paths["pdf"],
            "dwg": paths["dwg"],
        },
    )
    manifest_path = _assert_safe_file(source / "manifest.json", plan.release_root)
    write_manifest(manifest_path, manifest)
    manifest_result = verify_manifest(manifest_path)
    export_result = verify_exports(plan.release_root, plan.release_id)
    release_result = verify_release(source)

    reasons: list[str] = []
    if not manifest_result.valid:
        _append_errors(reasons, manifest_result.errors)
    if not export_result.valid:
        _append_errors(reasons, export_result.errors)
    if not release_result.valid:
        _append_errors(reasons, release_result.errors)

    first_promoted = False
    second_refused = False
    sealed_result_valid = False
    if not reasons:
        try:
            promoted = promote(source, golden_root=plan.golden_root)
            first_promoted = promoted.target == plan.golden_target
            sealed_result_valid = verify_release(
                promoted.target,
                require_sealed=True,
            ).valid
            if not sealed_result_valid:
                reasons.append("promoted lab target failed sealed verification")
            try:
                promote(source, golden_root=plan.golden_root)
            except PromotionRefused:
                second_refused = True
            else:
                reasons.append("second promotion to the same GOLDEN target was accepted")
        except PromotionRefused as exc:
            reasons.append(str(exc))

    qa_status = str(paths["qa_result"].report["status"])
    success = bool(
        not reasons
        and first_promoted
        and sealed_result_valid
        and second_refused
        and persistence_record.is_complete
        and manifest_result.valid
        and export_result.valid
        and release_result.valid
    )
    return ReleaseDrillResult(
        plan=plan,
        executed=True,
        success=success,
        reasons=tuple(reasons),
        release_directory=source,
        golden_target=plan.golden_target,
        second_promotion_refused=second_refused,
        qa_status=qa_status,
        persistence_complete=persistence_record.is_complete,
        manifest_valid=manifest_result.valid,
        exports_valid=export_result.valid,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="execute the disposable synthetic lab drill",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = run_release_drill(
            args.release_root,
            args.release_id,
            execute=args.execute,
        )
    except (OSError, TypeError, ValueError, ReleaseDrillError) as exc:
        print(f"release drill refused: {exc}", file=sys.stderr)
        return 2

    if not args.execute:
        print("BIM RELEASE DRILL (dry-run; no writes, Revit or MCP)")
        for step in result.plan.steps:
            print(f"  {step}")
        return 0

    print("BIM RELEASE DRILL (--execute; synthetic lab only)")
    print(f"  candidate: {result.release_directory}")
    print(f"  manifest: {'PASS' if result.manifest_valid else 'BLOCKED'}")
    print(f"  exports: {'PASS' if result.exports_valid else 'BLOCKED'}")
    print(f"  persistence: {'PASS' if result.persistence_complete else 'BLOCKED'}")
    print(f"  second promotion refused: {result.second_promotion_refused}")
    if result.success:
        print("  status: PASS")
        return 0
    for reason in result.reasons or ("an execution gate was not proven",):
        print(f"  reason: {reason}", file=sys.stderr)
    print("  status: BLOCKED", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ReleaseDrillError",
    "ReleaseDrillPlan",
    "ReleaseDrillResult",
    "build_blocked_persistence_actions",
    "build_persistence_actions",
    "main",
    "run_release_drill",
]
