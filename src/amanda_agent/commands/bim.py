"""Read-only BIM plan inspection and explicit synthetic execution commands."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from ..bim.journal import (
    JOURNAL_FILENAME,
    ExecutionJournal,
    JournalError,
    locate_journal,
    validate_evidence_path,
)
from ..bim.plan import BimPlan, write_plan_set
from ..models.capability import CapabilityRegistry

bim_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Inspect BIM plans and run an explicit synthetic-lab simulation.",
)


class BimCliError(RuntimeError):
    """The CLI cannot safely inspect or execute the requested plan."""


def _read_plan(path: Path) -> BimPlan:
    if path.is_symlink() or not path.is_file():
        raise BimCliError(f"plan file is missing or mutable: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return BimPlan.model_validate(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise BimCliError(f"invalid BIM plan: {exc}") from exc


def _fail(message: str) -> typer.NoReturn:
    typer.echo("bim refused: " + message, err=True)
    raise typer.Exit(code=2)


@bim_app.command()
def plan(
    solution: Path = typer.Option(  # noqa: B008
        ...,
        "--solution",
        exists=False,
        dir_okay=False,
        help="Path to the serialized BIM_PLAN.json to inspect.",
    ),
) -> None:
    """Inspect a plan and its diff operations without executing anything."""

    try:
        loaded = _read_plan(solution)
    except BimCliError as exc:
        _fail(str(exc))
    try:
        json_path, markdown_path = write_plan_set(loaded, solution.parent)
    except (OSError, ValueError) as exc:
        _fail(f"could not materialize BIM plan artifacts: {exc}")
    typer.echo("BIM plan (read-only Revit; artifacts generated)")
    typer.echo("json: " + str(json_path))
    typer.echo("markdown: " + str(markdown_path))
    typer.echo("document: " + loaded.document_id)
    typer.echo("managed: " + str(loaded.managed_count))
    typer.echo("operations: " + str(len(loaded.operations)))
    for operation in loaded.operations:
        typer.echo(
            f"  {operation.action.value} {operation.logical_id}"
            f" [{operation.semantic_capability}]"
        )


@bim_app.command(name="verify-plan")
def verify_plan(
    path: Path = typer.Argument(..., help="Path to the serialized BIM_PLAN.json."),  # noqa: B008
) -> None:
    """Show the independent write-read-verify rules encoded in a plan."""

    try:
        loaded = _read_plan(path)
    except BimCliError as exc:
        _fail(str(exc))
    typer.echo("BIM plan write-read-verify rules (read-only)")
    for operation in loaded.operations:
        typer.echo(f"  {operation.logical_id}: ")
        for rule in operation.verification_rules:
            typer.echo("    - " + rule)


@bim_app.command()
def status(
    project_root: Path = typer.Option(  # noqa: B008
        Path("."),
        "--project-root",
        help="Project root holding state/capabilities.yaml and the crosswalk.",
        dir_okay=True,
        file_okay=False,
    ),
) -> None:
    """Report available BIM modes without inspecting or mutating a model."""

    typer.echo("BIM status (read-only)")
    typer.echo("default mode: SYNTHETIC_LAB")
    typer.echo("execution: disabled unless --execute is explicit")
    typer.echo("provider writes: none")
    registry_path = Path(project_root) / "state" / "capabilities.yaml"
    crosswalk_path = Path(project_root) / "state" / "providers" / "semantic-crosswalk.yaml"
    if crosswalk_path.is_file():
        typer.echo("semantic crosswalk: loaded" + " (" + str(crosswalk_path) + ")")
    else:
        typer.echo("semantic crosswalk: not found" + " (" + str(crosswalk_path) + ")")
    if registry_path.is_file():
        try:
            registry, warnings = CapabilityRegistry.load_for_production(project_root)
        except (OSError, ValueError) as exc:
            _fail(f"could not load the capability registry: {exc}")
        typer.echo("capability registry: " + str(len(registry.entries)) + " entries")
        builds = sorted(
            {entry.revit_build for entry in registry.entries if entry.revit_build}
        )
        typer.echo("recorded builds: " + (", ".join(builds) if builds else "none"))
        for warning in warnings:
            typer.echo("warning: " + warning)
    else:
        typer.echo("capability registry: not found (" + str(registry_path) + ")")


@bim_app.command()
def claim(
    plan: Path = typer.Option(  # noqa: B008
        ...,
        "--plan",
        exists=False,
        dir_okay=False,
        help="Path to the serialized BIM_PLAN.json.",
    ),
) -> None:
    """Atomically claim the next READY operation in a durable journal."""

    try:
        _read_plan(plan)
        journal = ExecutionJournal(plan.parent / JOURNAL_FILENAME)
        event = journal.claim(plan)
    except (BimCliError, JournalError) as exc:
        _fail(str(exc))
    typer.echo("claimed     " + event["operation_id"])
    typer.echo("state       " + event["state"])
    typer.echo("lease       " + event["lease_token"])
    typer.echo("journal     " + str(journal.path))


@bim_app.command(name="record-result")
def record_result(
    operation_id: str = typer.Option(..., "--operation-id", help="Claimed task id."),
    evidence: Path = typer.Option(  # noqa: B008
        ...,
        "--evidence",
        exists=False,
        dir_okay=False,
        help="Path to independent write-read-verify evidence.",
    ),
) -> None:
    """Record an independently evidenced PASS for a claimed operation."""

    try:
        validate_evidence_path(evidence)
        journal = locate_journal(operation_id, evidence)
        event = journal.record_result(operation_id, evidence)
    except JournalError as exc:
        _fail(str(exc))
    typer.echo("recorded    " + event["operation_id"] + " " + event["result_status"])
    typer.echo("state       " + event["state"])
    typer.echo("evidence    " + event["evidence_sha256"])
    typer.echo("journal     " + str(journal.path))


@bim_app.command()
def execute(
    plan: Path = typer.Option(  # noqa: B008
        ...,
        "--plan",
        exists=False,
        dir_okay=False,
        help="Path to the serialized BIM_PLAN.json.",
    ),
    mode: str = typer.Option(..., "--mode", help="Execution mode."),
    fixture: bool = typer.Option(
        False,
        "--fixture",
        help="Confirm that the target is a synthetic fixture.",
    ),
    execute: bool = typer.Option(
        False,
        "--execute",
        help="Explicitly authorize the synthetic execution simulation.",
    ),
) -> None:
    """Run a deterministic synthetic simulation after explicit safety flags."""

    if not execute:
        _fail("pass --execute explicitly to run a BIM command")
    if mode != "SYNTHETIC_LAB":
        _fail("execution is restricted to mode SYNTHETIC_LAB")
    if not fixture:
        _fail("SYNTHETIC_LAB requires --fixture")
    try:
        loaded = _read_plan(plan)
    except BimCliError as exc:
        _fail(str(exc))
    typer.echo("BIM execute (SYNTHETIC_LAB; fixture; no Revit write)")
    for operation in loaded.operations:
        typer.echo(f"  WRITE {operation.logical_id} synthetic PASS")
        typer.echo(f"  READ  {operation.logical_id} independent query PASS")
        typer.echo(f"  VERIFY {operation.logical_id} write-read-verify PASS")


__all__ = ["bim_app"]
