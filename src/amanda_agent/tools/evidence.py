"""Evidence records for Revit capability tests.

The record keeps the observation made by a provider separate from the
capability registry entry.  A provider success flag is only one input to the
promotion bridge; file hashes, model re-queries, and persistence evidence are
validated before a :class:`ProviderCapability` is produced.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from amanda_agent.models.capability import (
    EVIDENCE_REFERENCE,
    CapabilityStatus,
    EvidenceScope,
    ProviderCapability,
)


class EvidenceValidationError(ValueError):
    """Raised when an evidence record cannot be promoted to a capability."""


def _references(value: str | Iterable[str] | None) -> list[str]:
    """Normalize one or more evidence references to a list of strings."""

    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def evidence_reference(path: str | Path) -> str:
    """Return a hashed evidence reference for an existing artifact."""

    artifact = Path(path)
    if not artifact.is_file():
        raise EvidenceValidationError(f"{artifact}: evidence file is missing")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    return f"{artifact}::sha256={digest}"


def verify_evidence_reference(reference: str) -> Path:
    """Verify a ``path::sha256=<hash>`` reference and return its path."""

    match = EVIDENCE_REFERENCE.search(reference)
    if match is None:
        raise EvidenceValidationError(
            f"{reference}: evidence reference has no ::sha256=<hash> suffix"
        )
    raw_path = reference[: match.start()]
    if not raw_path:
        raise EvidenceValidationError("evidence reference path cannot be blank")
    artifact = Path(raw_path)
    if not artifact.is_file():
        raise EvidenceValidationError(f"{raw_path}: evidence file is missing")
    actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if actual != match.group(1):
        raise EvidenceValidationError(f"{raw_path}: evidence hash mismatch")
    return artifact


def validate_evidence_references(references: Iterable[str]) -> tuple[str, ...]:
    """Verify and return unique evidence references in their original order."""

    unique: list[str] = []
    seen: set[str] = set()
    for reference in references:
        if reference in seen:
            continue
        verify_evidence_reference(reference)
        seen.add(reference)
        unique.append(reference)
    return tuple(unique)


class ModelQueryEvidence(BaseModel):
    """Evidence from an independent read of the Revit model after a call."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    independent: bool = Field(
        default=False,
        validation_alias=AliasChoices("independent", "independent_query"),
    )
    references: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "references", "evidence", "evidence_references"
        ),
    )
    result: Any = Field(
        default=None,
        validation_alias=AliasChoices("result", "output", "query_result"),
    )

    @field_validator("references", mode="before")
    @classmethod
    def _normalize_references(cls, value: str | Iterable[str] | None) -> list[str]:
        return _references(value)

    @classmethod
    def from_value(cls, value: Any) -> ModelQueryEvidence:
        """Coerce a fixture-friendly query evidence value to the model."""

        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(independent=True, references=[value])
        if isinstance(value, Mapping):
            payload = dict(value)
            for key in ("reference", "path"):
                if key in payload and "references" not in payload:
                    payload["references"] = [payload[key]]
                    break
            return cls.model_validate(payload)
        raise TypeError("model_query_evidence must be a mapping or reference")

    @property
    def has_payload(self) -> bool:
        """Whether the record contains a query result or a stored artifact."""

        return bool(self.references) or self.result is not None

    @property
    def is_independent(self) -> bool:
        """Whether usable independent model-query evidence is present."""

        return self.independent and self.has_payload


