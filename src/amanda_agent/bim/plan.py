"""Read-only, ordered BIM plans selected from the verified capability registry.

The planner is deliberately separate from execution. It turns the stable
desired/current diff into commands that carry their provider chain, verifier,
and compensating rollback command. A ``NOOP`` is retained as audit metadata
but never becomes a write command.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from amanda_agent.design.models import compute_design_approval_hash
from amanda_agent.models.capability import (
    CapabilityRegistry,
    CapabilityStatus,
    EvidenceScope,
    SelectionRefused,
)

from .diff import DiffAction, DiffOperation, DiffResult
from .models import BimStage
from .stages import CONCEPT_ONLY_MAX_STAGE, ExecutionMode, stage_at_or_before


class PlanGenerationError(RuntimeError):
    """A plan cannot be generated under the supplied evidence or mode."""


class PlanStatus(StrEnum):
    READY = "READY"
    HIGH_RISK_PLAN = "HIGH_RISK_PLAN"
    CHECKPOINT_REQUIRED = "CHECKPOINT_REQUIRED"


_ACTION_CAPABILITY = {
    DiffAction.CREATE: "revit.create_element",
    DiffAction.UPDATE: "revit.update_element",
    DiffAction.REPLACE: "revit.replace_element",
    DiffAction.DELETE: "revit.delete_element",
    DiffAction.NOOP: "revit.noop",
}

_CAPABILITY_STAGE = {
    "revit.create_project": BimStage.R01,
    "revit.create_toposolid": BimStage.R02,
    "revit.create_level": BimStage.R03,
    "revit.create_grid": BimStage.R03,
    "revit.create_reference": BimStage.R03,
    "revit.create_mass": BimStage.R04,
}


class RollbackPlan(BaseModel):
    """One compensating command for a planned mutation."""

    model_config = ConfigDict(extra="forbid")

    action: DiffAction
    semantic_capability: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    verification_rules: list[str] = Field(default_factory=list)


def _model_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return dict(value)
    return {}


def _desired_payload(operation: DiffOperation) -> dict[str, Any]:
    """Serialize the desired content without provenance-only runtime detail."""

    desired = operation.desired
    if desired is None:
        return {}
    return desired.model_dump(mode="json", exclude={"provenance"})


def _current_payload(operation: DiffOperation) -> dict[str, Any]:
    """Serialize the observed content used to restore an existing element."""

    return _model_payload(operation.current)


def _verification_rules(action: DiffAction) -> list[str]:
    common = ["independent_requery", "unique_id_present", "document_matches"]
    if action is DiffAction.CREATE:
        return common
    if action is DiffAction.UPDATE:
        return common + ["content_hash_matches"]
    if action is DiffAction.REPLACE:
        return common + ["old_element_absent", "new_element_present"]
    if action is DiffAction.DELETE:
        return ["independent_requery", "element_absent"]
    return ["no_mutation"]


def _rollback(operation: DiffOperation) -> RollbackPlan:
    """Build a deterministic inverse command from the pre-write observation."""

    if operation.action is DiffAction.CREATE:
        return RollbackPlan(
            action=DiffAction.DELETE,
            semantic_capability="revit.delete_element",
            payload={"logical_id": operation.logical_id},
            verification_rules=["independent_requery", "element_absent"],
        )
    if operation.action is DiffAction.DELETE:
        return RollbackPlan(
            action=DiffAction.CREATE,
            semantic_capability="revit.create_element",
            payload=_current_payload(operation),
            verification_rules=["independent_requery", "unique_id_present"],
        )
    return RollbackPlan(
        action=operation.action,
        semantic_capability=_ACTION_CAPABILITY[operation.action],
        payload=_current_payload(operation),
        verification_rules=_verification_rules(operation.action),
    )


class PlanOperation(BaseModel):
    """One serialized compiler operation with its selected provider chain."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1)
    logical_id: str = Field(min_length=1)
    action: DiffAction
    semantic_capability: str = Field(min_length=1)
    stage: BimStage = BimStage.R01
    desired_payload: dict[str, Any] = Field(default_factory=dict)
    verification_rules: list[str] = Field(default_factory=list)
    preferred_provider: str | None = None
    fallback_providers: list[str] = Field(default_factory=list)
    revit_build: str | None = None
    tool_schema_hash: str | None = None
    rollback: RollbackPlan | None = None

    @property
    def provider_chain(self) -> list[str]:
        if self.preferred_provider is None:
            return list(self.fallback_providers)
        return [self.preferred_provider, *self.fallback_providers]


