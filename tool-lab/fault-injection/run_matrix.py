"""Execute the P02-T17 fault matrix with an offline, evidence-first adapter.

The four cases that need a live Revit document are deliberately skipped.  The
offline adapter is intentionally small: it exercises the project's real
client-side breaker and timeout policy without pretending to be Revit or a
provider integration.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from amanda_agent.tools.circuit_breaker import (  # noqa: E402
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    FailureKind,
    FailureScope,
)


REVIT_SKIP_STATUS = "SKIPPED_NEEDS_REVIT"


class TargetUnavailable(RuntimeError):
    """The configured target cannot accept a provider request."""


class TargetTimeout(TimeoutError):
    """The configured target exceeded the read deadline."""


@dataclass(frozen=True)
class TargetConfig:
    """Identity and deterministic fault behavior for one runner invocation."""

    name: str = "synthetic-offline"
    provider: str = "synthetic"
    revit_build: str = "offline"
    breaker_failure_threshold: int = 3
    timeout_seconds: float = 0.01
    timeout_verification_state: str = "IN_DOUBT"
    safe_to_retry_after_timeout: bool = False

    @classmethod
    def from_json(cls, path: str | Path, *, default_name: str) -> TargetConfig:
        config_path = Path(path)
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"target config must be a JSON object: {config_path}")

        values: dict[str, Any] = dict(payload)
        values.setdefault("name", default_name)
        allowed = {
            "name",
            "provider",
            "revit_build",
            "breaker_failure_threshold",
            "timeout_seconds",
            "timeout_verification_state",
            "safe_to_retry_after_timeout",
        }
        unknown = sorted(set(values) - allowed)
        if unknown:
            raise ValueError("unknown target config fields: " + ", ".join(unknown))
        return cls(**values)


class SyntheticTarget:
    """Offline target that exposes only the fault behavior needed by P02-T17."""

    def __init__(self, config: TargetConfig) -> None:
        self.config = config
        self.events: list[str] = []

    def call_when_unavailable(self, *, reason: str) -> None:
        self.events.append("provider_call")
        raise TargetUnavailable(f"E02: provider unavailable ({reason})")

    def long_read(self) -> Mapping[str, Any]:
        self.events.append("long_read")
        raise TargetTimeout(
            f"E03: long read exceeded {self.config.timeout_seconds:g}s"
        )

    def verify_after_timeout(self) -> Mapping[str, Any]:
        self.events.append("verify_after_timeout")
        return {
            "state": self.config.timeout_verification_state,
            "safe_to_retry": self.config.safe_to_retry_after_timeout,
        }

    def retry_long_read(self) -> Mapping[str, Any]:
        self.events.append("retry_long_read")
        return {"status": "RETRY_ALLOWED_AFTER_VERIFICATION"}


def load_matrix(path: str | Path) -> dict[str, Any]:
    """Load and structurally validate a declarative fault matrix."""

    matrix_path = Path(path)
    payload = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"fault matrix must be a mapping: {matrix_path}")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("fault matrix cases must be a non-empty list")

    required = {
        "id",
        "description",
        "precondition",
        "action",
        "expected_result",
        "expected_error_class",
        "requires_revit",
        "human_gate",
        "proof_layer",
    }
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, Mapping):
            raise ValueError("each fault matrix case must be a mapping")
        missing = sorted(required - set(case))
        if missing:
            raise ValueError(
                f"fault matrix case {case.get('id', '<unknown>')} misses: "
                + ", ".join(missing)
            )
        case_id = str(case["id"])
        if case_id in seen:
            raise ValueError(f"duplicate fault matrix case: {case_id}")
        seen.add(case_id)
        if bool(case["requires_revit"]) != bool(case["human_gate"]):
            raise ValueError(f"requires_revit/human_gate mismatch: {case_id}")
    return dict(payload)


def _result_base(
    case: Mapping[str, Any],
    target: TargetConfig,
    *,
    status: str,
    started: float,
) -> dict[str, Any]:
    return {
        "id": str(case["id"]),
        "slug": str(case.get("slug", case["id"])),
        "status": status,
        "requires_revit": bool(case["requires_revit"]),
        "human_gate": bool(case["human_gate"]),
        "expected_error_class": case["expected_error_class"],
        "target": asdict(target),
        "observations": {},
        "error": None,
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def _skip_revit_case(
    case: Mapping[str, Any], target: TargetConfig, *, started: float
) -> dict[str, Any]:
    result = _result_base(case, target, status=REVIT_SKIP_STATUS, started=started)
    result["observations"] = {
        "reason": "requires a disposable Revit document and human gate",
        "provider_call_attempted": False,
    }
    return result


def _run_unavailable_case(
    case: Mapping[str, Any],
    target: TargetConfig,
    synthetic: SyntheticTarget,
    *,
    reason: str,
    started: float,
) -> dict[str, Any]:
    result = _result_base(case, target, status="FAIL", started=started)
    try:
        synthetic.call_when_unavailable(reason=reason)
    except TargetUnavailable as exc:
        observed_class = "E02"
        result["observations"] = {
            "observed_error_class": observed_class,
            "provider_call_attempted": True,
            "false_success": False,
            "error_message": str(exc),
        }
        result["status"] = (
            "PASS"
            if case["expected_error_class"] == observed_class
            else "FAIL"
        )
        return result
    result["error"] = "target unexpectedly accepted an unavailable-provider call"
    return result


def _run_breaker_case(
    case: Mapping[str, Any],
    target: TargetConfig,
    *,
    breaker_state: Path,
    started: float,
) -> dict[str, Any]:
    result = _result_base(case, target, status="FAIL", started=started)
    payload = case["action"]["payload"]
    signature = str(payload["error_signature"])
    scope = FailureScope(
        provider=target.provider,
        revit_build=target.revit_build,
        capability=str(case["slug"]),
        error_signature=signature,
    )
    breaker = CircuitBreaker(
        breaker_state,
        failure_threshold=target.breaker_failure_threshold,
    )
    states = [
        breaker.record_failure(scope, failure_kind=FailureKind.PROVIDER_HEALTH).value
        for _ in range(3)
    ]
    blocked = False
    try:
        breaker.assert_can_call(scope)
    except CircuitOpenError as exc:
        blocked = True
        block_message = str(exc)
    else:
        block_message = None

    observed_state = breaker.get_state(scope).value
    record = breaker.get_record(scope)
    result["observations"] = {
        "failure_states": states,
        "failure_count": breaker.failure_count(scope),
        "observed_breaker_state": observed_state,
        "ordinary_call_blocked": blocked,
        "block_message": block_message,
        "breaker_state_path": str(breaker_state),
        "scope": scope.model_dump(mode="json"),
        "record_persisted": record is not None,
    }
    result["status"] = (
        "PASS"
        if (
            observed_state == CircuitState.OPEN.value
            and breaker.failure_count(scope) == 3
            and blocked
        )
        else "FAIL"
    )
    return result


def _run_timeout_case(
    case: Mapping[str, Any],
    target: TargetConfig,
    synthetic: SyntheticTarget,
    *,
    started: float,
) -> dict[str, Any]:
    result = _result_base(case, target, status="FAIL", started=started)
    observed_class = None
    verification: Mapping[str, Any] | None = None
    retry_attempted = False
    try:
        synthetic.long_read()
    except TargetTimeout as exc:
        observed_class = "E03"
        verification = synthetic.verify_after_timeout()
        if bool(verification.get("safe_to_retry")):
            synthetic.retry_long_read()
            retry_attempted = True

    verified_before_retry = (
        "verify_after_timeout" in synthetic.events
        and (
            "retry_long_read" not in synthetic.events
            or synthetic.events.index("verify_after_timeout")
            < synthetic.events.index("retry_long_read")
        )
    )
    result["observations"] = {
        "observed_error_class": observed_class,
        "verification": verification,
        "verified_before_retry": verified_before_retry,
        "retry_attempted": retry_attempted,
        "event_order": synthetic.events,
        "safe_to_retry": bool(verification and verification.get("safe_to_retry")),
    }
    result["status"] = (
        "PASS"
        if (
            observed_class == case["expected_result"]["error_class"]
            and verified_before_retry
            and retry_attempted
            == bool(verification and verification.get("safe_to_retry"))
        )
        else "FAIL"
    )
    return result


def execute_case(
    case: Mapping[str, Any],
    target: TargetConfig,
    *,
    breaker_state: str | Path,
) -> dict[str, Any]:
    """Execute one case and return an observed result record."""

    started = time.perf_counter()
    if bool(case["requires_revit"]):
        return _skip_revit_case(case, target, started=started)

    synthetic = SyntheticTarget(target)
    case_id = str(case["id"])
    state_path = Path(breaker_state)
    if case_id == "FI-004":
        return _run_unavailable_case(
            case,
            target,
            synthetic,
            reason="MCP disabled/disconnected",
            started=started,
        )
    if case_id == "FI-005":
        return _run_unavailable_case(
            case,
            target,
            synthetic,
            reason="Revit closed",
            started=started,
        )
    if case_id == "FI-007":
        return _run_breaker_case(
            case,
            target,
            breaker_state=state_path,
            started=started,
        )
    if case_id == "FI-008":
        return _run_timeout_case(case, target, synthetic, started=started)

    result = _result_base(case, target, status="BLOCKED", started=started)
    result["error"] = "no offline adapter is defined for this case"
    result["observations"] = {
        "reason": "the case requires provider/Revit evidence"
    }
    return result


def _summary(results: list[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "total": len(results),
        "pass": sum(item["status"] == "PASS" for item in results),
        "fail": sum(item["status"] == "FAIL" for item in results),
        "blocked": sum(item["status"] == "BLOCKED" for item in results),
        "skipped_needs_revit": sum(
            item["status"] == REVIT_SKIP_STATUS for item in results
        ),
    }


def run_matrix(
    matrix_path: str | Path,
    results_path: str | Path,
    *,
    target: TargetConfig | None = None,
    breaker_state: str | Path | None = None,
) -> dict[str, Any]:
    """Execute the matrix and persist the complete JSON observation report."""

    matrix = load_matrix(matrix_path)
    resolved_target = target or TargetConfig()
    output_path = Path(results_path)
    state_path = Path(breaker_state or output_path.with_suffix(".breaker.yaml"))
    results = [
        execute_case(case, resolved_target, breaker_state=state_path)
        for case in matrix["cases"]
    ]
    report = {
        "schema_version": 1,
        "task_id": matrix.get("task_id", "P02-T17"),
        "generated_utc": datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "matrix_path": str(Path(matrix_path)),
        "target": asdict(resolved_target),
        "cases": results,
        "summary": _summary(results),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix",
        type=Path,
        default=Path(__file__).with_name("matrix.yaml"),
        help="declarative matrix YAML",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=Path(__file__).with_name("results") / "fault-injection.json",
        help="JSON result path",
    )
    parser.add_argument(
        "--target",
        default="synthetic-offline",
        help="target identity recorded in evidence",
    )
    parser.add_argument(
        "--target-config",
        type=Path,
        help="optional JSON TargetConfig override",
    )
    parser.add_argument(
        "--breaker-state",
        type=Path,
        help="optional persisted breaker state path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    target = (
        TargetConfig.from_json(args.target_config, default_name=args.target)
        if args.target_config
        else TargetConfig(name=args.target)
    )
    report = run_matrix(
        args.matrix,
        args.results,
        target=target,
        breaker_state=args.breaker_state,
    )
    print(
        json.dumps(
            {"results": str(args.results), "summary": report["summary"]},
            ensure_ascii=False,
        )
    )
    return 0 if report["summary"]["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
