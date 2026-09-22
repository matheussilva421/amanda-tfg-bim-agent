# Handoff - R05 collinear-wall repair and stdio bridge blocker (2026-09-21)

## Status

`PENDING / BLOCKED_FOR_LIVE_RETRY`. The code-side R05 repair is implemented and
the non-Revit test gate is green. A real R01-R05 rerun could not start because
the stdio MCP transport runs in the Codex sandbox identity and cannot see the
interactive Revit bridge. No production RVT was written in this session.

The authoritative durable state remains `PROJECT_STATE.yaml` revision 159:
`PHASE_08`, `P08-T08`, `GO_WITH_LIMITATIONS`, with site blockers and
`CROSSWALK_GRID_ROOF_GAP` still recorded. Do not mark R05, P08-T08, or the
production phase complete from this handoff.

## Work completed

- Root cause from the previous live R05 journal was preserved: two shell walls
  overlapped in Revit, producing `180/182` verified walls and a Revit warning.
- `src/amanda_agent/bim/stages/shell.py` now merges overlapping collinear room
  edge runs before building the desired wall state. Touching runs remain
  separate and diagonal edges are preserved.
- `src/amanda_agent/production/layout_bim.py` now uses the varying axis when
  merging collinear walls, preventing zero-length walls and keeping the shell
  driver aligned with the stage planner.
- Added regression coverage in `tests/unit/test_stage_shell.py` and
  `tests/unit/test_production_layout_bim.py`.
- `scripts/run_amanda_production.py` now accepts `--revit-pid` and selects the
  requested Revit process inside the same MCP stdio session. The helper is
  covered by `tests/unit/test_run_amanda_production.py`.
- Existing `scripts/prove_crosswalk_grid_roof.py` idempotency/path changes are
  still present in the working tree and were included in the relevant review
  scope; do not revert them as part of the R05 continuation.

## Tests and live attempts

