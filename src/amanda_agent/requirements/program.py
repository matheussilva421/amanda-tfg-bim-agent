"""Canonical compilation of the adopted program of needs.

The source is ``programa_necessidades.pdf`` at the version whose SHA-256 the
design section 1.1 records. Quantities and unit areas below are transcriptions
of that document: the module never invents a value, and the spreadsheet's
42-person hypothesis stays recorded as an unselected alternative.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

PROGRAM_SOURCE_ID = "SRC-PROGRAM-001"
PROGRAM_SOURCE_FILENAME = "programa_necessidades.pdf"
PROGRAM_SOURCE_SHA256 = (
    "11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17"
)
ADOPTED_PERSON_CAPACITY = 20
UNSELECTED_PERSON_CAPACITY = 42

INTERNAL_USEFUL_M2 = 626.0
EXTERNAL_PROGRAMMED_M2 = 260.0
ENCLOSED_ESTIMATE_M2 = (783.0, 814.0)
COVERED_ESTIMATE_M2 = (850.0, 950.0)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProgramSpace(_Model):
    """One source row, kept with its per-unit area and quantity."""

    logical_id: str
    name: str
    quantity: int = Field(ge=1)
    target_area_m2: float = Field(gt=0)
    area_kind: str
    accessible: bool | None = None
    beds_per_unit: int | None = Field(default=None, ge=1)
    source_page: int

    @property
    def total_area_m2(self) -> float:
        return self.quantity * self.target_area_m2


class ProgramSector(_Model):
    logical_id: str
    name: str
    area_kind: str
    subtotal_m2: float = Field(gt=0)
    spaces: list[ProgramSpace] = Field(min_length=1)

    @property
    def computed_subtotal_m2(self) -> float:
        return sum(space.total_area_m2 for space in self.spaces)


class ProgramBaseline(_Model):
    source_id: str
    source_filename: str
    source_sha256: str
    source_pages: list[int]
    person_capacity: int
    adoption_status: str
    selection_authority: str
    selection_date: str
    evidence: str


class UnselectedHypothesis(_Model):
    source_id: str
    source_locator: str
    person_capacity: int
    adoption_status: str
    reason_not_adopted: str


class AdoptedProgram(_Model):
    baseline: ProgramBaseline
    sectors: list[ProgramSector] = Field(min_length=1)
    unselected_hypotheses: list[UnselectedHypothesis]


def _space(
    logical_id: str,
    name: str,
    quantity: int,
    unit_area: float,
    area_kind: str,
    page: int,
    *,
    accessible: bool | None = None,
    beds_per_unit: int | None = None,
) -> ProgramSpace:
    return ProgramSpace(
        logical_id=logical_id,
        name=name,
        quantity=quantity,
        target_area_m2=unit_area,
        area_kind=area_kind,
        accessible=accessible,
        beds_per_unit=beds_per_unit,
        source_page=page,
    )


def build_program() -> AdoptedProgram:
    """Compile the adopted baseline transcriptions into canonical objects."""
    internal = "INTERNAL"
    external = "EXTERNAL"
    sectors = [
        ProgramSector(
            logical_id="SEC-01",
            name="Acolhimento e chegada",
            area_kind=internal,
            subtotal_m2=53.0,
            spaces=[
                _space("REQ-01-01", "Recepcao", 1, 10.0, internal, 1),
                _space("REQ-01-02", "Espera protegida", 1, 15.0, internal, 1),
                _space("REQ-01-03", "Acolhimento e triagem", 1, 12.0, internal, 1),
                _space("REQ-01-04", "Registro e entrevista inicial", 1, 10.0, internal, 1),
                _space("REQ-01-05", "Controle de acesso", 1, 6.0, internal, 1),
            ],
        ),
        ProgramSector(
            logical_id="SEC-02",
            name="Setor residencial",
            area_kind=internal,
            subtotal_m2=209.0,
            spaces=[
                _space("REQ-02-01", "Quarto individual", 2, 10.0, internal, 1, beds_per_unit=1),
                _space("REQ-02-02", "Quarto duplo", 3, 12.0, internal, 1, beds_per_unit=2),
                _space("REQ-02-03", "Quarto triplo familiar", 2, 15.0, internal, 1, beds_per_unit=3),
                _space("REQ-02-04", "Quarto familiar ampliado", 1, 18.0, internal, 1, beds_per_unit=1),
                _space("REQ-02-05", "Quarto acessivel", 1, 16.0, internal, 1, accessible=True, beds_per_unit=1),
                _space("REQ-02-06", "Banheiro comum", 5, 3.5, internal, 1),
                _space("REQ-02-07", "Banheiro acessivel", 1, 4.5, internal, 1, accessible=True),
                _space("REQ-02-08", "Sala de convivencia", 1, 30.0, internal, 1),
                _space("REQ-02-09", "Refeitorio residencial", 1, 25.0, internal, 1),
                _space("REQ-02-10", "Copa de apoio residencial", 1, 12.0, internal, 1),
            ],
        ),
        ProgramSector(
            logical_id="SEC-03",
            name="Setor infantil",
            area_kind=internal,
            subtotal_m2=52.0,
            spaces=[
                _space("REQ-03-01", "Brinquedoteca", 1, 24.0, internal, 1),
                _space("REQ-03-02", "Apoio pedagogico e estudos", 1, 18.0, internal, 1),
                _space("REQ-03-03", "Banheiro infantil", 1, 6.0, internal, 1),
                _space("REQ-03-04", "Deposito de brinquedos", 1, 4.0, internal, 1),
            ],
        ),
        ProgramSector(
            logical_id="SEC-04",
            name="Atendimento tecnico",
            area_kind=internal,
            subtotal_m2=80.0,
            spaces=[
                _space("REQ-04-01", "Psicologia", 1, 10.0, internal, 1),
                _space("REQ-04-02", "Servico social", 1, 10.0, internal, 1),
                _space("REQ-04-03", "Atendimento juridico", 1, 10.0, internal, 1),
                _space("REQ-04-04", "Sala de reuniao", 1, 15.0, internal, 1),
                _space("REQ-04-05", "Sala multiuso e grupos", 1, 30.0, internal, 1),
                _space("REQ-04-06", "Arquivo e apoio tecnico", 1, 5.0, internal, 1),
            ],
        ),
        ProgramSector(
            logical_id="SEC-05",
            name="Comunitario e capacitacao",
            area_kind=internal,
            subtotal_m2=81.0,
            spaces=[
                _space("REQ-05-01", "Salao multiuso", 1, 60.0, internal, 1),
                _space("REQ-05-02", "Deposito de cadeiras e material", 1, 8.0, internal, 1),
                _space("REQ-05-03", "Copa de apoio comunitario", 1, 8.0, internal, 2),
                _space("REQ-05-04", "Sanitario acessivel", 1, 5.0, internal, 2, accessible=True),
            ],
        ),
        ProgramSector(
            logical_id="SEC-06",
            name="Administracao e servicos",
            area_kind=internal,
            subtotal_m2=151.0,
            spaces=[
                _space("REQ-06-01", "Coordenacao", 1, 10.0, internal, 2),
                _space("REQ-06-02", "Secretaria e administrativo", 1, 12.0, internal, 2),
                _space("REQ-06-03", "Sala de equipe", 1, 15.0, internal, 2),
                _space("REQ-06-04", "Refeitorio e copa de funcionarios", 1, 15.0, internal, 2),
                _space("REQ-06-05", "Sanitario e vestiario de funcionarios", 1, 10.0, internal, 2),
                _space("REQ-06-06", "Cozinha de producao", 1, 25.0, internal, 2),
                _space("REQ-06-07", "Despensa seca", 1, 6.0, internal, 2),
                _space("REQ-06-08", "Freezer e refrigerados", 1, 4.0, internal, 2),
                _space("REQ-06-09", "Lavanderia", 1, 12.0, internal, 2),
                _space("REQ-06-10", "Rouparia", 1, 6.0, internal, 2),
                _space("REQ-06-11", "Almoxarifado", 1, 8.0, internal, 2),
                _space("REQ-06-12", "Deposito geral", 1, 6.0, internal, 2),
                _space("REQ-06-13", "DML", 1, 3.0, internal, 2),
                _space("REQ-06-14", "Carga e descarga", 1, 15.0, internal, 2),
                _space("REQ-06-15", "Residuos", 1, 4.0, internal, 2),
            ],
        ),
        ProgramSector(
            logical_id="SEC-07",
            name="Areas externas",
            area_kind=external,
            subtotal_m2=260.0,
            spaces=[
                _space("REQ-07-01", "Patio interno protegido", 1, 80.0, external, 2),
                _space("REQ-07-02", "Jardim terapeutico", 1, 80.0, external, 2),
                _space("REQ-07-03", "Horta comunitaria", 1, 30.0, external, 2),
                _space("REQ-07-04", "Exercicios e alongamento", 1, 30.0, external, 2),
                _space("REQ-07-05", "Playground", 1, 40.0, external, 2),
            ],
        ),
    ]
    return AdoptedProgram(
        baseline=ProgramBaseline(
            source_id=PROGRAM_SOURCE_ID,
            source_filename=PROGRAM_SOURCE_FILENAME,
            source_sha256=PROGRAM_SOURCE_SHA256,
            source_pages=[1, 2],
            person_capacity=ADOPTED_PERSON_CAPACITY,
            adoption_status="ACCEPTED",
            selection_authority="AGENT_DELEGATED",
            selection_date="2026-09-15",
            evidence=(
                "Explicit user selection of '20 pessoas, conforme o PDF' on "
                "2026-09-15; the source hash was re-checked during ingestion."
            ),
        ),
        sectors=sectors,
        unselected_hypotheses=[
            UnselectedHypothesis(
                source_id="SRC-SUP-011",
                source_locator=(
                    "TFG_Amanda_2026/4_PROJETO_E_CALCULOS/"
                    "01_programa_de_necessidades.xlsx Premissas!C27"
                ),
                person_capacity=UNSELECTED_PERSON_CAPACITY,
                adoption_status="REJECTED",
                reason_not_adopted=(
                    "The 42-person spreadsheet scenario is explicitly hypothetical "
                    "and was not selected; its rows are never summed into the PDF "
                    "baseline."
                ),
            )
        ],
    )


def reconcile(program: AdoptedProgram | None = None) -> dict:
    """Reconcile every sector subtotal and the global totals of the source."""
    program = program or build_program()
    mismatches = []
    for sector in program.sectors:
        if round(sector.computed_subtotal_m2, 6) != round(sector.subtotal_m2, 6):
            mismatches.append(
                {
                    "sector": sector.logical_id,
                    "declared": sector.subtotal_m2,
                    "computed": sector.computed_subtotal_m2,
                }
            )
    internal = sum(
        sector.computed_subtotal_m2
        for sector in program.sectors
        if sector.area_kind == "INTERNAL"
    )
    external = sum(
        sector.computed_subtotal_m2
        for sector in program.sectors
        if sector.area_kind == "EXTERNAL"
    )
    if round(internal, 6) != INTERNAL_USEFUL_M2:
        mismatches.append(
            {
                "sector": "INTERNAL_TOTAL",
                "declared": INTERNAL_USEFUL_M2,
                "computed": internal,
            }
        )
    if round(external, 6) != EXTERNAL_PROGRAMMED_M2:
        mismatches.append(
            {
                "sector": "EXTERNAL_TOTAL",
                "declared": EXTERNAL_PROGRAMMED_M2,
                "computed": external,
            }
        )
    return {
        "ok": not mismatches,
        "mismatches": mismatches,
        "internal_useful_m2": internal,
        "external_programmed_m2": external,
    }


def program_payload(program: AdoptedProgram | None = None) -> dict:
    """Build the canonical JSON payload written to project/requirements."""
    program = program or build_program()
    report = reconcile(program)
    return {
        "schema_version": 1,
        "generated_from": "src/amanda_agent/requirements/program.py",
        "baseline": program.baseline.model_dump(),
        "totals": {
            "internal_useful_m2": report["internal_useful_m2"],
            "external_programmed_m2": report["external_programmed_m2"],
            "enclosed_estimate_m2": list(ENCLOSED_ESTIMATE_M2),
            "covered_estimate_m2": list(COVERED_ESTIMATE_M2),
        },
        "reconciliation": report,
        "sectors": [
            {
                "logical_id": sector.logical_id,
                "name": sector.name,
                "area_kind": sector.area_kind,
                "subtotal_m2": sector.subtotal_m2,
                "spaces": [
                    {
                        **space.model_dump(),
                        "total_area_m2": space.total_area_m2,
                    }
                    for space in sector.spaces
                ],
            }
            for sector in program.sectors
        ],
        "unselected_hypotheses": [
            hypothesis.model_dump()
            for hypothesis in program.unselected_hypotheses
        ],
    }


_SUMMARY_TEMPLATE = """# Programa de necessidades adotado

