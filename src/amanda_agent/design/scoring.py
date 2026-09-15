"""Versioned multidimensional scoring with explicit missing-data treatment."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

_DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "design-engine" / "config" / "weights.yaml"


@dataclass(frozen=True)
class ScoreResult:
    raw_metrics: dict[str, float | None]
    normalized_metrics: dict[str, float | None]
    contributions: dict[str, float]
    weighted_total: float
    rebalanced_weight_total: float
    not_evaluated: list[str] = field(default_factory=list)
    weights_version: int = 1
    evidence: dict[str, str] = field(default_factory=dict)

    @property
    def overall_score(self) -> float:
        return self.weighted_total


def load_weight_config(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path is not None else _DEFAULT_CONFIG
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("dimensions"), dict):
        raise TypeError("weights YAML must contain a dimensions mapping")
    return payload


def load_weights(path: str | Path | None = None) -> dict[str, float]:
    return {name: float(item["weight"]) for name, item in load_weight_config(path)["dimensions"].items()}


def _metric_values(metrics: Any) -> dict[str, Any]:
    if hasattr(metrics, "model_dump"):
        values = metrics.model_dump(mode="python")
    elif isinstance(metrics, dict):
        values = dict(metrics)
    else:
        raise TypeError("metrics must be a mapping or Pydantic model")
    values.pop("overall_score", None)
    values.pop("evidence", None)
    return values


def _config_from_weights(weights: dict[str, Any] | None, path: str | Path | None) -> dict[str, Any]:
    config = load_weight_config(path)
    if weights is None:
        return config
    dimensions = config["dimensions"]
    unknown = set(weights) - set(dimensions)
    if unknown:
        raise ValueError("unknown score dimension: " + ", ".join(sorted(unknown)))
    for name, value in weights.items():
        if isinstance(value, dict):
            dimensions[name] = dict(value)
        else:
            dimensions[name] = {**dimensions[name], "weight": float(value)}
    return config


def score_candidate(metrics: Any, *, weights: dict[str, Any] | None = None, weights_path: str | Path | None = None) -> ScoreResult:
    """Normalize configured dimensions and rebalance only evaluated weights."""

    config = _config_from_weights(weights, weights_path)
    dimensions = config["dimensions"]
    values = _metric_values(metrics)
    unknown = set(values) - set(dimensions)
    if unknown:
        raise ValueError("unknown score dimension: " + ", ".join(sorted(unknown)))
    raw: dict[str, float | None] = {}
    normalized: dict[str, float | None] = {}
    not_evaluated: list[str] = []
    evidence: dict[str, str] = {}
    for name, specification in dimensions.items():
        value = values.get(name)
        raw[name] = None if value is None else float(value)
        evidence[name] = str(specification.get("evidence_source", "unspecified"))
        if value is None:
            normalized[name] = None
            not_evaluated.append(name)
            continue
        value = float(value)
        if not isfinite(value):
            raise ValueError(f"score dimension {name} must be finite")
        lower, upper = (float(item) for item in specification["bounds"])
        if value < lower or value > upper:
            raise ValueError(f"score dimension {name} is outside configured bounds")
        ratio = (value - lower) / max(upper - lower, 1e-12)
        if specification["direction"] == "lower":
            ratio = 1.0 - ratio
        normalized[name] = ratio
    evaluated = [name for name in dimensions if normalized[name] is not None]
    evaluated_weight = sum(float(dimensions[name]["weight"]) for name in evaluated)
    contributions = {
        name: cast(float, normalized[name]) * float(dimensions[name]["weight"]) / evaluated_weight
        for name in evaluated
    }
    total = sum(contributions.values())
    return ScoreResult(raw_metrics=raw, normalized_metrics=normalized, contributions=contributions, weighted_total=float(total), rebalanced_weight_total=float(total), not_evaluated=not_evaluated, weights_version=int(config.get("version", 1)), evidence=evidence)


score = score_candidate


__all__ = ["ScoreResult", "load_weight_config", "load_weights", "score", "score_candidate"]
