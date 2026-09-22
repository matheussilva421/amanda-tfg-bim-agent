from __future__ import annotations

import json
from pathlib import Path

from amanda_agent.design.architectural_layout import build_courtyard_layout
from scripts.qa_layout import run_checks


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_program_reconciliation_check_passes_for_observed_internal_rooms() -> None:
    program = json.loads(
        (REPOSITORY_ROOT / "project" / "requirements" / "program.json").read_text(
            encoding="utf-8"
        )
    )
    layout = build_courtyard_layout(program)

    reconciliation = next(
        item for item in run_checks(program, layout) if item["check"] == "program.reconciliation"
    )

    assert reconciliation["status"] == "PASS"
