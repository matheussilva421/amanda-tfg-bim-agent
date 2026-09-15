"""Geometric and identity QA over independent Revit query evidence."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from .models import QaCheck, QaCheckStatus, QaIssue, QaReport, Severity


def _rows(evidence: Any) -> tuple[list[dict[str, Any]], Mapping[str, Any]]:
    if isinstance(evidence, Mapping):
        raw = evidence.get("elements", evidence.get("items", []))
        rows = [dict(row) for row in raw or [] if isinstance(row, Mapping)]
        return rows, evidence
    return [dict(row) for row in evidence or [] if isinstance(row, Mapping)], {}


def _severity(value: Any, default: Severity) -> Severity:
    if value is None:
        return default
    try:
        return value if isinstance(value, Severity) else Severity(str(value).upper())
    except ValueError:
        return default


def _stage_key(stage: Any) -> str:
    value = getattr(stage, "value", stage)
    text = str(value or "").upper()
    if text.startswith("R") and text[1:2].isdigit():
        return text[:3]
    aliases = {
        "PROJECT_INITIALIZED": "R01",
        "SITE": "R02",
        "LEVELS_AND_REFERENCES": "R03",
        "MASSING": "R04",
        "DOCUMENTATION": "R13",
        "QA": "R14",
        "RELEASE_CANDIDATE": "R15",
        "GOLDEN": "R16",
    }
    return aliases.get(text, text)


def _default_level_severity(stage: Any) -> Severity:
    key = _stage_key(stage)
    try:
        number = int(key[1:]) if key.startswith("R") else 0
    except ValueError:
        number = 0
    return Severity.HIGH if number >= 13 else Severity.MEDIUM


def _issue(
    code: str,
    message: str,
    *,
    check_id: str,
    severity: Severity,
    evidence: Mapping[str, Any],
) -> QaIssue:
    return QaIssue(
        code=code,
        message=message,
        severity=severity,
        scope="model",
        mandatory=True,
        evidence=dict(evidence),
        check_id=check_id,
    )


def qa_model(
    evidence: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    *,
    config: Mapping[str, Any] | None = None,
    stage: Any = None,
    profile: str = "STUDY",
    scope: str = "model",
) -> QaReport:
    """Validate model state obtained by query, never a write response."""

    settings = dict(config or {})
    rows, container = _rows(evidence)
    managed = [row for row in rows if row.get("managed", True)]
    issues: list[QaIssue] = []
    checks: list[QaCheck] = []
    required: list[str] = []

    def add_check(check_id: str, failed: bool, status: QaCheckStatus | None = None) -> None:
        required.append(check_id)
        checks.append(
            QaCheck(
                check_id=check_id,
                mandatory=True,
                status=status or (QaCheckStatus.FAIL if failed else QaCheckStatus.PASS),
                severity_if_failed=Severity.HIGH,
                scope="model",
            )
        )

    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in managed:
        if row.get("logical_id"):
            by_id[str(row["logical_id"])].append(row)
    duplicate_ids = sorted(key for key, values in by_id.items() if len(values) > 1)
    for logical_id in duplicate_ids:
        issues.append(
            _issue(
                "DUPLICATE_LOGICAL_ID",
                f"managed logical_id {logical_id!r} occurs more than once",
                check_id="model.unique_ids",
                severity=Severity.CRITICAL,
                evidence={"logical_id": logical_id, "count": len(by_id[logical_id])},
            )
        )
    add_check("model.unique_ids", bool(duplicate_ids))

    host_failures = []
    for row in managed:
        hosted = bool(row.get("hosted", row.get("host_required", "host_id" in row)))
        host_id = row.get("host_id", row.get("host_logical_id"))
        host_exists = row.get("host_exists", bool(host_id))
        if hosted and (not host_id or host_exists is False):
            host_failures.append(row)
            issues.append(
                _issue(
                    "HOST_MISSING",
                    f"hosted element {row.get('logical_id', '<unknown>')!r} has no verified host",
                    check_id="model.hosts",
                    severity=_severity(row.get("host_missing_severity"), Severity.HIGH),
                    evidence={"element": row.get("logical_id"), "host_id": host_id},
                )
            )
    add_check("model.hosts", bool(host_failures))

    room_categories = {
        str(value).casefold()
        for value in settings.get("room_categories", ("room", "rooms"))
    }
    room_failures: dict[str, list[dict[str, Any]]] = {
        "positioned": [],
        "enclosed": [],
        "redundant": [],
    }
    for row in managed:
        is_room = bool(row.get("is_room")) or str(row.get("category", "")).casefold() in room_categories
        if not is_room:
            continue
        if row.get("positioned") is False or row.get("placed") is False:
            room_failures["positioned"].append(row)
            issues.append(
                _issue(
                    "ROOM_NOT_POSITIONED",
                    f"managed room {row.get('logical_id')!r} is not positioned",
                    check_id="model.rooms.positioned",
                    severity=Severity.HIGH,
                    evidence={"logical_id": row.get("logical_id")},
                )
            )
        if row.get("enclosed") is False or row.get("closed") is False:
            room_failures["enclosed"].append(row)
            issues.append(
                _issue(
                    "ROOM_NOT_ENCLOSED",
                    f"managed room {row.get('logical_id')!r} is not enclosed",
                    check_id="model.rooms.enclosed",
                    severity=Severity.HIGH,
                    evidence={"logical_id": row.get("logical_id")},
                )
            )
        if row.get("redundant") is True or row.get("is_redundant") is True:
            room_failures["redundant"].append(row)
            issues.append(
                _issue(
                    "ROOM_REDUNDANT",
                    f"managed room {row.get('logical_id')!r} is redundant",
                    check_id="model.rooms.redundant",
                    severity=Severity.HIGH,
                    evidence={"logical_id": row.get("logical_id")},
                )
            )
    add_check("model.rooms.positioned", bool(room_failures["positioned"]))
    add_check("model.rooms.enclosed", bool(room_failures["enclosed"]))
    add_check("model.rooms.redundant", bool(room_failures["redundant"]))

    outside_failures = []
    if settings.get("prohibit_outside_site", False):
        for row in managed:
            if row.get("within_site") is False or row.get("outside_site") is True:
                outside_failures.append(row)
                issues.append(
                    _issue(
                        "OUTSIDE_SITE",
                        f"managed element {row.get('logical_id')!r} is outside the permitted site",
                        check_id="model.site_bounds",
                        severity=Severity.HIGH,
                        evidence={"logical_id": row.get("logical_id")},
                    )
                )
    add_check("model.site_bounds", bool(outside_failures))

    level_failures = []
    configured_levels = settings.get("expected_levels", {})
    stage_severities = settings.get("level_severity_by_stage", {})
    level_severity = _severity(
        stage_severities.get(_stage_key(stage)), _default_level_severity(stage)
    )
    for row in managed:
        expected = row.get("expected_level")
        if expected is None and row.get("logical_id") in configured_levels:
            expected = configured_levels[row["logical_id"]]
        if expected is not None and row.get("level") != expected:
            level_failures.append(row)
            issues.append(
                _issue(
                    "UNEXPECTED_LEVEL",
                    f"element {row.get('logical_id')!r} is on an unexpected level",
                    check_id="model.levels",
                    severity=level_severity,
                    evidence={
                        "logical_id": row.get("logical_id"),
                        "expected": expected,
                        "observed": row.get("level"),
                        "stage": _stage_key(stage),
                    },
                )
            )
    add_check("model.levels", bool(level_failures))

    counts = container.get("counts", {}) if isinstance(container, Mapping) else {}
    before = counts.get("before", container.get("count_before"))
    after = counts.get("after", container.get("count_after"))
    if before is not None and after is not None:
        before_value, after_value = int(before), int(after)
        difference = abs(after_value - before_value)
        ratio = difference / max(abs(before_value), 1)
        absolute_limit = int(settings.get("massive_delta_absolute", 25))
        ratio_limit = float(settings.get("massive_delta_ratio", 0.5))
        massive = difference >= absolute_limit or ratio >= ratio_limit
        if massive:
            issues.append(
                _issue(
                    "MASSIVE_COUNT_DELTA",
                    f"element count changed from {before_value} to {after_value} unexpectedly",
                    check_id="model.count_delta",
                    severity=Severity.CRITICAL,
                    evidence={
                        "before": before_value,
                        "after": after_value,
                        "difference": difference,
                        "ratio": ratio,
                    },
                )
            )
        add_check("model.count_delta", massive)
    else:
        add_check("model.count_delta", False)

    return QaReport(
        profile=profile,
        scope=scope,
        checks=checks,
        issues=issues,
        required_check_ids=required,
        details={"managed_count": len(managed), "duplicate_logical_ids": duplicate_ids},
    )


validate_model = qa_model
model_qa = qa_model


__all__ = ["model_qa", "qa_model", "validate_model"]
