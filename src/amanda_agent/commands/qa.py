"""QA command boundary with explicit blocked-input reporting."""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer

from ..redaction import redact

QA_MODULES = (
    "models",
    "program",
    "model",
    "warnings",
    "architecture",
    "accessibility",
    "ifc",
    "pdf",
    "dwg",
)

qa_app = typer.Typer(
    no_args_is_help=False,
    add_completion=False,
    invoke_without_command=True,
    help="Run model and release-candidate QA with explicit status boundaries.",
)


@dataclass(frozen=True)
class QACommandResult:
    json_path: Path
    markdown_path: Path
    report: dict[str, Any]


def _load_model_manifest(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("model manifest is missing or mutable: " + str(path))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("model manifest is invalid: " + str(exc)) from exc
    if not isinstance(value, dict):
        raise TypeError("model manifest must contain a JSON object")
    return value


def _available_qa_modules() -> tuple[list[str], list[str]]:
    available: list[str] = []
    missing: list[str] = []
    for module_name in QA_MODULES:
        qualified = "amanda_agent.qa." + module_name
        try:
            importlib.import_module(qualified)
        except (ImportError, ModuleNotFoundError):
            missing.append(qualified)
        else:
            available.append(qualified)
    return available, missing


def _manifest_checks(source: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = source.get("qa_checks", source.get("checks", []))
    if not isinstance(candidates, list):
        return []
    checks: list[dict[str, Any]] = []
    for item in candidates:
        if isinstance(item, dict):
            checks.append(
                {
                    "id": str(item.get("id", item.get("name", "unnamed-check"))),
                    "status": str(item.get("status", "BLOCKED")).upper(),
                    "mandatory": bool(item.get("mandatory", False)),
                    "detail": str(item.get("detail", "")),
                }
            )
    return sorted(checks, key=lambda item: item["id"])


def build_qa_report(
    model_manifest: str | Path,
    *,
    release_id: str | None = None,
    profile: str = "STUDY",
) -> dict[str, Any]:
    """Build a redacted QA report without inventing absent evidence."""

    source_path = Path(model_manifest)
    source = _load_model_manifest(source_path)
    normalized_profile = profile.upper()
    if normalized_profile not in {"STUDY", "FINAL"}:
        raise ValueError("profile must be STUDY or FINAL")
    available, missing = _available_qa_modules()
    checks = _manifest_checks(source)
    had_explicit_checks = bool(checks)
    limitations: list[str] = []
    if missing:
        limitations.append(
            "QA modules P06-T01..T09 are not all present: " + ", ".join(missing)
        )
        checks.insert(
            0,
            {
                "id": "qa-suite",
                "status": "BLOCKED",
                "mandatory": normalized_profile == "FINAL",
                "detail": "the typed QA suite is not available at command time",
            },
        )
    elif not checks:
        limitations.append(
            "no explicit model QA evidence was supplied; an empty issue list is not acceptance"
        )
        checks.insert(
            0,
            {
                "id": "qa-evidence",
                "status": "BLOCKED",
                "mandatory": normalized_profile == "FINAL",
                "detail": "model manifest contains no executable or completed QA checks",
            },
        )
    status = "BLOCKED" if missing or not had_explicit_checks else "PASS"
    if any(item["status"] in {"FAIL", "CRITICAL"} for item in checks):
        status = "FAIL"
    elif any(
        item["status"] not in {"PASS", "PASS_WITH_WARNINGS"}
        for item in checks
    ):
        status = "BLOCKED"
    return redact(
        {
            "schema_version": 1,
            "release_id": release_id or source_path.stem,
            "profile": normalized_profile,
            "status": status,
            "checks": checks,
            "qa_modules_available": available,
            "qa_modules_missing": missing,
            "limitations": limitations,
            "model_manifest": source_path.name,
            "source_keys": sorted(source.keys()),
        }
    )


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# QA Report",
        "",
        f"Release: {report['release_id']}",
        f"Profile: {report['profile']}",
        f"Status: {report['status']}",
        "",
        "## Checks",
        "",
    ]
    for check in report["checks"]:
        mandatory = " mandatory" if check.get("mandatory") else " optional"
        detail = ": " + check["detail"] if check.get("detail") else ""
        lines.append(f"- {check['id']}: {check['status']}{mandatory}{detail}")
    lines.extend(["", "## Limitations", ""])
    if report["limitations"]:
        lines.extend("- " + limitation for limitation in report["limitations"])
    else:
        lines.append("- none recorded")
    return "\n".join(lines) + "\n"


def write_qa_reports(
    report: dict[str, Any],
    output_directory: str | Path,
) -> tuple[Path, Path]:
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    release_id = str(report["release_id"])
    json_path = output / f"{release_id}-qa.json"
    markdown_path = output / f"{release_id}-qa.md"
    json_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def run_qa(
    model_manifest: str | Path,
    *,
    release_id: str | None = None,
    profile: str = "STUDY",
    output_directory: str | Path | None = None,
) -> QACommandResult:
    source = Path(model_manifest)
    report = build_qa_report(source, release_id=release_id, profile=profile)
    output = Path(output_directory) if output_directory else source.parent / "qa-reports"
    json_path, markdown_path = write_qa_reports(report, output)
    return QACommandResult(json_path, markdown_path, report)


@qa_app.callback()
def qa(
    model_manifest: Path = typer.Option(  # noqa: B008
        ...,
        "--model-manifest",
        exists=False,
        dir_okay=False,
        help="Path to the serialized model manifest.",
    ),
    release_id: str | None = typer.Option(None, "--release-id"),
    profile: str = typer.Option("STUDY", "--profile"),
    output_dir: Path | None = typer.Option(None, "--output-dir"),  # noqa: B008
) -> None:
    """Write a JSON and Markdown QA report."""

    try:
        result = run_qa(
            model_manifest,
            release_id=release_id,
            profile=profile,
            output_directory=output_dir,
        )
    except (OSError, TypeError, ValueError) as exc:
        typer.echo("qa refused: " + str(exc), err=True)
        raise typer.Exit(code=2) from exc
    typer.echo("qa status    " + result.report["status"])
    typer.echo("json report  " + str(result.json_path))
    typer.echo("md report    " + str(result.markdown_path))


__all__ = [
    "QA_MODULES",
    "QACommandResult",
    "build_qa_report",
    "qa_app",
    "run_qa",
    "write_qa_reports",
]
