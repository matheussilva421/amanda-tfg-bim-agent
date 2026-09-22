# Handoff — QA reconciliation status correction (2026-09-21)

## Status

The offline layout QA reporter now preserves a failed program reconciliation
as `FAIL`. The production/Revit path remains blocked at the human Revit UI
boundary and no BIM write, persistence promotion, export promotion, or GOLDEN
promotion was performed in this block.

## Change

- `scripts/qa_layout.py` now reads the reconciler's `result.value` instead of
  the diagnostic `status` field. Only `PASS` and `PASS_WITH_WARNINGS` produce
  a passing check.
- `tests/unit/test_qa_layout_script.py` locks the observed behavior: the
  current delegated layout reports `program.reconciliation` as `FAIL` because
  required program spaces are missing from the reconciler input.
- `docs/reports/p08-layout-qa.json` and `docs/reports/p08-layout-qa.md` were
  regenerated. The report is intentionally `FAIL` with one program failure
  and five `MODEL_PENDING` checks; it is not a Revit QA result.

## TDD and validation

RED against the pre-change `HEAD` implementation:

```text
expected status FAIL, observed PASS
```

GREEN and regression:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_qa_layout_script.py -q --basetemp .tmp-pytest-qa-redgreen
1 passed, 0 failed
```

The reporter command was also run and correctly returned exit code 1 with
`verdict: FAIL`, `checks: 25 failed: 1 model_pending: 5`.

Full offline gate:

```text
.\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q --basetemp .tmp-pytest-qa-full
874 passed, 0 failed
```

`py_compile` and `git diff --check` passed for the changed code/report scope.

## Current blockers and exact resume

- `PROJECT_STATE.yaml` remains revision 159, `PHASE_08`, `P08-T08`,
  `GO_WITH_LIMITATIONS`; site blockers and `CROSSWALK_GRID_ROOF_GAP` remain
  open in the durable state.
- A native Revit UI session is still required to dismiss
  `Projeto não recentemente salvo`, reopen
  `revit/production/working/AMANDA_WORKING_001.20260921-213302.rvt`, and
  independently read the R05 records before any R06 continuation.
- Do not infer production PASS from the local QA report, process presence,
  historical journals, or provider health.
- After the human boundary is cleared, require fresh close/reopen evidence,
  then run the current production code from a normal-user PowerShell and stop
  on any unverified R06/R07 record.

## Git status

Only the QA correction, generated QA report, this handoff, and the new unit
test belong to this block. Existing ACL-visible GOLDEN phantom deletions,
Topologic result churn, and untracked package/production artifacts are
pre-existing and must remain unstaged unless a later task explicitly handles
them.

## Publication

The verified QA block was committed as `670b9ae` (`fix(qa): preserve program
reconciliation failures`) and pushed successfully to `origin/main`. The
working tree still has only the pre-existing unrelated dirty and untracked
paths described above.

## Durable state reconciliation

After re-reading the live evidence, `PROJECT_STATE.yaml` was corrected to
revision `160`:

- removed the stale `CROSSWALK_GRID_ROOF_GAP:BLOCKING` entry; the registered
  grid/roof capability evidence hashes to
  `d4f19a3c1e57621c7a1f8acd77c3a8219ef5d02ff2e642941d41c4a5b938675b`, records
  `persisted: true`, and independently reads one grid and one roof after
  reopen;
- changed `layout_qa` to `FAIL (25 checks, 1 failed, 5 MODEL_PENDING)` so the
  durable summary agrees with the regenerated QA report.

`amanda_agent status` now reports revision `160`, P08-T08 still pending, a
free writer lease, and the five site blockers. No task was advanced and no
production claim was made.
