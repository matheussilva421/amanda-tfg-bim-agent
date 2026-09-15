"""Contract tests for the shipped regulation registry document."""

from __future__ import annotations

from pathlib import Path

import yaml

from amanda_agent.requirements.regulations import (
    RegulationRegistry,
    RegulationRule,
    RegulationStatus,
)

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "project" / "regulations" / "registry.yaml"


def _document() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


def _registry() -> RegulationRegistry:
    rules = [
        RegulationRule(**payload) for payload in _document()["rules"]
    ]
    registry = RegulationRegistry()
    for rule in rules:
        registry.add(rule)
    return registry


def test_registry_document_exists_and_declares_a_schema_version():
    document = _document()
    assert document["schema_version"] == 1
    assert document["rules"]


def test_every_rule_carries_a_primary_source_and_a_source_reference():
    for rule in _registry().rules:
        assert rule.primary_source
        assert rule.source_refs
        assert rule.article or rule.status is RegulationStatus.IDENTIFIED


def test_no_numeric_rule_reaches_hard_constraint_while_unverified():
    registry = _registry()
    numeric = [rule for rule in registry.rules if rule.numeric_value is not None]
    assert numeric, "the corrected table supplies numeric parameters"
    unverified = [
        rule for rule in numeric if rule.status is not RegulationStatus.VERIFIED
    ]
    assert unverified == []
    # Every numeric rule that is present must compile, proving the record is
    # complete enough to be a hard constraint rather than a memory of one.
    compiled = registry.compile_derived_constraints()
    assert len(compiled) == len(numeric)


def test_regulation_names_identified_without_numeric_values_are_kept():
    identified = [
        rule
        for rule in _registry().rules
        if rule.status is RegulationStatus.IDENTIFIED
    ]
    assert identified
    for rule in identified:
        assert rule.numeric_value is None
        assert rule.primary_source


def test_superseding_amendments_are_recorded_not_ignored():
    ids = {rule.logical_id for rule in _registry().rules}
    assert "LC-208-2022" in ids
    text = REGISTRY.read_text(encoding="utf-8")
    assert "258/2024" in text
    assert "261/2025" in text

