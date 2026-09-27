from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.run_amanda_production as production_runner
from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import ExecutionMode
from amanda_agent.production.selection import legacy_selection_history
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


def test_stage_journal_path_preserves_each_attempt():
    first = production_runner._stage_journal_path("R05", "attempt-one")
    second = production_runner._stage_journal_path("R05", "attempt-two")

    assert first != second
    assert first.name == "R05-attempt-one.json"
    assert second.name == "R05-attempt-two.json"


def test_cli_resume_defaults_to_r05_and_general_run_keeps_r13(monkeypatch):
    calls = []
    monkeypatch.setattr(
        production_runner,
        "run",
        lambda *args, **kwargs: calls.append(kwargs) or 0,
    )

    assert production_runner.main(
        ["--rvt", "study.rvt", "--resume-run003-study"]
    ) == 0
    assert production_runner.main(["--rvt", "new.rvt"]) == 0

    assert calls[0]["max_stage"] == "R05"
    assert calls[1]["max_stage"] == "R13"


def test_run003_resume_refuses_any_stage_beyond_r05_before_loading_grant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    target = tmp_path / "AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt"
    target.write_bytes(b"existing RUN-003 target")
    monkeypatch.setattr(
        production_runner,
        "_validate_canonical_target",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        production_runner,
        "load_run003_study_authorization",
        lambda *_args: pytest.fail("R05-only guard must precede grant loading"),
    )

    status = production_runner.run(
        target,
        execute=False,
        max_stage="R06",
        resume_run003_study=True,
    )

    assert status == 2
    assert "limited to R05" in capsys.readouterr().err


def test_legacy_selection_history_uses_canonical_historical_r12_path():
    assert legacy_selection_history()["historical_rvt"] == (
        "revit/production/archive/linear-r12-superseded.rvt"
    )


def test_worktree_resolves_the_shared_repository_root_for_writer_lock(tmp_path: Path):
    main = tmp_path / "Amanda"
    worktree = tmp_path / "worktrees" / "canonical"
    git_dir = main / ".git" / "worktrees" / "canonical"
    worktree.mkdir(parents=True)
    git_dir.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")

    assert production_runner._shared_repository_root(worktree) == main.resolve()


def test_regular_checkout_keeps_its_repository_root_for_writer_lock(tmp_path: Path):
    checkout = tmp_path / "Amanda"
    (checkout / ".git").mkdir(parents=True)

    assert production_runner._shared_repository_root(checkout) == checkout.resolve()


def test_unaccepted_canonical_selection_is_capped_at_r04():
    mode, stage = production_runner._execution_scope(
        bim_eligible=False, requested_max_stage="R13"
    )

    assert mode is ExecutionMode.CANONICAL_PREACCEPTANCE
    assert stage is BimStage.R04


def test_accepted_selection_keeps_the_requested_detailed_stage():
    mode, stage = production_runner._execution_scope(
        bim_eligible=True, requested_max_stage="R13"
    )

    assert mode is ExecutionMode.DETAILED_BIM
    assert stage is BimStage.R13


def test_post_p6_scope_requires_the_exact_run003_target_and_r05_r13_grant(tmp_path):
    expected_target = tmp_path / "AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt"
    authorization = SimpleNamespace(
        permits_target_path=lambda path: Path(path).resolve() == expected_target.resolve(),
        permits_stage=lambda stage: BimStage[stage] in {
            BimStage.R05,
            BimStage.R06,
            BimStage.R07,
            BimStage.R08,
            BimStage.R09,
            BimStage.R10,
            BimStage.R11,
            BimStage.R12,
            BimStage.R13,
        },
    )

    mode, stage = production_runner._execution_scope(
        bim_eligible=False,
        requested_max_stage="R13",
        run003_study_authorization=authorization,
        target_path=expected_target,
    )

    assert mode.value == "NORMALIZED_STUDY_POST_P6"
    assert stage is BimStage.R13
    with pytest.raises(ValueError, match="exact RUN-003 target"):
        production_runner._execution_scope(
            bim_eligible=False,
            requested_max_stage="R13",
            run003_study_authorization=authorization,
            target_path=tmp_path / "different.rvt",
        )


