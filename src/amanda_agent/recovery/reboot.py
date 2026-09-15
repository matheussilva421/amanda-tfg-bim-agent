"""Deterministic, secret-safe reboot resume instructions."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Any

from ..bim.checkpoints import CheckpointManifest, sha256_file
from ..security.redaction import redact_text


def _text(value: Any, *, missing: str = "NOT_RECORDED") -> str:
    if value is None or not str(value).strip():
        return missing
    return redact_text(str(value).strip())


def _checkpoint_details(
    checkpoint: CheckpointManifest | Path | str | None,
    checkpoint_hash: str | None,
) -> tuple[str, str]:
    if checkpoint is None:
        return "No verified checkpoint recorded", "NOT_VERIFIED"
    if isinstance(checkpoint, CheckpointManifest):
        return _text(checkpoint.checkpoint_path), checkpoint.sha256
    path = Path(checkpoint)
    if path.suffix.casefold() == ".json" and path.name.casefold().endswith(
        ".manifest.json"
    ):
        try:
            manifest = CheckpointManifest.load(path)
        except (OSError, TypeError, ValueError):
            manifest = None
        if manifest is not None:
            return _text(manifest.checkpoint_path), manifest.sha256
    if path.is_file():
        try:
            digest = sha256_file(path)
        except OSError:
            digest = checkpoint_hash or "NOT_VERIFIED"
        return _text(path), _text(checkpoint_hash or digest)
    return _text(checkpoint), _text(checkpoint_hash, missing="NOT_VERIFIED")


def render_resume_after_reboot(
    *,
    phase: str,
    last_pass_task: str | None,
    reboot_reason: str,
    checkpoint: CheckpointManifest | Path | str | None,
    expected_revit_state: str,
    expected_provider_state: str,
    verification_commands: list[str] | tuple[str, ...],
    next_task: str,
    checkpoint_hash: str | None = None,
) -> str:
    """Render the exact resume handoff without a clock or machine secrets."""

    phase_text = _text(phase)
    last_task_text = _text(last_pass_task, missing="No verified PASS task recorded")
    reason_text = _text(reboot_reason)
    revit_text = _text(expected_revit_state)
    provider_text = _text(expected_provider_state)
    next_task_text = _text(next_task)
    checkpoint_path, checkpoint_digest = _checkpoint_details(checkpoint, checkpoint_hash)
    commands = [
        _text(command, missing="(empty command omitted)")
        for command in verification_commands
        if str(command).strip()
    ]
    if not commands:
        commands = ["NOT_RECORDED"]
    command_lines = "\n".join(f"{index}. `{command}`" for index, command in enumerate(commands, 1))
    return (
        "# RESUME_AFTER_REBOOT\n\n"
        "Status: PREPARED\n\n"
        "## Recovery context\n\n"
        f"- Phase: `{phase_text}`\n"
        f"- Last PASS task: `{last_task_text}`\n"
        f"- Reboot reason: {reason_text}\n"
        f"- Last checkpoint: `{checkpoint_path}`\n"
        f"- Checkpoint SHA-256: `{checkpoint_digest}`\n"
        f"- Expected Revit state: {revit_text}\n"
        f"- Expected provider state: {provider_text}\n\n"
        "## First verification commands\n\n"
        + command_lines
        + "\n\n## Next task\n\n"
        + f"`{next_task_text}`\n\n"
        "## Resume boundary\n\n"
        "Read `AGENTS.md`, `PROJECT_STATE.yaml`, the current plan, and the "
        "incremental handoff before resuming. A checkpoint reopen, provider "
        "healthcheck, current-state re-query, and task readiness must be evidenced "
        "before any new BIM mutation.\n"
    )


def write_resume_after_reboot(root: Path, **kwargs: Any) -> Path:
    """Atomically write the repository-root reboot handoff."""

    target = Path(root).resolve() / "RESUME_AFTER_REBOOT.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    content = render_resume_after_reboot(**kwargs)
    handle, temporary_name = tempfile.mkstemp(
        prefix=".RESUME_AFTER_REBOOT.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


generate_resume_after_reboot = write_resume_after_reboot
generate_resume_file = write_resume_after_reboot


__all__ = [
    "generate_resume_after_reboot",
    "generate_resume_file",
    "render_resume_after_reboot",
    "write_resume_after_reboot",
]
