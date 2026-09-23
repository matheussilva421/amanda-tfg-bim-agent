# Plan 10 — Canonical Direction Recovery / Stop the Linear Release

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans` task-by-task.

**Goal:** Stop the current R12 linear model from reaching final release, preserve its evidence safely, and hand production to Plan 11 + rewritten Phase 08.

**Architecture:** Reconciliation first, archive one legacy RVT, update decision/state semantics, then return immediately to the canonical pavilion rebuild. This plan must not create another generic infrastructure detour.

**Tech Stack:** Existing Git/state/Revit/provider tooling.

**Spec:** `docs/superpowers/specs/2026-09-22-canonical-pavilion-migration-design.md`

## Global Constraints

- The user has fixed the pavilion parti; no architecture vote remains between bar and pavilions.
- Preserve one hashable legacy R12 copy in arquivo histórico; delete only classified redundant copies later.
- Do not continue R13 on the linear model as final deliverable.
- Do not reset/reinstall validated providers.

### Task 1: Reconcile live state
- [ ] Fetch Git and inspect branches/worktrees/dirty files.
- [ ] Read live `PROJECT_STATE.yaml`, status, task history, journals and current RVT path.
- [ ] Record actual current stage/head in a migration handoff.

### Task 2: Freeze legacy evidence
- [ ] Save/close current linear RVT if needed.
- [ ] Hash it while closed.
- [ ] Copy exactly one historical reference into an archive path.
- [ ] Record current rooms/walls/openings/materials/checkpoint evidence.

### Task 3: Supersede decisions
- [ ] Append a new decision: `ARCHITECTURAL_PARTI=CANONICAL_PAVILION_CLUSTER`, `selection_authority=USER_DIRECTED`.
- [ ] Mark old `AMANDA-RUN-001-S01` and linear selection `SUPERSEDED_BY_USER_DIRECTION` without deleting history.
- [ ] Invalidate any active approval hash bound to old geometry for future writes.

### Task 4: Redirect task graph
- [ ] Insert Plan 11 migration tasks before rebuilt Phase 08 R04–R16.
- [ ] Set next task to canonical migration, not legacy R13.
- [ ] Preserve site blockers and provider capability state.

### Task 5: Clean only safe duplicates
- [ ] Classify old RVTs/temp files.
- [ ] Preserve sources, evidence, journals, baseline, checkpoints used by decisions and one legacy historical RVT.
- [ ] Delete only reproducible duplicates/temp/cache after manifesting them.

### Gate
Proceed only when no task can accidentally resume final documentation on the linear R12.


## Unified R12 Freeze + BIM-00 Write Gate

Plan 10 owns the mandatory transition from the historical linear model to a safe canonical target.

### Additional mandatory controls

- Follow `docs/source/references/R12_HISTORICAL_FREEZE_PROTOCOL.md`.
- Follow `docs/source/references/BIM_WRITE_GATE_PROTOCOL.md`.
- Record one immutable historical R12 copy, SHA-256, Revit build, units, coordinates/site assumptions, links/worksets when present, and evidence/journals.
- Mark it `HISTORICAL` / `SUPERSEDED_BY_USER_DIRECTION`.
- Do not use historical geometry/families as automatic drivers of new canonical geometry.
- Run BIM-00 before the first canonical geometry write and again when switching the production target.
- No provider fallback may bypass the gate.

### Gate outcome

Plan 10 is complete only when:
1. the historical R12 cannot accidentally resume as the final model;
2. the new canonical target is clearly identified;
3. canonical references are hash-verified;
4. the next canonical write is protected by BIM-00.
