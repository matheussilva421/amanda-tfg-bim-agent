from __future__ import annotations

import ast
from pathlib import Path

from scripts.qa_layout import run_checks

ROOT = Path(__file__).resolve().parents[2]


def test_program_reconciliation_check_passes_for_canonical_internal_rooms(
    canonical_program, canonical_layout, canonical_profile
) -> None:
    reconciliation = next(
        item
        for item in run_checks(canonical_program, canonical_layout, canonical_profile)
        if item["check"] == "program.reconciliation"
    )

    assert reconciliation["status"] == "PASS"


def test_qa_keeps_unverified_geometry_gates_blocked(
    canonical_program, canonical_layout, canonical_profile
) -> None:
    checks = {
        item["check"]: item
        for item in run_checks(canonical_program, canonical_layout, canonical_profile)
    }

    assert checks["canonical.CANON-011"]["status"] == "BLOCKED"
    assert checks["program.enclosed_estimate"]["status"] == "BLOCKED"
    assert checks["program.covered_estimate"]["status"] == "BLOCKED"
    assert checks["site.fit"]["status"] == "BLOCKED"
    assert checks["program.capacity_is_20"]["status"] == "PASS"
    assert checks["program.external_total_is_260"]["status"] == "PASS"


def test_active_qa_and_drawing_entrypoints_do_not_import_legacy_builder():
    entrypoints = (
        ROOT / "scripts" / "qa_layout.py",
        ROOT / "scripts" / "render_study_sheets.py",
    )
    for path in entrypoints:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        ]
        called = [
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        assert "build_courtyard_layout" not in imported, path
        assert "build_courtyard_layout" not in called, path
