# Handoff — R06 internal-wall type mapping and live Revit blocker (2026-09-22)

## Status

The R06 production retry is **not yet executed**. The latest live evidence has
52/52 verified R05 records, followed by a stale/current-attempt `R06.json`
with 30/30 internal-wall records failed at the typed provider verification
boundary. Every R06 failure had the same error:
`Requested properties do not match the committed element.`

The live Revit bridge is currently blocked before any new read or write by the
native modal `Projeto não recentemente salvo` (`#32770`). `horizun_health`
confirmed that the request never started and no model mutation occurred from
that probe. The computer-use surface exposed no targetable native window in
this session, so the modal remains human-controlled.

No BIM write, save/close/reopen certification, checkpoint promotion,
`PROJECT_STATE.yaml` transition, export promotion, or GOLDEN promotion was
performed in this block.

## Root cause and patch

The production compiler's R06 stage emits the semantic compiler field
`properties.wall_type_id = "INT_WALL_01"`. The `_stamp` bridge adapter only
translated `properties.type_id`, so R06 operations reached the typed provider
without the actual Revit wall type. The installed template's verified internal
wall type is ElementId `220` (`Interior - 138 mm Divisória (1-hr)`).

Changed files:

- `src/amanda_agent/production/layout_bim.py`
  - maps `revit.create_internal_wall` operations to `type_id=220` while
    retaining `wall_type_id` as the compiler-level semantic field;
  - leaves shell wall type translation unchanged.
- `tests/unit/test_production_layout_bim.py`
  - adds a regression asserting every stamped R06 operation carries
    `type_id=220`.
- this handoff.

The fix is deliberately limited to the compiler/provider boundary. It does
not alter room geometry, requirements, the R05 shell, the active Revit file,
or the durable project state.

## TDD and validation

RED against the pre-change implementation:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_production_layout_bim.py::test_layout_stage_bridges_template_internal_wall_type -q --basetemp .tmp-pytest-r06-type-red
1 failed: KeyError: 'type_id'
```

Focused GREEN:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_production_layout_bim.py::test_layout_stage_bridges_template_internal_wall_type tests/unit/test_production_layout_bim.py::test_layout_stage_builds_internal_walls_for_every_partition -q --basetemp .tmp-pytest-r06-type-green
2 passed, 0 failed
```

Focused provider/layout gate:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_production_layout_bim.py tests/unit/test_stage_layout.py tests/unit/test_bim_horizun_invoker.py -q --basetemp .tmp-pytest-r06-focused
76 passed, 0 failed
```

Offline regression gate:

```text
.\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q --basetemp .tmp-pytest-r06-full
876 passed, 0 failed
```

Additional checks:

- `py_compile` passed for the changed compiler, regression test, and
  production driver.
- `git diff --check` passed for the changed code/test scope.
- A read-only `horizun_health` retry was blocked by the persistent native modal;
  it reported that nothing ran and nothing was written.

## Git state

The narrow code/test patch is prepared but still needs commit and push. The
working tree also contains pre-existing ACL-visible phantom deletions under
`revit/lab/exports/p06t14/GOLDEN/RC01`, generated Topologic result changes,
untracked package/output trees, `.codex`, and `revit/production` artifacts.
Do not restore, delete, or stage those paths as part of this block.

Before publication, stage only:

```powershell
git add -- src/amanda_agent/production/layout_bim.py tests/unit/test_production_layout_bim.py docs/notes/2026-09-22-r06-internal-wall-type-handoff.md
git commit -m "fix(revit): map internal wall template type"
git push origin main
```

## Exact resume instructions

1. Have the owner dismiss `Projeto não recentemente salvo` in the native Revit
   UI without Save As or changing the intended saved target. Check every
   monitor; the dialog may be outside the visible Revit window.
2. Re-run `horizun_health` and `get_document_info` read-only. Confirm the
   selected Revit PID and active document path independently.
3. Preserve the existing failed R06 journal as historical evidence. Start a
   fresh normal-user production attempt from the current driver, which creates
   a new timestamped RVT, and run through R06 with the verified target:

   ```powershell
   .\.venv\Scripts\python.exe scripts/run_amanda_production.py `
     --rvt revit\production\working\AMANDA_WORKING_001.rvt `
     --max-stage R06 --revit-pid <published-revit-pid> --execute
   ```

4. Require fresh R01→R06 journals with every record `VERIFIED`, then perform
   independent save/close/reopen evidence before any R07 continuation. Stop on
   any provider error, warning that changes the acceptance boundary, or
   unverified readback.
5. Do not advance `PROJECT_STATE.yaml` from the local test gate, process
   presence, historical journals, or provider health alone.

## Pending

- Publish the narrow compiler/test/handoff commit and push it to `origin/main`.
- Clear the human Revit modal boundary.
- Run a fresh R01→R06 attempt and independently verify persistence.
- Only after that decide whether R07 is safe to start.