Fonte: `{source_filename}` (`{source_id}`), SHA-256 `{source_sha256}`.
Capacidade adotada: **{capacity} pessoas acolhidas simultaneamente**.
Status de adocao: `{adoption_status}` (selecao explicita do usuario em {date}).

| Setor | Subtotal | Ambientes |
|---|---:|---:|
{rows}

Totais reconciliados: **{internal:g} m² uteis internos** e
**{external:g} m² externos programados**. Estimativas do documento:
{enclosed_lo:g}-{enclosed_hi:g} m² fechados e {covered_lo:g}-{covered_hi:g} m²
cobertos no total.

## Hipotese nao adotada

{hypotheses}

> Area unitaria de pre-dimensionamento nao e automaticamente minimo normativo.
> Os totais devem ser ajustados conforme layout, fluxos, acessibilidade e
> exigencias normativas aplicaveis.
"""


def program_summary_markdown(program: AdoptedProgram | None = None) -> str:
    """Render the summary from canonical objects; never the reverse."""
    program = program or build_program()
    report = reconcile(program)
    rows = "\n".join(
        f"| {sector.name} | {sector.subtotal_m2:g} m² | {len(sector.spaces)} |"
        for sector in program.sectors
    )
    hypotheses = "\n".join(
        f"- `{item.source_id}` ({item.source_locator}): {item.person_capacity} "
        f"pessoas, status `{item.adoption_status}`. {item.reason_not_adopted}"
        for item in program.unselected_hypotheses
    )
    return _SUMMARY_TEMPLATE.format(
        source_filename=program.baseline.source_filename,
        source_id=program.baseline.source_id,
        source_sha256=program.baseline.source_sha256,
        capacity=program.baseline.person_capacity,
        adoption_status=program.baseline.adoption_status,
        date=program.baseline.selection_date,
        rows=rows,
        internal=report["internal_useful_m2"],
        external=report["external_programmed_m2"],
        enclosed_lo=ENCLOSED_ESTIMATE_M2[0],
        enclosed_hi=ENCLOSED_ESTIMATE_M2[1],
        covered_lo=COVERED_ESTIMATE_M2[0],
        covered_hi=COVERED_ESTIMATE_M2[1],
        hypotheses=hypotheses,
    )


def _write_atomically(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def write_program(root: Path) -> Path:
    """Write the canonical program JSON and return its path."""
    target = Path(root) / "project" / "requirements" / "program.json"
    _write_atomically(
        target, json.dumps(program_payload(), ensure_ascii=False, indent=2) + "\n"
    )
    return target


def write_program_summary(root: Path) -> Path:
    """Write the markdown summary derived from the canonical objects."""
    target = Path(root) / "project" / "requirements" / "program-summary.md"
    _write_atomically(target, program_summary_markdown())
    return target


__all__ = [
    "ADOPTED_PERSON_CAPACITY",
    "COVERED_ESTIMATE_M2",
    "ENCLOSED_ESTIMATE_M2",
    "EXTERNAL_PROGRAMMED_M2",
    "INTERNAL_USEFUL_M2",
    "PROGRAM_SOURCE_FILENAME",
    "PROGRAM_SOURCE_ID",
    "PROGRAM_SOURCE_SHA256",
    "UNSELECTED_PERSON_CAPACITY",
    "AdoptedProgram",
    "ProgramBaseline",
    "ProgramSector",
    "ProgramSpace",
    "UnselectedHypothesis",
    "build_program",
    "program_payload",
    "program_summary_markdown",
    "reconcile",
    "write_program",
    "write_program_summary",
]
