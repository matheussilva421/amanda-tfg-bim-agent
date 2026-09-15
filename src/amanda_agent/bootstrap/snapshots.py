"""Configuration snapshots: exact private backup plus a redacted summary.

Two artifacts are produced on purpose. Redacting the only backup would make an
exact rollback impossible, so the byte-preserving copy stays under the ignored
private directory and the Git-tracked summary carries hashes and redacted
settings only.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

from ..redaction import redact

SNAPSHOT_FILENAMES = (
    "config.toml",
    "auth.json",
    "AGENTS.md",
    "instructions.md",
)


def resolve_codex_home(environ: dict | None = None) -> Path:
    """Effective Codex home; the variable is read, never rewritten."""
    source = os.environ if environ is None else environ
    override = source.get("CODEX_HOME")
    if override:
        return Path(override)
    return Path.home() / ".codex"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _restrict_to_current_user(path: Path) -> str:
    """Owner-only ACL on Windows, rolled back if it would deny the owner.

    The account is resolved from the running process rather than from a
    guessed environment variable, and the result is verified by reading the
    snapshot back. A hardening step that locks the owner out is worse than no
    hardening at all, so access is proven before the change is kept.
    """
    if os.name != "nt":
        return "SKIPPED_NON_WINDOWS"

    import subprocess

    def run(*argv: str):
        return subprocess.run(
            ["icacls", str(path), *argv],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

    def readable() -> bool:
        try:
            next(path.iterdir(), None)
            return True
        except OSError:
            return False

    account = None
    try:
        whoami = subprocess.run(
            ["whoami"], capture_output=True, text=True, check=False, timeout=30
        )
        if whoami.returncode == 0 and whoami.stdout.strip():
            account = whoami.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        account = None
    if not account:
        return "SKIPPED_NO_IDENTITY"

    try:
        result = run("/inheritance:r", "/grant:r", account + ":(OI)(CI)F")
        if result.returncode != 0 or not readable():
            run("/reset", "/T", "/Q")
            run("/inheritance:e")
            return "ROLLED_BACK_OWNER_ACCESS_LOST"
    except (OSError, subprocess.SubprocessError):
        return "FAILED_INVOKING_ICACLS"
    return "RESTRICTED_TO_OWNER"


def _parse_toml(text: str):
    try:
        import tomllib

        return tomllib.loads(text)
    except Exception:
        return None


def snapshot_codex_config(
    *,
    codex_home: Path,
    private_root: Path,
    timestamp: str,
    harden_acl: bool = False,
) -> dict:
    """Copy the effective Codex configuration and summarize it safely."""
    codex_home = Path(codex_home)
    private_dir = Path(private_root) / timestamp / "codex-home"
    summary = {
        "generated_utc": timestamp,
        "codex_home": str(codex_home),
        "private_dir": str(private_dir),
        "status": "MISSING",
        "files": [],
        "note": (
            "The private directory holds the byte-preserving backup and is "
            "excluded from Git; only this redacted summary may be committed."
        ),
    }

    if not codex_home.is_dir():
        return summary

    private_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for name in SNAPSHOT_FILENAMES:
        source = codex_home / name
        if not source.is_file():
            continue
        target = private_dir / name
        shutil.copy2(source, target)
        raw = source.read_text(encoding="utf-8", errors="replace")
        entry = {
            "name": name,
            "bytes": source.stat().st_size,
            "sha256": sha256_of(source),
            "backup_path": str(target),
        }
        parsed = _parse_toml(raw) if name.endswith(".toml") else None
        if parsed is not None:
            entry["settings"] = redact(parsed)
        else:
            entry["settings"] = {
                "unparsed": True,
                "sha256_of_content": hashlib.sha256(
                    raw.encode("utf-8", errors="replace")
                ).hexdigest(),
            }
        files.append(entry)

    summary["files"] = files
    summary["status"] = "SNAPSHOTTED" if files else "EMPTY"
    # The private directory lives inside the user profile, which is already
    # scoped to the local account and administrators, and .gitignore keeps it
    # out of the repository. Rewriting ACLs is therefore opt-in: an
    # inheritance-breaking ACL that denies the owner is worse than relying on
    # the profile defaults, and it would also block sandboxed cleanup.
    if harden_acl:
        summary["private_acl"] = _restrict_to_current_user(private_dir)
    else:
        summary["private_acl"] = "DEFAULT_PROFILE_ACL"
    return summary


def inventory_revit_addins(roots: list[Path]) -> list[dict]:
    """Hash add-in manifests and bundles; content is never copied."""
    entries: list[dict] = []
    for root in roots:
        root = Path(root)
        if not root.exists():
            entries.append(
                {
                    "path": str(root),
                    "kind": "root",
                    "status": "ABSENT",
                    "note": "no add-ins installed at this root",
                }
            )
            continue
        if not any(True for _ in root.rglob("*")):
            entries.append(
                {
                    "path": str(root),
                    "kind": "root",
                    "status": "EMPTY",
                    "note": "root exists but contains no add-in files",
                }
            )
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            entries.append(
                {
                    "path": str(path),
                    "kind": path.suffix.lower().lstrip(".") or "file",
                    "status": "PRESENT",
                    "bytes": path.stat().st_size,
                    "sha256": sha256_of(path),
                    "modified_utc": _modified_utc(path),
                }
            )
    return entries


def _modified_utc(path: Path) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
