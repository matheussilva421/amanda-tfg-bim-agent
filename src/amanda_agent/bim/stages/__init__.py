"""Shared vocabulary, gates and dispatch for the BIM stage executors.

A stage module describes *desired* Revit work and the conditions under which
that work may run. Stage code never imports a Revit bridge: execution is
dispatched through an injected ``StageToolInvoker`` so the same code runs
against a synthetic fixture, a lab provider or, later, the production adapter.

Two rules are enforced here rather than left to the caller:

* the execution mode bounds which stages may be planned at all
  (``CONCEPT_ONLY`` stops at R04, ``SYNTHETIC_LAB`` only reaches fixtures, and
  detailed BIM needs a content-bound selection record);
* a capability is usable only when the registry can prove it for the exact
  Revit build and tool schema, exactly as ``bim.plan`` selects providers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from amanda_agent.design.models import (
    DesignSolution,
    DesignStatus,
    compute_design_approval_hash,
)
from amanda_agent.models.capability import (
    CapabilityRegistry,
    CapabilityStatus,
    EvidenceScope,
    ProviderCapability,
)
from amanda_agent.requirements.decisions import (
    DecisionScenario,
    SelectionKind,
)
from amanda_agent.site.models import (
    ScenarioOverrideStatus,
    SiteModel,
    SourceTopographyState,
    TopographyRepresentation,
)

from ..checkpoints import CheckpointManager, CheckpointManifest
from ..models import BimStage


class StageError(RuntimeError):
    """A stage cannot be planned or executed under the current evidence."""


class StagePreflightError(StageError):
    """The preflight gate refused the stage, so nothing may be written."""


class MissingCapabilityError(StageError):
    """No registry-approved provider can perform the requested operation."""


class ExecutionMode(StrEnum):
    """Who a run is allowed to write for."""

    CONCEPT_ONLY = "CONCEPT_ONLY"
    SYNTHETIC_LAB = "SYNTHETIC_LAB"
    DETAILED_BIM = "DETAILED_BIM"


CONCEPT_ONLY_MAX_STAGE = BimStage.R04

_STAGE_ORDER: tuple[BimStage, ...] = tuple(BimStage)

#: Operations a stage cannot run without, independent of the caller.
STAGE_REQUIRED_OPERATIONS: dict[BimStage, tuple[str, ...]] = {
    BimStage.R01: ("revit.create_project",),
    BimStage.R02: (),
}


class CheckStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class StageCheck(BaseModel):
    """One auditable preflight verdict."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    status: CheckStatus
    detail: str = Field(min_length=1)


class PreflightReport(BaseModel):
    """The complete preflight verdict for one stage attempt."""

    model_config = ConfigDict(extra="forbid")

    mode: ExecutionMode
    stage: BimStage
    scenario: DecisionScenario
    checks: list[StageCheck] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def get(self, name: str) -> StageCheck | None:
        for check in self.checks:
            if check.name == name:
                return check
        return None

    @property
    def failures(self) -> list[StageCheck]:
        return [check for check in self.checks if check.status is CheckStatus.FAIL]

    @property
    def blocked(self) -> list[StageCheck]:
        return [check for check in self.checks if check.status is CheckStatus.BLOCKED]

    @property
    def problems(self) -> list[str]:
        return [f"{check.name}: {check.detail}" for check in self.failures]

    @property
    def ok(self) -> bool:
        """A STUDY run may carry blocked checks; a FINAL run may not."""

        return not self.failures and not (
            self.scenario is DecisionScenario.FINAL and self.blocked
        )


