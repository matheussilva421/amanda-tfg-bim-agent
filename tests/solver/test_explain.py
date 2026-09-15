from __future__ import annotations

from pathlib import Path

from amanda_agent.design.explain import explain_candidate, write_why_this_option


def test_explanation_uses_high_metrics_penalties_and_hard_violations():
    candidate = {
        "id": "sol-1",
        "metrics": {"privacy_security": 0.95, "program_compliance": 0.9, "circulation": 0.4},
        "soft_penalties": {"adjacency": 2.0},
        "hard_violations": [{"code": "route_missing", "message": "route unavailable"}],
        "provenance": {"source_principles": ["privacy gradient"], "hypotheses": ["planar placeholder"]},
    }

    explanation = explain_candidate(candidate)

    assert any("privacy_security" in item for item in explanation.strengths)
    assert any("adjacency" in item for item in explanation.tradeoffs)
    assert explanation.hard_violations == ["route_missing: route unavailable"]
    assert explanation.source_principles == ["privacy gradient"]
    assert explanation.design_hypotheses == ["planar placeholder"]


def test_markdown_is_generated_only_from_structured_explanation(tmp_path: Path):
    candidate = {
        "id": "sol-1",
        "metrics": {"program_compliance": 1.0},
        "soft_penalties": {},
        "hard_violations": [],
        "provenance": {"source_principles": ["fixed program"], "hypotheses": []},
    }
    target = tmp_path / "WHY_THIS_OPTION.md"

    write_why_this_option(candidate, target)

    content = target.read_text(encoding="utf-8")
    assert content.startswith("# WHY_THIS_OPTION")
    assert "fixed program" in content
    assert "No unsupported claims" in content

