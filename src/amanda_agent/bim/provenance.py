"""Provenance attached to desired BIM elements and compiler runs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BimProvenance(BaseModel):
    """Traceable inputs for one desired BIM element."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    requirement_id: str = Field(min_length=1)
    design_option: str = Field(min_length=1)
    generation_run: str = Field(min_length=1)
    source_refs: list[str] = Field(default_factory=list)
    generated_at: datetime | None = None
    notes: dict[str, Any] = Field(default_factory=dict)


# Both spellings are useful at call sites while the serialized model remains
# stable and uses the lower-case BIM acronym in its canonical class name.
BIMProvenance = BimProvenance
Provenance = BimProvenance


__all__ = ["BIMProvenance", "BimProvenance", "Provenance"]
