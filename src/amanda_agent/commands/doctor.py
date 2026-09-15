"""Environment diagnosis.

The report separates what is universally required (the agent loop itself)
from what only a specific branch needs. A missing Revit build blocks the BIM
provider work while leaving source, solver and documentation work available,
so the exit code reflects only genuine, global failures.
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..bootstrap.environment import ToolProbe, probe_tools
from ..bootstrap.revit import scan_roots
from ..paths import ProjectPaths

PHASE_BIM_START = "PHASE_02"


def project_root(environ: dict | None = None) -> Path:
    import os

    source = os.environ if environ is None else environ
    override = source.get("AMANDA_PROJECT_ROOT")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3]


def run_revit_detection() -> dict:
    return scan_roots().as_dict()


def run_probes() -> list[ToolProbe]:
    return probe_tools()


def build_environment_report(
    *,
    revit: dict,
    probes: list[ToolProbe],
    root: Path,
) -> dict:
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "amanda_agent doctor",
        "project_root": str(root),
        "machine": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python": sys.version,
            "python_executable": sys.executable,
            "architecture": platform.machine(),
        },
        "revit": revit,
        "probes": [probe.as_dict() for probe in probes],
        "inventory": [
            probe.as_dict()
            for probe in probes
            if probe.name in {"dotnet", "python312"}
        ],
        "scope": (
            "read-only diagnosis; probes never install, upgrade or reconfigure "
            "the tools they inspect"
        ),
    }


def evaluate_health(report: dict) -> dict:
    """Decide what the observations actually block."""
    blocked_phases: list[str] = []
    reasons: list[str] = []
    critical = False

    probes = report.get("probes", [])
    for probe in probes:
        if probe.get("status") == "MISSING" and probe.get("critical"):
            critical = True
            reasons.append(
                "required tool missing: " + str(probe.get("name"))
            )

    revit = report.get("revit", {})
    if revit.get("probe_status") != "DETECTED":
        blocked_phases.append(PHASE_BIM_START)
        reasons.append(
            "no verified Revit installation: BIM provider work is blocked "
            "while source, solver and documentation work continue"
        )
    elif revit.get("ambiguous"):
        blocked_phases.append(PHASE_BIM_START)
        reasons.append("multiple Revit installations: the exact build must be selected")

    return {
        "critical_failure": critical,
        "exit_code": 1 if critical else 0,
        "blocked_phases": blocked_phases,
        "reasons": reasons,
        "verified": {
            "revit_detected": revit.get("probe_status") == "DETECTED",
            "codex_available": any(
                probe.get("name") == "codex" and probe.get("status") == "AVAILABLE"
                for probe in probes
            ),
        },
    }


def write_report(report: dict, root: Path) -> Path:
    paths = ProjectPaths.from_root(root)
    paths.ensure_directories()
    target = paths.state / "environment-report.json"
    target.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return target


def doctor(root: Path | None = None) -> tuple[dict, Path]:
    resolved_root = Path(root) if root is not None else project_root()
    report = build_environment_report(
        revit=run_revit_detection(),
        probes=run_probes(),
        root=resolved_root,
    )
    report["health"] = evaluate_health(report)
    target = write_report(report, resolved_root)
    return report, target
