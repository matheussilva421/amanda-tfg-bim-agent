"""Read-only detection of the installed Autodesk Revit products.

Detection is based on files and file metadata, never on a directory name
alone. An installed build is not evidence of a valid license or of a
successful launch, so the result is recorded as an inventory fact and the
downstream plans decide what a missing or ambiguous build blocks.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class RevitInstallation:
    product_name: str
    product_version: str
    file_version: str
    install_path: Path
    executable_path: Path
    api_path: Path
    year: int | None = None

    def as_dict(self) -> dict:
        return {
            "product_name": self.product_name,
            "product_version": self.product_version,
            "file_version": self.file_version,
            "install_path": str(self.install_path),
            "executable_path": str(self.executable_path),
            "api_path": str(self.api_path),
            "year": self.year,
        }


@dataclass
class RevitDetection:
    installations: list[RevitInstallation] = field(default_factory=list)
    searched_roots: list[str] = field(default_factory=list)
    probe_status: str = "NOT_PROBED"
    notes: list[str] = field(default_factory=list)

    @property
    def selected(self) -> RevitInstallation | None:
        """Highest installed year wins; ambiguity is reported, not hidden."""
        if not self.installations:
            return None
        return sorted(
            self.installations,
            key=lambda item: (item.year or 0, item.file_version),
            reverse=True,
        )[0]

    @property
    def is_ambiguous(self) -> bool:
        return len(self.installations) > 1

    def as_dict(self) -> dict:
        selected = self.selected
        return {
            "probe_status": self.probe_status,
            "installation_count": len(self.installations),
            "ambiguous": self.is_ambiguous,
            "searched_roots": list(self.searched_roots),
            "selected": selected.as_dict() if selected else None,
            "installations": [item.as_dict() for item in self.installations],
            "notes": list(self.notes),
        }


def program_files_roots() -> list[Path]:
    roots = []
    for variable in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
        value = os.environ.get(variable)
        if value:
            candidate = Path(value) / "Autodesk"
            if candidate not in roots:
                roots.append(candidate)
    return roots


def _year_from_name(name: str) -> int | None:
    digits = "".join(character for character in name if character.isdigit())
    if len(digits) == 4:
        return int(digits)
    return None


def scan_roots(roots: list[Path] | None = None) -> RevitDetection:
    """Inspect candidate Autodesk roots without launching anything."""
    detection = RevitDetection()
    candidates = roots if roots is not None else program_files_roots()
    for root in candidates:
        detection.searched_roots.append(str(root))
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if not child.is_dir() or not child.name.startswith("Revit 20"):
                continue
            executable = child / "Revit.exe"
            api = child / "RevitAPI.dll"
            if not (executable.is_file() and api.is_file()):
                detection.notes.append(
                    "incomplete installation at " + str(child)
                )
                continue
            metadata = _windows_file_metadata(executable)
            detection.installations.append(
                RevitInstallation(
                    product_name=metadata.get("ProductName") or child.name,
                    product_version=metadata.get("ProductVersion") or "",
                    file_version=metadata.get("FileVersion") or "",
                    install_path=child,
                    executable_path=executable,
                    api_path=api,
                    year=_year_from_name(child.name),
                )
            )
    detection.probe_status = "DETECTED" if detection.installations else "NOT_FOUND"
    return detection


def _windows_file_metadata(path: Path) -> dict:
    """Read version resources through PowerShell when available."""
    script = (
        "$ErrorActionPreference='Stop';"
        "$v=(Get-Item -LiteralPath '"
        + str(path).replace("'", "''")
        + "').VersionInfo;"
        "[pscustomobject]@{ProductName=$v.ProductName;"
        "ProductVersion=$v.ProductVersion;"
        "FileVersion=$v.FileVersion} | ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if completed.returncode != 0:
            return {}
        return json.loads(completed.stdout.strip() or "{}")
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return {}