Focused gate:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_stage_shell.py tests/unit/test_production_layout_bim.py -q --basetemp .tmp-pytest-session-r05a
21 passed, 0 failed
```

TDD transport-selection gate:

```text
RED: tests/unit/test_run_amanda_production.py failed at collection because
_select_revit_target did not exist.
GREEN: .\.venv\Scripts\python.exe -m pytest tests/unit/test_run_amanda_production.py -q --basetemp .tmp-pytest-r05-target-green
1 passed, 0 failed
```

Full non-Revit gate after all code changes:

```text
.\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q --basetemp .tmp-pytest-session-r05full3
869 passed, 0 failed
```

First live attempt, before the PID option:

```text
.\.venv\Scripts\python.exe scripts/run_amanda_production.py --rvt revit\production\working\AMANDA_WORKING_001.rvt --max-stage R05 --execute
```

It acquired and released the writer lease, but the stdio server returned
`no Revit is reachable`; R03 was not written or verified.

Second attempt, with the PID option:

```text
.\.venv\Scripts\python.exe scripts/run_amanda_production.py --rvt revit\production\working\AMANDA_WORKING_001.rvt --max-stage R05 --revit-pid 37588 --execute
```

The child stdio server returned no target payload. A raw transport probe showed
why: its `USERPROFILE` is `C:\Users\CodexSandboxOffline`, so its data root is
`C:\Users\CodexSandboxOffline\.horizun`; it sees zero discovery files and
reports `No Revit has published a bridge`. The interactive Horizun tool had
previously reported the real-user root `C:\Users\slvma\.horizun`, but that
selection is not shared with the child stdio server. The three Revit processes
seen earlier (PIDs 37588, 11560, 30312) then exited; a final process check found
no `Revit.exe` process and the interactive target list was empty.

The failed attempts left no `state/locks/revit-writer.lock` and no new
`20260921` production RVT. Do not treat `revit/production/journals/R05.json`
as new evidence; it is the earlier `180/182` failed run.

## Git and unrelated state

The branch was `main...origin/main` at `8b58bb2` on session start. The working
tree already contained unrelated dirty files, generated Topologic result
changes, untracked package/output trees, and the known ACL phantom deletions
under `revit/lab/exports/p06t14/GOLDEN/RC01`. Those paths were not restored,
deleted, or staged.

Relevant files for this block are:

- `scripts/prove_crosswalk_grid_roof.py`
- `scripts/run_amanda_production.py`
- `src/amanda_agent/bim/stages/shell.py`
- `src/amanda_agent/production/layout_bim.py`
- `tests/unit/test_stage_shell.py`
- `tests/unit/test_production_layout_bim.py`
- `tests/unit/test_run_amanda_production.py`
- this handoff

## Exact resume instructions

1. Start Revit 2027 in a normal user session with the Horizun add-in loaded.
   If the unsigned-add-in security prompt appears, the owner must choose
   `Sempre carregar`.
2. Prefer running the production command from a normal PowerShell process that
   has `USERPROFILE=C:\Users\slvma`, because the Codex sandbox child cannot see
   the real-user discovery root. Identify the published PID and pass it
   explicitly:

   ```powershell
   .\.venv\Scripts\python.exe scripts\run_amanda_production.py `
     --rvt revit\production\working\AMANDA_WORKING_001.rvt `
     --max-stage R05 --revit-pid <published-revit-pid> --execute
   ```

3. Require fresh R01/R02/R03/R04/R05 journals and `100%` verified records.
   Stop before R06 if any record fails or if the provider cannot independently
   read the committed element.
4. If R05 reaches `182/182`, perform the independent save/close/reopen check,
   then update `PROJECT_STATE.yaml`, create the next incremental handoff, and
   only then continue to R06-R13.
5. If the normal-user command is unavailable, use the interactive Horizun app
   route only with a manually controlled Revit target; do not infer that its
   health proves the sandbox stdio route.

## Commit/push result

The narrow commit `4c801f1` (`fix(revit): merge collinear shell walls before
R05`) was created after `git diff --check` and the 869-test gate, and pushed to
`origin/main`. The commit contains only the seven relevant files listed above.
The pre-existing unrelated output changes and known phantom GOLDEN paths remain
outside the commit and must not be staged or restored during continuation.

## Addendum - referential wall IDs and stdio environment (2026-09-21)

The session-start revalidation found Revit 2027 running as PID 15608, no
`state/locks/revit-writer.lock`, and an existing working RVT
`revit/production/working/AMANDA_WORKING_001.20260921-200931.rvt`. This is an
observation only; no BIM write was performed by this addendum.

The local production compiler had a deterministic chain-integrity defect:
R05 shell walls used `WALL-*`, R06 shared room boundaries used
`LAYOUT-WALL-*`, while R07/R12 consumers used a mixture of `PARTITION-*` and
wall IDs that were not produced by either stage. The fix in
`src/amanda_agent/production/layout_bim.py` now preserves the producer
namespace, keeps R06 shared segments individual, and uses a transitive
overlap merge consistent with the committed shell semantics. The regression
test `test_later_wall_consumers_reference_ids_created_by_r05_or_r06` proves
that every opening host and material target is created by R05 or R06.

The stdio transport now passes a copied controller environment to the MCP
child. `tests/unit/test_bim_transport_env.py` proves the complete environment
is preserved, including `USERPROFILE` and a sentinel variable.

Validation after the fixes:

```text
tests/unit/test_production_layout_bim.py tests/unit/test_stage_shell.py
tests/unit/test_stage_openings.py tests/unit/test_stage_layout.py: 33 passed
transport/provider tests: 56 passed
tests -m "not revit and not slow": 871 passed
```

The durable project state remains revision 159, `PHASE_08`, `P08-T08`,
`GO_WITH_LIMITATIONS`; the site blockers and `CROSSWALK_GRID_ROOF_GAP` remain
open. The next live gate is a fresh R01-R05 run from a normal-user PowerShell
with PID 15608 (or a freshly verified published PID), stopping on any failed
record. Do not advance `PROJECT_STATE.yaml` or claim production completion
until the independent save/close/reopen evidence exists.

## Addendum - shell semantic classification and live retry (2026-09-21 21:10)

The local patch now treats touching collinear shell runs as one geometric wall
while preserving the semantic distinction between a genuinely shared room
boundary and two adjacent external room edges. The merge buckets carry the
shared-boundary flag, and R05 uses that flag for `wall_kind` and `is_shared`;
this prevents the top and bottom edges of adjacent rooms from being mislabeled
as internal walls. The production layout driver continues to resolve openings
against the actual wall span after gallery/exterior wall merging, and the
crosswalk helper continues to use absolute paths and fresh idempotency keys.

Validation after this correction:

```text
Focused: .\.venv\Scripts\python.exe -m pytest tests/unit/test_stage_shell.py tests/unit/test_production_layout_bim.py tests/unit/test_stage_openings.py tests/unit/test_stage_layout.py tests/unit/test_run_amanda_production.py -q --basetemp .tmp-pytest-continuation-green3
34 passed, 0 failed

