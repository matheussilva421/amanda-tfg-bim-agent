"""Evidence-bound finalist explanations and WHY_THIS_OPTION.md output."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Explanation:
    strengths: list[str] = field(default_factory=list)
    tradeoffs: list[str] = field(default_factory=list)
    hard_violations: list[str] = field(default_factory=list)
    source_principles: list[str] = field(default_factory=list)
    design_hypotheses: list[str] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)


def _value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def explain_candidate(candidate: Any, comparisons: list[Any] | None = None) -> Explanation:
    metrics = dict(_value(candidate, "metrics", {}) or {})
    strengths = [f"{name}={float(value):.3f} is a high raw metric" for name, value in sorted(metrics.items()) if value is not None and float(value) >= 0.8]
    penalties = dict(_value(candidate, "soft_penalties", {}) or {})
    tradeoffs = [f"{name} incurs soft penalty {float(value):.3f}" for name, value in sorted(penalties.items()) if float(value) > 0]
    tradeoffs.extend(f"{name}={float(value):.3f} is a lower raw metric" for name, value in sorted(metrics.items()) if value is not None and float(value) < 0.6)
    if comparisons:
        tradeoffs.extend(f"relative comparison includes {len(comparisons)} alternatives" for _ in [0])
    hard: list[str] = []
    for violation in list(_value(candidate, "hard_violations", []) or []):
        if isinstance(violation, dict):
            hard.append(f"{violation.get('code', 'unknown')}: {violation.get('message', '')}".rstrip())
        else:
            hard.append(str(violation))
    provenance = dict(_value(candidate, "provenance", {}) or {})
    return Explanation(
        strengths=strengths,
        tradeoffs=tradeoffs,
        hard_violations=hard,
        source_principles=[str(item) for item in (provenance.get("source_principles", []) or [])],
        design_hypotheses=[str(item) for item in (provenance.get("hypotheses", provenance.get("design_hypotheses", [])) or [])],
        provenance=[str(item) for item in (provenance.get("refs", provenance.get("source_refs", [])) or [])],
    )


def explanation_markdown(explanation: Explanation, *, solution_id: str = "candidate") -> str:
    def section(title: str, values: list[str]) -> str:
        lines = "\n".join(f"- {item}" for item in values) or "- None recorded"
        return f"## {title}\n\n{lines}\n"

    return "\n".join([
        "# WHY_THIS_OPTION",
        "",
        f"Candidate: `{solution_id}`",
        "",
        section("Strengths", explanation.strengths),
        section("Tradeoffs", explanation.tradeoffs),
        section("Hard violations", explanation.hard_violations),
        section("Source principles", explanation.source_principles),
        section("Design hypotheses", explanation.design_hypotheses),
        section("Provenance", explanation.provenance),
        "No unsupported claims: every statement above is derived from structured candidate data.",
        "",
    ])


def write_why_this_option(candidate: Any, path: str | Path, *, comparisons: list[Any] | None = None) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    solution_id = str(_value(candidate, "id", _value(candidate, "solution_id", "candidate")))
    target.write_text(explanation_markdown(explain_candidate(candidate, comparisons), solution_id=solution_id), encoding="utf-8", newline="\n")
    return target


generate_explanation = explain_candidate
write_explanation = write_why_this_option


__all__ = ["Explanation", "explain_candidate", "explanation_markdown", "generate_explanation", "write_explanation", "write_why_this_option"]
