from __future__ import annotations

import subprocess
from pathlib import Path

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


def test_no_generated_zip_package_is_tracked():
    # Catches generated plan packages being committed as repository sources.
    assert _git("ls-files", "*.zip") == []


def test_active_entrypoints_do_not_route_to_stale_instructions():
    # Catches active entrypoints routing readers to obsolete three-board instructions.
    active_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in ACTIVE_DOCS
        if path.is_file() and path.suffix in {".md", ".yaml"}
    )
    hits = [term for term in STALE_ACTIVE_TERMS if term in active_text]
    assert hits == []


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
