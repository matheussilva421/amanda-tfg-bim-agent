"""Behavioral contracts for the verified regulation registry."""

from __future__ import annotations

import pytest

from amanda_agent.requirements.regulations import (
    RegulationRule,
    RegulationStatus,
    compile_derived_constraint,
)


def _rule(**overrides) -> RegulationRule:
    value = {
        "logical_id": "synthetic-rule-01",
        "title": "Synthetic numeric rule",
        "status": RegulationStatus.VERIFIED,
        "primary_source": "synthetic-primary-source",
        "source_version": "synthetic-v1",
        "source_date": "2031-04-05",
        "article": "synthetic-art-1",
        "map_reference": "synthetic-map-1",
        "extracted_rule": "The synthetic limit is 1.25 units.",
        "numeric_value": 1.25,
        "unit": "synthetic-unit",
        "scope": "synthetic-scope",
        "verification_evidence": ["synthetic-evidence:page-1"],
        "source_refs": ["synthetic-primary-source:page-1"],
    }
    value.update(overrides)
    return RegulationRule(**value)


def test_registry_exposes_the_required_statuses():
    assert {status.value for status in RegulationStatus} == {
        "IDENTIFIED",
        "SOURCE_ACQUIRED",
        "VERIFIED",
        "SUPERSEDED",
    }


def test_source_acquisition_alone_cannot_create_a_hard_constraint():
    rule = _rule(status=RegulationStatus.SOURCE_ACQUIRED)

    with pytest.raises(ValueError, match="VERIFIED"):
        compile_derived_constraint(rule)


@pytest.mark.parametrize(
    "missing",
    [
        "primary_source",
        "source_version",
        "source_date",
        "article",
        "map_reference",
        "extracted_rule",
        "unit",
        "scope",
        "verification_evidence",
    ],
)
def test_numeric_rule_requires_complete_verification_record(missing: str):
    value = _rule().model_dump()
    value[missing] = None if missing != "verification_evidence" else []
    rule = RegulationRule(**value)

    with pytest.raises(ValueError, match="incomplete"):
        compile_derived_constraint(rule)


def test_verified_numeric_rule_compiles_as_explicit_derived_constraint():
    compiled = compile_derived_constraint(_rule())

    assert compiled.fact_class == "DERIVED_CONSTRAINT"
    assert compiled.numeric_value == 1.25
    assert compiled.unit == "synthetic-unit"
    assert compiled.scope == "synthetic-scope"
    assert compiled.primary_source == "synthetic-primary-source"
    assert compiled.source_version == "synthetic-v1"
    assert compiled.article == "synthetic-art-1"
    assert compiled.map_reference == "synthetic-map-1"
    assert compiled.extracted_rule == "The synthetic limit is 1.25 units."
    assert compiled.source_refs == ["synthetic-primary-source:page-1"]
    assert compiled.verification_evidence == ["synthetic-evidence:page-1"]
