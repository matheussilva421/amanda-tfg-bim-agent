> GERADO de [2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-08) em 2026-09-15. Edite o COMBINED e execute `docs/review/package_review.py`; não edite esta cópia. Caminhos operacionais no texto são relativos à raiz do projeto.

<a id="phase-08"></a>

# Amanda Production End-to-End Run Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; use verification-before-completion before every Revit stage and final release.

**Goal:** Run the completed, tested local pipeline on Amanda's real TFG: ingest sources, generate alternatives, select one architecture, compile it to Revit, validate, export, and produce the first immutable GOLDEN deliverable set.

**Architecture:** This phase adds almost no new infrastructure. If production reveals a missing capability, stop that operation and return to the relevant Tool Lab/implementation plan before the new capability can touch production.

**Tech Stack:** The validated stack from Plans 01–07.

**Spec:** [design specification](../../../2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- First plan allowed to create Amanda production RVTs.
- No UNTESTED capability in production.
- Missing verified topography blocks final grading, not necessarily schematic design.
- One architecture must be explicitly `APPROVED_FOR_BIM` before detailed Revit compile.
- Every provider invocation/evidence is logged.
- Every R-stage checkpoint retained until GOLDEN.

---

### Task 1: Production preflight [P08-T01]

**Files:** read-only checks against state/config.

- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m amanda_agent doctor
.\.venv\Scripts\python.exe -m amanda_agent status
.\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q
codex mcp list
```

- [ ] Confirm exact current Revit build equals the build tested in `state/bim-environment.lock.yaml`.
- [ ] Run separately marked Revit tests only on explicit disposable fixtures. Confirm production-scope evidence for every required capability, including build/schema/persistence, not just a core provider status.
- [ ] Confirm each required operation's fallback/recovery route and its transport dependencies are tested.
- [ ] Confirm no stale writer lease.
- [ ] Confirm Git clean.
- [ ] Confirm source-manifest hashes still match.
- [ ] If Revit/provider build changed, `NO_GO` until Plan 02 regression reruns.

---

### Task 2: Re-ingest/validate the latest Amanda sources [P08-T02]

- [ ] Validate TFG and program PDFs against source manifest.
- [ ] Ingest every newer Amanda file supplied for the design run using a new source version, never overwrite old provenance.
- [ ] Regenerate canonical data only from the newly selected source set.
- [ ] Run project-intelligence tests.
- [ ] Commit source-version metadata and canonical-data change.

---

### Task 3: Resolve site data to highest verified level [P08-T03]

- [ ] Inspect only user-supplied/project-scoped site files for boundary/survey/topography.
- [ ] If verified survey/topography exists, ingest/hash/validate and set `VERIFIED_TOPOGRAPHY`.
- [ ] If absent, use `PLANAR_PLACEHOLDER` and retain blockers for final grading/altimetric accessibility.
- [ ] Never convert TFG placeholders into invented elevations.
- [ ] Generate updated `project/site/missing-data.yaml`.

---

### Task 4: Freeze design-run inputs [P08-T04]

Before generating options:
- [ ] validate source-backed principles;
- [ ] review design hypotheses file;
- [ ] Verify the recorded PROGRAM_BASELINE decision (PDF, 20 people; resolved 2026-09-15) and source hash remain applicable. Let the agent research and record TYPOLOGY and the best-supported SITE_BOUNDARY. If confirmation is unavailable, use a labeled provisional STUDY scenario and retain the corresponding verified/final checks as blocked; do not wait for aesthetic preferences. A changed program source needs version reconciliation; do not reopen the already answered baseline choice without a material change.
- [ ] freeze `requirements_version`;
- [ ] freeze `site_version`;
- [ ] freeze `weights_version`;
- [ ] freeze Design Engine Git commit;
- [ ] commit:

```powershell
git add project design-engine/config state
git commit -m "chore: freeze Amanda design run inputs"
```

---

### Task 5: Generate production candidate run 001 [P08-T05]

Target baseline: 6 archetypes × 24 seeds = 144 macro candidates.

- [ ] Configure 144 initial attempts (6 archetypes × 24 seeds), then record valid/invalid/unknown/duplicate counts. Do not fabricate candidates or relax hard rules to reach a quota.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m amanda_agent design --run-id AMANDA-RUN-001
```

- [ ] Store every seed, engine/input version.
- [ ] Record hard-constraint rejection count by rule.
- [ ] Verify zero hard-invalid candidate enters ranking.
- [ ] Preserve Pareto set.

---

### Task 6: Refine/rank top candidates [P08-T06]

- [ ] Refine approximately top 15 macro options into block/room geometry.
- [ ] Re-run hard constraints after refinement.
- [ ] Compute all raw score dimensions.
- [ ] Apply frozen weights.
- [ ] Keep Pareto non-dominated set.
- [ ] Select up to 5 distinct feasible candidates; keep the Pareto set across all feasible candidates and do not discard it solely by weighted cutoff. If fewer candidates exist, report counts and reasons.
- [ ] Generate per-finalist:
  - `solution.json`;
  - geometry GeoJSON;
  - adjacency/flow graph exports;
  - metrics/penalties;
  - `WHY_THIS_OPTION.md`;
  - floorplan/zoning SVG/PNG.

---

### Task 7: Environmental finalist pass [P08-T07]

- [ ] Run source-backed solar/ventilation heuristics on top 5.
- [ ] If detailed environmental capability is PASS, run the reproducible finalist simulation workflow.
- [ ] Mark outputs correctly as `HEURISTIC` or `SIMULATED`.
- [ ] Do not claim CFD/Radiance-type validation when only heuristic exists.
- [ ] Update comparison matrix with raw and weighted values.

---

### Task 8: Create conceptual Revit massing for top 3 [P08-T08]

For each finalist:
- [ ] acquire the shared writer lease and create a separate candidate RVT with execution mode CONCEPT_ONLY and no detailed-production approval;
- [ ] compile R01→R04 only;
- [ ] verify mass/site metrics against solution JSON;
- [ ] export 3D/site preview;
- [ ] save/close/reopen massing file;
- [ ] record provider tools/fallbacks;
- [ ] reject R05–R16 for CONCEPT_ONLY; finish verified save/reopen and release the lease before moving to the next candidate.

---

### Task 9: Delegated architectural selection and later Amanda review [P08-T09]

Prepare `solutions/finalists/comparison.md` containing:
- program compliance;
- privacy/security;
- flow metrics;
- solar/ventilation;
- accessibility potential;
- garden/external-space performance;
- constructability;
- known limitations;
- plan/3D previews.

- [ ] Generate an up-to-three-finalist comparison and choose the most justified option autonomously under the fixed brief. Save previews/comparison for Amanda/Matheus to review afterward; do not wait for a reply to start detailed development.
- [ ] Record selected solution ID, selection_authority=AGENT_DELEGATED, decider=agent, timestamp, rationale, source/metric evidence and approval_hash binding geometry/requirements/site/constraints/material intent in decision-register. Set amanda_review=AMANDA_REVIEW_PENDING; do not imply personal approval. Changed content requires a new decision/hash and validation, which the agent may perform autonomously.
- [ ] If a hybrid is justified by the agent or requested later by Amanda, create new solution with `parents=[...]`, rerun complete constraints/scoring/environmental pipeline, and include it as a new candidate—not an unvalidated manual splice.
- [ ] Set exactly one solution for the current project/run baseline to APPROVED_FOR_BIM; retain earlier approvals as superseded and bind active selection to approval_hash.
- [ ] Commit selection record and continue R05–R16 for the declared STUDY/FINAL scope. Later feedback creates a new version with affected-check revalidation; preserve the prior option/release and do not reopen the fixed 20-person capacity unless the user changes it.

---

### Task 10: Create production working RVT [P08-T10]

- [ ] Acquire `state/locks/revit-writer.lock`.
- [ ] Safety Sentinel verifies target path.
- [ ] Create `revit/production/working/AMANDA_WORKING_001.rvt` from tested project baseline/template.
- [ ] Hash pre-build state.
- [ ] Record session owner/provider health.

---

### Task 11: Compile R01–R04 [P08-T11]

- [ ] R01 project initialization.
- [ ] R02 supported site mode.
- [ ] R03 levels/references.
- [ ] R04 massing.

After every stage:
1. execute plan operation-by-operation;
2. WRITE→READ→VERIFY;
3. warning delta;
4. create stage checkpoint/hash;
5. update PROJECT_STATE;
6. only then advance.

---

### Task 12: Compile R05–R08 [P08-T12]

- [ ] R05 shell.
- [ ] R06 internal layout.
- [ ] R07 doors/windows/openings.
- [ ] R08 rooms.
- [ ] Run program quantity/area reconciliation after R08.
- [ ] Any missing required room is a stop condition before R09.

---

### Task 13: Compile R09–R12 [P08-T13]

- [ ] R09 accessibility to the extent supported by verified normative/site data.
- [ ] R10 functional furniture placeholders.
- [ ] R11 programmed exterior/landscape spaces.
- [ ] R12 approved material layer.
- [ ] Unsupported final compliance checks remain blockers, not green checkmarks.

---

### Task 14: Compile R13 documentation [P08-T14]

- [ ] site/floor/roof plans as applicable;
- [ ] architecturally meaningful sections;
- [ ] elevations;
- [ ] room/door/window schedules;
- [ ] area summary;
- [ ] sheets;
- [ ] dimensions/tags;
- [ ] preview export for every sheet.

- [ ] If Codex image inspection is available, review previews for obvious layout defects; otherwise create explicit human visual-review queue.

---

### Task 15: Run full R14 QA [P08-T15]

- [ ] Model/geometric QA.
- [ ] Program QA.
- [ ] Site QA.
- [ ] Accessibility QA to supported source scope.
- [ ] Architecture/concept graph QA.
- [ ] Warning delta.
- [ ] Documentation/export-preview QA.
- [ ] Write `QA_REPORT_RC01.md`.
- [ ] Fix genuine defects through new BIM plans/checkpoints; do not modify source requirements to make QA pass.

---

### Task 16: Create R15 Release Candidate [P08-T16]

- [ ] Save to a new RC path.
- [ ] Wait for save completion.
- [ ] Close Revit normally and hash the stable closed RC.
- [ ] Confirm process exit.
- [ ] Start detected Revit 2027 executable cold.
- [ ] Reopen RC.
- [ ] Reconnect preferred provider.
- [ ] Re-run critical model/program/room/provider QA.
- [ ] If divergence appears, rollback to last R14 PASS checkpoint and debug.

---

### Task 17: Export/validate RC [P08-T17]

- [ ] Export IFC through preferred verified capability.
- [ ] Parse IFC with IfcOpenShell and compare expected model structure.
- [ ] Export PDF sheets.
- [ ] Validate page count/nonblank previews.
- [ ] Export DWG.
- [ ] Run supported DWG validation and state limitation if parser depth is limited.
- [ ] Export selected PNG previews.
- [ ] Generate schedules/area report.
- [ ] Hash all release artifacts.

---

### Task 18: Promote R16 GOLDEN [P08-T18]

Preconditions:
- QA PASS or explicitly accepted noncritical limitation;
- persistence PASS;
- mandatory exports PASS;
- no unexplained critical warning/blocker;
- source/provider/input versions fixed.

- [ ] Generate final manifest.
- [ ] Prepare all Task 19 deliverables/reports in staging first; validate the declared STUDY/FINAL profile and mandatory checks, then publish the complete package into **new** `bim/releases/GOLDEN-001/` without overwrite.
- [ ] Verify post-copy RVT hash equals RC hash.
- [ ] Mark GOLDEN immutable in project state/safety policy.
- [ ] Release writer lock.

---

### Task 19: Final deliverable package preparation before Task 18 promotion [P08-T19]

Expected:

```text
bim/releases/GOLDEN-001/
├── Amanda_TFG_GOLDEN_001.rvt
├── Amanda_TFG_GOLDEN_001.ifc
├── DWG/
├── PDF/
├── preview/
├── manifest.json
├── QA_REPORT.md
├── PROGRAM_COMPLIANCE.md
├── ACCESSIBILITY_REPORT.md
├── CAPABILITY_REPORT.md
├── EXPORT_REPORT.md
└── provenance.json
```

- [ ] Verify all required paths.
- [ ] Verify hashes.
- [ ] Generate `AUTONOMY_REPORT.md`: fully autonomous / autonomous-with-fallback / human-required items.
- [ ] Generate final `RUN_SUMMARY.md` and the academic-deliverables status from Plan 03 Task 15. Record caderno, memorials, boards, visits, authorship and submission separately; no TFG_COMPLETE while required academic work remains pending.
- [ ] Commit metadata/reports; keep RVT binary outside normal Git unless LFS policy is later approved.

---

## Production Completion Gate

### SUCCESS
A sealed GOLDEN exists for its stated STUDY/FINAL scope; cold reopen, required QA, required exports and visual review have evidence; input/provider/provenance versions are recorded. This is pipeline/release success, not automatic TFG_COMPLETE.

### ACCEPTABLE LIMITATION
Only a STUDY release may retain explicitly identified missing survey/normative checks. FINAL stays blocked by any mandatory unresolved input/validation. Known program mismatch is never waived.

### FAILURE
Any release uses untested provider behavior, fabricated source data, unresolved program mismatch, corrupted state, or no cold-reopen verification.
