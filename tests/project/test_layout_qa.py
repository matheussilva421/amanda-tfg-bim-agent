from __future__ import annotations

from scripts.qa_layout import run_checks


def test_layout_reconciliation_scopes_to_observed_internal_rooms(
    canonical_program, canonical_layout, canonical_profile
):
    checks = run_checks(canonical_program, canonical_layout, canonical_profile)

    reconciliation = next(
        item for item in checks if item["check"] == "program.reconciliation"
    )
    assert reconciliation["status"] == "PASS"

    external = next(
        item for item in checks if item["check"] == "program.external_total_is_260"
    )
    assert external["status"] == "PASS"
