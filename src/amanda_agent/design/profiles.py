"""Evidence-bound service profiles for the design solver.

The YAML file is a declarative study input.  Numbers are wrapped in a small
citation record so a profile cannot silently acquire an uncited dimension.
Provisional profiles remain loadable for inspection, but selecting or using
one requires an explicit opt-in.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProfileValidationError(ValueError):
    """The profile document is malformed or fails its evidence checks."""


class ProfileProvisionalError(ValueError):
    """A provisional profile was used without explicit permission."""


class Citation(BaseModel):
    """A source locator attached to profile evidence."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    url: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    acessado_em: str = Field(min_length=1)
    paywalled: bool = False
    secondary: bool = False

    @model_validator(mode="after")
    def validate_date(self) -> Citation:
        try:
            date.fromisoformat(self.acessado_em)
        except ValueError as exc:
            raise ValueError("acessado_em must be an ISO date") from exc
        if not self.url.startswith(("https://", "http://")):
            raise ValueError("citation url must be absolute")
        return self


class CitedNumber(BaseModel):
    """A numeric design value whose source and status are explicit."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    value: float | int
    citation_id: str = Field(min_length=1)
    provisional: bool = False
    confidence: str | None = None

    @model_validator(mode="before")
    @classmethod
    def accept_citation_alias(cls, values: Any) -> Any:
        if isinstance(values, Mapping):
            values = dict(values)
            if "citation_id" not in values and "citation" in values:
                values["citation_id"] = values.pop("citation")
        return values

    @model_validator(mode="after")
    def validate_status(self) -> CitedNumber:
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise TypeError("cited number value must be numeric")
        if self.provisional and self.confidence != "low":
            raise ValueError("provisional values require confidence: low")
        if not self.provisional and self.confidence == "low":
            raise ValueError("non-provisional values cannot have low confidence")
        return self


class Requirement(BaseModel):
    """One mandatory program or operational requirement."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    citation_id: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def accept_citation_alias(cls, values: Any) -> Any:
        if isinstance(values, Mapping):
            values = dict(values)
            if "citation_id" not in values and "citation" in values:
                values["citation_id"] = values.pop("citation")
        return values


class AdjacencyRule(BaseModel):
    """A directed relation between two profile sectors."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    citation_id: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def accept_citation_alias(cls, values: Any) -> Any:
        if isinstance(values, Mapping):
            values = dict(values)
            if "citation_id" not in values and "citation" in values:
                values["citation_id"] = values.pop("citation")
        return values


class SectorProfile(BaseModel):
    """A sector allocation with cited capacity dimensions."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    share_of_useful_area: CitedNumber
    minimum_rooms: CitedNumber
    privacy_level: str = Field(min_length=1)
    area_per_person_m2: CitedNumber

    @model_validator(mode="after")
    def validate_dimensions(self) -> SectorProfile:
        if not 0 < float(self.share_of_useful_area.value) <= 1:
            raise ValueError("sector area share must be between zero and one")
        if float(self.minimum_rooms.value) < 1:
            raise ValueError("sector minimum_rooms must be at least one")
        if float(self.area_per_person_m2.value) <= 0:
            raise ValueError("sector area_per_person_m2 must be positive")
        if self.privacy_level not in {"low", "medium", "high", "very_high"}:
            raise ValueError("sector privacy_level is invalid")
        return self


