# Current Handoff

## Formal state and safety

Repository recovery (P0), four-board reconciliation (P1-T01), and identity
assignment (P2-T01) are complete. `PROJECT_STATE.yaml` points to pending
`P3-T01`; the last completed task is `P2-T01`. The source-bound identity is
recorded at `project/requirements/canonical-solution-identity.yaml`, while
`selected_design` remains null. The recovery anchor is
`pre-repository-recovery-2026-09-24`; the superseded P08 offline candidate is
preserved under `superseded-p08-t08-concept-offline-2026-09-24`.

P0 completed without Revit/model activity. All recovery evidence is transferred
to `docs/reports/repository-recovery.md`; `.recovery/` was removed after the
RVT and evidence checks. Preserve the private program and TFG PDFs locally;
they are intentionally ignored by Git. Five site conditions (three BLOCKING,
two DEGRADING) remain, and the held writer lease is unchanged. P1-T01 completed
without Revit/model activity. At P1-T01 closeout the solution identity was
unset and S02 was stale; P2-T01 has since assigned the source-bound identity
recorded above.

## P2-T01 closeout — identity only

Assigned `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C` with fingerprint
`4b1275558a6c2c40828dbba1422c0063703c182fd9d7b800b36a448499a073c4`. The
identity binds, in profile order, all four current canonical board hashes, the
official `programa_necessidades.pdf` hash, and the P1-T01 report hash. The
identity-only implementation lives in
`src/amanda_agent/production/canonical_identity.py`; the machine record and
short reconciliation report are `project/requirements/canonical-solution-identity.yaml`
and `docs/reports/P2-T01-canonical-solution-identity.md`.

`SELECTION_SOLUTION_ID` and `PROJECT_STATE.selected_design` remain null;
`approval_hash` is null. No layout, `DesignSolution`, BIM-00, Revit/RVT access or
write, R04, or R05 work occurred. S02 remains
`STALE_BY_CANONICAL_REFERENCE_EXPANSION`. The focused identity, selection,
state, repository-hygiene, and plan-order gate passed **41/41**; changed-file
Ruff is recorded at closeout. `P2-T01` is PASS and `P3-T01` is the next
authorized pending task; P3 was not started.

Focused command:
`.venv/Scripts/python.exe -m pytest tests/unit/test_canonical_solution_identity.py tests/unit/test_production_selection.py tests/unit/test_canonical_state_migration.py tests/project/test_repository_hygiene.py tests/policy/test_plan_order.py -q`
— 41 passed. Changed-file Ruff command:
`.venv/Scripts/ruff.exe check src/amanda_agent/production/canonical_identity.py tests/unit/test_canonical_solution_identity.py tests/unit/test_canonical_state_migration.py tests/project/test_repository_hygiene.py`
— all checks passed. Scoped `git diff --check` passed. TDD evidence: identity
tests first failed because the module was absent; after implementation they
reached 11 passed/1 failed only because the required persisted manifest had not
yet been generated. An independent review found that an internally consistent
but incorrect board or reconciliation hash could reach the writer. A new RED
case reproduced it; the writer now recomputes the live identity first, and
both source-hash regressions pass. The state-routing regressions failed against
the old P2 pointer and passed after the formal P3 transition. The reviewer
recheck then found stale wording from the P1 closeout; the handoff now labels it
as historical. Final independent read-only review returned **APPROVE**, noting
the writer/source binding fix, exact source hashes, null selection/approval,
and P3-T01 as the next pending task. P2 implementation commit on `main`:
`aa1975a` (`feat: assign canonical solution identity P2-T01`). The state-only
closeout will set `last_verified_commit` to this tested implementation commit.

RC01 preflight used read-only inspection. The normal sandbox listed 34 tracked
paths as deleted because it could not enumerate the protected directory. An
authorized elevated read found 36 physical files: all 34 tracked files match
the Git index after clean filters; the other two are ignored `.rvt`/`.rte`
files. This is an ACL visibility issue, not repository data loss. No RC01 path
was restored, edited, staged, or included in this task.

To resume, start from `main`, read the required current documents in the order
in `START_HERE.md`, verify `PROJECT_STATE.yaml` and the P3-T01 dependency, then
execute only P3-T01's non-Revit canonical hard checks and P3 layout/approval
generation if those checks pass. Do not begin BIM-00 or Revit/R04/R05 from this
handoff.

