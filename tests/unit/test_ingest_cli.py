"""The control plane can ingest sources from the command line."""

from pathlib import Path

import yaml
from typer.testing import CliRunner

from amanda_agent.cli import app
from amanda_agent.models.state import ProjectState
from amanda_agent.state.store import StateStore

runner = CliRunner()


def build_root(tmp_path: Path) -> Path:
    StateStore(tmp_path / "PROJECT_STATE.yaml").save(ProjectState())
    (tmp_path / "state").mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_ingest_command_copies_a_source_and_reports_the_hash(tmp_path, monkeypatch):
    root = build_root(tmp_path)
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(root))
    source = tmp_path / "incoming.pdf"
    source.write_bytes(b"%PDF-1.4\nsynthetic\x00\xff")

    result = runner.invoke(app, ["ingest", str(source)])

    assert result.exit_code == 0, result.stdout
    manifest = yaml.safe_load(
        (root / "project" / "provenance" / "source-manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    document = manifest["documents"][0]
    assert document["filename"] == "incoming.pdf"
    assert (root / document["immutable_path"]).read_bytes() == source.read_bytes()
    assert document["sha256"] in result.stdout


def test_ingest_command_refuses_to_lose_the_source_id(tmp_path, monkeypatch):
    root = build_root(tmp_path)
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(root))
    source = tmp_path / "incoming.pdf"
    source.write_bytes(b"%PDF-1.4\nsynthetic")

    first = runner.invoke(app, ["ingest", str(source), "--id", "SRC-PROGRAM-001"])
    assert first.exit_code == 0, first.stdout

    second = runner.invoke(app, ["ingest", str(source)])
    assert second.exit_code == 0, second.stdout

    manifest = yaml.safe_load(
        (root / "project" / "provenance" / "source-manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert len(manifest["documents"]) == 1
    assert manifest["documents"][0]["source_id"] == "SRC-PROGRAM-001"


def test_ingest_command_refuses_a_missing_source(tmp_path, monkeypatch):
    root = build_root(tmp_path)
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(root))

    result = runner.invoke(app, ["ingest", str(tmp_path / "absent.pdf")])

    assert result.exit_code != 0
    assert "absent.pdf" in (result.stdout + str(result.output))


def test_ingest_command_without_paths_explains_the_usage(tmp_path, monkeypatch):
    root = build_root(tmp_path)
    monkeypatch.setenv("AMANDA_PROJECT_ROOT", str(root))

    result = runner.invoke(app, ["ingest"])

    assert result.exit_code != 0
