# Handoff — canonical pavilion migration — updated 2026-09-23

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

## Task 7 update — multi-block BIM planning and write gates

- Added a canonical R03 planning path for `LEVEL-01` and admin `LEVEL-02`. The local zero datum and 3.20 m floor-to-floor value are labelled `DESIGN_ASSUMPTION` with non-probative evidence; every R03 operation carries `BIM-00` in `blocked_by`. No elevation is represented as survey evidence.
- Added a separate R04 mass for each of the seven canonical blocks. Admin mass is two storeys; service, child and all four residential pavilions remain one storey. The 3.20 m per-floor height is marked `PROVISIONAL_ASSUMPTION` for visual study only. Every mass operation is blocked by BIM-00, and the preflight records that gate as `BLOCKED`.
- Canonical R05 shell planning emits floors per block and level plus four separate covered connector slabs. It does not create a continuous gallery, connector walls or roofs with invented heights. Shell operations remain blocked until `CANONICAL_GEOMETRIC_ACCEPTANCE`; the executor and generic operation dispatcher both fail closed before calling providers.
- R08 room operations use the canonical logical level assignment and remain acceptance-blocked. The canonical wall builder emits no guessed wall hosts/partitions before accepted geometry.
- TDD evidence: expected RED was observed for the shared dispatcher blocker, shell executor blocker, R03 study-assumption mode, and prior R03/R04 refusal cases. After implementation, focused command `pytest tests/unit/test_production_layout_bim.py tests/unit/test_stage_shell.py tests/unit/test_stage_levels.py -q` using the existing Python 3.12.14 environment: **40 passed, 0 failed**. `git diff --check` passed.
- Ruff check still reports 10 pre-existing findings at unchanged legacy lines in the touched modules/tests; the three new findings in `levels.py` were fixed and the focused tests were rerun green.
- A prior full-suite baseline was **910 passed, 9 failed**. The failures were outside the Task 7 changes: stale flat-path provenance/P08 hashes after source relocation, duplicate task id in the combined-plan parser, and missing `.venv-topologic`. Re-run the required non-Revit regression at Task 10 and record its current result there.
- No Revit document was opened or written; no write was retried. `PROJECT_STATE.yaml`, production selection state and writer lease were not changed. BIM-00 is still pending before any R03/R04 geometry write. Geometric acceptance, all required visual regressions, site verification and R16 remain pending/blocked.
- Task 7 implementation commit `98dba47` (`feat: plan multi-block canonical BIM stages`) is pushed to `origin/codex/canonical-pavilion-migration`; the tree was clean immediately after push. After this checkpoint, continue Plan 11 Task 8: add regression tests and harden `scripts/run_amanda_production.py` so superseded R12 cannot become the canonical target. Do not run the production script before that migration.

## Task 8 update — runner hardening and board-aligned S02

