> GERADO de [2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-00) em 2026-09-15. Edite o COMBINED e execute `docs/review/package_review.py`; não edite esta cópia. Caminhos operacionais no texto são relativos à raiz do projeto.

<a id="phase-00"></a>

# Amanda TFG BIM Agent — Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Use `superpowers:using-git-worktrees` at execution time when starting from an existing repository. Use TDD for code, systematic debugging for failures, and verification-before-completion before claiming any task/phase is complete.

**Goal:** Build a local-first, fault-tolerant Codex-controlled architecture/BIM pipeline that ingests Amanda's TFG sources, proves Revit integrations on this PC, generates architectural alternatives, compiles an approved alternative into Autodesk Revit 2027, validates it, and emits an immutable GOLDEN release.

**Status:** REVISED_DOCUMENT on 2026-09-15; implementation and Revit acceptance NOT_RUN.

**Architecture:** One canonical combined file containing a master section and nine phase sections. Every phase produces testable software/evidence and ends in a `GO`, `GO_WITH_LIMITATIONS`, or `NO_GO` gate. Revit production writes are forbidden until the Tool Lab has generated a verified Capability Registry.

**Tech Stack:** Windows, Autodesk Revit 2027 Education, Codex CLI, Git, PowerShell, Python 3.12 x64, pytest, Pydantic, Typer, OR-Tools, Shapely, NetworkX, IfcOpenShell; optional TopologicPy/Ladybug/Honeybee; .NET 10; Horizun Revit MCP; RevitCortex; optional Blender MCP and Autodesk APS fallback.

