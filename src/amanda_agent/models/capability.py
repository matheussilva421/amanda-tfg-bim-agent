"""Deterministic capability registry for Revit providers (P02-T01).

A record can always be written, including UNTESTED and FAIL. Selection is the
part that is strict: production asks the registry for an operation and gets
either a capability whose evidence survives every invariant, or a
SelectionRefused explaining what is missing. A status field alone is never a
promotion.
"""

from __future__ import annotations

import hashlib
import os
import re
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

EVIDENCE_REFERENCE = re.compile(r"::sha256=([0-9a-f]{64})$")


class CapabilityStatus(StrEnum):
    """Lifecycle of a tested capability, not a claim about the provider."""

    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    DEGRADED = "DEGRADED"
    UNTESTED = "UNTESTED"
    FAIL = "FAIL"
    RETIRED = "RETIRED"


class EvidenceScope(StrEnum):
    """How far evidence travels: fixture, real provider, real production run."""

    SYNTHETIC = "SYNTHETIC"
    PROVIDER = "PROVIDER"
    PRODUCTION = "PRODUCTION"


SCOPE_RANK = {
    EvidenceScope.SYNTHETIC: 0,
    EvidenceScope.PROVIDER: 1,
    EvidenceScope.PRODUCTION: 2,
}

NEVER_SELECTABLE = (
    CapabilityStatus.FAIL,
    CapabilityStatus.RETIRED,
    CapabilityStatus.UNTESTED,
    CapabilityStatus.DEGRADED,
)


class SelectionRefused(RuntimeError):
    """Raised when no capability can satisfy a selection request."""


class ProviderCapability(BaseModel):
    """One provider proving one operation on one Revit build."""

    provider: str
    status: CapabilityStatus
    priority: int
    provider_commit: str | None = None
    transport_provider: str | None = None
    tool_schema_hash: str | None = None
    tested_scope: dict = Field(default_factory=dict)
    tested_scope_aliases: tuple[str, ...] = ()
    evidence_scope: EvidenceScope = EvidenceScope.SYNTHETIC
    revit_build: str | None = None
    save_reopen: bool = False
    independent_query: bool = False
    transport_healthy: bool = True
    warnings_delta: int = 0
    evidence: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    @field_validator("tested_scope")
    @classmethod
    def _scope_keys_must_be_strings(cls, value: dict) -> dict:
        for key in value:
            if not isinstance(key, str):
                raise ValueError("tested_scope keys must be strings")  # noqa: TRY004
        return value

    @property
    def operation(self) -> str | None:
        value = self.tested_scope.get("operation")
        return value if isinstance(value, str) else None

    @property
    def is_write(self) -> bool:
        return self.tested_scope.get("writes") is True

    @property
    def operations(self) -> tuple[str, ...]:
        """Every spelling this record answers to, provider name first.

        A record carries the provider's own short operation name plus the
        semantic names the stage vocabulary uses for it. Selection reads this
        tuple so a proven capability is reachable under both spellings.
        """

        names: list[str] = []
        if self.operation is not None:
            names.append(self.operation)
        for alias in self.tested_scope_aliases:
            if alias and alias not in names:
                names.append(alias)
        return tuple(names)


def _missing_fields(entry: ProviderCapability) -> list[str]:
    missing: list[str] = []
    if not entry.provider_commit:
        missing.append("provider_commit")
    if not entry.transport_provider:
        missing.append("transport_provider")
    if not entry.tool_schema_hash:
        missing.append("tool_schema_hash")
    if not entry.revit_build:
        missing.append("revit_build")
    if not entry.evidence:
        missing.append("evidence")
    if not entry.operation:
        missing.append("tested_scope.operation")
    if "writes" not in entry.tested_scope:
        missing.append("tested_scope.writes")
    return missing


def _evidence_problem(reference: str) -> str | None:
    match = EVIDENCE_REFERENCE.search(reference)
    if match is None:
        return f"{reference}: evidence reference has no ::sha256=<hash> suffix"
    raw_path = reference[: match.start()]
    path = Path(raw_path)
    if not path.is_file():
        return f"{raw_path}: evidence file is missing"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != match.group(1):
        return f"{raw_path}: evidence hash mismatch"
    return None


