"""Validation and reporting for the canonical ingest boundary."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import yaml

from ..requirements.decisions import load_decision_register
from ..requirements.regulations import (
    RegulationRegistry,
    RegulationRule,
)
from ..site.models import BoundaryPolygon, Topography
from ..site.models import SourceReference as SiteSourceReference
from .manifest import SourceManifest, sha256_file, source_inventory_paths
from .provenance import ProvenanceRecord

CheckStatus = Literal["PASS", "FAIL"]
Verdict = Literal["GO", "GO_WITH_LIMITATIONS", "NO_GO"]


@dataclass(frozen=True)
class ValidationCheck:
    """One short, reportable validation result."""

    name: str
    status: CheckStatus
    detail: str


@dataclass(frozen=True)
class ValidationResult:
    """Complete result of one read-only project validation."""

    verdict: Verdict
    checks: list[ValidationCheck]
    open_blocker_ids: list[str]
    limitations: int

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def passed(self) -> int:
        return sum(check.status == "PASS" for check in self.checks)

    @property
    def failed(self) -> int:
        return sum(check.status == "FAIL" for check in self.checks)


class _ValidationContext:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.manifest: SourceManifest | None = None
        self.manifest_by_id: dict[str, Any] = {}
        self.program: dict[str, Any] | None = None
        self.site: dict[str, Any] | None = None
        self.requirements: dict[str, dict[str, Any]] = {}
        self.registry: RegulationRegistry | None = None
        self.open_blocker_ids: list[str] = []
        self.limitations = 0


def _short_error(error: Exception) -> str:
    message = " ".join(str(error).split())
    return message[:280] if message else error.__class__.__name__


def _mapping(payload: Any, label: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError(f"{label} deve conter um objeto")
    return payload


def _schema_version(payload: dict[str, Any], label: str) -> None:
    if payload.get("schema_version") != 1:
        raise ValueError(f"{label} requer schema_version 1")


def _finite_positive(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} deve ser numerico")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} deve ser finito e positivo")
    return number


def _close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-6)


def _source_id_from_ref(reference: str) -> str:
    return reference.split("#", 1)[0].split()[0]


def _validate_manifest(context: _ValidationContext) -> None:
    path = context.root / "project" / "provenance" / "source-manifest.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    manifest = SourceManifest.model_validate(_mapping(payload, "source-manifest.yaml"))
    if manifest.schema_version != 1:
        raise ValueError("source-manifest.yaml requer schema_version 1")

    docs_root = (context.root / "docs" / "source").resolve()
    if not docs_root.is_dir():
        raise FileNotFoundError("docs/source ausente")
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for document in manifest.documents:
        if document.source_id in seen_ids:
            raise ValueError(f"source_id duplicado: {document.source_id}")
        seen_ids.add(document.source_id)
        candidate = (context.root / document.immutable_path).resolve()
        try:
            candidate.relative_to(docs_root)
        except ValueError as error:
            raise ValueError(
                f"caminho imutavel fora de docs/source: {document.immutable_path}"
            ) from error
        relative = candidate.relative_to(docs_root).as_posix()
        if relative in seen_paths:
            raise ValueError(f"caminho imutavel duplicado: {relative}")
        seen_paths.add(relative)
        if not candidate.is_file():
            raise FileNotFoundError(f"fonte ausente: {document.immutable_path}")
        if sha256_file(candidate) != document.sha256:
            raise ValueError(f"hash divergente: {document.filename}")
        context.manifest_by_id[document.source_id] = document

    actual_paths = {
        item.relative_to(docs_root).as_posix()
        for item in docs_root.rglob("*")
        if item.is_file()
    }
    try:
        expected_paths = source_inventory_paths(context.root, manifest)
    except (OSError, ValueError) as error:
        raise ValueError("manifesto suplementar de fontes invalido") from error
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        extra = sorted(actual_paths - expected_paths)
        details = []
        if missing:
            details.append("ausentes=" + ",".join(missing[:3]))
        if extra:
            details.append("sem manifesto=" + ",".join(extra[:3]))
        raise ValueError("docs/source diverge do manifesto (" + "; ".join(details) + ")")
    context.manifest = manifest


def _validate_program_schema(context: _ValidationContext) -> None:
    path = context.root / "project" / "requirements" / "program.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    program = _mapping(payload, "program.json")
    _schema_version(program, "program.json")
    baseline = _mapping(program.get("baseline"), "program.baseline")
    for field in (
        "source_id",
        "source_filename",
        "source_sha256",
        "source_pages",
        "person_capacity",
        "adoption_status",
        "selection_authority",
        "selection_date",
        "evidence",
    ):
        if field not in baseline:
            raise ValueError(f"program.baseline.{field} ausente")
    if not isinstance(baseline["source_pages"], list) or not baseline["source_pages"]:
        raise ValueError("program.baseline.source_pages invalido")
    if (
        isinstance(baseline["person_capacity"], bool)
        or not isinstance(baseline["person_capacity"], int)
        or baseline["person_capacity"] < 1
    ):
        raise ValueError("program.baseline.person_capacity invalido")

    totals = _mapping(program.get("totals"), "program.totals")
    internal_total = _finite_positive(totals.get("internal_useful_m2"), "totals.internal_useful_m2")
    external_total = _finite_positive(totals.get("external_programmed_m2"), "totals.external_programmed_m2")
    sectors = program.get("sectors")
    if not isinstance(sectors, list) or not sectors:
        raise ValueError("program.sectors deve ser uma lista nao vazia")

    identifiers: set[str] = set()
    computed = {"INTERNAL": 0.0, "EXTERNAL": 0.0}
    for sector in sectors:
        sector_data = _mapping(sector, "program.sector")
        for field in ("logical_id", "name", "area_kind", "subtotal_m2", "spaces"):
            if field not in sector_data:
                raise ValueError(f"program.sector.{field} ausente")
        area_kind = sector_data["area_kind"]
        if area_kind not in computed:
            raise ValueError(f"area_kind invalido: {area_kind}")
        subtotal = _finite_positive(sector_data["subtotal_m2"], "sector.subtotal_m2")
        spaces = sector_data["spaces"]
        if not isinstance(spaces, list) or not spaces:
            raise ValueError("program.sector.spaces deve ser uma lista nao vazia")
        sector_total = 0.0
        for space in spaces:
            space_data = _mapping(space, "program.space")
            for field in (
                "logical_id",
                "name",
                "quantity",
                "target_area_m2",
                "area_kind",
                "source_page",
            ):
                if field not in space_data:
                    raise ValueError(f"program.space.{field} ausente")
            logical_id = space_data["logical_id"]
            if logical_id in identifiers:
                raise ValueError(f"logical_id duplicado: {logical_id}")
            identifiers.add(logical_id)
            quantity = space_data["quantity"]
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
                raise ValueError(f"quantity invalida: {logical_id}")
            unit_area = _finite_positive(space_data["target_area_m2"], "space.target_area_m2")
            space_kind = space_data["area_kind"]
            if space_kind not in computed or space_kind != area_kind:
                raise ValueError(f"area_kind inconsistente: {logical_id}")
            source_page = space_data["source_page"]
            if isinstance(source_page, bool) or not isinstance(source_page, int) or source_page < 1:
                raise ValueError(f"source_page invalido: {logical_id}")
            row_total = quantity * unit_area
            if "total_area_m2" in space_data:
                recorded_total = _finite_positive(
                    space_data["total_area_m2"], "space.total_area_m2"
                )
                if not _close(recorded_total, row_total):
                    raise ValueError(f"total de espaco nao reconcilia: {logical_id}")
            sector_total += row_total
        if not _close(sector_total, subtotal):
            raise ValueError(f"subtotal nao reconcilia: {sector_data['logical_id']}")
        computed[area_kind] += sector_total

    if not _close(computed["INTERNAL"], internal_total):
        raise ValueError("total interno nao reconcilia")
    if not _close(computed["EXTERNAL"], external_total):
        raise ValueError("total externo nao reconcilia")
    reconciliation = _mapping(program.get("reconciliation"), "program.reconciliation")
    if reconciliation.get("ok") is not True or reconciliation.get("mismatches") != []:
        raise ValueError("program.reconciliation registra divergencia")
    context.program = program


def _validate_requirements_yaml(context: _ValidationContext) -> None:
    requirements_root = context.root / "project" / "requirements"
    files = sorted(requirements_root.glob("*.yaml"))
    if not files:
        raise FileNotFoundError("project/requirements/*.yaml ausente")
    for path in files:
        payload = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), path.name)
        _schema_version(payload, path.name)
        if path.name == "source-principles.yaml":
            collection_name = "principles"
            model = ProvenanceRecord
        elif path.name == "design-hypotheses.yaml":
            collection_name = "hypotheses"
            model = ProvenanceRecord
        elif path.name in {"decision-register.yaml", "decisions.yaml"}:
            load_decision_register(path)
            context.requirements[path.name] = payload
            continue
        elif path.name == "academic-deliverables.yaml":
            deliverables = payload.get("deliverables")
            if not isinstance(deliverables, list) or not deliverables:
                raise ValueError("academic-deliverables.yaml.deliverables invalido")
            for item in deliverables:
                deliverable = _mapping(item, "academic deliverable")
                for field in ("deliverable_id", "name", "status", "source_refs"):
                    if field not in deliverable:
                        raise ValueError(
                            f"academic deliverable sem {field}: "
                            + str(deliverable.get("deliverable_id", "?"))
                        )
                if not isinstance(deliverable["source_refs"], list):
                    raise TypeError("academic deliverable source_refs invalido")
            context.requirements[path.name] = payload
            continue
        else:
            collections = [value for value in payload.values() if isinstance(value, list)]
            if not collections:
                raise ValueError(f"{path.name} nao declara uma colecao canonica")
            context.requirements[path.name] = payload
            continue
        records = payload.get(collection_name)
        if not isinstance(records, list) or not records:
            raise ValueError(f"{path.name}.{collection_name} invalido")
        for item in records:
            model.model_validate(item)
        context.requirements[path.name] = payload


def _validate_site_schema(context: _ValidationContext) -> None:
    path = context.root / "project" / "site" / "site.json"
    payload = _mapping(json.loads(path.read_text(encoding="utf-8")), "site.json")
    _schema_version(payload, "site.json")
    for field in (
        "site_name",
        "location",
        "site_version",
        "boundary",
        "design_coordinate_origin",
        "topography",
        "provenance",
    ):
        if field not in payload:
            raise ValueError(f"site.{field} ausente")
    boundary = _mapping(payload["boundary"], "site.boundary")
    boundary_payload = {
        key: boundary[key]
        for key in ("coordinates", "kind", "placeholder_area_m2", "source_ref")
        if key in boundary
    }
    BoundaryPolygon.model_validate(boundary_payload)
    origin = _mapping(payload["design_coordinate_origin"], "site.design_coordinate_origin")
    if origin.get("convention") != "LOCAL_DESIGN_PLANE":
        raise ValueError("convencao da origem de projeto invalida")
    topography = Topography.model_validate(_mapping(payload["topography"], "site.topography"))
    provenance = payload["provenance"]
    if not isinstance(provenance, list) or not provenance:
        raise ValueError("site.provenance invalida")
    for reference in provenance:
        SiteSourceReference.model_validate(reference)
    context.site = payload
    # Keep the typed guard explicit even though status has its own report check.
    if topography.source_state.value == "MISSING" and topography.elevation_points:
        raise ValueError("topografia MISSING nao pode ter pontos")


def _validate_regulation_registry(context: _ValidationContext) -> None:
    path = context.root / "project" / "regulations" / "registry.yaml"
    payload = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), "registry.yaml")
    _schema_version(payload, "registry.yaml")
    rules = payload.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("registry.rules invalido")
    registry = RegulationRegistry()
    for item in rules:
        rule = RegulationRule.model_validate(item)
        if not rule.primary_source or not rule.source_refs:
            raise ValueError(f"regra sem proveniencia: {rule.logical_id}")
        registry.add(rule)
    registry.compile_derived_constraints()
    context.registry = registry


def _validate_program_totals(context: _ValidationContext) -> None:
    if context.program is None:
        raise ValueError("program.json nao foi carregado")
    reconciliation = context.program.get("reconciliation", {})
    if reconciliation.get("ok") is not True or reconciliation.get("mismatches"):
        raise ValueError("program totals nao reconciliados")


def _validate_provenance(context: _ValidationContext) -> None:
    if not context.manifest_by_id:
        raise ValueError("manifesto sem fontes")
    if context.program is not None:
        baseline = context.program["baseline"]
        document = context.manifest_by_id.get(baseline["source_id"])
        if document is None or document.sha256 != baseline["source_sha256"]:
            raise ValueError("proveniencia do baseline do programa diverge")
    if context.site is not None:
        for item in context.site["provenance"]:
            reference = SiteSourceReference.model_validate(item)
            document = context.manifest_by_id.get(reference.source_id)
            if document is None or document.sha256 != reference.sha256:
                raise ValueError(f"proveniencia do site diverge: {reference.source_id}")
        for frontage in context.site.get("frontages", []):
            frontage_data = _mapping(frontage, "site.frontage")
            source_id = _source_id_from_ref(str(frontage_data.get("source_ref", "")))
            document = context.manifest_by_id.get(source_id)
            if document is None or document.sha256 != frontage_data.get("sha256"):
                raise ValueError(f"proveniencia da frente diverge: {source_id}")
    source_principles = context.requirements.get("source-principles.yaml")
    if source_principles is not None:
        for item in source_principles["principles"]:
            record = ProvenanceRecord.model_validate(item)
            for reference in record.source_refs:
                document = context.manifest_by_id.get(reference.source_id)
                if document is None or document.sha256 != reference.source_hash:
                    raise ValueError(f"proveniencia do principio diverge: {reference.source_id}")
    if context.registry is not None:
        for rule in context.registry.rules:
            for reference in rule.source_refs:
                source_id = _source_id_from_ref(reference)
                if source_id not in context.manifest_by_id:
                    raise ValueError(f"fonte normativa ausente no manifesto: {source_id}")


def _validate_site_status(context: _ValidationContext) -> str:
    if context.site is None:
        raise ValueError("site.json nao foi carregado")
    notes: list[str] = []
    topography = context.site["topography"]
    source_state = topography.get("source_state")
    representation = topography.get("representation")
    elevations = topography.get("elevation_points")
    if source_state == "MISSING":
        if representation != "PLANAR_PLACEHOLDER" or elevations:
            raise ValueError("status topografico MISSING inconsistente")
        context.limitations += 1
        notes.append("topografia MISSING aceita como limitacao de estudo")
    elif source_state == "VERIFIED_TOPOGRAPHY":
        if representation != "VERIFIED_TOPOGRAPHY":
            raise ValueError("topografia verificada requer representacao verificada")
    else:
        raise ValueError("source_state topografico invalido")
    if context.site.get("boundary", {}).get("kind") == "STUDY_PLACEHOLDER":
        context.limitations += 1
        notes.append("boundary STUDY_PLACEHOLDER permanece provisoria")
    if context.site.get("true_north") is None:
        context.limitations += 1
        notes.append("true north pendente")
    if str(context.site.get("frontage_conflict", {}).get("resolution", "")).startswith("UNRESOLVED"):
        context.limitations += 1
        notes.append("conflito de frentes pendente")
    if context.registry is not None and any(
        rule.status.value in {"IDENTIFIED", "SOURCE_ACQUIRED"}
        for rule in context.registry.rules
    ):
        context.limitations += 1
        notes.append("parte do registro normativo permanece identificada")
    return "; ".join(notes) or "validado"


def _load_open_blockers(context: _ValidationContext) -> None:
    path = context.root / "state" / "blockers.yaml"
    payload = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), "blockers.yaml")
    if payload.get("schema_version") != 1:
        raise ValueError("blockers.yaml requer schema_version 1")
    blockers = payload.get("blockers")
    if not isinstance(blockers, list):
        raise TypeError("blockers.yaml.blockers invalido")
    identifiers: list[str] = []
    for blocker in blockers:
        item = _mapping(blocker, "blocker")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("bloqueador sem id")
        if item.get("resolved_utc") is None:
            identifiers.append(identifier)
    context.open_blocker_ids = identifiers


def _run_check(
    checks: list[ValidationCheck], name: str, callback: Any
) -> None:
    try:
        detail = callback()
    except (
        OSError,
        TypeError,
        ValueError,
        KeyError,
        IndexError,
        AttributeError,
        OverflowError,
        yaml.YAMLError,
    ) as error:
        checks.append(ValidationCheck(name, "FAIL", _short_error(error)))
    else:
        checks.append(ValidationCheck(name, "PASS", str(detail or "validado")))


def validate_project(root: Path) -> ValidationResult:
    """Validate the project without changing canonical inputs."""

    context = _ValidationContext(Path(root))
    checks: list[ValidationCheck] = []
    _run_check(checks, "Manifesto e hashes das fontes", lambda: _validate_manifest(context))
    _run_check(checks, "Schema de program.json", lambda: _validate_program_schema(context))
    _run_check(checks, "Schemas canonicos de requisitos", lambda: _validate_requirements_yaml(context))
    _run_check(checks, "Schema de site.json", lambda: _validate_site_schema(context))
    _run_check(checks, "Registro de regulamentacao", lambda: _validate_regulation_registry(context))
    _run_check(checks, "Proveniencia", lambda: _validate_provenance(context))
    _run_check(checks, "Totais do programa", lambda: _validate_program_totals(context))
    _run_check(checks, "Status do site", lambda: _validate_site_status(context))
    _run_check(checks, "Bloqueadores abertos", lambda: _load_open_blockers(context))
    context.limitations = max(context.limitations, len(context.open_blocker_ids))
    if any(check.status == "FAIL" for check in checks):
        verdict: Verdict = "NO_GO"
    elif context.limitations:
        verdict = "GO_WITH_LIMITATIONS"
    else:
        verdict = "GO"
    return ValidationResult(
        verdict=verdict,
        checks=checks,
        open_blocker_ids=context.open_blocker_ids,
        limitations=context.limitations,
    )


def render_validation_report(result: ValidationResult, *, generated_at: datetime | None = None) -> str:
    """Render the compact Portuguese report written by the CLI."""

    timestamp = generated_at or datetime.now().astimezone()
    lines = [
        "# Relatorio de validacao da ingestao",
        "",
        "- Comando: `amanda-agent ingest --validate-only`",
        f"- Data: {timestamp.date().isoformat()}",
        f"- Contagens: {result.total} verificacoes; {result.passed} PASS; {result.failed} FAIL; {result.limitations} limitacoes",
        f"- Veredito: **{result.verdict}**",
        "",
        "## Verificacoes",
        "",
    ]
    lines.extend(
        f"- {check.status} — {check.name}: {check.detail}"
        for check in result.checks
    )
    lines.extend(["", "## Bloqueadores abertos", ""])
    if result.open_blocker_ids:
        lines.extend(f"- {identifier}" for identifier in result.open_blocker_ids)
    else:
        lines.append("- nenhum")
    return "\n".join(lines) + "\n"


def write_validation_report(root: Path, result: ValidationResult) -> Path:
    """Write the generated report and return its path."""

    target = Path(root) / "docs" / "reports" / "ingest-report.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_validation_report(result), encoding="utf-8")
    return target


__all__ = [
    "ValidationCheck",
    "ValidationResult",
    "render_validation_report",
    "validate_project",
    "write_validation_report",
]