Full non-Revit: .\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q --basetemp .tmp-pytest-continuation-full
871 passed, 0 failed

Targeted lint: .\.venv\Scripts\python.exe -m ruff check --select B023 src/amanda_agent/bim/stages/shell.py
All checks passed

Syntax: .\.venv\Scripts\python.exe -m py_compile scripts/prove_crosswalk_grid_roof.py src/amanda_agent/bim/stages/shell.py src/amanda_agent/production/layout_bim.py
Passed
```

The global Ruff invocation still reports pre-existing style findings in the
dirty files (unused imports/noqa, SIM102 and test formatting); it is not a
clean repository-wide lint gate and was not broadened into this repair.

A live retry was attempted with Revit 2027 PID `15608`, which was visible to
the controller and had a current discovery file under
`C:\Users\slvma\.horizun\discovery`. The command was:

```text
.\.venv\Scripts\python.exe scripts/run_amanda_production.py --rvt revit\production\working\AMANDA_WORKING_001.rvt --max-stage R05 --revit-pid 15608 --execute
```

It stopped before R01 because the child `horizun-mcp.exe` resolved its own
profile as `C:\Users\CodexSandboxOffline`; raw calls returned `no Revit is
reachable` and `No Revit with process id 15608 has published a bridge`. The
lease was released. No new production RVT or stage journal was produced, and
the existing R02-R05 journals remain the earlier evidence; no production
stage may be marked PASS from this retry.

The current durable state is still `PROJECT_STATE.yaml` revision 159,
`PHASE_08`, `P08-T08`, `GO_WITH_LIMITATIONS`. The site blockers and
`CROSSWALK_GRID_ROOF_GAP` remain open. The next live action requires a
controller/stdio route that runs under the same Windows user context as Revit,
or a manually controlled interactive Horizun route. Do not work around this
by copying discovery files or by changing `PROJECT_STATE.yaml`; that would not
prove the real bridge connection.

## Publication and final verification (2026-09-21)

The functional patch and this addendum were committed as `f26b7f7`
(`fix(revit): preserve shell semantics across merged runs`) and pushed to
`origin/main`. The final non-Revit gate was rerun after the commit:

```text
.\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q --basetemp .tmp-pytest-final-r05
871 passed, 0 failed
```

`main` and the local `origin/main` tracking ref both resolve to
`f26b7f74f54104147b962c7b18203b5948f41efd`. A subsequent `git ls-remote`
refresh was unavailable because GitHub HTTPS was unreachable at that moment;
the successful push result is the publication evidence. The working tree still
shows only the pre-existing ACL-visible `GOLDEN/RC01` deletions, Topologic
result changes, untracked package/output trees, and timestamped production
journals; none are part of `f26b7f7`.

## Addendum - normal-user bridge retry and precision blocker (2026-09-21)

The normal-user route was available in this continuation. Revit 2027 build
`27.2.0.39` was responding as PID `15608`, its discovery file was visible under
`C:\Users\slvma\.horizun`, and `horizun_health` returned `healthy` with the
active document matched to the requested path. The production command was run
outside the Codex sandbox with the real-user profile:

```text
.\.venv\Scripts\python.exe scripts/run_amanda_production.py --rvt revit\production\working\AMANDA_WORKING_001.rvt --max-stage R05 --revit-pid 15608 --execute
```

It created the new attempt
`revit/production/working/AMANDA_WORKING_001.20260921-211721.rvt` and verified
R01-R04, but R05 stopped at `74/82`: eight external walls returned
`Requested properties do not match the committed element`. Independent reads
by `ALL_MODEL_MARK` found no rows for those eight IDs, so they were reverted;
the attempt is partial evidence and must not be promoted or reused.

Root cause: `_edge_key` used six-decimal canonical coordinates for identity,
while `_merge_collinear_edges` returned raw floating-point endpoints for a
single edge. Revit snapped endpoints to adjacent walls, and the strict
post-commit verifier rejected differences above its tolerance. The correction
canonicalizes all single, merged, and diagonal edge endpoints before emitting
the desired state. A TDD regression was first observed RED, then GREEN.

Validation after the correction:

```text
Focused: .\.venv\Scripts\python.exe -m pytest tests/unit/test_stage_shell.py tests/unit/test_production_layout_bim.py tests/unit/test_stage_openings.py tests/unit/test_stage_layout.py tests/unit/test_run_amanda_production.py -q --basetemp .tmp-pytest-r05-canonical-focused
35 passed, 0 failed

