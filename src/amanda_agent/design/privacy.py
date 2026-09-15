"""Deterministic privacy-gradient scoring with auditable transition evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from math import isfinite
from typing import Any

DIRECT_PUBLIC_RESIDENTIAL_PENALTY = 100.0


@dataclass(frozen=True)
class PrivacyGradientResult:
    """Quality and evidence for an ordered privacy transition sequence."""

    score: float
    penalty: float
    valid: bool
    evidence: dict[str, Any]

    @property
    def transition_sequence(self) -> list[int]:
        return list(self.evidence["transition_sequence"])


def _normalise_sequence(sequence: Sequence[Any]) -> tuple[list[int], list[str]]:
    if isinstance(sequence, (str, bytes)) or not sequence:
        raise ValueError("privacy sequence must contain at least one node")
    levels: list[int] = []
    identifiers: list[str] = []
    for item in sequence:
        if isinstance(item, Mapping):
            level = item.get("privacy_level")
            identifier = item.get("id", item.get("logical_id"))
            if identifier is not None:
                identifiers.append(str(identifier))
        else:
            level = item
        if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= 5:
            raise ValueError("privacy levels must be integers from 0 through 5")
        levels.append(level)
    return levels, identifiers


def evaluate_privacy_gradient(sequence: Sequence[Any]) -> PrivacyGradientResult:
    """Score a path from public to private while preserving its raw levels."""

    levels, identifiers = _normalise_sequence(sequence)
    penalty = 0.0
    direct_forbidden = False
    for current, following in pairwise(levels):
        jump = abs(following - current)
        penalty += float(max(0, jump - 1) ** 2)
        if current == 0 and following == 5:
            direct_forbidden = True
            penalty += DIRECT_PUBLIC_RESIDENTIAL_PENALTY
    valid = not direct_forbidden
    score = 1.0 / (1.0 + penalty) if isfinite(penalty) else 0.0
    evidence: dict[str, Any] = {
        "transition_sequence": list(levels),
        "node_ids": identifiers,
        "direct_public_to_residential": direct_forbidden,
    }
    return PrivacyGradientResult(
        score=score,
        penalty=penalty,
        valid=valid,
        evidence=evidence,
    )


def privacy_penalty(sequence: Sequence[Any]) -> float:
    """Return only the numeric privacy penalty for a sequence."""

    return evaluate_privacy_gradient(sequence).penalty


score_privacy_gradient = evaluate_privacy_gradient
compute_privacy_penalty = privacy_penalty


__all__ = [
    "DIRECT_PUBLIC_RESIDENTIAL_PENALTY",
    "PrivacyGradientResult",
    "compute_privacy_penalty",
    "evaluate_privacy_gradient",
    "privacy_penalty",
    "score_privacy_gradient",
]
