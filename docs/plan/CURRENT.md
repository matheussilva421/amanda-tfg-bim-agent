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
bounded R04 geometry listed under P5 below; R05 remains excluded. Its evidence
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

P5 is `PASS_WITH_WARNINGS`. The official PDF remains the authority for 20 people,
626 m² internal and 260 m² external. Five modelled external areas are 80/80/30/30/40
m². Coordinates remain local/unsurveyed; the admin board label discrepancy
(+37.407 m² / +18.7%), Nível 2 at 4.0 m versus upper plate at 3.2 m, and missing
room/function assignments remain open. No official area was changed.

Live closeout confirmed Horizun 1.3.3 healthy, Revit 2027 build 27.2.0.39,
73/73 registered commands and 80/80 tools. The exact RUN-003 target is active;
the open anchor document is also present, with zero other clients. The exclusive
RUN-003 lease was released after persistence verification. Save returned target
SHA-256 `33a99c7c760125da434017210b7ea2d506a3914ae59e002769a14138cca27b49`
(4,952,064 bytes); the separate checkpoint and corrected manifest verify. Exact
path close/reopen completed without upgrade and fresh typed queries confirmed
the contents. Five site-data blockers remain. No R05 operation occurred.
## P5 — R04 Revit

`P5-T01` is complete with `PASS_WITH_WARNINGS`; see the current execution
evidence above. `P6-T01` is next: accept the saved R04 geometry against all four
canonical boards and close CANON-011. The current image is a cropped wireframe
support capture; six earlier captures predate the latest geometry save. P6
remains pending for visual review, room/function reconciliation, admin area and
level discrepancies, and unresolved site inputs. R05 remains excluded and is
not authorized by this continuation.

## P6 — R04 visual/geometric acceptance

Compare real Revit output to all four boards. R05 is blocked until PASS.

## P7 — Detailed production

Run R05 through R13 with required regression gates.

## P8 — QA/RC

Run R14, R15 cold reopen, and exports.

## P9 — GOLDEN

Run R16 only after every required gate and documented deviation passes.

P0 through P5-T01 are closed. `PROJECT_STATE.yaml` and `state/task-graph.yaml`
point to P6-T01 as the next task. Historical plans are archive material in Git
history, not a second instruction source.
