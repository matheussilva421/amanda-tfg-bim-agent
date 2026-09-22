# Amanda TFG BIM Agent — R12 live materials handoff

Date: 2026-09-22  
Task: P08-T13  
Status: RUNNING; R09, R10, R11 and R12 PASS_WITH_WARNINGS; R13 next

## Stop point

The user explicitly requested that the session stop after creating this handoff
and updating Git. Do not start R13 in this session. Resume from the exact
canonical RVT and checkpoint below.

## Live target

Canonical production file:
`revit/production/working/AMANDA_WORKING_001.rvt`

Revit 2027 build `27.2.0.39`, product `20260716_1515(x64)`, PID `25996`,
Horizun `1.3.3`, contract `8b9600f5274d7dffb6e5bd5f`, one writer, non-workshared.
The selected design is `AMANDA-RUN-001-S01` with `AGENT_DELEGATED` authority,
approval hash
`bf7dcca735de166f100a6687f441ac7247ccf31f5e9e28a1bd4837591acba7ef`, and
`AMANDA_REVIEW_PENDING` retained.

## R12 completed

The official program remains 20 people, 626 m² internal and 260 m² external;
the historical 42-person hypothesis remains rejected. The R12 compiler dry run
passed for R01–R12 with layout hash
`9410f296b0d3a258a51971a6e2a35cd404f8018ca28ba5d6f36003516808539d` and
approval hash
`bf7dcca735de166f100a6687f441ac7247ccf31f5e9e28a1bd4837591acba7ef`.

R12 applied the two catalogued study material intents by wall type:

- 46 external walls: `Alvenaria ceramica revestida`, intent of durability and
  simple maintenance;
- 32 internal walls: `Divisoria leve`, intent of acoustic comfort and reversible
  layout review.

Both material intents remain `PROVISIONAL_ASSUMPTION` study decisions, not a
final product specification. The live model had 78 walls before and after the
operation. The approved provider route was `revit.assign_material` through the
registry-approved Horizun Python fallback; final preflight passed with zero
warnings and submitted source SHA-256
`2d5a3e343c61c704d697baf4c6ecea12a27d96ef54116d67f4f6fa3d680199cf`.

The single apply key was `amanda-r12-materials-20260922-v1`. It created or
reused materials `Alvenaria ceramica revestida` (id 222867) and `Divisoria leve`
(id 222868), targeted two wall types, changed two type compound structures,
reported 78/78 applied and left no transaction open. No blind retry was made.

Independent direct Revit API readback after apply returned 78/78 verified walls,
46 external material assignments, 32 internal assignments and zero failures.
After exact close/reopen, the active canonical path remained correct and the
independent readback again returned 78/78 with the same 46/32 split. The typed
whole-model query returned 4142 elements, 52 rooms, 87 openings, 78 walls, 238
furniture, 78 GenericModels and 95 materials, with complete coverage and zero
unreadable elements.

## Persistence evidence

Canonical save changed the hash from
`f4dd2d9cf72ccd7fa1703d543d11e6b657ae5893254a3f20e7fee34a7a8b0699` to
`ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29` at
`4345856` bytes. Close/reopen preserved the exact canonical path, Revit 2027
version and file size, with no discarded unsaved changes.

Checkpoint:
`revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R12-materials-20260922.rvt`

The checkpoint manifest is present and records SHA-256
`ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29`,
`4345856` bytes, stage `R12_MATERIALS`, and source equality. Checkpoint
verification returned `true`.

Preview:
`revit/production/previews/R12-materials-3D-20260922.png`

The preview is a real 1400x855 capture from view 221538, classified STUDY and
UNCALIBRATED, with SHA-256
`438e294422befd8ce9d6000cbab33518843c884ae2b4c0ce903cdaf0c4881d99`.
The view was restored and capture rollback returned `RolledBack`. It visibly
preserves the current pavilion/room model and provisional landscape markers;
it is not a FINAL or GOLDEN presentation.

## Tests and validation

Focused R12 gate:

`.\\.venv\\Scripts\\python.exe -m pytest tests/unit/test_stage_materials.py tests/unit/test_stage_landscape.py tests/unit/test_stage_furniture.py tests/unit/test_production_layout_bim.py tests/test_p08_inputs.py tests/unit/test_checkpoints.py -q -p no:cacheprovider --basetemp .tmp-pytest-delivery-r12`

Result: `48 passed, 0 failed in 8.30s`.

Compile gate:

`.\\.venv\\Scripts\\python.exe scripts/run_amanda_production.py --rvt revit/production/working/AMANDA_WORKING_001.rvt --max-stage R12`

Result: `PASS_DRY_RUN`; R01–R12 planned; nothing written by the compiler.

## Boundaries and blockers

R12 does not prove terrain, property boundary, site occupancy, frontage count,
true north, material procurement, final specification, normative compliance or
construction documentation. `SITE_TOPOGRAPHY`, `SITE_BOUNDARY` and
`SITE_OCCUPANCY` remain BLOCKING; `SITE_FRONTAGE_COUNT` and `SITE_TRUE_NORTH`
remain DEGRADING; `AMANDA_REVIEW_PENDING` remains open. No FINAL or GOLDEN
claim is valid.

## Git and excluded changes

The repository is on `main` tracking `origin/main`. The R12 evidence commit is
to contain only the state files, this handoff, the R12 checkpoint manifest and
the R12 preview. Existing unrelated deletions under
`revit/lab/exports/p06t14/GOLDEN/RC01/`, modified Tool Lab results, package
directories, `.codex/` and `release/` remain uncommitted and must be preserved.

## Resume exactly

1. Read this handoff and reconcile `PROJECT_STATE.yaml`, `state/status.md` and
   `state/task-graph.yaml` with live files.
2. Verify Horizun health, the active canonical path, the R12 checkpoint hash and
   a fresh whole-model summary before any write.
3. Continue P08-T13 at R13 documentation using the typed capability first,
   preserving all source, canonical, checkpoint and GOLDEN artifacts.
4. For any new BIM write, use WRITE → independent READ → VERIFY → save → exact
   close/reopen → checkpoint → real preview.
