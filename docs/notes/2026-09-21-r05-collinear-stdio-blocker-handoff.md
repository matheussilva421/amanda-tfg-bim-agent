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
