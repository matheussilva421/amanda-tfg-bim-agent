import pytest
from pydantic import ValidationError


def _reference(**overrides):
    from amanda_agent.ingest.provenance import SourceReference

    values = {
        "source_id": "SRC-001",
        "source_hash": "a" * 64,
        "page": 2,
        "extraction_method": "selectable text",
        "confidence": 0.95,
        "note": "statement copied from the source",
    }
    values.update(overrides)
    return SourceReference(**values)


def test_source_fact_without_source_id_is_rejected():
    from amanda_agent.ingest.provenance import FactClass, ProvenanceRecord

    with pytest.raises(ValidationError, match="source_id"):
        ProvenanceRecord(
            statement_id="FACT-001",
            statement="The source states a fact.",
            fact_class=FactClass.SOURCE_FACT,
            source_refs=[_reference(source_id=None)],
        )


def test_source_fact_without_source_hash_is_rejected():
    from amanda_agent.ingest.provenance import FactClass, ProvenanceRecord

    with pytest.raises(ValidationError, match="source_hash"):
        ProvenanceRecord(
            statement_id="FACT-001-HASH",
            statement="The source states a fact.",
            fact_class=FactClass.SOURCE_FACT,
            source_refs=[_reference(source_hash=None)],
        )


def test_hypothesis_cannot_claim_source_fact_class():
    from amanda_agent.ingest.provenance import FactClass, ProvenanceRecord

    with pytest.raises(ValidationError, match="DESIGN_HYPOTHESIS"):
        ProvenanceRecord(
            statement_id="HYP-001",
            statement="A provisional design assumption.",
            fact_class=FactClass.SOURCE_FACT,
            hypothesis=True,
            source_refs=[_reference()],
        )

    hypothesis = ProvenanceRecord(
        statement_id="HYP-002",
        statement="A provisional design assumption.",
        fact_class=FactClass.DESIGN_HYPOTHESIS,
        hypothesis=True,
    )
    assert hypothesis.fact_class is FactClass.DESIGN_HYPOTHESIS


def test_disputed_source_statement_preserves_original_text():
    from amanda_agent.ingest.provenance import (
        FactClass,
        ProvenanceRecord,
        VerificationStatus,
    )

    record = ProvenanceRecord(
        statement_id="FACT-002",
        statement="The source states 42 people.",
        fact_class=FactClass.SOURCE_FACT,
        source_refs=[_reference()],
        verification_status=VerificationStatus.DISPUTED,
    )

    assert record.verification_status is VerificationStatus.DISPUTED
    assert record.statement == "The source states 42 people."
