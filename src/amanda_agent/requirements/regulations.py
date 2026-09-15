"""Evidence-gated registry for normative regulation rules."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegulationStatus(StrEnum):
    IDENTIFIED = "IDENTIFIED"
    SOURCE_ACQUIRED = "SOURCE_ACQUIRED"
    VERIFIED = "VERIFIED"
    SUPERSEDED = "SUPERSEDED"


class RegulationRule(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str
    title: str
    status: RegulationStatus = RegulationStatus.IDENTIFIED
    primary_source: str | None = None
    source_version: str | None = None
    source_date: date | None = None
    article: str | None = None
    map_reference: str | None = None
    extracted_rule: str | None = None
    numeric_value: float | None = Field(default=None, allow_inf_nan=False)
    unit: str | None = None
    scope: str | None = None
    verification_evidence: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)

    @field_validator(
        "logical_id",
        "title",
        "primary_source",
        "source_version",
        "article",
        "map_reference",
        "extracted_rule",
        "unit",
        "scope",
        mode="before",
    )
    @classmethod
    def reject_empty_text(cls, value: Any) -> Any:
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError("text fields cannot be empty")
        return value

    @field_validator("verification_evidence", "source_refs", mode="before")
    @classmethod
    def reject_empty_references(cls, value: Any) -> Any:
        if value is None:
            return value
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError("references cannot be empty")
        return value


class DerivedConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact_class: Literal["DERIVED_CONSTRAINT"] = "DERIVED_CONSTRAINT"
    logical_id: str
    source_rule_id: str
    numeric_value: float = Field(allow_inf_nan=False)
    unit: str
    scope: str
    primary_source: str
    source_version: str
    source_date: date
    article: str
    map_reference: str
    extracted_rule: str
    source_refs: list[str] = Field(min_length=1)
    verification_evidence: list[str] = Field(min_length=1)


_REQUIRED_VERIFICATION_FIELDS = (
    "primary_source",
    "source_version",
    "source_date",
    "article",
    "map_reference",
    "extracted_rule",
    "unit",
    "scope",
    "verification_evidence",
    "source_refs",
)


def compile_derived_constraint(rule: RegulationRule) -> DerivedConstraint:
    """Compile only a verified, complete numeric rule into a hard constraint."""
    if rule.status is not RegulationStatus.VERIFIED:
        raise ValueError(
            "numeric rule must have status VERIFIED before becoming "
            "DERIVED_CONSTRAINT"
        )
    missing = [
        field_name
        for field_name in _REQUIRED_VERIFICATION_FIELDS
        if not getattr(rule, field_name)
    ]
    if rule.numeric_value is None:
        missing.append("numeric_value")
    if missing:
        raise ValueError(
            "incomplete verification record: " + ", ".join(missing)
        )
    return DerivedConstraint(
        logical_id=rule.logical_id,
        source_rule_id=rule.logical_id,
        numeric_value=rule.numeric_value,
        unit=rule.unit,
        scope=rule.scope,
        primary_source=rule.primary_source,
        source_version=rule.source_version,
        source_date=rule.source_date,
        article=rule.article,
        map_reference=rule.map_reference,
        extracted_rule=rule.extracted_rule,
        source_refs=rule.source_refs,
        verification_evidence=rule.verification_evidence,
    )


class RegulationRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: list[RegulationRule] = Field(default_factory=list)

    def add(self, rule: RegulationRule) -> None:
        if any(existing.logical_id == rule.logical_id for existing in self.rules):
            raise ValueError(f"duplicate logical_id: {rule.logical_id}")
        self.rules.append(rule)

    def compile_derived_constraints(self) -> list[DerivedConstraint]:
        """Compile every numeric rule; non-numeric rows stay non-constraints.

        A registry legitimately mixes an umbrella law entry, identified
        regulations awaiting their primary text and verified numeric
        parameters.  Only the numeric rows can become a hard constraint, so
        only they are compiled here; a numeric row that is not verified still
        raises.
        """
        return [
            compile_derived_constraint(rule)
            for rule in self.rules
            if rule.numeric_value is not None
        ]


__all__ = [
    "DerivedConstraint",
    "RegulationRegistry",
    "RegulationRule",
    "RegulationStatus",
    "compile_derived_constraint",
]