def test_run003_resume_uses_the_existing_target_without_template_or_save_as(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt"
    original_bytes = b"existing RUN-003 working document"
    target.write_bytes(original_bytes)
    solution_id = "AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"
    solution = SimpleNamespace(
        solution_id=solution_id,
        approval_hash="f" * 64,
        bim_eligible=False,
        run_id="AMANDA-RUN-003-PAVILION-CANONICAL",
    )
    selection = SimpleNamespace(
        solution=solution, approval_hash=solution.approval_hash, layout_hash="layout"
    )
    authorization = SimpleNamespace(
        solution_id=solution_id,
        approval_hash=solution.approval_hash,
        layout_hash="layout",
        checkpoint_sha256="c" * 64,
        target_path=str(target),
        permits_target_path=lambda path: Path(path).resolve() == target.resolve(),
        permits_stage=lambda stage: BimStage[getattr(stage, "name", stage)]
        in {
            BimStage.R05,
            BimStage.R06,
            BimStage.R07,
            BimStage.R08,
            BimStage.R09,
            BimStage.R10,
            BimStage.R11,
            BimStage.R12,
            BimStage.R13,
        },
        identity_bim_eligible=False,
        identity_revit_write_authorized=False,
    )
    registry = SimpleNamespace(
        entries=[SimpleNamespace(revit_build="27.2.0.39", tool_schema_hash="d" * 64)]
    )
    plan = SimpleNamespace(stage=BimStage.R05, operations=[])
    result = SimpleNamespace(
        stage=BimStage.R05,
        status=production_runner.RunStatus.VERIFIED,
        records=[],
    )
    health = {
        "status": "healthy",
        "revit_build": "27.2.0.39",
        "process_id": 38296,
        "other_clients_connected": 0,
        "open_document_count": 2,
        "no_active_document": False,
        "active_document": {
            "path": str(target),
            "is_active": True,
            "has_been_saved_to_disk": True,
        },
    }
    captured = {}
    class FakeLock:
        owner_token = "run003-test-token"

        def __init__(self, *_args, **_kwargs):
            pass

        def inspect(self):
            return None

        def acquire(self, **kwargs):
            captured["lock_arguments"] = kwargs

        def release(self):
            return True

    class FakeTransport:
        calls = []

        def __init__(self, **_kwargs):
            self.calls = []

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            captured["transport_calls"] = list(self.calls)

        def call(self, tool, arguments):
            self.calls.append((tool, arguments))
            return {"result": {"structuredContent": {"status": "saved"}}}

    monkeypatch.setattr(production_runner, "EVIDENCE_ROOT", tmp_path / "evidence")
    monkeypatch.setattr(production_runner, "LOCK_PATH", tmp_path / "writer.lock")
    monkeypatch.setattr(production_runner, "WriterLock", FakeLock)
    monkeypatch.setattr(production_runner, "McpProbeTransport", FakeTransport)
    monkeypatch.setattr(production_runner, "load_run003_study_authorization", lambda _root: authorization)
    monkeypatch.setattr(production_runner, "load_run003_study_selection", lambda _root, _grant: selection)
    monkeypatch.setattr(production_runner, "_validate_canonical_target", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(production_runner.CanonicalReferenceProfile, "load", lambda _root: SimpleNamespace(canonical_images=("a", "b", "c", "d"), source_hashes=("a" * 64, "b" * 64, "c" * 64, "d" * 64)))
    monkeypatch.setattr(production_runner, "_report_canonical_sources", lambda _profile: None)
    monkeypatch.setattr(production_runner, "build_canonical_pavilion_layout", lambda *_args: SimpleNamespace(content_hash="layout"))
    monkeypatch.setattr(production_runner, "build_selection", lambda *args, **kwargs: selection)
    monkeypatch.setattr(production_runner.CapabilityRegistry, "load_for_production", lambda *_args: (registry, []))

    def capture_plan_arguments(**kwargs):
        captured["plan_arguments"] = kwargs
        return [plan]

    monkeypatch.setattr(production_runner, "build_layout_stage_plans", capture_plan_arguments)
    monkeypatch.setattr(production_runner, "find_project_template", lambda *_: pytest.fail("resume must not open a template"))
    monkeypatch.setattr(production_runner, "_read_tool", lambda _transport, tool, _arguments: health if tool == "horizun_health" else {"path": str(target)})
    def verify_baseline(_transport, grant):
        captured["readback_authorization"] = grant
        return "p6-baseline-fingerprint"

    monkeypatch.setattr(production_runner, "_verify_p6_live_readback", verify_baseline)
    monkeypatch.setattr(production_runner, "_document_info", lambda _transport: {"path": str(target)})
    monkeypatch.setattr(production_runner, "execute_stage", lambda *_args, **_kwargs: result)
    monkeypatch.setattr(production_runner, "_select_revit_target", lambda *_args: {"selected_pid": 38296})
    monkeypatch.setattr(production_runner, "_activate", lambda *_args: None)

    def record_persistence(*_args, **kwargs):
        captured["persistence_call"] = kwargs
        return {"checkpoint_verified": True, "reopened_exact_target": True}

    monkeypatch.setattr(
        production_runner, "_save_checkpoint_reopen_stage", record_persistence
    )

    status = production_runner.run(
        target,
        execute=True,
        max_stage="R05",
        revit_pid=38296,
        resume_run003_study=True,
    )

    assert status == 0
    assert target.read_bytes() == original_bytes
    assert captured["plan_arguments"]["mode"].value == "NORMALIZED_STUDY_POST_P6"
    assert captured["plan_arguments"]["start_stage"] is BimStage.R05
    assert captured["plan_arguments"]["run003_study_authorization"] is authorization
    assert captured["lock_arguments"]["document_identity"] == str(target.resolve())
    assert captured["lock_arguments"]["reclaim_abandoned"] is False
    assert captured["readback_authorization"] is authorization
    assert captured["persistence_call"]["p6_checkpoint_sha256"] == authorization.checkpoint_sha256
    assert all(tool != "horizun_document_session" for tool, _ in captured["transport_calls"])


def test_run003_resume_dry_run_compiles_r05_without_lock_or_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt"
    target.write_bytes(b"existing target")
    solution_id = "AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C"
    solution = SimpleNamespace(
        solution_id=solution_id,
        approval_hash="f" * 64,
        bim_eligible=False,
    )
    selection = SimpleNamespace(
        solution=solution, approval_hash=solution.approval_hash, layout_hash="layout"
    )
    authorization = SimpleNamespace(
        solution_id=solution_id,
        approval_hash=solution.approval_hash,
        layout_hash="layout",
        identity_bim_eligible=False,
        identity_revit_write_authorized=False,
        permits_target_path=lambda path: Path(path).resolve() == target.resolve(),
        permits_stage=lambda stage: getattr(stage, "name", stage) in {"R05"},
    )
    registry = SimpleNamespace(
        entries=[SimpleNamespace(revit_build="27.2.0.39", tool_schema_hash="d" * 64)]
    )
    plan = SimpleNamespace(stage=BimStage.R05, operations=[])
    captured = {}

    monkeypatch.setattr(production_runner, "load_run003_study_authorization", lambda _root: authorization)
    monkeypatch.setattr(production_runner, "load_run003_study_selection", lambda _root, _grant: selection)
    monkeypatch.setattr(production_runner, "_validate_canonical_target", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(production_runner.CanonicalReferenceProfile, "load", lambda _root: SimpleNamespace(canonical_images=("a", "b", "c", "d"), source_hashes=("a" * 64, "b" * 64, "c" * 64, "d" * 64)))
    monkeypatch.setattr(production_runner, "_report_canonical_sources", lambda _profile: None)
    monkeypatch.setattr(production_runner, "build_canonical_pavilion_layout", lambda *_args: SimpleNamespace(content_hash="layout"))
    monkeypatch.setattr(production_runner, "build_selection", lambda *args, **kwargs: selection)
    monkeypatch.setattr(production_runner.CapabilityRegistry, "load_for_production", lambda *_args: (registry, []))
    def capture_plan(**kwargs):
        captured["plan"] = kwargs
        return [plan]

    monkeypatch.setattr(production_runner, "build_layout_stage_plans", capture_plan)
    monkeypatch.setattr(production_runner, "find_project_template", lambda *_: pytest.fail("resume dry-run must not look for a template"))

    class ForbiddenProvider:
        def __init__(self, *_args, **_kwargs):
            pytest.fail("resume dry-run must not connect to Revit")

    monkeypatch.setattr(production_runner, "McpProbeTransport", ForbiddenProvider)
    monkeypatch.setattr(production_runner, "WriterLock", ForbiddenProvider)

    status = production_runner.run(
        target,
        execute=False,
        max_stage="R05",
        resume_run003_study=True,
    )

    assert status == 0
    assert captured["plan"]["mode"] is ExecutionMode.NORMALIZED_STUDY_POST_P6
    assert captured["plan"]["start_stage"] is BimStage.R05
    assert captured["plan"]["run003_study_authorization"] is authorization


def test_live_revit_preflight_requires_single_idle_writer_target():
    healthy = {
        "status": "healthy",
        "revit_build": "27.2.0.39",
        "process_id": 31036,
        "no_active_document": True,
        "open_document_count": 0,
        "other_clients_connected": 0,
    }

    production_runner._validate_revit_session(
        healthy, expected_build="27.2.0.39", revit_pid=31036
    )

    for refused in (
        {**healthy, "status": "degraded"},
        {**healthy, "revit_build": "27.1.0.1"},
        {**healthy, "process_id": 1},
        {**healthy, "no_active_document": False, "open_document_count": 1},
        {**healthy, "other_clients_connected": 1},
    ):
        with pytest.raises(ValueError):
            production_runner._validate_revit_session(
                refused, expected_build="27.2.0.39", revit_pid=31036
            )


def test_live_revit_resume_requires_the_exact_saved_active_target(tmp_path: Path):
    target = tmp_path / "RUN-003.rvt"
    health = {
        "status": "healthy",
        "revit_build": "27.2.0.39",
        "process_id": 38296,
        "other_clients_connected": 0,
        "open_document_count": 2,
        "no_active_document": False,
        "active_document": {
            "path": str(target),
            "is_active": True,
            "has_been_saved_to_disk": True,
        },
    }

    production_runner._validate_revit_session(
        health,
        expected_build="27.2.0.39",
        revit_pid=38296,
        target_path=target,
    )

    for refused in (
        {**health, "active_document": {**health["active_document"], "path": str(tmp_path / "other.rvt")}},
        {**health, "active_document": {**health["active_document"], "has_been_saved_to_disk": False}},
        {**health, "other_clients_connected": 1},
    ):
        with pytest.raises(ValueError):
            production_runner._validate_revit_session(
                refused,
                expected_build="27.2.0.39",
                revit_pid=38296,
                target_path=target,
            )


def test_live_client_gate_error_reports_recent_client_identity(tmp_path: Path):
    target = tmp_path / "RUN-003.rvt"
    health = {
        "status": "healthy",
        "revit_build": "27.2.0.39",
        "process_id": 38296,
        "other_clients_connected": 1,
        "open_document_count": 2,
        "active_document": {
            "path": str(target),
            "is_active": True,
            "has_been_saved_to_disk": True,
        },
        "clients": {
            "other_clients_connected": 1,
            "clients_seen": [
                {
                    "pid": 21076,
                    "process_name": None,
                    "seconds_since_last_request": 29,
                    "process_alive": False,
                }
            ],
        },
    }

    with pytest.raises(ValueError, match=r"pid=21076.*process_alive=false"):
        production_runner._validate_revit_session(
            health,
            expected_build="27.2.0.39",
            revit_pid=38296,
            target_path=target,
        )


def test_live_client_gate_error_escapes_control_characters(tmp_path: Path):
    target = tmp_path / "RUN-003.rvt"
    health = {
        "status": "healthy",
        "revit_build": "27.2.0.39",
        "process_id": 38296,
        "other_clients_connected": 1,
        "open_document_count": 2,
        "active_document": {
            "path": str(target),
            "is_active": True,
            "has_been_saved_to_disk": True,
        },
        "clients": {
            "other_clients_connected": 1,
            "clients_seen": [
                {
                    "pid": 21076,
                    "process_name": "runner\nrole\x1b[31m",
                    "seconds_since_last_request": 29,
                    "process_alive": False,
                }
            ],
        },
    }

    with pytest.raises(ValueError) as exc_info:
        production_runner._validate_revit_session(
            health,
            expected_build="27.2.0.39",
            revit_pid=38296,
            target_path=target,
        )

    message = str(exc_info.value)
    assert "process_name=runner\\nrole\\x1b[31m" in message
    assert "\nrole" not in message
    assert "\x1b" not in message


def test_resume_reuses_only_a_live_lease_bound_to_the_exact_run003_target(
    tmp_path: Path,
):
    target = tmp_path / "RUN-003.rvt"
    lease = SimpleNamespace(
        host="same-host",
        path=tmp_path / "writer.lock",
        inspect=lambda: {
            "owner": "amanda-P7-RUN003-production",
            "owner_token": "existing-token",
            "document_identity": str(target),
            "host": "same-host",
            "process_id": 28364,
        },
        is_held_by_live_owner=lambda: True,
        acquire=lambda **_kwargs: pytest.fail("must retain the already live RUN-003 lease"),
    )

    owned = production_runner._acquire_writer_lease(
        lease,
        document_identity=str(target),
        reuse_existing_run003_lease=True,
    )

    assert owned is False

    lease.inspect = lambda: {
        "owner": "another-task",
        "owner_token": "other-token",
        "document_identity": str(target),
        "host": "same-host",
        "process_id": 28364,
    }
    with pytest.raises(production_runner.LockHeldByAnotherOwner):
        production_runner._acquire_writer_lease(
            lease,
            document_identity=str(target),
            reuse_existing_run003_lease=True,
        )


def test_run003_live_readback_must_match_the_accepted_p6_baseline(
    monkeypatch: pytest.MonkeyPatch,
):
    components = (
        "ADMIN_ACOLHIMENTO",
        "CHILD_SECTOR",
        "RES_PAV_A",
        "RES_PAV_B",
        "RES_PAV_C",
        "RES_PAV_D_COMMUNAL",
        "SERVICE_CAPACITATION",
    )
    boxes = {
        component: {
            "min": (float(index), 0.0, 0.0),
            "max": (float(index + 1), 1.0, 3.2),
        }
        for index, component in enumerate(components)
    }
    floor_ids = {"R04-ADMIN-FLOOR-L1": 331163, "R04-ADMIN-FLOOR-L2": 331170}
    authorization = SimpleNamespace(
        mass_bounding_boxes_m=boxes,
        administrative_floor_element_ids=floor_ids,
    )
    rows = [
        {
            "element_id": 320000 + index,
            "name": f"MASS-{name}",
            "bounding_box": {
                "min": list(bounds["min"]),
                "max": list(bounds["max"]),
            },
        }
        for index, (name, bounds) in enumerate(boxes.items())
    ]
    rows.extend(
        {"element_id": element_id, "name": mark}
        for mark, element_id in floor_ids.items()
    )
    rows.extend(
        {"element_id": 331200 + index, "name": f"FLOOR-{index}"}
        for index in range(12)
    )
    rows.extend(
        {"element_id": 331300 + index, "name": f"ROOF-{index}"}
        for index in range(4)
    )
    payload = {
        "matched_total": 25,
        "returned": 25,
        "coverage_complete": True,
        "unreadable_total": 0,
        "result_set_fingerprint": "p6-live-fingerprint",
        "summary": {"by_category": {"Massa": 7, "Pisos": 14, "Telhados": 4}},
        "rows": rows,
    }
    calls = []
    monkeypatch.setattr(
        production_runner,
        "_read_tool",
        lambda _transport, tool, arguments: calls.append((tool, arguments)) or payload,
    )

    fingerprint = production_runner._verify_p6_live_readback(object(), authorization)

    assert fingerprint == "p6-live-fingerprint"
    assert calls[0][0] == "horizun_query_model"
    assert calls[0][1]["include_types"] is False
    assert calls[0][1]["coordinate_units"] == "m"

    rows[0]["bounding_box"]["max"] = [1.0, 1.0, 6.4]
    with pytest.raises(ValueError, match="P6 mass bounding boxes"):
        production_runner._verify_p6_live_readback(object(), authorization)


def test_execute_stops_before_writer_lock_for_unaccepted_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    hashes = ("a" * 64, "b" * 64, "c" * 64, "d" * 64)
    profile = SimpleNamespace(
        canonical_images=("a.png", "b.png", "c.png", "d.png"),
        source_hashes=hashes,
    )
    solution = SimpleNamespace(
        solution_id="AMANDA-RUN-002-PAVILION-S02",
        approval_hash="f" * 64,
        bim_eligible=False,
    )
    selection = SimpleNamespace(solution=solution, approval_hash=solution.approval_hash)
    registry = SimpleNamespace(
        entries=[SimpleNamespace(revit_build="27.2.0.39", tool_schema_hash="d" * 64)]
    )

    monkeypatch.setattr(production_runner, "_validate_canonical_target", lambda *_: None)
    monkeypatch.setattr(production_runner.CanonicalReferenceProfile, "load", lambda _root: profile)
    monkeypatch.setattr(production_runner, "build_canonical_pavilion_layout", lambda *_: SimpleNamespace(content_hash="e" * 64))
    monkeypatch.setattr(production_runner, "build_selection", lambda *args, **kwargs: selection)
    monkeypatch.setattr(production_runner.CapabilityRegistry, "load_for_production", lambda *_: (registry, []))

    monkeypatch.setattr(
        production_runner,
        "build_layout_stage_plans",
        lambda **_kwargs: pytest.fail("an unaccepted selection must stop before stage planning"),
    )
    monkeypatch.setattr(production_runner, "find_project_template", lambda *_: None)

    class StopAtLock:
        def __init__(self, *_args, **_kwargs):
            pytest.fail("an unaccepted selection must stop before the writer lock")

    monkeypatch.setattr(production_runner, "WriterLock", StopAtLock)

    result = production_runner.run(
        tmp_path / "canonical.rvt", execute=True, max_stage="R13"
    )

    assert result == 2


@pytest.mark.parametrize("target_is_copy", [False, True])
def test_superseded_r12_path_or_manifest_hash_cannot_be_reused_as_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target_is_copy: bool,
):
    archive_relpath = Path(
        "revit/production/archive/linear-r12-superseded.rvt"
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


def test_runner_refuses_archived_r12_when_archive_bytes_do_not_match_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    archive_relpath = Path(
        "revit/production/archive/linear-r12-superseded.rvt"
    )
    archive = tmp_path / archive_relpath
    archive.parent.mkdir(parents=True)
    expected_bytes = b"sealed historical linear R12 model"
    archive.write_bytes(b"changed archived model")
    expected_digest = hashlib.sha256(expected_bytes).hexdigest()
    monkeypatch.setattr(
        "scripts.run_amanda_production.legacy_selection_history",
        lambda: {
            "historical_rvt": archive_relpath.as_posix(),
            "solution_id": "AMANDA-RUN-001-S01",
            "historical_rvt_sha256": expected_digest,
        },
    )
    (archive.parent / "manifest.json").write_text(
        json.dumps(
            {
                "record_type": "ARCHIVED_HISTORICAL_REVIT_MODEL",
                "repository_relative_archive_path": archive_relpath.as_posix(),
                "solution_id": "AMANDA-RUN-001-S01",
                "status": "SUPERSEDED_BY_USER_DIRECTION",
                "historical_only": True,
                "canonical_direction": {"may_reuse_linear_geometry": False},
                "artifact": {"sha256": expected_digest},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="archived R12 bytes do not match"):
        _validate_canonical_target(tmp_path / "new-canonical-target.rvt", repository_root=tmp_path)


def test_runner_reports_all_four_canonical_source_hashes(capsys):
    hashes = ("a" * 64, "b" * 64, "c" * 64, "d" * 64)
    profile = SimpleNamespace(
        canonical_images=(
            "canonical/site.png",
            "canonical/residential.png",
            "canonical/admin.png",
            "canonical/services.png",
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
    hashes = ("a" * 64, "b" * 64, "c" * 64, "d" * 64)
    profile = SimpleNamespace(
        canonical_images=(
            "canonical/site.png",
            "canonical/residential.png",
            "canonical/admin.png",
            "canonical/services.png",
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


def test_run003_r05_requires_save_checkpoint_cold_reopen_and_exact_readback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt"
    target.write_bytes(b"saved R05 study model")
    checkpoint_root = tmp_path / "evidence"
    transport = _PersistenceTransport(target)
    checkpoint_manager_type = production_runner.CheckpointManager

    class TrackingCheckpointManager:
        def __init__(self):
            self.delegate = checkpoint_manager_type()

        def create_checkpoint(self, *args, **kwargs):
            assert transport.closed is True
            return self.delegate.create_checkpoint(*args, **kwargs)

        def verify_checkpoint(self, *args, **kwargs):
            return self.delegate.verify_checkpoint(*args, **kwargs)

    monkeypatch.setattr(
        production_runner, "CheckpointManager", TrackingCheckpointManager
    )
    result = SimpleNamespace(
        stage=BimStage.R05,
        status=production_runner.RunStatus.VERIFIED,
        records=[
            SimpleNamespace(
                logical_id="R05-WALL-01",
                status=production_runner.RunStatus.VERIFIED,
                unique_id="persistent-wall-uid",
                evidence={"element_id": 514001, "unique_id": "persistent-wall-uid"},
            )
        ],
    )

    evidence = production_runner._save_checkpoint_reopen_stage(
        transport,
        target,
        result,
        run_key="r05-test",
        checkpoint_root=checkpoint_root,
        p6_checkpoint_sha256="8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326",
    )

    assert [tool for tool, _ in transport.calls] == [
        "get_document_info",
        "horizun_query_model",
        "horizun_save_document",
        "horizun_document_session",
        "horizun_document_session",
        "get_document_info",
        "horizun_query_model",
    ]
    before_save_query = transport.calls[1][1]
    after_reopen_query = transport.calls[6][1]
    assert before_save_query["element_ids"] == [514001]
    assert before_save_query["cache_mode"] == "bypass"
    assert before_save_query["include_bounding_box"] is True
    assert before_save_query == after_reopen_query
    close_args = transport.calls[3][1]
    assert close_args["operation"] == "close"
    assert close_args["save_on_close"] is True
    assert close_args["activate_other"] is True
    reopen_args = transport.calls[4][1]
    assert reopen_args["operation"] == "open"
    assert reopen_args["file_path"] == str(target.resolve())
    assert reopen_args["allow_upgrade"] is False
    query_args = after_reopen_query
    assert query_args["element_ids"] == [514001]
    assert query_args["cache_mode"] == "bypass"
    assert query_args["return_fields"] == ["unique_id", "category", "name"]
    assert evidence["checkpoint_sha256"]
    assert evidence["checkpoint_verified"] is True
    assert Path(evidence["checkpoint_path"]).is_file()
    assert Path(evidence["checkpoint_manifest_path"]).is_file()
    assert evidence["closed"] is True
    assert evidence["reopened_exact_target"] is True
    assert evidence["geometry_preserved"] is True
    assert evidence["pre_save_bounds_m"]["514001"] == {
        "min": [1.0, 2.0, 0.0],
        "max": [4.0, 5.0, 3.2],
    }
    assert evidence["post_reopen_readback"] == {
        "matched_total": 1,
        "returned": 1,
        "coverage_complete": True,
        "unreadable_total": 0,
        "element_ids": [514001],
        "unique_ids": ["persistent-wall-uid"],
        "geometry_preserved": True,
    }
    assert evidence["p6_checkpoint_sha256"] == (
        "8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326"
    )


def test_run003_r05_persistence_identity_mismatch_fails_closed(tmp_path: Path):
    target = tmp_path / "AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt"
    target.write_bytes(b"saved R05 study model")
    transport = _PersistenceTransport(target, readback_unique_id="changed-uid")
    result = SimpleNamespace(
        stage=BimStage.R05,
        status=production_runner.RunStatus.VERIFIED,
        records=[
            SimpleNamespace(
                logical_id="R05-WALL-01",
                status=production_runner.RunStatus.VERIFIED,
                unique_id="persistent-wall-uid",
                evidence={"element_id": 514001, "unique_id": "persistent-wall-uid"},
            )
        ],
    )

    with pytest.raises(RuntimeError, match="post-reopen identity changed"):
        production_runner._save_checkpoint_reopen_stage(
            transport,
            target,
            result,
            run_key="r05-identity-mismatch",
            checkpoint_root=tmp_path / "evidence",
            p6_checkpoint_sha256="8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326",
        )

    assert [tool for tool, _ in transport.calls][-1] == "horizun_query_model"
    assert transport.closed is False


def test_run003_r05_persistence_geometry_mismatch_fails_closed(tmp_path: Path):
    target = tmp_path / "AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt"
    target.write_bytes(b"saved R05 study model")
    transport = _PersistenceTransport(
        target,
        post_reopen_bounding_box={
            "min": [1.0, 2.0, 0.0],
            "max": [4.0, 5.0, 4.0],
        },
    )
    result = SimpleNamespace(
        stage=BimStage.R05,
        status=production_runner.RunStatus.VERIFIED,
        records=[
            SimpleNamespace(
                logical_id="R05-WALL-01",
                status=production_runner.RunStatus.VERIFIED,
                unique_id="persistent-wall-uid",
                evidence={"element_id": 514001, "unique_id": "persistent-wall-uid"},
            )
        ],
    )

    with pytest.raises(RuntimeError, match="post-reopen geometry changed"):
        production_runner._save_checkpoint_reopen_stage(
            transport,
            target,
            result,
            run_key="r05-geometry-mismatch",
            checkpoint_root=tmp_path / "evidence",
            p6_checkpoint_sha256="8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326",
        )

    assert [tool for tool, _ in transport.calls].count("horizun_query_model") == 2
    assert transport.closed is False


class _PersistenceTransport:
    def __init__(
        self,
        target: Path,
        *,
        readback_unique_id="persistent-wall-uid",
        post_reopen_bounding_box=None,
    ):
        self.target = target.resolve()
        self.calls = []
        self.closed = False
        self.readback_unique_id = readback_unique_id
        self.post_reopen_bounding_box = post_reopen_bounding_box or {
            "min": [1.0, 2.0, 0.0],
            "max": [4.0, 5.0, 3.2],
        }
        self.query_count = 0

    def call(self, tool, arguments):
        self.calls.append((tool, arguments))
        if tool == "horizun_save_document":
            payload = {"outcome": "saved_verified", "bytes_changed_on_disk": True}
        elif tool == "horizun_document_session" and arguments["operation"] == "close":
            self.closed = True
            payload = {"outcome": "closed_verified", "closed": True}
        elif tool == "horizun_document_session" and arguments["operation"] == "open":
            self.closed = False
            payload = {
                "opened": True,
                "path_matches_request": True,
                "upgraded_on_open": False,
            }
        elif tool == "get_document_info":
            payload = {"path": str(self.target)}
        elif tool == "horizun_query_model":
            self.query_count += 1
            bbox = (
                self.post_reopen_bounding_box
                if self.query_count > 1
                else {"min": [1.0, 2.0, 0.0], "max": [4.0, 5.0, 3.2]}
            )
            payload = {
                "matched_total": 1,
                "returned": 1,
                "coverage_complete": True,
                "unreadable_total": 0,
                "rows": [
                    {
                        "element_id": 514001,
                        "unique_id": (
                            self.readback_unique_id
                            if self.query_count > 1
                            else "persistent-wall-uid"
                        ),
                        "bounding_box": bbox,
                    }
                ],
            }
        else:
            raise AssertionError(f"unexpected tool call: {tool}")
        return {"result": {"structuredContent": payload}}


def test_active_runner_has_no_legacy_linear_layout_builder_import():
    source = Path(production_runner.__file__).read_text(encoding="utf-8")

    assert "build_courtyard_layout" not in source
