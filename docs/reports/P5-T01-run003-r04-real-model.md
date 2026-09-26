# P5-T01 — RUN-003 R04 real-model report

**Date:** 2026-09-26

**Result:** `PASS_WITH_WARNINGS`
**Scope:** R04 canonical massing only. No R05, GeoNatal research, or RC01 changes.

## Preflight and identity

BIM-00 passed at `revit/production/evidence/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY-BIM-00.json`. The target was created from the stock Portuguese Revit 2027 template and bound to `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`, study snapshot `study-detail-004`, the four current canonical boards, and the official program PDF. The live provider was Horizun 1.3.3 on Revit 2027 build 27.2.0.39; its 73/73 command registry was clean, the target was active and targetable, and there were no other clients. The S02 lease was safely resolved; the exclusive RUN-003 lease was acquired for the write.

Coordinates remain `LOCAL_NORMALIZED_STUDY_NOT_SURVEYED`. Heights remain provisional at 3.20 m per floor (6.40 m for the two-storey administration block).

## R04 geometry written

Seven `OST_Mass` elements were written to the real RUN-003 RVT. Typed queries and geometry/property checks passed after each write and again after cold reopen.

| Element | Revit ID | Measured area | Height |
|---|---:|---:|---:|
| `MASS-ADMIN_ACOLHIMENTO` | 328657 | 237.4073 m² | 6.40 m |
| `MASS-CHILD_SECTOR` | 328658 | 94.4807 m² | 3.20 m |
| `MASS-RES_PAV_A` | 328659 | 103.0385 m² | 3.20 m |
| `MASS-RES_PAV_B` | 328660 | 103.3452 m² | 3.20 m |
| `MASS-RES_PAV_C` | 328661 | 74.0868 m² | 3.20 m |
| `MASS-RES_PAV_D_COMMUNAL` | 328662 | 111.4485 m² | 3.20 m |
| `MASS-SERVICE_CAPACITATION` | 328663 | 446.5008 m² | 3.20 m |

The service/capacitation mass retains its six courtyard/garden interior rings. Its first write rolled back because one profile edge (0.119 mm) was below Revit's measured ShortCurveTolerance (0.7804 mm); a fresh idempotency key and corrected script were used. The successful retry script is `MASS-SERVICE_CAPACITATION-v2.py`, SHA-256 `dc9b3366df270deba2b837435f444cdc180cd1bf570e78230b2e33941c3461f5`. The profile then omitted one vertex with maximum deviation 0.0232 mm, below the measured tolerance. The resulting area delta was 0.00000148 m². This adjustment is recorded in the machine-readable evidence.

## Persistence and evidence

Horizun save returned `saved_verified` with target SHA-256 `120935963a19af4c654894d00f057304237ec7f98115f0eecb266e3a91aaef20` and 4,603,904 bytes. The POST-R04 checkpoint has the same SHA-256; its file hash and manifest were independently recomputed and `CheckpointManager.verify_checkpoint` passed. Direct filesystem hashing of the working RVT was denied while Revit held it open, so the report distinguishes the save result from the independently hashed checkpoint. The exact target was closed, reopened without upgrade, and queried again: seven masses, complete coverage, zero unreadable results. The temporary anchor document was closed; final live health confirmed RUN-003 active as the sole open document. The writer lease was released after model closeout.

The detailed record, including per-element IDs, unique IDs, typed queries, geometry readbacks, idempotency/job references, verification layers, and cold-reopen results, is `revit/production/evidence/AMANDA-RUN-003-R04/real-model-evidence.json`. Python results remain labelled `self_reported_verified` / `host_verified=false`; typed model queries independently confirm each element identity and bounding box before and after reopen.

No usable screenshot was produced: attempted captures rolled back and restored the view, and top-view calibration failed. Therefore CANON-011 and P6 visual/geometric acceptance remain open. No visual acceptance or R05 claim is made.

## Tests

- `python -m pytest tests/unit/test_bim_horizun_invoker.py -q`: 59 passed.
- The sub-tolerance-edge regression reproduced RED before the adapter correction and passed after it.
- No broad test suite was run.

## Open divergences and next task

The service profile has the documented sub-tolerance vertex omission. The coordinate basis is not a survey/cadastral boundary; floor heights are provisional. A reliable visual comparison against all four boards is still required for CANON-011. Five site-data blockers remain unresolved.

Next task: **P6-T01 — R04 visual/geometric acceptance**. R05 remains blocked until acceptance passes.
