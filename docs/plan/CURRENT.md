# Amanda TFG BIM Agent — Current Implementation Plan

## P0 — Repository Recovery (complete)

Repository recovery closed on 2026-09-24. The recovery report records branch consolidation, preservation tags, the single worktree, document migration, source/evidence/RVT retention, focused validation, and remote verification. No Revit/model action occurred during P0.

## P1 — Four-board reconciliation (P1-T01 complete)

P1-T01 binds exactly the four canonical boards and reconciles implantation, administration floors, residential pavilion membership, the curved service/capacitation courtyard, child-sector contents, and the official program. Its report records unresolved board-to-program differences without changing official areas. No Revit work or new solution identity was created.

## P2 — New canonical solution (P2-T01 complete)

P2-T01 assigned `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`, bound to exactly the four current canonical board hashes, the official program PDF hash, and the P1-T01 reconciliation report identity. The machine-readable record is `project/requirements/canonical-solution-identity.yaml`; `PROJECT_STATE.selected_design` remains null. This identity-only task created no layout or approval hash and authorized no BIM-00 or Revit write.

## P3 — Canonical QA and approval

P3-T01 generated offline candidate `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`, bound to the four boards, official program PDF, and P1-T01 report. The focused gate passed 74 tests; emitted QA is 17 PASS, 0 FAIL, CANON-011 BLOCKED. Direct builder calls revalidate the persisted identity against live sources, and the QA guard requires unique CANON-001..018 IDs. Independent re-review closed both code findings; final state review found no critical/important findings and its minor phase-edge test gap is closed. The candidate stays provisional, unselected, and ineligible for BIM; no Revit call or R04/R05 work occurred. Evidence: `docs/reports/P3-T01-canonical-qa-and-approval.md`.

## P4 — BIM-00

`P4-T01` establishes BIM-00 evidence for the exact new solution and target; it
depends on P3-T01. BIM-00 remains an evidence/authorization gate. In the
2026-09-26 user-directed continuation, a PASS immediately authorized the
bounded R04 geometry listed under P5 below; R05 was excluded at that milestone. Its evidence
must bind the `solution_id`, `layout_hash`, content `approval_hash`, exactly
four canonical board hashes, official program PDF SHA-256, target RVT path and
SHA-256, a separate checkpoint path and matching SHA-256, repository commit
SHA, and the `PROJECT_STATE.yaml` revision and raw-file SHA-256. Each binding
is compared to the active expected value; an unbound or mismatched value fails
closed. Required live checks include the writer lease, checkpoint, historical
R12 exclusion, canonical references, capability registry, Revit provider,
units, site-coordinate mode, family strategy, canonical selection, and
official program source. BIM-00 itself does not execute a Revit operation; the
explicit user continuation authorized R04 after its PASS and did not authorize
R05.

**Completed status (2026-09-26):** `P4-T01` passed BIM-00 against the exact
RUN-003 target, pre-R04 checkpoint, four canonical sources, official program,
repository commit, and state revision. The user then explicitly authorized
continuing to R04. The original seven-mass baseline remains, and the continuation
added 18 typed elements (14 floors, four roofs): two administrative plates, five
program-area site surfaces, four roofed open-sided residential connectors, and
three separately marked access routes. Typed post-reopen query returned 25
elements, complete coverage, zero unreadable. See
`docs/reports/P4-T01-run003-r04-geometry-completion-2026-09-26.md` and
`revit/production/evidence/AMANDA-RUN-003-R04/r04-spatial-model-evidence.json`.

P5 closed as `PASS_WITH_WARNINGS`. Its closeout recorded the admin board-area
difference and upper-plate offset that were present at that checkpoint. During
P6-T01, the reversible study envelope was reconciled to 10×20 m per floor and
the upper plate aligned to Nível 2 at 4.0 m; the official PDF remained unchanged.
The 20-person, 626 m² internal and 260 m² external program remains authoritative,
with five modeled external areas at 80/80/30/30/40 m². Internal room/function
assignments are still not modeled, and coordinates remain local/unsurveyed.

