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

Commits `9fe08bc3365d592b5159d39d6ee6a88f79b20d31` and `f466418561c101bf27bcf7e1fdd328018a683b32` are pushed to `origin/codex/canonical-pavilion-migration`. No pull request has been created. Plan 11 Task 1 is test/lint green, committed, and pushed; Task 2 is green, committed as `3276976d1f47c9486d4de8f36086600042d57386`, and its handoff/checklist checkpoint `5059cab11d897636e793eb1f59617768b4e8790b` is pushed. Task 3 is committed as `4c24bacd93e60e5e1150eb70d6560d04d7050d46`; the Task 3 handoff/checklist checkpoint is pushed. Task 4 is committed as `0cbf0fc8987831feeba492421da0f93549e4deb5`; its handoff/checklist checkpoint is pushed. Task 5 is committed as `ccfd410fe65ee074c0cdc76bff89e875a51bb443`; its handoff/checklist checkpoint is included in the current branch push. Private `docs/source/` inputs are ignored and must not be published. Original `main` checkout changes and untracked old packages remain untouched except the specifically requested local RVT archive/duplicate cleanup and prior package validation output.

## Exact resume

1. Continue with Plan 11 Task 7 using TDD; Task 6 consumers are now canonical and its reference inventory is recorded below.
2. `scripts/run_amanda_production.py` remains an interim active entrypoint with a legacy builder call; it fails closed at active selection. Migrate it in Task 8 and do not invoke it before then.
3. The new selection remains a `CANDIDATE` and is not BIM-eligible. Do not update `PROJECT_STATE.yaml` or execute Revit writes before the Task 10 migration proof and preceding gates.
4. Before any new Revit geometry, pass BIM-00 on a clean target; never copy R12 geometry.
5. Before detailing, pass `CANONICAL_GEOMETRIC_ACCEPTANCE`; run board visual regression at R04/R06/R08/R12/R13/R15. R16 stays blocked until all required geometry/visual and verified site inputs are resolved.
6. Preserve the GPT-6 Luna Xhigh-only subagent constraint. That exact option was unavailable in the current tool catalog; continue locally unless it appears.
7. Update `PROJECT_STATE.yaml` only after Plan 11 Task 10 migration proof passes. Current live state remains PHASE_08/P08-T13/R12 and has not been promoted.

## Task 2 update

- RED: `tests/unit/test_layout_protocol.py` failed to import the not-yet-created protocol module, as expected.
- GREEN: command `python -m pytest -p no:cacheprovider --basetemp=.tmp-pytest/plan11-task2-green tests/unit/test_layout_protocol.py tests/unit/test_architectural_layout.py -v` — 18 passed, 0 failed, Python 3.12.14.
- Ruff check passed; formatting applied.
- Added `LayoutProtocol`, `ExternalSpaceProtocol`, and immutable `ExternalSpace`; added a patio/veranda adapter to legacy `CourtyardLayout`. Updated the legacy builder's module docstring so it cannot be mistaken for active architectural truth. No legacy geometry code changed; all 16 pre-existing architectural layout tests passed.
- Task 2 and handoff checkpoint are committed and pushed. Task 3 is now GREEN and awaits its commit; Task 4 is next.

## Task 3 update — canonical pavilion layout

- RED: the focused test initially failed to import the not-yet-created `canonical_pavilion_layout` module, as expected.
- Implemented a deterministic normalized metric layout with 7 separate volumes: public two-level administration/arrival, 3 sleeping pavilions, 1 communal/dining pavilion, separate services/capacitation, and child sector.
- Official internal room instances are each assigned once for exactly 626 m²; residential IDs are distributed across the four residential pavilions. Five external spaces derive their names/areas from the versioned program and total exactly 260 m².
- Four covered external connectors meet the 80 m² central protected patio. Room/floor collision, building separation, landscape/building separation, area derivation, and hash input coverage are represented in focused tests. Coordinates explicitly remain `NORMALIZED_METRIC_REFERENCE_NOT_SURVEY`; site fit is `UNVERIFIED`.
- GREEN focused: 9 passed, 0 failed. Combined Task 1–3 regression: 31 passed, 0 failed, Python 3.12.14. Ruff check and `git diff --check` passed.
- No Revit document was opened or written. BIM-00, new solution selection/approval binding, `CANONICAL_GEOMETRIC_ACCEPTANCE`, and visual regression gates remain pending. Task 4 is now GREEN and awaits its commit; Task 5 is next. R16 remains blocked by the required gates and unverified site data.
- Task 3 implementation commit: `4c24bacd93e60e5e1150eb70d6560d04d7050d46` (`feat: build canonical pavilion layout`). The implementation and this handoff checkpoint are being published to `origin/codex/canonical-pavilion-migration`.

## Task 4 update — canonical parti QA