class BimPlan(BaseModel):
    """The read-only execution artifact Codex consumes."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, ge=1)
    generated_at: datetime
    document_id: str = Field(min_length=1)
    managed_count: int = Field(ge=0)
    operations: list[PlanOperation] = Field(default_factory=list)
    status: PlanStatus = PlanStatus.READY
    notes: list[str] = Field(default_factory=list)
    stage: BimStage = BimStage.R01
    execution_mode: ExecutionMode | None = None
    fixture: bool = False
    skipped_noops: list[str] = Field(default_factory=list)

    def to_file(self, path: str | Path) -> Path:
        """Serialize the plan without touching Revit or the working model."""

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target


def _coerce_stage(value: BimStage | str) -> BimStage:
    try:
        return value if isinstance(value, BimStage) else BimStage(value)
    except ValueError:
        try:
            return BimStage[str(value)]
        except KeyError as exc:
            raise PlanGenerationError(f"unknown BIM stage {value!r}") from exc


def _stage_for_operation(operation: DiffOperation, default: BimStage) -> BimStage:
    explicit = getattr(operation, "stage", None)
    if explicit is not None:
        return _coerce_stage(explicit)
    capability = operation.semantic_capability
    if capability in _CAPABILITY_STAGE:
        return _CAPABILITY_STAGE[capability]
    desired = operation.desired
    if desired is not None:
        category_stage = {
            "Project": BimStage.R01,
            "Site": BimStage.R02,
            "Levels": BimStage.R03,
            "Grids": BimStage.R03,
            "References": BimStage.R03,
            "Massing": BimStage.R04,
        }
        if desired.category in category_stage:
            return category_stage[desired.category]
    return default


def _effective_capability(operation: DiffOperation) -> str:
    if operation.semantic_capability and operation.semantic_capability != "bim.reconcile":
        return operation.semantic_capability
    return _ACTION_CAPABILITY[operation.action]


def _expand_operations(
    result: DiffResult,
    *,
    stage: BimStage,
    task_id_prefix: str,
) -> tuple[list[PlanOperation], list[str], BimStage]:
    ordered = sorted(
        result.operations,
        key=lambda operation: (
            list(BimStage).index(_stage_for_operation(operation, stage)),
            operation.logical_id,
            operation.action.value,
        ),
    )
    skipped = [operation.logical_id for operation in ordered if operation.action is DiffAction.NOOP]
    changed = [operation for operation in ordered if operation.action is not DiffAction.NOOP]
    stages = [_stage_for_operation(operation, stage) for operation in changed]
    effective_stage = max([stage, *stages], key=lambda item: list(BimStage).index(item))
    operations: list[PlanOperation] = []
    for index, operation in enumerate(changed, start=1):
        operation_stage = _stage_for_operation(operation, stage)
        action = operation.action
        operations.append(
            PlanOperation(
                task_id=f"{task_id_prefix}-{index:04d}",
                logical_id=operation.logical_id,
                action=action,
                semantic_capability=_effective_capability(operation),
                stage=operation_stage,
                desired_payload=_desired_payload(operation),
                verification_rules=_verification_rules(action),
                rollback=_rollback(operation),
            )
        )
    return operations, skipped, effective_stage


def plan_operations(
    result: DiffResult,
    *,
    stage: BimStage | str = BimStage.R01,
    task_id_prefix: str = "P05-T07",
) -> list[PlanOperation]:
    """Expand a diff into deterministic, stage-ordered write commands."""

    operations, _, _ = _expand_operations(
        result, stage=_coerce_stage(stage), task_id_prefix=task_id_prefix
    )
    return operations


def _select_chain(
    registry: CapabilityRegistry,
    *,
    operation: str,
    revit_build: str,
    tool_schema_hash: str,
    scope: EvidenceScope,
) -> tuple[str | None, list[str]]:
    candidates = registry.for_operation(operation)
    usable = [
        entry
        for entry in candidates
        if registry._refusal(
            entry,
            revit_build=revit_build,
            tool_schema_hash=tool_schema_hash,
            scope=scope,
            accept_pass_with_warnings=False,
        )
        is None
    ]
    if not usable:
        reasons = registry.refusals(
            operation,
            revit_build=revit_build,
            tool_schema_hash=tool_schema_hash,
            scope=scope,
        )
        raise SelectionRefused(
            f"no usable capability for {operation!r}: "
            + ("; ".join(reasons) or "none recorded")
        )
    usable.sort(
        key=lambda entry: (
            0 if entry.status is CapabilityStatus.PASS else 1,
            entry.priority,
            entry.provider,
        )
    )
    preferred = usable[0]
    return preferred.provider, [entry.provider for entry in usable[1:]]


def _validate_execution_scope(
    *,
    mode: ExecutionMode | str | None,
    stage: BimStage,
    fixture: bool,
    solution: Any | None,
) -> ExecutionMode | None:
    if mode is None:
        return None
    execution_mode = mode if isinstance(mode, ExecutionMode) else ExecutionMode(mode)
    if execution_mode is ExecutionMode.CONCEPT_ONLY and not stage_at_or_before(
        stage, CONCEPT_ONLY_MAX_STAGE
    ):
        raise PlanGenerationError(
            f"CONCEPT_ONLY permits stages through {CONCEPT_ONLY_MAX_STAGE.name}; "
            f"the plan reaches {stage.name}"
        )
    if execution_mode is ExecutionMode.SYNTHETIC_LAB and not fixture:
        raise PlanGenerationError(
            "SYNTHETIC_LAB is restricted to a fixture target; execution refused"
        )
    if execution_mode is ExecutionMode.DETAILED_BIM:
        if solution is None:
            raise PlanGenerationError(
                "DETAILED_BIM requires a content-bound selection record"
            )
        if not getattr(solution, "bim_eligible", False):
            raise PlanGenerationError(
                "DETAILED_BIM selection is not eligible or not content-bound"
            )
        approval_hash = getattr(solution, "approval_hash", None)
        if not approval_hash or approval_hash != compute_design_approval_hash(solution):
            raise PlanGenerationError(
                "DETAILED_BIM selection approval hash is not bound to its content"
            )
    return execution_mode


def generate_bim_plan(
    result: DiffResult,
    *,
    registry: CapabilityRegistry,
    revit_build: str,
    tool_schema_hash: str,
    scope: EvidenceScope = EvidenceScope.PRODUCTION,
    generated_at: datetime | None = None,
    stage: BimStage | str = BimStage.R01,
    execution_mode: ExecutionMode | str | None = None,
    fixture: bool = False,
    solution: Any | None = None,
    task_id_prefix: str = "P05-T07",
) -> BimPlan:
    """Generate a read-only plan and refuse unsupported execution modes."""

    base_stage = _coerce_stage(stage)
    expanded, skipped, effective_stage = _expand_operations(
        result, stage=base_stage, task_id_prefix=task_id_prefix
    )
    selected_mode = _validate_execution_scope(
        mode=execution_mode,
        stage=effective_stage,
        fixture=fixture,
        solution=solution,
    )
    operations: list[PlanOperation] = []
    for operation in expanded:
        try:
            preferred, fallbacks = _select_chain(
                registry,
                operation=operation.semantic_capability,
                revit_build=revit_build,
                tool_schema_hash=tool_schema_hash,
                scope=scope,
            )
        except SelectionRefused as exc:
            raise PlanGenerationError(str(exc)) from exc
        operations.append(
            operation.model_copy(
                update={
                    "preferred_provider": preferred,
                    "fallback_providers": fallbacks,
                    "revit_build": revit_build,
                    "tool_schema_hash": tool_schema_hash,
                }
            )
        )
    return BimPlan(
        generated_at=generated_at or datetime.now(UTC),
        document_id=result.document_id,
        managed_count=result.managed_count,
        operations=operations,
        notes=[
            "NOOP operations are omitted from execution because current content is equal"
            if skipped
            else "no idempotent NOOP operations were found"
        ],
        stage=effective_stage,
        execution_mode=selected_mode,
        fixture=fixture,
        skipped_noops=skipped,
    )


def write_plan_set(plan: BimPlan, directory: str | Path) -> tuple[Path, Path]:
    """Write BIM_PLAN.json and the human summary BIM_PLAN.md together."""

    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)
    json_path = plan.to_file(target_dir / "BIM_PLAN.json")
    markdown_path = target_dir / "BIM_PLAN.md"
    lines = [
        f"# BIM Plan (schema {plan.schema_version})",
        "",
        f"Generated at: {plan.generated_at.isoformat()}",
        f"Document identity: {plan.document_id}",
        f"Managed elements: {plan.managed_count}",
        f"Stage: {plan.stage.name}",
        f"Execution mode: {plan.execution_mode.value if plan.execution_mode else 'UNSPECIFIED'}",
        f"Status: {plan.status.value}",
        "",
        "## Operations",
        "",
    ]
    for operation in plan.operations:
        chain = " -> ".join(operation.provider_chain) or "(none)"
        rollback = operation.rollback.semantic_capability if operation.rollback else "(none)"
        lines.append(
            f"- {operation.task_id}: {operation.stage.name} {operation.action.value} "
            f"{operation.logical_id} [{operation.semantic_capability}; providers: {chain}; "
            f"rollback: {rollback}]"
        )
    if plan.skipped_noops:
        lines.extend(["", "## Idempotent skips", ""])
        lines.extend(f"- {logical_id}: current content already matches" for logical_id in plan.skipped_noops)
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, markdown_path


__all__ = [
    "BimPlan",
    "PlanGenerationError",
    "PlanOperation",
    "PlanStatus",
    "RollbackPlan",
    "generate_bim_plan",
    "plan_operations",
    "write_plan_set",
]
