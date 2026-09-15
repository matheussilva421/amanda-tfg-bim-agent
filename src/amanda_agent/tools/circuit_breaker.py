"""Persistent circuit breaking for Revit provider health failures.

The breaker is deliberately scoped by provider, Revit build, capability, and
error signature.  A failure in one scope cannot make a different provider or
operation unavailable, and input validation failures never affect provider
health state.
"""

from __future__ import annotations

import os
import tempfile
import time
from collections.abc import Callable, Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class CircuitState(StrEnum):
    """Lifecycle state of one persisted breaker scope."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class FailureKind(StrEnum):
    """Classification used to keep caller errors out of provider health."""

    PROVIDER_HEALTH = "PROVIDER_HEALTH"
    INPUT = "INPUT"
    VALIDATION = "VALIDATION"

    PROVIDER = "PROVIDER_HEALTH"
    INPUT_ERROR = "INPUT"
    VALIDATION_ERROR = "VALIDATION"


class CircuitBreakerError(RuntimeError):
    """Base class for circuit breaker control errors."""


class CircuitOpenError(CircuitBreakerError):
    """Raised when a caller attempts a blocked provider call."""


class ProbeDenied(CircuitBreakerError):
    """Raised when a HALF_OPEN transition is not controlled or read-only."""


class FailureScope(BaseModel):
    """The durable identity of one provider-health failure stream."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )

    provider: str
    revit_build: str
    capability: str = Field(
        validation_alias=AliasChoices("capability", "operation")
    )
    error_signature: str

    @field_validator("provider", "revit_build", "capability", "error_signature")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("failure scope values cannot be blank")
        return normalized

    @property
    def operation(self) -> str:
        """Return the capability under the operation terminology."""

        return self.capability

    @classmethod
    def from_error(
        cls,
        *,
        provider: str,
        revit_build: str,
        capability: str | None = None,
        operation: str | None = None,
        error: BaseException | str,
    ) -> FailureScope:
        """Build a scope with a stable type-and-message error signature."""

        selected_capability = capability or operation
        if selected_capability is None:
            raise ValueError("capability or operation is required")
        error_type = f"{type(error).__module__}.{type(error).__qualname__}"
        detail = str(error).strip()
        signature = error_type if not detail else f"{error_type}:{detail}"
        return cls(
            provider=provider,
            revit_build=revit_build,
            capability=selected_capability,
            error_signature=signature,
        )


class BreakerRecord(BaseModel):
    """One serialized circuit state and its consecutive failure count."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    revit_build: str
    capability: str
    error_signature: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = Field(default=0, ge=0)
    opened_at: float | None = None
    last_failure_at: float | None = None

    @field_validator("provider", "revit_build", "capability", "error_signature")
    @classmethod
    def _require_non_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("breaker record values cannot be blank")
        return normalized

    @property
    def scope(self) -> FailureScope:
        """Return the record's durable scope as a validated model."""

        return FailureScope(
            provider=self.provider,
            revit_build=self.revit_build,
            capability=self.capability,
            error_signature=self.error_signature,
        )


