"""Read-only BIM plan generation from a verified diff and capability registry."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from amanda_agent.models.capability import (
    CapabilityRegistry,
    CapabilityStatus,
    EvidenceScope,
    SelectionRefused,
)

from .diff import DiffAction, DiffResult


class PlanGenerationError(RuntimeError):
    """A required provider chain is not eligible under current evidence."""


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


def _desired_payload(operation: Any) -> dict[str, Any]:
    desired = getattr(operation, "desired", None)
    if desired is None:
        return {}
    payload = desired.model_dump(exclude={"provenance"})
    payload["requirement_id"] = desired.requirement_id
    payload["design_option"] = desired.design_option
    payload["generation_run"] = desired.generation_run
    return payload


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


class PlanOperation(BaseModel):
    """One serialized compiler operation with its provider chain."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1)
    logical_id: str = Field(min_length=1)
    action: DiffAction
    semantic_capability: str = Field(min_length=1)
    desired_payload: dict[str, Any] = Field(default_factory=dict)
    verification_rules: list[str] = Field(default_factory=list)
    preferred_provider: str | None = None
    fallback_providers: list[str] = Field(default_factory=list)
    revit_build: str | None = None
    tool_schema_hash: str | None = None

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

    def to_file(self, path: str | Path) -> Path:
        """Serialize the plan without touching Revit or the working model."""

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target


def plan_operations(result: DiffResult) -> list[PlanOperation]:
    """Expand a diff into deterministic operations in logical-id order."""

    ordered = sorted(result.operations, key=lambda operation: operation.logical_id)
    operations: list[PlanOperation] = []
    for index, operation in enumerate(ordered, start=1):
        if operation.action is DiffAction.NOOP:
            continue
        operations.append(
            PlanOperation(
                task_id=f"T{index:04d}:{operation.logical_id}:{operation.action.value}",
                logical_id=operation.logical_id,
                action=operation.action,
                semantic_capability=_ACTION_CAPABILITY[operation.action],
                desired_payload=_desired_payload(operation),
                verification_rules=_verification_rules(operation.action),
            )
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
            f"no usable capability for {operation!r}: " + ("; ".join(reasons) or "none recorded")
        )
    usable.sort(
        key=lambda entry: (
            0 if entry.status is CapabilityStatus.PASS else 1,
            entry.priority,
            entry.provider,
        )
    )
    preferred = usable[0]
    fallbacks = [entry.provider for entry in usable[1:]]
    return preferred.provider, fallbacks


def generate_bim_plan(
    result: DiffResult,
    *,
    registry: CapabilityRegistry,
    revit_build: str,
    tool_schema_hash: str,
    scope: EvidenceScope = EvidenceScope.PRODUCTION,
    generated_at: datetime | None = None,
) -> BimPlan:
    """Generate a read-only plan; never mutates the working model."""

    expanded = plan_operations(result)
    operations: list[PlanOperation] = []
    notes: list[str] = []
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
            PlanOperation(
                **operation.model_dump(exclude={"preferred_provider", "fallback_providers", "revit_build", "tool_schema_hash"}),
                preferred_provider=preferred,
                fallback_providers=fallbacks,
                revit_build=revit_build,
                tool_schema_hash=tool_schema_hash,
            )
        )
    return BimPlan(
        generated_at=generated_at or datetime.now(UTC),
        document_id=result.document_id,
        managed_count=result.managed_count,
        operations=operations,
        notes=notes,
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
        f"Status: {plan.status.value}",
        "",
        "## Operations",
        "",
    ]
    for operation in plan.operations:
        chain = " -> ".join(operation.provider_chain) or "(none)"
        lines.append(
            f"- {operation.task_id}: {operation.action.value} {operation.logical_id} "
            f"[{operation.semantic_capability}; providers: {chain}]"
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, markdown_path


__all__ = [
    "BimPlan",
    "PlanGenerationError",
    "PlanOperation",
    "PlanStatus",
    "generate_bim_plan",
    "plan_operations",
    "write_plan_set",
]
