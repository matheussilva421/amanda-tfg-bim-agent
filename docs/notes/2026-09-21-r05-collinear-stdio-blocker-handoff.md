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
