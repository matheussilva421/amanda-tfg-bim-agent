from __future__ import annotations

import json
from pathlib import Path

from scripts.qa_layout import run_checks
from amanda_agent.design.architectural_layout import build_courtyard_layout


ROOT = Path(__file__).resolve().parents[2]


def test_layout_reconciliation_scopes_to_observed_internal_rooms():
    program = json.loads(
        (ROOT / "project" / "requirements" / "program.json").read_text(
            encoding="utf-8"
        )
    )
    layout = build_courtyard_layout(program)

    checks = run_checks(program, layout)

    reconciliation = next(
        item for item in checks if item["check"] == "program.reconciliation"
    )
    assert reconciliation["status"] == "PASS"