**Spec:** [design specification](../../../2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- Every code task follows behavioral RED → minimal implementation → GREEN; run RED before the implementation snippet, distinguishing harness/import setup from the intended failing assertion. Record command/counts/evidence and commit/push status.
- Shell blocks are conditional future steps, not one pasteable script. Check native exit codes and stop on failed clone/build/install before registration. Validate discovered paths/version variables before use; do not guess an executable by first match or newest timestamp.
- Importable Python code lives only under src/amanda_agent; top-level subsystem folders hold configuration, fixtures or artifacts, not duplicate implementations.
- Detect the exact installed Revit 2027 build; never assume it.
- Local-first. APS/cloud is last-resort fallback only.
- Maximum autonomy within the current user-authorized task. Document review is REVIEW_ONLY; future execution follows recorded authorization and platform permissions. Preserve user work, the delegated selection policy in design section 6.15 and external data/publication boundaries.
- One active writer per RVT.
- Never write to files whose path identifies them as `GOLDEN`, `MASTER`, or source originals.
- Every BIM write follows `WRITE → READ → VERIFY`.
- A tool-returned success flag is not evidence of actual model mutation.
- No `UNTESTED` provider may touch Amanda production.
- Source facts, derived constraints, and design hypotheses are separate data classes.
- Requirements are immutable during optimization.
- Missing topography remains missing; do not fabricate elevations/declivities.
- Dependency/provider/Revit updates occur only in maintenance branches and require regression before promotion.
- Tasks can pause as `SUSPENDED` with persisted resume conditions; completed attempts end in `PASS`, `PASS_WITH_WARNINGS`, `DEGRADED`, `BLOCKED_BY_INPUT`, `BLOCKED_BY_TOOL`, `FAILED_ROLLED_BACK`, or `CRITICAL_FAILURE`.

## Upstream evidence and revalidation before installation

Reviewed against primary documentation on 2026-09-15. These are upstream statements, not local installation evidence. Before execution, re-open the sources and pin the selected commit/release plus artifact hashes; use local `codex mcp add --help` for CLI syntax (confirmed in this review).

- Horizun Revit MCP: `https://github.com/HorizunGroup/horizun-revit-mcp`
  - Current source-build docs support Revit 2023–2027.
  - Source build currently pins SDK `10.0.400` via `global.json`; confirm the selected commit and official SDK availability. This is a provider-specific SDK requirement, not a generic Revit installation/Plan 01 gate. Runtime .NET and build SDK are distinct.
  - Upstream now recommends its hash-verified published installer for ordinary installation; retain source build when needed for development/audit and record that choice. Source install command: `powershell -ExecutionPolicy Bypass -File .\install.ps1`.
  - Current Codex registration uses the absolute installed executable path discovered after installation; the installation task computes that path and calls `codex mcp add horizun-revit -- $HorizunExe`.
- RevitCortex: `https://github.com/LuDattilo/RevitCortex`
  - Current docs support Revit 2023–2027.
  - Revit 2027 plugin build uses `Release R27` and .NET 10+.
- Autodesk Revit 2027 API docs: `https://help.autodesk.com/view/RVT/2027/ENU/?guid=f7165618-24c9-4160-a7a4-09979fe4a981`
  - Revit 2027 runs on .NET 10.
- Codex MCP docs: `https://developers.openai.com/codex/mcp`
  - `codex mcp add NAME -- COMMAND`
  - `codex mcp list`
  - `/mcp` in Codex TUI.
- OR-Tools: `https://developers.google.com/optimization/install`
- Shapely: `https://shapely.readthedocs.io/`
- IfcOpenShell: `https://docs.ifcopenshell.org/ifcopenshell-python/installation.html`
- TopologicPy: `https://github.com/wassimj/topologicpy`
- Ladybug/Honeybee: `https://github.com/ladybug-tools/ladybug`, `https://github.com/ladybug-tools/lbt-honeybee`
- APS samples: `https://github.com/autodesk-platform-services/aps-sample-mcp-server-revit-automation`, `https://github.com/autodesk-platform-services/aps-sample-revit-mcp-tools-bundle`
- Blender MCP optional: `https://github.com/ahujasid/blender-mcp`

---

## Plan map and executable dependency contract

Read each phase through its anchor below. The original ZIP supplied during review contains the ten separate master/phase plans, identical to the original combined sections. Revised child files under docs/superpowers/plans are generated from this canonical combined file; regenerate after changes.

| Phase | Content | Dependency / completion |
|---|---|---|
| [00](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-00) | Master and bootstrap of repository | Documentation only |
| [01](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-01) | Foundation and durable state | Local Python/core tests; probes report Revit availability |
| [07A](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-07) | Tasks 1–6, 10–13 and 16 | After 01; policy, task graph, redaction and maintenance safeguards before installs |
| [03](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-03) | Source intelligence | After 01; independent of Revit |
| [02](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-02) | Provider Tool Lab | After 07A; missing Revit blocks this branch |
| [04](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-04) | Design engine | After 03; synthetic work may proceed with scoped input blockers |
| [05](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-05) | BIM compiler | After 02 and 04 |
| [06](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-06) | QA and synthetic release | After 05 |
| [07B](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-07) | Tasks 7–9, 14–15 and 17–19 | After 06; integrated recovery and fresh-session drills |
| [08](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-08) | Amanda production | After 06 and 07B plus resolved production input/selection gates |
| [09](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-09) | Rendering and cloud fallback | Optional post-release rendering; APS exception described below |

<!-- phase-dependencies -->
```json
{"01": [], "07A": ["01"], "03": ["01"], "02": ["07A"], "04": ["03"], "05": ["02", "04"], "06": ["05"], "07B": ["06"], "08": ["06", "07B"], "09": ["08"]}
```

This graph governs the normal route. Optional APS Tasks 6–10 may be evaluated in a synthetic sandbox after 07A for an evidenced local tool blocker, without requiring a GOLDEN that the blocker prevents. This exception never promotes a local-only phase GO: record changed deployment scope, authorization, costs and verified output contract; re-evaluate dependent gates. Other branches continue. Rendering may be tested after a synthetic release in 06.

Within a phase, numeric order is reading order, not an implicit dependency. Explicit exceptions: P06-T14 promotion depends on P06-T15 visual review; P08-T19 preparation depends on P08-T17 exports, and P08-T18 sealing depends on P08-T19. Build the task DAG from actual inputs/outputs and reject cycles.

Task IDs use `P<phase>-T<two-digit task>`; IDs, dependencies and explicit section anchors are stored in the future task graph. 07A/07B are gates over disjoint tasks in section 07, not duplicated implementations.

### Task M1: Establish the repository without relocating the input bundle [P00-T01]

**Inputs:** the four Markdown files in this root and the supplied academic materials. **Outputs:** a local Git repository when needed, private-data exclusions, source inventory, initial documentation commit.

- [ ] Verify `Get-Location`, local instructions, `git rev-parse --show-toplevel`, `git status --short --branch` and `git remote -v`. As of this review, the supplied folder is not a Git repository and has no known remote.
- [ ] Keep this root. For an existing repository, preserve unrelated work and use an isolated worktree if useful. For a new repository, initialize here, commit the safe baseline, then create a worktree if needed. Do not nest another project or assume a worktree can exist before the first commit.
- [ ] Retain these root docs as canonical. Regenerate the derived phase files with docs/review/package_review.py and verify their section hashes; do not edit the generated files independently. The root specification remains canonical.
- [ ] Before staging, create `.gitignore` with at least:

```gitignore
.venv/
.venv-*/
.tools/
vendor/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
.env.*
!.env.example
docs/source/
docs/review/source-extracts/
TFG_Amanda_2026/
/programa_necessidades.pdf
/TFG_Amanda*.pdf
project/provenance/extracted/
state/snapshots/private/
state/locks/
logs/raw/
*.rvt
*.rfa
*.rte
*.slog
```

- [ ] Keep raw source documents, extracts, private config backups and live locks local. Commit only reviewed code, nonsecret metadata, reports and the handoff. New nonpublic files must be classified before staging; ignore rules alone do not protect previously tracked files.
- [ ] Run `git init -b main` only if no enclosing repository exists. Stage explicit reviewed paths, inspect `git diff --cached --stat`, commit, then push only to an identified remote. If no remote is configured, record the blocker and the exact commands after its URL becomes known; do not invent a GitHub destination.
- [ ] Retain source and document hashes and update `docs/notes/YYYY-MM-DD-escopo-handoff.md` with status and next task.

---

### Task M2: Enforce plan dependency order [P00-T02]

**Files:**
- Modify later: `PROJECT_STATE.yaml`

**Interfaces:**
- Consumes: child phase gates.
- Produces: controlled phase advancement.

- [ ] Follow the dependency contract above: 01 → 07A → 02; 01 → 03 → 04; (02 + 04) → 05 → 06 → 07B → 08.
- [ ] Evaluate gates per branch and intended deliverable scope. Revit unavailable must not block source reconciliation or synthetic solver development.
- [ ] Production preflight requires every required operation's evidence and recovery route, not merely a provider-level green label.
- [ ] Execute optional 09 only under its rendering/APS need gates.

---

### Task M3: Global completion verification [P00-T03]

**Files:**
- Read: `state/status.md`, `PROJECT_STATE.yaml`, release manifest.

- [ ] **Step 1: Fast deterministic tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit tests/geometry tests/solver -q
```

Expected: PASS.

- [ ] **Step 2: Full non-Revit regression**

```powershell
.\.venv\Scripts\python.exe -m pytest tests -m "not revit" -q
```

Expected: PASS.

- [ ] **Step 3: Doctor**

```powershell
.\.venv\Scripts\python.exe -m amanda_agent doctor
```

Expected: critical local systems PASS.

- [ ] **Step 4: Status**

```powershell
.\.venv\Scripts\python.exe -m amanda_agent status
```

Expected: no unexplained blocker/stale writer lease/dirty phase state.

- [ ] **Step 5: If GOLDEN exists, validate manifest and hashes**

```powershell
.\.venv\Scripts\python.exe -m amanda_agent release verify --release-id GOLDEN-001
```

Expected: QA PASS, persistence PASS, export results, provider pins, source versions, and hashes.

---

## Master GO/NO-GO Policy

### GO
Proceed automatically.

### GO_WITH_LIMITATIONS
Proceed only if the limitation is in `state/blockers.yaml` and it does not invalidate the next phase. Example: missing verified topography may permit schematic design but blocks final grading.

### NO_GO
Preserve state, write a blocker report under `docs/reports/blockers/`, and stop dependent work.

---

## Execution Handoff

At implementation time:

1. read the design spec;
2. read this master plan;
3. read the current phase section in this combined file plus interfaces it consumes;
4. create/use an isolated worktree as Superpowers requires;
5. use TDD for each code task;
6. record evidence for each Revit tool task;
7. commit after every independently testable task;
8. update `PROJECT_STATE.yaml` and incremental handoff after significant work; commit and push safe changes when a remote is available;
9. never skip a phase gate because a downstream component “probably works”.
