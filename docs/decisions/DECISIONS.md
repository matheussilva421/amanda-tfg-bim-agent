# Active Decisions

## DEC-001 — Pavilion parti

Status: ACTIVE
Authority: USER_DIRECTED

The target parti follows the pavilion/block organization in the four canonical boards. The historical linear bar is superseded. This decision does not select a new model identity; that follows P1–P3 reconciliation and approval.

## DEC-002 — Source authority

Status: ACTIVE

Boards govern architectural geometry and organization. `docs/source/programa_necessidades.pdf` governs official quantitative program.

## DEC-003 — Four-board source set

Status: ACTIVE

Exactly four canonical boards form the current architectural source set. Their byte hashes are recorded in the recovery report and current specification; the normalized paths are verified in Task 7.

## DEC-004 — S02 stale

Status: ACTIVE

`AMANDA-RUN-002-PAVILION-S02` is `STALE_BY_CANONICAL_REFERENCE_EXPANSION` and may not advance to R05.

## DEC-005 — Historical storage

Status: ACTIVE

Git history and preserved tags are the archive for reproducible superseded operational documents. Superseded plans and handoffs do not remain active merely for convenience.

## DEC-006 — Delegated design research

Status: ACTIVE

Within an explicitly authorized task, the agent may research, compare, and select reversible design approaches inside verified source and requirement boundaries. Record the rationale and keep the selection revisable. Amanda's review is a separate human decision; never attribute approval to her without evidence.

## DEC-007 — Technical and academic completion

Status: ACTIVE

A technical `GOLDEN` release does not establish that the academic TFG is complete. Academic authorship, advisor review, defense, and institutional submission have separate owners and evidence. Do not claim `TFG_COMPLETE` while required academic deliverables remain open.

## DEC-008 — P1-T01 program and board reconciliation

Status: ACTIVE
Authority: USER_APPROVED design direction within DEC-006; official quantities remain fixed by the program PDF

The four boards govern spatial organization. The program PDF governs every room count, capacity, and area. The administrative block keeps public intake, technical service and support at ground level; coordination, administration, team, staff facilities and group/multiuse rooms are upstairs. Ground-floor SEC-05 Copa de apoio comunitário (8 m²) and Sanitário acessível (5 m²) retain their official IDs and areas while following the exact locations shown on Board 02; Board 04's larger/multiple depictions do not create duplicate rooms. The single SEC-04 Arquivo e apoio técnico (5 m²) is placed on the ground floor; Board 02's repeated upper label does not create a second room. Three independent sleeping pavilions use the official bedroom mix and exactly five common plus one accessible bathroom. Board 03's sixth common-bathroom cell is schematic and non-additive; the modeled split stays 2/2/1 and the extra cell is not mapped to an official room because the board does not identify it unambiguously. The fourth pavilion holds the communal living/dining/support rooms around the free protected patio. The child pavilion sits west/center-west beside the playground and carries all four official child-sector rooms.

The southeast service/capacitation block uses a curved composition around an unprogrammed court. Its campus pedestrian entry and cargo entry remain separate. The court is not one of the official external areas. Every SEC-05 and SEC-06 room is assigned once at its PDF area; SEC-05 Copa/Sanitário stay at the Board-02 ground-floor locations while the remaining SEC-05 and SEC-06 service rooms occupy the southeast block. Board-02 duplicate archive labeling and Board-04-only activities, room combinations, area deltas and unlabelled official support rooms remain explicit in `docs/reports/P1-T01-four-board-reconciliation.md`; no extra area or official room is inferred from a board label. The two official 80 m² spaces—protected patio and therapeutic garden—remain distinct.

P1-T01 leaves the selected design identity unset. The signed three-source DEC-CANONICAL-PARTI-001 remains hash-preserved but is formally superseded by DEC-CANONICAL-PARTI-002, which binds all four current board hashes and the official PDF. The old S02 detail entry is superseded; P2 must assign a new solution identity and fresh detail decision before any BIM artifact is emitted.

## DEC-009 — Reversible normalized study selection

Status: ACTIVE — `DEC-CANONICAL-DETAIL-004`

RUN-003 is selected by agent delegation for a reversible, normalized local-reference STUDY. Its coordinates are not surveyed site data. Missing boundary, topography, occupancy/transfer, frontage, and true-north evidence blocks only the dependent parcel and final claims. `AMANDA_REVIEW_PENDING` remains; the content approval hash is not personal approval. P4-T01 passed BIM-00 and persisted the R04 geometry. P6-T01 / CANON-011 now passes for four-board spatial topology; R06 owns internal layout, and R08 owns Revit Room creation and area readback. The Board-02 administrative deviations are `RESOLVED_FOR_STUDY` in `CANONICAL_DEVIATIONS.yaml`, with no personal approval recorded. DEC-010 separately records the user's conditional operational authorization for R05–R13 after P6 PASS.

## DEC-010 — RUN-003 detailed STUDY continuation after P6

Status: ACTIVE — explicit user operational authorization, 2026-09-26

After P6-T01 / CANON-011 reaches PASS against the saved RUN-003 R04 model and
all four current canonical boards, continue in the actual Revit session through
R05–R13 without asking for confirmation between green stage gates. Scope is the
same reversible, normalized local-reference `STUDY`; each stage must preserve
the official PDF program and follow WRITE → independent READ → VERIFY. R06/R08
must reconcile actual Revit Rooms to the official program and P1-T01 crosswalk.

This operational authorization does not claim Amanda's personal approval,
surveyed or cadastral site truth, parcel fit, true north, site availability,
FINAL, R14–R16, or GOLDEN. No GeoNatal research, RC01 modification, S01/S02/R12
reuse, official program change, force push, or ZIP creation is authorized.

## DEC-011 — Amanda-directed administrative layout dimensions

Status: ACTIVE — USER_DIRECTED, 2026-09-29
Authority: USER_DIRECTED for administrative spatial arrangement and nominal dimensional targets; official program PDF remains quantitative authority

Amanda provided a concrete two-floor administrative layout direction for future P7-T02/R06. Ground-floor and upper-floor nominal dimensions are recorded in `docs/inputs/2026-09-29-amanda-administrative-layout.md` and implementation issue #1. The direction is consistent with the current Board-02 functional split and P6 20×10 m normalized-study envelope.

The official program PDF continues to control official room quantities and official areas. The single official REQ-04-06 remains represented once on the ground floor. Amanda's upper `Apoio/Arquivo 5 m²` is retained as a derived architectural support space and must not be counted as a second official REQ-04-06. The protected upper veranda is approximately 10 m², semi-open, and must not be added to the official 626 m² internal useful area.

The dark CAD sketch supplied with the same direction is reference-only for rough adjacency where non-conflicting; its different quantitative labels do not override the official program or Amanda's explicit tables. Nominal dimensions are clear-layout targets that R06 must reconcile against wall thickness, circulation, stair/elevator/core and the verified R05 shell.

This decision prepares R06 only. It does not authorize R06 before P7-T01/R05 passes and does not move doors/windows (R07), formal Revit Rooms/area schedule (R08), or furniture (R10) into R06.
