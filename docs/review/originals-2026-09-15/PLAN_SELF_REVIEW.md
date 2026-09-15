# Amanda TFG BIM Agent — Implementation Plan Self-Review

**Review date:** 2026-09-11  
**Reviewed against:** `2026-09-11-amanda-tfg-bim-agent-design.md`  
**Result:** PASS

## 1. Spec coverage matrix

| Approved spec area | Implementation coverage |
|---|---|
| Purpose, scope, integrity-first principles | `00-master-implementation-plan.md`, enforced across all child plans |
| Environment bootstrap, exact Revit detection, snapshots, state | `01-foundation-environment-state.md` |
| Revit Tool Lab, Horizun primary, RevitCortex fallback, custom API, fault injection | `02-revit-tool-lab-providers.md` |
| Capability Registry, circuit breaker, provider evidence and promotion | `02-revit-tool-lab-providers.md` |
| Failure classification, retry/fallback policy, rollback prerequisites | Plans 02, 05, 07 |
| Source ingestion, provenance, SOURCE_FACT/DERIVED_CONSTRAINT/DESIGN_HYPOTHESIS | `03-project-intelligence.md` |
| Program/site canonical models and missing-data registry | `03-project-intelligence.md` |
| Hard/soft constraints, privacy, adjacency, independent flows | `04-design-engine.md` |
| OR-Tools/Shapely/NetworkX deterministic generation | `04-design-engine.md` |
| Optional TopologicPy and Ladybug/Honeybee evaluation | `04-design-engine.md` |
| Candidate generation, scoring, Pareto, reproducibility, finalist explanations | `04-design-engine.md` |
| Human `APPROVED_FOR_BIM` gate | Plans 04 and 08 |
| Desired-state BIM, logical IDs, diff/minimal mutation | `05-bim-compiler.md` |
| BIM stages R00–R16 and stage checkpoints | Plans 05 and 06 |
| Site/Toposolid behavior without invented topography | Plans 03 and 05 |
| Rooms, openings, accessibility, furniture, landscape, materials, documentation | `05-bim-compiler.md` |
| Model/program/concept/accessibility/warning QA | `06-qa-release-exports.md` |
| Save/close/restart/reopen persistence gate | Plans 02, 05, 06, 08 |
| IFC/PDF/DWG export validation | `06-qa-release-exports.md` |
| RC/GOLDEN immutable release and hashes | `06-qa-release-exports.md` |
| AGENTS.md, persistent state, session start/end, task graph | `07-autonomy-recovery-security.md` |
| Single writer, watchdog, crash/reboot/Codex-session recovery | `07-autonomy-recovery-security.md` |
| Secrets, trust review, maintenance/update policy | `07-autonomy-recovery-security.md` |
| One CLI entry point (`amanda-agent`) and doctor/status/resume/rollback | Plans 01–07 |
| Actual Amanda production run | `08-amanda-production-run.md` |
| Blender rendering and Autodesk APS last-resort extensions | `09-optional-render-cloud.md` |
| Definition of Done / definition of autonomy | Master plan + Plans 06, 08 |

**Coverage result:** No approved spec requirement is unassigned.

## 2. Intentional blockers preserved from the approved design

These are not plan gaps and must not be “fixed” by guessing:

- **Verified site topography:** final grading and topography-dependent accessibility validation remain blocked until a real survey/topographic source is provided.
- **Normative numeric rules:** accessibility/fire/building-code numbers may become hard constraints only after the applicable verified source/version is acquired and cited in the project registry.
- **Final architectural choice:** detailed BIM requires an explicit `APPROVED_FOR_BIM` human gate after finalist comparison.
- **Authentication/UAC:** Codex persists state and waits for the user when Windows or Autodesk requires an approval/login/MFA/license action.

## 3. Placeholder scan

Scanned every Markdown plan for the forbidden planning patterns:

- `TODO`
- `TBD`
- `implement later`
- `similar to task`
- `fill in details`
- `appropriate error handling`
- `write tests for the above`
- unresolved executable/repository/path placeholders

**Result:** PASS — no red-flag placeholder remains in the implementation plan bundle.

Runtime values that inherently must be discovered (for example the exact local Revit build, installed executable path, MCP tool names, repository commit SHA, and timestamps) have an explicit discovery step plus validation before persistence. They are not planning omissions.

## 4. Type/interface consistency review

Canonical names used consistently across the plans:

- `ProjectState`
- `TaskStatus`
- `PhaseGate`
- `CapabilityStatus`
- `ProviderCapability`
- `CapabilityRegistry`
- `DesignSolution`
- `DesiredElement`
- `VerificationResult`
- `APPROVED_FOR_BIM`
- Revit stages `R00` through `R16`
- capability states `PASS`, `PASS_WITH_WARNINGS`, `DEGRADED`, `UNTESTED`, `FAIL`, `RETIRED`
- task outcomes `PASS`, `PASS_WITH_WARNINGS`, `DEGRADED`, `BLOCKED_BY_INPUT`, `BLOCKED_BY_TOOL`, `FAILED_ROLLED_BACK`, `CRITICAL_FAILURE`

Provider-specific MCP tool names are deliberately **not guessed** in code-facing interfaces. Plan 02 requires Codex to discover the actual installed MCP schema and persist semantic tool maps before any automated provider use.

## 5. Cross-plan consistency review

- **Platform:** Windows + detected Revit 2027 Education throughout.
- **Revit build:** discovered at runtime; never assumed.
- **Local-first:** preserved throughout; APS appears only in Plan 09 as last-resort fallback.
- **Provider priority:** Horizun first after PASS evidence; RevitCortex second; custom API/interchange after verified need.
- **.NET:** Revit 2027 treated as .NET 10; Horizun source build explicitly checks the upstream-required exact SDK 10.0.400 before build.
- **Python:** core implementation is consistently Python 3.12 x64.
- **Production isolation:** Tool Lab precedes production; production begins only in Plan 08.
- **Revit concurrency:** single writer throughout.
- **GOLDEN:** immutable throughout.
- **Source fidelity:** requirements immutable during optimization; missing facts stay missing.
- **Updates:** provider/Revit updates occur only in maintenance isolation followed by regression.

**Result:** PASS.

## 6. Plan quality metrics

The plan is intentionally decomposed because the approved design contains multiple independently testable subsystems. The master plan provides dependency order and GO/NO-GO gates, while each child plan can be reviewed and executed independently.

The bundle includes:

- one master implementation plan;
- nine child implementation plans;
- a combined convenience plan;
- the approved design specification;
- a Codex handoff prompt;
- this self-review.

Every code-oriented subsystem includes concrete files/interfaces, test-first steps, expected commands/results, verification, and commit boundaries. Revit-facing steps add persistence evidence and rollback/fallback requirements beyond ordinary unit tests.

## 7. Final review verdict

**PASS — ready for execution handoff.**

Recommended execution mode: `superpowers:subagent-driven-development`, task-by-task, with reviewer gates. Use `superpowers:executing-plans` only if a single Codex session intentionally executes the plan inline in batches.
