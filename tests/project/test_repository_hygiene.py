from __future__ import annotations

import json
import subprocess
from pathlib import Path

from amanda_agent.state.store import StateStore
from amanda_agent.state.tasks import load_registry

ROOT = Path(__file__).resolve().parents[2]

ACTIVE_DOCS = (
    ROOT / "AGENTS.md",
    ROOT / "START_HERE.md",
    ROOT / "PROJECT_STATE.yaml",
    ROOT / "docs/spec/CURRENT.md",
    ROOT / "docs/plan/CURRENT.md",
    ROOT / "docs/decisions/DECISIONS.md",
    ROOT / "state/HANDOFF.md",
)

FORBIDDEN_ROOT_OPERATIONAL_FILES = (
    "2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md",
    "2026-09-11-amanda-tfg-bim-agent-design.md",
    "PLAN_SELF_REVIEW.md",
    "RESUME_AFTER_REBOOT.md",
    "START_HERE_FOR_CODEX.md",
)

FORBIDDEN_LEGACY_DOCUMENT_DIRS = (
    "docs/notes",
    "docs/superpowers/plans",
    "docs/superpowers/specs",
    "docs/review",
)

FORBIDDEN_LEGACY_HANDOFFS = (
    "docs/reports/2026-09-16-relatorio-completo-para-proximo-agente.md",
)

OBSOLETE_TOOL_HANDOFFS = (
    "tool-lab/topologic/HANDOFF.md",
    "tool-lab/environmental/HANDOFF.md",
    "tool-lab/revitcortex/results/t15-handoff.md",
)

STALE_ACTIVE_TERMS = (
    "three canonical boards",
    "três pranchas canônicas",
    "Miguel Castro interface",
    "2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md",
)


