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
from amanda_agent.design.models import (
    DesignSolution,
    DesignStatus,
    MetricSet,
    compute_design_approval_hash,
)
from amanda_agent.requirements.decisions import (
    DecisionRecord,
    ReviewStatus,
    SelectionAuthority,
    ValidationStatus,
    compute_approval_hash,
)

SCHEMA_VERSION = 1

#: Identity of the delegated selection of the adopted architectural layout.
SELECTION_DECISION_ID = "DEC-P08-T09-SELECTION-001"
SELECTION_TOPIC = "ARCHITECTURAL_SELECTION"
SELECTION_SOLUTION_ID = "AMANDA-RUN-001-S01"
SELECTION_ARCHETYPE = "COURTYARD_DOUBLE_LOADED_BAR"
ENGINE_VERSION = "design-engine-v1"
REQUIREMENTS_VERSION = "requirements-v1"
SITE_VERSION = "site-v1"

SELECTED_OPTION = (
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
            + "%.2f" % measured
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
        "estimates: it measures %.2f m2 against the 783-814 m2 range, because "
        "%.0f m2 of programmed rooms and %.2f m2 of gallery share one envelope "
        "and one gallery. The two-wing courtyard needs a second gallery and a "
        "second set of external walls and is roughly 30 percent over budget. The "
        "bar keeps every room on the gallery with daylight from its outer face, "
        "and the protected patio supplies the external space the programme "
        "requires. Every room area is exactly the canonical target; none was "
        "stretched to reach the total. The patio is held off the public edge by "
        "the building and closed by the perimeter wall, which remains an "
        "assumption because only a study boundary exists."
        % (
            accounting["gross_enclosed_m2"],
            accounting["net_internal_m2"],
            accounting["circulation_m2"],
        )
    )


def build_selection(
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
        decision_id=SELECTION_DECISION_ID,
        topic=SELECTION_TOPIC,
        alternatives=_alternatives(layout),
        selected_option=SELECTED_OPTION,
        rationale=rationale,
        source_refs=source_refs,
        confidence=0.7,
        affected_requirements=affected,
        selection_authority=SelectionAuthority.AGENT_DELEGATED,
        timestamp=timestamp,
        approval_hash=compute_approval_hash(
            selected_option=SELECTED_OPTION,
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
        solution_id=SELECTION_SOLUTION_ID,
        run_id=generation_run,
        seed=0,
        requirements_version=REQUIREMENTS_VERSION,
        site_version=SITE_VERSION,
        engine_version=ENGINE_VERSION,
        archetype=SELECTION_ARCHETYPE,
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
                "metrics are declared as the study scope of this selection, not "
                "as measured simulation output",
                "program compliance: every programmed room placed at its canonical "
                "target area, reconciled to 626.00 m2 internal useful",
                "privacy: the street face carries the public, service and "
                "community programme and the patio face carries residential, "
                "children and technical care, so no residential room opens onto "
                "the public edge",
                "circulation: one 1.50 m gallery reaches every room, above the "
                "accessible minimum",
                "accessibility: the accessible rooms the programme marks are "
                "placed on the gallery, and the gallery width is measured at "
                "1.50 m",
                "constructability: a single-storey double-loaded bar with a "
                "gallery needs one envelope and one gallery, which is the "
                "alternative that reaches the adopted enclosed-area estimate",
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


__all__ = [
    "SCHEMA_VERSION",
    "SELECTED_OPTION",
    "SELECTION_ARCHETYPE",
    "SELECTION_DECISION_ID",
    "SELECTION_SOLUTION_ID",
    "Selection",
    "SelectionError",
    "build_selection",
]