Full non-Revit: .\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q --basetemp .tmp-pytest-r05-canonical-full2
872 passed, 0 failed

Targeted Ruff: .\.venv\Scripts\python.exe -m ruff check --select B023 src/amanda_agent/bim/stages/shell.py
All checks passed

Syntax: .\.venv\Scripts\python.exe -m py_compile src/amanda_agent/bim/stages/shell.py scripts/run_amanda_production.py
Passed
```

The durable project state remains revision 159, `PHASE_08`, `P08-T08`,
`GO_WITH_LIMITATIONS`; blockers and `CROSSWALK_GRID_ROOF_GAP` remain open. No
state advancement, production PASS, save/close/reopen certification, or export
promotion is justified yet. The next action is to commit/push the narrow
precision fix, then rerun a fresh normal-user R01-R05 attempt and require
`100%` verified records before continuing.

## Addendum - R05 real PASS and persistence modal (2026-09-21)

After the precision fix was published, a fresh normal-user execution created
`revit/production/working/AMANDA_WORKING_001.20260921-213302.rvt` and passed:

```text
R02 VERIFIED 0/0 verified
R03 VERIFIED 3/3 verified
R04 VERIFIED 1/1 verified
R05 VERIFIED 82/82 verified
```

The run saved the file and released the writer lease. An independent read after
the first reopen observed `78` `OST_Walls`, `3` `OST_Floors`, and `1`
`OST_Roofs`; each of the eight formerly failing wall marks returned exactly one
row. The active document path matched the requested RVT.

The persistence close was then repeated with `activate_other=true`. The bridge
returned `closed=true` with object-identity evidence that the target Document
was absent from `Application.Documents` and `IsValidObject=false`; the file
remained on disk at `4,022,272` bytes with `disk_changed=false`.

The subsequent reopen is currently blocked by a Revit human modal:
`Projeto não recentemente salvo`. The bridge reports that the open request was
queued and removed without running while this dialog is present. A human must
answer or close that dialog in Revit; after it disappears, rerun the prepared
reopen/read check before claiming persistence PASS. Do not mark `PROJECT_STATE`
complete or proceed to R06-R13 until the reopen and critical reads are fresh.

Commit `4e5f045` (`fix(revit): canonicalize shell wall endpoints`) is pushed to
`origin/main`. The durable project state remains revision 159, `PHASE_08`,
`P08-T08`, `GO_WITH_LIMITATIONS`; the site blockers and
`CROSSWALK_GRID_ROOF_GAP` remain open.

## Addendum - resume revalidation (2026-09-21)

The next continuation rechecked the normal-user bridge and received the same
modal refusal before any request started: Revit still has
`Projeto não recentemente salvo` open. Even `horizun_health` was removed from
the queue after the modal probe, so no production write, read, or state change
was attempted. The native UI is not exposed to the current automation surface.

Resume condition: dismiss the Revit reminder without using Save As or changing
the saved target, then rerun the post-close `horizun_open_document` and critical
R05 reads for `AMANDA_WORKING_001.20260921-213302.rvt`. Only after that fresh
reopen evidence may R06-R13 begin.

The full production driver was also checked in dry-run mode after this
revalidation:

```text
.\.venv\Scripts\python.exe scripts/run_amanda_production.py --rvt revit\production\working\AMANDA_WORKING_001.rvt --max-stage R13
planned stages: R01 R02 R03 R04 R05 R06 R07 R08 R09 R10 R11 R12 R13
dry run: nothing written
```

The layout and approval hashes remained unchanged, and the installed template
was still `Default_M_PTB.rte` on Revit 2027. No live stage was advanced by this
dry run.

## Addendum - session-start revalidation (2026-09-21)

The session-start protocol was rerun without any BIM mutation. `amanda_agent
status` and `amanda_agent resume` both completed successfully and confirmed the
authoritative durable state: revision `159`, `PHASE_08`, next task `P08-T08`,
`GO_WITH_LIMITATIONS`, five site blockers, and a free writer lease. The
`PROJECT_STATE.yaml` blocker `CROSSWALK_GRID_ROOF_GAP` remains open. No
`state/locks/revit-writer.lock` exists.

The live process inventory showed Revit 2027 build `27.2.0.39` in PIDs `15608`
and `39808`. Process presence is not evidence that the requested document is
the active bridge target or that the persistence modal has been dismissed, so
no production command or provider write was started. The existing resume
boundary remains: dismiss the Revit human modal without changing the saved
target, then reopen and independently read
`AMANDA_WORKING_001.20260921-213302.rvt` before any R06-R13 work.

`amanda_agent doctor` detected Revit, but its persisted environment report
still says `python312: MISSING`; the pinned `.venv\Scripts\python.exe` ran
`status` and `resume` successfully. This is an environment-report freshness
discrepancy, not evidence to advance a production gate.

Git remains `main` at `89646c0`, matching `origin/main`. The working tree still
contains only the pre-existing ACL-visible phantom deletions under
`revit/lab/exports/p06t14/GOLDEN/RC01`, generated Topologic result changes, and
untracked `.codex`, package/output, and `revit/production` trees. They were not
restored, deleted, or staged. A repository-wide `git diff --check` is blocked by
the ACL-denied GOLDEN paths; no new handoff formatting error was found in the
path edited above.

## Addendum - handoff publication (2026-09-21)

The session-start handoff update was committed as `0f3a62b` (`docs: record
session-start revalidation`) and pushed successfully to `origin/main`. No code,
BIM model, project state, protected GOLDEN content, or unrelated working-tree
artifact was included in that commit. The next continuation still starts at
the human modal dismissal and fresh R05 reopen/read boundary described above.

## Session-start revalidation (2026-09-21 22:10:13 -03:00)

This session performed the repository session-start protocol only; no production BIM write or state advancement was performed.

### Observed facts

- Branch: `main`; current HEAD and `origin/main` were observed at `6f49873141dc4b954224c43cb403a0e6642a4855`. The durable state still has `last_verified_commit: null`; `f26b7f7` remains the latest commit previously described as the non-Revit regression gate in older handoff evidence.
- `PROJECT_STATE.yaml` remains revision `159`, phase `PHASE_08`, status `PENDING`, next task `P08-T08`, last completed task `P06-T14`, checkpoint `null`, and phase gate `GO_WITH_LIMITATIONS`.
- `.\.venv\Scripts\python.exe -m amanda_agent status` reported a free writer lease, five open blockers, and `P08-T08` as the only ready task.
- No `state/locks/revit-writer.lock` was present during the workspace inspection.
- Two `Revit.exe` processes and five `horizun-mcp.exe` processes were present. Their simultaneous presence is not evidence that a single production target is selected or that the bridge is usable for a write.
- The working tree still contains the known ACL-visible `revit/lab/exports/p06t14/GOLDEN/RC01` deletion reports, modifications in `tests/unit/test_production_layout_bim.py` and Topologic result files, and untracked package/output/production artifacts. These paths were not restored, deleted, staged, or committed.
- Read-only journal inspection found persisted `revit/production/journals/R05.json` with `VERIFIED` in 82/82 records and `R06.json` with `FAILED` in 4/30 records (26 verified). These are historical artifacts from earlier attempts, not fresh evidence from this session, and they do not justify advancing the durable state.

### Reconciliation issue

`PROJECT_STATE.yaml` lists seven blockers, including `REVIT_PIPE_SANDBOX_ACCESS` and `CROSSWALK_GRID_ROOF_GAP`, while `state/blockers.yaml`, `state/status.md`, and the `amanda_agent status` projection expose only five site blockers. This is a durable state/projection mismatch. Do not mark a task or phase complete, or rewrite the state to make the views agree, until the source of truth and blocker projection are reconciled with evidence.

### Tests and GitHub

No tests were executed in this session because no code or behavior was changed. The status command regenerated `state/status.md` as a side effect; that derived change was reverted because the command is documented as read-only and no state transition was intended. The latest recorded handoff evidence remains the prior non-Revit gate and live-attempt records; it was not reclassified as fresh evidence here. The final publication result for this revalidation is recorded below.

### Exact resume instructions

1. Define the concrete next user-authorized task before modifying code, state, or production artifacts.
2. If resuming P08-T08, reconcile the blocker projection first and preserve revision `159` until the evidence supports an explicit state transition.
3. Before any BIM write, re-query the live Revit build, provider health, active document identity, and writer lease; select one verified Revit target and keep the duplicate processes out of the write path.
4. For the R05 continuation, use the normal-user bridge route and require fresh R01-R05 journals, independent reads, and save/close/reopen evidence. A healthy process list or prior journal is insufficient.
## Publication after revalidation

The corrected handoff was committed as `0d5754f` (`docs: record session-start revalidation`) and `git push` returned success for `main -> origin/main` (`6f49873..0d5754f`). A later `git ls-remote` refresh was unavailable because GitHub HTTPS could not connect; no claim beyond the successful push command output is made here.

## Addendum - local R05/R06 overlap repair (2026-09-21)

The next local block addressed the historical R06 overlap failure without
touching Revit or advancing durable production state. R05 can now omit shared
room boundaries when R06 owns them, and R06 trims shared internal-wall
centerlines at perpendicular R05 host walls by the combined half-thickness
clearance. The existing producer namespaces remain unchanged: R05/R06 wall
IDs continue to be the IDs consumed by R07 and R12.

Changed files:

- `src/amanda_agent/bim/stages/layout.py`
- `src/amanda_agent/bim/stages/shell.py`
- `src/amanda_agent/production/layout_bim.py`
- `tests/unit/test_production_layout_bim.py`

The new production regression checks that no R05 wall body overlaps an R06
wall body. The focused stage/production gate was:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_stage_shell.py tests/unit/test_production_layout_bim.py tests/unit/test_stage_layout.py tests/unit/test_stage_openings.py tests/unit/test_run_amanda_production.py -q --basetemp .tmp-pytest-current-focused
36 passed, 0 failed
```