- RED: `tests/unit/test_canonical_qa.py` failed to import the not-yet-created QA module, as expected.
- Implemented all 12 rubric IDs with explicit `PASS`, `FAIL`, or `BLOCKED` results and evidence. The legacy single-bar layout fails `CANON-001`, `CANON-004`, and `CANON-012`; the pavilion model passes structural/program checks.
- `CANON-010` fails closed if a material-deviation register is absent or malformed. `CANON-011` stays `BLOCKED` until all R04/R06/R08/R12/R13/R15 regression entries pass against the three profile hashes. The normalized geometry limits are documented as non-site constraints.
- GREEN: 5 focused QA tests passed; combined Tasks 1–4 regression: 36 passed, 0 failed, Python 3.12.14. Ruff check and `git diff --check` passed.
- No Revit model was opened or written. BIM-00, canonical solution selection/approval binding, geometric acceptance, and stage visual regressions remain pending.
- Task 4 implementation commit: `0cbf0fc8987831feeba492421da0f93549e4deb5` (`test: enforce canonical pavilion parti`). This commit and the Task 4 handoff checkpoint are being published to `origin/codex/canonical-pavilion-migration`. Task 5 is next.

## Task 5 update — user-directed parti and canonical selection

- RED: new selection constants/history API were absent; after adding the rejection case, the active builder incorrectly accepted the legacy bar. Both expected REDs were observed before their fixes.
- Active solution ID is `AMANDA-RUN-002-PAVILION-S01` in collision-free run `AMANDA-RUN-002-PAVILION`; no existing run/decision ID collision was found.
- The selection carries two content-bound decisions: parti decision authority `USER_DIRECTED`, detailed layout authority `AGENT_DELEGATED`. Three canonical image hashes and the official program PDF SHA-256 are referenced in both decision evidence and solution geometry/approval hash.
- Detailed solution status is `CANDIDATE`; `bim_eligible=false` while site fit, canonical geometric acceptance, and stage regressions remain open. Invalid image/program SHA-256 values are rejected.
- `build_selection` now accepts canonical pavilion layouts only. `build_legacy_selection` is explicitly named for old evidence/tests; the legacy R12 record remains `SUPERSEDED_BY_USER_DIRECTION` with one archived RVT hash and `geometry_reuse_allowed=false`. The old BIM test fixture is explicitly labelled LEGACY.
- The current `scripts/run_amanda_production.py` still directly constructs the old layout and calls the active builder; it now fails closed before any write. Migrate and test this runner under Plan 11 Task 8; do not invoke it until then.
- GREEN: 6 focused selection tests; 39 tests passed across selection/legacy BIM/decision-register/design-model coverage; Tasks 1–4 canonical regression remains 36 passed. Ruff passed on changed selection/model/test files. No Revit model was opened or written.
- `PROJECT_STATE.yaml` and persistent decision registers remain unchanged pending offline run assembly and migration proof. Task 5 implementation commit: `ccfd410fe65ee074c0cdc76bff89e875a51bb443` (`feat: bind production selection to canonical pavilion boards`). This commit and the Task 5 handoff checkpoint are being published to `origin/codex/canonical-pavilion-migration`. Task 6 is next.

## Task 6 update — canonical QA, previews and study exports

- RED: the entrypoint AST test failed on the old direct import in `scripts/qa_layout.py`, as expected. After switching test fixtures to the canonical layout, the old QA/DXF/IFC consumers also failed on missing bar-only fields and a MultiPolygon footprint; these were the expected migration failures.
- Migrated `scripts/qa_layout.py` to the canonical profile/layout and rubric. It now reports `BLOCKED` for site fit, unmeasured enclosed/covered areas, missing stage visual regressions and Revit-only checks. The official 20-person, 626 m² internal and 260 m² external invariants remain checked; 783–814 m² and 850–950 m² remain estimates, not measurements.
- Rebuilt study previews for normalized implantation plus ground/upper floor plans. Removed generated elevations/section based on invented heights/openings. The PDF consumer now accepts only those three previews and labels the package as a draft when canonical QA is blocked.
- DXF preserves seven block outlines, internal rooms by level, five external program spaces and four covered connectors. IFC4 now carries a spatial inventory with level/area/2D WKT metadata and emits no invented walls, doors, windows, slabs or 3D geometry. Both remain STUDY exports, not final Revit deliverables.
- Reference inventory is in `docs/reports/canonical-migration/LEGACY_BUILDER_REFERENCE_CLASSIFICATION.md`. The remaining direct legacy call in `scripts/run_amanda_production.py` is ACTIVE but fail-closed pending Task 8. Legacy implementation and negative-control/adapter/compiler tests remain explicitly classified as historical coverage.
- GREEN: Task 6 focused group: 19 passed, 0 failed. Tasks 1–5 relevant regression group: 68 passed, 0 failed. Ruff passed on all changed/new Task 6 files; `git diff --check` passed. Actual canonical profile load/QA: 25 checks, 0 FAIL, 9 BLOCKED, expected exit 2. Actual renderer produced 3 PNG/SVG pairs in `.tmp-pytest/task6-live/drawings`; visual inspection is a structural preview check only and does not pass CANON-011.
- Tracked `docs/reports/p08-layout-qa.*` and `docs/reports/study-drawings/` still contain the prior linear study outputs; they were preserved during this code migration. Regenerate/replace them only with the canonical run package after Task 9 and validate before removing stale generated plan packages.
- No Revit document was opened or written. `PROJECT_STATE.yaml` and production decisions remain unchanged. Task 6 commit `089bba5` (`refactor: route production consumers to canonical pavilion layout`) is pushed to `origin/codex/canonical-pavilion-migration`. Continue with Task 7.
