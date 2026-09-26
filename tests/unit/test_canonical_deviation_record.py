import hashlib
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs" / "decisions" / "CANONICAL_DEVIATIONS.yaml"


def test_run003_administration_footprint_divergence_is_formally_open():
    data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    record = next(
        row for row in data["canonical_deviations"]
        if row["id"] == "CANONICAL_DEVIATION-ADM-001"
    )

    assert record["status"] == "OPEN_FOR_REVIEW"
    assert record["affected_elements"] == [
        {"mark": "R04-ADMIN-FLOOR-L1", "element_id": 329929},
        {"mark": "R04-ADMIN-FLOOR-L2", "element_id": 329936},
    ]
    assert record["canonical_board"]["board_id"] == "Board 02"
    assert record["canonical_board"]["source_path"] == "docs/source/canonical/02_administrativo.png"
    assert record["canonical_board"]["approximate_footprint_m2_per_floor"] == 200
    assert record["observed"]["area_m2_per_floor"] == pytest.approx(237.407316)
    assert record["observed"]["delta_m2_per_floor"] == pytest.approx(37.407316)
    assert record["observed"]["delta_percent"] == pytest.approx(18.703658)
    assert record["alternatives_considered"]
    assert record["decision"]["selected_alternative"] is None
    assert record["decision"]["approval_received"] is False
    assert record["decision"]["status"] == "AMANDA_REVIEW_REQUIRED"
    assert record["verifiable_reason"]
    assert len(record["alternatives_considered"]) >= 2
    assert record["impact"]
    assert "programa_necessidades.pdf" in record["official_program"]["source_path"]
    assert record["official_program"]["quantitative_program_changed"] is False

    assert {artifact["role"] for artifact in record["input_hashes"]} >= {
        "canonical_board_02",
        "official_program",
        "selected_run003_source_geometry",
    }
    assert {artifact["role"] for artifact in record["output_hashes"]} == {
        "saved_and_reopened_r04_run003_checkpoint"
    }

    for artifact in record["input_hashes"] + record["output_hashes"]:
        path = ROOT / artifact["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == artifact["sha256"], artifact["path"]
