from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_PATH = REPO_ROOT / "AGENTS.md"


def test_production_agents_policy_contains_required_rules_and_protocols() -> None:
    assert AGENTS_PATH.exists(), "AGENTS.md is missing"
    policy = AGENTS_PATH.read_text(encoding="utf-8").lower()

    required_rules = (
        "preserve model integrity",
        "never modify golden/source/master",
        "never use an untested provider on production",
        "every bim write gets independent read/verify",
        "never invent missing source data",
        "separate facts, constraints, and hypotheses",
        "requirements are immutable during optimization",
        "no mid-production dependency updates",
        "typed, verified tools first",
        "only registry-approved fallbacks",
        "checkpoint before destructive work",
        "formal task status",
        "never claim success without evidence",
        "if uncertain, preserve the last known-good state",
    )
    for rule in required_rules:
        assert rule in policy, f"missing required rule: {rule}"

    assert "docs/superpowers/plans/" in policy
    assert "2026-09-11-amanda-tfg-bim-agent-combined-plan.md" in policy
    assert (REPO_ROOT / "docs/superpowers/plans").is_dir()
    assert (
        REPO_ROOT / "2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md"
    ).is_file()

    assert "## session-start protocol" in policy
    assert "## session-end protocol" in policy
    assert "superpowers:subagent-driven-development" in policy
    assert "superpowers:systematic-debugging" in policy
    assert "superpowers:verification-before-completion" in policy
