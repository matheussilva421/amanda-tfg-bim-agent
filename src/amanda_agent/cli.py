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
    """Report environment health and write state/environment-report.json."""
    from .commands.doctor import doctor as run_doctor

    report, target = run_doctor()
    health = report["health"]
    typer.echo("environment report: " + str(target))
    for probe in report["probes"]:
        typer.echo(
            "  "
            + probe["name"].ljust(12)
            + probe["status"].ljust(10)
            + (probe.get("version") or "")
        )
    revit = report["revit"]
    selected = revit.get("selected")
    if selected:
        typer.echo(
            "  revit".ljust(14)
            + "DETECTED  "
            + str(selected.get("product_version"))
            + "  (file "
            + str(selected.get("file_version"))
            + ")"
        )
    else:
        typer.echo("  revit".ljust(14) + str(revit.get("probe_status")))
    for reason in health["reasons"]:
        typer.echo("  note: " + reason)
    if health["blocked_phases"]:
        typer.echo("  blocked phases: " + ", ".join(health["blocked_phases"]))
    if health["critical_failure"]:
        typer.echo("doctor: critical environment failure", err=True)
    raise typer.Exit(code=health["exit_code"])


@app.command()
def status() -> None:
    """Report project state. Read-only: never mutates the state it reports."""
    from .commands.status import render_status, status_snapshot
    from .commands.doctor import project_root

    render_status(status_snapshot(project_root()))


@app.command()
def resume() -> None:
    """Show what can be resumed now, honouring typed blocker severity."""
    from .commands.status import resume_plan
    from .commands.doctor import project_root

    plan = resume_plan(project_root())
    typer.echo("next task   " + plan["next_task"])
    runnable = [
        phase
        for phase in plan["runnable_phases"]
        if phase.startswith("PHASE")
    ]
    typer.echo("runnable    " + ", ".join(runnable))
    if plan["blocked_phases"]:
        typer.echo("blocked     " + ", ".join(plan["blocked_phases"]))
    for blocker in plan["blockers"]:
        typer.echo(
            "blocker     " + blocker.id + " [" + str(blocker.severity) + "]"
        )


@app.command()
def rollback() -> None:
    """Roll back to a checkpoint under a new filename.

    The destructive form requires an explicit checkpoint and target so a bare
    invocation can never overwrite a working model.
    """
    typer.echo(
        "rollback requires --checkpoint and --to; refusing to guess",
        err=True,
    )
    raise typer.Exit(code=2)


@app.command()
def bootstrap() -> None:
    """Set up the foundation and durable state. Safe to run repeatedly."""
    from .commands.bootstrap import bootstrap_environment
    from .commands.doctor import project_root

    result = bootstrap_environment(project_root())
    typer.echo("bootstrap root: " + result["root"])
    if result["created"]:
        for relative in result["created"]:
            typer.echo("  created " + relative)
    else:
        typer.echo("  nothing to create; existing state preserved")
    health = result["report"]["health"]
    for reason in health["reasons"]:
        typer.echo("  note: " + reason)
