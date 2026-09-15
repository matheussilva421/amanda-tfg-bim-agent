"""Render and persist the finalist comparison matrix for a design run."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import typer

from .design import RUNS_ROOT, DesignInputError, validate_run_id
from .doctor import project_root


class CompareInputError(RuntimeError):
    """Raised when a design run cannot be compared safely."""


def _read_run(run_directory: Path, run_id: str) -> dict[str, Any]:
    path = run_directory / "run.json"
    if not path.is_file() or path.is_symlink():
        raise CompareInputError(f"design run is missing: {run_id}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompareInputError(f"design run is invalid: {run_id}") from exc
    if not isinstance(payload, Mapping) or payload.get("run_id") != run_id:
        raise CompareInputError(f"design run identity is invalid: {run_id}")
    return dict(payload)


def _matrix_row(item: Any, index: int) -> dict[str, Any]:
    values = dict(item) if isinstance(item, Mapping) else {"value": item}
    finalist_id = values.get("finalist_id") or values.get("solution_id") or values.get("id")
    return {
        "finalist_id": str(finalist_id or f"finalist-{index:02d}"),
        "seed": values.get("seed"),
        "status": values.get("status"),
        "geometry_hash": values.get("geometry_hash"),
        "metrics": values.get("metrics", {}),
        "hard_violations": values.get("hard_violations", []),
    }


def compare_run(root: Path, *, run_id: str) -> dict[str, Any]:
    try:
        safe_run_id = validate_run_id(run_id)
    except DesignInputError as exc:
        raise CompareInputError(str(exc)) from exc
    root = Path(root).resolve()
    run_directory = root / RUNS_ROOT / safe_run_id
    run = _read_run(run_directory, safe_run_id)
    finalists = run.get("finalists")
    if not isinstance(finalists, list):
        raise CompareInputError(f"design run has no finalist list: {safe_run_id}")
    matrix = {
        "schema_version": 1,
        "run_id": safe_run_id,
        "columns": ["finalist_id", "seed", "status", "geometry_hash", "metrics", "hard_violations"],
        "finalists": [_matrix_row(item, index) for index, item in enumerate(finalists, start=1)],
    }
    matrix_path = run_directory / "finalist-matrix.json"
    matrix_path.write_text(
        json.dumps(matrix, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "run_id": safe_run_id,
        "matrix_path": matrix_path,
        "matrix_relative_path": matrix_path.relative_to(root),
        "finalists": matrix["finalists"],
    }


def render_matrix(result: Mapping[str, Any]) -> None:
    typer.echo("finalist matrix")
    typer.echo(f"run {result['run_id']}")
    typer.echo("finalist_id seed status geometry_hash")
    finalists = result["finalists"]
    if finalists:
        for finalist in finalists:
            typer.echo(
                f"{finalist['finalist_id']} {finalist.get('seed')} "
                f"{finalist.get('status')} {finalist.get('geometry_hash')}"
            )
    else:
        typer.echo("(none)")
    typer.echo(f"saved {result['matrix_relative_path']}")


def compare_command(run_id: str, root: Path | None = None) -> dict[str, Any]:
    return compare_run(root or project_root(), run_id=run_id)


__all__ = ["CompareInputError", "compare_command", "compare_run", "render_matrix"]
