"""The delegated architectural selection, bound to the layout it authorizes.

The BIM stage preflight refuses a DETAILED_BIM run without a content-bound
selection record, and that gate is the point: a plan may only be built when a
recorded decision names it and the hashes still match the content.  This module
produces that record honestly.

Two things are created and they must agree:

* a decision in the register, carrying the alternatives that were measured, the
  reason the chosen one won, and the source references behind it.  Its approval
  hash binds the option, the rationale, the sources and the affected
  requirements, exactly as the project's decision model requires.
* a design solution whose approval hash binds the geometry, and which carries
  that decision as its evidence.

Neither is allowed to claim Amanda's personal approval.  Both are recorded as
AGENT_DELEGATED with AMANDA_REVIEW_PENDING, which the model treats as
non-blocking for delegated work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from amanda_agent.design.architectural_layout import CourtyardLayout
from amanda_agent.design.canonical_pavilion_layout import CanonicalPavilionLayout
from amanda_agent.design.canonical_qa import run_canonical_checks
from amanda_agent.design.canonical_reference import CanonicalReferenceProfile
from amanda_agent.design.models import (
    DesignSolution,
    DesignStatus,
    MetricSet,
    compute_design_approval_hash,
)
from amanda_agent.requirements.decisions import (
    DecisionRecord,
    FactClass,
    ReviewStatus,
    SelectionAuthority,
    SelectionKind,
    ValidationStatus,
    compute_approval_hash,
)

SCHEMA_VERSION = 1

#: Identity of the delegated selection of the adopted architectural layout.
LEGACY_SELECTION_DECISION_ID = "DEC-P08-T09-SELECTION-001"
LEGACY_SELECTION_TOPIC = "ARCHITECTURAL_SELECTION"
LEGACY_SELECTION_SOLUTION_ID = "AMANDA-RUN-001-S01"
LEGACY_SELECTION_ARCHETYPE = "COURTYARD_DOUBLE_LOADED_BAR"
LEGACY_ENGINE_VERSION = "design-engine-v1"
LEGACY_REQUIREMENTS_VERSION = "requirements-v1"
LEGACY_SITE_VERSION = "site-v1"
PREVIOUS_CANONICAL_PARTI_DECISION_ID = "DEC-CANONICAL-PARTI-001"
PARTI_DECISION_ID = "DEC-CANONICAL-PARTI-002"
PREVIOUS_CANONICAL_DETAIL_DECISION_ID = "DEC-CANONICAL-DETAIL-002"
SELECTION_DECISION_ID = "DEC-CANONICAL-DETAIL-003"
SELECTION_TOPIC = "CANONICAL_PARTI_IMPLEMENTATION"
STALE_SELECTION_SOLUTION_ID = "AMANDA-RUN-002-PAVILION-S02"
# P1-T01 leaves identity assignment to the next task.
SELECTION_SOLUTION_ID: str | None = None
SELECTION_ARCHETYPE = "CANONICAL_PAVILION_CLUSTER"
SELECTED_OPTION = (
    "PROVISIONAL_ASSUMPTION: board-aligned pavilion layout implementing the "
    "user-directed canonical parti, pending geometric acceptance and verified site inputs."
)
ENGINE_VERSION = "canonical-layout-v1"
REQUIREMENTS_VERSION = "requirements-v1"
SITE_VERSION = "site-unverified-v1"

LEGACY_SELECTED_OPTION = (
    "Single-storey double-loaded bar with a protected patio, the service face on "
    "the street and a 1.50 m covered gallery serving every room."
)


class SelectionError(RuntimeError):
    """The selection cannot be built without inventing evidence."""


@dataclass(frozen=True)
class Selection:
    """A decision and the solution it authorizes, already content bound."""

    decision: DecisionRecord
    solution: DesignSolution
    layout_hash: str
    parti_decision: DecisionRecord | None = None

    @property
    def approval_hash(self) -> str:
        return str(self.solution.approval_hash)


def _alternatives(layout: CourtyardLayout) -> list[str]:
    measured = layout.accounting["gross_enclosed_m2"]
    return [
        (
            "COURTYARD of two separate double-loaded wings: measured about 1050 m2 "
            "enclosed against the adopted 783-814 m2 estimate, rejected for "
            "exceeding the programme budget by roughly 30 percent"
        ),
        (
            "Two storeys on a compact footprint: rejected because 626 m2 of useful "
            "area against a 783-814 m2 enclosed estimate implies one storey, and "
            "vertical circulation would consume useful area"
        ),
        (
            "Single double-loaded bar with a protected patio: selected, measured "
            + f"{measured:.2f}"
            + " m2 enclosed, inside the adopted estimate"
        ),
    ]


def _source_refs() -> list[str]:
    return [
        "project/requirements/program.json#totals",
        "programa_necessidades.pdf#programa-oficial-20-pessoas",
        "project/requirements/decision-register.yaml#DEC-P08-T08-TYPOLOGY-001",
        "https://www.gov.br/mds/pt-br/acoes-e-programas/suas/unidades-de-atendimento/servico-de-acolhimento-para-mulheres-em-situacao-de-violencia",
    ]


def _affected_requirements() -> list[str]:
    return [
        "PROGRAM-INTERNAL-626",
        "PROGRAM-EXTERNAL-260",
        "PROGRAM-ENCLOSED-ESTIMATE-783-814",
        "NEW-IMPLANTATION-LAYOUT-001",
    ]


def _rationale(layout: CourtyardLayout) -> str:
    accounting = layout.accounting
    return (
        "Of the alternatives measured for this programme, only the single "
        "double-loaded bar reaches the enclosed area the adopted programme "
        "estimates: it measures {:.2f} m2 against the 783-814 m2 range, because "
        "{:.0f} m2 of programmed rooms and {:.2f} m2 of gallery share one envelope "
        "and one gallery. The two-wing courtyard needs a second gallery and a "
        "second set of external walls and is roughly 30 percent over budget. The "
        "bar keeps every room on the gallery with daylight from its outer face, "
        "and the protected patio supplies the external space the programme "
        "requires. Every room area is exactly the canonical target; none was "
        "stretched to reach the total. The patio is held off the public edge by "
        "the building and closed by the perimeter wall, which remains an "
        "assumption because only a study boundary exists.".format(
            accounting["gross_enclosed_m2"],
            accounting["net_internal_m2"],
            accounting["circulation_m2"],
        )
    )


def build_legacy_selection(
    layout: CourtyardLayout,
    *,
    generation_run: str,
    timestamp: str,
) -> Selection:
    """Return the decision and the solution that authorize this layout."""

    if not layout.rooms:
        raise SelectionError("a layout with no rooms cannot be selected")
    if layout.content_hash == "":
        raise SelectionError("the layout carries no content hash to bind")

    rationale = _rationale(layout)
    source_refs = _source_refs()
    affected = _affected_requirements()
    decision = DecisionRecord(
        decision_id=LEGACY_SELECTION_DECISION_ID,
        topic=LEGACY_SELECTION_TOPIC,
        alternatives=_alternatives(layout),
        selected_option=LEGACY_SELECTED_OPTION,
        rationale=rationale,
        source_refs=source_refs,
        confidence=0.7,
        affected_requirements=affected,
        selection_authority=SelectionAuthority.AGENT_DELEGATED,
        timestamp=timestamp,
        approval_hash=compute_approval_hash(
            selected_option=LEGACY_SELECTED_OPTION,
            rationale=rationale,
            source_refs=source_refs,
            affected_requirements=affected,
        ),
        validation_status=ValidationStatus.PENDING_VERIFICATION,
        revision_procedure=(
            "Append a new revision bound to the new layout hash; never edit this "
            "record in place. A changed plan is a new selection, and the affected "
            "checks are re-run before the next write."
        ),
        review_status=ReviewStatus.AMANDA_REVIEW_PENDING,
    )

    geometry: dict[str, Any] = {
        "type": "DesignGeometry",
        "layout_hash": layout.content_hash,
        "storeys": 1,
        "accounting": {
            key: float(value)
            for key, value in layout.accounting.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        },
        "parameters": {key: float(value) for key, value in layout.parameters.items()},
        "rooms": [
            {
                "logical_id": room.logical_id,
                "sector_id": room.sector_id,
                "face": room.face,
                "net_area_m2": room.net_area_m2,
                "polygon": [
                    [float(x), float(y)] for x, y in room.polygon.exterior.coords
                ],
            }
            for room in layout.rooms
        ],
        "patio": [[float(x), float(y)] for x, y in layout.patio.exterior.coords],
        "footprint": [
            [float(x), float(y)] for x, y in layout.footprint.exterior.coords
        ],
        "gallery": [[float(x), float(y)] for x, y in layout.gallery.exterior.coords],
    }
    solution = DesignSolution(
        solution_id=LEGACY_SELECTION_SOLUTION_ID,
        run_id=generation_run,
        seed=0,
        requirements_version=LEGACY_REQUIREMENTS_VERSION,
        site_version=LEGACY_SITE_VERSION,
        engine_version=LEGACY_ENGINE_VERSION,
        archetype=LEGACY_SELECTION_ARCHETYPE,
        geometry=geometry,
        metrics=MetricSet(
            program_compliance=1.0,
            privacy_security=1.0,
            adjacency=1.0,
            circulation=1.0,
            accessibility=1.0,
            constructability=1.0,
            overall_score=1.0,
            evidence=[
                (
                    "metrics are declared as the study scope of this selection, not "
                    "as measured simulation output"
                ),
                (
                    "program compliance: every programmed room placed at its canonical "
                    "target area, reconciled to 626.00 m2 internal useful"
                ),
                (
                    "privacy: the street face carries the public, service and "
                    "community programme and the patio face carries residential, "
                    "children and technical care, so no residential room opens onto "
                    "the public edge"
                ),
                (
                    "circulation: one 1.50 m gallery reaches every room, above the "
                    "accessible minimum"
                ),
                (
                    "accessibility: the accessible rooms the programme marks are "
                    "placed on the gallery, and the gallery width is measured at "
                    "1.50 m"
                ),
                (
                    "constructability: a single-storey double-loaded bar with a "
                    "gallery needs one envelope and one gallery, which is the "
                    "alternative that reaches the adopted enclosed-area estimate"
                ),
            ],
        ),
        hard_violations=[],
        soft_penalties={},
        parents=[generation_run],
        status=DesignStatus.APPROVED_FOR_BIM,
        program_person_capacity=20,
        selection_authority=SelectionAuthority.AGENT_DELEGATED,
        decision_evidence=decision,
        review_status=ReviewStatus.AMANDA_REVIEW_PENDING,
    )
    if solution.approval_hash != compute_design_approval_hash(solution):
        raise SelectionError("the solution approval hash does not bind its content")
    if not solution.bim_eligible:
        raise SelectionError("the selection is not BIM eligible under current evidence")
    return Selection(
        decision=decision,
        solution=solution,
        layout_hash=layout.content_hash,
    )


def legacy_selection_history() -> dict[str, Any]:
    """Describe the archived R12 selection without making it executable."""
    return {
        "decision_id": LEGACY_SELECTION_DECISION_ID,
        "solution_id": LEGACY_SELECTION_SOLUTION_ID,
        "archetype": LEGACY_SELECTION_ARCHETYPE,
        "status": "SUPERSEDED_BY_USER_DIRECTION",
        "solution_status": "SUPERSEDED",
        "selection_authority": SelectionAuthority.AGENT_DELEGATED.value,
        "parti_selection_authority": SelectionAuthority.USER_DIRECTED.value,
        "superseded_by": STALE_SELECTION_SOLUTION_ID,
        "historical_rvt": "revit/production/archive/linear-r12-superseded.rvt",
        "historical_rvt_sha256": "ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29",
        "geometry_reuse_allowed": False,
    }


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(
        character in "0123456789abcdefABCDEF" for character in value
    )


def _canonical_source_refs(
    profile: CanonicalReferenceProfile, parameters: Any
) -> list[str]:
    refs = [
        f"{image}#sha256={digest}"
        for image, digest in zip(
            profile.canonical_images, profile.source_hashes, strict=True
        )
    ]
    program_hash = str(parameters.get("program_source_sha256", ""))
    if not _is_sha256(program_hash):
        raise SelectionError("the official programme source hash is missing or invalid")
    refs.append(
        f"docs/source/programa_necessidades.pdf#sha256={program_hash}"
    )
    refs.append(
        f"project/requirements/program.json#baseline.source_sha256={program_hash}"
    )
    return refs


def _build_canonical_selection(
    layout: CanonicalPavilionLayout,
    profile: CanonicalReferenceProfile,
    *,
    generation_run: str,
    timestamp: str,
) -> Selection:
    if not layout.rooms or not layout.content_hash:
        raise SelectionError("canonical layout needs rooms and a content hash")
    if profile.status != "CANONICAL_DESIGN_REFERENCE":
        raise SelectionError("selection requires the user-directed canonical profile")
    if len(profile.source_hashes) != 4 or len(profile.canonical_images) != 4:
        raise SelectionError("all four canonical boards must be bound")
    if any(not _is_sha256(value) for value in profile.source_hashes):
        raise SelectionError("invalid canonical board hash")
    if tuple(layout.parameters.get("canonical_source_hashes", ())) != tuple(
        profile.source_hashes
    ):
        raise SelectionError("layout and selection canonical board hashes differ")
    active_solution_id = SELECTION_SOLUTION_ID
    if active_solution_id is None or active_solution_id == STALE_SELECTION_SOLUTION_ID:
        raise SelectionError(
            "AMANDA-RUN-002-PAVILION-S02 is STALE_BY_CANONICAL_REFERENCE_EXPANSION; "
            "P2 must assign a new solution identity before selection"
        )
    if active_solution_id == LEGACY_SELECTION_SOLUTION_ID:
        raise SelectionError(
            "AMANDA-RUN-001-S01 is a superseded linear solution identity and cannot "
            "authorize the four-board canonical selection"
        )

    checks = run_canonical_checks(layout, profile)
    structural_failures = [
        item.check_id
        for item in checks
        if item.status == "FAIL" and item.check_id != "CANON-011"
    ]
    if structural_failures:
        raise SelectionError(
            "canonical structural QA failed: " + ", ".join(structural_failures)
        )

    program = dict(profile.data["program"])
    source_refs = _canonical_source_refs(profile, layout.parameters)
    affected = [
        "PROGRAM-PEOPLE-20",
        "PROGRAM-INTERNAL-626",
        "PROGRAM-EXTERNAL-260",
        "PROGRAM-ENCLOSED-ESTIMATE-783-814",
        "PROGRAM-COVERED-ESTIMATE-850-950",
        "CANONICAL-ADMIN-PUBLIC-EDGE-TWO-LEVELS",
        "CANONICAL-RESIDENTIAL-FOUR-PAVILIONS-AND-CENTRAL-GARDEN",
        "CANONICAL-CHILD-GREEN-INTERFACE",
        "CANONICAL-SEPARATE-SERVICE-ACCESS",
        "CANONICAL-COVERED-EXTERNAL-CIRCULATION",
    ]
    parti_option = (
        "USER_DIRECTED: exactly four canonical boards govern implantation, four "
        "residential pavilions around the protected garden, the public two-level "
        "administrative block, child-green interface, separate services and covered links."
    )
    parti_rationale = (
        "The current user direction explicitly names all four canonical board images "
        "as authority for geometry, organization, parti and spatial relationships. "
        "The official program PDF remains authoritative for capacity, quantities and "
        "areas. This decision fixes the architectural parti only; it does not claim "
        "verified parcel fit, topography, regulatory approval, geometric acceptance "
        "or visual regression."
    )
    parti_decision = DecisionRecord(
        decision_id=PARTI_DECISION_ID,
        topic="USER_DIRECTED_CANONICAL_PARTI",
        alternatives=[
            "Four residential pavilions around a protected garden, with separate public administration and service blocks",
            "AMANDA-RUN-001-S01 linear bar, explicitly superseded by user direction",
        ],
        selected_option=parti_option,
        rationale=parti_rationale,
        source_refs=source_refs,
        confidence=1.0,
        affected_requirements=affected,
        selection_authority=SelectionAuthority.USER_DIRECTED,
        timestamp=timestamp,
        supersedes=PREVIOUS_CANONICAL_PARTI_DECISION_ID,
        approval_hash=compute_approval_hash(
            selected_option=parti_option,
            rationale=parti_rationale,
            source_refs=source_refs,
            affected_requirements=affected,
        ),
        validation_status=ValidationStatus.VERIFIED,
        revision_procedure=(
            "A further parti change requires explicit new user direction and a new "
            "decision bound to all four current board hashes and the official program PDF hash."
        ),
        review_status=ReviewStatus.AMANDA_REVIEW_PENDING,
        selection_kind=SelectionKind.EVIDENCE_BACKED,
        adoption_status="USER_DIRECTED_FOUR_BOARD_CANONICAL_REFERENCE",
        rejected_options=["AMANDA-RUN-001-S01 linear bar"],
    )

    detail_refs = [
        *source_refs,
        f"decision:{parti_decision.decision_id}#approval_hash={parti_decision.approval_hash}",
        "project/site/missing-data.yaml#parcel-boundary-and-topography-unverified",
    ]
    detail_rationale = (
        "The normalized study follows the board topology: three sleeping pavilions "
        "occupy the northwest, southwest and southeast sides of the central garden; "
        "the communal/refectory pavilion is northeast; their covered paths bend "
        "around the garden. Administration stays on the public edge in two levels, "
        "services keep a separate access, and the child sector interfaces with green. "
        "The exact 20-person room and outdoor areas reconcile, and structural parti "
        "QA passes. Coordinates are normalized reference geometry, not survey data. "
        "The earlier S01 normalized candidate is superseded by this content-bound "
        "geometry revision and no Revit geometry was written from S01. Site fit, "
        "canonical geometric acceptance, and required stage visual regressions "
        "remain pending, so S02 is not BIM-eligible."
    )
    detail_decision = DecisionRecord(
        decision_id=SELECTION_DECISION_ID,
        topic=SELECTION_TOPIC,
        alternatives=[
            "PROVISIONAL_ASSUMPTION: board-aligned normalized pavilions and curved covered paths around a protected central patio",
            "Reuse of the superseded linear R12 geometry, prohibited",
        ],
        selected_option=SELECTED_OPTION,
        rationale=detail_rationale,
        source_refs=detail_refs,
        confidence=0.5,
        affected_requirements=affected,
        selection_authority=SelectionAuthority.AGENT_DELEGATED,
        timestamp=timestamp,
        supersedes=PREVIOUS_CANONICAL_DETAIL_DECISION_ID,
        approval_hash=compute_approval_hash(
            selected_option=SELECTED_OPTION,
            rationale=detail_rationale,
            source_refs=detail_refs,
            affected_requirements=affected,
        ),
        validation_status=ValidationStatus.BLOCKED_BY_INPUT,
        revision_procedure=(
            "A material layout change creates a new solution ID and approval hash; "
            "first reconcile site inputs, pass canonical geometric acceptance, and "
            "re-run applicable visual and BIM gates."
        ),
        review_status=ReviewStatus.AMANDA_REVIEW_PENDING,
        selection_kind=SelectionKind.PROVISIONAL_ASSUMPTION,
        fact_class=FactClass.DESIGN_HYPOTHESIS,
        verification_required=True,
        adoption_status="PROVISIONAL_PENDING_CANONICAL_GEOMETRIC_ACCEPTANCE",
        rejected_options=["Reuse of superseded AMANDA-RUN-001-S01 geometry"],
    )

    geometry = {
        "type": "CanonicalPavilionDesignGeometry",
        "layout_hash": layout.content_hash,
        "supersedes_provisional_solution_id": "AMANDA-RUN-002-PAVILION-S01",
        "supersedes_provisional_decision_id": PREVIOUS_CANONICAL_DETAIL_DECISION_ID,
        "parti_selection_authority": SelectionAuthority.USER_DIRECTED.value,
        "detailed_variant_authority": SelectionAuthority.AGENT_DELEGATED.value,
        "parti_decision": {
            "decision_id": parti_decision.decision_id,
            "approval_hash": parti_decision.approval_hash,
        },
        "canonical_reference": {
            "status": profile.status,
            "images": [
                {"path": image, "sha256": digest}
                for image, digest in zip(
                    profile.canonical_images, profile.source_hashes, strict=True
                )
            ],
        },
        "canonical_source_hashes": list(profile.source_hashes),
        "program": program,
        "program_source_sha256": layout.parameters["program_source_sha256"],
        "coordinate_basis": layout.coordinate_basis,
        "site_fit_status": layout.site_fit_status,
        "geometry_origin": "CANONICAL_PAVILION_RECONSTRUCTION",
        "superseded_source_reused": False,
        "blocks": [
            {
                "component_id": block.component_id,
                "role": block.role,
                "storeys": block.storeys,
                "footprint_wkt": block.footprint.wkt,
                "floor_footprints_wkt": {
                    str(level): polygon.wkt
                    for level, polygon in sorted(block.floor_footprints.items())
                },
            }
            for block in layout.blocks
        ],
        "rooms": [
            {
                "logical_id": room.logical_id,
                "sector_id": room.sector_id,
                "component_id": room.component_id,
                "level": room.level,
                "net_area_m2": room.net_area_m2,
                "accessible": room.accessible,
                "polygon_wkt": room.polygon.wkt,
            }
            for room in layout.rooms
        ],
        "external_spaces": [
            {
                "logical_id": space.logical_id,
                "component_id": space.component_id,
                "area_m2": space.area_m2,
                "polygon_wkt": space.polygon.wkt,
            }
            for space in layout.external_spaces
        ],
        "covered_connectors": [
            {
                "connector_id": path.connector_id,
                "from_component": path.from_component,
                "to_component": path.to_component,
                "footprint_wkt": path.footprint.wkt,
                "centerline": [list(point) for point in path.centerline],
            }
            for path in layout.covered_connectors
        ],
        "footprint_wkt": layout.footprint.wkt,
        "central_garden_wkt": layout.central_garden.polygon.wkt,
        "accounting": dict(layout.accounting),
        "canonical_qa": [
            {
                "check_id": item.check_id,
                "status": item.status,
                "evidence": item.evidence,
            }
            for item in checks
        ],
    }
    solution = DesignSolution(
        solution_id=active_solution_id,
        run_id=generation_run,
        seed=0,
        requirements_version=REQUIREMENTS_VERSION,
        site_version=SITE_VERSION,
        engine_version=ENGINE_VERSION,
        archetype=SELECTION_ARCHETYPE,
        geometry=geometry,
        metrics=MetricSet(
            program_compliance=1.0,
            evidence=[
                "626 m2 internal room instances and 260 m2 external program reconcile exactly",
                "Other performance dimensions are not scored before canonical geometric acceptance and verified site inputs",
            ],
        ),
        hard_violations=[],
        soft_penalties={},
        parents=[generation_run],
        status=DesignStatus.CANDIDATE,
        program_person_capacity=int(program["people"]),
        selection_authority=SelectionAuthority.AGENT_DELEGATED,
        decision_evidence=detail_decision,
        review_status=ReviewStatus.AMANDA_REVIEW_PENDING,
    )
    if solution.approval_hash != compute_design_approval_hash(solution):
        raise SelectionError(
            "canonical solution approval hash does not bind its content"
        )
    if solution.bim_eligible:
        raise SelectionError(
            "canonical solution must remain gated before BIM-00 and geometric acceptance"
        )
    return Selection(
        decision=detail_decision,
        solution=solution,
        layout_hash=layout.content_hash,
        parti_decision=parti_decision,
    )


def build_canonical_selection(
    layout: CanonicalPavilionLayout,
    profile: CanonicalReferenceProfile,
    *,
    generation_run: str,
    timestamp: str,
) -> Selection:
    """Build user-directed parti and delegated, still-provisional detail records."""
    return _build_canonical_selection(
        layout,
        profile,
        generation_run=generation_run,
        timestamp=timestamp,
    )


def build_selection(
    layout: CanonicalPavilionLayout,
    *,
    generation_run: str,
    timestamp: str,
    profile: CanonicalReferenceProfile | None = None,
) -> Selection:
    """Build only the active canonical selection; reject legacy geometry."""
    if not isinstance(layout, CanonicalPavilionLayout):
        raise SelectionError(
            "the active selection builder rejects legacy linear layouts"
        )
    if profile is None:
        raise SelectionError(
            "canonical selection requires its hashed reference profile"
        )
    return build_canonical_selection(
        layout,
        profile,
        generation_run=generation_run,
        timestamp=timestamp,
    )


__all__ = [
    "LEGACY_SELECTION_ARCHETYPE",
    "LEGACY_SELECTION_DECISION_ID",
    "LEGACY_SELECTION_SOLUTION_ID",
    "PARTI_DECISION_ID",
    "PREVIOUS_CANONICAL_DETAIL_DECISION_ID",
    "PREVIOUS_CANONICAL_PARTI_DECISION_ID",
    "SCHEMA_VERSION",
    "SELECTED_OPTION",
    "SELECTION_ARCHETYPE",
    "SELECTION_DECISION_ID",
    "SELECTION_SOLUTION_ID",
    "STALE_SELECTION_SOLUTION_ID",
    "Selection",
    "SelectionError",
    "build_canonical_selection",
    "build_selection",
    "legacy_selection_history",
]
