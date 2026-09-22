# Amanda TFG BIM Agent — R10 live furniture handoff

Date: 2026-09-22  
Task: P08-T13  
Status: RUNNING; R09 and R10 PASS_WITH_WARNINGS; R11 next

## Live target

Canonical production file:
`revit/production/working/AMANDA_WORKING_001.rvt`

Revit 2027 build `27.2.0.39`, PID `25996`, Horizun `1.3.3`, one writer, non-workshared. The selected design is `AMANDA-RUN-001-S01` with `AGENT_DELEGATED` authority, approval hash `bf7dcca735de166f100a6687f441ac7247ccf31f5e9e28a1bd4837591acba7ef`, and `AMANDA_REVIEW_PENDING` retained.

## R10 completed

The official program remains 20 people, 626 m² internal and 260 m² external; the historical 42-person hypothesis remains rejected. The R10 compiler initially exposed a concrete live mismatch: it planned furniture for explicit external sectors although the production RVT contains 52 internal rooms and no external `OST_Rooms`. A TDD test was written RED, then the minimum source correction was applied: skip only `area_kind=EXTERNAL`; omitted `area_kind` remains internal for existing fixtures.

The current production dry run planned R01–R10 with layout hash `9410f296b0d3a258a51971a6e2a35cd404f8018ca28ba5d6f36003516808539d`, approval hash `bf7dcca735de166f100a6687f441ac7247ccf31f5e9e28a1bd4837591acba7ef`, 238 internal furniture operations and 5 excluded external operations.

The registry-approved route for `revit.create_furniture_element` is the Horizun Python fallback. Final preflight passed with zero warnings, source hash `688f1b5bb4cd87124a80abcd2cf0d75c79cb588c4d28ea5fd12ca21c7683485a`. The single apply key was `amanda-r10-furniture-20260922-v1`. The bridge reported a Python failure at `document.Regenerate()` after the main transaction had committed. No blind retry was made.

Independent live readback reconciled the state:

- 238 `Mobiliário` instances
- 238 unique `FUR-...` marks
- 238 `AMANDA-R10|...` instance comments
- 238 positive bounding boxes
- visible type `1525 x 762mm`; family/type parameters `124560:124560`
- element IDs `222604`–`222841`
- whole model after reopen: 4115 elements, 52 rooms, 87 openings, 78 walls, 238 furniture, 53 GenericModels, coverage complete and 0 unreadable

## Persistence evidence

Save was verified at SHA-256:
`d7f899c6dd9b1ce86f0b933cbe51f47728dc61f6df2fe92cb1ffece6c00e8959`

Size: `4304896` bytes.

Checkpoint:
`revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R10-furniture-20260922.rvt`

`verify_checkpoint` returned `true`.

Preview:
`revit/production/previews/R10-furniture-3D-20260922.png`

The preview is a real 1400x865 capture from view 221538, classified STUDY and uncalibrated; the view was restored and the capture rollback returned `RolledBack`.

## Boundaries

The placed instances are functional study placeholders using the first verified in-document furniture type. They are not a final furniture catalog/specification. Site topography, boundary and occupancy remain blocking; frontage count and true north remain degrading. No FINAL or GOLDEN claim is valid.

## Resume exactly

Next substage: R11 landscape within P08-T13.

Start with Horizun health, active canonical path, R10 checkpoint/hash reconciliation and a fresh whole-model summary. Preserve source, canonical, checkpoints and GOLDEN artifacts. Use typed capability first; if the registry-approved fallback is required, preflight with zero warnings and perform one deliberate write followed by independent re-query, save, close/reopen, checkpoint and preview.

Relevant files:

- `docs/reports/delivery-mode/R10-live-evidence-2026-09-22.json`
- `revit/production/journals/R10-live-20260922.json`
- `revit/production/previews/R10-furniture-3D-20260922.png`
- `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R10-furniture-20260922.rvt.manifest.json`
- `state/task-graph.yaml`
- `PROJECT_STATE.yaml`
