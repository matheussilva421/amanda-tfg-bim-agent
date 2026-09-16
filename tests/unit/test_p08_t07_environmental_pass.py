from __future__ import annotations

import json
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[2] / "design-engine" / "runs" / "AMANDA-RUN-001"


def test_environmental_pass_records_source_backed_heuristics_for_all_finalists() -> None:
    artifact_path = RUN_ROOT / "environmental-pass.json"
    assert artifact_path.exists(), "P08-T07 environmental pass artifact is missing"

    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert artifact["run_id"] == "AMANDA-RUN-001"
    assert artifact["stage"] == "P08-T07"
    assert artifact["capability_check"]["environmental_simulation_registered"] is False
    assert artifact["comparison_matrix"]["status"] == "MISSING"
    assert artifact["inputs"]["true_north_deg"]["value"] == 0.0
    assert artifact["inputs"]["true_north_deg"]["status"] == "PLANAR_PLACEHOLDER"
    assert artifact["inputs"]["preferred_solar_orientation_deg"]["value"] == 90.0
    assert artifact["inputs"]["wind_direction_deg"]["value"] == 135.0

    finalists = artifact["finalists"]
    assert [item["solution_id"] for item in finalists] == [
        "AMANDA-RUN-001-F01",
        "AMANDA-RUN-001-F02",
    ]
    assert len(finalists) <= 5
    for item in finalists:
        assert item["classification"] == "HEURISTIC"
        assert item["labels"] == {"solar": "HEURISTIC", "ventilation": "HEURISTIC"}
        assert {
            key: item["raw_metrics"][key]
            for key in ("solar_heuristic", "ventilation_heuristic")
        } == {
            "solar_heuristic": 0.5,
            "ventilation_heuristic": 0.3055456351736995,
        }
        assert item["weighted_total"] == 0.7888960184315897
        assert item["weighted_contributions"]["solar_heuristic"] == 0.03
        assert item["weighted_contributions"]["ventilation_heuristic"] == 0.018332738110421968

    limitations = " ".join(artifact["limitations"])
    assert "CFD" in limitations
    assert "Radiance" in limitations
    assert "SITE_TRUE_NORTH" in limitations
    assert "DEGRADING" in limitations
