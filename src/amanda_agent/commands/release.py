"""CLI for fail-closed release promotion and verification."""

from __future__ import annotations

from pathlib import Path

import typer

from ..release.promote import PromotionRefused, verify_release
from ..release.promote import promote as promote_release
from .export import release_directory

release_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Verify release evidence and publish immutable GOLDEN directories.",
)


@release_app.command("promote")
def promote(
    release_id: str = typer.Option(..., "--release-id"),
    root: Path | None = typer.Option(None, "--root"),  # noqa: B008
    golden_root: Path | None = typer.Option(None, "--golden-root"),  # noqa: B008
) -> None:
    """Promote a validated release candidate without overwriting GOLDEN."""

    from .doctor import project_root

    base = root or project_root()
    source = release_directory(base, release_id)
    try:
        result = promote_release(
            source,
            release_id=release_id,
            golden_root=golden_root,
        )
    except (OSError, PromotionRefused, ValueError) as exc:
        typer.echo("release promote refused: " + str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo("release promote PASS")
    typer.echo("golden       " + str(result.target))


@release_app.command("verify")
def verify(
    release_id: str = typer.Option(..., "--release-id"),
    root: Path | None = typer.Option(None, "--root"),  # noqa: B008
) -> None:
    """Recompute release hashes and enforce manifest, QA and profile invariants."""

    from .doctor import project_root

    directory = release_directory(root or project_root(), release_id)
    result = verify_release(directory, require_sealed=True)
    if result.valid:
        typer.echo("release verify PASS")
        typer.echo("release      " + str(directory))
        raise typer.Exit(code=0)
    typer.echo("release verify refused", err=True)
    for error in result.errors:
        typer.echo("  " + error, err=True)
    raise typer.Exit(code=1)


__all__ = ["release_app"]
