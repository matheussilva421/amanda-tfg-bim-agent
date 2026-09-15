"""Snapshots keep an exact private backup and a redacted Git summary."""

from pathlib import Path

from amanda_agent.bootstrap.snapshots import (
    inventory_revit_addins,
    resolve_codex_home,
    snapshot_codex_config,
)
from amanda_agent.redaction import contains_secret

SECRET = "sk-supersecretvalue1234567890"

CONFIG = "\n".join(
    [
        'model = "gpt-5-codex"',
        'approval_policy = "on-request"',
        "",
        "[mcp_servers.example]",
        'command = "python"',
        'env = { OPENAI_API_KEY = "' + SECRET + '", PASSWORD = "hunter2" }',
        "",
    ]
)


def test_codex_home_prefers_the_environment_variable(tmp_path: Path):
    assert resolve_codex_home({"CODEX_HOME": str(tmp_path)}) == tmp_path
    assert resolve_codex_home({}).name == ".codex"


def test_private_backup_is_byte_preserving(tmp_path: Path):
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text(CONFIG, encoding="utf-8")
    private_root = tmp_path / "state" / "snapshots" / "private"

    summary = snapshot_codex_config(
        codex_home=codex_home, private_root=private_root, timestamp="20260915T000000Z"
    )

    backed_up = Path(summary["private_dir"]) / "config.toml"
    assert backed_up.read_bytes() == (codex_home / "config.toml").read_bytes()
    assert summary["private_acl"] == "DEFAULT_PROFILE_ACL"


def test_git_summary_never_contains_secrets(tmp_path: Path):
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text(CONFIG, encoding="utf-8")
    (codex_home / "auth.json").write_text(
        '{"access_token": "' + SECRET + '"}', encoding="utf-8"
    )
    private_root = tmp_path / "state" / "snapshots" / "private"

    summary = snapshot_codex_config(
        codex_home=codex_home, private_root=private_root, timestamp="20260915T000000Z"
    )

    assert contains_secret(summary) is False
    assert SECRET not in str(summary)
    config_entry = [
        entry for entry in summary["files"] if entry["name"] == "config.toml"
    ][0]
    assert config_entry["sha256"]
    env = config_entry["settings"]["mcp_servers"]["example"]["env"]
    assert env["OPENAI_API_KEY"] == "[REDACTED]"
    assert env["PASSWORD"] == "[REDACTED]"


def test_unparseable_config_still_gets_hashed_and_redacted(tmp_path: Path):
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text("broken = [" + SECRET, encoding="utf-8")
    private_root = tmp_path / "state" / "snapshots" / "private"

    summary = snapshot_codex_config(
        codex_home=codex_home, private_root=private_root, timestamp="20260915T000000Z"
    )

    assert summary["files"][0]["sha256"]
    assert SECRET not in str(summary)


def test_missing_codex_home_is_reported_not_raised(tmp_path: Path):
    summary = snapshot_codex_config(
        codex_home=tmp_path / "absent",
        private_root=tmp_path / "private",
        timestamp="20260915T000000Z",
    )

    assert summary["status"] == "MISSING"
    assert summary["files"] == []


def test_revit_addin_inventory_records_hash_and_never_content(tmp_path: Path):
    addins = tmp_path / "Addins" / "2027"
    addins.mkdir(parents=True)
    (addins / "SomeAddin.addin").write_text("<RevitAddIns/>", encoding="utf-8")
    (addins / "Nested").mkdir()
    (addins / "Nested" / "Other.addin").write_text("<RevitAddIns/>", encoding="utf-8")

    entries = inventory_revit_addins([addins, tmp_path / "absent"])

    present = [entry for entry in entries if entry["status"] == "PRESENT"]
    absent = [entry for entry in entries if entry["status"] == "ABSENT"]
    assert len(present) == 2
    assert all(entry["sha256"] for entry in present)
    assert all("content" not in entry for entry in present)
    assert len(absent) == 1, "an absent add-in root must still be reported"