The fresh non-Revit gate was:

```text
.\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q --basetemp .tmp-pytest-current-full2
873 passed, 0 failed
```

No live Revit write, save/close/reopen, state transition, or export promotion
was performed. The persisted `R06.json` remains historical failed evidence and
must be replaced by a fresh normal-user R01-R06 run after the Revit modal is
dismissed. The current live boundary is still the human modal
`Projeto não recentemente salvo`; do not run R07 or promote R06 until the
fresh R05 persistence read and the new R06 journal both show 100% verified
records.

The patch is ready for a narrow commit after `git diff --check`; the protected
`revit/lab/exports/p06t14/GOLDEN/RC01` paths, Topologic result churn, package
copy, and production journals/RVTs remain outside this block.

## Publication and post-commit verification (2026-09-21)

The local repair and this handoff were committed as `10202e6`
(`fix(revit): trim internal walls at shell junctions`) and pushed successfully
with `main -> origin/main`. The post-commit verification repeated the focused
gate and the full non-Revit gate:

```text
Focused: .\.venv\Scripts\python.exe -m pytest tests/unit/test_stage_shell.py tests/unit/test_production_layout_bim.py tests/unit/test_stage_layout.py tests/unit/test_stage_openings.py tests/unit/test_run_amanda_production.py -q --basetemp .tmp-pytest-postcommit-focused
36 passed, 0 failed

Full non-Revit: .\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q --basetemp .tmp-pytest-postcommit-full
873 passed, 0 failed
```