class PreflightRequest(BaseModel):
    """Everything the gate needs, without touching Revit."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    mode: ExecutionMode
    stage: BimStage = BimStage.R01
    scenario: DecisionScenario = DecisionScenario.STUDY
    registry: CapabilityRegistry = Field(default_factory=CapabilityRegistry)
    revit_build: str = Field(min_length=1)
    tool_schema_hash: str = Field(min_length=1)
    expected_build: str = Field(min_length=1)
    expected_tool_schema_hash: str = Field(min_length=1)
    selected_inputs: dict[str, str] = Field(default_factory=dict)
    expected_inputs: dict[str, str] = Field(default_factory=dict)
    required_operations: tuple[str, ...] = ()
    solution: DesignSolution | None = None
    expected_approval_hash: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    site: SiteModel | None = None
    fixture: bool = False
    evidence_scope: EvidenceScope = EvidenceScope.PRODUCTION
    generation_run: str = Field(default="RUN-0001", min_length=1)
    last_checkpoint_verified: bool | None = None
    registry_warnings: tuple[str, ...] = ()

    @classmethod
    def from_production_state(
        cls,
        project_root: str | Path,
        **overrides: Any,
    ) -> PreflightRequest:
        """Build a request from the on-disk production state.

        The registry is loaded through the declared crosswalk so semantic
        operation names resolve to recorded provider evidence. The measured
        build and the expected schema hash come from the state files; nothing
        here invents a value. Warnings from the loader are kept on the request
        so the preflight can name a declared gap.
        """

        root = Path(project_root)
        registry, warnings = CapabilityRegistry.load_for_production(root)
        payload = dict(overrides)
        payload.setdefault("registry", registry)
        payload.setdefault("registry_warnings", warnings)
        request = cls(**payload)
        return request


class StageOperation(BaseModel):
    """One desired Revit mutation owned by a stage."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    stage: BimStage
    logical_id: str = Field(min_length=1)
    semantic_capability: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    verification_rules: list[str] = Field(default_factory=list)
    blocked_by: list[str] = Field(default_factory=list)
    preferred_provider: str | None = None
    fallback_providers: list[str] = Field(default_factory=list)

    @property
    def provider_chain(self) -> list[str]:
        if self.preferred_provider is None:
            return list(self.fallback_providers)
        return [self.preferred_provider, *self.fallback_providers]


class StageToolCall(BaseModel):
    """A request handed to the injected provider adapter."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    stage: BimStage
    logical_id: str = Field(min_length=1)
    semantic_capability: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class StageExecutionRecord(BaseModel):
    """What the adapter reported for one dispatched operation."""

    model_config = ConfigDict(extra="forbid")

    stage: BimStage
    logical_id: str
    semantic_capability: str
    provider: str | None = None
    reported_success: bool
    raw: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class StageToolInvoker(Protocol):
    """The only door to a Revit provider, injected by the caller."""

    def invoke(self, call: StageToolCall) -> Mapping[str, Any]:
        """Run one operation and return the raw adapter result."""


def stage_at_or_before(stage: BimStage, limit: BimStage) -> bool:
    """Compare stages by declaration order, not by name."""

    return _STAGE_ORDER.index(stage) <= _STAGE_ORDER.index(limit)


def stage_checkpoint_label(stage: BimStage) -> str:
    """Return the canonical checkpoint label, for example R01_PROJECT_INITIALIZED."""

    return f"{stage.name}_{stage.value}"


def create_stage_checkpoint(
    *,
    source_path: Path,
    checkpoint_path: Path,
    stage: BimStage,
    manager: CheckpointManager | None = None,
    **kwargs: Any,
) -> CheckpointManifest:
    """Publish an immutable stage copy labelled with its formal stage name."""

    checkpoint_manager = manager or CheckpointManager()
    return checkpoint_manager.create_checkpoint(
        source_path,
        checkpoint_path,
        stage=stage_checkpoint_label(stage),
        **kwargs,
    )


def capability_is_selectable(
    registry: CapabilityRegistry,
    operation: str,
    *,
    revit_build: str,
    tool_schema_hash: str,
    scope: EvidenceScope = EvidenceScope.PRODUCTION,
) -> tuple[bool, list[str]]:
    """Whether one operation has a usable capability, with every refusal reason."""

    candidates = registry.for_operation(operation)
    if not candidates:
        gap = registry.gap_note(operation)
        if gap is not None:
            return False, [f"gap declarado no crosswalk: {gap}"]
        return False, [f"{operation}: no capability recorded"]
    reasons = registry.refusals(
        operation,
        revit_build=revit_build,
        tool_schema_hash=tool_schema_hash,
        scope=scope,
    )
    if len(reasons) < len(candidates):
        return True, reasons
    return False, reasons


def select_capability(
    registry: CapabilityRegistry,
    operation: str,
    *,
    revit_build: str,
    tool_schema_hash: str,
    scope: EvidenceScope = EvidenceScope.PRODUCTION,
) -> tuple[ProviderCapability, list[ProviderCapability]]:
    """Return the best usable capability and the rest of the chain, or refuse.

    The per-record predicate is read through the registry exactly as
    ``bim.plan`` does, so plan selection and stage selection cannot drift.
    """

    usable = [
        entry
        for entry in registry.for_operation(operation)
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
        raise MissingCapabilityError(
            f"no usable capability for {operation!r}: "
            + ("; ".join(reasons) or "no capability recorded")
        )
    usable.sort(
        key=lambda entry: (
            0 if entry.status is CapabilityStatus.PASS else 1,
            entry.priority,
            entry.provider,
        )
    )
    return usable[0], usable[1:]


def require_capability(
    registry: CapabilityRegistry,
    operation: str,
    *,
    revit_build: str,
    tool_schema_hash: str,
    scope: EvidenceScope = EvidenceScope.PRODUCTION,
) -> ProviderCapability:
    """Return the preferred capability for an operation or refuse loudly."""

    preferred, _ = select_capability(
        registry,
        operation,
        revit_build=revit_build,
        tool_schema_hash=tool_schema_hash,
        scope=scope,
    )
    return preferred


def provider_chain(
    registry: CapabilityRegistry,
    operation: str,
    *,
    revit_build: str,
    tool_schema_hash: str,
    scope: EvidenceScope = EvidenceScope.PRODUCTION,
) -> tuple[str, list[str]]:
    """Return the preferred provider and its verified fallbacks."""

    preferred, rest = select_capability(
        registry,
        operation,
        revit_build=revit_build,
        tool_schema_hash=tool_schema_hash,
        scope=scope,
    )
    return preferred.provider, [entry.provider for entry in rest]


def with_stage_requirements(
    request: PreflightRequest,
    extra: Sequence[str] = (),
) -> PreflightRequest:
    """Merge the stage's own required operations into the request."""

    merged: list[str] = []
    for operation in (
        *STAGE_REQUIRED_OPERATIONS.get(request.stage, ()),
        *request.required_operations,
        *extra,
    ):
        if operation not in merged:
            merged.append(operation)
    return request.model_copy(update={"required_operations": tuple(merged)})


