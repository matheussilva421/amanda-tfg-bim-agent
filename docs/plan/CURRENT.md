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

`P4-T01` establishes BIM-00 evidence and can authorize only the exact new
solution and target; it depends on P3-T01 and excludes R04/R05. Its evidence
must bind the `solution_id`, `layout_hash`, content `approval_hash`, exactly
four canonical board hashes, official program PDF SHA-256, target RVT path and
SHA-256, a separate checkpoint path and matching SHA-256, repository commit
SHA, and the `PROJECT_STATE.yaml` revision and raw-file SHA-256. Each binding
is compared to the active expected value; an unbound or mismatched value fails
closed. Required live checks include the writer lease, checkpoint, historical
R12 exclusion, canonical references, capability registry, Revit provider,
units, site-coordinate mode, family strategy, canonical selection, and
official program source. BIM-00 is an evidence/authorization gate only; it
does not execute an R04/R05 operation.

**Current status:** `P4-T01` is `BLOCKED_BY_INPUT`. DEC-CANONICAL-DETAIL-004
selects RUN-003 for reversible normalized local-reference STUDY through R04;
`AMANDA_REVIEW_PENDING` remains, `bim_eligible=false` remains for detailed/final
production, and CANON-011 awaits real comparison with all four boards. Missing
survey/site inputs constrain their dependent final claims but do not block this
study. BIM-00 still cannot pass: Horizun cannot reach the installed Revit
provider, the writer lease is held for superseded S02, and no exact RUN-003
target/checkpoint is bound. P4-T01 remains the retry pointer; R04 writes stay
blocked until BIM-00 PASS, and R05 stays blocked until CANON-011 PASS. See
`docs/reports/P4-T01-bim00-blocker-report.md`; the selected offline STUDY
snapshot is `design-engine/runs/AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C-study-detail-004/`.

## P5 — R04 Revit

Create canonical massing, save, close, reopen, and query.

## P6 — R04 visual/geometric acceptance

Compare real Revit output to all four boards. R05 is blocked until PASS.

## P7 — Detailed production

Run R05 through R13 with required regression gates.

## P8 — QA/RC

Run R14, R15 cold reopen, and exports.

## P9 — GOLDEN

Run R16 only after every required gate and documented deviation passes.

P0, P1-T01, P2-T01, and P3-T01 are closed. `PROJECT_STATE.yaml` is the
formal task pointer; P4-T01 is `BLOCKED_BY_INPUT` and remains the retry pointer.
Historical plans are archive material in Git history, not a second instruction
source.
