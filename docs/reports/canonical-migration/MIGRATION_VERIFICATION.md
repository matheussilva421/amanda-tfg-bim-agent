# Canonical pavilion migration verification

**Date:** 2026-09-23

**Plan:** `docs/superpowers/plans/11-canonical-pavilion-migration.md`, Task 10

**Worktree:** `codex/canonical-pavilion-migration`

**Git anchors:** Task 8 implementation `06c524c`; Task 9 implementation `59684b6`; Task 10 verification `5eb767d` (`test: verify canonical pavilion migration`), pushed to `origin/codex/canonical-pavilion-migration` from `e822b70`.

## Verdict

**Migration-specific gates: PASS. Full non-Revit suite: 929 passed, 9 known baseline failures.** The same nine failure families were already present before Task 10 (baseline: 910 passed, 9 failed); this run introduces no additional failing test. The canonical migration checks, retained legacy contracts, BIM stage regressions, and real dry production compilation pass. The known suite failures are preserved below rather than hidden or repaired by changing private source inputs or installing an unrelated environment.

## Bound design identity

- Parti authority: `USER_DIRECTED`; detail authority: `AGENT_DELEGATED`.
- Run: `AMANDA-RUN-002-PAVILION`.
- Selected candidate: `AMANDA-RUN-002-PAVILION-S02`; status remains `CANDIDATE`, `bim_eligible=false`.
- Approval hash: `75afda89d6a18cd2834bdd571e761ea047305465c6579a4a9d0474e409f91bdf`.
- Layout hash: `20529b1d08c570546641397a4e9fd302a2a23bef917f50bfea6d22824a19f556`.
- Canonical implantation board SHA-256: `d7db84c0696f0018ed0bc0525bcc2128378d05ece8e3e5c09e2162493793de7b`.
- Canonical residential board SHA-256: `12e35091f33352c21691eb083bf479ba2efd44af4c65774c89021b641de4a5c6`.
- Canonical administration board SHA-256: `80cdcccf99154d69ea87943950db420912e949d6320279695a2fd70d44ad286c`.
- Bound program remains 20 people, 626 m² internal, 260 m² external; enclosed and covered ranges remain estimates.
- Historical linear R12 remains `SUPERSEDED_BY_USER_DIRECTION`, SHA-256 `ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29`.

## Task 10 changes and safety boundaries

- Added `PLANNING_ONLY`, which retains the content-bound selection and input versions, blocks every operation, and is rejected by the stage executor before provider dispatch.
- Missing or invalid provider evidence is recorded as `BLOCKED` only for read-only planning. No provider is assigned to those operations; detailed BIM continues to fail closed.
- R07 produces an explicit empty blocked plan when accepted host-wall geometry is unavailable. R09 produces an empty blocked plan when measured accessibility input is absent. No openings, routes, dimensions, or compliance claims are inferred.
- The canonical R04 plan retains one mass operation per each of the seven blocks and the `BIM-00` gate. R05 and later detailing retain `CANONICAL_GEOMETRIC_ACCEPTANCE` gates.
- The production registry currently rejects the `revit.create_wall` Cortex evidence reference: `state/capabilities.yaml` records `cb696597ce833cac36ddee883e056a22863d608d05c089544ba7eeeaaf639171`; the referenced file currently hashes to `3a3a69b5372caf4a51aed3a6904d3d521738597f4df59de4c3bf454613b8bd22`. It remains unusable for writes. Planning reports this as blocked and leaves providers unassigned.
- No Revit document was opened, no provider transport or writer lock was started, no RVT was created, and no geometry was written.

## Test and command evidence

