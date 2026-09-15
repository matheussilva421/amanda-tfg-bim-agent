from pathlib import Path

import yaml

from amanda_agent.ingest.provenance import (
    FactClass,
    ProvenanceRecord,
    SourceReference,
)

ROOT = Path(__file__).parents[2]
SOURCE_PRINCIPLES_PATH = ROOT / "project" / "requirements" / "source-principles.yaml"
DESIGN_HYPOTHESES_PATH = ROOT / "project" / "requirements" / "design-hypotheses.yaml"


def _load_records(path: Path, collection: str) -> list[ProvenanceRecord]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [ProvenanceRecord.model_validate(item) for item in payload[collection]]


def test_source_principles_are_source_facts_with_complete_provenance():
    records = _load_records(SOURCE_PRINCIPLES_PATH, "principles")

    assert records
    for record in records:
        assert record.fact_class is FactClass.SOURCE_FACT
        assert record.hypothesis is not True
        assert record.source_refs
        assert all(isinstance(reference, SourceReference) for reference in record.source_refs)
        assert all(reference.source_id == "SRC-TFG-001" for reference in record.source_refs)
        assert all(reference.source_hash for reference in record.source_refs)
        assert all(reference.page is not None for reference in record.source_refs)


def test_source_principles_prohibit_design_hypotheses():
    payload = yaml.safe_load(
        SOURCE_PRINCIPLES_PATH.read_text(encoding="utf-8")
    )

    assert all(
        item.get("fact_class") != FactClass.DESIGN_HYPOTHESIS.value
        for item in payload["principles"]
    )


def test_design_hypotheses_are_explicitly_classified():
    records = _load_records(DESIGN_HYPOTHESES_PATH, "hypotheses")

    assert records
    for record in records:
        assert record.fact_class is FactClass.DESIGN_HYPOTHESIS
        assert record.hypothesis is True
