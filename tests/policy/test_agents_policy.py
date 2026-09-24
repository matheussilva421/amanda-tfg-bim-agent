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

    for current_path in (
        "start_here.md",
        "docs/spec/current.md",
        "docs/plan/current.md",
        "docs/decisions/decisions.md",
        "state/handoff.md",
    ):
        assert current_path in policy
    assert (REPO_ROOT / "START_HERE.md").is_file()
    assert (REPO_ROOT / "docs/spec/CURRENT.md").is_file()
    assert (REPO_ROOT / "docs/plan/CURRENT.md").is_file()
    assert (REPO_ROOT / "docs/decisions/DECISIONS.md").is_file()
    assert (REPO_ROOT / "state/HANDOFF.md").is_file()

    assert "## session-start protocol" in policy
    assert "## session-end protocol" in policy
    assert "superpowers:subagent-driven-development" in policy
    assert "superpowers:systematic-debugging" in policy
    assert "superpowers:verification-before-completion" in policy
