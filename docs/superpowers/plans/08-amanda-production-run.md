> GENERATED from `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-08` on 2026-09-22. The canonical pavilion override and Plan 11 take precedence for Amanda production.

<a id="phase-08"></a>

# Amanda Production End-to-End Run — Canonical Pavilion Rebuild

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; use verification-before-completion before every Revit stage and release.

**Goal:** Replace the superseded linear R12 production geometry with a new pavilion/block BIM that materially matches the canonical boards while preserving the official program and all validated infrastructure.

**Architecture:** Archive the current linear R12 as historical evidence; execute Plan 11 to introduce the canonical pavilion layout/selection; then rebuild R04–R16 in a clean RVT using the already verified Revit providers/compiler/QA.

**Tech Stack:** Existing validated stack from Plans 01–07 + canonical reference profile and Plan 11.

**Spec:** `docs/superpowers/specs/2026-09-22-canonical-pavilion-migration-design.md`

## Global Constraints

- Canonical boards are authoritative for parti/spatial organization and are `CANONICAL_DESIGN_REFERENCE`.
- `AMANDA-RUN-001-S01` is `SUPERSEDED_BY_USER_DIRECTION`.
- Do not continue final R13–R16 on the legacy linear R12.
- Do not reuse the legacy linear geometry as final geometry.
- Reuse providers, families, parameters, compiler, QA, recovery and capability evidence when still valid.
- Official program remains 20 people / 626 m² internal / 260 m² external.
- Missing survey/site inputs limit FINAL claims, not the canonical STUDY rebuild.
- Every live milestone needs WRITE→READ→VERIFY + checkpoint + real Revit preview.

### Task 1: Canonical migration preflight [P08-T01]

- [ ] Read `START_HERE_FOR_CODEX.md`, canonical override, new migration spec and Plan 11.
- [ ] `git fetch --all --prune`; inspect branches/worktrees/dirty files.
- [ ] Run doctor/status and provider health.
- [ ] Confirm current live state; if R12 legacy advanced beyond the packaged snapshot, record it but still apply supersedence.
- [ ] Verify SHA-256 of program PDF and three canonical boards against `docs/source/SOURCE_MANIFEST.json`.
- [ ] `NO_GO` if canonical sources are missing/corrupt.

### Task 2: Archive legacy linear R12 [P08-T02]

- [ ] Close/save legacy RVT if open; obtain stable closed-file hash.
- [ ] Preserve exactly one canonical historical copy as `archive/superseded-linear/AMANDA_LINEAR_R12_SUPERSEDED_REFERENCE.rvt` or equivalent project path.
- [ ] Record stage, hash, source path, last known QA and reason `SUPERSEDED_BY_USER_DIRECTION`.
- [ ] Do not delete linked evidence/journals needed to prove history.
- [ ] Do not use archived geometry as the new model base.

### Task 3: Apply Plan 11 code/state migration [P08-T03]

- [ ] Execute every task in `docs/superpowers/plans/11-canonical-pavilion-migration.md` using TDD.
- [ ] Require all migration tests and existing non-Revit regressions PASS.
- [ ] Require a new run/solution ID and content-bound approval hash that includes canonical reference hashes.

### Task 4: Reconcile site input without changing the canonical parti [P08-T04]

- [ ] Ingest verified boundary/topography/north if available.
- [ ] Otherwise continue as STUDY with `PROVISIONAL_ASSUMPTION` and existing blockers.
- [ ] Map canonical "public edge" to verified/provisional Miguel Castro interface without copying street names/area from generated boards.
- [ ] Never use missing site evidence as justification to return to a linear bar.

### Task 5: Generate canonical pavilion run [P08-T05]

- [ ] Generate alternatives **only within** the fixed pavilion parti.
- [ ] Required common invariants: admin public edge, 4 residential functional pavilions around central garden, child-green interface, separate service/capacitation block/access, covered external connections.
- [ ] Variants may tune curvature, spacing, rotation and distribution, but cannot become a single bar.
- [ ] Run hard program/geometry checks; preserve program areas exactly.
- [ ] Save candidate geometry, metrics, canonical-conformance report and previews.

### Task 6: Select implementation inside the canonical parti [P08-T06]

- [ ] Rank only canonical-conforming pavilion variants.
- [ ] `selection_authority=USER_DIRECTED` for the parti itself.
- [ ] `selection_authority=AGENT_DELEGATED` may select the best detailed implementation inside that parti.
- [ ] Build new `approval_hash` from geometry + requirements + site profile + constraints + canonical board SHA-256 hashes.
- [ ] `AMANDA_REVIEW_PENDING` remains nonblocking.
- [ ] Record old selection as superseded; never edit its historical record in place.

### Task 7: Create clean canonical production RVT [P08-T07]

- [ ] Acquire single writer lease.
- [ ] Create a **new** working RVT from tested template/base, not from the R12 linear file.
- [ ] Reuse validated families/parameters/settings as imports/config, not legacy building geometry.
- [ ] Record pre-build hash and canonical solution ID.

### Task 8: R01–R04 canonical massing [P08-T08]

- [ ] R01 initialize project.
- [ ] R02 site STUDY/verified mode.
- [ ] R03 levels/references; admin must support reference two-storey intent.
- [ ] R04 create distinct masses for admin, service/capacitation, residential pavilions and child/landscape program as appropriate.
- [ ] Verify `CANON-001`..`CANON-008` applicable at massing stage.
- [ ] Export real Revit site/3D preview side-by-side with canonical implantation board.
- [ ] Stop if the result reads visually as one linear bar.

