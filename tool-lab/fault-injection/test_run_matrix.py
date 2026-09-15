from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run_matrix.py")
SPEC = importlib.util.spec_from_file_location("t17_run_matrix", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
run_matrix = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run_matrix
SPEC.loader.exec_module(run_matrix)


MATRIX_PATH = Path(__file__).with_name("matrix.yaml")
EXPECTED_IDS = {
    "FI-001",
    "FI-002",
    "FI-003",
    "FI-004",
    "FI-005",
    "FI-006",
    "FI-007",
    "FI-008",
}


def test_matrix_declares_all_eight_cases_with_required_fields() -> None:
    matrix = run_matrix.load_matrix(MATRIX_PATH)

    assert {case["id"] for case in matrix["cases"]} == EXPECTED_IDS
    required = {
        "id",
        "description",
        "precondition",
        "action",
        "expected_result",
        "expected_error_class",
        "requires_revit",
        "human_gate",
        "proof_layer",
    }
    for case in matrix["cases"]:
        assert required <= set(case)
        assert case["requires_revit"] is case["human_gate"]


def test_runner_executes_offline_cases_and_skips_revit_cases(tmp_path: Path) -> None:
    result_path = tmp_path / "fault-injection-results.json"
    breaker_path = tmp_path / "breaker-state.yaml"

    report = run_matrix.run_matrix(
        MATRIX_PATH,
        result_path,
        target=run_matrix.TargetConfig(name="focused-test-target"),
        breaker_state=breaker_path,
    )

    by_id = {item["id"]: item for item in report["cases"]}
    assert {item["status"] for item in report["cases"] if item["requires_revit"]} == {
        "SKIPPED_NEEDS_REVIT"
    }
    assert by_id["FI-004"]["status"] == "PASS"
    assert by_id["FI-005"]["status"] == "PASS"
    assert by_id["FI-007"]["status"] == "PASS"
    assert by_id["FI-008"]["status"] == "PASS"
    assert report["summary"] == {
        "total": 8,
        "pass": 4,
        "fail": 0,
        "blocked": 0,
        "skipped_needs_revit": 4,
    }
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    assert saved["cases"] == report["cases"]
    assert breaker_path.exists()


def test_timeout_case_verifies_before_retry(tmp_path: Path) -> None:
    case = next(
        item
        for item in run_matrix.load_matrix(MATRIX_PATH)["cases"]
        if item["id"] == "FI-008"
    )

    result = run_matrix.execute_case(
        case,
        run_matrix.TargetConfig(name="timeout-test-target"),
        breaker_state=tmp_path / "breaker-state.yaml",
    )

    assert result["status"] == "PASS"
    assert result["expected_error_class"] == "E03"
    assert result["observations"]["verified_before_retry"] is True
    assert result["observations"]["retry_attempted"] is False