At P5 closeout, Horizun 1.3.3 was healthy and the exact RUN-003 target was
saved, reopened, and read back. That checkpoint was superseded by the P6
reconciliation recorded below. Five site-data blockers remain; no R05 operation
occurred.
## P5 — R04 Revit

`P5-T01` is complete with `PASS_WITH_WARNINGS`. P6-T01 reconciled the
administrative envelope and levels and refreshed the checkpoint/readback.

## P6 — R04 visual/geometric acceptance (`PASS`)

P6-T01 has updated the real RUN-003 admin envelope and levels, saved and
cold-reopened a new checkpoint, and refreshed typed readback and visual capture
evidence. `CANONICAL_DEVIATION-ADM-001` is resolved for this reversible study;
no Amanda approval or official-program change is claimed. CANON-011 passes for
the normalized STUDY's four-board spatial topology. R06 owns internal layout;
R08 owns Revit Room creation and area readback. Five site-data gaps continue to limit
only claims dependent on surveyed or cadastral inputs. The focused
child/playground image from the prior checkpoint remains reference-only; current
typed bounds and the current full-implantation capture support that relation.

## P7 — Detailed production

DEC-010 records historical conditional authorization after P6 PASS. The current
user authorization covers `P7-T01/R05` only. Each later stage requires its own
task gate; completing R05 does not start R06. Each authorized stage requires its
own focused test, typed readback, independent verification, QA, evidence,
checkpoint where specified, commit and push before any later stage.

| Task | Stage | Scope | Hard predecessor |
|---|---|---|---|
| P7-T01 | R05 | Architectural shell: exterior walls, floor plates, roofs, voids and covered circulation | P6-T01 |
| P7-T02 | R06 | Internal rooms/layout, reconciled exactly to P1-T01 and the official program PDF | P7-T01 |
| P7-T03 | R07 | Hosted doors, windows and openings; verify hosts and access | P7-T02 |
| P7-T04 | R08 | Revit Rooms, exact room IDs/counts/areas and program reconciliation schedule | P7-T03 |
| P7-T05 | R09 | Accessibility geometry and evidence; unsupported numeric claims remain UNVERIFIED/BLOCKED | P7-T04 |
| P7-T06 | R10 | Functional furniture/equipment for use and scale checks | P7-T05 |
| P7-T07 | R11 | Landscape, preserving the five official exterior areas totaling 260 m² | P7-T06 |
| P7-T08 | R12 | Study materials, without changing canonical design decisions | P7-T07 |
| P7-T09 | R13 | Plans, sections, elevations, schedules, sheets and explicit STUDY labeling | P7-T08 |

### P7-T02 / R06 prepared input — Amanda administrative direction (2026-09-29)

A new USER_DIRECTED administrative layout input is recorded in `docs/inputs/2026-09-29-amanda-administrative-layout.md`, with the implementation plan in `docs/plan/P7-T02-R06-administrative-layout-2026-09-29.md` and tracking issue #1. It preserves official program quantities/areas while fixing nominal room proportions and the intended two-floor arrangement. The upper 5 m² support/archive is derived rather than a second official REQ-04-06; the 10 m² veranda is semi-open/non-official internal useful area. The conflicting dark CAD sketch is not quantitative authority.

This preparation does **not** start or authorize P7-T02. P7-T01/R05 remains the hard predecessor and the current execution gate.

The current P7 authorization is limited to this normalized RUN-003 STUDY and
`P7-T01/R05`. R06 and later stages are not authorized by this task; completing
R05 does not start R06. This does not establish personal Amanda approval,
verified site fit, FINAL status, R14–R16, or a GOLDEN release.

## P8 — QA/RC

Run R14, R15 cold reopen, and exports.

## P9 — GOLDEN

Run R16 only after every required gate and documented deviation passes.

P0 through P6-T01 are closed. `PROJECT_STATE.yaml` and `state/task-graph.yaml`
point to P7-T01 as the next task. Historical plans are archive material in Git
history, not a second instruction source.
