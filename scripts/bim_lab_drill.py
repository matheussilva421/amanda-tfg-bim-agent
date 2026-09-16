"""Fail-closed synthetic BIM lab drill.

The default mode only prints the generated R01-R13 plan summary.  Revit and
the MCP transport are constructed only after the explicit ``--execute`` flag
and lab-path safety gates pass.

``--preflight`` performs a read-only target, writer-lock and provider-health
check.  It returns 0 when all gates pass, 2 for a local safety or lock refusal,
and 3 when the provider cannot be reached.  A preflight never records PASS or
acquires the writer lock.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from amanda_agent.bim.checkpoints import CheckpointError
from amanda_agent.bim.lab_fixture import (
    BUILD,
    SCHEMA,
    build_lab_fixture_plans,
    build_lab_fixture_registry,
)
from amanda_agent.bim.providers import (
    HorizunInvoker,
    McpProbeTransport,
    McpTransport,
    McpTransportError,
)
from amanda_agent.bim.runner import RunStatus, StageRunResult, execute_chain
from amanda_agent.bim.safety import SafetyError, assert_writable_target
from amanda_agent.bim.stages import create_stage_checkpoint
from amanda_agent.state.locks import LockError, WriterLock

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LAB_ROOT = REPOSITORY_ROOT / "revit" / "lab"
WRITER_LOCK_PATH = REPOSITORY_ROOT / "state" / "locks" / "revit-writer.lock"


class LabDrillError(RuntimeError):
    """The drill cannot prove a safe synthetic lab target."""


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return True


def _assert_lab_target(
    path: Path, *, label: str, lab_root: Path = LAB_ROOT
) -> Path:
    candidate = Path(path).resolve(strict=False)
    safe_lab_root = Path(lab_root).resolve(strict=False)
    if not _under(candidate, safe_lab_root):
        raise LabDrillError(
            f"{label} must be inside the laboratory area: {candidate}"
        )
    try:
        return assert_writable_target(candidate, writable_roots=[safe_lab_root])
    except SafetyError as exc:
        raise LabDrillError(f"{label} refused by safety sentinel: {exc}") from exc


def _assert_fixture_root(path: Path) -> Path:
    root = Path(path).resolve(strict=False)
    if not _under(root, LAB_ROOT):
        raise LabDrillError(
            f"fixture-root must be inside the repository laboratory area: {root}"
        )
    # The safety API validates file targets.  A non-existent child proves the
    # directory is an allowed write area without creating or replacing it.
    probe = root / ".amanda-bim-fixture-target.rvt"
    try:
        assert_writable_target(probe, writable_roots=[LAB_ROOT])
    except SafetyError as exc:
        raise LabDrillError(f"fixture-root refused by safety sentinel: {exc}") from exc
    return root


def _build_plans(root: Path) -> list[Any]:
    registry = build_lab_fixture_registry(
        root=root,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
    )
    return build_lab_fixture_plans(
        root=root,
        registry=registry,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
    )


def _print_plan(plans: Iterable[Any]) -> None:
    print("BIM LAB DRILL (dry-run; no Revit/MCP/lock/checkpoint writes)")
    for plan in plans:
        print(
            f"{plan.stage.name} {plan.checkpoint_label}: {len(plan.operations)} operation(s)"
        )
        for operation in plan.operations:
            provider = operation.preferred_provider or (
                operation.fallback_providers[0]
                if operation.fallback_providers
                else "UNSELECTED"
            )
            print(
                f"  {operation.logical_id} [{operation.semantic_capability}]"
                f" provider={provider}"
            )


def _record_json(record: Any) -> dict[str, Any]:
    return {
        "stage": record.stage.name,
        "logical_id": record.logical_id,
        "semantic_capability": record.semantic_capability,
        "provider": record.provider,
        "tool": record.tool,
        "reported_success": record.reported_success,
        "status": record.status.value,
        "unique_id": record.unique_id,
        "evidence": record.evidence,
        "error": record.error,
        "layers": [layer.model_dump(mode="json") for layer in record.layers],
    }


def _stage_json(result: StageRunResult, *, checkpoint: Any | None) -> dict[str, Any]:
    return {
        "stage": result.stage.name,
        "status": result.status.value,
        "warnings": list(result.warnings),
        "checkpoint": (
            {
                "path": str(checkpoint.checkpoint_path),
                "manifest": str(checkpoint.manifest_path),
                "sha256": checkpoint.sha256,
            }
            if checkpoint is not None
            else None
        ),
        "records": [_record_json(record) for record in result.records],
    }


def _write_stage_journal(
    result: StageRunResult, *, root: Path, checkpoint: Any | None
) -> Path:
    journal = root / "journals" / f"{result.stage.name}.json"
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text(
        json.dumps(_stage_json(result, checkpoint=checkpoint), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return journal


def _default_transport_factory() -> McpProbeTransport:
    return McpProbeTransport()


def _default_health_check(transport: McpTransport) -> Mapping[str, Any] | None:
    reply = transport.call("horizun_health", {})
    if reply is None:
        raise McpTransportError("horizun health returned no response")
    return reply


def _assert_provider_health(result: Any) -> None:
    if result is False or result is None:
        raise McpTransportError("horizun health reported an unreachable provider")
    if not isinstance(result, Mapping):
        return
    if result.get("error"):
        raise McpTransportError(f"horizun health returned an error: {result['error']}")
    if result.get("healthy") is False or result.get("ok") is False:
        raise McpTransportError("horizun health reported an unhealthy provider")
    nested = result.get("result")
    if isinstance(nested, Mapping) and nested.get("isError") is True:
        raise McpTransportError("horizun health reported an MCP error")


def run_preflight(
    rvt: Path,
    *,
    lab_root: Path = LAB_ROOT,
    lock_path: Path = WRITER_LOCK_PATH,
    transport_factory: Callable[[], Any] | None = None,
    health_check: Callable[[McpTransport], Any] | None = None,
) -> int:
    """Run read-only safety and provider gates before the lab drill.

    ``transport_factory`` and ``health_check`` are injectable so this contract
    can be verified without constructing Revit or contacting the live MCP.
    """

    try:
        safe_rvt = _assert_lab_target(rvt, label="--rvt", lab_root=lab_root)
        if not safe_rvt.is_file():
            raise LabDrillError(f"--rvt must identify an existing lab RVT file: {safe_rvt}")
        writer_lock = WriterLock(lock_path, owner="amanda-bim-lab-preflight")
        if writer_lock.exists():
            raise LabDrillError(f"writer lock is occupied: {lock_path}")
    except (LabDrillError, LockError) as exc:
        print(f"BIM LAB PREFLIGHT: REFUSED ({exc})", file=sys.stderr)
        return 2

    factory = transport_factory or _default_transport_factory
    check_health = health_check or _default_health_check
    try:
        with factory() as transport:
            _assert_provider_health(check_health(transport))
    except Exception as exc:  # noqa: BLE001 - preflight must fail closed at the provider boundary
        print(f"BIM LAB PREFLIGHT: PROVIDER_UNREACHABLE ({exc})", file=sys.stderr)
        return 3

    print("BIM LAB PREFLIGHT: PASS (target allowed, writer lock free, provider reachable)")
    return 0


def _execute(rvt: Path, fixture_root: Path) -> int:
    safe_rvt = _assert_lab_target(rvt, label="--rvt")
    safe_fixture_root = _assert_fixture_root(fixture_root)
    if not safe_rvt.is_file():
        raise LabDrillError(f"--rvt must identify an existing lab RVT file: {safe_rvt}")

    lock = WriterLock(WRITER_LOCK_PATH, owner="amanda-bim-lab-drill")
    lock.acquire(reclaim_abandoned=True)
    try:
        # Re-check the target after the lease exists so the write boundary has
        # the same owner token that guards the provider run.
        try:
            assert_writable_target(
                safe_rvt,
                writable_roots=[LAB_ROOT],
                lease=lock,
                lease_token=lock.owner_token,
                require_lease=True,
            )
        except SafetyError as exc:
            raise LabDrillError(
                f"--rvt lease-bound safety check refused: {exc}"
            ) from exc

        plans = _build_plans(safe_fixture_root)

        def on_stage(result: StageRunResult) -> None:
            checkpoint = None
            if result.status is RunStatus.VERIFIED:
                checkpoint = create_stage_checkpoint(
                    source_path=safe_rvt,
                    checkpoint_path=safe_fixture_root
                    / "checkpoints"
                    / f"{result.stage.name}.rvt",
                    stage=result.stage,
                )
            journal = _write_stage_journal(
                result,
                root=safe_fixture_root,
                checkpoint=checkpoint,
            )
            print(
                f"{result.stage.name} {result.status.value}"
                f" records={len(result.records)} journal={journal}"
            )

        print("BIM LAB DRILL (--execute; lab target only; parent review required)")
        with McpProbeTransport() as transport:
            invoker = HorizunInvoker(transport=transport, target_document=str(safe_rvt))
            results = execute_chain(plans, invoker=invoker, on_stage=on_stage)
        if len(results) != len(plans) or any(
            result.status is not RunStatus.VERIFIED for result in results
        ):
            return 2
        return 0
    finally:
        lock.release()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rvt", type=Path, required=True, help="Lab RVT target")
    parser.add_argument(
        "--fixture-root",
        type=Path,
        help="Directory for synthetic evidence, checkpoints and journals",
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--execute",
        action="store_true",
        help="Explicitly run the provider against the validated lab RVT",
    )
    modes.add_argument(
        "--preflight",
        action="store_true",
        help="Read-only target, writer-lock and provider-health check",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.preflight:
            return run_preflight(args.rvt)
        if args.execute:
            if args.fixture_root is None:
                print(
                    "bim lab drill refused: --fixture-root is required with --execute",
                    file=sys.stderr,
                )
                return 2
            return _execute(args.rvt, args.fixture_root)
        with tempfile.TemporaryDirectory(prefix="amanda-bim-lab-dry-") as temporary:
            plans = _build_plans(Path(temporary))
            _print_plan(plans)
        return 0
    except (
        CheckpointError,
        LabDrillError,
        LockError,
        McpTransportError,
        OSError,
        ValueError,
    ) as exc:
        print(f"bim lab drill refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
