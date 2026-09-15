"""The human-intervention state machine.

This module exists to answer one question honestly: does this action require a
person, or does it merely feel like it should? Under
``AGENT_DELEGATED`` the agent already holds authority for routine design work,
finalist selection, researched typology and material choices, and reversible
provisional assumptions. Raising a gate for those would stall the project on a
decision that was delegated, so the default answer for them is deliberately
"proceed".

A gate is emitted only for a boundary the agent genuinely cannot cross: a
credential, an elevation prompt, a licence that must be validated by its owner,
an outward-facing irreversible action, money, work that is not ours to destroy,
or a material change to an already-selected brief.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class SelectionAuthority(StrEnum):
    """Who decides the routine architectural questions."""

    AGENT_DELEGATED = "AGENT_DELEGATED"
    USER_REQUESTED_PAUSE = "USER_REQUESTED_PAUSE"


class HumanGateReason(StrEnum):
    """Why the agent must stop and ask."""

    UAC_APPROVAL = "UAC_APPROVAL"
    AUTHENTICATION_OR_MFA = "AUTHENTICATION_OR_MFA"
    LICENSE_VALIDATION = "LICENSE_VALIDATION"
    ESSENTIAL_SOURCE_DATA = "ESSENTIAL_SOURCE_DATA"
    ARCHITECTURAL_SELECTION = "ARCHITECTURAL_SELECTION"
    IRREVERSIBLE_EXTERNAL_ACTION = "IRREVERSIBLE_EXTERNAL_ACTION"
    EXTERNAL_DATA_OR_COST = "EXTERNAL_DATA_OR_COST"
    PLATFORM_PERMISSION = "PLATFORM_PERMISSION"
    USER_WORK_AT_RISK = "USER_WORK_AT_RISK"
    PROGRAM_BASELINE = "PROGRAM_BASELINE"


#: Phrases that identify each boundary, matched case-insensitively.
_TRIGGERS: tuple = (
    (HumanGateReason.UAC_APPROVAL, ("uac", "user account control")),
    (
        HumanGateReason.AUTHENTICATION_OR_MFA,
        ("mfa", "multi-factor", "sign in", "sign-in", "log in", "login",
         "authenticate", "password prompt", "2fa"),
    ),
    (
        HumanGateReason.LICENSE_VALIDATION,
        ("licence", "license", "activation", "activate"),
    ),
    (
        HumanGateReason.USER_WORK_AT_RISK,
        ("unsaved", "user work", "kill", "force close", "discard"),
    ),
    (
        HumanGateReason.IRREVERSIBLE_EXTERNAL_ACTION,
        ("publish", "submit", "issue the release", "irreversible",
         "send to the client", "deliver to"),
    ),
    (
        HumanGateReason.EXTERNAL_DATA_OR_COST,
        ("buy", "purchase", "paid", "subscription", "cost", "invoice",
         "credit card"),
    ),
    (
        HumanGateReason.PLATFORM_PERMISSION,
        ("platform permission", "app permission", "admin rights",
         "requires approval from the platform"),
    ),
)

#: Phrases showing a permission is already held, so it is not a boundary.
_PERMISSION_ALREADY_HELD = (
    "already approved",
    "already granted",
    "already have",
    "existing authorization",
    "existing authorisation",
    "existing permission",
    "approved by the platform permission model",
    "previously approved",
)

#: Phrases showing a permission is genuinely missing and must be requested.
_PERMISSION_MISSING = (
    "not granted",
    "denied",
    "is required",
    "requires",
    "needs",
    "revoked",
    "expired",
)


def _scope_for(reason: HumanGateReason) -> tuple:
    """Which work stops, and which work may keep going.

    A Revit or provider boundary halts the Tool Lab and everything that
    consumes a proven provider; source intelligence and the solver are
    independent work and must not be dragged down with it.
    """
    provider_scope = (
        ["PHASE_02 (Tool Lab)", "PHASE_05..PHASE_08 (compiler through release)"],
        ["PHASE_03 (project intelligence)", "PHASE_04 (solver)"],
    )
    scopes = {
        HumanGateReason.UAC_APPROVAL: provider_scope,
        HumanGateReason.AUTHENTICATION_OR_MFA: provider_scope,
        HumanGateReason.LICENSE_VALIDATION: provider_scope,
        HumanGateReason.USER_WORK_AT_RISK: provider_scope,
        HumanGateReason.IRREVERSIBLE_EXTERNAL_ACTION: (
            ["the outward-facing publication step"],
            ["all local, reversible work"],
        ),
        HumanGateReason.EXTERNAL_DATA_OR_COST: (
            ["the dependent verification only"],
            ["all independent work"],
        ),
        HumanGateReason.PLATFORM_PERMISSION: (
            ["the blocked tool path"],
            ["the already-approved fallbacks"],
        ),
        HumanGateReason.ESSENTIAL_SOURCE_DATA: (
            ["the dependent verification only"],
            ["all independent work"],
        ),
        HumanGateReason.PROGRAM_BASELINE: (
            ["the program-dependent design work"],
            ["the independent research"],
        ),
        HumanGateReason.ARCHITECTURAL_SELECTION: (
            ["the design step awaiting the user's review"],
            ["all research and reversible preparation"],
        ),
    }
    return scopes.get(reason, ([], []))


@dataclass(frozen=True)
class HumanGateDecision:
    """The verdict, with enough detail to become a blocker record."""

    required: bool
    reason: HumanGateReason | None = None
    explanation: str = ""
    action: str = ""
    blocked_work: list = field(default_factory=list)
    allowed_work: list = field(default_factory=list)

    def as_blocker(self, blocker_id: str = "HUMAN-GATE") -> dict:
        """Render as a blocker payload for the blocker registry."""
        if not self.required:
            raise ValueError("a decision that is not a gate is not a blocker")
        return {
            "id": blocker_id,
            "summary": self.explanation,
            "severity": "BLOCKING",
            "reason": str(self.reason),
            "affected_tasks": list(self.blocked_work),
            "allowed_tasks": list(self.allowed_work),
            "resolution_action": self.action,
        }


def _matches(text: str, phrases: tuple) -> bool:
    return any(phrase in text for phrase in phrases)


def _program_baseline_change(text: str) -> bool:
    """A change to the brief, not a confirmation of it.

    The 20-person baseline is already resolved, so confirming it is not a gate.
    Only a material change to it returns to the user.
    """
    change_verbs = ("change", "revoke", "replace", "raise", "increase", "modify", "rescind")
    subjects = ("brief", "program", "baseline", "residents", "pessoas")
    if "42" in text and ("resident" in text or "pessoas" in text or "person" in text):
        return True
    return _matches(text, change_verbs) and _matches(text, subjects)


def evaluate_gate(
    action: str,
    *,
    authority: SelectionAuthority | str,
    provisional_study_possible: bool = False,
    research_exhausted: bool = False,
) -> HumanGateDecision:
    """Decide whether ``action`` needs a human, and why.

    ``provisional_study_possible`` and ``research_exhausted`` exist so that a
    missing source datum cannot be escalated before a reversible STUDY path has
    actually been ruled out.
    """
    try:
        resolved = SelectionAuthority(authority)
    except ValueError as exc:
        raise ValueError(
            "unknown selection authority: " + str(authority)
        ) from exc
    text = (action or "").lower()

    for reason, phrases in _TRIGGERS:
        if not _matches(text, phrases):
            continue
        if reason is HumanGateReason.PLATFORM_PERMISSION:
            # Installing a package the platform model already authorises is
            # routine work; only a permission that is actually missing is a
            # human boundary.
            if _matches(text, _PERMISSION_ALREADY_HELD) and not _matches(
                text, _PERMISSION_MISSING
            ):
                continue
        return _gate(reason, action)

    if "essential source data" in text:
        if research_exhausted and not provisional_study_possible:
            return _gate(HumanGateReason.ESSENTIAL_SOURCE_DATA, action)
        return HumanGateDecision(
            required=False,
            explanation=(
                "a reversible STUDY path still covers this, so the work "
                "continues on a provisional assumption instead of stopping"
            ),
        )

    if _program_baseline_change(text) and _matches(
        text, ("brief", "program", "baseline", "residents", "pessoas")
    ):
        return _gate(HumanGateReason.PROGRAM_BASELINE, action)

    if resolved is SelectionAuthority.USER_REQUESTED_PAUSE and _matches(
        text, ("approve", "approval", "review the design", "selection")
    ):
        return _gate(HumanGateReason.ARCHITECTURAL_SELECTION, action)

    return HumanGateDecision(
        required=False,
        explanation=(
            "AGENT_DELEGATED covers this choice; the agent decides, records the "
            "justification and an approval_hash, and Amanda reviews afterwards"
        ),
    )


def _gate(reason: HumanGateReason, action: str) -> HumanGateDecision:
    blocked, allowed = _scope_for(reason)
    return HumanGateDecision(
        required=True,
        reason=reason,
        explanation=str(reason) + ": " + action.strip(),
        action=_ACTION_TEXT[reason],
        blocked_work=list(blocked),
        allowed_work=list(allowed),
    )


#: What the person actually has to do. A gate without this is just a stall.
_ACTION_TEXT = {
    HumanGateReason.UAC_APPROVAL: (
        "Approve the Windows elevation prompt on the machine, then report back "
        "that it completed."
    ),
    HumanGateReason.AUTHENTICATION_OR_MFA: (
        "Sign in with the required MFA in your own browser session. The agent "
        "will not type credentials for you."
    ),
    HumanGateReason.LICENSE_VALIDATION: (
        "Open Revit once and confirm the licence is valid and the product "
        "starts, then report the result."
    ),
    HumanGateReason.ESSENTIAL_SOURCE_DATA: (
        "Provide the missing source document or measurement, or authorise a "
        "declared provisional value in writing."
    ),
    HumanGateReason.ARCHITECTURAL_SELECTION: (
        "Review the presented alternatives and state which one to develop."
    ),
    HumanGateReason.IRREVERSIBLE_EXTERNAL_ACTION: (
        "Perform or explicitly authorise the irreversible external action."
    ),
    HumanGateReason.EXTERNAL_DATA_OR_COST: (
        "Decide whether to incur the external cost or supply the data yourself."
    ),
    HumanGateReason.PLATFORM_PERMISSION: (
        "Grant the platform permission or confirm the fallback route."
    ),
    HumanGateReason.USER_WORK_AT_RISK: (
        "Save or close your own work in that application, then confirm it is "
        "safe to continue."
    ),
    HumanGateReason.PROGRAM_BASELINE: (
        "Confirm whether the material change to the selected brief is wanted; "
        "the current baseline stays in force until you do."
    ),
}


def needs_human(
    action: str,
    *,
    authority: SelectionAuthority | str = SelectionAuthority.AGENT_DELEGATED,
    **kwargs,
) -> bool:
    """Convenience predicate for call sites that only need the yes/no."""
    return evaluate_gate(action, authority=authority, **kwargs).required