class CircuitBreaker:
    """Gate provider calls and persist each scope's recovery state.

    ``begin_probe`` is the only method that can move an OPEN scope to
    HALF_OPEN.  It requires an explicit read-only probe and either an elapsed
    cooldown or an explicit remediation confirmation.  A HALF_OPEN scope can
    close only after ``record_success(..., independent=True)``.
    """

    schema_version = 1

    def __init__(
        self,
        path: str | Path,
        scope: FailureScope | Mapping[str, Any] | None = None,
        *,
        provider: str | None = None,
        revit_build: str | None = None,
        capability: str | None = None,
        operation: str | None = None,
        error_signature: str | None = None,
        failure_threshold: int = 3,
        cooldown_seconds: float = 60.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if not isinstance(failure_threshold, int) or isinstance(
            failure_threshold, bool
        ) or failure_threshold < 1:
            raise ValueError("failure_threshold must be a positive integer")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds cannot be negative")

        self.path = Path(path)
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = float(cooldown_seconds)
        self._clock = time.time if clock is None else clock
        self._records: dict[tuple[str, str, str, str], BreakerRecord] = {}
        self._default_scope = self._initial_scope(
            scope,
            provider=provider,
            revit_build=revit_build,
            capability=capability,
            operation=operation,
            error_signature=error_signature,
        )
        self._load()

    # -- inspection -----------------------------------------------------
    @property
    def scope(self) -> FailureScope | None:
        """Return the constructor scope, if this breaker has one."""

        return self._default_scope

    @property
    def state(self) -> CircuitState:
        """Return the default scope state, or CLOSED for an empty breaker."""

        return self.get_state()

    @property
    def records(self) -> tuple[BreakerRecord, ...]:
        """Return an immutable snapshot of all persisted records."""

        return tuple(record.model_copy(deep=True) for record in self._records.values())

    def get_record(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
    ) -> BreakerRecord | None:
        """Return a read-only copy of one scope's record, if present."""

        resolved = self._resolve_scope(scope)
        if resolved is None:
            if len(self._records) == 1:
                return next(iter(self._records.values())).model_copy(deep=True)
            return None
        record = self._records.get(self._key(resolved))
        return None if record is None else record.model_copy(deep=True)

    def get_state(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
    ) -> CircuitState:
        """Return CLOSED for an unseen scope, otherwise its current state."""

        record = self.get_record(scope)
        return CircuitState.CLOSED if record is None else record.state

    def state_for(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
    ) -> CircuitState:
        """Alias for ``get_state`` suitable for callers using state wording."""

        return self.get_state(scope)

    def failure_count(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
    ) -> int:
        """Return the consecutive provider-health failure count."""

        record = self.get_record(scope)
        return 0 if record is None else record.failure_count

    def failure_count_for(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
    ) -> int:
        """Alias for ``failure_count``."""

        return self.failure_count(scope)

    def can_call(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
    ) -> bool:
        """Return whether an ordinary provider call is currently allowed."""

        return self.get_state(scope) is CircuitState.CLOSED

    def allow_call(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
    ) -> bool:
        """Alias for ``can_call``."""

        return self.can_call(scope)

    def is_open(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
    ) -> bool:
        """Return whether a scope is OPEN and blocking calls."""

        return self.get_state(scope) is CircuitState.OPEN

    def assert_can_call(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
    ) -> None:
        """Raise ``CircuitOpenError`` when the scope is not CLOSED."""

        state = self.get_state(scope)
        if state is not CircuitState.CLOSED:
            resolved = self._resolve_scope(scope)
            label = "unknown scope" if resolved is None else repr(resolved.capability)
            raise CircuitOpenError(
                f"provider call blocked for capability {label}: {state.value}"
            )

    # -- state transitions ---------------------------------------------
    def record_failure(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
        *,
        failure_kind: FailureKind | str | None = None,
        error: BaseException | str | None = None,
        error_signature: str | None = None,
        provider_health_failure: bool | None = None,
        input_error: bool = False,
    ) -> CircuitState:
        """Record a provider failure, or ignore an input/validation error.

        A missing signature is represented by ``UNSPECIFIED`` when a
        constructor scope is supplied.  Passing an exception without an
        explicit scope derives a stable signature from its type and message.
        """

        resolved = self._resolve_scope(
            scope,
            error=error,
            error_signature=error_signature,
        )
        kind = self._classify_failure(
            failure_kind,
            error=error,
            input_error=input_error,
            provider_health_failure=provider_health_failure,
        )
        if kind is not FailureKind.PROVIDER_HEALTH:
            return self.get_state(resolved)
        if resolved is None:
            raise ValueError("a failure scope is required for provider failures")

        key = self._key(resolved)
        previous = self._records.get(key)
        record = (
            BreakerRecord(
                provider=resolved.provider,
                revit_build=resolved.revit_build,
                capability=resolved.capability,
                error_signature=resolved.error_signature,
            )
            if previous is None
            else previous.model_copy(deep=True)
        )
        now = float(self._clock())

        if record.state is CircuitState.OPEN:
            return record.state

        record.last_failure_at = now
        if record.state is CircuitState.HALF_OPEN:
            record.failure_count = max(self.failure_threshold, record.failure_count + 1)
            record.state = CircuitState.OPEN
            record.opened_at = now
        else:
            record.failure_count += 1
            if record.failure_count >= self.failure_threshold:
                record.state = CircuitState.OPEN
                record.opened_at = now

        return self._commit(key, record, previous)

    def record_provider_failure(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
        *,
        error: BaseException | str | None = None,
        error_signature: str | None = None,
    ) -> CircuitState:
        """Explicit alias for recording a provider-health failure."""

        return self.record_failure(
            scope,
            failure_kind=FailureKind.PROVIDER_HEALTH,
            error=error,
            error_signature=error_signature,
        )

    def record_input_error(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
    ) -> CircuitState:
        """Record no health failure for caller input rejected before dispatch."""

        return self.record_failure(scope, failure_kind=FailureKind.INPUT)

    def record_validation_error(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
    ) -> CircuitState:
        """Record no health failure for local validation failure."""

        return self.record_failure(scope, failure_kind=FailureKind.VALIDATION)

    def record_success(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
        *,
        independent: bool = False,
        independent_query: bool | None = None,
    ) -> CircuitState:
        """Record success, requiring independent evidence to close a probe."""

        if independent_query is not None:
            independent = independent_query
        resolved = self._resolve_scope(scope)
        if resolved is None:
            return CircuitState.CLOSED
        key = self._key(resolved)
        previous = self._records.get(key)
        if previous is None:
            return CircuitState.CLOSED
        record = previous.model_copy(deep=True)

        if record.state is CircuitState.OPEN:
            return record.state
        if record.state is CircuitState.HALF_OPEN and not independent:
            return record.state

        record.state = CircuitState.CLOSED
        record.failure_count = 0
        record.opened_at = None
        record.last_failure_at = None
        return self._commit(key, record, previous)

    def begin_probe(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
        *,
        read_only: bool,
        remediation_confirmed: bool = False,
        now: float | None = None,
    ) -> bool:
        """Move an OPEN scope to HALF_OPEN for one controlled read probe.

        The method returns ``False`` when the scope is not OPEN or its
        cooldown has not elapsed.  A non-read-only request raises
        ``ProbeDenied`` so a caller cannot accidentally use the probe as a
        write path.
        """

        resolved = self._resolve_scope(scope)
        if resolved is None:
            return False
        key = self._key(resolved)
        previous = self._records.get(key)
        if previous is None or previous.state is not CircuitState.OPEN:
            return False
        if not read_only:
            raise ProbeDenied("HALF_OPEN probes must be read-only")

        current_time = float(self._clock() if now is None else now)
        cooldown_elapsed = previous.opened_at is not None and (
            current_time >= previous.opened_at + self.cooldown_seconds
        )
        if not cooldown_elapsed and not remediation_confirmed:
            return False

        record = previous.model_copy(deep=True)
        record.state = CircuitState.HALF_OPEN
        return_value = self._commit(key, record, previous)
        return return_value is CircuitState.HALF_OPEN

    def probe(
        self,
        scope: FailureScope | Mapping[str, Any] | None = None,
        *,
        read_only: bool,
        remediation_confirmed: bool = False,
        now: float | None = None,
    ) -> bool:
        """Alias for ``begin_probe``."""

        return self.begin_probe(
            scope,
            read_only=read_only,
            remediation_confirmed=remediation_confirmed,
            now=now,
        )

    # -- persistence ----------------------------------------------------
    def save(self) -> Path:
        """Persist the current breaker records using an atomic UTF-8 write."""

        self._save()
        return self.path

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"invalid circuit breaker YAML: {self.path}") from exc
        if not isinstance(payload, Mapping):
            raise TypeError(f"circuit breaker state is not a mapping: {self.path}")
        if payload.get("schema_version", self.schema_version) != self.schema_version:
            raise ValueError(f"unsupported circuit breaker schema: {self.path}")

        raw_records = payload.get("breakers", payload.get("entries", []))
        if not isinstance(raw_records, list):
            raise TypeError("circuit breaker breakers must be a list")
        for raw_record in raw_records:
            if not isinstance(raw_record, Mapping):
                raise TypeError("circuit breaker entries must be mappings")
            values = dict(raw_record)
            nested_scope = values.pop("scope", None)
            if nested_scope is not None:
                if not isinstance(nested_scope, Mapping):
                    raise ValueError("circuit breaker scope must be a mapping")
                merged_scope = dict(nested_scope)
                merged_scope.update(values)
                values = merged_scope
            record = BreakerRecord.model_validate(values)
            key = self._key(record.scope)
            if key in self._records:
                raise ValueError("duplicate circuit breaker scope")
            self._records[key] = record

    def _save(self) -> None:
        payload = {
            "schema_version": self.schema_version,
            "breakers": [
                record.model_dump(mode="json") for record in self._records.values()
            ],
        }
        text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=str(self.path.parent),
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self.path)
        except BaseException:
            temporary_path.unlink(missing_ok=True)
            raise

    # -- helpers --------------------------------------------------------
    @staticmethod
    def _key(scope: FailureScope) -> tuple[str, str, str, str]:
        return (
            scope.provider,
            scope.revit_build,
            scope.capability,
            scope.error_signature,
        )

    @staticmethod
    def _initial_scope(
        scope: FailureScope | Mapping[str, Any] | None,
        *,
        provider: str | None,
        revit_build: str | None,
        capability: str | None,
        operation: str | None,
        error_signature: str | None,
    ) -> FailureScope | None:
        supplied_fields = (
            provider,
            revit_build,
            capability,
            operation,
            error_signature,
        )
        if scope is not None and any(value is not None for value in supplied_fields):
            raise ValueError("scope cannot be combined with scope fields")
        if scope is not None:
            return FailureScope.model_validate(scope)
        if not any(value is not None for value in supplied_fields):
            return None
        selected_capability = capability or operation
        if provider is None or revit_build is None or selected_capability is None:
            raise ValueError(
                "provider, revit_build, and capability/operation are required"
            )
        return FailureScope(
            provider=provider,
            revit_build=revit_build,
            capability=selected_capability,
            error_signature=error_signature or "UNSPECIFIED",
        )

    def _resolve_scope(
        self,
        scope: FailureScope | Mapping[str, Any] | None,
        *,
        error: BaseException | str | None = None,
        error_signature: str | None = None,
    ) -> FailureScope | None:
        if scope is not None:
            return FailureScope.model_validate(scope)
        if self._default_scope is not None:
            selected_signature = error_signature
            if selected_signature is None and error is not None:
                error_type = f"{type(error).__module__}.{type(error).__qualname__}"
                detail = str(error).strip()
                selected_signature = (
                    error_type if not detail else f"{error_type}:{detail}"
                )
            if selected_signature is not None:
                return self._default_scope.model_copy(
                    update={"error_signature": selected_signature}
                )
            return self._default_scope
        if len(self._records) == 1:
            return next(iter(self._records.values())).scope
        return None

    @staticmethod
    def _classify_failure(
        failure_kind: FailureKind | str | None,
        *,
        error: BaseException | str | None,
        input_error: bool,
        provider_health_failure: bool | None,
    ) -> FailureKind:
        if input_error or provider_health_failure is False:
            return FailureKind.INPUT
        if failure_kind is not None:
            try:
                return FailureKind(str(failure_kind).strip().upper())
            except ValueError as exc:
                raise ValueError(f"unknown failure kind: {failure_kind}") from exc
        if isinstance(error, (ValueError, TypeError)) or (
            error is not None and type(error).__name__.endswith("ValidationError")
        ):
            return FailureKind.VALIDATION
        return FailureKind.PROVIDER_HEALTH

    def _commit(
        self,
        key: tuple[str, str, str, str],
        record: BreakerRecord,
        previous: BreakerRecord | None,
    ) -> CircuitState:
        self._records[key] = record
        try:
            self._save()
        except BaseException:
            if previous is None:
                self._records.pop(key, None)
            else:
                self._records[key] = previous
            raise
        return record.state


# Descriptive aliases keep the state vocabulary discoverable to callers that
# use "breaker" instead of "circuit" in their own code.
BreakerState = CircuitState
CircuitBreakerState = CircuitState
ProbeNotAllowed = ProbeDenied


__all__ = [
    "BreakerRecord",
    "BreakerState",
    "CircuitBreaker",
    "CircuitBreakerError",
    "CircuitBreakerState",
    "CircuitOpenError",
    "CircuitState",
    "FailureKind",
    "FailureScope",
    "ProbeDenied",
    "ProbeNotAllowed",
]
