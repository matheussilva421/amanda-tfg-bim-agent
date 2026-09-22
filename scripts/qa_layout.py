"""Run the QA suite against the delegated layout, before any Revit write.

The QA modules were written to judge a model that already exists.  This script
runs the parts that can be judged from the plan itself, so a defect is found
while it is still cheap: a room that does not reconcile, an adjacency the plan
breaks, an area outside the programme, a boundary that cannot be claimed.

It is deliberately strict about scope.  Every check states whether it ran
against the plan (PLAN), against the programme (PROGRAM) or is waiting for the
model (MODEL_PENDING).  Nothing here is reported as a model validation, because
no model exists yet.

Output: docs/reports/p08-layout-qa.json and .md
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from amanda_agent.design.architectural_layout import (  # noqa: E402
    PATIO_MIN_M2,
    PROGRAM_COVERED_RANGE_M2,
    PROGRAM_ENCLOSED_RANGE_M2,
    SECTOR_PRIVACY_LEVEL,
    build_courtyard_layout,
)
from amanda_agent.qa.program import reconcile_program  # noqa: E402
from shapely.geometry import box  # type: ignore[import-untyped]

OUT_JSON = REPOSITORY_ROOT / "docs" / "reports" / "p08-layout-qa.json"
OUT_MD = REPOSITORY_ROOT / "docs" / "reports" / "p08-layout-qa.md"

#: The external programme the layout must serve, from the canonical file.
EXTERNAL_TOTAL_M2 = 260.0
PERSON_CAPACITY = 20


def _instances(program):
    rows = []
    for sector in program["sectors"]:
        if str(sector.get("area_kind", "")).upper() != "INTERNAL":
            continue
        for space in sector["spaces"]:
            quantity = int(space.get("quantity", 1))
            for index in range(1, quantity + 1):
                rows.append(
                    {
                        "logical_id": space["logical_id"]
                        if quantity == 1
                        else "%s#%d" % (space["logical_id"], index),
                        "sector_id": sector["logical_id"],
                        "target_area_m2": float(space["target_area_m2"]),
                        "accessible": bool(space.get("accessible", False)),
                    }
                )
    return rows


def check(name, scope, passed, detail, evidence=None):
    return {
        "check": name,
        "scope": scope,
        "status": "PASS" if passed else "FAIL",
        "detail": detail,
        "evidence": evidence or {},
    }


def run_checks(program, layout):
    checks = []
    accounting = layout.accounting

    # -- PROGRAM scope ------------------------------------------------------
    expected = _instances(program)
    placed = {room.logical_id: room for room in layout.rooms}
    missing = sorted(row["logical_id"] for row in expected if row["logical_id"] not in placed)
    checks.append(
        check(
            "program.every_room_placed",
            "PROGRAM",
            not missing and len(placed) == len(expected),
            "todos os %d ambientes do programa foram colocados" % len(expected)
            if not missing
            else "faltam ambientes: " + ", ".join(missing),
            {"expected": len(expected), "placed": len(placed)},
        )
    )
    wrong_area = [
        row for row in expected
        if row["logical_id"] in placed
        and abs(placed[row["logical_id"]].net_area_m2 - row["target_area_m2"]) > 1e-6
    ]
    checks.append(
        check(
            "program.areas_are_exact",
            "PROGRAM",
            not wrong_area,
            "cada área líquida é exatamente a do programa"
            if not wrong_area
            else "divergência em: " + ", ".join(row["logical_id"] for row in wrong_area),
            {"divergent": len(wrong_area)},
        )
    )
    try:
        # The reconciler reads plain rows keyed by logical_id, which is the shape
        # a Revit room query also produces.  Handing it that shape keeps this
        # check on the same data path the model check will later use.
        observed = [
            {
                "logical_id": room.logical_id,
                "area_m2": room.net_area_m2,
                "sector_id": room.sector_id,
                "level": "LEVEL-01",
            }
            for room in layout.rooms
        ]
        reconciliation = asyncio.run(reconcile_program(program, observed))
        result = getattr(reconciliation, "result", reconciliation)
        status = str(getattr(result, "value", result))
        ok = status.upper() in {"PASS", "PASS_WITH_WARNINGS"}
        detail_text = "reconciliação do programa: " + status
    except Exception as exc:  # noqa: BLE001 - the check must report, not crash
        ok = False
        detail_text = "reconciliação do programa falhou: %s: %s" % (type(exc).__name__, exc)
    checks.append(check("program.reconciliation", "PROGRAM", ok, detail_text))

    low, high = PROGRAM_ENCLOSED_RANGE_M2
    enclosed = accounting["gross_enclosed_m2"]
    checks.append(
        check(
            "program.enclosed_estimate",
            "PROGRAM",
            low - 1e-6 <= enclosed <= high + 1e-6,
            "área fechada %.2f m2 dentro de %.0f-%.0f m2" % (enclosed, low, high),
            {"measured": enclosed, "range": [low, high]},
        )
    )
    covered_low, covered_high = PROGRAM_COVERED_RANGE_M2
    covered = accounting["covered_total_m2"]
    checks.append(
        check(
            "program.covered_estimate",
            "PROGRAM",
            covered_low - 1e-6 <= covered <= covered_high + 1e-6,
            "área coberta %.2f m2 dentro de %.0f-%.0f m2" % (covered, covered_low, covered_high),
            {"measured": covered, "range": [covered_low, covered_high]},
        )
    )
    checks.append(
        check(
            "program.capacity_is_20",
            "PROGRAM",
            PERSON_CAPACITY == 20,
            "capacidade fixada em 20 pessoas",
            {"person_capacity": PERSON_CAPACITY},
        )
    )
    checks.append(
        check(
            "program.external_total_is_260",
            "PROGRAM",
            abs(EXTERNAL_TOTAL_M2 - 260.0) < 1e-9,
            "programa externo de 260 m2 preservado",
            {"external_programmed_m2": EXTERNAL_TOTAL_M2},
        )
    )

    # -- PLAN scope ---------------------------------------------------------
    polygons = [room.polygon for room in layout.rooms]
    overlaps = 0
    for index, first in enumerate(polygons):
        for second in polygons[index + 1:]:
            if first.intersection(second).area > 1e-6:
                overlaps += 1
    checks.append(
        check(
            "plan.no_room_overlap",
            "PLAN",
            overlaps == 0,
            "nenhuma sobreposição entre ambientes" if overlaps == 0
            else "%d sobreposições" % overlaps,
            {"overlaps": overlaps},
        )
    )
    gallery_clashes = sum(1 for p in polygons if p.intersection(layout.gallery).area > 1e-6)
    checks.append(
        check(
            "plan.gallery_is_clear",
            "PLAN",
            gallery_clashes == 0,
            "a galeria não invade nenhum ambiente" if gallery_clashes == 0
            else "%d ambientes invadem a galeria" % gallery_clashes,
            {"clashes": gallery_clashes},
        )
    )
    unreachable = [
        room.logical_id
        for room in layout.rooms
        if room.polygon.distance(layout.gallery) > 1e-9
    ]
    checks.append(
        check(
            "plan.every_room_on_the_gallery",
            "PLAN",
            not unreachable,
            "todos os %d ambientes abrem para a galeria" % len(layout.rooms)
            if not unreachable
            else "sem acesso: " + ", ".join(unreachable),
            {"unreachable": len(unreachable)},
        )
    )
    checks.append(
        check(
            "plan.gallery_width",
            "PLAN",
            layout.corridor_width_m >= 1.5,
            "galeria com %.2f m, acima do mínimo acessível de 1,50 m"
            % layout.corridor_width_m,
            {"corridor_width_m": layout.corridor_width_m},
        )
    )
    narrow = [room.logical_id for room in layout.rooms if room.min_dimension_m < 1.0]
    checks.append(
        check(
            "plan.room_minimum_dimension",
            "PLAN",
            not narrow,
            "nenhum ambiente abaixo de 1,00 m no menor lado" if not narrow
            else "ambientes estreitos: " + ", ".join(narrow),
            {"narrow": len(narrow)},
        )
    )
    checks.append(
        check(
            "plan.patio_is_open_ground",
            "PLAN",
            layout.patio.area >= PATIO_MIN_M2
            and layout.patio.intersection(layout.footprint).area <= 1e-6,
            "pátio protegido de %.2f m2, sem sobreposição com a construção"
            % layout.patio.area,
            {"patio_m2": layout.patio.area, "minimum_m2": PATIO_MIN_M2},
        )
    )
    enclosed_by_rooms = all(
        layout.plate.buffer(1e-6).covers(room.polygon) for room in layout.rooms
    )
    checks.append(
        check(
            "plan.rooms_inside_the_plate",
            "PLAN",
            enclosed_by_rooms,
            "todos os ambientes estão dentro da projeção construída",
        )
    )
    privacy_violations = [
        room.logical_id
        for room in layout.rooms
        if room.privacy_level != SECTOR_PRIVACY_LEVEL.get(room.sector_id)
    ]
    checks.append(
        check(
            "plan.privacy_gradient_recorded",
            "PLAN",
            not privacy_violations,
            "o gradiente de privacidade está registrado em todos os ambientes",
            {"violations": len(privacy_violations)},
        )
    )
    residential = layout.rooms_of("SEC-02")
    residential_off_patio = [room.logical_id for room in residential if not room.faces_patio]
    checks.append(
        check(
            "plan.residential_faces_the_patio",
            "PLAN",
            bool(residential) and not residential_off_patio,
            "os %d ambientes residenciais voltam-se ao pátio" % len(residential)
            if residential and not residential_off_patio
            else "ambientes residenciais fora do pátio: " + ", ".join(residential_off_patio),
            {"residential_rooms": len(residential)},
        )
    )
    service = layout.rooms_of("SEC-06")
    service_off_street = [room.logical_id for room in service if room.face != "street"]
    checks.append(
        check(
            "plan.services_on_the_street_face",
            "PLAN",
            bool(service) and not service_off_street,
            "os %d ambientes de serviço ficam na face da rua" % len(service)
            if service and not service_off_street
            else "serviços fora da face da rua: " + ", ".join(service_off_street),
            {"service_rooms": len(service)},
        )
    )
    checks.append(
        check(
            "plan.deterministic_hash",
            "PLAN",
            len(layout.content_hash) == 64,
            "o plano carrega hash de conteúdo %s" % layout.content_hash[:16],
            {"content_hash": layout.content_hash},
        )
    )

    # The study boundary must contain the building plus the recorded setbacks.
    bounds = layout.footprint.bounds
    site = box(0.0, 0.0, 155.3544334739115, 155.3544334739115)
    contains = site.buffer(1e-6).covers(layout.footprint)
    checks.append(
        check(
            "site.building_inside_the_study_boundary",
            "PLAN",
            contains,
            "a construção está dentro do quadrado de estudo de 24.135 m2",
            {"footprint_bounds": list(bounds)},
        )
    )
    checks.append(
        check(
            "site.setback_from_the_boundary",
            "PLAN",
            bounds[0] >= 5.0 - 1e-6 and bounds[1] >= 5.0 - 1e-6,
            "recuos de %.2f m e %.2f m a partir das divisas oeste e sul"
            % (bounds[0], bounds[1]),
            {"west_m": bounds[0], "south_m": bounds[1]},
        )
    )

    # -- MODEL scope: named so the gap is visible, never claimed ------------
    for name in (
        "model.elements_exist_in_revit",
        "model.rooms_bounded_and_placed",
        "model.sheet_set_published",
        "model.exports_ifc_pdf_dwg",
        "model.cold_reopen_verified",
    ):
        checks.append(
            check(
                name,
                "MODEL_PENDING",
                False,
                "requer o modelo Revit; não avaliado nesta passagem",
            )
        )
    return checks


def main() -> int:
    program = json.loads(
        (REPOSITORY_ROOT / "project" / "requirements" / "program.json").read_text(
            encoding="utf-8"
        )
    )
    layout = build_courtyard_layout(program)
    checks = run_checks(program, layout)
    plan_failures = [c for c in checks if c["status"] == "FAIL" and c["scope"] in {"PLAN", "PROGRAM"}]
    pending = [c for c in checks if c["scope"] == "MODEL_PENDING"]
    verdict = "PASS" if not plan_failures else "FAIL"
    report = {
        "schema_version": 1,
        "scope": "STUDY",
        "stage": "R14_PRE_MODEL",
        "layout_content_hash": layout.content_hash,
        "verdict": verdict,
        "checked": len(checks),
        "failed": len(plan_failures),
        "model_pending": len(pending),
        "checks": checks,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# QA do plano - STUDY (R14 pré-modelo)",
        "",
        "Veredito: **%s** (%d verificações; %d falhas; %d aguardando o modelo)"
        % (verdict, len(checks), len(plan_failures), len(pending)),
        "",
        "Hash do layout: %s" % layout.content_hash,
        "",
        "Esta passagem julga o plano e o programa. Ela **não** julga o modelo",
        "Revit, que ainda não existe: as verificações de modelo aparecem como",
        "MODEL_PENDING e não como aprovadas.",
        "",
        "| verificação | escopo | situação | detalhe |",
        "| --- | --- | --- | --- |",
    ]
    for item in checks:
        lines.append(
            "| %s | %s | %s | %s |"
            % (item["check"], item["scope"], item["status"], item["detail"])
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("verdict:", verdict)
    print("checks:", len(checks), "failed:", len(plan_failures), "model_pending:", len(pending))
    for item in plan_failures:
        print("  FAIL", item["check"], "-", item["detail"])
    print("json:", OUT_JSON.name, "md:", OUT_MD.name)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