- Task 8 TDD RED was observed for rejecting the archived R12 target/byte-identical copy, reporting the canonical source hashes, and replacing the active legacy layout import. Runner tests also retain the writer-lock, safe target, idempotency, and provider activation contracts.
- Revised the normalized pavilion arrangement to match the canonical relationships: communal/refectory pavilion northeast of the garden, three sleeping pavilions in the other quadrants, curved covered paths, child sector northwest, administration/public arrival south, and separate services to the east. The model remains normalized and is not a site survey.
- Updated QA to reject a wrong communal quadrant and straight connector centerlines. Changed the immutable connector model/hash inputs and selection evidence accordingly. New candidate identity is `AMANDA-RUN-002-PAVILION-S02`; it supersedes unexecuted provisional S01. Approval hash: `75afda89d6a18cd2834bdd571e761ea047305465c6579a4a9d0474e409f91bdf`. Canonical source hashes remain implantation `d7db84c0696f0018ed0bc0525bcc2128378d05ece8e3e5c09e2162493793de7b`, residential `12e35091f33352c21691eb083bf479ba2efd44af4c65774c89021b641de4a5c6`, administration `80cdcccf99154d69ea87943950db420912e949d6320279695a2fd70d44ad286c`.
- Focused command: `pytest tests/unit/test_canonical_pavilion_layout.py tests/unit/test_canonical_qa.py tests/unit/test_production_selection.py tests/unit/test_run_amanda_production.py tests/unit/test_production_layout_bim.py tests/unit/test_dxf_export.py tests/unit/test_ifc_export.py -q --tb=short` — **70 passed, 0 failed**. Ruff passed on all changed implementation/test files; `git diff --check` passed.
- Fresh PNG/SVG study previews were generated under `.tmp-pytest/canonical-board-review-20260923`. Visual inspection confirmed the intended normalized block relationships, but these are schematic evidence only: they do not pass R04 Revit visual regression or `CANONICAL_GEOMETRIC_ACCEPTANCE`.
- Runner dry invocation printed all three board hashes, S02, and the approval hash, then exited nonzero at the existing detailed-BIM eligibility guard before capability/provider/Revit calls. No target file was created, no Revit document was opened, and no BIM write occurred. The wrapped process exit was 1; the runner's intended gated return is 2.
- BIM-00 remains pending. Horizun/Revit 2027 was previously verified healthy, with no open document, other client, queued/running job, or acquired writer lease. A canonical target path/checkpoint has not been established. Keep all Revit geometry writes blocked until BIM-00 evidence exists.
- **Sequencing ruling:** global detailed eligibility cannot be the only gate for R04. Once BIM-00 passes, R04 massing must be available to create the geometric/visual acceptance evidence; R05 and later detailing remain blocked until `CANONICAL_GEOMETRIC_ACCEPTANCE`. Dry planning may compile plans but must not write. Cost if wrong: no route to generate required R04 acceptance evidence, or unsafe pre-acceptance detailing.
- `PROJECT_STATE.yaml`, task graph, and persistent decision registers remain unchanged pending Task 10 migration proof. R16 remains blocked by unverified site data, accessibility evidence, and required R04/R06/R08/R12/R13/R15 visual regressions.
- Task 8 commit `06c524c` (`fix: prevent canonical rebuild from reusing legacy linear RVT`) is pushed to `origin/codex/canonical-pavilion-migration`; push advanced remote from `cea23fa` to `06c524c`. Exact resume: start Plan 11 Task 9, add an offline canonical run-artifact builder with TDD, bind S02 geometry/program/board hashes into deterministic solution metadata, and keep all runtime outputs local/ignored unless repository policy requires committed metadata.

## Task 9 update — offline canonical run artifacts

