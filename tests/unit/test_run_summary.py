from pathlib import Path

from amanda_agent.session.summary import (
    RunSummary,
    render_run_summary,
    write_run_summary,
)


def test_run_summary_covers_outcomes_links_and_provider_fallback():
    summary = RunSummary(
        attempted=["P07-T17"],
        changed=["state/status.md"],
        passed=["pytest focused suite"],
        failed=[],
        rolled_back=["provider update experiment"],
        next_tasks=["P07-T18"],
        log_paths=["logs/recovery-drill.log"],
        evidence_paths=["tool-lab/reports/recovery.json"],
        provider="horizun",
        fallback_provider="custom-api",
        fallback_used=True,
    )

    markdown = render_run_summary(summary)

    for heading in (
        "Attempted",
        "Changed",
        "Passed",
        "Failed",
        "Rolled back",
        "Next",
        "Provider",
    ):
        assert heading in markdown
    assert "logs/recovery-drill.log" in markdown
    assert "tool-lab/reports/recovery.json" in markdown
    assert "horizun" in markdown
    assert "custom-api" in markdown
    assert "provider update experiment" in markdown


def test_run_summary_links_paths_without_persisting_payloads(tmp_path: Path):
    summary = RunSummary(
        attempted=["P07-T19"],
        changed=[],
        passed=[],
        failed=["healthcheck failed; token=secret-value"],
        rolled_back=[],
        next_tasks=["P07-T17"],
        log_paths=["logs/reboot.log"],
        evidence_paths=["docs/reports/reboot.json"],
        provider="horizun",
    )

    path = write_run_summary(tmp_path, summary)
    content = path.read_text(encoding="utf-8")

    assert path == tmp_path / "docs" / "reports" / "run-summary.md"
    assert "[logs/reboot.log](logs/reboot.log)" in content
    assert "[docs/reports/reboot.json](docs/reports/reboot.json)" in content
    assert "secret-value" not in content
    assert "[REDACTED]" in content


def test_empty_categories_are_explicitly_recorded():
    summary = RunSummary.from_mapping(
        {
            "attempted": ["task"],
            "changed": [],
            "passed": [],
            "failed": [],
            "rolled_back": [],
            "next": ["next"],
        }
    )

    markdown = render_run_summary(summary)
    assert "- none recorded" in markdown