def _active_provisional_overrides(site: SiteModel | None) -> list[Any]:
    if site is None:
        return []
    return [
        override
        for override in site.scenario_overrides
        if override.status is ScenarioOverrideStatus.ACTIVE
    ]


def _pass(name: str, detail: str) -> StageCheck:
    return StageCheck(name=name, status=CheckStatus.PASS, detail=detail)


def _fail(name: str, detail: str) -> StageCheck:
    return StageCheck(name=name, status=CheckStatus.FAIL, detail=detail)


def run_preflight(request: PreflightRequest) -> PreflightReport:
    """Evaluate every documented preflight condition without writing anything."""

    checks: list[StageCheck] = []
    notes: list[str] = []
    solution = request.solution
    registry = request.registry

    # 1. The execution mode bounds the stage window.
    if request.mode is ExecutionMode.CONCEPT_ONLY and not stage_at_or_before(
        request.stage, CONCEPT_ONLY_MAX_STAGE
    ):
        checks.append(
            _fail(
                "mode_stage_window",
                f"CONCEPT_ONLY permits stages through {CONCEPT_ONLY_MAX_STAGE.name} "
                f"only, got {request.stage.name}",
            )
        )
    else:
        checks.append(
            _pass(
                "mode_stage_window",
                f"{request.mode.value} permits stage {request.stage.name}",
            )
        )

    # 2. A mode must match what it is allowed to write for.
    if request.mode is ExecutionMode.SYNTHETIC_LAB and not request.fixture:
        checks.append(
            _fail(
                "fixture_scope",
                "SYNTHETIC_LAB is restricted to fixtures and cannot authorize a real target",
            )
        )
    elif request.mode is ExecutionMode.DETAILED_BIM and request.fixture:
        checks.append(
            _fail("fixture_scope", "a fixture target cannot authorize detailed production")
        )
    else:
        checks.append(_pass("fixture_scope", "target scope matches the execution mode"))

    # 3. Detailed BIM needs an explicit, content-bound selection record.
    if request.mode is not ExecutionMode.DETAILED_BIM:
        checks.append(
            _pass("selection_record", "mode does not require a design selection record")
        )
    elif solution is None:
        checks.append(
            _fail(
                "selection_record",
                "detailed BIM requires an explicit APPROVED_FOR_BIM selection record",
            )
        )
    elif solution.status not in (
        DesignStatus.APPROVED_FOR_BIM,
        DesignStatus.AMANDA_REVIEW_PENDING,
    ):
        checks.append(
            _fail(
                "selection_record",
                f"status {solution.status.value} is not eligible for detailed BIM",
            )
        )
    elif not solution.bim_eligible:
        checks.append(
            _fail(
                "selection_record",
                "the selection record is not BIM eligible under the current evidence",
            )
        )
    else:
        if solution.status is DesignStatus.AMANDA_REVIEW_PENDING:
            notes.append(
                "AMANDA_REVIEW_PENDING is nonblocking for delegated work and does not "
                "imply personal approval"
            )
        checks.append(
            _pass(
                "selection_record",
                f"{solution.status.value} under {solution.selection_authority.value}",
            )
        )

    # 4. The approval hash must still bind the solution content.
    if request.mode is not ExecutionMode.DETAILED_BIM:
        checks.append(
            _pass("approval_hash", "mode does not require a content-bound approval hash")
        )
    elif solution is None:
        checks.append(_fail("approval_hash", "no selection record to bind"))
    elif solution.decision_evidence is None:
        checks.append(
            _fail("approval_hash", "decision evidence is required to bind the approval hash")
        )
    elif not solution.decision_evidence.approval_hash_valid:
        checks.append(
            _fail("approval_hash", "decision evidence approval_hash is no longer valid")
        )
    elif solution.decision_evidence.selection_authority is not solution.selection_authority:
        checks.append(
            _fail("approval_hash", "decision evidence authority does not match the solution")
        )
    elif (
        request.expected_approval_hash is not None
        and solution.approval_hash != request.expected_approval_hash
    ):
        checks.append(
            _fail(
                "approval_hash",
                "the solution approval_hash is not the hash this run was authorized for",
            )
        )
    elif solution.approval_hash != compute_design_approval_hash(solution):
        checks.append(
            _fail("approval_hash", "approval_hash is not bound to the current solution content")
        )
    else:
        checks.append(_pass("approval_hash", "approval_hash matches the solution content"))

    # 5. Selected input versions must match the run and the selected solution.
    version_problems: list[str] = []
    for key, expected in sorted(request.expected_inputs.items()):
        selected = request.selected_inputs.get(key)
        if selected is None:
            version_problems.append(f"{key} was not selected")
        elif selected != expected:
            version_problems.append(f"{key}: selected {selected!r} != expected {expected!r}")
    if request.mode is ExecutionMode.DETAILED_BIM and solution is not None:
        pinned = {
            "requirements_version": solution.requirements_version,
            "site_version": str(solution.site_version),
            "engine_version": solution.engine_version,
        }
        for key, value in pinned.items():
            selected = request.selected_inputs.get(key)
            if selected is None:
                version_problems.append(f"detailed BIM must select {key}")
            elif selected != value:
                version_problems.append(f"{key}: selected {selected!r} != solution {value!r}")
    if version_problems:
        checks.append(_fail("input_versions", "; ".join(version_problems)))
    else:
        checks.append(_pass("input_versions", "selected input versions match the run"))

    # 6. The pinned build and tool schema must be the live ones.
    if request.expected_build != request.revit_build:
        checks.append(
            _fail(
                "revit_build",
                f"pinned build {request.expected_build!r} is not the live build "
                f"{request.revit_build!r}",
            )
        )
    elif request.expected_tool_schema_hash != request.tool_schema_hash:
        checks.append(
            _fail(
                "revit_build",
                f"pinned tool schema hash {request.expected_tool_schema_hash!r} is not the "
                f"live {request.tool_schema_hash!r}",
            )
        )
    else:
        checks.append(
            _pass("revit_build", f"exact build {request.revit_build} and schema hash match")
        )

    # 7. The registry must prove every operation the stage needs.
    scope = request.evidence_scope
    operations = list(request.required_operations)
    if operations:
        refused: list[str] = []
        for operation in operations:
            selectable, reasons = capability_is_selectable(
                registry,
                operation,
                revit_build=request.revit_build,
                tool_schema_hash=request.tool_schema_hash,
                scope=scope,
            )
            if not selectable:
                refused.append(f"{operation}: " + ("; ".join(reasons) or "no record"))
        if refused:
            checks.append(_fail("capability_registry", " | ".join(refused)))
        else:
            checks.append(
                _pass("capability_registry", "every required operation has a usable capability")
            )
    else:
        recorded = sorted(
            {entry.operation for entry in registry.entries if entry.operation is not None}
        )
        usable = [
            operation
            for operation in recorded
            if capability_is_selectable(
                registry,
                operation,
                revit_build=request.revit_build,
                tool_schema_hash=request.tool_schema_hash,
                scope=scope,
            )[0]
        ]
        if usable:
            checks.append(
                _pass(
                    "capability_registry",
                    "registry offers a selectable capability for the exact build",
                )
            )
        else:
            checks.append(
                _fail(
                    "capability_registry",
                    "the registry has no selectable capability for build "
                    f"{request.revit_build!r} and schema {request.tool_schema_hash!r}",
                )
            )

    # 8. STUDY may carry provisional assumptions; FINAL may not.
    provisional = _active_provisional_overrides(request.site)
    if request.scenario is DecisionScenario.STUDY:
        if request.site is None:
            notes.append("STUDY profile: no site model supplied, so no site claim is made")
        else:
            notes.append(
                "STUDY profile: topography source is "
                f"{request.site.topography.source_state.value} and no FINAL claim is certified"
            )
        if provisional:
            notes.append(
                "STUDY profile: an active PROVISIONAL_ASSUMPTION scenario override is "
                "carried as a design hypothesis only"
            )
        checks.append(_pass("site_profile", "STUDY profile records provisional input as such"))
    else:
        final_problems: list[str] = []
        if request.site is None:
            final_problems.append("FINAL requires a site model with verified topography")
        else:
            topography = request.site.topography
            if (
                topography.source_state is not SourceTopographyState.VERIFIED_TOPOGRAPHY
                or topography.representation
                is not TopographyRepresentation.VERIFIED_TOPOGRAPHY
            ):
                final_problems.append(
                    "FINAL requires verified topography; an unverified assumption cannot "
                    "certify FINAL"
                )
        if provisional:
            final_problems.append(
                "FINAL cannot rely on an active PROVISIONAL_ASSUMPTION scenario override"
            )
        if (
            solution is not None
            and solution.decision_evidence is not None
            and solution.decision_evidence.selection_kind
            is SelectionKind.PROVISIONAL_ASSUMPTION
        ):
            final_problems.append("FINAL cannot rely on a PROVISIONAL_ASSUMPTION decision")
        if final_problems:
            checks.append(_fail("site_profile", "; ".join(final_problems)))
        else:
            checks.append(_pass("site_profile", "verified input supports the FINAL profile"))

    # 9. The previous checkpoint must have verified before a new stage runs.
    if request.last_checkpoint_verified is None:
        notes.append("no previous checkpoint is recorded for this run")
        checks.append(_pass("last_checkpoint", "no previous checkpoint to verify"))
    elif request.last_checkpoint_verified:
        checks.append(_pass("last_checkpoint", "the previous checkpoint hash verified"))
    else:
        checks.append(
            _fail("last_checkpoint", "the previous checkpoint failed hash verification")
        )

    return PreflightReport(
        mode=request.mode,
        stage=request.stage,
        scenario=request.scenario,
        checks=checks,
        notes=notes,
    )