def _git(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_current_operational_documents_are_unique_and_present():
    # Catches required CURRENT and entrypoint documents disappearing.
    missing = [path.relative_to(ROOT).as_posix() for path in ACTIVE_DOCS if not path.is_file()]
    assert missing == [], f"missing required operational docs: {missing}"


def test_superseded_root_operational_documents_are_absent():
    # Catches old competing operational documents being restored at the root.
    present = [name for name in FORBIDDEN_ROOT_OPERATIONAL_FILES if (ROOT / name).exists()]
    assert present == []


def test_legacy_plan_spec_and_handoff_trees_are_absent():
    present_dirs = [name for name in FORBIDDEN_LEGACY_DOCUMENT_DIRS if (ROOT / name).exists()]
    present_handoffs = [name for name in FORBIDDEN_LEGACY_HANDOFFS if (ROOT / name).exists()]
    assert present_dirs == [], f"legacy operational document directories remain: {present_dirs}"
    assert present_handoffs == [], f"superseded handoffs remain: {present_handoffs}"


def test_old_tool_handoffs_are_removed_or_reclassified_as_evidence():
    present = [name for name in OBSOLETE_TOOL_HANDOFFS if (ROOT / name).exists()]
    assert present == [], f"old tool handoffs remain active: {present}"
    assert (ROOT / "tool-lab/revitcortex/results/t15-close-reopen-evidence.md").is_file()


def test_task_registry_routes_through_the_single_current_plan():
    registry = load_registry(ROOT / "state/task-graph.yaml")
    plan_paths = {record.plan_path for record in registry.tasks.values()}
    assert plan_paths == {"docs/plan/CURRENT.md"}
    assert (ROOT / "docs/plan/CURRENT.md").is_file()


def test_source_inventory_records_the_current_operational_documents(tmp_path: Path):
    output_path = tmp_path / "source-inventory.json"
    script = ROOT / "bootstrap/get-source-inventory.ps1"
    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-Root",
            str(ROOT),
            "-OutputPath",
            str(output_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    inventory = json.loads(output_path.read_text(encoding="utf-8-sig"))
    paths = {entry["path"] for entry in inventory["entries"]}
    assert {
        "AGENTS.md",
        "START_HERE.md",
        "PROJECT_STATE.yaml",
        "docs/spec/CURRENT.md",
        "docs/plan/CURRENT.md",
        "docs/decisions/DECISIONS.md",
        "state/HANDOFF.md",
    }.issubset(paths)


def test_no_generated_zip_package_is_tracked():
    # Catches generated plan packages being committed as repository sources.
    assert _git("ls-files", "*.zip") == []


def test_source_zip_files_are_not_hidden_by_generated_package_ignores():
    result = subprocess.run(
        ["git", "check-ignore", "-q", "supplied-source-evidence.zip"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, "source/evidence ZIPs must remain addable"


def test_active_entrypoints_do_not_route_to_stale_instructions():
    # Catches active entrypoints routing readers to obsolete three-board instructions.
    active_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in ACTIVE_DOCS
        if path.is_file() and path.suffix in {".md", ".yaml"}
    )
    hits = [term for term in STALE_ACTIVE_TERMS if term in active_text]
    assert hits == []


def test_local_cleanup_script_has_no_route_to_deleted_plan():
    script = (ROOT / "scripts/cleanup-local.ps1").read_text(encoding="utf-8")
    assert "docs/superpowers/plans/" not in script


def test_exactly_four_canonical_board_images_are_active():
    # Catches missing, extra, or misnamed images in the active canonical source set.
    canonical = ROOT / "docs/source/canonical"
    images = (
        sorted(
            path.name
            for path in canonical.iterdir()
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
        )
        if canonical.is_dir()
        else []
    )
    assert images == [
        "01_implantacao.png",
        "02_administrativo.png",
        "03_residencial.png",
        "04_servicos.png",
    ]


def test_bim00_task_records_input_blocker_without_unlocking_r04():
    state = StateStore(ROOT / "PROJECT_STATE.yaml").load()
    registry = load_registry(ROOT / "state/task-graph.yaml")

    assert state.phase_id == "P4"
    assert state.phase_status.value == "BLOCKED_BY_INPUT"
    assert state.last_completed_task == "P3-T01"
    assert state.next_task == "P4-T01"
    assert state.selected_design == "AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"
    assert "SITE_TOPOGRAPHY:DEGRADING" in state.blockers
    assert "SITE_BOUNDARY:DEGRADING" in state.blockers
    assert "SITE_OCCUPANCY:DEGRADING" in state.blockers
    assert "REVIT_PROVIDER_UNREACHABLE:BLOCKING" in state.blockers
    assert "RUN003_TARGET_CHECKPOINT_UNBOUND:BLOCKING" in state.blockers
    assert "P1-T01" in registry.tasks
    assert registry.tasks["P1-T01"].status.value == "PASS"
    assert registry.tasks["P2-T01"].status.value == "PASS"
    assert registry.tasks["P3-T01"].status.value == "PASS"
    assert registry.tasks["P4-T01"].status.value == "BLOCKED_BY_INPUT"
    assert registry.ready_tasks() == []

    dashboard = (ROOT / "state/status.md").read_text(encoding="utf-8")
    assert "Phase: `P4` — bim-00" in dashboard
    assert "Phase status: `BLOCKED_BY_INPUT`" in dashboard
    assert "Next task: `P4-T01`" in dashboard
    assert "Last recorded task: `P3-T01`" in dashboard
    assert "`horizun-revit-mcp`: UNREACHABLE" in dashboard
    assert "Selected design: `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`" in dashboard
    assert "`P1`: 1/1 PASS" in dashboard
    assert "`P2`: 1/1 PASS" in dashboard
    assert "`P3`: 1/1 PASS" in dashboard
    assert "`P4`: 0/1 PASS" in dashboard
    assert "READY: (none)" in dashboard

    handoff = (ROOT / "state/HANDOFF.md").read_text(encoding="utf-8")
    normalized_handoff = " ".join(handoff.split())
    assert "Historical P4 continuation" in normalized_handoff
    assert "superseded by the active P4-T01 continuation above" in normalized_handoff

    superseded_tasks = [f"P08-CAN-T{number:02}" for number in range(9, 20)]
    assert all(task_id in registry.tasks for task_id in superseded_tasks)
    assert all(
        registry.tasks[task_id].status.value == "SUSPENDED"
        for task_id in superseded_tasks
    )
