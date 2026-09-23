"""Versioned decisions and the academic boundary of technical releases."""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SelectionAuthority(StrEnum):
    """Authority that selected the option recorded by a decision."""

    AGENT_DELEGATED = "AGENT_DELEGATED"
    USER_DIRECTED = "USER_DIRECTED"
    AMANDA_DIRECTED = "AMANDA_DIRECTED"
    USER_REQUESTED_PAUSE = "USER_REQUESTED_PAUSE"


class DecisionScenario(StrEnum):
    """Release context in which a decision may be consumed."""

    STUDY = "STUDY"
    FINAL = "FINAL"


Scenario = DecisionScenario


class FactClass(StrEnum):
    """Epistemic class kept alongside the decision record."""

    SOURCE_FACT = "SOURCE_FACT"
    DERIVED_CONSTRAINT = "DERIVED_CONSTRAINT"
    DESIGN_HYPOTHESIS = "DESIGN_HYPOTHESIS"


class SelectionKind(StrEnum):
    """Whether an option is evidence-backed or an explicitly reversible assumption."""

    EVIDENCE_BACKED = "EVIDENCE_BACKED"
    PROVISIONAL_ASSUMPTION = "PROVISIONAL_ASSUMPTION"


class ValidationStatus(StrEnum):
    """Validation state of the input needed by a decision."""

    UNVERIFIED = "UNVERIFIED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    BLOCKED_BY_INPUT = "BLOCKED_BY_INPUT"
    NOT_EVALUATED = "NOT_EVALUATED"
    SUPERSEDED = "SUPERSEDED"


class ReviewStatus(StrEnum):
    """Amanda review state, independent from execution authority."""

    AMANDA_REVIEW_PENDING = "AMANDA_REVIEW_PENDING"
    AMANDA_ACCEPTED = "AMANDA_ACCEPTED"
    SUPERSEDED = "SUPERSEDED"


class AcademicStatus(StrEnum):
    """Status of an academic deliverable, separate from technical output."""

    PENDING = "PENDING"
    PROVISIONAL = "PROVISIONAL"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


