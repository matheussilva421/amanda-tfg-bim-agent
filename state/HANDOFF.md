# Current Handoff

## Formal state and safety

Repository recovery (P0) remains active. `PROJECT_STATE.yaml` points to
`RECOVERY-VALIDATE`; do not activate P1 until Task 13's final validation and
remote check are complete. The recovery anchor is
`pre-repository-recovery-2026-09-24`; the superseded P08 offline candidate is
preserved under `superseded-p08-t08-concept-offline-2026-09-24`.

No Revit or model work is in scope during P0. Preserve `.recovery/` until Task
13 transfers its evidence. Preserve the private program and TFG PDFs locally;
they are intentionally ignored by Git.

## Current documentation flow

Start with `START_HERE.md`, then read `AGENTS.md`, `PROJECT_STATE.yaml`,
`docs/spec/CURRENT.md`, `docs/plan/CURRENT.md`, `docs/decisions/DECISIONS.md`,
and this handoff. The four active canonical images are normalized under
`docs/source/canonical/`; prior board images remain byte-identical under the
historical source path. Source and evidence inventories are covered by the
immutable manifest plus `SOURCE_MANIFEST.json`.

## Completed work

- Tasks 1–6 are complete and pushed; the Task 6 close commit is
  `6e9995765316c321e6820c5f0cde23638dc07b46`.
- Task 7 normalized the four canonical board paths, preserved historic board
  images and source evidence, and reconciled the source validators. Its focused
  gates passed 18/18; supplemental source-manifest tests passed 5/5. Independent
  review approved the work after a direct ingest-validator rejection test was
  added. Task 7's implementation commit is
  `f5da48d5c25f7f2b33e3a09c7fe0a7c30485e27a`; the pushed documentation closeout
  is `fe1e5ea287cfb5dec75877a278349a7ab519e1ec`.
- Task 7's additional historical check found a pre-existing digest mismatch in
  `test_p08_freeze_binds_versions_and_current_file_hashes`: 4 passed, 1 failed.
  `decision-register.yaml` was unchanged by Task 7; retain this failure for the
  final report rather than rebinding the historical freeze.

## Task 8 complete

The hygiene test for absence of legacy plan/spec/handoff trees was added and
first run RED as expected. The old root instructions, 13 child plans, one
legacy spec, 88 notes/handoffs, 33 package-review artifacts, stale 2026-09-16
handoff report, and all four tracked plan ZIP archives have now been removed
from the active tree. Their blobs remain in the safety tag/Git history.
Independent review confirmed all four ZIP hashes and manifests, then requested
two fixes: one stale Blender report route and missing final gate evidence. Both
are fixed and recorded. A follow-up review found one cleanup-script comment
still naming a deleted plan; a hygiene test caught it RED, the route was
removed, and the GREEN result is recorded. Two standalone tool-lab handoffs
were removed after their findings were confirmed in maintained README/task
history; the detailed P02-T15 record was renamed as evidence and remains linked
from its result report. Final review approved the staged diff.

The ignored 13-file text-extraction cache was moved to
`project/provenance/extracted/source-extracts/`; its manifest paths were
updated and all records resolve. Original source files remain in the source
tree. `.gitignore`, `AGENTS.md`, the current spec and decisions, source
inventory routing, task registry plan paths, session/reboot handoff writers,
repository hygiene tests, historical report pointers, this handoff, and the
recovery report are updated. The final focused suite passed 73/73 and Ruff
passed across changed operational Python and focused test files. Commit
`06da0b24170a55cf0fa3bb705ce07d98082ec907` is on `main` and `origin/main`.
Elevated status confirmed 36 RC01 files intact and one worktree. The only
remaining named handoff is this file. No Revit/model action occurred. See
`docs/reports/repository-recovery.md` for the command, detailed evidence, and
known historical freeze mismatch.

## Exact resume

Begin Task 9 by reading its recovery-plan section and classifying the full RVT
inventory. Verify the historical linear R12 hash before any move; keep
`revit/production/working/CURRENT.rvt` absent, never delete `UNKNOWN`, and do
not open Revit or mutate a model. Commit/push each reviewed task. Continue
sequentially through Tasks 10–13; only Task 13 may remove `.recovery/` or set
the formal next task to P1-T01.

## Git checkpoint

Task 8 started at `fe1e5ea287cfb5dec75877a278349a7ab519e1ec` and closed at
`HEAD = main = origin/main = 06da0b24170a55cf0fa3bb705ce07d98082ec907`, with
exactly one worktree. The workspace still contains the intentional untracked
`.recovery/` evidence.
