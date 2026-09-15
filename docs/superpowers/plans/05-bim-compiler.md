> GERADO de [2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-05) em 2026-09-15. Edite o COMBINED e execute `docs/review/package_review.py`; não edite esta cópia. Caminhos operacionais no texto são relativos à raiz do projeto.

<a id="phase-05"></a>

# BIM Compiler and Revit Desired-State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for compiler/policy code; systematic debugging for provider/Revit failures; verification-before-completion before stage promotion.

**Goal:** Compile a solution explicitly marked `APPROVED_FOR_BIM` into staged Revit 2027 checkpoints using the verified Capability Registry, with desired-state diffs, stable logical IDs, unit safety, provenance, checkpoints, and rollback.

**Architecture:** The Python compiler produces a read-only `BIM_PLAN.json`. Codex executes the plan through actual MCP tools selected from the Capability Registry. The compiler never decides architecture inside Revit; it reconciles desired state against current managed state and requests the smallest safe mutation set.

**Tech Stack:** Python 3.12, Revit 2027, verified Horizun/RevitCortex MCP capabilities, custom C# fallback, Shapely, IfcOpenShell.

**Spec:** [design specification](../../../2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- Detailed production compile requires `APPROVED_FOR_BIM`.
- Safety Sentinel must pass before every production write.
- One writer lock.
- Every write re-read and verified.
- Every stage produces a checkpoint/hash before the next stage.
- Logical IDs survive Revit ElementId replacement.
- Units convert through one library.
- Missing verified topography forbids final grading/altimetric claims.
- Destructive diff threshold blocks mass deletion/replacement.

## File Structure

```text
src/amanda_agent/bim/
├── models.py
├── units.py
├── provenance.py
├── desired_state.py
├── current_state.py
├── diff.py
├── plan.py
├── safety.py
├── checkpoints.py
├── verification.py
└── stages/
    ├── project.py
    ├── site.py
    ├── levels.py
    ├── massing.py
    ├── shell.py
    ├── layout.py
    ├── openings.py
    ├── rooms.py
    ├── accessibility.py
    ├── furniture.py
    ├── landscape.py
    ├── materials.py
    └── documentation.py
```

---

### Task 1: Revit unit conversion library [P05-T01]

**Files:**
- Create: `src/amanda_agent/bim/units.py`
- Test: `tests/unit/test_revit_units.py`

**Interfaces:** `meters_to_feet`, `feet_to_meters`, `sqm_to_sqft`, `sqft_to_sqm`.

- [ ] Write round-trip tests for 1 m, 10 m, 1 m², 24 m².
- [ ] Implement exact 1 ft = 0.3048 m conversion.
- [ ] Keep Design Engine data metric; record each discovered tool's input/output units. Typed providers may already accept metres: convert only for capabilities declaring internal feet. For direct Revit API use UnitUtils with declared spec/unit IDs. Test double conversion, area/volume/angle, linked-model transforms, project/true north and geospatial origin/CRS.
- [ ] Commit.

---

### Task 2: BIM stage and desired-element models [P05-T02]

**Files:**
- Create: `src/amanda_agent/bim/models.py`
- Create: `src/amanda_agent/bim/provenance.py`
- Test: `tests/unit/test_bim_models.py`

Stages:
`R00 EMPTY_SANDBOX`, `R01 PROJECT_INITIALIZED`, `R02 SITE`, `R03 LEVELS_AND_REFERENCES`, `R04 MASSING`, `R05 ARCHITECTURAL_SHELL`, `R06 INTERNAL_LAYOUT`, `R07 OPENINGS`, `R08 ROOMS`, `R09 ACCESSIBILITY`, `R10 FURNITURE`, `R11 LANDSCAPE`, `R12 MATERIALS`, `R13 DOCUMENTATION`, `R14 QA`, `R15 RELEASE_CANDIDATE`, `R16 GOLDEN`.

- [ ] `DesiredElement` requires logical_id, category, geometry/properties, requirement_id, design_option, generation_run.
- [ ] Test duplicate logical IDs rejected.
- [ ] Commit.

---

### Task 3: Safety Sentinel [P05-T03]

**Files:**
- Create: `src/amanda_agent/bim/safety.py`
- Test: `tests/unit/test_bim_safety.py`

**Interfaces:** `assert_writable_target(Path)`.

- [ ] Test path containing `GOLDEN` rejected.
- [ ] Test `MASTER` rejected.
- [ ] Test `source` rejected.
- [ ] Test `revit/production/working/AMANDA_WORKING_001.rvt` accepted.
- [ ] Enforce canonical writable-root allowlist, protected source/baseline/checkpoint/release identities, active document ID/path and shared lease. Test renamed originals, hardlinks, junctions and stale document switches; deny ambiguous target identity. Filename matching is a secondary guard.
- [ ] Commit.

---

### Task 4: Checkpoint manager [P05-T04]

**Files:**
- Create: `src/amanda_agent/bim/checkpoints.py`
- Test: `tests/unit/test_checkpoints.py`

**Interfaces:** create immutable stage copy + SHA256 manifest; verify hash before rollback.

- [ ] Test file copy hash equality, refusal of an active/incomplete save, and failure before checkpoint manifest publication. Save/close the owned file normally (or use a separately proven snapshot API), hash stable bytes, reopen/verify when required, then publish the checkpoint manifest. A stale on-disk copy is not the current Revit state.
- [ ] Test existing checkpoint path cannot be overwritten.
- [ ] Test GOLDEN cannot be used as writable checkpoint target.
- [ ] Implement.
- [ ] Commit.

---

### Task 5: Desired/current-state diff [P05-T05]

**Files:**
- Create: `src/amanda_agent/bim/desired_state.py`
- Create: `src/amanda_agent/bim/current_state.py`
- Create: `src/amanda_agent/bim/diff.py`
- Test: `tests/unit/test_bim_diff.py`

Actions: `CREATE`, `UPDATE`, `REPLACE`, `NOOP`, `DELETE`.

- [ ] 17 correct + 1 missing desired room → one CREATE.
- [ ] Existing logical ID + equivalent geometry/properties → NOOP.
- [ ] Duplicate current logical ID → hard error.
- [ ] Unmanaged elements are not deleted. Map logical IDs to Revit UniqueId + document identity, keeping ElementId only for the active session; detect user divergence before overwrite. Test SaveAs/reopen/replacement and persistent metadata across process restart.
- [ ] Commit.

---

### Task 6: Destructive-change threshold [P05-T06]

**Files:**
- Modify: `src/amanda_agent/bim/diff.py`
- Test: `tests/unit/test_destructive_threshold.py`

- [ ] Baseline threshold 10% of **managed** elements for DELETE/REPLACE.
- [ ] 11 destructive operations / 100 managed → block `HIGH_RISK_PLAN`.
- [ ] 5 / 100 may proceed only with a pre-operation checkpoint.
- [ ] Count cascading host deletions/type changes, including unmanaged dependents, before mutation. Unknown cascade blocks execution. Define zero/small-denominator and absolute-count safeguards; destructive threshold release requires a concrete reviewed plan under current authorization. Threshold config lives in versioned YAML.
- [ ] Commit.

---

### Task 7: BIM plan generator [P05-T07]

**Files:**
- Create: `src/amanda_agent/bim/plan.py`
- Test: `tests/unit/test_bim_plan.py`

Every operation contains:
- task_id;
- logical_id;
- action;
- semantic capability;
- desired payload;
- verification rules;
- preferred provider + verified fallbacks from registry.

- [ ] Stable operation ordering.
- [ ] Reject capability chain if all providers `UNTESTED/FAIL`.
- [ ] Plan generation is read-only.
- [ ] Write human summary `BIM_PLAN.md` alongside JSON.
- [ ] Commit.

---

### Task 8: Write-read-verify result model [P05-T08]

**Files:**
- Create: `src/amanda_agent/bim/verification.py`
- Test: `tests/unit/test_verification.py`

Verification layers:
1. existence;
2. properties;
3. geometry;
4. persistence when required.

- [ ] Tool says success but query misses element → FAIL.
- [ ] Element exists but geometry exceeds tolerance → FAIL.
- [ ] Correct element → PASS.
- [ ] Commit.

---

### Task 9: Project initialization stage R01 [P05-T09]

**Files:**
- Create: `src/amanda_agent/bim/stages/project.py`
- Test: `tests/unit/test_stage_project.py`

- [ ] Preflight checks mode: CONCEPT_ONLY permits finalists through R04; SYNTHETIC_LAB permits fixtures; detailed BIM permits APPROVED_FOR_BIM under AGENT_DELEGATED with matching approval_hash, decision evidence, selected input versions, healthy registry and exact build. AMANDA_REVIEW_PENDING is nonblocking. Real/unverified site input must be distinguished by STUDY profile and PROVISIONAL_ASSUMPTION; an unverified assumption cannot certify FINAL.
- [ ] Template order: Amanda template copy if supplied and tested; else installed architectural template discovered on machine.
- [ ] Desired project metadata/naming is deterministic.
- [ ] Lab-execute R01 and save/reopen.
- [ ] Checkpoint `R01_PROJECT_INITIALIZED`.

---

### Task 10: Site stage R02 [P05-T10]

**Files:**
- Create: `src/amanda_agent/bim/stages/site.py`
- Test: `tests/unit/test_stage_site.py`

Modes:
- `PLANAR_PLACEHOLDER`: site boundary/reference only, optionally with an explicitly hypothetical study scenario override; no claimed surveyed Z. Report the source as MISSING until verified, even if the study depicts a slope.
- `VERIFIED_TOPOGRAPHY`: may request Toposolid/grading capability.

- [ ] Test missing topography yields no claimed surveyed Z points; any local z=0 plane is explicitly a synthetic design reference.
- [ ] Test verified point set creates desired Toposolid operation only if capability registry has a PASS provider.
- [ ] Run synthetic site through lab preferred provider.
- [ ] Verify extents/elevations and save/reopen.
- [ ] Checkpoint.

---

### Task 11: Levels/references R03 [P05-T11]

**Files:** `src/amanda_agent/bim/stages/levels.py`, tests.

- [ ] Generate only levels required by selected solution/topography.
- [ ] The agent may research and adopt a provisional structural grid/concept if needed for the selected architectural solution; record design assumptions and keep structural engineering verification separate. Never label a proposed system as measured or technically certified without evidence.
- [ ] Verify name/elevation after write.
- [ ] Checkpoint.

---

### Task 12: Massing R04 [P05-T12]

**Files:** `src/amanda_agent/bim/stages/massing.py`, tests.

- [ ] Convert approved block polygons to simplified Revit masses/surrogate geometry supported by verified provider.
- [ ] Compare centroid, area, dimensions, rotation, separation, site containment against design JSON.
- [ ] Export 3D preview if verified capability exists.
- [ ] Reject any geometry mismatch beyond tolerances.
- [ ] Checkpoint.

---

### Task 13: Architectural shell R05 [P05-T13]

**Files:** `src/amanda_agent/bim/stages/shell.py`, tests.

- [ ] Derive shared wall topology once from net-room/gross-shell geometry, applying type thickness, location line, joins and host dependencies; adjacent rooms must not create duplicate coincident walls. Test two rooms sharing one wall, corners, openings and area reconciliation after wall creation.
- [ ] Floors from closed loops.
- [ ] Simple approved roof representation.
- [ ] Controlled type catalog only (`EXT_WALL_01`, `INT_WALL_01`, etc.); no uncontrolled type proliferation.
- [ ] Query duplicate/off-axis/unjoined warnings.
- [ ] Save/reopen and checkpoint.

---

### Task 14: Internal layout R06 [P05-T14]

**Files:** `src/amanda_agent/bim/stages/layout.py`, tests.

- [ ] Convert room polygons to internal walls/boundaries.
- [ ] Preserve logical IDs independent of ElementId.
- [ ] At R06 measure boundary/enclosure geometry; actual Revit Room objects and computed areas are queried after R08. Distinguish finished-face room area from wall centreline geometry.
- [ ] Accept configured area range; do not deform walls to chase exact decimals.
- [ ] Checkpoint.

---

### Task 15: Openings R07 [P05-T15]

**Files:** `src/amanda_agent/bim/stages/openings.py`, `project/bim/family-registry.yaml`, tests.

Family priority:
1. appropriate existing project family;
2. validated installed Autodesk content;
3. controlled project family;
4. generated/adapted family through verified provider/custom API;
5. project placeholder.

- [ ] Never auto-download arbitrary internet families.
- [ ] Verify door/window host, dimensions, intended connectivity, collision.
- [ ] Checkpoint.

---

### Task 16: Rooms R08 [P05-T16]

**Files:** `src/amanda_agent/bim/stages/rooms.py`, tests.

- [ ] Create/associate one room object per canonical room logical ID.
- [ ] Store name, number, sector, target area, privacy and source/requirement ID in managed metadata where safe.
- [ ] Query all rooms.
- [ ] Reject unplaced/not-enclosed/redundant managed rooms.
- [ ] Reconcile quantities/areas.
- [ ] Checkpoint.

---

### Task 17: Accessibility R09 [P05-T17]

**Files:** `src/amanda_agent/bim/stages/accessibility.py`, tests.

- [ ] Numeric rules loaded only from VERIFIED regulation registry.
- [ ] Build accessible route graph from entrance through required accessible spaces.
- [ ] If normative numeric data absent, output `BLOCKED_BY_INPUT` for those checks, never false PASS.
- [ ] Verify geometric checks supported by available source data.
- [ ] Checkpoint only for completed supported scope.

---

### Task 18: Furniture R10 [P05-T18]

**Files:** `src/amanda_agent/bim/stages/furniture.py`, controlled catalog, tests.

- [ ] Functional placeholders only after room geometry/clearances stabilize.
- [ ] Bedroom, psychology/technical, dining, office, child-area fixture sets are explicit.
- [ ] Use furnishings for spatial QA, not decorative randomization.
- [ ] Checkpoint.

---

### Task 19: Landscape R11 [P05-T19]

**Files:** `src/amanda_agent/bim/stages/landscape.py`, tests.

- [ ] Every programmed external space keeps logical ID and target area.
- [ ] Verify intended privacy/adjacency.
- [ ] Vegetation starts as controlled placeholders.
- [ ] West/privacy vegetation strategy can be represented only when it is part of approved option, not injected ad hoc.
- [ ] Checkpoint.

---

### Task 20: Materials R12 [P05-T20]

**Files:** `src/amanda_agent/bim/stages/materials.py`, `project/bim/material-catalog.yaml`, tests.

- [ ] Controlled catalog.
- [ ] No duplicate material names/types per run.
- [ ] Explicit material choices, traceable to selected design intent.
- [ ] Checkpoint.

---

### Task 21: Documentation R13 [P05-T21]

**Files:** `src/amanda_agent/bim/stages/documentation.py`, view/sheet registries, tests.

- [ ] Deterministic plan/site/roof view list.
- [ ] Sections selected for architectural relationships (courtyard/residential/transitions/access), not arbitrary count.
- [ ] Elevations.
- [ ] Room/door/window schedules and area summary.
- [ ] Sheet registry and view placement plan.
- [ ] Dimension/tag plan.
- [ ] Execute lab documentation build through verified capabilities.
- [ ] Export previews for Plan 06 QA.
- [ ] Checkpoint.

---

### Task 22: BIM CLI [P05-T22]

**Files:**
- Create: `src/amanda_agent/commands/bim.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_bim_cli.py`

Commands:
- `amanda-agent bim plan --solution PATH`
- `amanda-agent bim verify-plan PATH`
- `amanda-agent bim status`
- `amanda-agent bim claim --plan PATH`
- `amanda-agent bim record-result --operation-id ID --evidence PATH`

- [ ] Reject detailed BIM without a valid delegated or explicit human selection record. Accept AGENT_DELEGATED while AMANDA_REVIEW_PENDING; verify CONCEPT_ONLY remains limited to R04. Test hash invalidation after changed inputs, then validated agent reselection with a new decision/version, without another routine preference gate.
- [ ] GOLDEN/source target rejected.
- [ ] `plan` never mutates Revit.
- [ ] Plan contains only evidence-bound eligible provider chains for the exact operation scope.
- [ ] Implement a durable execution journal: operation_id, plan/input/checkpoint/document hashes, lease token, provider/schema versions, dependencies, intended delta and verifier. `claim` atomically marks the next READY operation; Codex invokes the actual MCP tool; `record-result` validates independent evidence before marking PASS.
- [ ] Tests: duplicate claim/ack, result for wrong model/hash, out-of-order result, interrupted write, pending host transaction, expired lease and stale plan. A transport timeout becomes IN_DOUBT; hold the writer and reconcile actual state before retry, fallback or lock release. A JSON plan alone does not execute MCP.
- [ ] Journal states are separate from TaskStatus: READY, CLAIMED, IN_DOUBT, VERIFIED, FAILED. Resume reconciles an in-doubt operation before dispatching any later mutation.
- [ ] Commit.

---

### Task 23: Synthetic end-to-end BIM compile [P05-T23]

**Fixture:** regression courtyard solution, not Amanda production.

- [ ] Acquire writer lease.
- [ ] Copy lab baseline to new working RVT.
- [ ] Compile R01→R13 in order.
- [ ] Stage checkpoint after each PASS.
- [ ] Force one preferred-provider failure on a noncritical synthetic operation and prove registry fallback is used.
- [ ] Save/close/restart/reopen at R13.
- [ ] Re-query managed logical IDs.
- [ ] Run model/program QA subset.
- [ ] Release writer lease.
- [ ] Write `tool-lab/reports/bim-compiler-e2e.md` with provider choices/fallbacks/warnings/durations.

---

## Phase 05 Verification Gate

### GO
Synthetic approved solution reaches R13, survives restart/reopen, preserves IDs/state, and exercises verified fallback without duplicate corruption.

### GO_WITH_LIMITATIONS
A nonessential family/documentation/site feature is degraded but has a tested safe alternative and is represented in the registry.

### NO_GO
Safety Sentinel can be bypassed, unmanaged elements are destroyed, duplicate managed elements appear, or restart/reopen diverges from desired state.