- Added `scripts/build_canonical_pavilion_run.py` and `tests/unit/test_build_canonical_pavilion_run.py`. The builder writes a deterministic run with a typed solution, separate geometry JSON, selection decisions, canonical QA report, normalized SVG preview, `run.json`, and SHA-256 artifact manifest. It stages a new output directory atomically, accepts an identical existing run idempotently, and refuses a conflicting output.
- TDD RED was observed first for missing artifacts/false success on a CRITICAL QA failure. A direct CLI invocation then exposed a second issue: imports depended on external `PYTHONPATH`; an end-to-end subprocess test reproduced it, and the script now bootstraps the repository `src` directory itself.
- Focused regression command covering the builder, canonical reference/layout/QA, selection, runner, BIM planning, DXF and IFC: **77 passed, 0 failed**. Ruff and `git diff --check` passed.
- Ran the actual builder into `design-engine/runs/AMANDA-RUN-002-PAVILION/`. It produced 7 small files (~203 KB total); re-running the command accepted the matching output unchanged. The six manifest-listed artifacts all match their recorded byte counts and SHA-256 values.
- Persisted IDs: run `AMANDA-RUN-002-PAVILION`, solution `AMANDA-RUN-002-PAVILION-S02`; approval hash `75afda89d6a18cd2834bdd571e761ea047305465c6579a4a9d0474e409f91bdf`; layout hash `20529b1d08c570546641397a4e9fd302a2a23bef917f50bfea6d22824a19f556`. The three canonical board hashes are carried in solution, run metadata and manifest. The 20-person program reconciles to 626 m² internal and 260 m² external; the 783–814 m² enclosed and 850–950 m² covered ranges remain estimates in the bound program snapshot.
- Canonical QA: 12 checks, 11 PASS, 0 FAIL, 1 BLOCKED (`CANON-011`, pending the required stage visual regressions). Pydantic readback confirmed the solution approval hash, `USER_DIRECTED` parti authority, `AGENT_DELEGATED` provisional detailing, and `bim_eligible=false`. Run metadata records `revit_calls=0`; this is not a Revit deliverable or a geometric-acceptance pass.
- Files generated: `design-engine/runs/AMANDA-RUN-002-PAVILION/run.json`, `canonical-qa.json`, `selection.json`, `layout-preview.svg`, `artifact-manifest.json`, and finalist `solution.json`/`geometry.json`. The run output is small and follows the repository convention of tracking earlier run JSON; the private source boards and RVT binaries remain untracked/excluded.
- No project state or decision register was promoted. No Revit document was opened or written. BIM-00, R04 visual regression, `CANONICAL_GEOMETRIC_ACCEPTANCE`, later visual regressions and R16 remain pending.
- Task 9 commit `59684b6` (`feat: build offline canonical pavilion run`) is pushed to `origin/codex/canonical-pavilion-migration`; remote advanced from `f73b759` to `59684b6`.
- Exact resume: Plan 11 Task 10 — run `pytest tests -m "not revit and not slow" -q`; search for active legacy builder calls; execute the production dry plan through R13 without provider writes; record exact gate evidence in `docs/reports/canonical-migration/MIGRATION_VERIFICATION.md`. Only after that proof may Task 11 migrate `PROJECT_STATE.yaml` and task/decision history.

## Task 10 update — migration proof with preserved baseline failures

- Added `PLANNING_ONLY` as content-bound, non-executable planning. Every operation is blocked, and the generic stage executor refuses this mode before dispatch. Missing capability evidence is reported as `BLOCKED` for planning only; no unverified provider is assigned. `DETAILED_BIM` still reports capability mismatches as `FAIL`.
- Added truthful empty blocked plans for canonical R07 when accepted wall-host geometry is absent and R09 when explicit measured accessibility input is absent. Neither stage invents geometry or compliance values.
- TDD RED was observed for R07 host refusal, unselectable capability status, and the R01 dry operation attempting to name an unverified provider. GREEN now includes all the final checks below.
- Final BIM runner/stage regression: **129 passed, 0 failed**. Canonical reference/layout/QA/selection/run tests: **31 passed, 0 failed**. Retained legacy and migration-boundary tests: **58 passed, 0 failed**.
- Required full non-Revit regression: **929 passed, 9 failed**. The same nine failure families were recorded in the prior 910/9 baseline: private ignored `docs/source/` inventory and stale P08 hashes, missing local `programa_necessidades.pdf`, two ingest `NO_GO` cases, duplicate `P00-T01` in the combined plan, and two missing `.venv-topologic` cases. No new failing test was introduced; exact IDs and explanations are in `docs/reports/canonical-migration/MIGRATION_VERIFICATION.md`.
- Real CLI dry plan to R13 exited 0 and printed candidate S02, all board hashes, approval/layout hashes, stages R01–R13, and `dry run: nothing written`. The temporary RVT target was absent afterward. Unit guards also verified no provider transport or writer lock in dry mode.
- For a deliberately invalid capability registry, all seven R04 masses remain separate while operations have no provider/fallback and carry `PLANNING_ONLY` plus `CAPABILITY_EVIDENCE_BLOCKED`. Production registry still rejects the recorded Cortex wall fixture hash; that evidence remains blocked and cannot authorize writes.
- `rg -n "build_courtyard_layout" src scripts` finds only the legacy module definition/export; there are zero script references. The reference classification was updated.
- Ruff import-order findings introduced by the edits were fixed. Final `ruff check` reports 10 previously existing style findings at unchanged code lines; `git diff --check` passes.
- No Revit document was opened, no geometry was written, and `PROJECT_STATE.yaml` remains unchanged. The selected S02 candidate remains `bim_eligible=false`. Task 10 migration-specific gates pass with the full-suite failures explicitly carried as baseline limitations.
- Verification report: `docs/reports/canonical-migration/MIGRATION_VERIFICATION.md`. Files changed include the BIM stage preflight/operation planners, production runner/compiler, focused tests, Plan 11 Task 10 checklist, and legacy-reference classification.
- Task 10 verification commit `5eb767d` (`test: verify canonical pavilion migration`) is pushed to `origin/codex/canonical-pavilion-migration`; remote advanced from `e822b70` to `5eb767d`. The worktree was clean immediately after this commit/push. Proceed to Plan 11 Task 11 state/decision/task-graph migration; keep BIM-00 before any new Revit geometry, and keep acceptance, visual-regression, site and accessibility gates explicit. R16 remains blocked.

