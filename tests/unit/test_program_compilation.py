"""The adopted program of needs is compiled from the source, not remembered."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from amanda_agent.requirements.program import (
    ADOPTED_PERSON_CAPACITY,
    PROGRAM_SOURCE_SHA256,
    UNSELECTED_PERSON_CAPACITY,
    build_program,
    program_summary_markdown,
    reconcile,
    write_program,
    write_program_summary,
)


def test_adopted_baseline_keeps_the_pdf_hash_from_the_design():
    assert PROGRAM_SOURCE_SHA256 == (
        "11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17"
    )
    assert ADOPTED_PERSON_CAPACITY == 20
    assert UNSELECTED_PERSON_CAPACITY == 42


def test_sector_subtotals_match_the_source_table():
    program = build_program()
    subtotals = {sector.name: sector.subtotal_m2 for sector in program.sectors}

    assert subtotals == {
        "Acolhimento e chegada": 53.0,
        "Setor residencial": 209.0,
        "Setor infantil": 52.0,
        "Atendimento tecnico": 80.0,
        "Comunitario e capacitacao": 81.0,
        "Administracao e servicos": 151.0,
        "Areas externas": 260.0,
    }


def test_every_sector_reconciles_against_its_own_rows():
    for sector in build_program().sectors:
        assert sector.computed_subtotal_m2 == pytest.approx(sector.subtotal_m2)


def test_global_totals_reconcile_to_the_source_summary():
    report = reconcile()

    assert report["ok"] is True
    assert report["mismatches"] == []
    assert report["internal_useful_m2"] == pytest.approx(626.0)
    assert report["external_programmed_m2"] == pytest.approx(260.0)


def test_accessible_bedroom_and_bathroom_are_present_requirements():
    names = {
        space.name: space
        for sector in build_program().sectors
        for space in sector.spaces
    }

    assert names["Quarto acessivel"].accessible is True
    assert names["Quarto acessivel"].quantity == 1
    assert names["Quarto acessivel"].target_area_m2 == pytest.approx(16.0)
    assert names["Banheiro acessivel"].accessible is True
    assert names["Sanitario acessivel"].accessible is True


def test_unit_areas_are_per_unit_and_totals_use_quantity_times_unit():
    program = build_program()
    bathrooms = next(
        space
        for sector in program.sectors
        for space in sector.spaces
        if space.logical_id == "REQ-02-06"
    )

    assert bathrooms.quantity == 5
    assert bathrooms.target_area_m2 == pytest.approx(3.5)
    assert bathrooms.total_area_m2 == pytest.approx(17.5)


def test_logical_ids_are_unique_across_the_whole_program():
    identifiers = [
        space.logical_id
        for sector in build_program().sectors
        for space in sector.spaces
    ]

    assert len(identifiers) == len(set(identifiers))
    assert len(identifiers) == 49, "5 + 10 + 4 + 6 + 4 + 15 + 5 source rows"


def test_compiled_program_is_written_as_canonical_json(tmp_path: Path):
    written = write_program(tmp_path)

    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["baseline"]["source_id"] == "SRC-PROGRAM-001"
    assert payload["baseline"]["person_capacity"] == 20
    assert payload["baseline"]["adoption_status"] == "ACCEPTED"
    assert payload["baseline"]["selection_authority"] == "AGENT_DELEGATED"
    assert payload["totals"]["internal_useful_m2"] == 626.0
    assert payload["totals"]["external_programmed_m2"] == 260.0
    assert payload["totals"]["enclosed_estimate_m2"] == [783.0, 814.0]
    assert payload["totals"]["covered_estimate_m2"] == [850.0, 950.0]
    assert payload["unselected_hypotheses"][0]["person_capacity"] == 42
    assert payload["unselected_hypotheses"][0]["adoption_status"] == "REJECTED"
    assert payload["reconciliation"]["ok"] is True


def test_summary_is_rendered_from_the_canonical_objects(tmp_path: Path):
    written = write_program_summary(tmp_path)
    text = written.read_text(encoding="utf-8")

    assert "626" in text
    assert "260" in text
    assert "20" in text
    assert "SRC-PROGRAM-001" in text
    assert "REJECTED" in text
    assert "42" in text


def test_summary_matches_the_canonical_payload(tmp_path: Path):
    payload = json.loads(write_program(tmp_path).read_text(encoding="utf-8"))
    summary = program_summary_markdown()

    for sector in payload["sectors"]:
        assert sector["name"] in summary
    assert f'{payload["totals"]["internal_useful_m2"]:g}' in summary
