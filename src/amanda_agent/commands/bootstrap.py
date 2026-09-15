"""Idempotent foundation setup.

Running this twice must not change a value a human or an earlier run already
established, so every write is missing-only. Provider installation is
deliberately absent: that belongs to Plan 02, after the build inputs are
audited.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from ..paths import ProjectPaths
from ..state.store import StateStore
from .doctor import (
    build_environment_report,
    evaluate_health,
    run_probes,
    run_revit_detection,
)


def _write_if_missing(path: Path, payload) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    return True


def _environment_lock(report: dict) -> dict:
    revit = report["revit"].get("selected") or {}
    tools = {probe["name"]: probe for probe in report["probes"]}
    return {
        "schema_version": 1,
        "generated_utc": report["generated_utc"],
        "scope": (
            "durable environment lock: the verified host facts this project "
            "was built against"
        ),
        "revit": {
            "selected_build": revit.get("file_version"),
            "product_version": revit.get("product_version"),
            "install_path": revit.get("install_path"),
            "note": (
                "installed files do not prove licensing or a successful launch"
            ),
        },
        "python": {
            "version": (tools.get("python312") or {}).get("version"),
            "note": "the control plane runs on the pinned 3.12 venv",
        },
        "codex": {"version": (tools.get("codex") or {}).get("version")},
        "git": {"version": (tools.get("git") or {}).get("version")},
        "powershell": {
            "version": (tools.get("powershell") or {}).get("version")
        },
        "dotnet": {
            "sdks": (tools.get("dotnet") or {}).get("sdks", []),
            "note": "inventory only; a pinned SDK is installed in Plan 02",
        },
    }


def _tool_health(report: dict) -> dict:
    return {
        "schema_version": 1,
        "generated_utc": report["generated_utc"],
        "tools": {
            probe["name"]: {
                "status": probe["status"],
                "version": probe["version"],
            }
            for probe in report["probes"]
        },
        "revit": {
            "status": report["revit"]["probe_status"],
            "selected": (report["revit"].get("selected") or {}).get("file_version"),
        },
    }


def bootstrap_environment(root: Path) -> dict:
    """Create the foundation directories and durable state, once."""
    paths = ProjectPaths.from_root(root)
    paths.ensure_directories()

    report = build_environment_report(
        revit=run_revit_detection(),
        probes=run_probes(),
        root=paths.root,
    )
    report["health"] = evaluate_health(report)

    created = []
    (paths.state / "environment-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    created.append("state/environment-report.json")

    store = StateStore(paths.project_state)
    if not paths.project_state.exists():
        store.save(store.load())
        created.append("PROJECT_STATE.yaml")

    if _write_if_missing(
        paths.state / "bim-environment.lock.yaml", _environment_lock(report)
    ):
        created.append("state/bim-environment.lock.yaml")

    if _write_if_missing(
        paths.state / "blockers.yaml", {"schema_version": 1, "blockers": []}
    ):
        created.append("state/blockers.yaml")

    if _write_if_missing(paths.state / "tool-health.yaml", _tool_health(report)):
        created.append("state/tool-health.yaml")

    return {
        "root": str(paths.root),
        "created": created,
        "report": report,
    }
