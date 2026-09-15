"""Command line entry point.

The application is intentionally built as a skeleton first: the command set is
declared before any behaviour exists so that missing behaviour is observable as
a failing test rather than as an absent module.
"""

from pathlib import Path

import typer

from .commands.tool_lab import tool_lab_app

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Amanda TFG BIM Agent control plane.",
)

app.add_typer(tool_lab_app, name="tool-lab")


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
    from .commands.doctor import project_root
    from .commands.status import render_status, status_snapshot

    render_status(status_snapshot(project_root()))


@app.command(name="task-graph")
def task_graph() -> None:
    """Show task-level progress and the exact READY tasks. Read-only."""
    from .commands.advance import render_task_graph, task_graph_report
    from .commands.doctor import project_root
    from .state.advance import AdvanceRefused

    try:
        report = task_graph_report(project_root())
    except AdvanceRefused as exc:
        typer.echo("task-graph: " + str(exc), err=True)
        raise typer.Exit(code=2)
    render_task_graph(report)


@app.command()
def advance(
    task: str = typer.Option(..., "--task", help="Task id such as P01-T01."),
    status: str = typer.Option(..., "--status", help="Outcome to record."),
    evidence: list[str] = typer.Option(
        None, "--evidence", help="Command and result. Repeat for each."
    ),
    next_task: str = typer.Option(
        None, "--next-task", help="Override the computed next READY task."
    ),
    expected_revision: int = typer.Option(
        None, "--expected-revision", help="Refuse if the state moved on."
    ),
    allow_unready: str = typer.Option(
        None,
        "--allow-unready",
        help="Record a task whose dependencies are unfinished, with the reason.",
    ),
) -> None:
    """Record a finished task. Requires evidence: green without proof is a lie."""
    from .commands.advance import run_advance
    from .commands.doctor import project_root
    from .state.advance import AdvanceRefused

    try:
        result = run_advance(
            project_root(),
            task_id=task,
            status=status,
            evidence=list(evidence or []),
            next_task=next_task,
            expected_revision=expected_revision,
            allow_unready=allow_unready,
        )
    except AdvanceRefused as exc:
        typer.echo("advance refused: " + str(exc), err=True)
        raise typer.Exit(code=2)
    typer.echo("recorded     " + result["task_id"] + " " + result["status"])
    typer.echo("next task    " + str(result["next_task"]))
    typer.echo("revision     " + str(result["state_revision"]))


@app.command(name="phase-gate")
def phase_gate(
    gate: str = typer.Option(..., "--gate", help="GO, GO_WITH_LIMITATIONS or NO_GO."),
    reason: str = typer.Option(..., "--reason", help="Why this gate was chosen."),
    verified_commit: str = typer.Option(
        None, "--verified-commit", help="Commit hash the gate was checked against."
    ),
) -> None:
    """Record the phase gate decision on PROJECT_STATE.yaml."""
    from .commands.advance import run_phase_gate
    from .commands.doctor import project_root
    from .state.advance import AdvanceRefused

    try:
        result = run_phase_gate(
            project_root(),
            gate=gate,
            reason=reason,
            verified_commit=verified_commit,
        )
    except AdvanceRefused as exc:
        typer.echo("phase-gate refused: " + str(exc), err=True)
        raise typer.Exit(code=2)
    typer.echo("phase gate   " + result["phase_gate"])
    typer.echo("reason       " + result["reason"])
    typer.echo("revision     " + str(result["state_revision"]))


@app.command(name="advance-phase")
def advance_phase(
    gate: str = typer.Option(..., "--gate", help="GO, GO_WITH_LIMITATIONS or NO_GO."),
    next_phase: str = typer.Option(..., "--next-phase", help="Phase id to open."),
    next_phase_name: str = typer.Option(
        ..., "--next-phase-name", help="Human name of the phase to open."
    ),
    next_task: str = typer.Option(..., "--next-task", help="First task of that phase."),
    reason: str = typer.Option(..., "--reason", help="Why the gate is defensible."),
) -> None:
    """Close the current phase. Refuses while its tasks are still open."""
    from .commands.advance import run_advance_phase
    from .commands.doctor import project_root
    from .state.advance import AdvanceRefused

    try:
        result = run_advance_phase(
            project_root(),
            gate=gate,
            next_phase_id=next_phase,
            next_phase_name=next_phase_name,
            next_task=next_task,
            reason=reason,
        )
    except AdvanceRefused as exc:
        typer.echo("advance-phase refused: " + str(exc), err=True)
        raise typer.Exit(code=2)
    typer.echo("phase        " + result["phase_id"])
    typer.echo("phase gate   " + result["phase_gate"])
    typer.echo("next task    " + result["next_task"])
    typer.echo("revision     " + str(result["state_revision"]))


@app.command()
def resume() -> None:
    """Show what can be resumed now, honouring typed blocker severity."""
    from .commands.doctor import project_root
    from .commands.status import resume_plan

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
def ingest(
    paths: list[str] = typer.Argument(
        None, help="Source files to copy into the immutable local store."
    ),
    source_id: list[str] = typer.Option(
        None, "--id", help="Stable source id such as SRC-PROGRAM-001."
    ),
    validate_only: bool = typer.Option(
        False,
        "--validate-only",
        help="Validate sources and canonical project data, without ingesting files.",
    ),
) -> None:
    """Ingest source files or validate the canonical project boundary."""
    from .commands.doctor import project_root
    from .commands.ingest import IngestError, ingest_sources

    if validate_only:
        from .ingest.validate import validate_project, write_validation_report

        root = project_root()
        validation = validate_project(root)
        report_path = write_validation_report(root, validation)
        typer.echo("report       " + str(report_path))
        typer.echo("verdict      " + validation.verdict)
        if validation.verdict == "NO_GO":
            raise typer.Exit(code=1)
        return

    if not paths:
        typer.echo(
            "ingest needs at least one PATH, for example: "
            "amanda-agent ingest programa_necessidades.pdf --id SRC-PROGRAM-001",
            err=True,
        )
        raise typer.Exit(code=2)
    try:
        documents = ingest_sources(
            project_root(),
            [Path(value) for value in paths],
            source_ids=list(source_id) if source_id else None,
        )
    except IngestError as exc:
        typer.echo("ingest refused: " + str(exc), err=True)
        raise typer.Exit(code=2)
    for document in documents:
        typer.echo(
            "ingested     "
            + document.source_id
            + "  "
            + document.sha256
            + "  "
            + document.immutable_path
        )


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


@app.command()
def design(
    run_id: str = typer.Option(..., "--run-id", help="Stable design run id."),
) -> None:
    """Generate a deterministic run from canonical requirements and site data."""
    from .commands.design import DesignInputError, design_command

    try:
        result = design_command(run_id)
    except DesignInputError as exc:
        typer.echo("design refused: " + str(exc), err=True)
        raise typer.Exit(code=2) from exc
    typer.echo("design run   " + result["run_id"])
    typer.echo("run dir      " + str(result["run_directory"]))
    typer.echo("candidates   " + str(result["candidate_count"]))
    typer.echo("finalists    " + str(result["finalist_count"]))


@app.command()
def compare(
    run_id: str = typer.Argument(..., help="Design run id such as RUN-001."),
) -> None:
    """Print and persist the finalist comparison matrix."""
    from .commands.compare import CompareInputError, compare_command, render_matrix

    try:
        result = compare_command(run_id)
    except CompareInputError as exc:
        typer.echo("compare refused: " + str(exc), err=True)
        raise typer.Exit(code=2) from exc
    render_matrix(result)


if __name__ == "__main__":
    app()