def _canonicalize(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, BaseModel):
        return _canonicalize(value.model_dump(mode="python"))
    if isinstance(value, dict):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def compute_approval_hash(
    *,
    selected_option: Any,
    rationale: Any,
    source_refs: Any,
    affected_requirements: Any,
) -> str:
    """Return the stable SHA-256 binding the decision's material inputs."""
    payload = {
        "selected_option": _canonicalize(selected_option),
        "rationale": _canonicalize(rationale),
        "source_refs": _canonicalize(source_refs),
        "affected_requirements": _canonicalize(affected_requirements),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class DecisionRecord(BaseModel):
    """One immutable-in-practice decision version."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    decision_id: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    alternatives: list[str] = Field(min_length=1)
    selected_option: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    affected_requirements: list[str] = Field(min_length=1)
    selection_authority: SelectionAuthority
    timestamp: str = Field(min_length=1)
    supersedes: str | None = Field(default=None, min_length=1)
    approval_hash: str = Field(default="", pattern=r"^[0-9a-f]{64}$")
    validation_status: ValidationStatus
    revision_procedure: str = Field(min_length=1)
    review_status: ReviewStatus

    fact_class: FactClass = FactClass.SOURCE_FACT
    scenario: DecisionScenario = DecisionScenario.STUDY
    selection_kind: SelectionKind = SelectionKind.EVIDENCE_BACKED
    verification_required: bool = False
    adoption_status: str | None = Field(default=None, min_length=1)
    rejected_options: list[str] = Field(default_factory=list)
    source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")

    @field_validator(
        "alternatives",
        "source_refs",
        "affected_requirements",
        "rejected_options",
        mode="before",
    )
    @classmethod
    def non_empty_items(cls, value: Any) -> Any:
        if value is None:
            return value
        if not isinstance(value, list):
            raise TypeError("must be a list")
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError("list items must be non-empty strings")
        return value

    @model_validator(mode="before")
    @classmethod
    def infer_provisional_kind(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        values = dict(values)
        selected_option = str(values.get("selected_option", ""))
        if selected_option.startswith("PROVISIONAL_ASSUMPTION"):
            values.setdefault("selection_kind", SelectionKind.PROVISIONAL_ASSUMPTION)
        if "approval_hash" not in values:
            values["approval_hash"] = compute_approval_hash(
                selected_option=values.get("selected_option"),
                rationale=values.get("rationale"),
                source_refs=values.get("source_refs"),
                affected_requirements=values.get("affected_requirements"),
            )
        return values

    @model_validator(mode="after")
    def guard_provisional_assumptions(self) -> DecisionRecord:
        provisional = (
            self.selection_kind is SelectionKind.PROVISIONAL_ASSUMPTION
            or self.selected_option.startswith("PROVISIONAL_ASSUMPTION")
        )
        if provisional and self.fact_class is not FactClass.DESIGN_HYPOTHESIS:
            raise ValueError("PROVISIONAL_ASSUMPTION requires DESIGN_HYPOTHESIS")
        if provisional and self.scenario is not DecisionScenario.STUDY:
            raise ValueError("PROVISIONAL_ASSUMPTION requires STUDY")
        if provisional and self.validation_status is ValidationStatus.VERIFIED:
            raise ValueError(
                "PROVISIONAL_ASSUMPTION cannot have validation_status VERIFIED"
            )
        if (
            self.fact_class is FactClass.DESIGN_HYPOTHESIS
            and self.validation_status is ValidationStatus.VERIFIED
        ):
            raise ValueError("a DESIGN_HYPOTHESIS cannot be promoted to VERIFIED")
        return self

    @model_validator(mode="after")
    def validate_approval_hash(self) -> DecisionRecord:
        if not self.approval_hash_valid:
            raise ValueError(
                "approval_hash does not match the selected option, rationale, "
                "source references and affected requirements"
            )
        return self

    @property
    def approval_hash_valid(self) -> bool:
        """Whether this record's hash still matches its material inputs."""
        return self.is_approval_hash_valid()

    def is_approval_hash_valid(self, approval_hash: str | None = None) -> bool:
        candidate = self.approval_hash if approval_hash is None else approval_hash
        expected = compute_approval_hash(
            selected_option=self.selected_option,
            rationale=self.rationale,
            source_refs=self.source_refs,
            affected_requirements=self.affected_requirements,
        )
        return candidate == expected

    @property
    def can_execute(self) -> bool:
        """Amanda review pending is informative and does not stop execution."""
        return self.validation_status is not ValidationStatus.SUPERSEDED


class AcademicDeliverable(BaseModel):
    """A human-auditable academic output or prerequisite."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    deliverable_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)
    status: AcademicStatus
    status_reason: str = ""
    evidence: list[str] = Field(default_factory=list)
    expected_quantity: str | None = Field(default=None, min_length=1)
    date: str | None = Field(default=None, min_length=1)
    production_role: str = Field(min_length=1)
    requires_human_action: bool = True
    required_for_tfg_complete: bool = True

    @field_validator("source_refs", "evidence", mode="before")
    @classmethod
    def valid_reference_lists(cls, value: Any) -> Any:
        if value is None:
            return value
        if not isinstance(value, list):
            raise TypeError("must be a list")
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError("list items must be non-empty strings")
        return value

    @property
    def complete(self) -> bool:
        return self.status is AcademicStatus.COMPLETED and bool(self.evidence)


class AcademicDeliverableScope(BaseModel):
    """Academic completion status that technical STUDY releases can bypass."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    deliverables: list[AcademicDeliverable] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self) -> AcademicDeliverableScope:
        identifiers = [item.deliverable_id for item in self.deliverables]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("duplicate academic deliverable id")
        return self

    def get(self, deliverable_id: str) -> AcademicDeliverable:
        for item in self.deliverables:
            if item.deliverable_id == deliverable_id:
                return item
        raise KeyError(deliverable_id)

    @property
    def can_claim_tfg_complete(self) -> bool:
        return all(
            not item.required_for_tfg_complete or item.complete
            for item in self.deliverables
        )

    @property
    def final_blocked_reasons(self) -> list[str]:
        return [
            f"academic deliverable {item.deliverable_id} ({item.name}) is unresolved"
            for item in self.deliverables
            if item.required_for_tfg_complete and not item.complete
        ]

    def can_release(self, scenario: DecisionScenario | str) -> bool:
        return DecisionScenario(scenario) is DecisionScenario.STUDY or not (
            self.final_blocked_reasons
        )


def build_academic_deliverable_scope() -> AcademicDeliverableScope:
    """Build the scope without inventing dates, visits, signatures or submissions."""
    caderno_source = "TFG_Amanda Fernandes_ENTREGA 15.06.2026.pdf#chapters-3-and-5"
    support_source = (
        "TFG_Amanda_2026/1_COMECE_AQUI/02_plano_de_acompanhamento.pdf#pages-2-5"
    )
    gap_source = "TFG_Amanda_2026/1_COMECE_AQUI/01_COMECE_AQUI.pdf#pages-1-2"
    human_role = "HUMAN_AUTHORED_VALIDATED"
    human_required = "HUMAN_REQUIRED"
    bim_role = "BIM_GENERATED_WITH_HUMAN_VALIDATION"

    return AcademicDeliverableScope(
        deliverables=[
            AcademicDeliverable(
                deliverable_id="academic-caderno-revision",
                name="Caderno revision",
                owner="Amanda",
                source_refs=[caderno_source, support_source],
                status=AcademicStatus.PENDING,
                production_role=human_role,
            ),
            AcademicDeliverable(
                deliverable_id="academic-visits",
                name="Field visits and survey",
                owner="Amanda",
                source_refs=[gap_source, support_source],
                status=AcademicStatus.PENDING,
                production_role=human_required,
            ),
            AcademicDeliverable(
                deliverable_id="academic-metaprojeto",
                name="Metaprojeto",
                owner="Amanda",
                source_refs=[support_source],
                status=AcademicStatus.PENDING,
                production_role=human_role,
            ),
            AcademicDeliverable(
                deliverable_id="academic-preliminary-study",
                name="Preliminary study",
                owner="Amanda",
                source_refs=[support_source],
                status=AcademicStatus.PENDING,
                production_role=bim_role,
            ),
            AcademicDeliverable(
                deliverable_id="academic-anteprojeto",
                name="Anteprojeto",
                owner="Amanda",
                source_refs=[support_source],
                status=AcademicStatus.PENDING,
                production_role=bim_role,
            ),
            AcademicDeliverable(
                deliverable_id="academic-pranchas",
                name="Landscape synthesis boards",
                owner="Amanda",
                source_refs=[support_source],
                status=AcademicStatus.PROVISIONAL,
                status_reason=(
                    "Support-plan quantity claim stays provisional until the "
                    "institutional regulation is acquired; date is unknown."
                ),
                expected_quantity="4-6 A1",
                production_role=human_role,
            ),
            AcademicDeliverable(
                deliverable_id="academic-descriptive-memorial",
                name="Descriptive memorial",
                owner="Amanda",
                source_refs=[support_source],
                status=AcademicStatus.PENDING,
                production_role=human_role,
            ),
            AcademicDeliverable(
                deliverable_id="academic-calculation-memorial",
                name="Calculation memorial",
                owner="Amanda",
                source_refs=[support_source],
                status=AcademicStatus.PENDING,
                production_role=human_role,
            ),
            AcademicDeliverable(
                deliverable_id="academic-defense",
                name="Defense",
                owner="Amanda",
                source_refs=[support_source],
                status=AcademicStatus.PENDING,
                production_role=human_required,
            ),
            AcademicDeliverable(
                deliverable_id="academic-authorship",
                name="Authorship and author declaration",
                owner="Amanda",
                source_refs=[caderno_source, support_source],
                status=AcademicStatus.PENDING,
                production_role=human_required,
            ),
            AcademicDeliverable(
                deliverable_id="academic-institutional-submission",
                name="Institutional submission",
                owner="Amanda",
                source_refs=[support_source],
                status=AcademicStatus.PENDING,
                production_role=human_required,
            ),
        ]
    )


class DecisionRegister(BaseModel):
    """Collection of decisions plus the independent academic completion scope."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, ge=1)
    decisions: list[DecisionRecord] = Field(default_factory=list)
    academic_scope: AcademicDeliverableScope = Field(
        default_factory=build_academic_deliverable_scope
    )

    @model_validator(mode="before")
    @classmethod
    def accept_yaml_shapes(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if "decisions" not in values and "entries" in values:
            values["decisions"] = values.pop("entries")
        if "academic_scope" not in values and "academic_deliverables" in values:
            deliverables = values.pop("academic_deliverables")
            values["academic_scope"] = (
                deliverables
                if isinstance(deliverables, dict)
                else {"deliverables": deliverables}
            )
        return values

    @model_validator(mode="after")
    def unique_ids(self) -> DecisionRegister:
        identifiers = [item.decision_id for item in self.decisions]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("duplicate decision_id")
        return self

    @property
    def entries(self) -> list[DecisionRecord]:
        return self.decisions

    def get(self, decision_id: str) -> DecisionRecord:
        for decision in self.decisions:
            if decision.decision_id == decision_id:
                return decision
        raise KeyError(decision_id)

    def for_topic(self, topic: str) -> DecisionRecord:
        matches = [decision for decision in self.decisions if decision.topic == topic]
        if not matches:
            raise KeyError(topic)
        return matches[-1]

    def can_execute(self, decision_id: str) -> bool:
        return self.get(decision_id).can_execute

    def accept_amanda(self, decision_id: str) -> DecisionRecord:
        """Record later acceptance without changing the material hash inputs."""
        current = self.get(decision_id)
        if current.review_status is ReviewStatus.SUPERSEDED:
            raise ValueError("cannot accept a superseded decision")
        accepted = current.model_copy(
            update={"review_status": ReviewStatus.AMANDA_ACCEPTED}
        )
        self.decisions[self.decisions.index(current)] = accepted
        return accepted

    def create_revision(
        self,
        decision_id: str,
        *,
        selected_option: str,
        rationale: str,
        decision_id_for_revision: str | None = None,
        **updates: Any,
    ) -> DecisionRecord:
        """Append a new version and mark the superseded version immutable."""
        previous = self.get(decision_id)
        new_id = decision_id_for_revision or self._next_revision_id(previous)
        payload = previous.model_dump()
        payload.update(updates)
        payload.update(
            {
                "decision_id": new_id,
                "selected_option": selected_option,
                "rationale": rationale,
                "supersedes": previous.decision_id,
                "approval_hash": compute_approval_hash(
                    selected_option=selected_option,
                    rationale=rationale,
                    source_refs=payload["source_refs"],
                    affected_requirements=payload["affected_requirements"],
                ),
            }
        )
        revised = DecisionRecord(**payload)
        superseded = previous.model_copy(
            update={
                "validation_status": ValidationStatus.SUPERSEDED,
                "review_status": ReviewStatus.SUPERSEDED,
            }
        )
        self.decisions[self.decisions.index(previous)] = superseded
        self.decisions.append(revised)
        return revised

    def _next_revision_id(self, previous: DecisionRecord) -> str:
        prefix = previous.decision_id + "-r"
        revision_numbers = [
            int(item.decision_id[len(prefix) :])
            for item in self.decisions
            if item.decision_id.startswith(prefix)
            and item.decision_id[len(prefix) :].isdigit()
        ]
        return prefix + str(max(revision_numbers, default=1) + 1)

    @property
    def final_blocked_reasons(self) -> list[str]:
        decision_reasons = [
            (
                f"decision {decision.decision_id} ({decision.topic}) requires "
                f"verification before FINAL: {decision.validation_status}"
            )
            for decision in self.decisions
            if decision.verification_required
            and decision.validation_status is not ValidationStatus.VERIFIED
            and decision.validation_status is not ValidationStatus.SUPERSEDED
        ]
        return decision_reasons + self.academic_scope.final_blocked_reasons

    def can_proceed(self, scenario: DecisionScenario | str) -> bool:
        resolved = DecisionScenario(scenario)
        if resolved is DecisionScenario.STUDY:
            current = [
                decision
                for decision in self.decisions
                if decision.validation_status is not ValidationStatus.SUPERSEDED
            ]
            return all(decision.can_execute for decision in current)
        return not self.final_blocked_reasons

    def can_release(self, scenario: DecisionScenario | str) -> bool:
        return self.can_proceed(scenario)


def load_decision_register(path: str | Path) -> DecisionRegister:
    """Load the checked YAML shape without turning it into executable state."""
    source = Path(path)
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("decision register YAML must contain a mapping")
    return DecisionRegister.model_validate(payload)


__all__ = [
    "AcademicDeliverable",
    "AcademicDeliverableScope",
    "AcademicStatus",
    "DecisionRecord",
    "DecisionRegister",
    "DecisionScenario",
    "FactClass",
    "ReviewStatus",
    "Scenario",
    "SelectionAuthority",
    "SelectionKind",
    "ValidationStatus",
    "build_academic_deliverable_scope",
    "compute_approval_hash",
    "load_decision_register",
]
