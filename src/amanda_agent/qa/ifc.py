"""Local IFC validation using the installed IfcOpenShell runtime."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .models import QaCheck, QaCheckStatus, QaIssue, QaReport, Severity


def _issue(
    code: str,
    message: str,
    *,
    check_id: str,
    severity: Severity,
    mandatory: bool = True,
    evidence: Mapping[str, Any] | None = None,
    missing_input: bool = False,
) -> QaIssue:
    return QaIssue(
        code=code,
        message=message,
        severity=severity,
        scope="ifc",
        mandatory=mandatory,
        evidence=dict(evidence or {}),
        check_id=check_id,
        missing_input=missing_input,
    )


def _base_report(
    checks: list[QaCheck],
    issues: list[QaIssue],
    *,
    profile: str,
    scope: str,
    details: dict[str, Any] | None = None,
) -> QaReport:
    return QaReport(
        profile=profile,
        scope=scope,
        checks=checks,
        issues=issues,
        required_check_ids=[check.check_id for check in checks],
        details=details or {},
    )


def create_minimal_ifc(path: str | Path) -> Path:
    """Create a tiny local IFC4 fixture with one storey/space/wall/door."""

    import ifcopenshell
    import ifcopenshell.api

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    model = ifcopenshell.api.run("project.create_file", version="IFC4")
    project = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcProject", name="QA Fixture"
    )
    ifcopenshell.api.run("unit.assign_unit", model, length={"is_metric": True, "raw": "METERS"})
    site = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcSite", name="site-01"
    )
    building = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcBuilding", name="building-01"
    )
    storey = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcBuildingStorey", name="storey-01"
    )
    ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcSpace", name="space-01"
    )
    ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcWall", name="wall-01"
    )
    ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcDoor", name="door-01"
    )
    ifcopenshell.api.run("aggregate.assign_object", model, products=[site], relating_object=project)
    ifcopenshell.api.run("aggregate.assign_object", model, products=[building], relating_object=site)
    ifcopenshell.api.run("aggregate.assign_object", model, products=[storey], relating_object=building)
    model.write(str(target))
    return target


def _entity_logical_map(model: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for entity_type in ("IfcSpace", "IfcWall", "IfcDoor", "IfcBuildingStorey"):
        for entity in model.by_type(entity_type):
            name = getattr(entity, "Name", None)
            guid = getattr(entity, "GlobalId", None)
            if name and guid:
                result[str(name)] = str(guid)
    return result


def _counts(model: Any) -> dict[str, int]:
    return {
        "storeys": len(model.by_type("IfcBuildingStorey")),
        "spaces": len(model.by_type("IfcSpace")),
        "walls": len(model.by_type("IfcWall")),
        "doors": len(model.by_type("IfcDoor")),
        "openings": len(model.by_type("IfcRelVoidsElement")),
    }


def _unit_name(model: Any) -> str | None:
    projects = model.by_type("IfcProject")
    if not projects:
        return None
    try:
        units = projects[0].Units
    except AttributeError:
        units = None
    if units is not None:
        candidates = units.Units
    else:
        candidates = model.by_type("IfcSIUnit")
    for unit in candidates:
        if str(getattr(unit, "UnitType", "")).upper() == "LENGTHUNIT":
            return str(getattr(unit, "Name", ""))
    return None


def validate_ifc(
    path: str | Path,
    *,
    expected_counts: Mapping[str, int] | None = None,
    logical_id_map: Mapping[str, str] | None = None,
    export_settings: Mapping[str, Any] | None = None,
    observed_metadata: Mapping[str, Any] | None = None,
    expected_metadata: Mapping[str, Any] | None = None,
    splits_merges: list[Mapping[str, Any]] | None = None,
    profile: str = "STUDY",
    scope: str = "ifc",
) -> QaReport:
    """Parse and validate IFC counts, metadata, openings, and logical IDs."""

    target = Path(path)
    if not target.is_file():
        issue = _issue(
            "MISSING_INPUT_IFC",
            f"IFC file does not exist: {target}",
            check_id="ifc.parse",
            severity=Severity.HIGH,
            missing_input=True,
        )
        return _base_report(
            [QaCheck(check_id="ifc.parse", mandatory=True, status=QaCheckStatus.BLOCKED, severity_if_failed=Severity.HIGH, scope="ifc")],
            [issue],
            profile=profile,
            scope=scope,
        )
    if target.stat().st_size == 0:
        issue = _issue(
            "INVALID_IFC_FILE",
            "IFC file is zero bytes",
            check_id="ifc.parse",
            severity=Severity.CRITICAL,
        )
        return _base_report(
            [QaCheck(check_id="ifc.parse", mandatory=True, status=QaCheckStatus.FAIL, severity_if_failed=Severity.CRITICAL, scope="ifc")],
            [issue],
            profile=profile,
            scope=scope,
        )

    with target.open("rb") as stream:
        header = stream.read(32).lstrip()
    if not header.startswith(b"ISO-10303-21;"):
        issue = _issue(
            "INVALID_IFC_FILE",
            "IFC file does not have an ISO-10303-21 exchange header",
            check_id="ifc.parse",
            severity=Severity.CRITICAL,
            evidence={"path": str(target)},
        )
        return _base_report(
            [QaCheck(check_id="ifc.parse", mandatory=True, status=QaCheckStatus.FAIL, severity_if_failed=Severity.CRITICAL, scope="ifc")],
            [issue],
            profile=profile,
            scope=scope,
        )

    try:
        import ifcopenshell

        model = ifcopenshell.open(str(target))
    except (OSError, RuntimeError, ValueError) as exc:
        issue = _issue(
            "INVALID_IFC_FILE",
            f"IFC file could not be parsed: {exc}",
            check_id="ifc.parse",
            severity=Severity.CRITICAL,
            evidence={"path": str(target), "error_type": type(exc).__name__},
        )
        return _base_report(
            [QaCheck(check_id="ifc.parse", mandatory=True, status=QaCheckStatus.FAIL, severity_if_failed=Severity.CRITICAL, scope="ifc")],
            [issue],
            profile=profile,
            scope=scope,
        )

    actual_counts = _counts(model)
    derived_map = _entity_logical_map(model)
    issues: list[QaIssue] = []
    checks: list[QaCheck] = [
        QaCheck(check_id="ifc.parse", mandatory=True, status=QaCheckStatus.PASS, severity_if_failed=Severity.CRITICAL, scope="ifc")
    ]
    if expected_counts:
        mismatches = {
            key: {"expected": int(expected), "observed": actual_counts.get(key, 0)}
            for key, expected in expected_counts.items()
            if int(expected) != actual_counts.get(key, 0)
        }
        if mismatches:
            issues.append(
                _issue(
                    "IFC_COUNT_MISMATCH",
                    "IFC core entity counts differ from expected export evidence",
                    check_id="ifc.counts",
                    severity=Severity.HIGH,
                    evidence={"mismatches": mismatches},
                )
            )
        checks.append(QaCheck(check_id="ifc.counts", mandatory=True, status=QaCheckStatus.FAIL if mismatches else QaCheckStatus.PASS, severity_if_failed=Severity.HIGH, scope="ifc"))

    if logical_id_map:
        guids = {str(entity.GlobalId) for entity in model if getattr(entity, "GlobalId", None)}
        mapping_errors = {
            logical_id: guid
            for logical_id, guid in logical_id_map.items()
            if str(guid) not in guids
            or (
                str(logical_id) in derived_map
                and derived_map[str(logical_id)] != str(guid)
            )
        }
        if mapping_errors:
            issues.append(
                _issue(
                    "LOGICAL_ID_MAPPING_MISMATCH",
                    "one or more managed logical IDs do not map to IFC GUIDs",
                    check_id="ifc.logical_id_mapping",
                    severity=Severity.HIGH,
                    evidence={"mapping_errors": mapping_errors},
                )
            )
        checks.append(QaCheck(check_id="ifc.logical_id_mapping", mandatory=True, status=QaCheckStatus.FAIL if mapping_errors else QaCheckStatus.PASS, severity_if_failed=Severity.HIGH, scope="ifc"))
    elif splits_merges:
        issues.append(
            _issue(
                "EXPLICIT_MAPPING_REQUIRED",
                "IFC splits/merges require an explicit logical-ID to GUID mapping",
                check_id="ifc.logical_id_mapping",
                severity=Severity.HIGH,
                evidence={"splits_merges": list(splits_merges)},
                missing_input=True,
            )
        )
        checks.append(QaCheck(check_id="ifc.logical_id_mapping", mandatory=True, status=QaCheckStatus.BLOCKED, severity_if_failed=Severity.HIGH, scope="ifc"))

    expected_meta = dict(expected_metadata or export_settings or {})
    observed_meta = dict(observed_metadata or {})
    if "units" in expected_meta and "units" not in observed_meta:
        observed_meta["units"] = _unit_name(model)
    metadata_mismatches = {
        key: {"expected": value, "observed": observed_meta.get(key)}
        for key, value in expected_meta.items()
        if observed_meta.get(key) != value
    }
    if expected_meta:
        if metadata_mismatches:
            issues.append(
                _issue(
                    "IFC_EXPORT_METADATA_MISMATCH",
                    "IFC units, transforms, georeference, extents, or export settings differ",
                    check_id="ifc.export_metadata",
                    severity=Severity.HIGH,
                    evidence={"mismatches": metadata_mismatches},
                )
            )
        checks.append(QaCheck(check_id="ifc.export_metadata", mandatory=True, status=QaCheckStatus.FAIL if metadata_mismatches else QaCheckStatus.PASS, severity_if_failed=Severity.HIGH, scope="ifc"))

    details = {
        "path": str(target),
        "size_bytes": target.stat().st_size,
        "counts": {key: actual_counts[key] for key in ("storeys", "spaces", "walls", "doors")},
        "all_counts": actual_counts,
        "logical_id_map": derived_map,
        "units": _unit_name(model),
    }
    return _base_report(checks, issues, profile=profile, scope=scope, details=details)


validate = validate_ifc
ifc_qa = validate_ifc


__all__ = ["create_minimal_ifc", "ifc_qa", "validate", "validate_ifc"]