def dispatch_operations(
    operations: Sequence[StageOperation],
    *,
    invoker: StageToolInvoker,
) -> list[StageExecutionRecord]:
    """Hand every desired operation to the injected adapter, in order."""

    blocked = [
        (operation.logical_id, sorted(set(operation.blocked_by)))
        for operation in operations
        if operation.blocked_by
    ]
    if blocked:
        details = "; ".join(
            f"{logical_id}: {', '.join(gates)}" for logical_id, gates in blocked
        )
        raise StagePreflightError(
            "operation dispatch blocked by evidence gate: " + details
        )

    records: list[StageExecutionRecord] = []
    for operation in operations:
        provider = operation.preferred_provider or (
            operation.fallback_providers[0] if operation.fallback_providers else None
        )
        if provider is None:
            raise StageError(f"operation {operation.logical_id} has no selected provider")
        call = StageToolCall(
            stage=operation.stage,
            logical_id=operation.logical_id,
            semantic_capability=operation.semantic_capability,
            provider=provider,
            payload=operation.payload,
        )
        raw = invoker.invoke(call)
        records.append(
            StageExecutionRecord(
                stage=operation.stage,
                logical_id=operation.logical_id,
                semantic_capability=operation.semantic_capability,
                provider=provider,
                reported_success=bool(dict(raw).get("reported_success", False)),
                raw=dict(raw),
            )
        )
    return records


__all__ = [
    "CONCEPT_ONLY_MAX_STAGE",
    "STAGE_REQUIRED_OPERATIONS",
    "CheckStatus",
    "EvidenceScope",
    "ExecutionMode",
    "MissingCapabilityError",
    "PreflightReport",
    "PreflightRequest",
    "StageCheck",
    "StageError",
    "StageExecutionRecord",
    "StageOperation",
    "StagePreflightError",
    "StageToolCall",
    "StageToolInvoker",
    "capability_is_selectable",
    "create_stage_checkpoint",
    "dispatch_operations",
    "provider_chain",
    "require_capability",
    "run_preflight",
    "select_capability",
    "stage_at_or_before",
    "stage_checkpoint_label",
    "with_stage_requirements",
]
