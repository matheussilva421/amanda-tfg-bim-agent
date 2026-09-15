"""Command line entry point.

The application is intentionally built as a skeleton first: the command set is
declared before any behaviour exists so that missing behaviour is observable as
a failing test rather than as an absent module.
"""

import typer

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Amanda TFG BIM Agent control plane.",
)


@app.command()
def version() -> None:
    """Print the control-plane version."""
    from . import __version__

    typer.echo(__version__)


@app.command()
def doctor() -> None:
    """Report environment health. Not implemented yet."""
    typer.echo("doctor: not implemented", err=True)
    raise typer.Exit(code=2)


@app.command()
def status() -> None:
    """Report project state. Not implemented yet."""
    typer.echo("status: not implemented", err=True)
    raise typer.Exit(code=2)


@app.command()
def resume() -> None:
    """Resume work. Not implemented yet."""
    typer.echo("resume: not implemented", err=True)
    raise typer.Exit(code=2)


@app.command()
def rollback() -> None:
    """Roll back to a checkpoint. Not implemented yet."""
    typer.echo("rollback: not implemented", err=True)
    raise typer.Exit(code=2)
