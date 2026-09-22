# Handoff - P08-T08 offline conceptual preparation (2026-09-22)

## Scope and boundary

This block implements only the offline, testable preparation seam for P08-T08. It does not close P08-T08 and is not real Revit evidence. No BIM write, save/close/reopen, checkpoint promotion, PROJECT_STATE.yaml update, export, or GOLDEN promotion occurred.

## Implemented

- Added scripts/bim_concept_candidates.py.
- Added tests/unit/test_bim_concept_candidates.py.
- The preparation:
  - reads and validates a content-bound solution.json identity;
  - compiles exactly R01, R02, R03, and R04 with CONCEPT_ONLY;
  - refuses any stage after R04;
  - verifies block count/area and site area against solution geometry;
  - writes JSON plans, metrics-verification.json, an SVG preview, and candidate-bundle.json in a new solution_id directory;
  - records provider_evidence_scope=SYNTHETIC, live_revit_evidence=false, writer_lease_acquired=false, and save_close_reopen=PENDING_LIVE_REVIT;
  - hashes generated artifacts in manifest.json;
  - never acquires the shared writer lease and never writes an RVT.
- The batch wrapper prepares F01/F02 in separate directories and preserves deterministic path order.

## TDD

RED:
```text
pytest tests/unit/test_bim_concept_candidates.py -q -p no:cacheprovider
ImportError: No module named scripts.bim_concept_candidates
```

GREEN:
```text
pytest tests/unit/test_bim_concept_candidates.py -q -p no:cacheprovider
4 passed
```

## Validation

- AST for both files: PASS.
- Ruff for both files: PASS.
- Focused P08-T08/BIM:
  ```text
  pytest tests/unit/test_bim_concept_candidates.py tests/unit/test_bim_plan.py tests/unit/test_bim_solution_compiler.py tests/unit/test_production_layout_bim.py -q -p no:cacheprovider
  33 passed
  ```
- Available non-Revit suite, excluding groups requiring ignored artifacts or unavailable environments:
  ```text
  pytest tests -m "not revit and not slow" --ignore tests/project/test_provenance_integrity.py --ignore tests/test_p08_inputs.py --ignore tests/unit/test_design_refine.py --ignore tests/unit/test_ingest_validation.py --ignore tests/unit/test_topologic_spike.py -q -p no:cacheprovider
  863 passed
  ```
- Full non-Revit attempt in the isolated worktree: 871 passed and 11 failed because of checkout prerequisites, with no traceback in the new files:
  - docs/source is absent from the worktree;
  - source hashes in test_p08_inputs.py do not match this checkout;
  - .venv-topologic is not provisioned.
- py_compile could not create scripts/__pycache__ because of worktree ACL; AST was used for syntax verification and passed.

## Git

- Worktree: C:\Users\slvma\.codex\worktrees\p08-t08-concept-offline\Projeto Amanda.
- The checkout was created from a1cf328 at detached HEAD and still needs a branch/commit.
- The main checkout keeps its pre-existing 41 changes/artifacts; none were restored, deleted, or staged.
- This handoff should be committed with only the script and test.

## Pending

1. To satisfy the live part of P08-T08, obtain a visible, operable Revit session, probe provider/PID/document read-only, and run each candidate with WRITE -> READ -> VERIFY.
2. Obtain independent save/close/reopen and Revit-produced 3D/site previews; the SVGs here are offline STUDY previews.
3. Record real journals/checkpoints before considering any state advance.
4. Do not treat OFFLINE_PLAN_READY, SYNTHETIC, or local tests as PASS_REAL.

## Resume

```powershell
Set-Location 'C:\Users\slvma\.codex\worktrees\p08-t08-concept-offline\Projeto Amanda'
git status --short --branch
git log -1 --oneline
& 'C:\Users\slvma\Downloads\Github\Projeto Amanda\.venv\Scripts\python.exe' -m pytest tests/unit/test_bim_concept_candidates.py tests/unit/test_bim_plan.py tests/unit/test_bim_solution_compiler.py tests/unit/test_production_layout_bim.py -q --basetemp 'C:\Users\slvma\Downloads\Github\Projeto Amanda\.tmp-p08-t08-resume' -p no:cacheprovider
```

Then review the diff, commit it on a codex/ branch, push according to project authorization, and keep live work stopped until the Revit UI blocker is cleared.
