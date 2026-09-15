"""Current managed and unmanaged element observations from Revit."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CurrentElement(BaseModel):
    """An independent query result for one Revit element.

    ``element_id`` is session-only. The persistent identity is the pair of
    ``unique_id`` and ``document_id`` together with the managed logical ID.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    logical_id: str | None = Field(default=None, min_length=1)
    category: str = Field(min_length=1)
    geometry: dict[str, Any] = Field(default_factory=dict)
    properties: dict[str, Any] = Field(default_factory=dict)
    unique_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    element_id: int | str | None = Field(default=None, exclude=True)
    diverged: bool = False
    expected_content_hash: str | None = None
    observed_content_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def accept_revit_unique_id_alias(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if "unique_id" not in values and "revit_unique_id" in values:
            values["unique_id"] = values.pop("revit_unique_id")
        return values

    @model_validator(mode="after")
    def mark_hash_divergence(self) -> CurrentElement:
        if (
            self.expected_content_hash is not None
            and self.observed_content_hash is not None
            and self.expected_content_hash != self.observed_content_hash
        ):
            self.diverged = True
        return self

    @property
    def managed(self) -> bool:
        return self.logical_id is not None

    @property
    def revit_unique_id(self) -> str:
        return self.unique_id


class CurrentState(BaseModel):
    """A document query with duplicate and document-identity safeguards."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(default="unknown", min_length=1)
    elements: list[CurrentElement] = Field(default_factory=list)
    source: str = Field(default="revit-query", min_length=1)

    @model_validator(mode="after")
    def validate_logical_id_uniqueness(self) -> CurrentState:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for element in self.elements:
            if element.logical_id is None:
                continue
            if element.logical_id in seen:
                duplicates.add(element.logical_id)
            seen.add(element.logical_id)
            if element.document_id != self.document_id:
                raise ValueError(
                    f"element document identity {element.document_id!r} does not match "
                    f"current state {self.document_id!r}"
                )
        if duplicates:
            joined = ", ".join(sorted(duplicates))
            raise ValueError(f"duplicate logical_id in current state: {joined}")
        return self

    def managed_by_logical_id(self) -> dict[str, CurrentElement]:
        return {
            element.logical_id: element
            for element in self.elements
            if element.logical_id is not None
        }


CurrentModel = CurrentState
CurrentElementState = CurrentElement


__all__ = [
    "CurrentElement",
    "CurrentElementState",
    "CurrentModel",
    "CurrentState",
]