`py_compile` passed for the three changed Python modules. The targeted Ruff
command reported 14 pre-existing `F401` findings in `layout_bim.py` and the
production-layout test; it reported no `E9` or `B023` finding. This is a lint
limitation, not a production or Revit gate.

Final publication state: `HEAD` and `origin/main` both resolve to
`10202e6791afc2d6084c923a14880f0061fd17f1`. The working tree still contains
only the known protected GOLDEN ACL entries, Topologic result churn, and
untracked package/production artifacts. No project-state transition, Revit
write, persistence certification, R07 continuation, or GOLDEN promotion was
performed.

## Session-end UI boundary (2026-09-21)

A final computer-use probe found no native Windows applications exposed to the
session; only browser surfaces were available. Revit therefore could not be
controlled to dismiss `Projeto não recentemente salvo`. No UI action, BIM
write, reopen attempt, or state mutation was made. Resume from the existing
human boundary: dismiss that modal without Save As or changing the target,
then reopen and independently read
`revit/production/working/AMANDA_WORKING_001.20260921-213302.rvt` before any
R06 continuation.

## Session-start revalidation (2026-09-21, current continuation)

This continuation repeated the repository session-start checks and made no BIM
write, provider write, state transition, checkpoint promotion, or export
promotion.

### Fresh evidence

