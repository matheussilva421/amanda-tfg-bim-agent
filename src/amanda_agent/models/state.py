"""Project state and task outcome vocabulary."""

from enum import StrEnum

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    DEGRADED = "DEGRADED"
    BLOCKED_BY_INPUT = "BLOCKED_BY_INPUT"
    BLOCKED_BY_TOOL = "BLOCKED_BY_TOOL"
    FAILED_ROLLED_BACK = "FAILED_ROLLED_BACK"
    CRITICAL_FAILURE = "CRITICAL_FAILURE"


class PhaseGate(StrEnum):
    GO = "GO"
    GO_WITH_LIMITATIONS = "GO_WITH_LIMITATIONS"
    NO_GO = "NO_GO"


class ProjectState(BaseModel):
    project: str = "Amanda TFG BIM Agent"
    phase_id: str = "PHASE_01"
    phase_name: str = "foundation-environment-state"
    phase_status: TaskStatus = TaskStatus.PENDING
    last_completed_task: str | None = None
    next_task: str = "P01-T01"
    schema_version: int = 1
    state_revision: int = 0
    phase_gate: PhaseGate | None = None
    selected_design: str | None = None
    revit_stage: str | None = None  # no model before verified R00
    current_checkpoint: str | None = None
    blockers: list[str] = Field(default_factory=list)
    last_verified_commit: str | None = None