class SemanticCrosswalk(BaseModel):
    """Declared bindings from provider operation names to semantic names."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    generated_utc: str | None = None
    rule: str | None = None
    provenance: dict = Field(default_factory=dict)
    rows: list[dict] = Field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> SemanticCrosswalk:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls.model_validate(payload)

    def aliases(self) -> dict[str, tuple[str, ...]]:
        """Map each registered entry name to the semantic names it answers to."""

        mapping: dict[str, list[str]] = {}
        for row in self.rows:
            semantic = row.get("semantic")
            entry = row.get("registered_entry")
            if not isinstance(semantic, str) or not semantic:
                raise ValueError("crosswalk row has no semantic name")
            if entry in (None, ""):
                continue
            if not isinstance(entry, str):
                raise ValueError(f"crosswalk row {semantic} has a non-string entry")
            names = mapping.setdefault(entry, [])
            if semantic not in names:
                names.append(semantic)
        return {key: tuple(value) for key, value in mapping.items()}

    def apply(self, registry: CapabilityRegistry) -> CapabilityRegistry:
        """Return a registry whose entries also answer to the semantic names.

        A row that names an entry the registry does not hold raises: a declared
        binding with nothing behind it would let a stage believe a capability
        exists. A row with no registered entry is a recorded gap and is skipped.
        """

        known = {entry.operation for entry in registry.entries if entry.operation}
        aliases = self.aliases()
        unknown = sorted(name for name in aliases if name not in known)
        if unknown:
            joined = ", ".join(unknown)
            raise ValueError(f"crosswalk claims unregistered entries: {joined}")
        entries: list[ProviderCapability] = []
        for entry in registry.entries:
            extra = tuple(aliases.get(entry.operation or "", ()))
            merged = tuple(dict.fromkeys((*entry.tested_scope_aliases, *extra)))
            entries.append(entry.model_copy(update={"tested_scope_aliases": merged}))
        gaps = dict(registry.declared_gaps)
        for row in self.rows:
            if row.get("registered_entry") not in (None, ""):
                continue
            semantic = row.get("semantic")
            if not isinstance(semantic, str) or not semantic:
                raise ValueError("crosswalk row has no semantic name")
            note = row.get("gap")
            gaps[semantic] = note if isinstance(note, str) and note else "no registered entry"
        return registry.model_copy(update={"entries": entries, "declared_gaps": gaps})


class CapabilityRegistry(BaseModel):
    """Append-only capability evidence store with a strict selector."""

    schema_version: int = 1
    generated_utc: str | None = None
    preferred_provider: str | None = None
    entries: list[ProviderCapability] = Field(default_factory=list)
    declared_gaps: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def load_with_crosswalk(cls, registry_path: str | Path, crosswalk_path: str | Path):
        """Load the registry and read the declared semantic vocabulary into it.

        The crosswalk is the only place a provider's short operation name is
        bound to the semantic name the BIM stages ask for, and it may only
        claim entries the registry already holds. Selecting a semantic name
        this way reads exactly the evidence recorded for its provider route;
        it never invents an entry or promotes an evidence scope.
        """

        crosswalk = SemanticCrosswalk.load(crosswalk_path)
        registry = cls.load(registry_path)
        return crosswalk.apply(registry)

    @classmethod
    def load_for_production(cls, project_root: str | Path):
        """Load the registry the production path selects from, with warnings.

        The declared crosswalk is read whenever it is present, so a semantic
        operation name resolves to exactly the evidence recorded for its
        provider route. When the file is missing the loader falls back to the
        provider-only names and says so; it never invents aliases. Declared
        gaps are returned as warnings and remain refusals at selection time.
        """

        root = Path(project_root)
        registry_path = root / "state" / "capabilities.yaml"
        crosswalk_path = root / "state" / "providers" / "semantic-crosswalk.yaml"
        warnings: list[str] = []
        if crosswalk_path.is_file():
            registry = cls.load_with_crosswalk(registry_path, crosswalk_path)
        else:
            warnings.append(
                f"semantic crosswalk not found at {crosswalk_path}; selecting with "
                "provider names only, without semantic aliases"
            )
            registry = cls.load(registry_path)
        for operation, gap in sorted(registry.declared_gaps.items()):
            warnings.append(f"gap declarado no crosswalk: {operation}: {gap}")
        return registry, tuple(warnings)

    def record(self, entry: ProviderCapability) -> ProviderCapability:
        self.entries.append(entry)
        return entry

    def for_operation(self, operation: str) -> list[ProviderCapability]:
        return [entry for entry in self.entries if operation in entry.operations]

    def gap_note(self, operation: str) -> str | None:
        """The declared crosswalk gap for an operation, when one is recorded."""

        return self.declared_gaps.get(operation)

    def refusals(
        self,
        operation: str,
        *,
        revit_build: str,
        tool_schema_hash: str,
        scope: EvidenceScope = EvidenceScope.PRODUCTION,
        accept_pass_with_warnings: bool = False,
    ) -> list[str]:
        """Return one refusal reason per candidate that cannot be used."""

        reasons: list[str] = []
        candidates = self.for_operation(operation)
        if not candidates:
            gap = self.declared_gaps.get(operation)
            if gap is not None:
                reasons.append(f"gap declarado no crosswalk: {gap}")
        for entry in candidates:
            reason = self._refusal(
                entry,
                revit_build=revit_build,
                tool_schema_hash=tool_schema_hash,
                scope=scope,
                accept_pass_with_warnings=accept_pass_with_warnings,
            )
            if reason is not None:
                reasons.append(reason)
        return reasons

    def _refusal(
        self,
        entry: ProviderCapability,
        *,
        revit_build: str,
        tool_schema_hash: str,
        scope: EvidenceScope,
        accept_pass_with_warnings: bool,
    ) -> str | None:
        label = entry.provider
        missing = _missing_fields(entry)
        if missing:
            joined = ", ".join(missing)
            return f"{label}: incomplete evidence record (missing {joined})"
        if entry.status in NEVER_SELECTABLE:
            return f"{label}: status {entry.status.value} is never selectable"
        if entry.status is CapabilityStatus.PASS_WITH_WARNINGS:
            if entry.warnings_delta <= 0:
                return f"{label}: PASS_WITH_WARNINGS needs a positive warnings_delta"
            if not accept_pass_with_warnings:
                return (
                    f"{label}: PASS_WITH_WARNINGS (warnings_delta={entry.warnings_delta}) "
                    "requires explicit acceptance"
                )
        if entry.revit_build != revit_build:
            return f"{label}: revit build {entry.revit_build} is not the requested {revit_build}"
        if entry.tool_schema_hash != tool_schema_hash:
            return f"{label}: tool schema hash {entry.tool_schema_hash} is stale"
        if not entry.transport_healthy:
            return f"{label}: transport {entry.transport_provider} is not healthy"
        if scope is not EvidenceScope.SYNTHETIC and entry.evidence_scope is EvidenceScope.SYNTHETIC:
            return (
                f"{label}: synthetic-only evidence cannot "
                f"satisfy a {scope.value} selection"
            )
        if entry.is_write and not entry.independent_query:
            return f"{label}: write capability needs an independent model re-query"
        if entry.is_write and not entry.save_reopen:
            return f"{label}: write capability needs save/reopen persistence proof"
        for reference in entry.evidence:
            problem = _evidence_problem(reference)
            if problem is not None:
                return f"{label}: {problem}"
        return None

    def preferred(
        self,
        *,
        operation: str,
        revit_build: str,
        tool_schema_hash: str,
        scope: EvidenceScope = EvidenceScope.PRODUCTION,
        accept_pass_with_warnings: bool = False,
    ) -> ProviderCapability:
        """Return the single best capability or refuse with every reason."""

        candidates = self.for_operation(operation)
        if not candidates:
            gap = self.declared_gaps.get(operation)
            if gap is not None:
                raise SelectionRefused(
                    f"gap declarado no crosswalk for {operation!r}: {gap}"
                )
            raise SelectionRefused(f"no capability recorded for operation {operation!r}")

        usable = [
            entry
            for entry in candidates
            if self._refusal(
                entry,
                revit_build=revit_build,
                tool_schema_hash=tool_schema_hash,
                scope=scope,
                accept_pass_with_warnings=accept_pass_with_warnings,
            )
            is None
        ]
        if not usable:
            reasons = self.refusals(
                operation,
                revit_build=revit_build,
                tool_schema_hash=tool_schema_hash,
                scope=scope,
                accept_pass_with_warnings=accept_pass_with_warnings,
            )
            raise SelectionRefused(
                f"no usable capability for operation {operation!r}: " + "; ".join(reasons)
            )

        def rank(entry: ProviderCapability) -> tuple[int, int, str]:
            status_rank = 0 if entry.status is CapabilityStatus.PASS else 1
            return (status_rank, entry.priority, entry.provider)

        return min(usable, key=rank)

    def save(self, path: str | Path) -> Path:
        """Persist atomically; a reader never sees a half-written registry."""

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self.model_dump(mode="json")
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        os.replace(temporary, target)
        return target

    @classmethod
    def load(cls, path: str | Path) -> CapabilityRegistry:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls.model_validate(payload)
