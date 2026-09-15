"""Guard Revit, provider, and critical dependency updates."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class UpdateKind(StrEnum):
    REVIT = "REVIT"
    PROVIDER = "PROVIDER"
    CRITICAL_DEPENDENCY = "CRITICAL_DEPENDENCY"


class UpdateDenied(PermissionError):
    """Raised by the enforcing helper when policy refuses an update."""


@dataclass(frozen=True)
class RegressionEvidence:
    """The required synthetic regression result for Revit/provider changes."""

    full_provider: bool
    synthetic_e2e: bool
    result: str
    evidence_ref: str

    def __post_init__(self) -> None:
        result = str(self.result).strip().upper()
        if not result:
            raise ValueError("regression result cannot be blank")
        object.__setattr__(self, "result", result)

    @property
    def passed(self) -> bool:
        return (
            self.full_provider
            and self.synthetic_e2e
            and self.result == "PASS"
            and bool(str(self.evidence_ref).strip())
        )


@dataclass(frozen=True)
class UpdateRequest:
    """A proposed update and the isolation/evidence context around it."""

    component: UpdateKind | str
    phase: str
    branch: str
    worktree: str | Path | None = None
    regression: RegressionEvidence | None = None

    def __post_init__(self) -> None:
        try:
            kind = UpdateKind(str(self.component).strip().upper().replace("-", "_"))
        except ValueError as exc:
            raise ValueError("unsupported update component: " + str(self.component)) from exc
        if not str(self.phase).strip():
            raise ValueError("update phase cannot be blank")
        if not str(self.branch).strip():
            raise ValueError("update branch cannot be blank")
        object.__setattr__(self, "component", kind)


@dataclass(frozen=True)
class UpdateDecision:
    allowed: bool
    reason: str
    request: UpdateRequest


_BLOCKED_PHASES = frozenset({"PRODUCTION_BUILD", "QA", "RC", "RELEASE"})
_ISOLATED_PHASES = frozenset({"MAINTENANCE", "EXPERIMENT"})


def _normalize(value: str) -> str:
    return "_".join(str(value).strip().upper().replace("-", " ").split())


def _is_isolated_name(value: str | Path | None) -> bool:
    if value is None:
        return False
    text = str(value).strip().replace("\\", "/").strip("/")
    segments = [segment for segment in text.split("/") if segment]
    if not segments:
        return False
    branch_namespace = _normalize(segments[0])
    leaf = _normalize(segments[-1])
    return branch_namespace in _ISOLATED_PHASES or leaf in _ISOLATED_PHASES or leaf.startswith(
        ("MAINTENANCE_", "EXPERIMENT_")
    )


def evaluate_update(request: UpdateRequest) -> UpdateDecision:
    """Return the policy decision without changing the environment."""
    if not isinstance(request, UpdateRequest):
        raise TypeError("request must be an UpdateRequest")

    phase = _normalize(request.phase)
    if phase in _BLOCKED_PHASES:
        return UpdateDecision(
            allowed=False,
            reason="updates are refused during the current production/QA/RC/release phase",
            request=request,
        )

    if phase not in _ISOLATED_PHASES or not (
        _is_isolated_name(request.branch) or _is_isolated_name(request.worktree)
    ):
        return UpdateDecision(
            allowed=False,
            reason="updates are allowed only inside a maintenance or experiment branch/worktree",
            request=request,
        )

    if request.component in {UpdateKind.REVIT, UpdateKind.PROVIDER}:
        if request.regression is None or not request.regression.passed:
            return UpdateDecision(
                allowed=False,
                reason=(
                    "Revit/provider updates require a passing full provider plus "
                    "synthetic end-to-end regression"
                ),
                request=request,
            )

    return UpdateDecision(
        allowed=True,
        reason="update is isolated and satisfies the maintenance policy",
        request=request,
    )


def assert_update_allowed(request: UpdateRequest) -> UpdateDecision:
    decision = evaluate_update(request)
    if not decision.allowed:
        raise UpdateDenied(decision.reason)
    return decision


def can_update(request: UpdateRequest) -> bool:
    return evaluate_update(request).allowed


__all__ = [
    "RegressionEvidence",
    "UpdateDecision",
    "UpdateDenied",
    "UpdateKind",
    "UpdateRequest",
    "assert_update_allowed",
    "can_update",
    "evaluate_update",
]