## Current documentation flow

Start with `START_HERE.md`, then read `AGENTS.md`, `PROJECT_STATE.yaml`,
`docs/spec/CURRENT.md`, `docs/plan/CURRENT.md`, `docs/decisions/DECISIONS.md`,
and this handoff. The four active canonical images are normalized under
`docs/source/canonical/`; prior board images remain byte-identical under the
historical source path. Source and evidence inventories are covered by the
immutable manifest plus `SOURCE_MANIFEST.json`.

## P1-T01 closeout — four canonical boards

P1-T01 is implemented from `main`; the implementation binds the exact four
canonical image hashes and the official PDF hash. The crosswalk, geometry,
capacity/area authority, and remaining board/program discrepancies are in
`docs/reports/P1-T01-four-board-reconciliation.md`. The official 20-person,
626 m² internal, and 260 m² external program was not changed. The active
decision register now supersedes the three-source and S02 decisions while
preserving their signed history; the new solution identity remains unset and
`AMANDA-RUN-002-PAVILION-S02` remains stale.

Verification: the focused 11-module suite passed 100/100; changed-file Ruff
passed; `git diff --check` passed when scoped to P1-T01 files. A repository-wide
diff check also encountered pre-existing deleted GOLDEN/RC01 paths that deny
read access; those unrelated deletions remain unstaged and untouched. Independent
review by Huygens found no technical reconciliation blocker but withheld full
approval until commit/push, and asked that the historical decision-register
note below be clarified; it is now marked as a P0 checkpoint and superseded.
Follow-up review by Herschel verified the four-source decision, Board 03 count,
deviation schema/output hash, S01/S02 status, and task pointers, then found that
`AMANDA-RUN-002-PAVILION-S01` could still authorize selection and that the review
status wording here conflicted with the task graph. A regression test failed
for that alias and passed for the existing S01; the selection guard now rejects
both historical linear identities, and this handoff records those findings
instead of saying evidence is still pending. Implementation commit
`0d3fc94474f2a0d0944e10db6c602ce223aa7bc7` was pushed and a fresh remote read
confirmed `origin/main` at that SHA. Herschel's follow-up then caught the second
linear S01 alias; the fix and its regression test are in commit
`0d27fef6d068d471ac0bfe8b8634e902e08ed091`, which was pushed. A fresh remote
read confirmed `origin/main` at that SHA. Final independent review by Laplace
returned **APPROVE** for P1-T01: both historical S01 identifiers are rejected,
the task pointers and handoff agree, all four boards and the official program
are bound, and no BIM/R04/R05/Revit activity occurred. That reviewer ran the
two-case S01 regression only (2 passed; 6 deselected). The full focused gate
passed 100/100 and changed-file Ruff passed. `PROJECT_STATE.yaml` records
`0d27fef6d068d471ac0bfe8b8634e902e08ed091` as the last verified implementation
commit; the final handoff/state-only closeout commit is separate.

Open discrepancies are documented in the report: Board 03 draws six common
bathroom cells while the official PDF specifies five; the exact extra graphic
cell is not identifiable. Board 02/04 repeat or relabel archive, copa, and
sanitary functions with inconsistent areas/counts. Board 04 labels computer
and workshop uses without official room/area equivalents, and several support
labels do not map one-to-one. The PDF quantities/areas remain authoritative.
Canonical visual check CANON-011 remains blocked pending later Revit evidence;
P1-T01 made no Revit writes or BIM artifact. Next task: P2-T01 only; no R04/R05
or Revit work is authorized by this handoff.

## Historical P0 recovery log — reference only; superseded by current state above

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

## Task 10 complete; independent review approved (historical P0 checkpoint)

The 43-path design-engine baseline is fully classified in
`.recovery/design-engine-classification.json`: 4 active generator configs,
37 stale-evidence fixtures (including all seven S02 artifacts), 2 invalid
predecessor run logs recoverable from the safety tag, and 0 unknown paths.
Only the two invalid predecessor logs were removed from the active tree; their
SHA-256 values and exact tag recovery are in
`docs/reports/repository-recovery.md`. `design-engine/current/` remains absent.

