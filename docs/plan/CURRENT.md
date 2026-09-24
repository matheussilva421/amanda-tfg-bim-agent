# Amanda TFG BIM Agent — Current Implementation Plan

## P0 — Repository Recovery (complete)

Repository recovery closed on 2026-09-24. The recovery report records branch consolidation, preservation tags, the single worktree, document migration, source/evidence/RVT retention, focused validation, and remote verification. No Revit/model action occurred during P0.

## P1 — Four-board reconciliation

Fix every three-board assumption. Reconcile administration floors, residential pavilion membership, services curved/patio geometry, implantation, and child-sector implementation. Begin with P1-T01 after recovery validation.

## P2 — New canonical solution

Create a new solution identity after stale S02. Bind it to all four canonical board hashes and the official program source hash.

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

P0 is closed. `PROJECT_STATE.yaml` is the formal next-task pointer and now sets P1-T01 as ready. Historical plans are archive material in Git history, not a second instruction source.