- `amanda_agent doctor` detected Revit 2027 build `27.2.0.39`; its persisted
  environment report still lists `python312` as missing, while the pinned
  project `.venv` remains the executable used for project commands.
- `amanda_agent status` reports `PHASE_08`, `PENDING`, next task `P08-T08`,
  revision `159`, no checkpoint, a free writer lease, and five open site
  blockers.
- `amanda_agent resume` resolves `P08-T08` and repeats the same site-dependent
  final blockers. No task became runnable as a result of this read-only check.
- The process inventory contains Revit PIDs `15608` and `39808` plus multiple
  `horizun-mcp` processes. This is not evidence of a single verified target,
  active-document identity, or modal dismissal.
- The computer-use surface exposes no native Windows application, so the
  Revit reminder `Projeto não recentemente salvo` cannot be dismissed by this
  session. No attempt was made to bypass that boundary through process or file
  manipulation.

### Tests and GitHub

No automated tests were run because no code or behavior changed. The working
tree remains dirty with the pre-existing ACL-visible deletions below
`revit/lab/exports/p06t14/GOLDEN/RC01`, generated Topologic result changes, and
untracked package/production artifacts. They were not restored, deleted,
staged, or committed. The handoff update is the only file changed by this
continuation and must be published separately from those artifacts.

### Exact resume boundary

1. Obtain a native Revit UI session and dismiss `Projeto não recentemente
   salvo` without Save As or changing the saved target.
2. Re-query the normal-user provider, open
   `revit/production/working/AMANDA_WORKING_001.20260921-213302.rvt`, and
   independently read the critical R05 records.
3. Require fresh close/reopen evidence before starting R06. Do not advance
   `PROJECT_STATE.yaml` or infer production PASS from the process list,
   previous journals, or provider health alone.

## Local continuation and workspace cleanup (2026-09-21, current goal)

This continuation advanced the offline side of the production path without
claiming a Revit result. No BIM write, provider write, state transition,
checkpoint promotion, or export promotion was performed.

### Fresh local evidence

- Focused production/stage gate: `36 passed, 0 failed` across shell, layout,
  openings, stage layout, and production-driver tests.
- Full non-Revit gate: `873 passed, 0 failed` in `63.85s` using a temporary
  directory outside the repository.
- Targeted Ruff `B023` check: passed.
- `py_compile` passed for `shell.py`, `layout_bim.py`, and
  `run_amanda_production.py`.
