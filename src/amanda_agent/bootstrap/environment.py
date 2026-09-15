"""Probes for the tools the control plane depends on.

Probes are pure reads. They never install, upgrade, or reconfigure anything:
the SDK inventory exists so a later plan can decide which pinned compiler a
specific provider build needs.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class DotnetSdk:
    version: str
    base_path: str


@dataclass
class ToolProbe:
    name: str
    status: str
    version: str | None = None
    detail: str = ""
    path: str | None = None
    critical: bool = False
    sdks: list[DotnetSdk] = field(default_factory=list)

    def as_dict(self) -> dict:
        payload = {
            "name": self.name,
            "status": self.status,
            "version": self.version,
            "detail": self.detail,
            "path": self.path,
            "critical": self.critical,
        }
        if self.sdks:
            payload["sdks"] = [
                {"version": sdk.version, "base_path": sdk.base_path}
                for sdk in self.sdks
            ]
        return payload


def parse_dotnet_sdks(text: str) -> list[DotnetSdk]:
    """Parse the output of the dotnet --list-sdks command."""
    sdks: list[DotnetSdk] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or "[" not in line or "]" not in line:
            continue
        version, _, remainder = line.partition("[")
        base_path = remainder.rsplit("]", 1)[0].strip()
        version = version.strip()
        if not version or not base_path:
            continue
        sdks.append(DotnetSdk(version=version, base_path=base_path))
    return sdks


def _default_runner(argv: list[str]) -> CommandResult:
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return CommandResult(127, "", str(exc))
    return CommandResult(
        completed.returncode, completed.stdout or "", completed.stderr or ""
    )


def _first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def probe_tools(
    *,
    runner: Callable[[list[str]], CommandResult] | None = None,
    which: Callable[[str], str | None] | None = None,
) -> list[ToolProbe]:
    """Probe the toolchain. Codex is required; the SDK is only inventoried."""
    run = runner or _default_runner
    locate = which or (lambda name: shutil.which(name))
    probes: list[ToolProbe] = []

    version_commands = [
        ("git", ["git", "--version"], True, "Git is required for provenance."),
        (
            "codex",
            ["codex", "--version"],
            True,
            "Codex drives the agent loop; without it the pipeline cannot run.",
        ),
    ]
    for name, argv, critical, note in version_commands:
        location = locate(name)
        result = run(argv)
        if result.returncode == 0 and _first_line(result.stdout):
            probes.append(
                ToolProbe(
                    name=name,
                    status="AVAILABLE",
                    version=_first_line(result.stdout),
                    path=location,
                    critical=critical,
                    detail=note,
                )
            )
        else:
            probes.append(
                ToolProbe(
                    name=name,
                    status="MISSING",
                    path=location,
                    critical=critical,
                    detail=_first_line(result.stderr) or note,
                )
            )

    powershell = locate("powershell") or locate("pwsh")
    result = run(
        [
            powershell or "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$PSVersionTable.PSVersion.ToString()",
        ]
    )
    probes.append(
        ToolProbe(
            name="powershell",
            status="AVAILABLE" if result.returncode == 0 else "MISSING",
            version=_first_line(result.stdout) or None,
            path=powershell,
            critical=False,
            detail="Runs the bootstrap scripts.",
        )
    )

    python_probe = None
    candidate_paths: list[str] = []
    for name in ("py", "python"):
        candidate_paths.append(name + " -3.12")
        result = run([name, "-3.12", "--version"])
        detected = _first_line(result.stdout)
        # The launcher may silently fall back to another interpreter, so the
        # reported series is checked instead of trusting the requested flag.
        if result.returncode == 0 and detected.startswith("Python 3.12"):
            python_probe = ToolProbe(
                name="python312",
                status="AVAILABLE",
                version=detected,
                path=locate(name),
                critical=False,
                detail="Control-plane interpreter; 3.12 x64 is required by the plan.",
            )
            break
    if python_probe is None:
        python_probe = ToolProbe(
            name="python312",
            status="MISSING",
            critical=False,
            detail=(
                "No Python 3.12 launcher was found for "
                + ", ".join(candidate_paths)
                + ". The control-plane venv already pins 3.12 and is used instead."
            ),
        )
    probes.append(python_probe)

    result = run(["dotnet", "--list-sdks"])
    sdks = parse_dotnet_sdks(result.stdout) if result.returncode == 0 else []
    probes.append(
        ToolProbe(
            name="dotnet",
            status="AVAILABLE" if sdks else "MISSING",
            version=sdks[0].version if sdks else None,
            path=locate("dotnet"),
            critical=False,
            sdks=sdks,
            detail=(
                "Inventory only. A provider-specific SDK is installed in Plan 02 "
                "only after auditing that source build's pinned requirements."
            ),
        )
    )
    return probes
