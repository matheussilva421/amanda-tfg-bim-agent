# Current Handoff

## Formal state and safety

Repository recovery (P0), four-board reconciliation (P1-T01), identity
assignment (P2-T01), and offline canonical QA (P3-T01) are complete.
P4-T01 was attempted as a read-only BIM-00 preflight and is
`BLOCKED_BY_INPUT`. `PROJECT_STATE.yaml` remains at P4 with `next_task: P4-T01`;
P3-T01 is the last PASS task. The source-bound identity is recorded at
`project/requirements/canonical-solution-identity.yaml`, while
the selected design is RUN-003 for normalized study only; final/detailed
eligibility remains false. The recovery anchor is
`pre-repository-recovery-2026-09-24`; the superseded P08 offline candidate is
preserved under `superseded-p08-t08-concept-offline-2026-09-24`.

## P4-T01 attempt — BIM-00 blocked

> Historical snapshot from the original P4-T01 attempt. Its eligibility and
> runtime observations below are superseded by the current continuation section
> later in this file; use that section and PROJECT_STATE.yaml for current state.

No BIM-00 evidence or authorization was emitted. RUN-003 remains
`OFFLINE_CANDIDATE`, `bim_eligible=false`, `revit_calls=0`, with
`selected_design=null`, `current_checkpoint=null`, and a detail decision marked
`BLOCKED_BY_INPUT` / `AMANDA_REVIEW_PENDING`. The hashes of all four canonical
boards, the official program PDF, and the P1 report were independently
recomputed and match the persisted identity. Values are recorded in
`docs/reports/P4-T01-bim00-blocker-report.md`.

There are preserved RVTs in the production tree, but none is bound as the
RUN-003 target; `revit/production/working/CURRENT.rvt` is absent. The writer
lock remains HELD by `amanda-P08-CAN-T09-R03` on superseded S02; it was not
released or reclaimed. No Revit process was running, so live provider health
was not established. Site topography, boundary, and occupancy remain blocking;
frontage count and true north remain unresolved/degrading.

P4 contract hardening added mandatory binding and comparison for the official
program SHA-256, repository commit, and `PROJECT_STATE.yaml` revision/raw SHA.
Focused gate tests: 41 passed; combined gate/status/state tests: 57 passed;
final focused closeout suite: 103 passed; Ruff and scoped diff check passed. The
tests first produced 38 failures and 1 pass before the fix.
Independent review found no Critical, Important, or Minor findings. Code and
plan contract are committed as `bc494683f9d9b154c40bdc8069a3dfa48710c665`;
`last_verified_commit` points there. State revision is 182.

### Recheck — 2026-09-25

