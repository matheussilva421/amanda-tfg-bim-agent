from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.run_amanda_production as production_runner
from scripts.run_amanda_production import (
    _new_idempotency_key,
    _report_canonical_sources,
    _select_revit_target,
    _validate_canonical_target,
)


class _Transport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def call(self, tool, arguments):
        self.calls.append((tool, arguments))
        return self.response


def test_select_revit_target_sets_and_verifies_the_requested_pid():
    transport = _Transport({"result": {"structuredContent": {"selected_pid": 37588}}})

    selected = _select_revit_target(transport, 37588)

    assert selected == {"selected_pid": 37588}
    assert transport.calls == [("horizun_target", {"pid": 37588})]


def test_final_save_key_is_unique_per_production_attempt():
    assert _new_idempotency_key("save", "run-abc123") == "amanda-save-run-abc123"


@pytest.mark.parametrize("target_is_copy", [False, True])
def test_superseded_r12_path_or_manifest_hash_cannot_be_reused_as_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target_is_copy: bool,
):
    archive_relpath = Path(
        "revit/production/archive/superseded-linear/AMANDA-RUN-001-S01-R12-linear-historical-20260922.rvt"
    )
    archive = tmp_path / archive_relpath
    archive.parent.mkdir(parents=True)
    archived_bytes = b"historical linear R12 model bytes"
    archive.write_bytes(archived_bytes)
    digest = hashlib.sha256(archived_bytes).hexdigest()
    monkeypatch.setattr(
        "scripts.run_amanda_production.legacy_selection_history",
        lambda: {
            "historical_rvt": archive_relpath.as_posix(),
            "solution_id": "AMANDA-RUN-001-S01",
            "historical_rvt_sha256": digest,
        },
    )
    manifest = {
        "record_type": "ARCHIVED_HISTORICAL_REVIT_MODEL",
        "repository_relative_archive_path": archive_relpath.as_posix(),
        "solution_id": "AMANDA-RUN-001-S01",
        "status": "SUPERSEDED_BY_USER_DIRECTION",
        "historical_only": True,
        "canonical_direction": {"may_reuse_linear_geometry": False},
        "artifact": {"sha256": digest},
    }
    manifest_path = archive.parent / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    target = tmp_path / "new-canonical-target.rvt" if target_is_copy else archive
    if target_is_copy:
        target.write_bytes(archived_bytes)

    with pytest.raises(ValueError, match="SUPERSEDED_BY_USER_DIRECTION"):
        _validate_canonical_target(target, repository_root=tmp_path)


def test_runner_reports_all_three_canonical_source_hashes(capsys):
    hashes = ("a" * 64, "b" * 64, "c" * 64)
    profile = SimpleNamespace(
        canonical_images=(
            "canonical/site.png",
            "canonical/residential.png",
            "canonical/admin.png",
        ),
        source_hashes=hashes,
    )

    _report_canonical_sources(profile)

    output = capsys.readouterr().out
    assert "canonical source hashes" in output
    assert all(digest in output for digest in hashes)


def test_dry_run_compiles_pending_candidate_without_provider_or_writer_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    hashes = ("a" * 64, "b" * 64, "c" * 64)
    profile = SimpleNamespace(
        canonical_images=(
            "canonical/site.png",
            "canonical/residential.png",
            "canonical/admin.png",
        ),
        source_hashes=hashes,
    )
    solution = SimpleNamespace(
        solution_id="AMANDA-RUN-002-PAVILION-S02",
        approval_hash="f" * 64,
        bim_eligible=False,
    )
    selection = SimpleNamespace(solution=solution, approval_hash="f" * 64)
    monkeypatch.setattr(
        production_runner, "_validate_canonical_target", lambda *_: None
    )
    monkeypatch.setattr(
        production_runner.CanonicalReferenceProfile,
        "load",
        lambda _root: profile,
    )
    layout = SimpleNamespace(
        program="official-program", profile=profile, content_hash="canonical-layout-hash"
    )
    monkeypatch.setattr(production_runner, "build_canonical_pavilion_layout", lambda *_: layout)
    monkeypatch.setattr(
        production_runner, "build_selection", lambda *args, **kwargs: selection
    )
    registry = SimpleNamespace(
        entries=[
            SimpleNamespace(revit_build="27.2.0.39", tool_schema_hash="a" * 64)
        ]
    )
    monkeypatch.setattr(
        production_runner.CapabilityRegistry,
        "load_for_production",
        lambda *_: (registry, []),
    )
    captured_planning_arguments = {}

    def capture_plan_arguments(**kwargs):
        captured_planning_arguments.update(kwargs)
        return [SimpleNamespace(stage=SimpleNamespace(name="R13"), operations=[])]

    monkeypatch.setattr(
        production_runner, "build_layout_stage_plans", capture_plan_arguments
    )
    monkeypatch.setattr(production_runner, "find_project_template", lambda *_: None)

    class ForbiddenTransport:
        def __init__(self, **_kwargs):
            pytest.fail("dry planning must never start a provider transport")

    class ForbiddenWriterLock:
        def __init__(self, *_args, **_kwargs):
            pytest.fail("dry planning must never acquire the production writer lock")

    monkeypatch.setattr(production_runner, "McpProbeTransport", ForbiddenTransport)
    monkeypatch.setattr(production_runner, "WriterLock", ForbiddenWriterLock)

    target = tmp_path / "new-canonical-target.rvt"
    result = production_runner.run(
        target, execute=False, max_stage="R13"
    )

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert result == 0
    assert all(digest in output for digest in hashes)
    assert "planned stages: ['R13']" in output
    assert "dry run: nothing written" in output
    assert "AMANDA-RUN-002-PAVILION-S02" in output
    assert captured_planning_arguments["mode"].value == "PLANNING_ONLY"
    assert captured_planning_arguments["max_stage"].name == "R13"
    assert captured_planning_arguments["solution"].bim_eligible is False
    assert not target.exists()


def test_active_runner_has_no_legacy_linear_layout_builder_import():
    source = Path(production_runner.__file__).read_text(encoding="utf-8")

    assert "build_courtyard_layout" not in source
