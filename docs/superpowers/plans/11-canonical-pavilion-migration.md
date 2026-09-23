# Canonical Pavilion Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the code path that hard-codes the single double-loaded bar with a content-bound canonical pavilion layout/selection that drives the new Revit production run.

**Architecture:** Preserve `architectural_layout.py` as legacy compatibility/history. Add a new canonical reference loader and pavilion layout module; update selection and production scripts to consume the canonical layout. Bind approval hashes to the three canonical board hashes. All exports/QA/BIM compiler consumers migrate through a stable layout protocol rather than directly importing the legacy builder.

**Tech Stack:** Python 3.12, Shapely, Pydantic/dataclasses, pytest, existing BIM compiler/Revit provider stack.

**Spec:** `docs/superpowers/specs/2026-09-22-canonical-pavilion-migration-design.md`

## Global Constraints

- Program: 20 people, 626 m² internal, 260 m² external.
- Canonical parti: separate blocks/pavilions; no single linear bar.
- Three canonical board SHA-256 values must be included in selection evidence/approval binding.
- Existing linear R12 is historical only.
- TDD: RED → minimal GREEN → regression → commit.
- No unverified Revit capability is introduced by this migration.

## Review Focus

1. Program room counts/areas remain exact after distributing rooms among pavilions.
2. Canonical pavilions remain separate geometries and cannot collapse into one connected bar.
3. Approval hash changes when any canonical image, geometry or program input changes.
4. Legacy exports/tests do not silently continue calling `build_courtyard_layout` for the active production path.
5. Revit production script cannot resume an old linear RVT as the canonical target.

---

### Task 1: Canonical reference profile loader

**Files:**
- Create: `src/amanda_agent/design/canonical_reference.py`
- Test: `tests/unit/test_canonical_reference.py`
- Read: `docs/source/references/CANONICAL_REFERENCE_PROFILE.yaml`
- Read: `docs/source/SOURCE_MANIFEST.json`

**Interfaces:**
- Produces: `CanonicalReferenceProfile.load(root: Path) -> CanonicalReferenceProfile`
- Produces: `profile.source_hashes: tuple[str, ...]`

- [x] **Step 1: Write failing test** asserting 3 canonical design refs, `single_linear_bar_allowed is False`, target residential pavilion count 4, and source SHA values exist.
- [x] **Step 2: Run** focused test; confirmed RED because module was absent.
- [x] **Step 3: Implement minimal loader** that validates YAML + source manifest, rejects missing/hash-mismatched canonical image.
- [x] **Step 4: Run test** and confirm PASS (4 passed, Python 3.12.14).
- [x] **Step 5: Commit** `feat: establish canonical pavilion reference and archive R12` (`9fe08bc`).

### Task 2: Introduce stable layout protocol

**Files:**
- Create: `src/amanda_agent/design/layout_protocol.py`
- Test: `tests/unit/test_layout_protocol.py`
- Modify: consumers that type against `CourtyardLayout` directly only as required.

**Interfaces:**
- Produces protocol/properties required by BIM/export/QA: `rooms`, `footprint`, `external_spaces`, `content_hash`, `accounting`, `parameters`, `service_access_point`.

- [x] Write failing test with both a small fake layout and legacy `CourtyardLayout` satisfying protocol.
- [x] Run and confirm RED (protocol module absent).
- [x] Implement protocol/dataclasses and a geometry-neutral legacy adapter; legacy geometry unchanged.
- [x] Run and confirm GREEN (18 focused and legacy regression tests passed).
- [x] Commit `refactor: define production layout protocol` (`3276976`).

### Task 3: Canonical pavilion layout model

**Files:**
- Create: `src/amanda_agent/design/canonical_pavilion_layout.py`
- Test: `tests/unit/test_canonical_pavilion_layout.py`

**Interfaces:**
- Produces: `CanonicalPavilionLayout`
- Produces: `build_canonical_pavilion_layout(program, profile) -> CanonicalPavilionLayout`

Required logical components:
- `ADMIN_ACOLHIMENTO` — public edge, two-level intent;
- `RES_PAV_A`, `RES_PAV_B`, `RES_PAV_C` — sleeping pavilions;
- `RES_PAV_D_COMMUNAL` — convivência/refeitório/copa;
- `SERVICE_CAPACITATION` — separate block/access;
- `CHILD_SECTOR` — green interface;
- `THERAPEUTIC_GARDEN`, `PROTECTED_PATIO`, `HORTA`, `EXERCISE`, `PLAYGROUND`;
- covered external connectors.

- [x] Write RED tests asserting no single polygon/bar contains all internal program and exactly 626 m² net internal is assigned once.
- [x] Add test that residential official mix is distributed across 4 pavilion groups and all required logical IDs remain unique.
- [x] Add test that admin and residential clusters have distinct footprints separated by external space.
- [x] Add test that external programmed spaces sum to 260 m².
- [x] Add test that central garden intersects/relates to all residential pavilion access paths without overlapping closed footprints.
- [x] Implement minimal deterministic normalized reference geometry, scaling dimensions from program areas rather than trusting pixels as survey measurements.
- [x] Run tests; GREEN.
- [x] Commit `feat: build canonical pavilion layout`.

