"""Read-only export planning and artifact verification commands."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer

from ..release.manifest import (
    ManifestVerification,
    load_manifest,
    verify_manifest,
)

export_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Plan and verify release exports without writing them.",
)


@dataclass(frozen=True)
class ExportVerification:
    valid: bool
    release_directory: Path
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    manifest_result: ManifestVerification | None

    def __bool__(self) -> bool:
        return self.valid


def release_directory(root: str | Path, release_id: str) -> Path:
    """Resolve an existing release or return the canonical planned location."""

    base = Path(root)
    candidates = (
        base / "releases" / release_id,
        base / "release" / release_id,
        base / "deliverables" / release_id,
        base / release_id,
        base / "releases" / "GOLDEN" / release_id,
        base / "release" / "GOLDEN" / release_id,
        base / "deliverables" / "GOLDEN" / release_id,
        base / "GOLDEN" / release_id,
    )
    for candidate in candidates:
        if candidate.is_dir() or (candidate / "manifest.json").is_file():
            return candidate
    return candidates[0]


def plan_exports(root: str | Path, release_id: str) -> dict[str, Any]:
    """Return the export plan without creating directories or manifests."""

    directory = release_directory(root, release_id)
    manifest_path = directory / "manifest.json"
    expected: list[dict[str, Any]] = []
    if manifest_path.is_file():
        try:
            manifest = load_manifest(manifest_path)
        except (OSError, ValueError, TypeError):
            manifest = None
        if manifest is not None:
            expected = [dict(item) for item in manifest.exports]
    if not expected:
        expected = [
            {"path": "model.rvt", "mandatory": True},
            {"path": "exports/model.ifc", "mandatory": True},
            {"path": "exports/documentation.pdf", "mandatory": True},
            {"path": "exports/documentation.dwg", "mandatory": False},
        ]
    return {
        "release_id": release_id,
        "release_directory": directory.as_posix(),
        "manifest": manifest_path.as_posix(),
        "read_only": True,
        "exports": sorted(expected, key=lambda item: str(item.get("path", "")).casefold()),
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_exports(
    root: str | Path,
    release_id: str,
) -> ExportVerification:
    """Recompute export hashes, sizes and declared sidecar signatures."""

    directory = release_directory(root, release_id)
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        return ExportVerification(
            valid=False,
            release_directory=directory,
            errors=("release manifest is missing: " + str(manifest_path),),
            warnings=(),
            manifest_result=None,
        )
    manifest_result = verify_manifest(manifest_path)
    errors = list(manifest_result.errors)
    warnings = list(manifest_result.warnings)
    try:
        manifest = load_manifest(manifest_path)
    except (OSError, ValueError, TypeError) as exc:
        return ExportVerification(
            valid=False,
            release_directory=directory,
            errors=tuple(errors + ["invalid manifest: " + str(exc)]),
            warnings=tuple(warnings),
            manifest_result=manifest_result,
        )
    for export in manifest.exports:
        path_value = export.get("path")
        if not path_value:
            errors.append("export entry has no path")
            continue
        candidate = Path(str(path_value))
        resolved_root = directory.resolve()
        path = (directory / candidate).resolve()
        try:
            path.relative_to(resolved_root)
        except ValueError:
            errors.append("export path escapes release directory: " + str(path_value))
            continue
        if not path.is_file():
            if export.get("mandatory", export.get("required", False)):
                errors.append("mandatory export is missing: " + str(path_value))
            else:
                warnings.append("optional export is missing: " + str(path_value))
            continue
        expected_size = export.get("size_bytes")
        if expected_size is not None and path.stat().st_size != expected_size:
            errors.append("export size mismatch: " + str(path_value))
        expected_hash = export.get("sha256") or manifest.content_hashes.get(str(path_value))
        if expected_hash is not None and _sha256(path) != expected_hash:
            errors.append("export hash mismatch: " + str(path_value))
        signature_path = export.get("signature_path")
        expected_signature = export.get("signature")
        if signature_path and expected_signature is not None:
            sidecar = directory / str(signature_path)
            if not sidecar.is_file():
                errors.append("export signature is missing: " + str(signature_path))
            elif sidecar.read_text(encoding="utf-8").strip() != str(expected_signature):
                errors.append("export signature mismatch: " + str(path_value))
    return ExportVerification(
        valid=not errors,
        release_directory=directory,
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(dict.fromkeys(warnings)),
        manifest_result=manifest_result,
    )


@export_app.command("plan")
def plan(
    release_id: str = typer.Option(..., "--release-id"),
    root: Path | None = typer.Option(None, "--root"),  # noqa: B008
) -> None:
    """Print the planned export set; this command is strictly read-only."""

    from .doctor import project_root

    result = plan_exports(root or project_root(), release_id)
    typer.echo("export plan (read-only)")
    typer.echo("release      " + result["release_id"])
    typer.echo("manifest     " + result["manifest"])
    for item in result["exports"]:
        flag = "mandatory" if item.get("mandatory", item.get("required", False)) else "optional"
        typer.echo("  " + str(item.get("path", "<unnamed>")) + " [" + flag + "]")


@export_app.command("verify")
def verify(
    release_id: str = typer.Option(..., "--release-id"),
    root: Path | None = typer.Option(None, "--root"),  # noqa: B008
) -> None:
    """Recompute expected export hashes, sizes and supported signatures."""

    from .doctor import project_root

    result = verify_exports(root or project_root(), release_id)
    if result.valid:
        typer.echo("export verify PASS")
        typer.echo("release      " + str(result.release_directory))
        raise typer.Exit(code=0)
    typer.echo("export verify refused", err=True)
    for error in result.errors:
        typer.echo("  " + error, err=True)
    raise typer.Exit(code=1)


__all__ = [
    "ExportVerification",
    "export_app",
    "plan_exports",
    "release_directory",
    "verify_exports",
]