- Production dry-run planned `R01` through `R13`, retained the current layout
  and approval hashes, selected the Revit 2027 template, and reported
  `dry run: nothing written`.
- The persisted `revit/production/journals/R06.json` remains historical
  evidence with `26/30` verified and four overlap failures. Local tests do not
  replace a fresh normal-user R06 journal.

### Cleanup result

- The root contained 198 `.tmp-*` artifacts totaling approximately `8.71 GB`.
- Large pytest result trees were removed through an explicit, path-checked
  cleanup. The root now contains 119 small `.tmp-*` entries totaling about
  `137 KB`.
- Remaining entries include ACL-protected scratch directories and small
  exploratory files. Broad deletion and relocation were rejected or blocked by
  ACL safety checks; no ownership change or forced removal was attempted.
- Source files, RVTs, journals, deliverables, checkpoints, GOLDEN paths, and
  unrelated dirty files were preserved.

### Exact next production action

After a native Revit UI session dismisses `Projeto não recentemente salvo`,
re-query the normal-user bridge, reopen
`revit/production/working/AMANDA_WORKING_001.20260921-213302.rvt`, independently
read the critical R05 elements, and complete the close/reopen persistence gate.
Only then run a fresh R06 with the current code and stop on any unverified
record before considering R07–R13.

## Session-start revalidation and modal retry (2026-09-21, 23:27 -03:00)

This continuation performed the required read-only session checks and retried
the normal-user bridge health probe. No BIM write, provider write, state
transition, checkpoint promotion, export promotion, or production-file
mutation occurred.

### Fresh evidence

- `amanda_agent status` reports `PHASE_08`, `PENDING`, next task `P08-T08`,
  revision `159`, no checkpoint, a free writer lease, and the same five open
  site blockers.
- `amanda_agent resume` still resolves `P08-T08`; the final site-dependent
  blockers remain unchanged.
- `amanda_agent doctor` detects Revit 2027 build `27.2.0.39`, while its
  persisted environment report still lists `python312` as missing. The pinned
  project `.venv` remains the executable used for project commands.
- The explicit `horizun_health` call was removed from the queue after 3000 ms
  because Revit still has the human modal `Projeto não recentemente salvo`
  open. The bridge reported that the request never started, so no model read
  or write happened.
- Computer-use inspection exposed no native Windows applications, only browser
  surfaces. The modal cannot be dismissed through this session.
- The process inventory showed Revit 2027 PIDs `15608` and `39808` and six
  `horizun-mcp` processes. Process presence is not evidence of an active
  document, a single verified target, or modal dismissal.
- `state/locks/revit-writer.lock` is absent.

The `doctor` command refreshed `state/environment-report.json` and
`state/status.md` as derived side effects. Both were restored to their
pre-checkout contents before this handoff update; no generated state report is
part of the next commit.

### Tests and GitHub

No automated tests were run because no code or behavior changed. The existing
working-tree state was preserved: ACL-visible phantom deletions below
`revit/lab/exports/p06t14/GOLDEN/RC01`, generated Topologic result changes,
and untracked package/production artifacts remain outside this documentation
block. The only intended change is this handoff addendum.

### Exact resume boundary

1. Obtain a native Revit UI session and dismiss `Projeto não recentemente
   salvo` without Save As or changing the saved target.
2. Re-query the normal-user bridge, open
   `revit/production/working/AMANDA_WORKING_001.20260921-213302.rvt`, and
   independently read the critical R05 elements.
3. Require fresh close/reopen evidence before starting R06. Do not advance
   `PROJECT_STATE.yaml` or infer production PASS from process presence,
   previous journals, or provider health alone.

## Publication after modal revalidation (2026-09-21, 23:31 -03:00)

The handoff revalidation was committed as `807e66a` (`docs: record modal
revalidation`) and pushed successfully to `origin/main`. Fresh verification
confirmed `HEAD` and `origin/main` resolve to
`807e66aa122bb30505fb032eaf6d64658285f9ba`, with no staged files. The working
tree still contains only the previously preserved dirty reports, ACL-visible
GOLDEN phantom deletions, Topologic result churn, and untracked package/
production artifacts; none were included in the publication.