| Gate | Command or evidence | Result |
| --- | --- | --- |
| Canonical reference/layout/QA/selection/run | `pytest tests/unit/test_canonical_reference.py tests/unit/test_canonical_pavilion_layout.py tests/unit/test_canonical_qa.py tests/unit/test_production_selection.py tests/unit/test_build_canonical_pavilion_run.py -q` | 31 passed, 0 failed |
| Retained legacy contracts and migration boundary | `pytest tests/unit/test_architectural_layout.py tests/unit/test_layout_protocol.py tests/unit/test_canonical_qa.py tests/unit/test_production_layout_bim.py tests/unit/test_production_selection.py -q` | 58 passed, 0 failed |
| BIM runner and stage modules | `pytest tests/unit/test_bim_runner.py tests/unit/test_production_layout_bim.py tests/unit/test_run_amanda_production.py tests/unit/test_stage_accessibility.py tests/unit/test_stage_documentation.py tests/unit/test_stage_furniture.py tests/unit/test_stage_landscape.py tests/unit/test_stage_layout.py tests/unit/test_stage_levels.py tests/unit/test_stage_massing.py tests/unit/test_stage_materials.py tests/unit/test_stage_openings.py tests/unit/test_stage_project.py tests/unit/test_stage_rooms.py tests/unit/test_stage_shell.py tests/unit/test_stage_site.py -q` | 129 passed, 0 failed |
| Full non-Revit suite | `pytest tests -m "not revit and not slow" -q --tb=short --basetemp=.tmp-pytest/task10-final2-non-revit-20260923` | 929 passed, 9 failed; failure IDs and causes below |
| Real production dry compile | `python scripts/run_amanda_production.py --rvt .tmp-pytest/task10-dry-only/canonical-dry-plan-final.rvt --max-stage R13` | Exit 0; planned R01–R13; printed S02, all three board hashes, approval/layout hashes and `dry run: nothing written`; target RVT absent afterward |
| Active legacy-builder search | `rg -n "build_courtyard_layout" src scripts` | Only definition/export in `src/amanda_agent/design/architectural_layout.py`; no `scripts/` matches |
| Ruff | `ruff check` on changed Python files | 9 import-order issues introduced during edits were fixed. 10 existing findings remain at unchanged legacy lines (`SIM102`, `UP031`, `ISC004`, `C408`). |
| Whitespace | `git diff --check` | Passed |

The focused counts overlap and must not be summed. Final pytest used the project Python 3.12 environment and a worktree-local basetemp.

### Full-suite failures

1. `tests/project/test_provenance_integrity.py::test_all_immutable_source_files_exist_and_match_manifest_hashes` — private ignored `docs/source/` inventory does not match the tracked manifest.
2. `tests/test_p08_inputs.py::test_p08_source_version_binds_every_manifest_file_without_new_sources` — frozen P08 source-manifest hash is stale.
3. `tests/test_p08_inputs.py::test_p08_freeze_binds_versions_and_current_file_hashes` — an old P08 frozen input hash is stale.
4. `tests/unit/test_design_refine.py::test_refinement_publishes_schema_valid_distinct_finalist_artifacts` — immutable source `programa_necessidades.pdf` is absent from this worktree's local source set.
5. `tests/unit/test_ingest_validation.py::test_validation_accepts_missing_topography_as_a_limited_study` — ingest returns `NO_GO` for the existing manifest state.
6. `tests/unit/test_ingest_validation.py::test_validation_report_is_short_portuguese_and_lists_exact_blockers` — same `NO_GO` source-manifest condition.
7. `tests/unit/test_task_graph.py::test_phase_level_plan_edges_exist_as_task_dependencies` — duplicate `P00-T01` in `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md`.
8. `tests/unit/test_topologic_spike.py::test_topologic_spike_measures_space_and_persists_json_report` — `.venv-topologic` is not provisioned.
9. `tests/unit/test_topologic_spike.py::test_topologic_spike_names_a_network_blocked_export_instead_of_failing` — same missing `.venv-topologic` environment.

The same nine failure families were recorded at the pre-Task-10 full-suite baseline (910 passed, 9 failed). No private source manifest was rewritten, no PDF was fabricated, and no dependency environment was installed to make these checks appear green.

## Exact continuation

Plan 11 Task 11 state migration is applied in worktree revision 172. `PROJECT_STATE.yaml` selects S02 under `USER_DIRECTED` parti authority and points to `P08-CAN-T07`; old linear `P08-T13..T19` tasks are suspended and their evidence remains intact. The archived R12 file was re-read at 4,345,856 bytes with SHA-256 `ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29`. The worktree-local canonical target does not exist. Before creating it, perform the fresh live Revit/provider and writer-lease checks in Plan 11 Task 12. BIM-00 is required before R04 geometry; `CANONICAL_GEOMETRIC_ACCEPTANCE` and visual regressions R04/R06/R08/R12/R13/R15 remain open, site/accessibility evidence is incomplete, and R16 remains blocked.