class Profile(BaseModel):
    """One selectable service profile."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    max_simultaneous_people: CitedNumber
    sectors: list[SectorProfile] = Field(min_length=1)
    mandatory_requirements: list[Requirement] = Field(min_length=1)
    adjacency_rules: dict[str, list[AdjacencyRule]]
    citations: list[Citation] = Field(min_length=1)
    provisional: bool = False

    @model_validator(mode="before")
    @classmethod
    def accept_requirement_alias(cls, values: Any) -> Any:
        if isinstance(values, Mapping):
            values = dict(values)
            if "mandatory_requirements" not in values and "requirements" in values:
                values["mandatory_requirements"] = values.pop("requirements")
        return values

    @model_validator(mode="after")
    def validate_evidence_and_shape(self) -> Profile:
        expected_rules = {"mandatory", "permitted", "undesired"}
        if set(self.adjacency_rules) != expected_rules:
            raise ValueError(
                "adjacency_rules must contain mandatory, permitted and undesired"
            )
        sector_ids = [sector.id for sector in self.sectors]
        if len(sector_ids) != len(set(sector_ids)):
            raise ValueError("profile sector ids must be unique")
        share_total = sum(
            float(sector.share_of_useful_area.value) for sector in self.sectors
        )
        if not math.isclose(share_total, 1.0, rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError("profile sector shares must total one")
        citation_ids = {citation.id for citation in self.citations}
        if len(citation_ids) != len(self.citations):
            raise ValueError("profile citation ids must be unique")
        numbers = [self.max_simultaneous_people]
        numbers.extend(
            number
            for sector in self.sectors
            for number in (
                sector.share_of_useful_area,
                sector.minimum_rooms,
                sector.area_per_person_m2,
            )
        )
        missing = {
            number.citation_id for number in numbers if number.citation_id not in citation_ids
        }
        missing.update(
            requirement.citation_id
            for requirement in self.mandatory_requirements
            if requirement.citation_id not in citation_ids
        )
        for rules in self.adjacency_rules.values():
            missing.update(
                rule.citation_id
                for rule in rules
                if rule.citation_id not in citation_ids
            )
        if missing:
            raise ValueError("profile has unresolved citation ids: " + ", ".join(sorted(missing)))
        if float(self.max_simultaneous_people.value) > 20:
            raise ValueError("profile capacity cannot exceed 20 people")
        if not any(
            number.provisional for number in numbers
        ) and self.provisional:
            raise ValueError("profile marked provisional without provisional evidence")
        return self

    @property
    def is_provisional(self) -> bool:
        """Whether any selected profile dimension is a study assumption."""

        return self.provisional or any(
            number.provisional
            for sector in self.sectors
            for number in (
                sector.share_of_useful_area,
                sector.minimum_rooms,
                sector.area_per_person_m2,
            )
        ) or self.max_simultaneous_people.provisional

    @property
    def requirements(self) -> list[Requirement]:
        """Compatibility view for callers that use the shorter name."""

        return self.mandatory_requirements


class ProfileCatalog(BaseModel):
    """Validated profile document and its global simultaneous-use ceiling."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, ge=1)
    max_simultaneous_people: CitedNumber
    profiles: list[Profile] = Field(min_length=1)
    citations: list[Citation] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_catalog(self) -> ProfileCatalog:
        if float(self.max_simultaneous_people.value) > 20:
            raise ValueError("catalog capacity cannot exceed 20 people")
        ids = [profile.id for profile in self.profiles]
        if len(ids) != len(set(ids)):
            raise ValueError("profile ids must be unique")
        citation_ids = {citation.id for citation in self.citations}
        if self.max_simultaneous_people.citation_id not in citation_ids:
            raise ValueError("catalog capacity has an unresolved citation id")
        if len(citation_ids) != len(self.citations):
            raise ValueError("catalog citation ids must be unique")
        return self


_ACTIVE_CATALOG: ProfileCatalog | None = None


def load_profiles(path: str | Path) -> ProfileCatalog:
    """Read and validate a profile YAML document, then make it active."""

    target = Path(path)
    if target.is_symlink() or not target.is_file():
        raise ProfileValidationError(f"profile document is missing or mutable: {target}")
    try:
        payload = yaml.safe_load(target.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise TypeError("profile document must be a mapping")
        catalog = ProfileCatalog.model_validate(payload)
    except (OSError, UnicodeError, yaml.YAMLError, TypeError, ValueError) as exc:
        if isinstance(exc, ProfileValidationError):
            raise
        raise ProfileValidationError(f"invalid profile document: {exc}") from exc
    global _ACTIVE_CATALOG
    _ACTIVE_CATALOG = catalog
    return catalog


def _active_catalog(catalog: ProfileCatalog | None = None) -> ProfileCatalog:
    if catalog is not None:
        return catalog
    if _ACTIVE_CATALOG is None:
        default_path = Path("design-engine") / "config" / "profiles.yaml"
        return load_profiles(default_path)
    return _ACTIVE_CATALOG


def select_profile(
    profile_id: str,
    *,
    allow_provisional: bool = False,
    catalog: ProfileCatalog | None = None,
) -> Profile:
    """Select one profile, refusing study assumptions unless opted in."""

    selected = next(
        (profile for profile in _active_catalog(catalog).profiles if profile.id == profile_id),
        None,
    )
    if selected is None:
        raise KeyError(profile_id)
    if selected.is_provisional and not allow_provisional:
        raise ProfileProvisionalError(
            f"profile {profile_id!r} is provisional; pass allow_provisional=True"
        )
    return selected


def check_capacity(
    profile: Profile,
    people: int,
    *,
    allow_provisional: bool = False,
) -> bool:
    """Return whether a simultaneous population fits the profile ceiling."""

    if isinstance(people, bool) or not isinstance(people, int):
        raise TypeError("people must be an integer")
    if people < 0:
        raise ValueError("people must be non-negative")
    if not isinstance(profile, Profile):
        raise TypeError("profile must be a Profile")
    if profile.is_provisional and not allow_provisional:
        raise ProfileProvisionalError(
            f"profile {profile.id!r} is provisional; pass allow_provisional=True"
        )
    ceiling = min(20, int(profile.max_simultaneous_people.value))
    return people <= ceiling


__all__ = [
    "AdjacencyRule",
    "Citation",
    "CitedNumber",
    "Profile",
    "ProfileCatalog",
    "ProfileProvisionalError",
    "ProfileValidationError",
    "Requirement",
    "SectorProfile",
    "check_capacity",
    "load_profiles",
    "select_profile",
]
