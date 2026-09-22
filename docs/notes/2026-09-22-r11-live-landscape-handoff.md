# Amanda TFG BIM Agent — R11 live landscape handoff

Date: 2026-09-22  
Task: P08-T13  
Status: RUNNING; R09, R10 and R11 PASS_WITH_WARNINGS; R12 next

## Live target

Canonical production file:
`revit/production/working/AMANDA_WORKING_001.rvt`

Revit 2027 build `27.2.0.39`, PID `25996`, Horizun `1.3.3`, one writer, non-workshared. The selected design is `AMANDA-RUN-001-S01` with `AGENT_DELEGATED` authority, approval hash `bf7dcca735de166f100a6687f441ac7247ccf31f5e9e28a1bd4837591acba7ef`, and `AMANDA_REVIEW_PENDING` retained.

## R11 completed

The official program remains 20 people, 626 m² internal and 260 m² external; the historical 42-person hypothesis remains rejected. The landscape compiler has five first-class external zones: patio interno protegido 80 m², jardim terapêutico 80 m², horta comunitária 30 m², exercícios e alongamento 30 m², and playground 40 m². Four visual/functional layers per zone carry no extra programmed area.

The live RVT has no verified terrain, boundary, north, site coordinates or external `OST_Rooms`. Therefore the applied R11 positions are explicitly `PROVISIONAL_ASSUMPTION` study coordinates derived from the adopted layout extents and adjacency narrative. They are reversible study geometry and must not be read as a survey, site plan or normative landscape solution. No source refactor was needed.

The production dry run passed for R01–R11 with layout hash `9410f296b0d3a258a51971a6e2a35cd404f8018ca28ba5d6f36003516808539d`, approval hash `bf7dcca735de166f100a6687f441ac7247ccf31f5e9e28a1bd4837591acba7ef`, and 25 R11 operations.

The registry-approved route for `revit.create_landscape_element` is the Horizun Python fallback. Final preflight passed with zero warnings, source hash `e7397e1aa28b9907240ca917120378df6f9cfe7979281d34fe709fd3b042042d`, and the single apply key was `amanda-r11-landscape-20260922-v1`. The bridge classified the Python result as `completed_unverified`; no blind retry was made. The independent host query is the proof.

Independent live readback reconciled the state:

- 78 `Modelos genéricos` total
- 25 unique `R11-REQ-07-...` marks
- 25 `AMANDA-R11|...|PROVISIONAL_ASSUMPTION` instance comments
- 25 positive bounding boxes
- whole model after reopen: 4140 elements, 52 rooms, 87 openings, 78 walls, 238 furniture, 78 GenericModels, coverage complete and 0 unreadable

## Persistence evidence

Save was verified at SHA-256:
`f4dd2d9cf72ccd7fa1703d543d11e6b657ae5893254a3f20e7fee34a7a8b0699`

Size: `4325376` bytes.

Checkpoint:
`revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R11-landscape-20260922.rvt`

`verify_checkpoint` returned `true`.

Preview:
`revit/production/previews/R11-landscape-3D-20260922.png`

The preview is a real 1400x855 capture from view 221538, classified STUDY and uncalibrated; the view was restored and the capture rollback returned `RolledBack`. It visibly preserves the current pavilions/rooms and the provisional external study markers.

## Tests

Command:
`.\\.venv\\Scripts\\python.exe -m pytest tests/unit/test_stage_landscape.py tests/unit/test_stage_furniture.py tests/unit/test_production_layout_bim.py tests/test_p08_inputs.py tests/unit/test_checkpoints.py -q -p no:cacheprovider --basetemp .tmp-pytest-delivery-r11`

Result: `44 passed, 0 failed in 15.76s`. JSON/YAML validation passed, the R01–R11 compile dry run passed with nothing written, and `git diff --check` passed for the intended R11/state files.

## Boundaries

R11 does not prove terrain, property boundary, site occupancy, frontage count, true north, final planting, irrigation, external furniture procurement or construction documentation. Site topography, boundary and occupancy remain blocking; frontage count and true north remain degrading. No FINAL or GOLDEN claim is valid.

## Resume exactly

Next substage: R12 materials within P08-T13.

Start with Horizun health, active canonical path, R11 checkpoint/hash reconciliation and a fresh whole-model summary. Preserve source, canonical, checkpoints and GOLDEN artifacts. Use typed capability first; if the registry-approved fallback is required, preflight with zero warnings and perform one deliberate write followed by independent re-query, save, close/reopen, checkpoint and preview.

Relevant files:

- `docs/reports/delivery-mode/R11-live-evidence-2026-09-22.json`
- `revit/production/journals/R11-live-20260922.json`
- `revit/production/previews/R11-landscape-3D-20260922.png`
- `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R11-landscape-20260922.rvt.manifest.json`
- `state/task-graph.yaml`
- `PROJECT_STATE.yaml`