## Task 11 update — canonical state and task-graph migration (2026-09-23)

- Applied migration to `PROJECT_STATE.yaml` revision 172. Active solution is `AMANDA-RUN-002-PAVILION-S02`, parti authority `USER_DIRECTED`, detail authority `AGENT_DELEGATED`, solution approval hash `75afda89d6a18cd2834bdd571e761ea047305465c6579a4a9d0474e409f91bdf`, layout hash `20529b1d08c570546641397a4e9fd302a2a23bef917f50bfea6d22824a19f556`.
- Cleared the old R12 checkpoint from the active field and retained it as `historical_r12_checkpoint`. Active Revit stage is `PRE_R04`; no canonical RVT exists. The intended relative path is `revit/production/working/AMANDA-RUN-002-PAVILION-S02.rvt`, status `NOT_CREATED`.
- Re-read the single archived linear R12 file: `revit/production/archive/superseded-linear/AMANDA-RUN-001-S01-R12-linear-historical-20260922.rvt`, 4,345,856 bytes, SHA-256 `ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29`. Geometry reuse is prohibited.
- Appended decisions `DEC-CANONICAL-R12-SUPERSESSION-001`, `DEC-CANONICAL-PARTI-001`, and `DEC-CANONICAL-DETAIL-002`, each hash-validated by `DecisionRegister`. The three board hashes and archive hash are recorded in the user-directed supersedence record.
- Suspended the old linear `P08-T13..T19` chain without removing its evidence. Added canonical namespaced tasks `P08-CAN-T01..T19`; T01..T06 are complete with warnings where site/non-Revit baseline limits apply, and `P08-CAN-T07` is the next task. Updated Phase 08 plan headings to match these unique IDs.
- TDD: the four migration contract tests were RED against S01/missing records/active linear tasks, then GREEN: `pytest tests/unit/test_canonical_state_migration.py -q` — 4 passed, 0 failed. Focused regression: 46 passed; 1 known baseline failure remains in `tests/unit/test_task_graph.py::test_phase_level_plan_edges_exist_as_task_dependencies` because the combined plan contains duplicate `P00-T01`. The decision-register expectation was updated to include the three required canonical decisions.
- Ran `python -m amanda_agent status`; it reports PHASE_08 RUNNING, revision 172, `P08-CAN-T07` READY, writer lease free, and five site blockers. The status file's stored provider health is not a fresh live-provider probe.
- No Revit document was opened or written. Both checkout lock-file paths are absent; the canonical target is absent. Next: complete Plan 11 Task 12 with a fresh live Revit/provider/lease check and verify the existing generated run manifest; then create the clean target (P08-CAN-T07) and require BIM-00 before R04 geometry (P08-CAN-T08). Keep canonical geometric acceptance and visual regression gates active; R16 remains blocked.