### Task 9: R05 shell [P08-T09]

- [ ] Create shell for separate volumes/pavilions.
- [ ] Admin vertical circulation/second level where required by canonical reference intent.
- [ ] Residential roofs/envelopes remain distinct volumes.
- [ ] Covered external paths are not converted into enclosed bar circulation.
- [ ] WRITE→READ→VERIFY; checkpoint; preview.

### Task 10: R06 internal layout [P08-T10]

- [ ] Place canonical room groups according to `CANONICAL_REFERENCE_MATRIX.md`.
- [ ] Keep exact program net areas and logical IDs.
- [ ] Preserve three sleeping pavilions + one communal residential pavilion.
- [ ] Preserve admin ground/upper functional logic.
- [ ] Validate no room overlaps and all required spaces exist.

### Task 11: R07 openings and circulation [P08-T11]

- [ ] Place doors/windows on correct hosts.
- [ ] Build protected/covered connections between pavilions.
- [ ] Maintain public/service/residential flow separation.
- [ ] Validate routes and hosted-element persistence.

### Task 12: R08 rooms/program reconciliation [P08-T12]

- [ ] Create/requery every room object.
- [ ] Reconcile 626 m² internal and capacity 20.
- [ ] Verify residential room mix against official program and canonical residential board.
- [ ] Export floor-plan preview; run canonical visual QA.

### Task 13: R09–R12 developed architecture [P08-T13]

- [ ] R09 accessibility to verified scope.
- [ ] R10 functional furniture.
- [ ] R11 pátio/jardim terapêutico, horta, exercícios, playground and external program totaling 260 m².
- [ ] R12 materials consistent with canonical warm/domestic/institutional language.
- [ ] Preserve landscape as program, not leftover space.
- [ ] Export plan + 3D preview and canonical-conformance report.

### Task 14: R13 documentation [P08-T14]

- [ ] implantation/site plan matching canonical block relationships;
- [ ] administrative ground/upper plans;
- [ ] residential pavilion plan;
- [ ] service/capacitation/child plan(s) as needed;
- [ ] roof plan;
- [ ] meaningful sections/elevations;
- [ ] schedules/areas;
- [ ] sheets, dimensions, tags and previews.
- [ ] Side-by-side check against all three canonical boards; every material difference must be a registered deviation.

### Task 15: R14 QA including canonical QA [P08-T15]

- [ ] Model/geometric QA.
- [ ] Program QA.
- [ ] Site/accessibility QA to supported source scope.
- [ ] Warning delta.
- [ ] Documentation QA.
- [ ] Run all checks in `CANONICAL_QA_RUBRIC.yaml`.
- [ ] CRITICAL canonical failure blocks RC.

### Task 16: R15 Release Candidate + cold reopen [P08-T16]

- [ ] Save RC to new path.
- [ ] Close Revit normally; hash closed file.
- [ ] Cold start Revit and reopen RC.
- [ ] Reconnect provider and requery critical elements/rooms/pavilions.
- [ ] Re-run program + canonical critical QA.

### Task 17: Export and validate model-derived deliverables [P08-T17]

- [ ] IFC and IfcOpenShell validation.
- [ ] PDF sheets and nonblank preview validation.
- [ ] DWG when verified capability applies.
- [ ] PNG previews.
- [ ] schedules/area report.
- [ ] All release artifacts hashed.

### Task 18: Promote R16 GOLDEN [P08-T18]

- [ ] Require program QA, persistence, exports and canonical QA PASS for declared scope.
- [ ] Generate manifest with canonical source hashes and deviation register.
- [ ] Publish into new immutable GOLDEN directory without overwrite.
- [ ] Mark legacy linear release/history explicitly superseded.

### Task 19: Cleanup and final handoff [P08-T19]

- [ ] Keep original PDFs, canonical boards, SOURCE_MANIFEST, state/evidence, one legacy R12 historical RVT, current checkpoints and GOLDEN.
- [ ] Remove obsolete plan-package folders/ZIPs only after new package is verified in workspace.
- [ ] Remove redundant linear WORKING copies/temp/lab outputs only when classified reproducible and non-evidentiary.
- [ ] Generate `RUN_SUMMARY.md`, `CANONICAL_CONFORMANCE_REPORT.md`, `AUTONOMY_REPORT.md` and exact resume state.

## Production Completion Gate

### SUCCESS
A cold-reopenable GOLDEN exists, follows the canonical pavilion parti, reconciles the official program, has model-derived exports, and has no unexplained CRITICAL canonical deviation.

### FAILURE
Any release continues the linear bar, omits canonical pavilion relationships, fabricates source/site facts, or lacks cold-reopen/QA evidence.


## Canonical geometric + visual QA gates — unified patch integration

During the rewritten pavilion production run:

- **R04:** run canonical geometric acceptance + visual regression before shell detailing.
- **R06:** rerun topology/circulation acceptance after internal layout.
- **R08:** verify program/room reconciliation and export a canonical plan comparison.
- **R12:** run developed-architecture visual regression.
- **R13:** side-by-side board/documentation comparison is mandatory.
- **R15:** after cold reopen, repeat critical geometric and visual checks.
- **R16:** GOLDEN is blocked unless canonical geometric acceptance and visual regression pass, except for explicitly documented/approved `CANONICAL_DEVIATION` items.

Use:
- `docs/source/references/CANONICAL_GEOMETRIC_ACCEPTANCE.md`
- `docs/source/references/VISUAL_REGRESSION_QA_PROTOCOL.md`
