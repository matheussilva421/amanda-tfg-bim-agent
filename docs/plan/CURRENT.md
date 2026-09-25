# Amanda TFG BIM Agent — Current Implementation Plan

## P0 — Repository Recovery (complete)

Repository recovery closed on 2026-09-24. The recovery report records branch consolidation, preservation tags, the single worktree, document migration, source/evidence/RVT retention, focused validation, and remote verification. No Revit/model action occurred during P0.

## P1 — Four-board reconciliation (P1-T01 complete)

P1-T01 binds exactly the four canonical boards and reconciles implantation, administration floors, residential pavilion membership, the curved service/capacitation courtyard, child-sector contents, and the official program. Its report records unresolved board-to-program differences without changing official areas. No Revit work or new solution identity was created.

## P2 — New canonical solution

P2-T01 is the next task: assign a new solution identity after stale S02 and bind it to all four canonical board hashes and the official program source hash. It remains pending; do not start it automatically from P1-T01 closeout.

## P3 — Canonical QA and approval

Pass all non-Revit four-board hard checks; generate new layout and approval hashes.

## P4 — BIM-00

Authorize only the exact new solution and target.

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

P0 and P1-T01 are closed. `PROJECT_STATE.yaml` is the formal pointer and now names pending P2-T01. Historical plans are archive material in Git history, not a second instruction source.