At the Task 10/P0 recovery checkpoint, the signed decision register had not
changed. Its root-level S02 source_ref target,
`design-engine/runs/AMANDA-RUN-002-PAVILION/solution.json`, was absent from the
worktree, baseline, and recovery tag; the nested S02 finalist artifacts were
stale evidence. This is historical recovery context only. P1-T01 subsequently
updated the active register: the previous three-source and S02 detail records
are formally superseded with their signed history preserved, and
`DEC-CANONICAL-PARTI-002` binds the four current boards plus the official PDF.
See `project/requirements/decision-register.yaml` and the P1-T01 report.

Task 10 focused tests: 72 passed, 0 failed across `test_design_refine.py`,
`test_p08_t07_environmental_pass.py`, `test_bim_solution_compiler.py`,
`test_production_layout_bim.py`, `test_build_canonical_pavilion_run.py`,
`test_canonical_reference.py`, `test_canonical_pavilion_layout.py`,
`test_canonical_qa.py`, and `test_production_selection.py`. An expanded
10-module run including `test_canonical_state_migration.py` passed 76/76. No
full suite or Revit/model action occurred. Independent review approved the
scoped changes with no actionable findings. Implementation commit
`051161520f4725ffa6c650e39b6b128ffb43e09a` is pushed; fresh remote verification
matched `origin/main` at that SHA. The elevated view confirmed one worktree and
only `.recovery/` untracked. Task 11 began after the Task 10 closeout was
verified.

## Exact resume

Task 11 cleanup and Task 12 branch retirement are complete and independently
reviewed. Task 13 is now in progress: finish the final evidence, tests, and
document audit before removing `.recovery/` or setting the formal next task to
P1-T01. Do not use `git clean` to delete; preserve gate evidence, source files,
RVTs, and release artifacts.

## Task 11 complete; independent review approved

The read-only `git clean -ndX` preview listed 241 would-remove paths and two
vendor repositories it would skip. The preview and root-temp metadata are saved
under `.recovery/`. The preview includes protected
source PDFs/documents, provenance extractions, raw logs, production/checkpoint
RVTs, the live writer lock, all virtual environments, `.recovery/`, and
`.superpowers/`; these are not cleanup targets.

The preview has 134 root `.tmp-*` entries (104 scripts, 24 directories, and six
test log/text files), 32 `__pycache__` directories, and `.pytest_cache/`.
Preserve these six historical gate logs unchanged:
`.tmp-pytest-r05-canonical-full2.log`, `.tmp-pytest-r05-tree.log`,
`.tmp-y5.txt`, `.tmp-y7.txt`, `.tmp-y8.txt`, and `.tmp-y9.txt`. Also preserve
`.tmp-pytest-delivery-r11/`, referenced by the committed R11 evidence. The five
`.tmp-pytest-y5/` through `.tmp-pytest-y9/` basetemp directories are protected
test-output trees (four contain 1,679 files each; y7 contains 25); default
access was denied, and elevated read-only inspection confirmed generated
pytest outputs. Keep them for evidence.

The remaining root `.tmp-*.py` files are ignored scratch candidates. A static
AST pass parsed all 104 without executing them; their filenames have no
tracked source references. Some contain file-write or provider-call paths,
but no script was run. A scan of 345 nested `.rvt`/`.rfa`/`.rte` test fixtures
across root temp directories found only 6,149 bytes total (largest 53 bytes);
no actual Revit model is in that group.

Two other pytest scratch trees contain nested junctions, each targeting its
own `area-restrita` test fixture. Preserve both trees and do not move or
recursively remove them:
`.tmp-p08-t08-full/test_junction_escape_identity_0/revit/production/working`
and
`.tmp-p08-t08-full-available/test_junction_escape_identity_0/revit/production/working`.
The exact resolved targets are inside the matching test directories.

The explicit target manifest is recorded at
`.recovery/task11-approved-delete-manifest.csv` with its path list at
`.recovery/task11-approved-delete-list.txt`: 153 candidates (120 root scratch
entries, 32 `__pycache__` directories, and `.pytest_cache/`). The 120 root
entries are 104 scripts and 16 test-scratch directories; all resolved paths
stay inside the workspace and the selected directories have no nested
reparse points. Removed exactly those 153 paths with explicit
`Remove-Item -LiteralPath`, never `git clean`. Post-delete verification found
all targets absent, zero failures, all 14 excluded root temp evidence paths
present, and the fresh dry-run equal to the original set minus the removals:
88 paths remain, with no new or missing entries. `.ruff_cache/` and every
other unclassified path remain. Independent reviewer Carson approved the
exact 153-path delta, the 241-to-88 preview reconciliation, and the 14
preserved evidence paths with no actionable findings. Push and verify this
report/handoff closeout before Task 12.

