"""Reconcile a configured program of needs with observed model evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from .models import QaCheck, QaCheckStatus, QaIssue, QaReport, QaResult, Severity


async def load_program_config(source: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    """Load a program configuration from a mapping or YAML file asynchronously."""

    if isinstance(source, Mapping):
        return dict(source)
    path = Path(source)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        return dict(dump())
    raise TypeError(f"expected mapping-like program input, got {type(value).__name__}")


def _configured_spaces(program: Any) -> list[dict[str, Any]]:
    payload = _as_mapping(program)
    result: list[dict[str, Any]] = []

    for key in ("spaces", "rooms", "external_spaces"):
        for item in payload.get(key, []) or []:
            result.append(dict(item))
    for sector in payload.get("sectors", []) or []:
        sector_area_kind = sector.get("area_kind")
        for item in sector.get("spaces", []) or []:
            row = dict(item)
            if sector_area_kind is not None:
                row.setdefault("area_kind", sector_area_kind)
            result.append(row)
    unique: dict[str, dict[str, Any]] = {}
    for item in result:
        logical_id = str(item.get("logical_id", "")).strip()
        if logical_id:
            unique[logical_id] = item
    return list(unique.values())


def _observed_spaces(observed: Any) -> dict[str, dict[str, Any]]:
    if observed is None:
        return {}
    if isinstance(observed, Mapping):
        rows = observed.get("spaces", observed.get("rooms", []))
        if isinstance(rows, Mapping):
            return {str(key): dict(value) for key, value in rows.items()}
        result = {str(item["logical_id"]): dict(item) for item in rows or [] if "logical_id" in item}
        return result
    return {
        str(item["logical_id"]): dict(item)
        for item in observed
        if isinstance(item, Mapping) and "logical_id" in item
    }


def _area_limits(spec: Mapping[str, Any]) -> tuple[float, float, float, float]:
    target = spec.get("target_area_m2", spec.get("area_m2"))
    configured_range = spec.get("area_range_m2", spec.get("area_range"))
    if configured_range is None:
        if target is None:
            raise ValueError(f"space {spec.get('logical_id')} has no area rule")
        configured_range = [target, target]
    low, high = float(configured_range[0]), float(configured_range[1])
    soft = float(spec.get("soft_tolerance_m2", spec.get("soft_tolerance", 0)))
    hard_minimum = float(spec.get("hard_minimum_m2", spec.get("hard_minimum", low)))
    return low, high, soft, hard_minimum


def _observed_area(row: Mapping[str, Any]) -> float:
    if "area_m2" in row:
        return float(row["area_m2"])
    if "unit_area_m2" in row:
        return float(row["unit_area_m2"])
    if "total_area_m2" in row and int(row.get("quantity", 1)):
        return float(row["total_area_m2"]) / int(row.get("quantity", 1))
    raise ValueError("observed space has no area_m2")


def _issue(
    code: str,
    message: str,
    *,
    check_id: str,
    spec: Mapping[str, Any],
    mandatory: bool,
    severity: Severity,
    observed: Mapping[str, Any] | None = None,
) -> QaIssue:
    evidence = {
        "logical_id": spec.get("logical_id"),
        "area_kind": spec.get("area_kind", "INTERNAL"),
        "required_quantity": spec.get("quantity", 1),
    }
    if observed is not None:
        evidence["observed"] = dict(observed)
    return QaIssue(
        code=code,
        message=message,
        severity=severity,
        scope="program",
        mandatory=mandatory,
        evidence=evidence,
        check_id=check_id,
    )


async def reconcile_program(
    program: Mapping[str, Any] | str | Path | Any,
    observed: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    *,
    config: Mapping[str, Any] | str | Path | None = None,
    profile: str = "STUDY",
    scope: str = "program",
) -> QaReport:
    """Reconcile configured rooms and external spaces against query evidence.

    The program is an injected model. No room names or TFG-specific identifiers
    are interpreted by this validator; ``logical_id`` is the only identity key.
    """

    configured = await load_program_config(config) if config is not None else _as_mapping(program)
    expected_spaces = _configured_spaces(configured)
    observed_by_id = _observed_spaces(observed)
    issues: list[QaIssue] = []
    checks: list[QaCheck] = []
    required_ids: list[str] = []

    for spec in expected_spaces:
        logical_id = str(spec["logical_id"])
        check_id = f"program.{logical_id}"
        required_ids.append(check_id)
        row = observed_by_id.get(logical_id)
        status = QaCheckStatus.PASS
        if row is None:
            status = QaCheckStatus.FAIL
            issues.append(
                _issue(
                    "MISSING_REQUIRED_SPACE",
                    f"required programmed space {logical_id!r} is missing",
                    check_id=check_id,
                    spec=spec,
                    mandatory=True,
                    severity=Severity.HIGH,
                )
            )
        else:
            expected_quantity = int(spec.get("quantity", 1))
            actual_quantity = int(row.get("quantity", 1))
            if actual_quantity != expected_quantity:
                status = QaCheckStatus.FAIL
                issues.append(
                    _issue(
                        "QUANTITY_MISMATCH",
                        f"space {logical_id!r} has quantity {actual_quantity}, expected {expected_quantity}",
                        check_id=check_id,
                        spec=spec,
                        mandatory=True,
                        severity=Severity.HIGH,
                        observed=row,
                    )
                )
            try:
                area = _observed_area(row)
                low, high, soft, hard_minimum = _area_limits(spec)
            except (KeyError, TypeError, ValueError) as exc:
                status = QaCheckStatus.BLOCKED
                issues.append(
                    QaIssue(
                        code="MISSING_INPUT_AREA",
                        message=f"space {logical_id!r} cannot be checked: {exc}",
                        severity=Severity.HIGH,
                        scope="program",
                        mandatory=True,
                        evidence={"logical_id": logical_id, "observed": dict(row)},
                        check_id=check_id,
                        missing_input=True,
                    )
                )
            else:
                if area < hard_minimum:
                    status = QaCheckStatus.FAIL
                    issues.append(
                        _issue(
                            "AREA_BELOW_HARD_MINIMUM",
                            f"space {logical_id!r} area {area:g} m2 is below hard minimum {hard_minimum:g} m2",
                            check_id=check_id,
                            spec=spec,
                            mandatory=True,
                            severity=Severity.HIGH,
                            observed=row,
                        )
                    )
                elif area < low - soft or area > high + soft:
                    issues.append(
                        _issue(
                            "AREA_OUTSIDE_SOFT_TOLERANCE",
                            f"space {logical_id!r} area {area:g} m2 is outside configured soft tolerance",
                            check_id=check_id,
                            spec=spec,
                            mandatory=False,
                            severity=Severity.MEDIUM,
                            observed=row,
                        )
                    )
        checks.append(
            QaCheck(
                check_id=check_id,
                mandatory=True,
                status=status,
                severity_if_failed=Severity.HIGH,
                scope="program",
            )
        )

    observed_summary = observed if isinstance(observed, Mapping) else {}
    expected_totals = configured.get("totals", {})
    total_checks: list[QaCheck] = []
    for key, check_id in (
        ("internal_useful_m2", "program.total.internal"),
        ("external_programmed_m2", "program.total.external"),
    ):
        if key not in expected_totals or key not in observed_summary:
            continue
        required_ids.append(check_id)
        expected = float(expected_totals[key])
        actual = float(observed_summary[key])
        status = QaCheckStatus.PASS if actual == expected else QaCheckStatus.FAIL
        if status is QaCheckStatus.FAIL:
            issues.append(
                QaIssue(
                    code="PROGRAM_TOTAL_MISMATCH",
                    message=f"program total {key} is {actual:g}, expected {expected:g}",
                    severity=Severity.HIGH,
                    scope="program",
                    mandatory=True,
                    evidence={"expected": expected, "observed": actual, "area_kind": key},
                    check_id=check_id,
                )
            )
        total_checks.append(
            QaCheck(
                check_id=check_id,
                mandatory=True,
                status=status,
                severity_if_failed=Severity.HIGH,
                scope="program",
            )
        )

    checks.extend(total_checks)
    return QaReport(
        profile=profile,
        scope=scope,
        checks=checks,
        issues=issues,
        required_check_ids=required_ids,
        details={
            "configured_space_count": len(expected_spaces),
            "observed_space_count": len(observed_by_id),
            "external_space_ids": [
                item["logical_id"]
                for item in expected_spaces
                if str(item.get("area_kind", "INTERNAL")).upper() == "EXTERNAL"
            ],
        },
    )


reconcile = reconcile_program
validate_program = reconcile_program


__all__ = ["load_program_config", "reconcile", "reconcile_program", "validate_program"]