class SaveReopenResult(BaseModel):
    """Result of saving, closing, reopening, and checking the model again."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    success: bool = Field(
        default=False,
        validation_alias=AliasChoices("success", "passed", "ok"),
    )
    references: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "references", "evidence", "evidence_references"
        ),
    )
    details: Any = None

    @field_validator("references", mode="before")
    @classmethod
    def _normalize_references(cls, value: str | Iterable[str] | None) -> list[str]:
        return _references(value)

    @classmethod
    def from_value(cls, value: Any) -> SaveReopenResult:
        """Coerce a boolean or mapping into a typed persistence result."""

        if isinstance(value, cls):
            return value
        if isinstance(value, bool):
            return cls(success=value)
        if isinstance(value, Mapping):
            return cls.model_validate(value)
        raise TypeError("save_reopen_result must be a boolean or mapping")


class EvidenceRecord(BaseModel):
    """One provider/tool capability test and its independently checked outputs."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    provider: str
    tool: str
    input_fixture_reference: str = Field(
        validation_alias=AliasChoices(
            "input_fixture_reference", "input_fixture", "input_fixture_ref"
        )
    )
    raw_output_path: str = Field(
        validation_alias=AliasChoices(
            "raw_output_path", "raw_output", "raw_output_reference"
        )
    )
    model_query_evidence: ModelQueryEvidence | None = Field(
        default=None,
        validation_alias=AliasChoices("model_query_evidence", "model_query"),
    )
    warnings_delta: int = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("warnings_delta", "warning_delta"),
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        validation_alias=AliasChoices("duration_seconds", "duration"),
    )
    save_reopen_result: SaveReopenResult = Field(
        default_factory=SaveReopenResult,
        validation_alias=AliasChoices("save_reopen_result", "save_reopen"),
    )
    artifact_hashes: list[str] = Field(default_factory=list)
    success: bool = False

    # Capability metadata is copied into ProviderCapability by the bridge.
    status: CapabilityStatus | None = None
    priority: int = 0
    provider_commit: str | None = None
    transport_provider: str | None = None
    tool_schema_hash: str | None = None
    tested_scope: dict[str, Any] = Field(default_factory=dict)
    writes: bool | None = None
    evidence_scope: EvidenceScope = EvidenceScope.SYNTHETIC
    revit_build: str | None = None
    limitations: list[str] = Field(default_factory=list)

    @field_validator("model_query_evidence", mode="before")
    @classmethod
    def _normalize_model_query(
        cls, value: Any
    ) -> ModelQueryEvidence | None:
        if value is None or isinstance(value, ModelQueryEvidence):
            return value
        return ModelQueryEvidence.from_value(value)

    @field_validator("save_reopen_result", mode="before")
    @classmethod
    def _normalize_save_reopen(cls, value: Any) -> SaveReopenResult:
        return SaveReopenResult.from_value(value)

    @field_validator("artifact_hashes", mode="before")
    @classmethod
    def _normalize_artifact_hashes(
        cls, value: str | Iterable[str] | None
    ) -> list[str]:
        return _references(value)

    @property
    def duration(self) -> float:
        """Return the measured duration in seconds."""

        return self.duration_seconds

    @property
    def save_reopen(self) -> bool:
        """Return whether the save/close/reopen check passed."""

        return self.save_reopen_result.success

    @property
    def independent_query(self) -> bool:
        """Return whether an independent model re-query is evidenced."""

        return bool(
            self.model_query_evidence
            and self.model_query_evidence.is_independent
        )

    @property
    def effective_tested_scope(self) -> dict[str, Any]:
        """Return the scope with the tool and write flag made explicit."""

        scope = dict(self.tested_scope)
        scope.setdefault("operation", self.tool)
        if self.writes is not None:
            scope.setdefault("writes", self.writes)
        else:
            scope.setdefault("writes", False)
        return scope

    @property
    def is_write(self) -> bool:
        """Return whether this test exercises a mutating operation."""

        return self.effective_tested_scope.get("writes") is True

    @property
    def capability_status(self) -> CapabilityStatus:
        """Return the status that the bridge will put in the registry."""

        if self.status is not None:
            return self.status
        if not self.success:
            return CapabilityStatus.FAIL
        if self.warnings_delta:
            return CapabilityStatus.PASS_WITH_WARNINGS
        return CapabilityStatus.PASS

    @property
    def evidence_references(self) -> tuple[str, ...]:
        """Return all artifact references carried by this test result."""

        references: list[str] = [
            self.input_fixture_reference,
            self.raw_output_path,
        ]
        if self.model_query_evidence is not None:
            references.extend(self.model_query_evidence.references)
        references.extend(self.save_reopen_result.references)
        references.extend(self.artifact_hashes)

        unique: list[str] = []
        seen: set[str] = set()
        for reference in references:
            if reference not in seen:
                seen.add(reference)
                unique.append(reference)
        return tuple(unique)

    def validate_for_capability(self) -> EvidenceRecord:
        """Validate evidence invariants before capability serialization."""

        status = self.capability_status
        passing = status in {
            CapabilityStatus.PASS,
            CapabilityStatus.PASS_WITH_WARNINGS,
        }
        if passing and not self.success:
            raise EvidenceValidationError(
                "capability PASS status requires success=True"
            )
        if self.status is CapabilityStatus.PASS_WITH_WARNINGS and not self.warnings_delta:
            raise EvidenceValidationError(
                "PASS_WITH_WARNINGS requires a positive warnings_delta"
            )

        if passing and self.is_write and not self.independent_query:
            raise EvidenceValidationError(
                "write capability PASS requires independent model-query evidence "
                "from an independent re-read from Revit"
            )
        if passing and self.is_write and not self.save_reopen:
            raise EvidenceValidationError(
                "write capability PASS requires save/reopen persistence evidence"
            )

        missing = {
            "provider_commit": self.provider_commit,
            "transport_provider": self.transport_provider,
            "tool_schema_hash": self.tool_schema_hash,
            "revit_build": self.revit_build,
        }
        if passing:
            absent = [name for name, value in missing.items() if not value]
            if absent:
                raise EvidenceValidationError(
                    "capability PASS is incomplete (missing "
                    + ", ".join(absent)
                    + ")"
                )
            scope = self.effective_tested_scope
            if not isinstance(scope.get("operation"), str) or not scope["operation"]:
                raise EvidenceValidationError(
                    "capability PASS requires tested_scope.operation"
                )
            if not isinstance(scope.get("writes"), bool):
                raise EvidenceValidationError(
                    "capability PASS requires tested_scope.writes"
                )

        validate_evidence_references(self.evidence_references)
        return self

    def to_provider_capability(self) -> ProviderCapability:
        """Validate this record and bridge it into the capability registry."""

        self.validate_for_capability()
        return ProviderCapability(
            provider=self.provider,
            status=self.capability_status,
            priority=self.priority,
            provider_commit=self.provider_commit,
            transport_provider=self.transport_provider,
            tool_schema_hash=self.tool_schema_hash,
            tested_scope=self.effective_tested_scope,
            evidence_scope=self.evidence_scope,
            revit_build=self.revit_build,
            save_reopen=self.save_reopen,
            independent_query=self.independent_query,
            warnings_delta=self.warnings_delta,
            evidence=list(self.evidence_references),
            limitations=list(self.limitations),
        )

    # Short aliases keep the bridge discoverable for callers that call the
    # operation a serializer or simply ask for a capability.
    def to_capability(self) -> ProviderCapability:
        """Alias for :meth:`to_provider_capability`."""

        return self.to_provider_capability()

    def serialize(self) -> ProviderCapability:
        """Alias for :meth:`to_provider_capability`."""

        return self.to_provider_capability()


CapabilityEvidenceRecord = EvidenceRecord
CapabilityTestResult = EvidenceRecord


def to_provider_capability(record: EvidenceRecord) -> ProviderCapability:
    """Bridge a validated evidence record into the capability registry."""

    return record.to_provider_capability()


__all__ = [
    "CapabilityEvidenceRecord",
    "CapabilityTestResult",
    "EvidenceRecord",
    "EvidenceValidationError",
    "ModelQueryEvidence",
    "SaveReopenResult",
    "evidence_reference",
    "to_provider_capability",
    "validate_evidence_references",
    "verify_evidence_reference",
]
