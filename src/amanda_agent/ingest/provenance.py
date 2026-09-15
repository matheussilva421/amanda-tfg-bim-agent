"""Typed provenance records for source assertions and design reasoning."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class FactClass(StrEnum):
    SOURCE_FACT = "SOURCE_FACT"
    DERIVED_CONSTRAINT = "DERIVED_CONSTRAINT"
    DESIGN_HYPOTHESIS = "DESIGN_HYPOTHESIS"


class VerificationStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    SUPERSEDED = "SUPERSEDED"


class AdoptionStatus(StrEnum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class SourceReference(BaseModel):
    """A precise pointer to the source material used by a statement."""

    source_id: str | None = Field(default=None, min_length=1)
    source_hash: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    locator: str | None = None
    page: int | None = Field(default=None, ge=1)
    paragraph: str | int | None = None
    table: str | int | None = None
    sheet: str | None = None
    cell: str | None = None
    extraction_method: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    note: str = ""
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    adoption_status: AdoptionStatus = AdoptionStatus.PROPOSED

    @model_validator(mode="before")
    @classmethod
    def accept_hash_aliases(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if "source_hash" not in values:
            for alias in ("sha256", "source_sha256"):
                if alias in values:
                    values["source_hash"] = values[alias]
                    break
        return values

    @model_validator(mode="after")
    def require_locator(self) -> SourceReference:
        if not any(
            value is not None
            for value in (
                self.locator,
                self.page,
                self.paragraph,
                self.table,
                self.sheet,
                self.cell,
            )
        ):
            raise ValueError(
                "a source reference needs a page, paragraph, table, sheet or cell locator"
            )
        return self

    @property
    def sha256(self) -> str | None:
        """Compatibility accessor for callers that name the hash ``sha256``."""
        return self.source_hash

    @property
    def source_sha256(self) -> str | None:
        return self.source_hash


class ProvenanceRecord(BaseModel):
    """One immutable statement with an explicit epistemic classification."""

    statement_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    fact_class: FactClass
    source_refs: list[SourceReference] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    adoption_status: AdoptionStatus = AdoptionStatus.PROPOSED
    hypothesis: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def accept_statement_aliases(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if "statement" not in values:
            for alias in ("claim", "text"):
                if alias in values:
                    values["statement"] = values[alias]
                    break
        if "source_refs" not in values:
            reference = values.get("source_reference", values.get("source_ref"))
        else:
            reference = None
        if "source_refs" not in values and reference is not None:
            values["source_refs"] = (
                reference if isinstance(reference, list) else [reference]
            )
        return values

    @model_validator(mode="after")
    def validate_classification(self) -> ProvenanceRecord:
        if self.fact_class is FactClass.SOURCE_FACT:
            if not self.source_refs:
                raise ValueError("SOURCE_FACT requires source_refs")
            missing_source_id = [
                reference for reference in self.source_refs if not reference.source_id
            ]
            if missing_source_id:
                raise ValueError("SOURCE_FACT source_refs require source_id")
            missing_source_hash = [
                reference for reference in self.source_refs if not reference.source_hash
            ]
            if missing_source_hash:
                raise ValueError("SOURCE_FACT source_refs require source_hash")

        if (
            self.hypothesis is True
            and self.fact_class is not FactClass.DESIGN_HYPOTHESIS
        ):
            raise ValueError("a hypothesis must use DESIGN_HYPOTHESIS")
        if self.fact_class is FactClass.DESIGN_HYPOTHESIS:
            if self.hypothesis is False:
                raise ValueError(
                    "DESIGN_HYPOTHESIS cannot claim a non-hypothesis class"
                )
            self.hypothesis = True
        return self

    @property
    def source_reference(self) -> SourceReference | None:
        return self.source_refs[0] if self.source_refs else None


SourceStatement = ProvenanceRecord
ProvenanceStatement = ProvenanceRecord
Fact = ProvenanceRecord
