import hashlib
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs" / "decisions" / "CANONICAL_DEVIATIONS.yaml"


def test_run003_administration_footprint_is_reconciled_in_reversible_study():
    data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    record = next(
        row for row in data["canonical_deviations"]
        if row["id"] == "CANONICAL_DEVIATION-ADM-001"
    )

    assert record["status"] == "RESOLVED_FOR_STUDY"
    assert record["affected_elements"] == [
        {"mark": "MASS-ADMIN_ACOLHIMENTO", "element_id": 328657},
        {"mark": "R04-ADMIN-FLOOR-L1", "element_id": 331163},
        {"mark": "R04-ADMIN-FLOOR-L2", "element_id": 331170},
    ]
    assert record["canonical_board"]["board_id"] == "Board 02"
    assert record["canonical_board"]["source_path"] == "docs/source/canonical/02_administrativo.png"
    assert record["canonical_board"]["approximate_footprint_m2_per_floor"] == 200
    assert record["observed"]["area_m2_per_floor"] == pytest.approx(200.0)
    assert record["observed"]["delta_m2_per_floor"] == pytest.approx(0.0)
    assert record["observed"]["delta_percent"] == pytest.approx(0.0)
    assert record["observed"]["prior_checkpoint_area_m2_per_floor"] == pytest.approx(237.407316)
    assert record["alternatives_considered"]
    assert record["decision"]["selected_alternative"] == "refit_to_board_approximation"
    assert record["decision"]["approval_received"] is False
    assert record["decision"]["status"] == "RESOLVED_BY_DELEGATED_STUDY_RECONCILIATION"
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
    assert {artifact["role"] for artifact in record["input_hashes"]} >= {
        "p6_pre_replacement_checkpoint",
    }
    assert {artifact["role"] for artifact in record["output_hashes"]} == {
        "saved_and_reopened_p6_t01_run003_checkpoint"
    }

    for artifact in record["input_hashes"] + record["output_hashes"]:
        path = ROOT / artifact["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == artifact["sha256"], artifact["path"]
