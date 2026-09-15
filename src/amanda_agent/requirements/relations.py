"""Canonical spatial relations and circulation flow labels."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RelationType(StrEnum):
    """Strength and direction of the desired spatial relationship."""

    MUST_ADJOIN = "MUST_ADJOIN"
    SHOULD_ADJOIN = "SHOULD_ADJOIN"
    SHOULD_BE_NEAR = "SHOULD_BE_NEAR"
    CAN_BE_NEAR = "CAN_BE_NEAR"
    NEUTRAL = "NEUTRAL"
    SHOULD_BE_SEPARATED = "SHOULD_BE_SEPARATED"
    MUST_BE_SEPARATED = "MUST_BE_SEPARATED"


class FlowNetwork(StrEnum):
    """Independent circulation networks represented by the design engine."""

    RESIDENT = "resident"
    CHILD = "child"
    STAFF = "staff"
    VISITOR = "visitor"
    SERVICE = "service"
    EMERGENCY = "emergency"


class EnvironmentRelation(BaseModel):
    """A weighted relation between two environment logical identifiers."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_logical_id: str = Field(min_length=1)
    target_logical_id: str = Field(min_length=1)
    relation: RelationType
    weight: float = Field(ge=0, le=1, allow_inf_nan=False)
    flow: FlowNetwork | None = None
    max_distance_m: float | None = Field(
        default=None,
        gt=0,
        allow_inf_nan=False,
    )
    preferred_distance_m: float | None = Field(
        default=None,
        gt=0,
        allow_inf_nan=False,
    )
    allow_self: bool = False

    @model_validator(mode="after")
    def validate_relation(self) -> EnvironmentRelation:
        if (
            self.source_logical_id == self.target_logical_id
            and not self.allow_self
        ):
            raise ValueError("self relation is not allowed")
        if (
            self.preferred_distance_m is not None
            and self.max_distance_m is not None
            and self.preferred_distance_m > self.max_distance_m
        ):
            raise ValueError("preferred distance cannot exceed max distance")
        return self


Relation = RelationType
FlowType = FlowNetwork
RoomRelation = EnvironmentRelation
SpaceRelation = EnvironmentRelation


__all__ = [
    "EnvironmentRelation",
    "FlowNetwork",
    "FlowType",
    "Relation",
    "RelationType",
    "RoomRelation",
    "SpaceRelation",
]
