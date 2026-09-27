"""Exact, checkpoint-bound reconciliation for the RUN-003 P6 readback."""

from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
RECONCILIATION = (
    ROOT
    / "revit"
    / "production"
    / "evidence"
    / "AMANDA-RUN-003-R04"
    / "p6-readback-fingerprint-reconciliation.json"
)


def _api():
    try:
        return importlib.import_module(
            "amanda_agent.production.p6_fingerprint_reconciliation"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"P6 exact-readback reconciliation gate is missing: {exc}")


def _fixture():
    api = _api()
    auth_api = importlib.import_module("amanda_agent.production.run003_study")
    authorization = auth_api.load_run003_study_authorization(ROOT)
    record = api.load_p6_fingerprint_reconciliation(ROOT, authorization)
    diagnostic_path = ROOT / record.diagnostic_path
    diagnostic = json.loads(diagnostic_path.read_text(encoding="utf-8"))
    rows = copy.deepcopy(diagnostic["readback"]["rows"])
    shared = {
        "matched_total": 25,
        "returned": 25,
        "coverage_complete": True,
        "unreadable_total": 0,
        "summary": {"by_category": {"Massa": 7, "Pisos": 14, "Telhados": 4}},
        "rows": rows,
    }
    compact = {
        **shared,
        "rows": copy.deepcopy(rows),
        "result_set_fingerprint": record.observed_compact_fingerprint,
    }
    detailed = {**shared, "result_set_fingerprint": record.observed_detailed_fingerprint}
    return api, authorization, record, compact, detailed


def test_exact_p6_diagnostic_reconciles_both_query_signatures_and_all_rows():
    api, authorization, record, compact, detailed = _fixture()

    result = api.verify_reconciled_p6_readback(
        ROOT,
        authorization,
        compact,
        detailed,
        record=record,
    )

    assert result["status"] == "RECONCILED_EXACT_READBACK_ONLY"
    assert result["historical_accepted_fingerprint"] == "4636abc6b294829b"
    assert result["observed_compact_fingerprint"] == "2f12a578c8451f3f"
    assert result["observed_detailed_fingerprint"] == "1aac5d79b05b159a"
    assert result["row_count"] == 25
    assert result["rows_sha256"] == (
        "3732c3c44c405a6453df8157243b7695b442b9969c979c141c6e829011940c0d"
    )
    assert result["p6_acceptance_gate_passed"] is False
    assert result["model_write_performed"] is False


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("compact_fingerprint", "compact fingerprint"),
        ("detailed_fingerprint", "detailed fingerprint"),
        ("compact_row_geometry", "compact/detailed row"),
        ("row_geometry", "rows_sha256"),
        ("checkpoint_sha", "checkpoint SHA-256"),
        ("diagnostic_bytes", "diagnostic SHA-256"),
    ],
)
def test_reconciliation_fails_closed_when_any_exact_binding_changes(
    tmp_path, change, message
):
    api, authorization, record, compact, detailed = _fixture()
    if change == "compact_fingerprint":
        compact["result_set_fingerprint"] = "unexpected"
    elif change == "detailed_fingerprint":
        detailed["result_set_fingerprint"] = "unexpected"
    elif change == "compact_row_geometry":
        compact["rows"][0]["bounding_box"]["max"][0] += 0.001
    elif change == "row_geometry":
        detailed["rows"][0]["bounding_box"]["max"][0] += 0.001
    elif change == "checkpoint_sha":
        authorization = SimpleNamespace(
            **{
                **authorization.model_dump(),
                "checkpoint_sha256": "0" * 64,
            }
        )
    elif change == "diagnostic_bytes":
        diagnostic = tmp_path / record.diagnostic_path
        diagnostic.parent.mkdir(parents=True)
        source = ROOT / record.diagnostic_path
        diagnostic.write_bytes(source.read_bytes() + b" ")
        addendum = tmp_path / RECONCILIATION.relative_to(ROOT)
        addendum.parent.mkdir(parents=True, exist_ok=True)
        addendum.write_bytes(RECONCILIATION.read_bytes())
        with pytest.raises(api.P6FingerprintReconciliationError, match=message):
            api.load_p6_fingerprint_reconciliation(
                tmp_path, authorization, reconciliation_path=addendum
            )
        return

    with pytest.raises(api.P6FingerprintReconciliationError, match=message):
        api.verify_reconciled_p6_readback(
            ROOT, authorization, compact, detailed, record=record
        )