### Task 4: Canonical visual/parti invariants

**Files:**
- Create: `src/amanda_agent/design/canonical_qa.py`
- Test: `tests/unit/test_canonical_qa.py`

**Interfaces:**
- Produces: `run_canonical_checks(layout, profile) -> list[CanonicalCheck]`

- [x] RED test: legacy `build_courtyard_layout` must fail `CANON-001`/`CANON-004`.
- [x] RED test: canonical pavilion layout passes structural parti checks.
- [x] Implement checks from `CANONICAL_QA_RUBRIC.yaml`.
- [x] Include high-level relative-location tests: admin public side; residential protected side; service separated; child-green adjacency; central garden.
- [x] Run GREEN.
- [x] Commit `test: enforce canonical pavilion parti`.

### Task 5: Replace active production selection

**Files:**
- Modify: `src/amanda_agent/production/selection.py`
- Test: create/update `tests/unit/test_production_selection.py`
- Modify: decision-register write path if needed.

**Interfaces:**
- New solution ID baseline: `AMANDA-RUN-002-PAVILION-S01` (or next collision-free revision generated from live state).
- Parti authority: `USER_DIRECTED`.
- Detailed variant authority: `AGENT_DELEGATED`.

- [x] Write RED test asserting old `SELECTION_ARCHETYPE == COURTYARD_DOUBLE_LOADED_BAR` is no longer the active production selection.
- [x] Write RED test asserting canonical source hashes are part of the selection evidence and changing one changes `approval_hash`.
- [x] Write RED test asserting legacy selection remains representable as superseded history.
- [x] Implement new selection builder against `CanonicalPavilionLayout`.
- [x] Update rationale: do not claim bar wins by area; state user-fixed pavilion parti and agent-selected implementation inside it.
- [x] Run tests; GREEN.
- [x] Commit `feat: bind production selection to canonical pavilion boards`.

### Task 6: Migrate QA/export consumers off the legacy builder

**Files:**
- Modify: `scripts/qa_layout.py`
- Modify: `scripts/render_study_sheets.py`
- Modify: `tests/project/test_layout_qa.py`
- Modify: `tests/unit/test_ifc_export.py`
- Modify: `tests/unit/test_dxf_export.py`
- Modify: `tests/unit/test_qa_layout_script.py`
- Modify: `tests/unit/test_production_layout_bim.py`

**Interfaces:**
- Active production/test fixture imports `build_canonical_pavilion_layout` or a new resolver `build_active_layout(...)`.
- Legacy layout tests remain under explicitly named legacy coverage where useful.

- [x] Search repository for `build_courtyard_layout` and classify every reference as LEGACY or ACTIVE in `docs/reports/canonical-migration/LEGACY_BUILDER_REFERENCE_CLASSIFICATION.md`.
- [x] Add failing assertion that active QA/drawing entrypoints contain no direct legacy builder import or call.
- [x] Migrate QA, study drawing/PDF, DXF and IFC consumers to the canonical layout/protocol.
- [x] Update expected geometry without weakening program invariants; keep unverified vertical/site outputs blocked.
- [x] Run focused tests; GREEN (19 Task 6 tests; 68 relevant Tasks 1–5 regression tests).
- [x] Commit `refactor: route production consumers to canonical pavilion layout`.

### Task 7: Update BIM stage planning for multi-block/two-level admin geometry

**Files:**
- Modify: `src/amanda_agent/production/layout_bim.py`
- Modify: relevant `src/amanda_agent/bim/stages/*.py` only where single-plate assumptions exist.
- Test: `tests/unit/test_production_layout_bim.py`

**Interfaces:**
- Accept multiple closed footprints/levels instead of one bar plate.
- Covered connectors are external/covered circulation, not enclosed corridor.

- [x] RED test: plan contains distinct shell operations for admin, service and residential pavilion footprints.
- [x] RED test: admin Level 02 operations exist while residential pavilions remain ground-oriented unless the canonical design later changes.
- [x] RED test: no operation recreates a full-length double-loaded gallery as the main building.
- [x] Implement minimal multi-block planning, with R03/R04 study assumptions explicitly blocked by BIM-00 and R05 detail blocked by canonical geometric acceptance.
- [x] Run tests; GREEN (40 focused tests passed; 0 failed).
- [x] Commit `feat: plan multi-block canonical BIM stages` (`98dba47`, pushed to `origin/codex/canonical-pavilion-migration`).

### Task 8: Harden production runner against legacy RVT reuse

**Files:**
- Modify: `scripts/run_amanda_production.py`
- Test: create/update `tests/unit/test_run_amanda_production.py`

**Interfaces:**
- New canonical run starts from tested template/base.
- Legacy R12 path must be explicitly rejected as production target.

