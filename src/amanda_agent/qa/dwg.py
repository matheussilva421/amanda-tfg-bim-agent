"""DWG export sanity validation without introducing a proprietary parser."""

from __future__ import annotations

from pathlib import Path

from .models import QaCheck, QaCheckStatus, QaIssue, QaReport, Severity


def validate_dwg(
    path: str | Path,
    *,
    profile: str = "STUDY",
    scope: str = "dwg",
) -> QaReport:
    """Check path, size, and the documented DWG header.

    No compatible local parser is registered in this repository, so accepted
    files carry an explicit ``LIMITED_DWG_VALIDATION`` finding.
    """

    target = Path(path)
    check_id = "dwg.signature"
    if not target.is_file():
        return QaReport(
            profile=profile,
            scope=scope,
            checks=[QaCheck(check_id=check_id, mandatory=True, status=QaCheckStatus.BLOCKED, severity_if_failed=Severity.HIGH, scope="dwg")],
            issues=[QaIssue(
                code="MISSING_INPUT_DWG",
                message=f"DWG file does not exist: {target}",
                severity=Severity.HIGH,
                scope="dwg",
                mandatory=True,
                evidence={"path": str(target)},
                check_id=check_id,
                missing_input=True,
            )],
            required_check_ids=[check_id],
        )
    size = target.stat().st_size
    with target.open("rb") as stream:
        signature = stream.read(6).decode("ascii", errors="replace")
    if size == 0:
        valid = False
        code = "INVALID_DWG_SIZE"
        message = "DWG file is zero bytes"
    elif not signature.startswith("AC10") or len(signature) != 6 or not signature[4:].isdigit():
        valid = False
        code = "INVALID_DWG_SIGNATURE"
        message = "DWG file does not have an AC10xx header signature"
    else:
        valid = True
        code = "LIMITED_DWG_VALIDATION"
        message = "only DWG signature and nonzero size were verified; no local parser is registered"

    checks = [
        QaCheck(
            check_id=check_id,
            mandatory=True,
            status=QaCheckStatus.PASS if valid else QaCheckStatus.FAIL,
            severity_if_failed=Severity.HIGH,
            scope="dwg",
        )
    ]
    issue = QaIssue(
        code=code,
        message=message,
        severity=Severity.LOW if valid else Severity.CRITICAL,
        scope="dwg",
        mandatory=not valid,
        evidence={"path": str(target), "size_bytes": size, "signature": signature},
        check_id=check_id,
    )
    return QaReport(
        profile=profile,
        scope=scope,
        checks=checks,
        issues=[issue],
        required_check_ids=[check_id],
        details={
            "path": str(target),
            "size_bytes": size,
            "signature": signature,
            "validation": "LIMITED_DWG_VALIDATION" if valid else "REJECTED",
        },
    )


validate = validate_dwg
dwg_qa = validate_dwg


__all__ = ["dwg_qa", "validate", "validate_dwg"]
