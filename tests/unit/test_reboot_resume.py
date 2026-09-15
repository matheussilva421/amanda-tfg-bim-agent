from pathlib import Path

from amanda_agent.bim.checkpoints import CheckpointManager
from amanda_agent.recovery.reboot import (
    render_resume_after_reboot,
    write_resume_after_reboot,
)


def test_resume_file_contains_deterministic_recovery_contract(tmp_path: Path):
    source = tmp_path / "working.rvt"
    checkpoint_path = tmp_path / "R02.rvt"
    source.write_bytes(b"stable")
    manifest = CheckpointManager().create_checkpoint(
        source, checkpoint_path, stage="R02_SITE"
    )

    values = {
        "phase": "PHASE_07B",
        "last_pass_task": "P07-T15",
        "reboot_reason": "provider update requires reboot",
        "checkpoint": manifest,
        "expected_revit_state": "closed; reopen only the disposable study file",
        "expected_provider_state": "horizun HEALTHY; fallback disabled",
        "verification_commands": [
            "python -m amanda_agent doctor",
            "python -m amanda_agent status",
            "python -m amanda_agent resume",
        ],
        "next_task": "P07-T17",
    }

    first = render_resume_after_reboot(**values)
    second = render_resume_after_reboot(**values)
    assert first == second
    assert "PHASE_07B" in first
    assert "P07-T15" in first
    assert manifest.sha256 in first
    assert "P07-T17" in first
    assert "python -m amanda_agent doctor" in first


def test_resume_writer_redacts_secret_values(tmp_path: Path):
    path = write_resume_after_reboot(
        tmp_path,
        phase="PHASE_07B",
        last_pass_task="P07-T15",
        reboot_reason="token=super-secret-value",
        checkpoint=None,
        expected_revit_state="closed",
        expected_provider_state="provider healthy",
        verification_commands=["python -m amanda_agent status --api-key=abc12345"],
        next_task="P07-T17",
    )

    content = path.read_text(encoding="utf-8")
    assert content == render_resume_after_reboot(
        phase="PHASE_07B",
        last_pass_task="P07-T15",
        reboot_reason="token=super-secret-value",
        checkpoint=None,
        expected_revit_state="closed",
        expected_provider_state="provider healthy",
        verification_commands=["python -m amanda_agent status --api-key=abc12345"],
        next_task="P07-T17",
    )
    assert "super-secret-value" not in content
    assert "abc12345" not in content
    assert "[REDACTED]" in content


def test_resume_file_can_record_missing_checkpoint_honestly(tmp_path: Path):
    path = write_resume_after_reboot(
        tmp_path,
        phase="PHASE_07B",
        last_pass_task=None,
        reboot_reason="controlled procedure rehearsal",
        checkpoint=None,
        expected_revit_state="NOT_VERIFIED",
        expected_provider_state="NOT_VERIFIED",
        verification_commands=["python -m amanda_agent doctor"],
        next_task="P07-T17",
    )

    content = path.read_text(encoding="utf-8")
    assert "No verified PASS task recorded" in content
    assert "No verified checkpoint recorded" in content