## Task 12 update — BIM-00 preacceptance route is still fail-closed (2026-09-23)

- Branch/worktree: `codex/canonical-pavilion-migration`, HEAD `af9c44e` (`docs: switch production state to canonical pavilion run`), tracking `origin/codex/canonical-pavilion-migration`. The canonical RVT remains absent; no Revit geometry was written.
- Live read-only health: Horizun 1.3.3, Revit `27.2.0.39`, PID `31036`; no active/open document; no queued/running jobs. Health also reports `other_clients_connected=1` inside its 10-minute window and lists PID `22456` as already terminated. This is not a one-writer pass; wait for a fresh zero count before any Revit write.
- The provider tool catalog marks `horizun_audit_model` read-only and supports `require_coordinate_facts: [length_units]`. The provider toolmap lists it as a `model_scan` alternative, but `state/capabilities.yaml` has no `model_scan` evidence record. Do not use the alternative on a production target until the required Tool Lab evidence and registry authorization exist.
- No disposable `.rvt` fixture exists under `revit/lab`; only prior lab/export directories are present. Use a fresh copy derived from the installed metric template for the new read-only audit capability check; do not open or reuse the archived linear R12 as a fixture.
- TDD offline work: the new BIM-00 authorization contract tests were RED on the missing module, then the contract and R04-only canonical preacceptance compiler tests passed together (**35 passed, 0 failed**). This includes binding to target/solution/approval/layout/board hashes and preserving `CANONICAL_GEOMETRIC_ACCEPTANCE`.
- Follow-up command `pytest tests/unit/test_bim00_write_gate.py tests/unit/test_production_layout_bim.py tests/unit/test_run_amanda_production.py -q -p no:cacheprovider --basetemp=.tmp-pytest/task12-safe-green -k "not routes_unaccepted_selection"` passed **46 tests, 0 failed**; the archive-byte integrity test is included. The runner orchestration test intentionally remains RED: the current driver still exits before compiling any unaccepted selection. This is the correct current fail-closed behavior while the complete evidence path is unavailable.
- Automatic review rejected (1) activating R01–R04 execution before a tested live BIM-00 evidence/authorization sequence exists, and (2) adding a live evidence collector before audit output semantics and state transitions are validated. Do not work around either rejection. Validate the exact read-only audit output and close/checkpoint/reopen sequence in Tool Lab, then retry a narrow activation patch with tests that prove no R03/R04 dispatch can occur unless BIM-00 passes.
- Files currently modified/untracked in the worktree: `scripts/run_amanda_production.py`, `src/amanda_agent/bim/stages/__init__.py`, `src/amanda_agent/production/layout_bim.py`, `src/amanda_agent/bim/write_gate.py`, and three corresponding unit-test files. None of these Task 12 changes are committed or pushed yet. No provider call wrote a model.
- Ruff on these files reports nine existing style findings at unchanged lines in `layout_bim.py` and its older test helpers; the one new finding in the runner helper was corrected. `git diff --check` passes.
- Next: refresh the live health only after the stale client window has elapsed; require healthy build/PID, `other_clients_connected=0`, and no open document. Then create one disposable lab `.rvt`, test `length_units` via the actual read-only audit, independently verify its output and document identity, and record exact output/hash. Only then implement and test the BIM-00 evidence collector and the sequential target-save/checkpoint/reopen/gate path. Keep R05+ and R16 blocked pending geometric/visual acceptance.
- Current tests used the project Python 3.12.14 virtualenv at the original checkout with `PYTHONPATH=src`; keep pytest cache disabled and use a worktree-local `--basetemp`.

## Continuation — R04 provider permission review blocker (2026-09-23)

