# Handoff — canonical pavilion migration — 2026-09-22

## Status

Work continues on `codex/canonical-pavilion-migration` in the isolated worktree `C:\Users\slvma\.codex\worktrees\canonical-pavilion-migration\Projeto Amanda`, based on `7daf6f67a9980705d96bf25e0b648305feeef39b`. The original checkout remains dirty from pre-existing user files; no reset/restore was run. The production folder in the original checkout was changed only for the requested R12 archive and exact duplicate cleanup below.

## Completed

- Read and validated the extracted package named by the user. Static validator: 13/13 checks passed. Its embedded checksum list has 74 entries: 73 match and one stale goal document differs from the sidecar ZIP. The extracted folder named in the goal remains authoritative.
- Installed the Plan 11/spec/reference source bundle into the isolated worktree. `docs/source/` is deliberately ignored by the repository because it contains private academic source material; those local files were not staged. Tests use synthetic inputs plus a local-only integration test for the actual private board hashes.
- Confirmed canonical board hashes:
  - implantation: `d7db84c0696f0018ed0bc0525bcc2128378d05ece8e3e5c09e2162493793de7b`
  - residential: `12e35091f33352c21691eb083bf479ba2efd44af4c65774c89021b641de4a5c6`
  - administrative: `80cdcccf99154d69ea87943950db420912e949d6320279695a2fd70d44ad286c`
- Frozen linear `AMANDA-RUN-001-S01` R12 as one local historical RVT at `revit/production/archive/superseded-linear/AMANDA-RUN-001-S01-R12-linear-historical-20260922.rvt`.
  - SHA-256: `ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29`; bytes: 4,345,856.
  - Disk-only Revit inspection reports format 2027, non-workshared, and did not open/upgrade the file. Horizun reports no active/open document; build 27.2.0.39.
  - Status is `SUPERSEDED_BY_USER_DIRECTION`; canonical decision authority is recorded as `USER_DIRECTED`; linear geometry is historical only.
  - Units and linked-file metadata were not inspected and remain unknown. The original tracked R12 checkpoint sidecar was preserved unchanged; the archive register records its path and SHA-256.
- Classified 7 exact duplicate pairs among 77 production RVTs by SHA-256 and size. Archived the R12 checkpoint and removed its duplicate working RVT; removed six other working copies whose matching checkpoints remain. Post-cleanup: 70 RVTs, 70 unique hashes, 0 duplicate pairs. No other production RVTs were touched.
- Plan 11 Task 1 TDD is implemented in `src/amanda_agent/design/canonical_reference.py` and `tests/unit/test_canonical_reference.py`.
  - RED: import failed because the module did not yet exist (expected).
  - GREEN command: `python -m pytest -p no:cacheprovider --basetemp=.tmp-pytest/plan11-task1 tests/unit/test_canonical_reference.py -v`, using the existing project `.venv` Python 3.12.14 and worktree `PYTHONPATH`.
  - Result: 4 tests passed, 0 failed, including local checks for the three actual private board hashes and missing/mismatched asset rejection.
  - Ruff check passed on both files; Ruff formatting applied.
- The initial pytest default temp location was denied by the sandbox. Re-running with a worktree-local `.tmp-pytest` parent resolved it; no code failure remained.
- Program source confirms 20 people, 626 m² internal, 260 m² external, 783–814 m² enclosed estimate, and 850–950 m² covered estimate. 42 is not adopted.
- Site is CPChoque in Lagoa Nova, Natal, with TFG-reported area/frontages; topography remains placeholders and the canonical map inset conflicts. Parcel boundary, survey, and topography are still unverified.

## Files in the isolated worktree

- Added the unified migration spec, Plan 10/11, combined plan, source handoff, execution handoff, and archive register.
- Updated `docs/superpowers/plans/00-master-implementation-plan.md` and `08-amanda-production-run.md`.
- Added `src/amanda_agent/design/canonical_reference.py` and `tests/unit/test_canonical_reference.py`.
- Added `revit/production/archive/superseded-linear/manifest.json` (the binary RVT is in the original checkout and remains ignored by Git).
- The `.superpowers/sdd/11-canonical-pavilion-migration/progress.md` ledger is intentionally ignored and remains the task-level execution log.

## GitHub

No commit, PR, or push yet. Plan 11 Task 1 is test/lint green; its planned feature commit remains pending. Private `docs/source/` inputs are ignored and must not be published. Original `main` checkout changes and untracked old packages remain untouched except the specifically requested local RVT archive/duplicate cleanup and prior package validation output.

## Exact resume

1. Commit Task 1 implementation/test and the current documentation/archival register without adding ignored `docs/source/` or any RVT binaries.
2. Continue Plan 11 Task 2 with RED-first tests for the stable layout protocol.
3. Keep old linear selection/R12 superseded; create a new solution and approval hash bound to the three board hashes and official program before any new geometry.
4. Do not write new Revit geometry until BIM-00 passes. Start a clean target, never copy R12 geometry.
5. Before detailing, pass `CANONICAL_GEOMETRIC_ACCEPTANCE`; run board visual regression at R04/R06/R08/R12/R13/R15. R16 stays blocked until all required geometry/visual and verified site inputs are resolved.
6. Preserve the GPT-6 Luna Xhigh-only subagent constraint. That exact option was unavailable in the current tool catalog; continue locally unless it appears.
7. Update `PROJECT_STATE.yaml` only after Plan 11 Task 10 migration proof passes. Current live state is still PHASE_08/P08-T13/R12 and has not been promoted.
