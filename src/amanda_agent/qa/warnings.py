"""Versioned warning baselines and fail-closed warning deltas."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field


class WarningBaselineEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    regex: str = ""
    text: str = ""
    severity: str = "MEDIUM"
    status: str = "KNOWN"
    reason: str = ""
    provenance: dict[str, Any] = Field(default_factory=dict)


class WarningBaseline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(ge=1)
    severity_map_version: int = Field(ge=1)
    severity_map: dict[str, str] = Field(default_factory=dict)
    entries: list[WarningBaselineEntry] = Field(default_factory=list)


class WarningObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    text: str = ""
    severity: str
    status: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    baseline_id: str | None = None

    @property
    def is_new(self) -> bool:
        return self.status in {"NEW", "REVIEW"}


class WarningDelta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseline_schema_version: int
    severity_map_version: int
    known: list[WarningObservation] = Field(default_factory=list)
    new: list[WarningObservation] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def _default_baseline_path() -> Path:
    return Path(__file__).resolve().parents[3] / "state" / "known-warnings.yaml"


def load_warning_baseline(
    source: Mapping[str, Any] | str | Path | None = None,
) -> WarningBaseline:
    """Load a versioned baseline from YAML or an injected mapping."""

    if source is None:
        source = _default_baseline_path()
    if isinstance(source, Mapping):
        return WarningBaseline.model_validate(dict(source))
    payload = yaml.safe_load(Path(source).read_text(encoding="utf-8")) or {}
    return WarningBaseline.model_validate(payload)


def _warning_value(value: Any, index: int) -> tuple[str, str, dict[str, Any]]:
    if isinstance(value, str):
        return f"warning-{index}", value, {"text": value}
    if not isinstance(value, Mapping):
        text = str(value)
        return f"warning-{index}", text, {"text": text}
    identifier = str(value.get("id", value.get("code", f"warning-{index}")))
    text = str(value.get("text", value.get("message", "")))
    evidence = dict(value.get("evidence", {}) or {})
    evidence.setdefault("id", identifier)
    evidence.setdefault("text", text)
    if value.get("query") is not None:
        evidence["query"] = value["query"]
    return identifier, text, evidence


def _entry_for(
    identifier: str,
    text: str,
    entries: Sequence[WarningBaselineEntry],
) -> WarningBaselineEntry | None:
    for entry in entries:
        if identifier == entry.id:
            return entry
    for entry in entries:
        if entry.regex:
            try:
                if re.search(entry.regex, text, flags=re.IGNORECASE):
                    return entry
            except re.error:
                continue
    return None


def compare_warnings(
    baseline: WarningBaseline | Mapping[str, Any] | str | Path,
    current_warnings: Sequence[Mapping[str, Any] | str] | None,
    *,
    query_evidence: Mapping[str, Any] | None = None,
) -> WarningDelta:
    """Compare current provider warnings with a baseline without silencing any."""

    record = baseline if isinstance(baseline, WarningBaseline) else load_warning_baseline(baseline)
    known: list[WarningObservation] = []
    new: list[WarningObservation] = []
    for index, current in enumerate(current_warnings or [], start=1):
        identifier, text, evidence = _warning_value(current, index)
        if query_evidence and identifier in query_evidence:
            supplied = query_evidence[identifier]
            evidence["query"] = supplied
        entry = _entry_for(identifier, text, record.entries)
        if entry is not None:
            severity = record.severity_map.get(identifier, entry.severity)
            known.append(
                WarningObservation(
                    id=identifier,
                    text=text,
                    severity=severity,
                    status="KNOWN",
                    evidence={**evidence, "baseline_id": entry.id},
                    baseline_id=entry.id,
                )
            )
            continue

        # A query-backed observation is a concrete new delta. An observation
        # without query provenance remains reviewable as an unknown warning.
        status = "NEW" if "query" in evidence else "REVIEW"
        new.append(
            WarningObservation(
                id=identifier,
                text=text,
                severity="REVIEW",
                status=status,
                evidence=evidence,
            )
        )
    return WarningDelta(
        baseline_schema_version=record.schema_version,
        severity_map_version=record.severity_map_version,
        known=known,
        new=new,
    )


compare_warning_delta = compare_warnings
warning_delta = compare_warnings


__all__ = [
    "WarningBaseline",
    "WarningBaselineEntry",
    "WarningDelta",
    "WarningObservation",
    "compare_warning_delta",
    "compare_warnings",
    "load_warning_baseline",
    "warning_delta",
]