- P08-CAN-T07 is `PASS_WITH_WARNINGS`: real target `revit/production/working/AMANDA-RUN-002-PAVILION-S02.rvt` exists, originated from the installed Revit 2027 metric template, and was closed/checkpointed/reopened. R01 checkpoint SHA-256 is `f5d4b0f52eca096a29ca3f34bb50d9a83d76f1461ee1d35bc3eb4563318678f7`; a typed, bypass-cache model query found 0 OST_Mass with complete coverage.
- BIM-00 is PASS and authorizes the exact seven R04 volumes. Evidence file: `revit/production/evidence/AMANDA-RUN-002-PAVILION-S02-BIM-00.json`, SHA-256 `f62c7d7de431fdbbdce82094239827ddb8901ef7ae503f01d3306ab65a1dcce9`. Selection S02 approval hash/layout hash and all three canonical image hashes match the loaded source profile.
- Live Revit remains healthy: Horizun 1.3.3, Revit 27.2.0.39, exact S02 target active, one open document, `other_clients_connected=0`, no queued/running jobs. After the access review blocked R04, the owned writer lease was gracefully released (generation 2); reacquire and revalidate before any later write.
- No R04 mass was written. The registered project adapter maps `revit.create_mass` to `horizun_execute_python`. A safe live `horizun_create_elements` dry-run on S02 returned `unsupported kind 'mass'`, `valid=0`, `transaction_status=not_started`, `write_started=false`; this confirms the typed endpoint cannot make the required volume. Its fallback block recommended Python, but the automatic reviewer had rejected `horizun_request_python_access` because it grants indefinite arbitrary Python across files, batches and Revit restarts, broader than this operation. Do not retry through `horizun_execute_python` or another indirect executor. P08-CAN-T08 remains `BLOCKED_BY_TOOL`.
- Safe continuation requires a bounded, typed Horizun mass capability or a policy-approved permission route. Do not repair/use the RevitCortex capability while the intended Horizun operation remains available; no provider fallback was attempted.
- Site coordinates and the 3.20 m visual heights remain `PROVISIONAL_ASSUMPTION` for STUDY. R05+ remain blocked pending canonical geometric acceptance. Focused tests were not rerun because their inputs/code are unchanged; no full suite was run.

- GitHub checkpoint: `a67c8ed517c5585885e5873da4a3eea0e51d7612` (`feat: gate canonical R04 with BIM-00`) was pushed to `origin/codex/canonical-pavilion-migration`; it contains the gate, focused regressions, S02 status and raw BIM-00 evidence.
- Next user/policy dependency: expose a one-operation typed mass write, or decide whether to pursue a separate approval path for the persistent Python permission. The previous request was rejected at automatic review before a Revit consent dialog appeared.

## Recheck — no safe typed R04 mass route (2026-09-23)

- Loaded `CanonicalReferenceProfile` from the active worktree root. Status is `CANONICAL_DESIGN_REFERENCE`; the three image hashes exactly match `PROJECT_STATE.yaml`. The root `docs/source/references/canonical/` is present, so no asset copy or hash change is needed.
- Fresh Horizun health still identifies S02 as the active saved target on Revit 2027 build 27.2.0.39, one open document, zero other clients, and no queued/running jobs. The writer lease was released and must be reacquired/revalidated before a future write.
- The live typed `horizun_create_elements` rehearsal rejected `kind=mass` before transaction start (`valid=0`, `write_started=false`). The exposed RevitCortex catalog has no dedicated mass-creation tool, and the project capability registry contains no approved RevitCortex mass evidence; no Cortex hash was modified or provider write attempted.
- The only proven Horizun mass route is the arbitrary Python executor. Automatic review rejected its broad persistent permission. No safe production write route remains available; `P08-CAN-T08` stays `BLOCKED_BY_TOOL`, with no R04 geometry or Revit preview.
- Before this handoff update, branch `codex/canonical-pavilion-migration` was clean at pushed commit `82b257d` on origin. No broad test suite was run; existing focused gates and hashes were reused.