The exact preserved paths include the six historical test log/text files,
`.tmp-pytest-delivery-r11/`, `.tmp-pytest-y5/` through `.tmp-pytest-y9/`, and
`.tmp-p08-t08-full/` plus `.tmp-p08-t08-full-available/` because they contain
internal test junctions. Production/checkpoint RVTs, private sources, raw
logs, provenance, writer lock, environments, `.recovery/`, `.superpowers/`, and
vendor repos remain preserved. No Revit/model action or tests occurred.

## Task 12 complete; independent review approved

Retired both obsolete branches after classifying their history. The local and
remote `codex/canonical-pavilion-migration` tips were already ancestors of
`main` (local comparison `20 0`, remote-tracking comparison `22 0`); remote
deletion succeeded and local `git branch -d` removed the merged ref.

The P08 branch had exactly two commits beyond `main`: `e5c9a0e` adds an
offline R01–R04 concept-candidate bundle for legacy `AMANDA-RUN-001-F01/F02`,
and `125c7d9` closes its handoff. It is not current four-board production
work and was not merged. Its complete history is preserved by the published
annotated tag `superseded-p08-t08-concept-offline-2026-09-24`, which peels to
`125c7d956d40fab6c358e4c6702199b4eac4d854`. The remote branch was deleted;
the local ref was removed by exact-OID `git update-ref -d`, not `branch -D`.

The recovery tag `pre-repository-recovery-2026-09-24` remains published and
peels to `30cc3b0f7860dfb5e46299402585213d1ac2d02b`. Fresh post-deletion
remote verification showed `origin/main` at `64d6b94503202fe7d29396efeb26e1e57f84b2c0`,
both old branch refs absent, and both tags present. Local status shows one
worktree on `main` and only `.recovery/` untracked. Independent reviewer
Pascal approved the branch proof, preservation tags, and post-deletion state.
No tests or Revit/model operations were run during this task.

## Task 13 complete; independent review approved

The `.recovery/` crosswalk was committed before deletion. All 15 items
(12,196,838 bytes) are accounted for in the recovery report, with zero reparse
points. The 112-row RVT inventory matched all retained paths; the three
quarantined copies matched retained checkpoints byte for byte. Their redundant
copies were removed, leaving 109 RVTs under `revit/`; RC01 still has 36 files
and its manifest/model hashes match the earlier verification.

The current structure is one plan (`docs/plan/CURRENT.md`), one spec
(`docs/spec/CURRENT.md`), and this sole active handoff. No ZIP is tracked or
present under `docs/`; `docs/notes/` and the old plan/spec/review directories
are absent. The source manifest remains present with 20 assets.

TDD readiness change: the first test failed because P1-T01 was absent from the
task registry. The registry now has P1-T01 as its only READY task and suspends
legacy `P08-CAN-T09` through `P08-CAN-T19`; no task was marked complete. The
focused gate passed 76/76 across repository hygiene, state/dashboard/task graph,
plan order, canonical references/layout/QA, source manifest, and provenance.
`amanda_agent status` exits 0 with phase P1 READY, next P1-T01, zero pending
tasks, five site conditions (three BLOCKING, two DEGRADING), and writer lease
HELD by `amanda-P08-CAN-T09-R03`. The lease was not changed. Independent
reviewer Halley approved the final recovery state. No Revit/model action.

## Git checkpoint

Task 9 implementation commit: `c4adceb70c3824dba50c8ef3010472b94664b6f4`;
report/handoff closeout commit: `1290ba3e83ed44fee4a447a7b6e6d6aad92604d1`.
Both were pushed. After the closeout push, a fresh `git ls-remote` check
confirmed `HEAD = main = origin/main` at
`1290ba3e83ed44fee4a447a7b6e6d6aad92604d1` and exactly one worktree.
Task 13 removed `.recovery/` after the full hash inventory and report transfer.
The three redundant quarantine copies were removed only after matching their
retained checkpoints; all 109 unique RVTs remain under `revit/`.
