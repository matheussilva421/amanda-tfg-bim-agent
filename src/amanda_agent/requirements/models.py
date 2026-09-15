"""Canonical and draft schemas for the program of requirements."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class UnknownRequirementFieldError(ValueError):
    """Raised when a draft still lacks a field required by the canonical model."""


class _RequirementModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("logical_id", "name", "sector", mode="before", check_fields=False)
    @classmethod
    def non_empty_text(cls, value: Any) -> Any:
        if value is None:
            return value
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be a non-empty string")
        return value

    @field_validator("source_refs", mode="before", check_fields=False)
    @classmethod
    def non_empty_source_refs(cls, value: Any) -> Any:
        if value is None:
            return value
        if not isinstance(value, list) or not value:
            raise ValueError("source_refs must contain at least one reference")
        if any(not isinstance(ref, str) or not ref.strip() for ref in value):
            raise ValueError("source_refs cannot contain empty references")
        return value


class SpaceRequirement(_RequirementModel):
    logical_id: str
    name: str
    sector: str
    quantity: int = Field(ge=1)
    target_area_m2: float = Field(gt=0, allow_inf_nan=False)
    min_area_m2: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    max_area_m2: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    privacy_level: int | None = Field(default=None, ge=0, le=5)
    accessible: bool | None = None
    source_refs: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_range(self) -> SpaceRequirement:
        if (
            self.min_area_m2 is not None
            and self.max_area_m2 is not None
            and self.min_area_m2 > self.max_area_m2
        ):
            raise ValueError("minimum area exceeds maximum area")
        if self.min_area_m2 is not None and self.target_area_m2 < self.min_area_m2:
            raise ValueError("target below minimum")
        if self.max_area_m2 is not None and self.target_area_m2 > self.max_area_m2:
            raise ValueError("target above maximum")
        return self


class SectorRequirement(_RequirementModel):
    logical_id: str
    name: str
    spaces: list[SpaceRequirement] = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)


class ProgramRequirementSet(_RequirementModel):
    sectors: list[SectorRequirement] = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_logical_ids(self) -> ProgramRequirementSet:
        seen: set[str] = set()
        for sector in self.sectors:
            identifiers = [sector.logical_id] + [
                space.logical_id for space in sector.spaces
            ]
            for logical_id in identifiers:
                if logical_id in seen:
                    raise ValueError(f"duplicate logical_id: {logical_id}")
                seen.add(logical_id)
        return self


def _require_known(value: Any, fields: tuple[str, ...], *, prefix: str = "") -> None:
    for field_name in fields:
        if value.get(field_name) is None:
            location = f"{prefix}.{field_name}" if prefix else field_name
            raise UnknownRequirementFieldError(
                f"unknown required requirement field: {location}"
            )


class _DraftRequirementModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("logical_id", "name", "sector", mode="before", check_fields=False)
    @classmethod
    def non_empty_known_text(cls, value: Any) -> Any:
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError("must be a non-empty string when supplied")
        return value

    @field_validator("source_refs", mode="before", check_fields=False)
    @classmethod
    def non_empty_known_source_refs(cls, value: Any) -> Any:
        if value is not None and (
            not isinstance(value, list)
            or any(not isinstance(ref, str) or not ref.strip() for ref in value)
        ):
            raise ValueError("source_refs cannot contain empty references")
        return value


class DraftSpaceRequirement(_DraftRequirementModel):
    logical_id: str | None = None
    name: str | None = None
    sector: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    target_area_m2: float | None = Field(
        default=None, gt=0, allow_inf_nan=False
    )
    min_area_m2: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    max_area_m2: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    privacy_level: int | None = Field(default=None, ge=0, le=5)
    accessible: bool | None = None
    source_refs: list[str] | None = None

    def to_canonical(self) -> SpaceRequirement:
        values = self.model_dump()
        _require_known(
            values,
            (
                "logical_id",
                "name",
                "sector",
                "quantity",
                "target_area_m2",
                "source_refs",
            ),
        )
        return SpaceRequirement(**values)

    compile = to_canonical


class DraftSectorRequirement(_DraftRequirementModel):
    logical_id: str | None = None
    name: str | None = None
    spaces: list[DraftSpaceRequirement] | None = None
    source_refs: list[str] | None = None

    def to_canonical(self) -> SectorRequirement:
        values = self.model_dump()
        _require_known(values, ("logical_id", "name", "spaces", "source_refs"))
        spaces = [space.to_canonical() for space in self.spaces or []]
        return SectorRequirement(
            logical_id=values["logical_id"],
            name=values["name"],
            spaces=spaces,
            source_refs=values["source_refs"],
        )

    compile = to_canonical


class DraftProgramRequirementSet(_DraftRequirementModel):
    sectors: list[DraftSectorRequirement] | None = None
    source_refs: list[str] | None = None

    def to_canonical(self) -> ProgramRequirementSet:
        values = self.model_dump()
        _require_known(values, ("sectors", "source_refs"))
        sectors = [sector.to_canonical() for sector in self.sectors or []]
        return ProgramRequirementSet(
            sectors=sectors,
            source_refs=values["source_refs"],
        )

    compile = to_canonical


__all__ = [
    "DraftProgramRequirementSet",
    "DraftSectorRequirement",
    "DraftSpaceRequirement",
    "ProgramRequirementSet",
    "SectorRequirement",
    "SpaceRequirement",
    "UnknownRequirementFieldError",
]
