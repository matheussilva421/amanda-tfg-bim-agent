"""Typed lifecycle and desired-state models for the BIM compiler."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .provenance import BimProvenance


class BimStage(StrEnum):
    """Formal Revit stage names in their only valid progression order."""

    R00 = "EMPTY_SANDBOX"
    R01 = "PROJECT_INITIALIZED"
    R02 = "SITE"
    R03 = "LEVELS_AND_REFERENCES"
    R04 = "MASSING"
    R05 = "ARCHITECTURAL_SHELL"
    R06 = "INTERNAL_LAYOUT"
    R07 = "OPENINGS"
    R08 = "ROOMS"
    R09 = "ACCESSIBILITY"
    R10 = "FURNITURE"
    R11 = "LANDSCAPE"
    R12 = "MATERIALS"
    R13 = "DOCUMENTATION"
    R14 = "QA"
    R15 = "RELEASE_CANDIDATE"
    R16 = "GOLDEN"

    # Descriptive aliases are convenient for callers that do not use stage
    # numbers. Enum aliases do not change iteration order or cardinality.
    EMPTY_SANDBOX = R00
    PROJECT_INITIALIZED = R01
    SITE = R02
    LEVELS_AND_REFERENCES = R03
    MASSING = R04
    ARCHITECTURAL_SHELL = R05
    INTERNAL_LAYOUT = R06
    OPENINGS = R07
    ROOMS = R08
    ACCESSIBILITY = R09
    FURNITURE = R10
    LANDSCAPE = R11
    MATERIALS = R12
    DOCUMENTATION = R13
    QA = R14
    RELEASE_CANDIDATE = R15
    GOLDEN = R16


BIMStage = BimStage
Stage = BimStage


class DesiredElement(BaseModel):
    """One managed element the compiler wants Revit to contain."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    geometry: dict[str, Any]
    properties: dict[str, Any]
    requirement_id: str = Field(min_length=1)
    design_option: str = Field(min_length=1)
    generation_run: str = Field(min_length=1)
    provenance: BimProvenance | None = None

    @model_validator(mode="after")
    def align_provenance(self) -> DesiredElement:
        """Keep an explicitly supplied provenance record consistent."""

        if self.provenance is not None:
            if self.provenance.requirement_id != self.requirement_id:
                raise ValueError("provenance requirement_id does not match element")
            if self.provenance.design_option != self.design_option:
                raise ValueError("provenance design_option does not match element")
            if self.provenance.generation_run != self.generation_run:
                raise ValueError("provenance generation_run does not match element")
        return self


class DesiredState(BaseModel):
    """A desired model with unique managed logical identities."""

    model_config = ConfigDict(extra="forbid")

    elements: list[DesiredElement] = Field(default_factory=list)
    stage: BimStage = BimStage.R00
    generation_run: str | None = Field(default=None, min_length=1)
    model_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_logical_ids(self) -> DesiredState:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for element in self.elements:
            if element.logical_id in seen:
                duplicates.add(element.logical_id)
            seen.add(element.logical_id)
        if duplicates:
            joined = ", ".join(sorted(duplicates))
            raise ValueError(f"duplicate logical_id: {joined}")
        return self

    def by_logical_id(self) -> dict[str, DesiredElement]:
        """Return a stable lookup of managed elements."""

        return {element.logical_id: element for element in self.elements}


class StageRecord(BaseModel):
    """A stage marker suitable for serializing compiler progress."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    stage: BimStage
    checkpoint_sha256: str | None = None
    generation_run: str = Field(min_length=1)


__all__ = [
    "BIMStage",
    "BimStage",
    "DesiredElement",
    "DesiredState",
    "Stage",
    "StageRecord",
]