- [x] RED test: path/manifest tagged `SUPERSEDED_BY_USER_DIRECTION` cannot be selected as canonical production target.
- [x] RED test: canonical source hashes printed/recorded at plan start.
- [x] Update imports from legacy builder to canonical active layout resolver.
- [x] Preserve writer lock, safe save-as, idempotency and provider activation behavior.
- [x] Run focused tests; GREEN (70 passed, 0 failed; Ruff and `git diff --check` passed).
- [x] Commit `fix: prevent canonical rebuild from reusing legacy linear RVT`.

#### Task 8 sequencing ruling

The detailed selection remains `bim_eligible=false` until canonical geometric acceptance, while R04 massing must be created after BIM-00 and reviewed before that acceptance. Therefore a global detailed-eligibility check must not prevent an R04-only plan/write once BIM-00 has passed. Keep R05 and later detailing blocked until acceptance; dry planning remains write-free. Cost if wrong: either no path to produce the required R04 acceptance evidence or an unsafe pre-acceptance detail write.

### Task 9: Create canonical run artifacts offline before Revit write

**Files:**
- Create at runtime under `design-engine/runs/AMANDA-RUN-002-PAVILION/`.
- Create: `scripts/build_canonical_pavilion_run.py` if no existing command cleanly does this.
- Test: `tests/unit/test_build_canonical_pavilion_run.py`.

- [x] RED test requires solution JSON, geometry file, canonical QA report, board hashes and approval hash.
- [x] Generate deterministic run from program + profile.
- [x] Run canonical QA; CRITICAL failures must exit nonzero.
- [x] Export simple SVG schematic only as offline evidence, not Revit completion.
- [x] Commit code and the small generated run artifacts under the existing tracked-run convention; private boards/RVT remain excluded.

### Task 10: Regression and migration proof

**Files:**
- Create: `docs/reports/canonical-migration/MIGRATION_VERIFICATION.md` at runtime.

- [x] Run legacy unit tests that should remain valid (58 passed, 0 failed).
- [x] Run canonical layout/selection/QA tests (31 passed, 0 failed).
- [x] Run all non-Revit regression: `pytest tests -m "not revit and not slow" -q` (929 passed, 9 known baseline failures; same nine failure families as the 910/9 pre-Task-10 baseline).
- [x] Search active production code: zero legacy builder references in `scripts/`; only the explicit legacy module definition/export remains in `src/`.
- [x] Run dry production plan to R13; no file/provider/writer activity; seven distinct R04 block masses and write/evidence blockers verified.
- [x] Record exact pass counts, Git anchors and canonical hashes in `docs/reports/canonical-migration/MIGRATION_VERIFICATION.md`.
- [x] Commit `test: verify canonical pavilion migration`.

### Task 11: State/decision/task-graph migration

**Files:**
- Modify in live repo: `PROJECT_STATE.yaml`, `state/task-graph.yaml`, `state/task-history.yaml`, `project/requirements/decision-register.yaml`, handoff/status files.

- [x] Append supersedence record for `AMANDA-RUN-001-S01`.
- [x] Set active selected design to new canonical solution only after Task 10 passes.
- [x] Reset Revit stage for new geometry to pre-R04/R04 as appropriate; do not pretend R12 legacy completion applies to new geometry.
- [x] Preserve provider/capability PASS state and site blockers.
- [x] Set next task to rewritten Phase 08 canonical production.
- [ ] Commit `docs: switch production state to canonical pavilion run`.

### Task 12: Execution handoff to rewritten Phase 08

- [ ] Verify one clean canonical working target path.
- [ ] Verify legacy R12 archive exists and is hash recorded.
- [ ] Verify canonical run/selection/approval hash exists.
- [ ] Verify writer lease is free.
- [ ] Write exact next command for P08-CAN-T07 clean-target setup followed by P08-CAN-T08/R04 build.
- [ ] Proceed directly to rewritten Phase 08; do not open another design debate.


## Unified Migration Revision + Pavilion Semantics

The two revision patches add these mandatory migration constraints:

### Protection
Before canonical reconstruction, the previous R12 state is immutable historical evidence and its identity/hash are recorded.

### Canonical reconstruction
The new active solution must:
- have a new solution identity;
- remain a multiple-pavilion/block system;
- preserve the semantic attributes in `PAVILION_SEMANTIC_DEFINITION.md`;
- bind selection evidence to canonical reference hashes.

### Geometric acceptance
Before detailed BIM production, run `CANONICAL_GEOMETRIC_ACCEPTANCE.md`.

### Visual regression
After massing and at the defined downstream milestones, run `VISUAL_REGRESSION_QA_PROTOCOL.md`.

### Blocking rule
Similarity of implementation to the canonical boards is required. Reuse of historical linear geometry or historical selection rationale is prohibited.

### Fixed vs variable semantics
Fixed:
- architectural role;
- block/pavilion relationships;
- landscape relationship;
- circulation logic;
- spatial/privacy hierarchy.

Variable:
- structural modulation;
- construction parameters;
- technical detailing;
- BIM family/type representation;
- documentation graphics;
- minor dimensional adjustment required by verified technical constraints.

The agent optimizes implementation quality, not the user-directed architectural intent.
