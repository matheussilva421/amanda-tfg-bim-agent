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
`5d95d12ce87559d0e986ce4db1dc880c550c8534` is on `main` and `origin/main`.
Elevated status confirmed 36 RC01 files intact and one worktree. The only
remaining named handoff is this file. No Revit/model action occurred. See
`docs/reports/repository-recovery.md` for the command, detailed evidence, and
known historical freeze mismatch.

## Task 9 complete; independent review approved

The independent review approved the inventory, hashes, retention decisions,
and recorded test evidence. It found one stale handoff status; the status was
corrected and the scoped re-review approved the correction. Commit
`c4adceb70c3824dba50c8ef3010472b94664b6f4` is on `main` and was pushed to
`origin/main`; fresh remote verification confirmed all four refs match.
The report/handoff closeout commit `1290ba3e83ed44fee4a447a7b6e6d6aad92604d1`
was also pushed and verified against the remote.

The 112-row RVT baseline is classified: 31 `LAB_FIXTURE`, 4
`CHECKPOINT_R04`, 4 `CHECKPOINT_R06`, 1 `CHECKPOINT_R08`, 1
`HISTORICAL_LINEAR_R12`, and 71 `UNKNOWN`. All `UNKNOWN` files remain
preserved. The historical linear model was moved by path only to
`revit/production/archive/linear-r12-superseded.rvt`; its 4,345,856-byte
SHA-256 remains
`ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29`. The
manifest now sits at `revit/production/archive/manifest.json`. Three byte-
identical S02 working duplicates are in `.recovery/rvt-duplicates/` until
Task 13; the S02 file named by the writer lease remains in place and
`revit/production/working/CURRENT.rvt` remains absent. No Revit process or
model content was opened or modified.

The signed decision register keeps its original historical `source_refs`
string because `approval_hash` binds that value. A proposed path update failed
register validation and was reverted without rebinding the hash; the current
archive path is recorded by the manifest, active selection history, and
recovery report.

Fresh Task 9 checks: R12 path guards 4/4; historical decision source test
1/1; state-store/status-dashboard 10/10; status CLI exited 0 and reported the
existing writer lease as HELD. The full production-runner unit module had
14/15 passing; its unchanged R04 routing fixture expected a lock exception
after the current acceptance gate returns early. The focused path checks passed
when run with `.venv/Scripts/python.exe -m pytest`; the bare `pytest.exe`
launcher could not import the local `scripts` namespace. Independent review
approved, implementation commit `c4adceb70c3824dba50c8ef3010472b94664b6f4`
and closeout commit `1290ba3e83ed44fee4a447a7b6e6d6aad92604d1` were pushed,
and remote main matched after the closeout push. `PROJECT_STATE.yaml` remains
at `RECOVERY-VALIDATE`.

## Task 10 complete; independent review approved

The 43-path design-engine baseline is fully classified in
`.recovery/design-engine-classification.json`: 4 active generator configs,
37 stale-evidence fixtures (including all seven S02 artifacts), 2 invalid
predecessor run logs recoverable from the safety tag, and 0 unknown paths.
Only the two invalid predecessor logs were removed from the active tree; their
SHA-256 values and exact tag recovery are in
`docs/reports/repository-recovery.md`. `design-engine/current/` remains absent.

The signed decision register remains unchanged. Its root-level S02 source_ref
target, `design-engine/runs/AMANDA-RUN-002-PAVILION/solution.json`, is absent
from the worktree, baseline, and recovery tag. Record it as a pre-existing
dangling reference; do not rehash the register or fabricate the target. The
nested S02 finalist artifacts remain stale evidence.

Task 10 focused tests: 72 passed, 0 failed across `test_design_refine.py`,
`test_p08_t07_environmental_pass.py`, `test_bim_solution_compiler.py`,
`test_production_layout_bim.py`, `test_build_canonical_pavilion_run.py`,
`test_canonical_reference.py`, `test_canonical_pavilion_layout.py`,
`test_canonical_qa.py`, and `test_production_selection.py`. An expanded
10-module run including `test_canonical_state_migration.py` passed 76/76. No
full suite or Revit/model action occurred. Independent review approved the
scoped changes with no actionable findings. Commit and push this task, confirm
remote `main`, then start Task 11. Do not start it before the Task 10 closeout
push is verified.

## Exact resume

Commit and push the reviewed Task 10 report/handoff and two explicit
design-engine removals. Verify `main` matches `origin/main`. Next execute Task 11: preview
ignored files with `git clean -ndX`, classify candidates, and remove only the
approved cache/temp paths by explicit path. Do not use `git clean` to delete;
preserve gate evidence, source files, RVTs, and release artifacts. Continue
Tasks 12–13 in order; only Task 13 may remove `.recovery/` or set the formal
next task to P1-T01.

## Git checkpoint

Task 9 implementation commit: `c4adceb70c3824dba50c8ef3010472b94664b6f4`;
report/handoff closeout commit: `1290ba3e83ed44fee4a447a7b6e6d6aad92604d1`.
Both were pushed. After the closeout push, a fresh `git ls-remote` check
confirmed `HEAD = main = origin/main` at
`1290ba3e83ed44fee4a447a7b6e6d6aad92604d1` and exactly one worktree.
`.recovery/` and the three quarantined RVT duplicates remain local and are
intentionally preserved for Task 13.
