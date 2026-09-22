# Amanda TFG BIM Agent — R09 live accessibility handoff

Date: 2026-09-22
Task: P08-T13
Status: RUNNING; R09 PASS_WITH_WARNINGS; R10 next

## Live target

Canonical production file:
revit/production/working/AMANDA_WORKING_001.rvt

Revit 2027 build 27.2.0.39, PID 25996, Horizun 1.3.3, one writer, non-workshared. The selected design is AMANDA-RUN-001-S01 with AGENT_DELEGATED authority, approval_hash bf7dcca735de166f100a6687f441ac7247ccf31f5e9e28a1bd4837591acba7ef, and AMANDA_REVIEW_PENDING retained.

## R09 completed

The R09 plan had 52 measured route inputs and a measured gallery width of 1.5 m. No VERIFIED numeric accessibility rule was available, so numeric status is STATUS_NAO_VERIFICADO and no normative compliance claim is allowed.

The registry explicitly routes revit.create_accessibility_element through the approved Horizun Python fallback. The final preflight passed with zero warnings. Two earlier executions stopped before transaction because imports were incomplete; after each, health/readback proved the canonical model stayed at 3824 elements and 0 GenericModel elements. The third execution used a new idempotency key and created 53 study markers: 52 route envelopes plus R09-WIDTH-GALLERY.

The fallback response was classified completed_unverified by the bridge because arbitrary Python is not host-verified. Independent host queries then proved:

- 53 GenericModel elements
- 53 unique R09 ALL_MODEL_MARK values
- 53/53 readable positive bounding boxes
- coverage_complete true
- 0 unreadable

After reopen, whole-model readback returned 3877 elements, 52 rooms, 87 openings, 78 walls and 53 R09 GenericModels.

## Persistence evidence

Save:
b8145958ea27e85b232afbc72081f42b47ffcad310ac16f8e8057409d5a9548a

Size: 4247552 bytes.

Checkpoint:
revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R09-accessibility-20260922.rvt

verify_checkpoint returned true.

Preview:
revit/production/previews/R09-accessibility-3D-20260922.png

The preview is a real 1400x865 STUDY capture from view 221538, uncalibrated, with the view restored after rollback.

## Boundaries

The route envelopes are reversible study geometry in GenericModel. They are not a normative accessibility certification or final construction detail. SITE_TOPOGRAPHY, SITE_BOUNDARY and SITE_OCCUPANCY remain blocking; SITE_FRONTAGE_COUNT and SITE_TRUE_NORTH remain degrading. No FINAL or GOLDEN claim is valid.

Do not repeat R09. Reconcile the live hash, active path and R09 checkpoint before any future write. Preserve source, canonical, checkpoints and GOLDEN artifacts.

## Resume exactly

Next substage: R10_FURNITURE within P08-T13.

Start with Horizun health, active canonical document, whole-model summary and R09 checkpoint verification. Compile R10 without mutating first. Then perform the smallest safe write, independent read, verify, save, close/reopen, checkpoint and real preview. Continue to R11 and R12 before marking P08-T13 PASS_WITH_WARNINGS.

Relevant files:

- docs/reports/delivery-mode/R09-live-evidence-2026-09-22.json
- revit/production/journals/R09-live-20260922.json
- revit/production/previews/R09-accessibility-3D-20260922.png
- revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R09-accessibility-20260922.rvt.manifest.json
- state/task-graph.yaml
- PROJECT_STATE.yaml