An official RN government PMRN service charter updated 2026-02-03 lists BPChoque
at Av. Miguel Castro, s/n, Lagoa Nova, Natal
([source](https://www.transparencia.rn.gov.br/docs/orgaosdogoverno/cartasdeservico/Carta_de_Servi%C3%A7os_PMRN.pdf)).
This is partial evidence of the published institutional address. It does not
identify the cadastral parcel or establish an approved transfer, so
`SITE_OCCUPANCY` remains `BLOCKING` for claiming site availability. The other
site fields remain unverified: placeholder boundary, missing topography,
unresolved frontage conflict, and no verified true-north bearing.

An independent read-only audit confirmed RUN-003 is still unselected and
ineligible, with no exact target/checkpoint; CANON-011 remains pending human
visual acceptance. The lease remains held for S02 and was not changed. No Revit
process or document was opened or written. `P4-T01` remains the retry pointer;
P5/R04 and R05 remain unauthorized. A fresh `git ls-remote` could not reach
GitHub in this session; local `HEAD` and `origin/main` both pointed to
`f367e99bd65268ba4ea665225808f771ac9c11cd` before these documentation updates.
The recheck commit `05684895699053409ccc39ad78045ba45ef73d38` was subsequently
pushed, and a fresh `git ls-remote --heads origin main` confirmed that commit
at `refs/heads/main`. This handoff status correction is being committed as a
fast-forward follow-up. The pre-existing RC01 deletions were not staged or
changed.

### P4-T01 continuation — scoped study selection and BIM-00 hardening (2026-09-25)

- The previously recorded site-data dependency was too broad for normalized
  academic STUDY. Successor decision `DEC-CANONICAL-DETAIL-004` selects RUN-003
  only through R04 with `LOCAL_NORMALIZED_STUDY_NOT_SURVEYED`; Amanda review
  remains pending and CANON-011 still requires a real four-board comparison
  before R05. The content approval hash is not personal approval.
- `PROJECT_STATE.yaml` revision 184 records RUN-003 as the current reversible
  study selection. Site blockers are DEGRADING for this scope; final/site claims
  remain constrained by `project/site/missing-data.yaml`. The current P4 blockers
  are unreachable Horizun provider, writer lease held for superseded S02, and no
  exact RUN-003 target/checkpoint.
- The generated current study snapshot is
  `design-engine/runs/AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C-study-detail-004/`.
  It binds detail decision 004 (hash
  `29d70f0e830708a3926abad14877f4c3941418630c5f0225b0bf5924f2dabd8b`) and
  content approval `961b6edc95bd097fe600b2ce968aacdf28876bf3c587b788a0b2358baddfc0b0`.
  Its manifest verifies 6/6 files; QA remains 17 PASS, 0 FAIL, CANON-011
  BLOCKED; it records `bim_eligible=false` and `revit_calls=0`. Original P3
  snapshot remains preserved at its original path.
- R04 mass payloads carry `design_scenario=STUDY` and the typed coordinate mode.
  BIM-00 refuses untyped/mismatched coordinate modes. R04 mass writer now
  preserves base elevation and interior rings, and completion requires separate
  geometry readback from the Revit model before verification. Model readback
  geometry/identity now override self-reported write payload fields; failed
  readback removes the geometry claim so runner verification fails closed.
- Regression tests for independent review findings reproduced RED: FINAL plans
  could pass BIM-00 and blocked P4-T01 was also recorded as completed. The new
  scenario/state regressions reported 4 failures and 62 passes before fixes.
  BIM-00 now requires STUDY; the last completed task is P3-T01; the old resume
  instructions are explicitly superseded. The focused BIM-00/R04/readback/
  geometric suite previously passed 154 tests. Review follow-up also requested
  explicit claim scope in the dashboard and a historical label on the older
  pre-DEC-004 section. Both changes have regression coverage; independent
  confirmation approved with no remaining findings. The final 19-module focused
  suite passed 270/270 and scoped Ruff passed. Record diff check, snapshot hash,
  manifest 6/6 validation, and QA 17 PASS/0 FAIL/CANON-011 BLOCKED are verified.
  Record commit and push below at closeout.
- Read-only Revit diagnostics: Revit 2027 PID 38152 responds but has no
  targetable main window; `horizun_health` failed with no reachable Revit.
  No RVT was opened and no Revit write, BIM-00 authorization, R04 or R05 was
  performed. S02 lease remains untouched.
- Resume P4-T01 only after a targetable/healthy provider, safe resolution of the
  S02 writer lease, and an exact RUN-003 target/checkpoint are evidenced. Rebind
  current commit/state/source hashes then rerun BIM-00; do not advance R05
  until CANON-011 passes.

### Bounded official-source research — 2026-09-25

`docs/reports/P4-T01-site-source-research-2026-09-25.md` records a read-only
search of official municipal and state sources. It found no verifiable
project-specific cadastral polygon, site survey/topography/datum, physical
occupancy confirmation or transfer/availability decision, frontage count, or
true-north bearing. The PMRN service charter supports only a published BPChoque
institutional address; the municipal law and procurement specification are
routes/specifications, not parcel data, although the municipal specification
does describe geospatial references/products. GeoNatal serves a public 40,568-
feature lot GeoJSON collection with CRS84, but no feature was linked to this
project parcel; the served file alone does not establish currentness or
site-specific applicability. Unrelated content was also observed on alternate
routes, which is an anomaly of content and does not prove the official layers
are compromised. No site blocker was resolved or reclassified; `P4-T01` stays
`BLOCKED_BY_INPUT`. The task-graph CLI validated
182 registered tasks, with no ready task. No test suite, Revit, or RVT was run
or opened. No BIM authorization or R04/R05 work occurred. The research delta
was committed as `4723b3c9d352289b88e133bae1c67fa405198487` and pushed; a fresh
`git ls-remote --heads origin main` verified that SHA on the remote. The
pre-existing RC01 deletions were not staged.

The read-only environment doctor exited 0: Git, Codex, PowerShell and .NET were
available; Revit 2027 was detected, but no Revit process was running. The venv
Python is 3.12.14 even though the host-only probe reports `python312 MISSING`;
live provider health remains unverified. The S02 writer lease was not touched.
Automatic approval review rejected matching cadastral features to the project
site using its area/neighborhood/street description because it could identify
a third-party parcel. No feature was assigned to this project; obtain explicit
user approval before any site-specific match.

The GeoNatal response metadata correction and approval-review blocker note were
independently reviewed and committed as
`3ed955662d8ca340205e266b9175691aeaaf7ec4`; the commit was pushed, and a fresh
remote read confirmed `origin/main` at the same SHA.

Resume only P4-T01 after the canonical selection is approved/eligible, required
site inputs are resolved, an exact target and separate checkpoint are
designated, and the writer lease/provider can produce fresh passing evidence.
Do not choose an existing RVT by filename, reclaim the S02 lease, reuse S02 as
the solution, or run R04/R05. P5 remains unauthorized.

P0 completed without Revit/model activity. All recovery evidence is transferred
to `docs/reports/repository-recovery.md`; `.recovery/` was removed after the
RVT and evidence checks. Preserve the private program and TFG PDFs locally;
they are intentionally ignored by Git. Five site conditions (three BLOCKING,
two DEGRADING) remain, and the held writer lease is unchanged. P1-T01 completed
without Revit/model activity. At P1-T01 closeout the solution identity was
unset and S02 was stale; P2-T01 has since assigned the source-bound identity
recorded above. Five site conditions (three BLOCKING, two DEGRADING) remain;
the held writer lease was not changed.

## P3-T01 closeout — canonical QA and candidate

Generated offline candidate `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`
with identity fingerprint
`4b1275558a6c2c40828dbba1422c0063703c182fd9d7b800b36a448499a073c4`. It binds
all four current board hashes, the official 20-person / 626 m² internal /
260 m² external program PDF, and the P1-T01 report. Layout hash:
`7fde3e34a162167ce27fe2e3158a38f446882816a7c81bb326d486bdfaaae2e2`;
candidate content approval hash:
`eea4a342a4d732cbc986a16d01d93e3981e79a5931f8d99ebef82c61d24299ec`;
detail-decision hash:
`f37c5c8c2f4f43e957429bd05dbc659012a7f6eaa0b0be65e23cbf7f47c43efc`.
The approval hash is a deterministic content binding, not Amanda approval or
BIM authorization. `DEC-CANONICAL-DETAIL-003` remains provisional,
`BLOCKED_BY_INPUT`, and `AMANDA_REVIEW_PENDING`.

P3 QA requires exactly one each of CANON-001..018: **17 PASS, 0 FAIL,
CANON-011 BLOCKED**, zero critical failures. The normal CLI and direct builder
both validate the persisted P2 identity against live sources including the P1
report. A forged self-consistent report hash regression was first reproduced
RED and then passed GREEN. A second RED/GREEN regression rejects duplicate/missing
QA IDs. Independent review and re-review verified both fixes and no CLI
regression. The final state review found no Critical/Important issues and one
Minor gap in negative phase-edge coverage; tests now cover P1→P2, P2→P3, and
P3→P4.

Focused command:
`.venv/Scripts/python.exe -m pytest tests/unit/test_build_canonical_pavilion_run.py tests/unit/test_canonical_solution_identity.py tests/unit/test_production_selection.py tests/unit/test_canonical_qa.py tests/unit/test_decision_register.py tests/project/test_repository_hygiene.py tests/policy/test_plan_order.py -q`
— **74 passed**. State/task/session routing suite — **55 passed**. Changed-file Ruff and `git diff --check` pass. The builder
regenerated RUN-003 deterministically; its six artifact-manifest entries all
match recorded SHA-256 and byte counts. `bim_eligible=false`, `revit_calls=0`,
`selected_design=null`; no Revit access/write and no R04/R05 activity.

Broader downstream check
`.venv/Scripts/pytest.exe tests/unit/test_production_layout_bim.py -q` returned
**26 passed, 5 failed**. All five failures are R04 planning preflights at
`projection_area: MASS-SERVICE_CAPACITATION`; this is recorded as an R04
readiness blocker and was not modified in P3. Board 03's six drawn common-WC
cells vs five official rooms, Board 02/04 repeated or relabeled support areas,
and Board 04 unpriced training functions remain explicitly reconciled in the
P1 report. CANON-011 visual acceptance and site verification remain pending.

P3 writer/QA correction commit `0957a516c09a97075c820d105ccdebac3c4cacc4`,
phase-order correction commit `d85456ea5d0d5c1c6e849f18846be52bf53f95c5`,
and P4 gate contract commit `bc494683f9d9b154c40bdc8069a3dfa48710c665` are
on `main`. P4-T01 is formally `BLOCKED_BY_INPUT`; it remains the retry pointer.
Do not run R04/R05 or write Revit from this handoff. Do not touch or stage RC01
paths.

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
`aa1975a` (`feat: assign canonical solution identity P2-T01`). State-only
closeout commit `b563953` set `last_verified_commit` to this tested
implementation commit. Both commits were pushed; a fresh remote read confirmed
`origin/main` at `b563953` before this handoff/status refresh.

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

## Historical P4 continuation — normalized study audit and candidate search (2026-09-25)

This subsection records the earlier pre-DEC-CANONICAL-DETAIL-004 snapshot. Its
selection, eligibility, site-scope, and resume statements are superseded by the
active P4-T01 continuation above; use that section and `PROJECT_STATE.yaml`.

The user supplied explicit authorization for a read-only public candidate
search and asked to continue through later gates when they pass. The search
found only a `CANDIDATE` geographic context (Lagoa Nova / Av. Miguel Castro / a
rounded institutional GeoNatal point). It did not identify a parcel polygon
that can be tied to the TFG's approximate 24,135 m² site. No lot is
`PROVISIONAL` or `VERIFIED`; no owner, CPF, title or private records were
searched. Evidence is added to
`docs/reports/P4-T01-site-source-research-2026-09-25.md`.

An independent read-only audit found that missing site evidence and
`AMANDA_REVIEW_PENDING` should not alone prevent a reversible normalized
academic `STUDY` through R04. Existing site-data and preacceptance code already
allows that scope. The gaps still block cadastral placement, final grading,
legal frontage/setback/orientation statements, and actual availability or
transfer claims. The current P4 record still lacks a typed site-coordinate
mode, and the project state/spec wording needs an explicit normalized-study
scope before the gate can be issued. Human approval remains pending.

The first focused run of the R04 planner/provider suite had 5 failures, all at
`projection_area: MASS-SERVICE_CAPACITATION`: R04 exported only the outer
polygon ring and filled the six internal voids. TDD regressions reproduced the
missing-ring behavior in both planning and the generated Revit route. The
implementation now carries all interior rings into the R04 geometry, computes
net area including the voids, and makes independent geometry verification
reject a readback with a missing ring. Focused validation is **39 passed** for
`test_stage_massing.py`, the complete `test_production_layout_bim.py`, and the
mass provider route. Independent code review is still pending. A Ruff pass
reported existing violations in the touched legacy modules plus a new test
`exec` lint finding; the test lint finding must be addressed and changed-file
checks rerun.

No Revit process was started and no RVT was opened or written. A read-only
Horizun health call returned “no Revit is reachable.” The S02 lease remains
untouched; the recorded owner PID was not running and no Revit process was
present, but lease transition criteria and an exact RUN-003 target/checkpoint
have not yet been completed. `PROJECT_STATE.yaml` still points to P4-T01 and
still has no selected design/checkpoint. RC01 deletions remain untouched and
unstaged.

**Resume:** superseded. Continue from the latest `P4-T01 continuation` section
above and its explicit blocker list. Do not repeat already completed coordinate
binding, R04 ring/readback, or offline snapshot work.
