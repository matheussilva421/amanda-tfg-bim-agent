# Handoff — production save idempotency and Revit modal blocker (2026-09-22)

## Status

The production driver's final save operation now uses an idempotency key scoped
to the current deliberate production attempt. The offline code and regression
gates are green. The live Revit continuation remains blocked before any new
read or write because the native modal `Projeto não recentemente salvo` is
still open.

No BIM write, provider write, save/close/reopen certification, project-state
transition, checkpoint promotion, export promotion, or GOLDEN promotion was
performed in this block.

## Change

- `scripts/run_amanda_production.py` adds `_new_idempotency_key(label, run_key)`
  and uses it for the final `horizun_save_document` call.
- `tests/unit/test_run_amanda_production.py` adds a regression for the
  attempt-scoped save key.
- The generated `state/status.md` drift from a read-only status command was
  restored to the repository `HEAD` content and is outside this change.

The root cause was a constant final-save key (`amanda-save-1`) in a driver that
already gives each production attempt its own run key. A retry or later attempt
could therefore receive the bridge's recorded answer for an older save instead
of executing the intended save operation.

## TDD and validation

RED against the pre-change `HEAD` implementation:

```text
pytest tests/unit/test_run_amanda_production.py -q
ImportError: cannot import name `_new_idempotency_key`
```

GREEN:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_run_amanda_production.py -q --basetemp .tmp-pytest-save-green
2 passed, 0 failed
```

Regression gate:

```text
.\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q --basetemp .tmp-pytest-idempotency-full
875 passed, 0 failed
```

Additional checks:

- `py_compile` passed for the changed production driver and unit test.
- `git diff --check` passed for the changed files.
- `horizun_health` was retried read-only and did not start: Revit reported the
  modal `Projeto não recentemente salvo` and removed the queued request after
  3000 ms. The computer-use surface exposed no native Windows application,
  so the modal could not be dismissed in this session.

## Git and unrelated state

The branch was `main` at `ddbf4ba`, matching `origin/main` at session start.
The intended patch is limited to the two files above. Pre-existing ACL-visible
phantom deletions below `revit/lab/exports/p06t14/GOLDEN/RC01`, generated
Topologic result changes, and untracked `.codex`, package/output, and
`revit/production` artifacts remain unstaged and must not be restored or
committed as part of this block.

The first `git restore -- state/status.md` attempt was rejected because Git
could not create `.git/index.lock`; the generated file was then restored by
writing the exact `HEAD` blob directly, without changing the index.

## Exact resume instructions

1. Obtain a native Revit UI session and dismiss `Projeto não recentemente
   salvo` without Save As or changing the saved target.
2. Re-run `horizun_health`, select one verified Revit PID if needed, and
   independently reopen/read
   `revit/production/working/AMANDA_WORKING_001.20260921-213302.rvt`.
3. Require fresh close/reopen evidence for the R05 model before starting R06.
4. Run a fresh normal-user R06 with the current driver and stop on any
   unverified record. Do not promote `PROJECT_STATE.yaml` from historical
   journals, process presence, provider health, or offline tests.
5. If Git index permissions remain blocked, publish the narrow patch manually
   with:

   ```powershell
   git add -- scripts/run_amanda_production.py tests/unit/test_run_amanda_production.py docs/notes/2026-09-22-save-idempotency-modal-blocker-handoff.md
   git commit -m "fix(revit): scope production save idempotency keys"
   git push origin main
   ```

## Pending

- Publish the narrow code/test/handoff block if the Git index becomes writable.
- Dismiss the Revit modal through a human-controlled native UI session.
- Complete the fresh R05 reopen gate, then continue R06 only with fresh
  WRITE→READ→VERIFY evidence.
