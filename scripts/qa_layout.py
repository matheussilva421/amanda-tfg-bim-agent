"""Run canonical parti and programme QA before Revit writes.

Normalized study geometry is not a cadastral survey or a vertically resolved
building model. Unverified site, enclosure, coverage, visual and Revit checks
remain BLOCKED in the report.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from amanda_agent.design.canonical_pavilion_layout import (
    build_canonical_pavilion_layout,
)
from amanda_agent.design.canonical_qa import run_canonical_checks
from amanda_agent.design.canonical_reference import (
    CanonicalReferenceProfile,
)
from amanda_agent.qa.program import reconcile_program

OUT_JSON = REPOSITORY_ROOT / "docs" / "reports" / "p08-layout-qa.json"
OUT_MD = REPOSITORY_ROOT / "docs" / "reports" / "p08-layout-qa.md"


def _program_room_instances(program: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected: dict[str, dict[str, Any]] = {}
    for sector in program["sectors"]:
        if str(sector.get("area_kind", "")).upper() != "INTERNAL":
            continue
        for space in sector["spaces"]:
            quantity = int(space.get("quantity", 1))
            for index in range(1, quantity + 1):
                logical_id = (
                    space["logical_id"]
                    if quantity == 1
                    else f"{space['logical_id']}#{index}"
                )
                expected[logical_id] = {
                    "logical_id": logical_id,
                    "base_id": space["logical_id"],
                    "sector_id": sector["logical_id"],
                    "area_m2": float(space["target_area_m2"]),
                }
    return expected


def _check(name: str, scope: str, status: str, detail: str, evidence=None) -> dict:
    return {
        "check": name,
        "scope": scope,
        "status": status,
        "detail": detail,
        "evidence": evidence or {},
    }


def _reconcile_program(program: dict[str, Any], layout: Any) -> tuple[str, str]:
    observed_by_base_id: dict[str, dict[str, Any]] = {}
    for room in layout.rooms:
        base_id = room.logical_id.split("#", 1)[0]
        row = observed_by_base_id.setdefault(
            base_id,
            {
                "logical_id": base_id,
                "quantity": 0,
                "area_m2": room.net_area_m2,
                "sector_id": room.sector_id,
            },
        )
        row["quantity"] += 1

    room_program = {
        **program,
        "sectors": [
            sector
            for sector in program["sectors"]
            if str(sector.get("area_kind", "")).upper() == "INTERNAL"
        ],
    }
    try:
        result = asyncio.run(
            reconcile_program(room_program, list(observed_by_base_id.values()))
        )
        result = getattr(result, "result", result)
        status = str(getattr(result, "value", result)).upper()
        passed = "PASS" if status in {"PASS", "PASS_WITH_WARNINGS"} else "FAIL"
        return passed, "reconciliação do programa interno: " + status
    except Exception as exc:  # noqa: BLE001 - report validation errors as evidence
        return "FAIL", f"reconciliação do programa falhou: {type(exc).__name__}: {exc}"


def run_checks(
    program: dict[str, Any], layout: Any, profile: CanonicalReferenceProfile
) -> list[dict]:
    """Evaluate canonical design/program facts and preserve unresolved gates."""
    checks: list[dict] = []
    expected = _program_room_instances(program)
    placed = {room.logical_id: room for room in layout.rooms}
    missing = sorted(set(expected) - set(placed))
    unexpected = sorted(set(placed) - set(expected))
    wrong_area = [
        logical_id
        for logical_id, spec in expected.items()
        if logical_id in placed
        and (
            placed[logical_id].sector_id != spec["sector_id"]
            or abs(float(placed[logical_id].net_area_m2) - spec["area_m2"]) > 1e-6
        )
    ]
    program_rooms_ok = not missing and not unexpected and not wrong_area
    checks.append(
        _check(
            "program.rooms_match_official_program",
            "PROGRAM",
            "PASS" if program_rooms_ok else "FAIL",
            "IDs, setores e áreas internas conferem com o programa oficial"
            if program_rooms_ok
            else "divergências de ambientes: "
            + ", ".join(missing + unexpected + wrong_area),
            {
                "expected": len(expected),
                "placed": len(placed),
                "missing": missing,
                "unexpected": unexpected,
                "wrong_area_or_sector": wrong_area,
            },
        )
    )

    reconciliation_status, reconciliation_detail = _reconcile_program(program, layout)
    checks.append(
        _check(
            "program.reconciliation",
            "PROGRAM",
            reconciliation_status,
            reconciliation_detail,
        )
    )

    baseline = program["baseline"]
    reference_program = profile.data["program"]
    expected_people = int(baseline["person_capacity"])
    people_match = (
        expected_people == 20
        and int(reference_program["people"]) == 20
        and int(layout.parameters.get("people", -1)) == 20
    )
    checks.append(
        _check(
            "program.capacity_is_20",
            "PROGRAM",
            "PASS" if people_match else "FAIL",
            "capacidade oficial de 20 pessoas preservada"
            if people_match
            else "capacidade diverge da base oficial",
            {
                "program": expected_people,
                "canonical_reference": reference_program["people"],
            },
        )
    )

    expected_internal = float(program["totals"]["internal_useful_m2"])
    internal_area = sum(float(room.net_area_m2) for room in layout.rooms)
    internal_ok = abs(internal_area - expected_internal) <= 1e-6
    checks.append(
        _check(
            "program.internal_total_is_626",
            "PROGRAM",
            "PASS" if internal_ok and expected_internal == 626.0 else "FAIL",
            f"área útil interna {internal_area:.2f} m² de 626 m²",
            {
                "measured_net_internal_m2": internal_area,
                "programmed_m2": expected_internal,
            },
        )
    )

    expected_external = float(program["totals"]["external_programmed_m2"])
    external_area = sum(float(item.area_m2) for item in layout.external_spaces)
    external_ok = abs(external_area - expected_external) <= 1e-6
    checks.append(
        _check(
            "program.external_total_is_260",
            "PROGRAM",
            "PASS" if external_ok and expected_external == 260.0 else "FAIL",
            f"área externa programada {external_area:.2f} m² de 260 m²",
            {
                "measured_external_program_m2": external_area,
                "programmed_m2": expected_external,
            },
        )
    )

    checks.extend(
        (
            _check(
                "program.enclosed_estimate",
                "PROGRAM",
                "BLOCKED",
                "estimativa oficial de 783–814 m² ainda não medida em envoltórias verificadas",
                {
                    "official_range_m2": list(
                        program["totals"]["enclosed_estimate_m2"]
                    ),
                    "measured": None,
                },
            ),
            _check(
                "program.covered_estimate",
                "PROGRAM",
                "BLOCKED",
                "estimativa oficial de 850–950 m² ainda não medida em coberturas verificadas",
                {
                    "official_range_m2": list(program["totals"]["covered_estimate_m2"]),
                    "measured": None,
                },
            ),
            _check(
                "site.fit",
                "SITE",
                "BLOCKED",
                "implantação em coordenadas normalizadas; terreno, divisas, norte e topografia não verificados",
                {
                    "coordinate_basis": layout.coordinate_basis,
                    "site_fit_status": layout.site_fit_status,
                },
            ),
        )
    )

    checks.extend(
        {
            "check": "canonical." + item.check_id,
            "scope": "CANONICAL",
            "status": item.status,
            "detail": item.rule + ": " + item.evidence,
            "evidence": {"severity": item.severity},
        }
        for item in run_canonical_checks(layout, profile)
    )

    for name in (
        "model.elements_exist_in_revit",
        "model.rooms_bounded_and_placed",
        "model.sheet_set_published",
        "model.exports_ifc_pdf_dwg",
        "model.cold_reopen_verified",
    ):
        checks.append(
            _check(
                name,
                "MODEL_PENDING",
                "BLOCKED",
                "requer geometria Revit produzida, verificada e reaberta",
            )
        )
    return checks


def main() -> int:
    program = json.loads(
        (REPOSITORY_ROOT / "project" / "requirements" / "program.json").read_text(
            encoding="utf-8"
        )
    )
    profile = CanonicalReferenceProfile.load(REPOSITORY_ROOT)
    layout = build_canonical_pavilion_layout(program, profile)
    checks = run_checks(program, layout, profile)
    failed = [item for item in checks if item["status"] == "FAIL"]
    blocked = [item for item in checks if item["status"] == "BLOCKED"]
    verdict = "FAIL" if failed else "BLOCKED" if blocked else "PASS"
    report = {
        "schema_version": 2,
        "scope": "STUDY",
        "stage": "CANONICAL_PRE_MODEL",
        "layout_content_hash": layout.content_hash,
        "canonical_source_hashes": list(profile.source_hashes),
        "coordinate_basis": layout.coordinate_basis,
        "site_fit_status": layout.site_fit_status,
        "verdict": verdict,
        "checked": len(checks),
        "failed": len(failed),
        "blocked": len(blocked),
        "checks": checks,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# QA do partido canônico — STUDY",
        "",
        f"Veredito: **{verdict}** ({len(checks)} verificações; {len(failed)} falhas; {len(blocked)} bloqueadas)",
        "",
        f"Hash do layout: {layout.content_hash}",
        "",
        "Referências canônicas (SHA-256): " + ", ".join(profile.source_hashes),
        "",
        (
            "A geometria usa coordenadas métricas normalizadas, não levantamento. "
            "Área fechada, área coberta, implantação no terreno, regressões visuais "
            "e produção Revit continuam bloqueadas até haver evidência verificada."
        ),
        "",
        "| verificação | escopo | situação | detalhe |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        "| {} | {} | {} | {} |".format(
            item["check"],
            item["scope"],
            item["status"],
            item["detail"].replace("|", "\\|"),
        )
        for item in checks
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("verdict:", verdict)
    print("checks:", len(checks), "failed:", len(failed), "blocked:", len(blocked))
    for item in failed:
        print("  FAIL", item["check"], "-", item["detail"])
    for item in blocked:
        print("  BLOCKED", item["check"], "-", item["detail"])
    print("json:", OUT_JSON.name, "md:", OUT_MD.name)
    return 0 if verdict == "PASS" else 1 if verdict == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
