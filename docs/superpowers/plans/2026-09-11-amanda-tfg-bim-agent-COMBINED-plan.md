
# UNIFIED PATCH ADDENDUM — 2026-09-22

The canonical pavilion package now incorporates both uploaded patch sets.

Operational consequences:
- the historical linear R12 is frozen and cannot drive new canonical geometry;
- BIM-00 is mandatory before canonical Revit writes;
- pavilion semantics distinguish fixed architectural intent from variable BIM implementation;
- canonical geometric acceptance is mandatory before detailed BIM;
- visual-regression QA is repeated at major Revit milestones;
- R16 release is blocked by canonical geometric/visual failure unless the discrepancy is a documented and approved `CANONICAL_DEVIATION`.

Supporting contracts:
- `docs/source/references/R12_HISTORICAL_FREEZE_PROTOCOL.md`
- `docs/source/references/BIM_WRITE_GATE_PROTOCOL.md`
- `docs/source/references/PAVILION_SEMANTIC_DEFINITION.md`
- `docs/source/references/CANONICAL_GEOMETRIC_ACCEPTANCE.md`
- `docs/source/references/VISUAL_REGRESSION_QA_PROTOCOL.md`

Where older text conflicts with this addendum, the latest user direction and these canonical contracts prevail.

---

# CURRENT CANONICAL OVERRIDE — 2026-09-22

For Amanda production, the pavilion/block parti shown in `docs/source/references/canonical/` is fixed by user direction. `AMANDA-RUN-001-S01` / the linear bar is superseded. Phase 08 below has been rewritten for canonical migration. Plan 11 is the code-level migration plan and must run before the rebuilt production sequence.

---

<a id="phase-00"></a>

# Amanda TFG BIM Agent — Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Use `superpowers:using-git-worktrees` at execution time when starting from an existing repository. Use TDD for code, systematic debugging for failures, and verification-before-completion before claiming any task/phase is complete.

**Goal:** Build a local-first, fault-tolerant Codex-controlled architecture/BIM pipeline that ingests Amanda's TFG sources, proves Revit integrations on this PC, generates architectural alternatives, compiles an approved alternative into Autodesk Revit 2027, validates it, and emits an immutable GOLDEN release.

**Status:** IMPLEMENTED_IN_PROGRESS. By 2026-09-22 the project had reached PHASE_08 with substantial Tool Lab/design/QA implementation. DELIVERY MODE in Plan 10 overrides infrastructure-first prioritization; reconcile live workspace before acting.

**Architecture:** One canonical combined file containing a master section and nine phase sections. Every phase produces testable software/evidence and ends in a `GO`, `GO_WITH_LIMITATIONS`, or `NO_GO` gate. Revit production writes are forbidden until the Tool Lab has generated a verified Capability Registry.

**Tech Stack:** Windows, Autodesk Revit 2027 Education, Codex CLI, Git, PowerShell, Python 3.12 x64, pytest, Pydantic, Typer, OR-Tools, Shapely, NetworkX, IfcOpenShell; optional TopologicPy/Ladybug/Honeybee; .NET 10; Horizun Revit MCP; RevitCortex; optional Blender MCP and Autodesk APS fallback.

**Spec:** [design specification](2026-09-11-amanda-tfg-bim-agent-design.md)

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
| [00](#phase-00) | Master and bootstrap of repository | Documentation only |
| [01](#phase-01) | Foundation and durable state | Local Python/core tests; probes report Revit availability |
| [07A](#phase-07) | Tasks 1–6, 10–13 and 16 | After 01; policy, task graph, redaction and maintenance safeguards before installs |
| [03](#phase-03) | Source intelligence | After 01; independent of Revit |
| [02](#phase-02) | Provider Tool Lab | After 07A; missing Revit blocks this branch |
| [04](#phase-04) | Design engine | After 03; synthetic work may proceed with scoped input blockers |
| [05](#phase-05) | BIM compiler | After 02 and 04 |
| [06](#phase-06) | QA and synthetic release | After 05 |
| [07B](#phase-07) | Tasks 7–9, 14–15 and 17–19 | After 06; integrated recovery and fresh-session drills |
| [08](#phase-08) | Amanda production | After 06 and 07B plus resolved production input/selection gates |
| [09](#phase-09) | Rendering and cloud fallback | Optional post-release rendering; APS exception described below |

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
<a id="phase-01"></a>

# Foundation, Environment, Persistent State, and CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`. Use TDD for code, systematic debugging for failures, verification-before-completion before phase PASS.

**Goal:** Create the Python control plane, detect the real Windows/Revit/Codex/.NET environment, snapshot configurations, establish durable project state, single-writer locking, logs, and `doctor/status/resume/rollback` commands.

**Architecture:** A Python 3.12 package owns project state and deterministic policy. Environment probes are isolated so they can be unit tested. Bootstrap never edits Amanda RVTs.

**Tech Stack:** Python 3.12 x64, Typer, Pydantic v2, PyYAML, Rich, pytest, PowerShell, Git.

**Spec:** [design specification](2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- Revit 2027 Education is the target, not verified installed/licensed state. Detect it read-only; do not reinstall it as part of foundation.
- Detect Revit by installed files/metadata.
- Install a provider-specific SDK only after auditing that provider's pinned build inputs in Plan 02; Plan 01 inventories SDKs.
- Preserve existing Codex MCP config and Revit add-ins.
- Snapshot before modification.
- Never persist secrets to Git/logs.

---

## File Structure

```text
src/amanda_agent/
├── __init__.py
├── __main__.py
├── cli.py
├── paths.py
├── logging.py
├── models/
│   ├── environment.py
│   └── state.py
├── state/
│   ├── store.py
│   └── locks.py
├── bootstrap/
│   ├── revit.py
│   ├── environment.py
│   └── snapshots.py
└── commands/
    ├── doctor.py
    ├── status.py
    ├── resume.py
    └── rollback.py

tests/
├── unit/
└── bootstrap/
```

### Task 1: Bootstrap Python package and CLI [P01-T01]

**Files:**
- Create: `pyproject.toml`
- Create: `src/amanda_agent/__init__.py`
- Create: `src/amanda_agent/__main__.py`
- Create: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_cli.py`

**Interfaces:**
- Produces `python -m amanda_agent`.

- [ ] **Step 1: Write failing CLI test**

```python
from typer.testing import CliRunner
from amanda_agent.cli import app

runner = CliRunner()

def test_help_lists_core_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("doctor", "status", "resume", "rollback"):
        assert command in result.stdout
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "amanda-tfg-bim-agent"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
  "typer>=0.16,<1",
  "pydantic>=2.11,<3",
  "PyYAML>=6,<7",
  "rich>=14,<15"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.4,<9",
  "pytest-cov>=6,<7",
  "ruff>=0.12,<1",
  "mypy>=1.17,<2"
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
  "revit: requires running Revit and a verified provider",
  "slow: intentionally expensive"
]
```

- [ ] **Step 3: Prepare the test harness, run RED, then create minimal CLI**

Create package/import skeleton and Typer app with no commands, then perform Steps 4–5 to obtain the venv before the first test invocation. Run `tests/unit/test_cli.py`; record its expected failing assertion for absent commands. Import/dependency failure alone is harness setup, not the intended behavioral RED. Only after that failure, add the commands below; they explicitly fail until implemented.

```python
# src/amanda_agent/cli.py
import typer

app = typer.Typer(no_args_is_help=True)

@app.command()
def doctor() -> None:
    typer.echo("doctor: not implemented", err=True)
    raise typer.Exit(code=2)

@app.command()
def status() -> None:
    typer.echo("status: not implemented", err=True)
    raise typer.Exit(code=2)

@app.command()
def resume() -> None:
    typer.echo("resume: not implemented", err=True)
    raise typer.Exit(code=2)

@app.command()
def rollback() -> None:
    typer.echo("rollback: not implemented", err=True)
    raise typer.Exit(code=2)
```

```python
# src/amanda_agent/__main__.py
from .cli import app

if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Ensure Python 3.12 x64**

```powershell
py -3.12 --version
```

If absent:

```powershell
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
```

- [ ] **Step 5: Create venv and install**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

- [ ] **Step 6: Verify GREEN and unsupported-command behavior**

Add tests that each stub exits 2 and never reports success. Later tasks replace stubs with behavior-specific failing tests first; the Phase 01 gate rejects remaining stubs.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_cli.py -v
```

Expected: PASS after implementation.

- [ ] **Step 7: Commit**

```powershell
git add pyproject.toml src tests
git commit -m "feat: add Amanda agent CLI foundation"
```

---

### Task 2: Canonical paths [P01-T02]

**Files:**
- Create: `src/amanda_agent/paths.py`
- Test: `tests/unit/test_paths.py`

**Interfaces:** `ProjectPaths.from_root(Path) -> ProjectPaths`

- [ ] Write test asserting `state`, `logs`, `bim`, `PROJECT_STATE.yaml`, and snapshots derive from root.
- [ ] Implement:

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    state: Path
    logs: Path
    bim: Path
    project_state: Path
    snapshots: Path

    @classmethod
    def from_root(cls, root: Path) -> "ProjectPaths":
        root = root.resolve()
        return cls(
            root=root,
            state=root / "state",
            logs=root / "logs",
            bim=root / "bim",
            project_state=root / "PROJECT_STATE.yaml",
            snapshots=root / "state" / "snapshots",
        )
```

- [ ] Run `pytest tests/unit/test_paths.py -v`.
- [ ] Commit `feat: add canonical project paths`.

---

### Task 3: Project-state models [P01-T03]

**Files:**
- Create: `src/amanda_agent/models/state.py`
- Test: `tests/unit/test_state_models.py`

**Interfaces:** `TaskStatus`, `PhaseGate`, `ProjectState`.

- [ ] Write failing default-state test.
- [ ] Implement:

```python
from enum import StrEnum
from pydantic import BaseModel, Field

class TaskStatus(StrEnum):
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    DEGRADED = "DEGRADED"
    BLOCKED_BY_INPUT = "BLOCKED_BY_INPUT"
    BLOCKED_BY_TOOL = "BLOCKED_BY_TOOL"
    FAILED_ROLLED_BACK = "FAILED_ROLLED_BACK"
    CRITICAL_FAILURE = "CRITICAL_FAILURE"

class PhaseGate(StrEnum):
    GO = "GO"
    GO_WITH_LIMITATIONS = "GO_WITH_LIMITATIONS"
    NO_GO = "NO_GO"

class ProjectState(BaseModel):
    project: str = "Amanda TFG BIM Agent"
    phase_id: str = "PHASE_01"
    phase_name: str = "foundation-environment-state"
    phase_status: TaskStatus = TaskStatus.PENDING
    last_completed_task: str | None = None
    next_task: str = "P01-T01"
    schema_version: int = 1
    state_revision: int = 0
    phase_gate: PhaseGate | None = None
    selected_design: str | None = None
    revit_stage: str | None = None  # no model before verified R00
    current_checkpoint: str | None = None
    blockers: list[str] = Field(default_factory=list)
    last_verified_commit: str | None = None
```

- [ ] Test JSON/YAML-safe model dump.
- [ ] Commit.

---

### Task 4: Atomic YAML state store [P01-T04]

**Files:**
- Create: `src/amanda_agent/state/store.py`
- Test: `tests/unit/test_state_store.py`

**Interfaces:** `StateStore.load`, `StateStore.save`.

- [ ] RED: round-trip, invalid schema, interrupted write, stale revision and two-process concurrent update tests. A failed save must leave the previous valid state readable.
- [ ] Implement unique temporary files in the destination directory, flush + `os.fsync`, atomic `os.replace`, and cleanup on failure. Use a separate state-store lock and compare-and-swap `state_revision` so atomic replacement cannot silently lose another writer's updates.
- [ ] Persist schema version; migrate with a backup and tested migration, never reset invalid state to defaults. Keep operation journal/checkpoint references consistent with the saved revision and reconcile after interruption.
- [ ] GREEN: run `tests/unit/test_state_store.py`, record counts, then commit.

---

### Task 5: Single-writer lock [P01-T05]

**Files:**
- Create: `src/amanda_agent/state/locks.py`
- Test: `tests/unit/test_writer_lock.py`

**Interfaces:** `WriterLock.acquire(owner)`, `release`, `inspect`.

- [ ] Test two writers cannot acquire same lease.
- [ ] Implement OS-backed exclusive ownership plus owner token, PID/start time, host, document identity, heartbeat and fencing generation in a shared local runtime root. Project worktrees/providers use the same lock; a worktree-local copy is only a diagnostic pointer. Test two processes in different worktrees and reuse of a PID.
- [ ] Test owner-only release and stale-lock inspection; expiry never permits a second writer until the old process/in-flight operation is proved inactive. Keep acquisition/release atomic and recover abandoned OS handles after process death.
- [ ] Commit.

---

### Task 6: Detect actual Revit 2027 installation [P01-T06]

**Files:**
- Create: `bootstrap/get-revit-metadata.ps1`
- Create: `src/amanda_agent/bootstrap/revit.py`
- Test: `tests/bootstrap/test_revit_detection.py`

**Interfaces:** returns executable, RevitAPI.dll, install path, product/file version.

- [ ] Write fake-filesystem test for `Autodesk/Revit 2027/RevitAPI.dll`.
- [ ] Create runtime script:

```powershell
$root = Join-Path $env:ProgramFiles "Autodesk"
$result = Get-ChildItem $root -Directory -Filter "Revit 20*" -ErrorAction SilentlyContinue | ForEach-Object {
  $exe = Join-Path $_.FullName "Revit.exe"
  $api = Join-Path $_.FullName "RevitAPI.dll"
  if ((Test-Path $exe) -and (Test-Path $api)) {
    $v = (Get-Item $exe).VersionInfo
    [pscustomobject]@{
      productName = $v.ProductName
      productVersion = $v.ProductVersion
      fileVersion = $v.FileVersion
      installPath = $_.FullName
      executablePath = $exe
      apiPath = $api
    }
  }
}
$result | ConvertTo-Json -Depth 4
```

- [ ] Run it on the live machine.
- [ ] Normalize zero/one/many probe results, check executable metadata rather than directory name alone, and record the selected exact build. Missing/ambiguous install blocks Plan 02, not non-Revit branches; installed files do not prove a valid license or successful launch.
- [ ] Store exact build in environment report.
- [ ] Commit.

---

### Task 7: Probe Codex/Git/PowerShell/Python/.NET [P01-T07]

**Files:**
- Create: `src/amanda_agent/bootstrap/environment.py`
- Test: `tests/bootstrap/test_environment_detection.py`

- [ ] Add parser test for `dotnet --list-sdks`.
- [ ] Probe:

```powershell
git --version
codex --version
$PSVersionTable.PSVersion.ToString()
py -3.12 --version
dotnet --list-sdks
```

- [ ] Record SDK inventory without installation. Plan 02 discovers the selected source build's `global.json`, project target frameworks and installer needs before requesting a provider-specific SDK.
- [ ] A missing SDK affects only that source-build route. Official download existence/version must be verified at execution time; never silently roll forward a pinned compiler or reinstall Revit to satisfy it.
- [ ] Commit probe code and nonsecret inventory, not tool binaries.

---

### Task 8: Snapshot Codex config and Revit add-in inventory [P01-T08]

**Files:**
- Create: `src/amanda_agent/bootstrap/snapshots.py`
- Test: `tests/unit/test_snapshots.py`

- [ ] Write redaction test for keys containing TOKEN/SECRET/PASSWORD/API_KEY/AUTHORIZATION.
- [ ] Implement redaction.
- [ ] Resolve active Codex home from `CODEX_HOME` when set, otherwise the documented user default; do not change the variable. Record the effective configuration source without exposing its content.
- [ ] Keep a byte-preserving config backup under ignored `state/snapshots/private/<timestamp>/`, restricted to the local user. Produce a separate redacted summary for Git. Redacting the only backup would prevent exact rollback.
- [ ] Inventory both `%ProgramData%/Autodesk/Revit/Addins/2027` and `%APPDATA%/Autodesk/Revit/Addins/2027`, referenced assemblies and bundle locations relevant to the chosen installer. Save paths, hashes, versions and intended writes.
- [ ] Test nested secrets, command arguments and headers; scan all staged metadata before commit. Never bulk-stage raw snapshots.
- [ ] Verify restoration on a disposable config fixture; commit only code and sanitized summaries.

---

### Task 9: Structured JSONL logger [P01-T09]

**Files:**
- Create: `src/amanda_agent/logging.py`
- Test: `tests/unit/test_logging.py`

- [ ] Test one record has timestamp/task/operation/provider/status.
- [ ] Implement append-only JSONL writer.
- [ ] Ensure redaction occurs before raw exception payloads are persisted.
- [ ] Commit.

---

### Task 10: `doctor` [P01-T10]

**Files:**
- Create: `src/amanda_agent/commands/doctor.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_doctor.py`

**Interfaces:** writes `state/environment-report.json`, returns nonzero on critical failure.

- [ ] Test phase-aware results: missing Revit blocks BIM/provider work, while source/solver commands remain usable.
- [ ] Test missing provider-specific SDK blocks only a selected source build; core `doctor` reports it as inventory, not a universal failure.
- [ ] Test missing Codex is critical.
- [ ] Wire probes into report.
- [ ] Run `python -m amanda_agent doctor` on live PC.
- [ ] Commit.

---

### Task 11: `status`, `resume`, `rollback` [P01-T11]

**Files:**
- Create command modules and tests.

- [ ] `status` is read-only and prints phase, next task, blocker count, writer lease, Revit stage.
- [ ] Implement the minimal typed blocker/task-DAG models here so `resume` is usable before 07A; 07A extends these same modules, not a second implementation. `resume` blocks only affected tasks; reject unknown dependencies/cycles and never infer severity from a string prefix.
- [ ] `rollback` validates source checkpoint hash and copies it to a **new** working filename.
- [ ] `rollback` enforces resolved writable roots/protected-file identity and the shared writer lease; rejects existing targets, junction/hardlink escapes, active-document mismatch and source/checkpoint destinations. Filename tokens are secondary guards. Require quiescent Revit before restore.
- [ ] Test all four conditions.
- [ ] Commit.

---

### Task 12: Initialize durable state files [P01-T12]

**Files:**
- Create: `PROJECT_STATE.yaml`
- Create: `state/bim-environment.lock.yaml`
- Create: `state/blockers.yaml`
- Create: `state/tool-health.yaml`

- [ ] Serialize default `ProjectState` with the real code.
- [ ] Record actual Revit build, Python, Codex, Git, PowerShell, .NET SDKs.
- [ ] Before ingestion, source topography status is null/uninspected; afterward use `MISSING` or `VERIFIED_TOPOGRAPHY`. Representation `PLANAR_PLACEHOLDER` is separate from source verification and never upgrades MISSING.
- [ ] Commit state baselines.

---

---

### Task 13: Add the idempotent `bootstrap` command [P01-T13]

**Files:**
- Create: `src/amanda_agent/commands/bootstrap.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_bootstrap_cli.py`

**Interfaces:** `amanda-agent bootstrap` performs only foundation/environment setup that is safe to repeat. Provider installation belongs to Plan 02.

- [ ] **Step 1: Write a test that `bootstrap` is idempotent against a temporary project root**
- [ ] **Step 2: Implement orchestration of directory creation, environment probing, safe snapshots, default state initialization, and environment-report write**
- [ ] **Step 3: Make a second invocation preserve existing state values and create no duplicate logical configuration**
- [ ] **Step 4: Run:**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_bootstrap_cli.py -v
.\.venv\Scripts\python.exe -m amanda_agent bootstrap
```

Expected: exit 0 when Plan 01 prerequisites are green; no Revit provider is installed.

- [ ] **Step 5: Commit**

```powershell
git add src/amanda_agent/commands/bootstrap.py src/amanda_agent/cli.py tests/unit/test_bootstrap_cli.py
git commit -m "feat: add idempotent environment bootstrap command"
```

## Phase 01 Verification Gate

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit tests/bootstrap -q
.\.venv\Scripts\python.exe -m amanda_agent doctor
.\.venv\Scripts\python.exe -m amanda_agent status
git status --short
```

### GO
- tests PASS;
- Revit detection result recorded; absent/ambiguous builds produce a scoped Plan 02 blocker;
- Codex detected;
- SDK inventory recorded; provider-specific prerequisites deferred to the audited build route;
- snapshots created;
- state files valid;
- no stale writer lease;
- Git clean.

### NO_GO
Core state/path/CLI/redaction failure blocks all dependent phases. Missing Revit or license blocks Plan 02 only; 03 and 04 may proceed within their source gates.
<a id="phase-02"></a>

# Revit Tool Lab, Provider Validation, and Capability Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`. Use TDD for registry/policy code, systematic debugging for every provider failure, and verification-before-completion before promoting any capability.

**Goal:** Install Horizun and RevitCortex from pinned source, prove their capabilities against the actual Revit 2027 build in disposable models, prove a custom Revit API fallback, inject failures, and build the deterministic Capability Registry used by production.

**Architecture:** Nothing in this plan touches Amanda production. Every provider gets its own disposable RVT copies. Codex discovers the **actual** MCP tool catalog after installation and records a semantic toolmap; no tool names are invented from documentation. Promotion requires independent model re-query and save/reopen persistence.

**Tech Stack:** Revit 2027, .NET 10, Horizun Revit MCP, RevitCortex, Codex MCP, C#, Python/Pydantic/pytest.

**Spec:** [design specification](2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- Revit closed for provider install/build/deploy.
- Source-first; pin repository commit before installation.
- Preserve all existing Codex MCP servers.
- Horizun is tested first and preferred on ties.
- Cortex is a verified fallback, not a competing simultaneous writer.
- Arbitrary code execution is lab-only until typed-tool need is proven.
- Every mutation test uses a fresh disposable RVT copy.
- Save→close→reopen persistence is mandatory for capability PASS.
- Never infer PASS from README claims.

## File Structure

```text
vendor/
├── horizun-revit-mcp/
└── RevitCortex/

src/amanda_agent/
├── models/capability.py
├── tools/registry.py
├── tools/circuit_breaker.py
├── tools/evidence.py
└── providers/
    ├── toolmap.py
    └── selection.py

state/
├── capabilities.yaml
├── install-manifest.yaml
└── providers/
    ├── horizun-toolmap.yaml
    └── revitcortex-toolmap.yaml

tool-lab/
├── fixtures/
├── horizun/
├── revitcortex/
├── custom-api/
├── fault-injection/
└── reports/

revit/lab/
├── baseline/
├── horizun/
├── revitcortex/
└── custom-api/
```

---

### Task 1: Capability registry models [P02-T01]

**Files:**
- Create: `src/amanda_agent/models/capability.py`
- Create: `src/amanda_agent/tools/registry.py`
- Test: `tests/unit/test_capability_registry.py`

**Interfaces:** `CapabilityRegistry.record`, `CapabilityRegistry.preferred`.

- [ ] **Step 1: Write failing selection test**

Write RED cases using fixture evidence records with synthetic scope clearly marked: FAIL is never selected; a bare PASS with no build/schema/evidence/persistence is rejected; stale build or tool schema is rejected; a valid matching capability wins deterministically. Test production selection against synthetic evidence to ensure it is refused.

- [ ] **Step 2: Implement status/provider models**

```python
from enum import StrEnum
from pydantic import BaseModel, Field

class CapabilityStatus(StrEnum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    DEGRADED = "DEGRADED"
    UNTESTED = "UNTESTED"
    FAIL = "FAIL"
    RETIRED = "RETIRED"

class ProviderCapability(BaseModel):
    provider: str
    status: CapabilityStatus
    priority: int
    provider_commit: str | None = None
    transport_provider: str | None = None
    tool_schema_hash: str | None = None
    tested_scope: dict = Field(default_factory=dict)
    evidence_scope: str = "SYNTHETIC"
    revit_build: str | None = None
    save_reopen: bool = False
    warnings_delta: int = 0
    evidence: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
```

- [ ] **Step 3: Selection rules**
  1. validate evidence paths/hashes, installed artifact and provider commit, exact Revit build, tool_schema_hash, tested_scope (operation/types/units/limits), and transport health; write operations require independent query and persistence; reject incomplete/stale or synthetic-only evidence for production;
  2. then select only `PASS` or explicitly accepted `PASS_WITH_WARNINGS`;
  3. prefer `PASS`;
  4. lowest numeric priority wins;
  5. provider name is deterministic tie-breaker.

The model snippet permits recording UNTESTED/FAIL entries; promotion/selection validators enforce all evidence invariants. A status field alone is never promotion.

- [ ] **Step 4: Persist YAML atomically and test round-trip**
- [ ] **Step 5: Run test and commit**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_capability_registry.py -v
git add src/amanda_agent/models/capability.py src/amanda_agent/tools tests/unit/test_capability_registry.py
git commit -m "feat: add deterministic capability registry"
```

---

### Task 2: Circuit breaker [P02-T02]

**Files:**
- Create: `src/amanda_agent/tools/circuit_breaker.py`
- Test: `tests/unit/test_circuit_breaker.py`

- [ ] Test three consecutive equivalent failures open breaker.
- [ ] Implement states `CLOSED`, `OPEN`, `HALF_OPEN`.
- [ ] Success resets failure counter.
- [ ] Persist breaker scope (provider/build/capability/error signature) across sessions. OPEN blocks calls until a controlled read-only HALF_OPEN probe after cooldown/remediation; close only on independent success. Input errors do not count as provider-health failures.
- [ ] Commit.

---

### Task 3: Evidence record model [P02-T03]

**Files:**
- Create: `src/amanda_agent/tools/evidence.py`
- Test: `tests/unit/test_evidence.py`

**Interfaces:** each capability test stores provider, tool, input fixture, raw output path, model-query evidence, warning delta, duration, save/reopen result, artifact hashes.

- [ ] Write validation test requiring model-query evidence for write PASS.
- [ ] Implement model.
- [ ] Test that `success=true` without independent evidence cannot serialize as capability PASS.
- [ ] Commit.

---

### Task 4: Clone/audit/pin/build/install Horizun from source [P02-T04]

**Files:**
- Create: `tool-lab/horizun/source-audit.md`
- Modify: `state/install-manifest.yaml`
- Modify: `state/bim-environment.lock.yaml`

- [ ] **Step 1: Confirm Revit is closed**

```powershell
Get-Process Revit -ErrorAction SilentlyContinue
```

If Revit has user work open, request normal save/close. Do not force-kill an unknown model.

- [ ] **Step 2: Clone**

```powershell
New-Item -ItemType Directory -Force vendor | Out-Null
git clone https://github.com/HorizunGroup/horizun-revit-mcp.git vendor/horizun-revit-mcp
git -C vendor/horizun-revit-mcp rev-parse HEAD
git -C vendor/horizun-revit-mcp status --short
```

Expected: clean checkout. Record SHA.

- [ ] **Step 3: Read upstream execution contracts before running code**

Codex must read:
- `vendor/horizun-revit-mcp/AGENTS.md`;
- `README.md`;
- `install.ps1`;
- any client-registration script that will modify Codex config.

Write `tool-lab/horizun/source-audit.md` containing exact commit, prerequisites, expected writes, network activity, config edits, rollback/uninstall path.

- [ ] **Step 4: Verify the pinned source-build SDK and deployment isolation**

```powershell
dotnet --list-sdks
```

Read the pinned `global.json` (reviewed upstream currently requests `10.0.400`) and confirm official availability. If absent, download Microsoft's installer to a local file, inspect it and install the exact SDK under `.tools/dotnet`; verify with the absolute `dotnet.exe` and set PATH only for this build process. Record source/version/hash. Do not substitute another SDK silently. Revit and client restarts require a persisted handoff first.

- [ ] **Step 5: Run upstream source installer**

```powershell
Push-Location vendor/horizun-revit-mcp
powershell -ExecutionPolicy Bypass -File .\install.ps1
Pop-Location
```

Expected: detects Revit 2027; builds matching add-in and MCP server; verifies installed binaries.

- [ ] **Step 6: Find installed MCP executable and hash it**

```powershell
# Resolve the exact path from the audited installer manifest/status.
# Fail if absent, ambiguous, outside the intended install root or hash-mismatched.
# Persist it as HorizunExe only after checking the installed version/commit.
```

- [ ] **Step 7: Confirm Codex registration**

```powershell
codex mcp list
```

If automatic registration is absent:

```powershell
codex mcp add horizun-revit -- $HorizunExe
codex mcp list
```

- [ ] **Step 8: Configure only Horizun timeouts**

Snapshot the active Codex config location resolved in Plan 01 first. Coordinate a separate resume session if the installer requires Codex closed; it cannot close its own active session and then continue inline. Ensure the `horizun-revit` table has `startup_timeout_sec = 120` and `tool_timeout_sec = 600`, preserving every other server.

- [ ] **Step 9: Write install manifest**

Record source URL, commit, installed exe path, SHA256, Revit build, SDK version, config snapshot path, rollback procedure.

- [ ] **Step 10: Commit audit/manifests**

```powershell
git add tool-lab/horizun/source-audit.md state/install-manifest.yaml state/bim-environment.lock.yaml
git commit -m "chore: install and pin Horizun Revit MCP"
```

---

### Task 5: Create immutable disposable Revit baseline fixture [P02-T05]

**Files/Artifacts:**
- Create: `tool-lab/fixtures/baseline-fixture.yaml`
- Create: `tool-lab/fixtures/baseline-manifest.json`
- Artifact: `revit/lab/baseline/LAB_R00_EMPTY.rvt`

- [ ] Define intended fixture metadata:

```yaml
fixture_id: LAB_BASELINE_001
revit_year: 2027
project_units: metric
purpose: provider-smoke-and-fault-injection
```

- [ ] Launch Revit 2027 and create a new disposable architectural project using an installed architectural template discovered on the PC.
- [ ] Save exactly as `revit/lab/baseline/LAB_R00_EMPTY.rvt`.
- [ ] Close and reopen once without any provider writes.
- [ ] Hash it:

```powershell
Get-FileHash revit/lab/baseline/LAB_R00_EMPTY.rvt -Algorithm SHA256
```

- [ ] Record hash and initial warning/model summary.
- [ ] Never mutate the baseline itself; copy it for every test case.

---

### Task 6: Discover actual Horizun MCP tool catalog [P02-T06]

**Files:**
- Create: `state/providers/horizun-toolmap.yaml`
- Create: `tool-lab/horizun/tool-discovery.md`
- Test: `tests/providers/test_toolmaps.py`

**Interfaces:** semantic capability names map to **actual discovered tool names**.

- [ ] Restart Codex after registration.
- [ ] Run `/mcp`; confirm `horizun-revit` active.
- [ ] Use Codex MCP tool search/catalog inspection to identify actual tools for:
  - health;
  - document info/query;
  - model scan/query;
  - level;
  - wall;
  - floor;
  - room;
  - door;
  - window;
  - views;
  - section/elevation;
  - sheets;
  - schedules;
  - dimensions;
  - site/toposolid;
  - save;
  - PDF/IFC/DWG/image export;
  - custom Python execution if exposed.
- [ ] Generate `horizun-toolmap.yaml` directly from actual catalog results; do not type guessed tool names.
- [ ] Add a validator test rejecting unresolved placeholder-marker patterns in any committed toolmap scalar.
- [ ] Commit toolmap and discovery evidence.

---

### Task 7: Horizun read-only smoke [P02-T07]

**Artifacts:** `revit/lab/horizun/LAB_HORIZUN_READ.rvt`, `tool-lab/horizun/results/read-smoke.json`.

- [ ] Copy baseline to Horizun read fixture.
- [ ] Open copy in Revit.
- [ ] Invoke mapped health/document/read tools.
- [ ] Verify returned document path is disposable copy.
- [ ] Capture baseline element summary and warning count.
- [ ] Re-query after reads and assert no mutation.
- [ ] Promote read capabilities only with evidence.

---

### Task 8: Horizun `create_level` persistence test [P02-T08]

**Fixture:** fresh baseline copy.

- [ ] Query levels before.
- [ ] Create `LAB_LEVEL_TEST` at 4.0 m using actual mapped typed tool.
- [ ] Re-query; exactly one expected level delta.
- [ ] Verify elevation within 2 mm.
- [ ] Save.
- [ ] Close Revit.
- [ ] Reopen fixture.
- [ ] Re-query level.
- [ ] Mark `create_level` PASS only if persistence succeeds.

---

### Task 9: Horizun `create_wall` persistence test [P02-T09]

Desired wall:
- straight;
- 10.0 m design length;
- base on known level;
- 3.0 m height.

- [ ] Query before.
- [ ] Create typed wall.
- [ ] Re-query by returned ID and by spatial/category query.
- [ ] Verify count delta = 1.
- [ ] Verify length, level, height within configured tolerance.
- [ ] Record warnings delta.
- [ ] Save/close/reopen/re-query.
- [ ] Promote only after persistence.

---

### Task 10: Horizun floor and room tests [P02-T10]

- [ ] Fresh baseline copy for floor.
- [ ] Create 6 m × 4 m floor (target 24 m²).
- [ ] Verify area, level, polygon, warnings, persistence.
- [ ] Fresh baseline copy for room.
- [ ] Create verified 4 m × 4 m enclosure.
- [ ] Place named/numbered room.
- [ ] Verify placed/enclosed/area/persistence.
- [ ] Record both capabilities.

---

### Task 11: Horizun hosted/documentation/export matrix [P02-T11]

For each capability use a fresh or intentionally composite lab fixture and record evidence:

- [ ] door hosted in verified wall;
- [ ] window hosted in verified wall;
- [ ] floor plan view;
- [ ] section/elevation;
- [ ] sheet + viewport;
- [ ] room schedule;
- [ ] dimension;
- [ ] PDF export + nonzero file;
- [ ] IFC export + retain for later parser verification;
- [ ] DWG/image export when mapped tool exists;
- [ ] composite save/close/reopen.

Each result records input, actual tool, raw output, independent query, warning delta, duration, artifact path/hash.

---

### Task 12: Horizun Toposolid/site test [P02-T12]

Use only synthetic geometry:

```yaml
points_m:
  - [0, 0, 0.0]
  - [20, 0, 0.5]
  - [20, 20, 1.0]
  - [0, 20, 0.5]
```

- [ ] Fresh baseline copy.
- [ ] Invoke actual mapped site capability if available.
- [ ] Verify bounding/extents/elevation through best independent model query available.
- [ ] Save/reopen.
- [ ] Mark `PASS`, `DEGRADED`, or `FAIL`; never assume production Toposolid support.

---

### Task 13: Clone/audit/build/deploy RevitCortex [P02-T13]

**Files:** source audit, install manifest, environment lock.

- [ ] Close Revit normally.
- [ ] Clone/pin:

```powershell
git clone https://github.com/LuDattilo/RevitCortex.git vendor/RevitCortex
git -C vendor/RevitCortex rev-parse HEAD
```

- [ ] Read README, security docs, workflows, deploy script, code-execution security notes.
- [ ] Write audit report.
- [ ] Restore/build server:

```powershell
dotnet restore vendor/RevitCortex/src/RevitCortex.Server/RevitCortex.Server.csproj
dotnet build vendor/RevitCortex/src/RevitCortex.Server/RevitCortex.Server.csproj -c Release
```

- [ ] Build Revit 2027 plugin:

```powershell
dotnet build -c "Release R27" vendor/RevitCortex/src/RevitCortex.Plugin/RevitCortex.Plugin.csproj
```

- [ ] Deploy:

```powershell
Push-Location vendor/RevitCortex
powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -RevitVersion 2027 -Config Release
Pop-Location
```

- [ ] Find actual server executable:

```powershell
# Publish the audited server project/configuration to one isolated output directory.
# Resolve CortexExe from that publish manifest; verify framework, version and hash.
# Fail on ambiguity instead of choosing the newest executable in the repository.
```

- [ ] Register:

```powershell
codex mcp add revitcortex -- $CortexExe
codex mcp list
```

- [ ] Record commit/path/hash/config snapshot/rollback.
- [ ] Commit audit/manifests.

---

### Task 14: Discover Cortex tools and prove bridge [P02-T14]

- [ ] Open fresh Cortex lab RVT.
- [ ] Turn the RevitCortex ribbon `Cortex Switch` ON; it is off by default in current docs.
- [ ] Confirm bridge is localhost only.
- [ ] Confirm Codex `/mcp` sees server/tools.
- [ ] Generate actual `revitcortex-toolmap.yaml` from catalog.
- [ ] Validate no placeholders.
- [ ] Record current port/settings and logs.

---

### Task 15: A/B Cortex smoke using identical fixtures [P02-T15]

Repeat the exact same desired inputs used for Horizun:

- [ ] level;
- [ ] 10 m wall;
- [ ] 24 m² floor;
- [ ] room;
- [ ] hosted door/window;
- [ ] views/sheet/schedule;
- [ ] save/close/reopen.

Compare geometry, warnings, persistence, duration. Do not alter Horizun results.

---

### Task 16: Custom C# Revit API fallback proof [P02-T16]

**Files:** `tool-lab/custom-api/CreateLabWall.cs`, result report.

- [ ] Write exact C# that retrieves a known level, converts meters to Revit internal units, creates one 5 m wall at 3 m height inside a transaction, logs returned ElementId, and throws on missing prerequisites.
- [ ] Execute through a verified host in a disposable file and record `transport_provider`. A custom script using Cortex/Horizun inherits that host's outage; for an independent fallback, test a separate Revit ExternalCommand/ExternalEvent add-in. Python outside Revit cannot invoke document mutations directly.
- [ ] Re-query independently.
- [ ] Save/close/reopen.
- [ ] Register `custom_csharp:create_wall` only if PASS.

---

### Task 17: Fault-injection matrix [P02-T17]

**Files:** `tool-lab/fault-injection/matrix.yaml`, results report.

Run each against disposable files:

- [ ] invalid element ID → classify `E01`;
- [ ] nonexistent family/type → no mutation;
- [ ] hosted element without host → no orphan;
- [ ] MCP disabled/disconnected → `E02`;
- [ ] Revit closed → provider unavailable, not false success;
- [ ] intentionally invalid batch item after valid items → measure provider atomicity;
- [ ] repeated same failure ×3 → circuit breaker OPEN;
- [ ] timeout on long read → verify before retry because Revit may still be working.

Document exact semantics per provider.

---

### Task 18: Crash/recovery drill [P02-T18]

- [ ] Create/hash known-good disposable checkpoint.
- [ ] Persist task as RUNNING.
- [ ] Make one mutation in working copy.
- [ ] Before simulated crash, prove the owned PID/start time has only disposable documents, no user model, and a verified checkpoint; terminate only that process. If ownership cannot be proved, block the destructive drill and preserve user work.
- [ ] Start new Revit process.
- [ ] Open last PASS checkpoint.
- [ ] Reconnect preferred provider.
- [ ] Rerun health/read smoke.
- [ ] Confirm interrupted mutation is not marked PASS.
- [ ] Record drill PASS/FAIL.

---

### Task 19: Provider benchmark and final matrix [P02-T19]

**Files:**
- Create: `tool-lab/reports/provider-benchmark.md`
- Modify: `state/capabilities.yaml`
- Modify: `state/tool-health.yaml`
- Modify: `state/bim-environment.lock.yaml`

For every tested capability rank:
1. reliability;
2. model quality;
3. save/reopen persistence;
4. observability/error quality;
5. warning cleanliness;
6. speed.

Rules:
- prefer Horizun on genuine tie;
- prefer Cortex when evidence is materially better;
- custom API is fallback unless both typed paths fail;
- IFC/DXF/cloud are not inserted until their own tests exist;
- no `UNTESTED` provider may be preferred.

- [ ] Write final environment pins (Revit build + both provider commits/hashes).
- [ ] Commit matrix/report.

---

---

### Task 20: Add the `tool-lab` CLI surface [P02-T20]

**Files:**
- Create: `src/amanda_agent/commands/tool_lab.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_tool_lab_cli.py`

**Interfaces:**
- `amanda-agent tool-lab status`
- `amanda-agent tool-lab queue`
- `amanda-agent tool-lab verify-registry`

The CLI does not replace Codex MCP calls; it owns the deterministic queue, evidence requirements, and registry validation around those calls.

- [ ] **Step 1: Test `status` reports provider commit, health, PASS/FAIL/UNTESTED counts**
- [ ] **Step 2: Test `queue` never emits a production file path and schedules UNTESTED required capabilities first**
- [ ] **Step 3: Test `verify-registry` fails when a preferred provider is UNTESTED/FAIL or lacks save/reopen evidence for a write capability**
- [ ] **Step 4: Implement commands and run:**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_tool_lab_cli.py -v
.\.venv\Scripts\python.exe -m amanda_agent tool-lab status
.\.venv\Scripts\python.exe -m amanda_agent tool-lab verify-registry
```

- [ ] **Step 5: Commit**

```powershell
git add src/amanda_agent/commands/tool_lab.py src/amanda_agent/cli.py tests/unit/test_tool_lab_cli.py
git commit -m "feat: add Revit Tool Lab control commands"
```

## Phase 02 Verification Gate

### GO
- Installed providers are pinned and connected; every required operation is covered by at least one eligible provider.
- At least one typed provider passes core read/write/save/reopen for level/wall/floor/room.
- Each required core operation has a tested fallback/recovery route. Record transport dependencies; a custom API route is eligible only for its tested scope. Missing a second typed provider is a scoped limitation if an independent tested recovery route covers the required operation.
- Custom API proof works.
- Fault injection + crash drill complete.
- No Amanda production file opened.

### GO_WITH_LIMITATIONS
Any missing preferred/secondary provider or noncore capability is explicitly scoped; a tested eligible route covers every operation required by the next stage. No missing critical operation is waived.

### NO_GO
No stable typed provider can perform core read/write/persistence on this actual Revit 2027 build.
<a id="phase-03"></a>

# Project Intelligence and Source Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for parser/schema code; systematic debugging for reconciliation failures.

**Goal:** Convert Amanda's TFG, program of needs, site material, and verified normative/source files into canonical structured project data with immutable provenance and an explicit missing-data registry.

**Architecture:** Source files are immutable. Extraction produces three separate classes: `SOURCE_FACT`, `DERIVED_CONSTRAINT`, and `DESIGN_HYPOTHESIS`. Canonical JSON/YAML is schema-validated and becomes the only input consumed by the Design Engine.

**Tech Stack:** Python 3.12, Pydantic, PyYAML, local PDF parser, Shapely/GeoJSON.

**Spec:** [design specification](2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- Preserve original source bytes and SHA-256.
- Never silently “correct” Amanda's source values.
- Every `SOURCE_FACT` has a source reference.
- Missing topography remains missing.
- Numeric normative rules enter hard constraints only from a verified source/version.

## File Structure

```text
src/amanda_agent/
├── ingest/
│   ├── manifest.py
│   ├── provenance.py
│   ├── pdf.py
│   └── pipeline.py
├── requirements/
│   ├── models.py
│   ├── relations.py
│   ├── regulations.py
│   └── validators.py
└── site/
    ├── models.py
    ├── geometry.py
    └── transform.py

project/
├── requirements/
├── site/
├── regulations/
├── references/
└── provenance/

docs/source/
```

---

### Task 1: Source manifest and hashing [P03-T01]

**Files:**
- Create: `src/amanda_agent/ingest/manifest.py`
- Test: `tests/unit/test_source_manifest.py`

**Interfaces:** `sha256_file(Path) -> str`, `SourceDocument`.

- [ ] Write SHA-256 fixture test using `abc` known digest.
- [ ] Implement streaming file hash (1 MiB chunks; no full-file load required).
- [ ] Define `SourceDocument` fields: source_id, filename, sha256, mime_type, ingested_at, immutable_path.
- [ ] Test round-trip.
- [ ] Commit.

---

### Task 2: Provenance model [P03-T02]

**Files:**
- Create: `src/amanda_agent/ingest/provenance.py`
- Test: `tests/unit/test_provenance.py`

**Interfaces:**

```python
class FactClass(StrEnum):
    SOURCE_FACT = "SOURCE_FACT"
    DERIVED_CONSTRAINT = "DERIVED_CONSTRAINT"
    DESIGN_HYPOTHESIS = "DESIGN_HYPOTHESIS"
```

Each `SourceReference` includes source ID/hash, page/paragraph/table or sheet/cell locator, extraction method, confidence and note. Add verification_status and adoption_status from design section 1.1; a source statement may be DISPUTED and a documented hypothesis remains DESIGN_HYPOTHESIS.

- [ ] Test `SOURCE_FACT` without source ID is rejected.
- [ ] Test a hypothesis cannot claim fact class.
- [ ] Implement.
- [ ] Commit.

---

### Task 3: Immutable ingest command [P03-T03]

**Files:**
- Create: `src/amanda_agent/commands/ingest.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_ingest_command.py`

**Interfaces:** `amanda-agent ingest PATH...`

- [ ] Test source copied byte-for-byte into `docs/source/`.
- [ ] Test same content hash is recognized and not duplicated unnecessarily.
- [ ] Test a different file cannot overwrite an existing immutable source path.
- [ ] Generate/update `project/provenance/source-manifest.yaml` atomically.
- [ ] Commit.

---

### Task 4: Inventory and reconcile all supplied Amanda sources [P03-T04]

**Expected sources:** the root TFG/program PDFs and the 21-file `TFG_Amanda_2026/` supporting package. Follow the source table in design section 1.1. Inventory DOCX/XLSX/SVG/DXF/IFC/PPTX/HTML as well as PDFs; do not execute embedded scripts or follow external links during extraction.

- [ ] Search the explicitly provided input folder/path, not the entire user's home drive.
- [ ] Treat support documents as source assertions/hypotheses, not primary verified regulation or approved architecture. `PROGRAM_BASELINE = RESOLVED`: the user explicitly selected **20 people according to programa_necessidades.pdf** on 2026-09-15. Adopt its full program (626 m² internal useful area, 260 m² programmed external area); preserve the spreadsheet's 42-person hypothesis as not adopted. Persist the selection with source SHA256 and this decision's provenance; do not ask for the same choice again or merge spreadsheet quantities into the PDF baseline.
- [ ] If either core PDF source is absent, set production blocker `BLOCKED_BY_INPUT:SOURCE_DOCUMENTS`, but keep synthetic development usable.
- [ ] When present, assign stable IDs `SRC-TFG-001`, `SRC-PROGRAM-001` for this source version.
- [ ] Compute hashes.
- [ ] Verify copied bytes match hashes.
- [ ] Keep PDFs private/local; commit them only if repository policy explicitly allows source documents. Manifests can be committed independently.

---

### Task 5: PDF text extraction adapter [P03-T05]

**Files:**
- Create: `src/amanda_agent/ingest/pdf.py`
- Test: `tests/unit/test_pdf_adapter.py`

- [ ] Add a local parser dependency only after a small compatibility test; prefer PyMuPDF or pypdf based on actual extraction quality. Install and lock the tested Shapely version here before site-schema validation (Plan 04 reuses this lock), plus DOCX/XLSX adapters when needed. Dependencies required by this phase cannot first be installed in Phase 04.
- [ ] Create fixture PDF with two pages and known text.
- [ ] Test page-number-preserving extraction.
- [ ] Store extracted text under `project/provenance/extracted/` with source hash.
- [ ] Never treat OCR output as authoritative when selectable text exists.
- [ ] Add tested DOCX paragraph/table and XLSX sheet/cell/formula adapters. Distinguish formulas, cached values and independently recalculated values; a stale cache is not proof. Inspect drawings/IFC units and provenance in read-only copies. Retain placeholders/conflicts with locators.
- [ ] Commit parser choice/version to environment lock.

---

### Task 6: Program requirement schema [P03-T06]

**Files:**
- Create: `src/amanda_agent/requirements/models.py`
- Test: `tests/unit/test_requirement_models.py`

**Interfaces:** `SpaceRequirement`, `SectorRequirement`, `ProgramRequirementSet`.

- [ ] Write tests rejecting zero/negative canonical area/quantity, empty provenance, NaN/infinity, invalid ranges and duplicate IDs. Use a separate draft-extraction schema with nulls for unknowns; canonical compilation blocks required unknown fields instead of inventing them.
- [ ] Implement:

```python
from pydantic import BaseModel, Field, model_validator

class SpaceRequirement(BaseModel):
    logical_id: str
    name: str
    sector: str
    quantity: int = Field(ge=1)
    target_area_m2: float = Field(gt=0)
    min_area_m2: float | None = Field(default=None, gt=0)
    max_area_m2: float | None = Field(default=None, gt=0)
    privacy_level: int | None = Field(default=None, ge=0, le=5)
    accessible: bool | None = None
    source_refs: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_range(self):
        if self.min_area_m2 is not None and self.target_area_m2 < self.min_area_m2:
            raise ValueError("target below minimum")
        if self.max_area_m2 is not None and self.target_area_m2 > self.max_area_m2:
            raise ValueError("target above maximum")
        return self
```

- [ ] Test and commit.

---

### Task 7: Compile the program of needs into canonical JSON [P03-T07]

**Files:**
- Create at runtime: `project/requirements/program.json`
- Create: `project/requirements/program-summary.md`
- Test: `tests/project/test_amanda_program.py`

- [ ] Extract every program line item exactly from source.
- [ ] Assign one requirement ID per source row and expand quantity into stable instance IDs only at generation. Explicitly tag internal/external area and whether target_area_m2 is per unit; every total is quantity × unit area. Avoid double expansion.
- [ ] Record source quantity/target-area facts.
- [ ] Import the selected PDF baseline for up to 20 simultaneously accommodated people. Preserve its room quantities and per-unit area targets; distribution of women/children/beds needs layout validation. Record the 42-person spreadsheet as an unselected hypothesis; adapt derived calculations from the adopted inputs instead of importing the other scenario's totals. User selection resolves adoption, not normative verification or APPROVED_FOR_BIM.
- [ ] Reconcile source subtotals and overall internal/external totals.
- [ ] Add tests for known source totals and presence of accessible bedroom/bathroom requirements.
- [ ] Generate markdown summary from canonical JSON, never the reverse.
- [ ] Commit canonical JSON and tests.

---

### Task 8: Relations schema [P03-T08]

**Files:**
- Create: `src/amanda_agent/requirements/relations.py`
- Test: `tests/unit/test_relations.py`

Relation enum:
- `MUST_ADJOIN`
- `SHOULD_ADJOIN`
- `SHOULD_BE_NEAR`
- `CAN_BE_NEAR`
- `NEUTRAL`
- `SHOULD_BE_SEPARATED`
- `MUST_BE_SEPARATED`

- [ ] Test self-relations rejected unless explicitly whitelisted for group relation.
- [ ] Add weight and optional max/preferred distance.
- [ ] Add flow-network enum: resident, child, staff, visitor, service, emergency.
- [ ] Commit.

---

### Task 9: Compile source-backed principles separately from design hypotheses [P03-T09]

**Files:**
- Create: `project/requirements/source-principles.yaml`
- Create: `project/requirements/design-hypotheses.yaml`
- Test: `tests/project/test_fact_separation.py`

- [ ] Extract only TFG-supported principles into source-principles, including the stated shelter/transition/city logic, block/garden parti, privacy/security concepts, and stated climate orientation findings.
- [ ] Put inferred room adjacency proposals into design-hypotheses.
- [ ] Every source principle gets source refs.
- [ ] Validator forbids a `DESIGN_HYPOTHESIS` object from appearing in source-principles.
- [ ] Commit.

---

### Task 10: Canonical site schema [P03-T10]

**Files:**
- Create: `src/amanda_agent/site/models.py`
- Test: `tests/unit/test_site_models.py`

Fields:
- boundary polygon;
- design coordinate origin;
- true north;
- frontages/roads;
- candidate access points;
- buildable area if verified;
- setbacks if verified;
- topography state;
- provenance.

Source topography enum: `MISSING`, `VERIFIED_TOPOGRAPHY`. Separate representation enum: `PLANAR_PLACEHOLDER`, `VERIFIED_TOPOGRAPHY`. A local drawing plane may use z=0 as a design convention, but no surveyed elevation points are emitted for MISSING sources. If needed to develop a sloping-site study, store hypothetical elevations in a separate versioned scenario override with PROVISIONAL_ASSUMPTION, never in the verified/source point set; test replacement by later survey data and invalidation of affected checks.

- [ ] Test invalid self-intersecting boundary is rejected by Shapely.
- [ ] Test `MISSING` cannot carry invented elevation points.
- [ ] Commit.

---

### Task 11: Compile known site facts and missing-data registry [P03-T11]

**Files:**
- Create: `project/site/site.json`
- Create: `project/site/missing-data.yaml`

- [ ] Record reported site area 24,135 m² as a source assertion, with SITE_BOUNDARY/SITE_OCCUPANCY blockers for legal boundary, current use and relocation premise. If no verified calibrated polygon/north exists after research, create an explicitly provisional study reconstruction with uncertainty/source rationale; never claim an equal-area rectangle is the real cadastral boundary. Separate the scenario geometry from verified site data.
- [ ] Record the conflicting three/four-frontage assertions with locators. Verify actual boundary/frontages before freezing site_version; do not resolve them by counting names in prose.
- [ ] Record true north/orientation only from verified source drawing/data.
- [ ] If no verified survey/topographic file is supplied, set `topography = MISSING`.
- [ ] Add blocker:

```yaml
id: SITE_TOPOGRAPHY
state: MISSING
blocks:
  - final_grading
  - final_altimetric_accessibility_validation
allows:
  - 2d_macrozoning
  - schematic_massing_on_planar_reference
```

- [ ] Commit.

---

### Task 12: Regulation source registry [P03-T12]

**Files:**
- Create: `src/amanda_agent/requirements/regulations.py`
- Create: `project/regulations/registry.yaml`
- Test: `tests/unit/test_regulation_registry.py`

Statuses: `IDENTIFIED`, `SOURCE_ACQUIRED`, `VERIFIED`, `SUPERSEDED`.

- [ ] Seed regulation names identified by Amanda's TFG without copying remembered numerical rules.
- [ ] Require applicable primary source/version/date/article/map, extracted rule, unit, scope and verification evidence before a normative number becomes DERIVED_CONSTRAINT. Acquisition alone is not verification. The supplied LC208 DOCX and XLSX 'ATENDE' cells are secondary references only.
- [ ] Test an unverified numeric rule cannot be compiled as hard constraint.
- [ ] Commit.

---

### Task 13: Provenance integrity suite [P03-T13]

**Files:** `tests/project/test_provenance_integrity.py`

- [ ] Every source fact has source ref.
- [ ] Every requirement logical ID unique.
- [ ] No unresolved numeric source placeholder silently became a number.
- [ ] No hypothesis exists in source-fact files.
- [ ] Source file hashes still match immutable copies.
- [ ] Program subtotal/global reconciliation passes.
- [ ] Commit.

---

### Task 14: One-command validation report [P03-T14]

**Files:**
- Modify: `src/amanda_agent/commands/ingest.py`
- Runtime: `docs/reports/ingest-report.md`

- [ ] `amanda-agent ingest --validate-only` validates source hashes, canonical schemas, provenance, program totals, site status, regulation registry.
- [ ] Expected missing topography yields `GO_WITH_LIMITATIONS`, not corruption.
- [ ] Malformed canonical data yields nonzero exit.
- [ ] Report exact blocker IDs.
- [ ] Commit.

---

### Task 15: Academic deliverable and decision register [P03-T15]

**Files:** future `project/requirements/academic-deliverables.yaml`, `project/requirements/decisions.yaml`; tests `tests/project/test_deliverable_scope.py`.

- [ ] Map caderno revision, visits, metaprojeto, preliminary study, anteprojeto, pranchas, descriptive/calculation memorials, defense, authorship and institutional submission from the support plan to owner/source/status/evidence.
- [ ] Record the support claim of 4–6 A1 landscape synthesis boards as provisional until the institutional regulation is acquired. Keep dates unknown until the official calendar is available.
- [ ] Assign BIM-generated outputs versus human-authored/validated deliverables. No automated signatures, field visits or institutional submissions are implied by software completion.
- [ ] Test that an unresolved mandatory academic deliverable prevents a claim of TFG_COMPLETE while technical STUDY releases remain possible.
- [ ] Record TYPOLOGY, PROGRAM_BASELINE, SITE_BOUNDARY, SITE_OCCUPANCY and REGULATION_APPLICABILITY separately from finalist selection in `project/requirements/decision-register.yaml`, following design section 6.15.
- [ ] Implement research tasks using available read-only search/source tools: official maps/cadastral material, applicable consolidated regulation/anexos and institutional/project references. Persist queries, sources, applicability and conclusions. The agent decides routine architectural questions without waiting for preferences.
- [ ] Test that AGENT_DELEGATED can select an evidence-backed option and continue; unverified data can be recorded as PROVISIONAL_ASSUMPTION within DESIGN_HYPOTHESIS for a STUDY scenario, never VERIFIED source data. Keep normative numbers from unverified sources out of verified hard constraints.
- [ ] Test that missing source input blocks only the affected verified check, while a separately labeled provisional study can proceed; FINAL stays blocked by unresolved mandatory verification. Test later replacement of the assumption propagates to affected geometry/BIM/exports and preserves prior versions.
- [ ] Test Amanda feedback creates a new decision revision, takes precedence over delegated preferences, invalidates obsolete approval_hash and schedules the dependent validations without overwriting protected originals/releases.

## Phase 03 Verification Gate

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit tests/project -q
.\.venv\Scripts\python.exe -m amanda_agent ingest --validate-only
```

### GO
Canonical program/site/provenance valid and sufficient for intended design stage.

### GO_WITH_LIMITATIONS
Survey/topography or a normative source is missing, but schematic design remains valid within declared limits.

### NO_GO
Program/site source cannot be reconciled or source provenance is unreliable.
<a id="phase-04"></a>

# Generative Design Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for all solver/geometry code; systematic debugging for infeasible models or nondeterminism.

**Goal:** Implement deterministic generation, validation, scoring, Pareto filtering, and explanation of architectural alternatives from canonical Amanda requirements/site data.

**Architecture:** OR-Tools CP-SAT solves discrete assignment decisions; Shapely is geometric truth; NetworkX handles graphs/path metrics. Resolution progresses site → macrozones → blocks → sectors → rooms. TopologicPy and Ladybug/Honeybee are optional enhancements and must not destabilize the core engine.

**Tech Stack:** Python 3.12, OR-Tools, Shapely, NetworkX, IfcOpenShell; optional TopologicPy, Ladybug/Honeybee.

**Spec:** [design specification](2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- Same canonical input + engine version + seed = same output.
- Hard violation invalidates candidate.
- Soft constraints affect score only.
- No beauty score.
- Weights are versioned files.
- Source requirements are read-only.
- Gardens/external spaces are first-class program geometry.
- Detailed environmental simulation is finalist-only.

## File Structure

```text
src/amanda_agent/design/
├── models.py
├── geometry.py
├── constraints.py
├── adjacency.py
├── flows.py
├── privacy.py
├── archetypes.py
├── macrozones.py
├── blocks.py
├── rooms.py
├── external_spaces.py
├── environmental.py
├── scoring.py
├── pareto.py
├── generate.py
├── pipeline.py
└── explain.py

design-engine/config/
├── tolerances.yaml
├── weights.yaml
└── archetypes.yaml

tests/
├── geometry/
├── solver/
└── regression/fixtures/
```

---

### Task 1: Install and pin core design dependencies [P04-T01]

**Files:**
- Modify: `pyproject.toml`
- Create: `requirements.lock.txt`

- [ ] Add:

```toml
"ortools>=9.14,<10",
"shapely>=2.1,<3",
"networkx>=3.5,<4",
"ifcopenshell>=0.8,<1"
```

- [ ] Install:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

- [ ] Verify:

```powershell
.\.venv\Scripts\python.exe -c "import ortools, shapely, networkx, ifcopenshell; print('PASS')"
```

- [ ] Resolve these candidate ranges against available Windows/Python wheels before adopting them. Freeze exact resolved third-party packages, excluding editable absolute paths; rebuild a fresh venv from the lock and run import/core tests before claiming reproducibility:

```powershell
.\.venv\Scripts\python.exe -m pip freeze --exclude-editable | Sort-Object | Set-Content -Encoding utf8 requirements.lock.txt
```

- [ ] Commit.

---

### Task 2: Design solution models [P04-T02]

**Files:**
- Create: `src/amanda_agent/design/models.py`
- Test: `tests/solver/test_design_models.py`

**Interfaces:** `DesignSolution`, `MetricSet`, `ConstraintViolation`, `DesignStatus`.

- [ ] Write JSON round-trip test.
- [ ] Require fields: solution_id, run_id, seed, requirements_version, site_version, engine_version, archetype, geometry, metrics, hard_violations, soft_penalties, parents, status.
- [ ] Test APPROVED_FOR_BIM is explicit, content-bound and not default. AGENT_DELEGATED with valid decision evidence is eligible without Amanda approval; AMANDA_REVIEW_PENDING does not block BIM. Reject records falsely attributing personal approval or changing the fixed 20-person program.
- [ ] Commit.

---

### Task 3: Geometry primitives/tolerances [P04-T03]

**Files:**
- Create: `src/amanda_agent/design/geometry.py`
- Create: `design-engine/config/tolerances.yaml`
- Test: `tests/geometry/test_geometry.py`

- [ ] Define tolerances in meters/percent; no feet inside Design Engine.
- [ ] Test containment, overlap, minimum distance, area delta, centroid.
- [ ] Implement with Shapely, not hand-rolled polygon math.
- [ ] Test a self-intersecting polygon fails early.
- [ ] Commit.

---

### Task 4: Hard-constraint engine [P04-T04]

**Files:**
- Create: `src/amanda_agent/design/constraints.py`
- Test: `tests/solver/test_hard_constraints.py`

**Interfaces:** `validate_candidate(candidate, requirements, site) -> list[ConstraintViolation]`.

- [ ] Test room outside buildable site → violation.
- [ ] Test overlap → violation.
- [ ] Test required room missing → violation.
- [ ] Test required accessible room missing → violation.
- [ ] Test `MUST_BE_SEPARATED` broken → violation.
- [ ] Implement validators by resolution: MACRO validates sector capacities/boundary/separation; BLOCK validates block geometry and gross-area budget; ROOM validates expanded room instances, net areas and traversable routes. Checks unavailable at that resolution are NOT_EVALUATED, never PASS. Do not reject every macro candidate merely because rooms do not exist yet.
- [ ] Assert hard violations are never converted to numeric soft penalties.
- [ ] Commit.

---

### Task 5: Adjacency graph [P04-T05]

**Files:**
- Create: `src/amanda_agent/design/adjacency.py`
- Test: `tests/solver/test_adjacency.py`

- [ ] Build NetworkX graph from canonical relations.
- [ ] Test `MUST_ADJOIN` pass/fail.
- [ ] Test `SHOULD_BE_NEAR` penalty monotonically worsens with distance.
- [ ] Test `MUST_BE_SEPARATED` stays hard.
- [ ] Commit.

---

### Task 6: Flow graphs [P04-T06]

**Files:**
- Create: `src/amanda_agent/design/flows.py`
- Test: `tests/solver/test_flows.py`

- [ ] Implement independent resident/child/staff/visitor/service/emergency graphs.
- [ ] Synthetic visitor route crossing private residential node must fail when policy forbids it.
- [ ] Service/resident path crossing may be a weighted soft penalty when configured.
- [ ] Derive traversable graph edges from actual corridors, portals/doors, widths, obstacles and access permissions, with vertical connections where applicable. An adjacency or centroid line is not an accessible route. Compute path lengths/crossings deterministically and reject disconnected routes.
- [ ] Commit.

---

### Task 7: Privacy gradient metric [P04-T07]

**Files:**
- Create: `src/amanda_agent/design/privacy.py`
- Test: `tests/solver/test_privacy.py`

- [ ] Test direct public→privacy-5 transition is strongly penalized/invalid per configuration.
- [ ] Test public→controlled→technical→transition→residential scores better.
- [ ] Keep raw transition sequence in evidence.
- [ ] Commit.

---

### Task 8: Archetype configuration [P04-T08]

**Files:**
- Create: `design-engine/config/archetypes.yaml`
- Create: `src/amanda_agent/design/archetypes.py`
- Test: `tests/solver/test_archetypes.py`

Archetypes:
- COURTYARD
- LINEAR_SPINE
- CLUSTER
- PRIVACY_GRADIENT
- DOUBLE_COURTYARD
- COMB

- [ ] Define each as initialization/relationship rules, not a fixed drawing.
- [ ] Synthetic rectangular site: each archetype must produce a valid macro seed.
- [ ] Make gradient/courtyard/cluster exploration explicit for Amanda without forcing winner.
- [ ] Commit.

---

### Task 9: OR-Tools macrozone solver [P04-T09]

**Files:**
- Create: `src/amanda_agent/design/macrozones.py`
- Test: `tests/solver/test_macrozones.py`

- [ ] Write a three-sector RED test.
- [ ] Model sector-to-region assignment with CP-SAT.
- [ ] Encode bounded integer-grid variables/scaling for CP-SAT, sector capacity and separation/adjacency. Define discretization/rounding tolerance and revalidate resulting metric polygons with Shapely; reject grid-feasible but geometrically invalid results. Record solver status and infeasibility evidence separately.
- [ ] Set solver random seed from run seed.
- [ ] Test two executions with same seed produce same assignment/order.
- [ ] Commit.

---

### Task 10: Block polygon generator [P04-T10]

**Files:**
- Create: `src/amanda_agent/design/blocks.py`
- Test: `tests/solver/test_blocks.py`

- [ ] Blocks remain inside buildable area.
- [ ] Blocks do not overlap.
- [ ] Block area matches sector demand within configured band.
- [ ] Sector splitting is allowed only by archetype/configuration.
- [ ] Reject sliver polygons under minimum width.
- [ ] Commit.

---

### Task 11: Room refinement [P04-T11]

**Files:**
- Create: `src/amanda_agent/design/rooms.py`
- Test: `tests/solver/test_rooms.py`

- [ ] Start with synthetic 3-room rectangle.
- [ ] Enforce canonical area/min-dimension constraints only when they exist.
- [ ] Preserve room logical IDs.
- [ ] Reject overlaps and unreachable/orphan spaces.
- [ ] Separate net room area from gross footprint, wall thickness, shafts and circulation; assign each area once and report the net-to-gross factor as a hypothesis until modeled. Test multi-storey and single-storey accounting; outside gardens do not count as enclosed internal area.
- [ ] Commit.

---

### Task 12: External spaces as first-class geometry [P04-T12]

**Files:**
- Create: `src/amanda_agent/design/external_spaces.py`
- Test: `tests/solver/test_external_spaces.py`

- [ ] Required external logical IDs appear exactly once.
- [ ] Programmed area targets/tolerances respected.
- [ ] Protected/therapeutic external spaces respect privacy policy.
- [ ] Playground/child relations tested.
- [ ] No “leftover polygon = garden” shortcut.
- [ ] Commit.

---

### Task 13: Versioned scoring [P04-T13]

**Files:**
- Create: `src/amanda_agent/design/scoring.py`
- Create: `design-engine/config/weights.yaml`
- Test: `tests/solver/test_scoring.py`

Raw dimensions:
- program compliance;
- privacy/security;
- adjacency;
- circulation;
- accessibility;
- solar heuristic;
- ventilation heuristic;
- green integration;
- compactness;
- constructability;
- concept fidelity.

- [ ] Unknown score dimension is rejected.
- [ ] Give each metric unit, min/max direction, normalization bounds, missing-data rule and evidence source in the versioned configuration. Apply weights to normalized comparable values; never mix raw metres and percentages. Missing environmental inputs yield NOT_EVALUATED and exclude/rebalance that dimension transparently across the whole comparison. Weight changes alter total but never raw metrics.
- [ ] Store raw metrics and weighted total.
- [ ] Explicitly no aesthetics/beauty metric.
- [ ] Commit.

---

### Task 14: Pareto frontier [P04-T14]

**Files:**
- Create: `src/amanda_agent/design/pareto.py`
- Test: `tests/solver/test_pareto.py`

- [ ] Known dominated vector fixture.
- [ ] Deterministic non-dominated filtering.
- [ ] Preserve tradeoff alternatives even when weighted total lower.
- [ ] Commit.

---

### Task 15: Fast solar/ventilation heuristics [P04-T15]

**Files:**
- Create: `src/amanda_agent/design/environmental.py`
- Test: `tests/solver/test_environmental_heuristics.py`

- [ ] True-north-aware facade orientation.
- [ ] Apply source-backed Amanda orientation/wind findings as **project heuristics**, not universal truth.
- [ ] Label outputs `HEURISTIC`.
- [ ] Test expected relative score changes for east/west and wind exposure on synthetic case.
- [ ] Commit.

---

### Task 16: Deterministic generation [P04-T16]

**Files:**
- Create: `src/amanda_agent/design/generate.py`
- Test: `tests/solver/test_generation_reproducibility.py`

- [ ] Generate fixed set with run ID and seed list.
- [ ] Canonicalize JSON ordering/float rounding before hash.
- [ ] Set `num_search_workers = 1`, pinned OR-Tools/runtime, fixed seed, deterministic search budget and ordered inputs. Record OPTIMAL/FEASIBLE/INFEASIBLE/UNKNOWN separately; wall-clock timeout UNKNOWN is not proof of infeasibility. Same input/version/solver configuration produces the same geometry hash in the supported environment; exclude timestamps, paths, durations and run IDs from the semantic digest.
- [ ] On a fixture with multiple known feasible options, test diversity of the configured generator. Different seeds do not guarantee different optima; deduplicate geometry hashes and report actual candidate count.
- [ ] Store every seed with candidate.
- [ ] Commit.

---

### Task 17: Progressive pipeline [P04-T17]

**Files:**
- Create: `src/amanda_agent/design/pipeline.py`
- Test: `tests/solver/test_pipeline.py`

Default production intent:
- 120–240 macro candidates;
- hard filter;
- top ~15;
- room refinement;
- top ~5;
- detailed finalist stage;
- top 3.

- [ ] Counts are config values.
- [ ] Unit test uses smaller values.
- [ ] Every rejected candidate records exact hard rejection reason.
- [ ] No Revit call in pipeline.
- [ ] Commit.

---

### Task 18: Explainability [P04-T18]

**Files:**
- Create: `src/amanda_agent/design/explain.py`
- Test: `tests/solver/test_explain.py`

- [ ] Generate strengths from actual high raw metrics.
- [ ] Generate tradeoffs from actual penalties/relative comparisons.
- [ ] List hard violations (finalists must have none).
- [ ] Distinguish source principle vs design hypothesis.
- [ ] Produce `WHY_THIS_OPTION.md` from structured data; no unsupported prose claim.
- [ ] Commit.

---

### Task 19: Core regression fixtures [P04-T19]

**Directories:**
- `tests/regression/fixtures/simple-3-room/`
- `courtyard/`
- `two-access/`
- `privacy-gradient/`
- `accessible-route/`

For each fixture:
- [ ] input JSON;
- [ ] seed;
- [ ] expected invariants JSON;
- [ ] expected canonical hash when stable enough;
- [ ] regression test.

Commit fixtures.

---

### Task 20: Optional TopologicPy spike [P04-T20]

- [ ] Create isolated `.venv-topologic` so core solver cannot be broken.
- [ ] Install an exact evaluated TopologicPy version with its own dependency lock; record package availability before installation.
- [ ] Run minimal topology/graph operation.
- [ ] Record package/dependency versions, license, install conflicts, runtime value.
- [ ] Promote only if it adds a proven capability over NetworkX/Shapely.
- [ ] Otherwise keep capability UNTESTED or DEGRADED according to evidence and set scheduling decision `DEFERRED_OPTIONAL` outside CapabilityStatus; core engine remains GO.

---

### Task 21: Optional Ladybug/Honeybee finalist environment [P04-T21]

- [ ] Create isolated `.venv-environmental`.
- [ ] Install `ladybug-core` and `lbt-honeybee`.
- [ ] Verify imports/CLI.
- [ ] Verify EPW station/timezone/year/hash plus the actual Radiance/EnergyPlus executables and versions needed by the selected recipe. Package imports alone do not prove a simulation engine. Run one synthetic reproducible case and validate outputs.
- [ ] Label genuine solver output `SIMULATED` only after reproducible run.
- [ ] Failure does not block core heuristic engine.

---

### Task 22: CLI `design` and `compare` [P04-T22]

**Files:**
- Create: `src/amanda_agent/commands/design.py`
- Create: `src/amanda_agent/commands/compare.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_design_cli.py`

- [ ] `design --run-id RUN-001` reads canonical requirements/site and creates run directory.
- [ ] Reject mutable/invalid source state.
- [ ] `compare RUN-001` prints and saves finalist matrix.
- [ ] Source files remain unchanged; assert before/after hashes.
- [ ] Commit.

---

## Phase 04 Verification Gate

```powershell
.\.venv\Scripts\python.exe -m pytest tests/geometry tests/solver tests/regression -q
```

### GO
Core engine deterministic, hard constraints enforced, finalists explainable, no Revit dependency.

### GO_WITH_LIMITATIONS
Optional TopologicPy or detailed Ladybug/Honeybee unavailable while OR-Tools/Shapely/NetworkX core is green.

### NO_GO
Hard constraints can leak, requirements mutate, or same-seed reproducibility fails.
<a id="phase-05"></a>

# BIM Compiler and Revit Desired-State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for compiler/policy code; systematic debugging for provider/Revit failures; verification-before-completion before stage promotion.

**Goal:** Compile a solution explicitly marked `APPROVED_FOR_BIM` into staged Revit 2027 checkpoints using the verified Capability Registry, with desired-state diffs, stable logical IDs, unit safety, provenance, checkpoints, and rollback.

**Architecture:** The Python compiler produces a read-only `BIM_PLAN.json`. Codex executes the plan through actual MCP tools selected from the Capability Registry. The compiler never decides architecture inside Revit; it reconciles desired state against current managed state and requests the smallest safe mutation set.

**Tech Stack:** Python 3.12, Revit 2027, verified Horizun/RevitCortex MCP capabilities, custom C# fallback, Shapely, IfcOpenShell.

**Spec:** [design specification](2026-09-11-amanda-tfg-bim-agent-design.md)

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
<a id="phase-06"></a>

# QA, Persistence, Export, and GOLDEN Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for QA/release code; verification-before-completion is mandatory before RC/GOLDEN promotion.

**Goal:** Implement model/program/architecture/accessibility/documentation QA, warning baselines, export validation, cold persistence tests, release manifests, hashes, and immutable GOLDEN promotion.

**Architecture:** QA consumes Revit query evidence and exported files. It does not trust write responses. A release candidate must survive save→close→process exit→restart→reopen→critical QA. GOLDEN promotion is a one-way new-directory operation.

**Tech Stack:** Python 3.12, Pydantic, IfcOpenShell, local PDF parser/renderer, verified Revit query/export capabilities.

**Spec:** [design specification](2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- QA may block a build; it does not silently change requirements.
- Unknown warnings are never auto-ignored.
- GOLDEN is immutable.
- File existence is not sufficient export validation.
- IFC must parse.
- PDF page count/content preview must be checked.
- RC cannot promote without persistence evidence.

---

### Task 1: QA typed models [P06-T01]

**Files:**
- Create: `src/amanda_agent/qa/models.py`
- Test: `tests/unit/test_qa_models.py`

Severities: `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
Result: `PASS`, `PASS_WITH_WARNINGS`, `FAIL`, `BLOCKED_BY_INPUT`.

- [ ] Write serialization/aggregation tests.
- [ ] A CRITICAL issue or failed mandatory HIGH check forces overall FAIL; aggregation includes scope/mandatory flag. Missing mandatory checks block the relevant release profile, even when no defects are present.
- [ ] A missing-input issue cannot be converted to PASS.
- [ ] Commit.

---

### Task 2: Program reconciliation QA [P06-T02]

**Files:**
- Create: `src/amanda_agent/qa/program.py`
- Test: `tests/unit/test_program_qa.py`

- [ ] Missing required room → FAIL.
- [ ] Quantity mismatch → FAIL.
- [ ] Room area within configured range → PASS.
- [ ] Area outside soft tolerance but above hard minimum → warning according to config.
- [ ] Area below verified hard minimum → FAIL.
- [ ] External programmed-space quantities/areas reconciled too.
- [ ] Commit.

---

### Task 3: Model/geometric QA [P06-T03]

**Files:**
- Create: `src/amanda_agent/qa/model.py`
- Test: `tests/unit/test_model_qa.py`

- [ ] Duplicate managed logical IDs → CRITICAL.
- [ ] Hosted element without host → HIGH/CRITICAL.
- [ ] Managed room unplaced/not enclosed/redundant → HIGH.
- [ ] Managed element outside site when prohibited → HIGH.
- [ ] Level mismatch → severity by stage.
- [ ] Unexpected massive element-count delta → CRITICAL.
- [ ] Commit.

---

### Task 4: Warning baseline/delta [P06-T04]

**Files:**
- Create: `src/amanda_agent/qa/warnings.py`
- Create: `state/known-warnings.yaml`
- Test: `tests/unit/test_warning_delta.py`

- [ ] Baseline warning remains known, not “new”.
- [ ] New warning is emitted as delta.
- [ ] Known pattern severity map is versioned.
- [ ] Unknown warning defaults to reviewable severity, not ignore.
- [ ] Record warning ID/text/provider query evidence.
- [ ] Commit.

---

### Task 5: Architecture/concept QA [P06-T05]

**Files:**
- Create: `src/amanda_agent/qa/architecture.py`
- Test: `tests/unit/test_architecture_qa.py`

- [ ] Compare BIM logical adjacency graph to approved solution graph.
- [ ] Verify private residential zone has no unauthorized public-flow edge.
- [ ] Verify service-flow policy.
- [ ] Verify programmed therapeutic/protected garden relations.
- [ ] Verify shelter/transition/city sequence metrics did not collapse during BIM compile.
- [ ] Commit.

---

### Task 6: Accessibility QA status discipline [P06-T06]

**Files:**
- Create: `src/amanda_agent/qa/accessibility.py`
- Test: `tests/unit/test_accessibility_qa.py`

- [ ] Route-continuity checks use geometry/graph data.
- [ ] Numeric dimensional checks use only VERIFIED regulation rules.
- [ ] Missing rule/source → `BLOCKED_BY_INPUT` for that check.
- [ ] Report unsupported checks explicitly.
- [ ] Commit.

---

### Task 7: IFC validator [P06-T07]

**Files:**
- Create: `src/amanda_agent/qa/ifc.py`
- Test: `tests/unit/test_ifc_qa.py`

- [ ] Build or store a tiny valid IFC fixture.
- [ ] Parse via IfcOpenShell.
- [ ] Reject zero-byte/unparseable file.
- [ ] Count expected storeys/spaces/walls/doors on fixture.
- [ ] Production validator compares units, geospatial/project transforms, extents, storeys/spaces, openings and logical-ID mapping under the pinned export settings. Legitimate splits/merges need explicit mapping; counts alone cannot prove fidelity.
- [ ] Commit.

---

### Task 8: PDF validator [P06-T08]

**Files:**
- Create: `src/amanda_agent/qa/pdf.py`
- Test: `tests/unit/test_pdf_qa.py`

- [ ] Reject missing/zero-byte PDF.
- [ ] Verify expected minimum/exact page count from export manifest.
- [ ] Render every page to PNG with the locally validated PDF library/tool.
- [ ] Store previews in release `preview/pdf/`.
- [ ] Detect blank pages by raster variance threshold as a machine sanity signal; do not use this as sole visual quality test.
- [ ] Commit.

---

### Task 9: DWG sanity validator [P06-T09]

**Files:**
- Create: `src/amanda_agent/qa/dwg.py`
- Test: `tests/unit/test_dwg_qa.py`

- [ ] Verify path/nonzero size.
- [ ] If a compatible local DWG parser is already available/tested, inspect header/extents/layers.
- [ ] Otherwise verify export result, file signature/size and explicitly report `LIMITED_DWG_VALIDATION`; do not install AutoCAD solely for QA.
- [ ] Commit.

---

### Task 10: Persistence coordinator [P06-T10]

**Files:**
- Create: `src/amanda_agent/qa/persistence.py`
- Test: `tests/unit/test_persistence_plan.py`

Required sequence:
1. save RC;
2. wait for save completion;
3. close Revit normally and hash the closed stable file;
4. confirm process exits;
5. start Revit 2027 executable detected by Plan 01;
6. open RC;
7. reconnect preferred provider;
8. provider health;
9. critical model/program QA;
10. compare semantic state expectations; if an intentional later save changes file bytes, regenerate hashes/exports and revalidate before sealing.

- [ ] Test promotion object refuses incomplete sequence.
- [ ] Commit.

---

### Task 11: Release manifest [P06-T11]

**Files:**
- Create: `src/amanda_agent/release/manifest.py`
- Test: `tests/unit/test_release_manifest.py`

Fields include:
- project/release;
- timestamp;
- Revit product/file build;
- provider repo commits + installed hashes;
- Design Engine version/commit;
- selected solution ID/run/seed;
- requirements/site/regulation versions;
- QA summary;
- persistence summary;
- exports and hashes;
- release_profile STUDY or FINAL, required versus optional checks/artifacts, accepted limitations and approval evidence;
- content hashes for every artifact except the manifest itself (avoid recursive self-hash), and source-to-export identity/coordinate map.

- [ ] Deterministic sorted JSON serialization.
- [ ] Missing required artifact hash blocks GOLDEN.
- [ ] Commit.

---

### Task 12: GOLDEN promoter [P06-T12]

**Files:**
- Create: `src/amanda_agent/release/promote.py`
- Test: `tests/unit/test_release_promotion.py`

- [ ] QA FAIL and any unwaived mandatory blocked check prevent promotion. STUDY may explicitly retain missing survey/normative checks, with visible limitations; FINAL cannot waive them into compliance. Never infer acceptance from an empty issue list.
- [ ] Persistence incomplete blocks promotion.
- [ ] Mandatory export validation incomplete blocks promotion.
- [ ] Existing GOLDEN directory cannot be overwritten.
- [ ] Assemble the complete RVT/exports/previews/reports/provenance in a new staging directory; verify every hash and mandatory result, then publish with a no-overwrite atomic directory operation where supported (otherwise a tested completion marker protocol). Interrupted staging is never a GOLDEN. All reports exist before sealing; later corrections create a new release.
- [ ] Commit.

---

### Task 13: QA/export CLI [P06-T13]

**Files:**
- Create: `src/amanda_agent/commands/qa.py`
- Create: `src/amanda_agent/commands/export.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_release_cli.py`

Commands:
- `amanda-agent qa --model-manifest PATH`
- `amanda-agent export plan --release-id RC01`
- `amanda-agent export verify --release-id RC01`
- `amanda-agent release promote --release-id RC01`
- `amanda-agent release verify --release-id GOLDEN-001`

Create `src/amanda_agent/commands/release.py` and register its Typer group. `release verify` recomputes actual artifact hashes, required-file presence and manifest/QA/profile invariants; printing JSON is not validation.

- [ ] `qa` writes JSON + Markdown.
- [ ] export plan is read-only.
- [ ] promotion guard tested from CLI.
- [ ] Commit.

---

### Task 14: Synthetic R14→R16 release drill [P06-T14]

**Artifacts:** lab release directories.

- [ ] Use Plan 05 synthetic R13 model.
- [ ] Run full supported QA; create R14 report.
- [ ] Save to a new provisional RC path; certify R15 only after the cold-reopen verification below.
- [ ] Hash RC.
- [ ] Close Revit; verify exit.
- [ ] Restart cold; reopen RC; reconnect provider.
- [ ] Re-run critical QA.
- [ ] Export IFC; parse with IfcOpenShell.
- [ ] Export PDF; validate pages/previews.
- [ ] Export DWG; run supported validator.
- [ ] Generate manifest and artifact hashes.
- [ ] Complete required visual review (Task 15), reports and provenance in staging before promoting lab GOLDEN R16.
- [ ] Attempt to promote over same GOLDEN path and assert rejection.

---

### Task 15: Visual-documentation review protocol [P06-T15]

**Files:** `src/amanda_agent/qa/visual.py`, tests where deterministic.

- [ ] Collect sheet/page PNG previews.
- [ ] When current Codex environment supports image inspection, inspect for viewport overflow, crop errors, obvious tag/cota collisions, blank views, titleblock collisions.
- [ ] Store machine/vision findings as `VISUAL_REVIEW`, not normative proof.
- [ ] If Codex image inspection is unavailable, produce a human-review queue with exact preview files rather than claiming visual PASS.
- [ ] Commit.

---

## Phase 06 Verification Gate

### GO
Synthetic GOLDEN exists, is immutable, survived cold Revit restart, and has validated IFC/PDF plus supported DWG evidence.

### GO_WITH_LIMITATIONS
A declared STUDY profile may accept limited DWG-depth checks with evidence. Required sheet visual review and mandatory exports cannot be silently skipped; a pending review blocks that deliverable's final acceptance.

### NO_GO
RC can promote without persistence/QA, GOLDEN can be overwritten, or invalid exports are accepted.
<a id="phase-07"></a>

# Autonomous Operation, Recovery, Security, and Multi-Session Continuity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; systematic debugging for repeated failures; verification-before-completion before autonomy is considered safe.

**Goal:** Make the Codex workflow safe and resumable across long sessions, new chats, Revit crashes/hangs, Windows reboots, provider failures, and maintenance updates.

**Architecture:** Filesystem state + Git are authoritative; chat memory is not. Session protocols, task dependency graph, locks, budgets, recovery manager, secret redaction, trust scoring, maintenance isolation, and status summaries govern autonomous work.

**Tech Stack:** Python 3.12, Git, PowerShell, Windows process inspection, YAML/JSON.

**Spec:** [design specification](2026-09-11-amanda-tfg-bim-agent-design.md)

## Execution subsets

07A: Tasks 1–6, 10–13 and 16 after Plan 01, before provider installation. 07B: Tasks 7–9, 14–15 and 17–19 after synthetic release in Plan 06. Plan 01's minimal checkpoint/rollback protocol supports the earlier Tool Lab drill; these later tasks integrate and harden it. Tests use fixture contracts until a real dependency exists.

## Global Constraints

- One Revit production writer lease.
- No dependency/provider update during production phase.
- UAC/login/MFA are human boundaries.
- Technical fallbacks already authorized by registry do not need human approval.
- Never disable firewall/antivirus as a convenience.
- No cracked software.
- Secrets are never written to Git/logs/reports.

---

### Task 1: Production `AGENTS.md` [P07-T01]

**Files:**
- Create or merge without discarding existing instructions: `AGENTS.md`
- Test: `tests/policy/test_agents_policy.py`

Required rules must include, verbatim in substance:
1. preserve model integrity above completion;
2. never modify GOLDEN/source/master;
3. never use UNTESTED provider on production;
4. every BIM write gets independent read/verify;
5. never invent missing source data;
6. separate facts/constraints/hypotheses;
7. requirements immutable during optimization;
8. no mid-production dependency updates;
9. typed verified tools first;
10. only registry-approved fallbacks;
11. checkpoint before destructive work;
12. formal task status;
13. never claim success without evidence;
14. if uncertain, preserve last known-good state.

- [ ] Test required rules/plan paths exist in AGENTS.
- [ ] Add session-start/session-end instructions.
- [ ] Add Superpowers skill requirements.
- [ ] Commit.

---

### Task 2: Task dependency graph [P07-T02]

**Files:**
- Create: `src/amanda_agent/state/tasks.py`
- Create: `state/task-graph.yaml`
- Test: `tests/unit/test_task_graph.py`

- [ ] Represent task IDs, plan path, dependencies, phase, status.
- [ ] Downstream cannot become READY until all hard dependencies PASS/PASS_WITH_WARNINGS as allowed.
- [ ] `BLOCKED_BY_INPUT` propagates only to dependent branch.
- [ ] Parallel-ready tasks explicitly identified.
- [ ] Commit.

---

### Task 3: Session start protocol [P07-T03]

**Files:**
- Create: `src/amanda_agent/session/start.py`
- Test: `tests/unit/test_session_start.py`

Checks in order:
1. locate repo root;
2. read AGENTS;
3. load PROJECT_STATE;
4. load current child plan path;
5. inspect `git status`;
6. inspect environment lock;
7. inspect blockers;
8. inspect writer lock;
9. if BIM phase, verify Revit build + provider health;
10. resolve exact next READY task.

- [ ] Dirty source/config changes are reported before execution.
- [ ] Non-BIM phase does not require Revit running.
- [ ] Commit.

---

### Task 4: Session end protocol [P07-T04]

**Files:**
- Create: `src/amanda_agent/session/end.py`
- Test: `tests/unit/test_session_end.py`

- [ ] Cannot cleanly end with a task still RUNNING unless state changes to an explicit suspended/blocker state.
- [ ] Requires relevant test command/result recorded.
- [ ] Requires project-state update.
- [ ] Requires next task ID and incremental handoff including changes, evidence, tests, GitHub status, blockers and resume instructions; no reliance on chat memory.
- [ ] Requires checkpoint reference when BIM was mutated.
- [ ] Commit.

---

### Task 5: Retry/fallback/time budgets [P07-T05]

**Files:**
- Create: `src/amanda_agent/state/budgets.py`
- Test: `tests/unit/test_budgets.py`

Default policy:
- idempotent read retry budget: 3;
- mutating call retry budget: 2, but only after verifying no partial mutation;
- fallback budget: 3 providers/strategies;
- task soft/hard time limits are per-task config; hard timeout stops new dispatch and enters reconciliation, not automatic lock release or an overlapping fallback;
- equivalent repeated error signatures trigger `LOOP_DETECTED`.

- [ ] Test read budget exhaustion.
- [ ] Test mutation retry denied when partial-mutation flag true.
- [ ] Test repeated signature loop detection.
- [ ] Commit.

---

### Task 6: Blocker registry [P07-T06]

**Files:**
- Create: `src/amanda_agent/state/blockers.py`
- Test: `tests/unit/test_blockers.py`

Blocker fields:
- ID;
- severity;
- source/evidence;
- tasks blocked;
- tasks still allowed;
- resolution action;
- created/resolved timestamps.

- [ ] Missing site topography blocks final grading but permits schematic macrozoning.
- [ ] Missing APS authorization blocks cloud; missing/expired Revit licensing blocks local Revit as well. CPU-only ingestion/solver work remains possible.
- [ ] Commit.

---

### Task 7: Recovery manager [P07-T07]

**Files:**
- Create: `src/amanda_agent/recovery/manager.py`
- Test: `tests/unit/test_recovery_manager.py`

- [ ] CRASHED state selects last hash-verified PASS checkpoint.
- [ ] Interrupted mutation is never retried blindly.
- [ ] Recovery plan contains reopen, provider reconnect, healthcheck, current-state re-query, then decision retry/fallback.
- [ ] A corrupted checkpoint is skipped for earlier verified one.
- [ ] Commit.

---

### Task 8: Revit watchdog [P07-T08]

**Files:**
- Create: `src/amanda_agent/recovery/watchdog.py`
- Test: `tests/unit/test_watchdog.py`

States: `HEALTHY`, `BUSY`, `SUSPECTED_HANG`, `HUNG`, `CRASHED`.

Inputs:
- process existence/PID;
- elapsed operation time;
- last MCP heartbeat/result;
- CPU/process responsiveness where obtainable;
- current task timeout.

- [ ] Timeout alone must not immediately imply HUNG.
- [ ] HUNG requires multiple corroborating signals/grace period.
- [ ] Force kill is last action after normal-close attempt and verified prior checkpoint/state persistence; require owned PID/start time and disposable/authorized documents. Do not attempt a new checkpoint from a hung process or kill unknown user work.
- [ ] Commit.

---

### Task 9: Reboot-resume file [P07-T09]

**Files:**
- Create: `src/amanda_agent/recovery/reboot.py`
- Test: `tests/unit/test_reboot_resume.py`

Generate `RESUME_AFTER_REBOOT.md` with:
- phase;
- current/last PASS task;
- reason for reboot;
- last checkpoint/hash;
- expected Revit/provider state;
- first verification commands;
- next task.

- [ ] Redact secrets.
- [ ] Test deterministic content.
- [ ] Commit.

---

### Task 10: Security redaction [P07-T10]

**Files:**
- Create: `src/amanda_agent/security/redaction.py`
- Test: `tests/unit/test_redaction.py`

- [ ] Redact bearer tokens, API keys, client secrets, passwords, authorization headers, private-key blocks.
- [ ] Preserve error type/host/status code/diagnostic nonsecret text.
- [ ] All logger/reporter paths call redactor before persistence.
- [ ] Commit.

---

### Task 11: Tool trust scoring [P07-T11]

**Files:**
- Create: `src/amanda_agent/tools/trust.py`
- Test: `tests/unit/test_tool_trust.py`

Evidence dimensions:
- maintainer/source reputation;
- recency/maintenance;
- license;
- Revit/Codex compatibility;
- tests/CI;
- issue quality;
- release provenance/signing/hashes;
- security docs;
- API/write scope.

- [ ] Unknown license prevents automatic promotion.
- [ ] Unsigned Windows binary is not automatically rejected if source-build path/provenance is available, but risk is recorded.
- [ ] Official-but-sample code is labeled sample risk, not treated as production by default.
- [ ] Commit.

---

### Task 12: Tool-discovery report [P07-T12]

**Files:**
- Create: `src/amanda_agent/tools/discovery.py`
- Test: `tests/unit/test_tool_discovery.py`

Required report fields:
- repository URL;
- commit/tag;
- license;
- build method;
- install effects;
- network behavior;
- Revit support;
- MCP/Codex support;
- rollback;
- risk score;
- exact capability being sought.

- [ ] No discovery candidate can install directly to production; it must go through Tool Lab.
- [ ] Commit.

---

### Task 13: Maintenance/update guard [P07-T13]

**Files:**
- Create: `src/amanda_agent/maintenance/policy.py`
- Test: `tests/unit/test_maintenance_policy.py`

- [ ] Block Revit/provider/critical dependency updates when phase is production build, QA, RC, or release.
- [ ] Allow updates only in maintenance/experiment branch/worktree.
- [ ] Provider/Revit update requires full provider + synthetic E2E regression.
- [ ] Commit.

---

### Task 14: Status dashboard [P07-T14]

**Files:**
- Create: `src/amanda_agent/status_dashboard.py`
- Modify: status command.
- Test: `tests/unit/test_status_dashboard.py`

`state/status.md` includes:
- phase/task progress;
- Revit build;
- provider health;
- PASS/FAIL/UNTESTED capability counts;
- blocker summary;
- selected design;
- Revit stage;
- current checkpoint;
- writer lease;
- last verified Git commit.

- [ ] Generate markdown from machine state.
- [ ] Commit.

---

### Task 15: Run summary [P07-T15]

**Files:**
- Create: `src/amanda_agent/session/summary.py`
- Test: `tests/unit/test_run_summary.py`

- [ ] Summarize attempted/changed/passed/failed/rolled-back/next.
- [ ] Link raw logs/evidence paths instead of pasting huge payloads.
- [ ] Include provider/fallback usage.
- [ ] Commit.

---

### Task 16: Human-intervention state machine [P07-T16]

**Files:**
- Create: `src/amanda_agent/state/human_gate.py`
- Test: `tests/unit/test_human_gate.py`

Human gate reasons (respect previously granted authorization; never use this enum to override platform/user limits):
- `UAC_APPROVAL`;
- `AUTHENTICATION_OR_MFA`;
- `LICENSE_VALIDATION`;
- `ESSENTIAL_SOURCE_DATA` only for affected work after research and provisional-study alternatives are exhausted;
- `ARCHITECTURAL_SELECTION` only if the user later revokes delegation or explicitly requests a pause; currently disabled as a waiting gate;
- `IRREVERSIBLE_EXTERNAL_ACTION`;
- `EXTERNAL_DATA_OR_COST`;
- `PLATFORM_PERMISSION`;
- `USER_WORK_AT_RISK`;
- `PROGRAM_BASELINE` only for a requested material change to the already selected 20-person brief.

- [ ] Routine architectural choices, finalist selection, researched typology/materials and provisional STUDY assumptions must not emit a human gate under AGENT_DELEGATED. Routine package installation/provider fallback uses existing authorization and platform permissions.
- [ ] Commit.

---

### Task 17: Fresh-session recovery drill [P07-T17]

**Artifact:** `docs/reports/session-recovery-drill.md`.

- [ ] Complete and commit a test task.
- [ ] Persist project state with exact next task.
- [ ] Persist handoff and end the current session; a subsequent session performs the next steps. Closure of the current agent cannot be simulated by code that then claims to continue after restart.
- [ ] Start a new Codex session in repo.
- [ ] It must read AGENTS/state/current plan/git and identify exact next READY task without user re-explaining history.
- [ ] Record PASS/FAIL.

---

### Task 18: Provider-update isolation drill [P07-T18]

- [ ] Create isolated experiment worktree/branch.
- [ ] A Git worktree isolates source only: it does not isolate `%APPDATA%` add-ins, Codex config, ports, installed DLLs or Revit processes. Use a separate sandbox/deployment root or a backed-up maintenance window and one process owner for a real install. Otherwise change only fixtures/mocks in the worktree.
- [ ] Run Tool Lab regression.
- [ ] Deliberately leave an experiment failing.
- [ ] Verify `main` provider pins and production checkpoints unchanged.
- [ ] Remove experiment worktree safely after report.

---

### Task 19: Full reboot simulation/procedure [P07-T19]

Without rebooting unnecessarily, validate the procedure:

- [ ] Generate `RESUME_AFTER_REBOOT.md`.
- [ ] Persist/commit state.
- [ ] Persist handoff before closing owned Revit/Codex normally; following steps run in a new session with separate evidence.
- [ ] Start new shell/Codex session as if after reboot.
- [ ] Run doctor/status/provider health.
- [ ] Resume next task.
- [ ] If an actual provider install later requires reboot, use the same verified procedure.

---

## Phase 07 Verification Gate

### GO
Fresh-session resume, writer lease, blocker propagation, budgets, secret redaction, recovery planning, update guards, and human-gate boundaries pass.

### NO_GO
Continuity relies on chat memory, two writers can own production, secrets enter logs, or recovery can overwrite protected files.
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

<a id="phase-09"></a>

# Optional Rendering and Cloud Fallback Extensions Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; Tool Lab validation remains mandatory for optional providers.

**Goal:** Add optional Blender rendering and Autodesk APS/Revit Automation fallback **without** making either a hidden dependency of the local production pipeline.

**Architecture:** Blender consumes a verified release/export; it never edits the authoritative Revit GOLDEN. APS is registered only for a concrete blocked local capability, uses separate credentials, and stays below verified local providers in routing priority.

**Tech Stack:** Blender MCP/uvx, Blender, Autodesk APS Automation API samples, Codex MCP, existing local pipeline.

**Spec:** [design specification](2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- Rendering consumes a verified export/release. APS need/audit/synthetic testing may follow 07A when a concrete local blocker prevents reaching GOLDEN; use the explicit exception in the master dependency contract.
- Cloud remains fallback-only.
- Optional provider failure cannot invalidate a valid local GOLDEN.
- No credentials in Git/logs.
- Every optional MCP gets a Tool Lab and capability entry.

---

### Task 1: Determine immediate rendering need [P09-T01]

- [ ] Read current Amanda deliverable requirements.
- [ ] If no render is required, set Blender scheduling decision `DEFERRED_OPTIONAL` and leave untested capability `UNTESTED` and do not install just for novelty.
- [ ] If renders are required, proceed.

---

### Task 2: Install/verify `uv` for Blender MCP [P09-T02]

Current upstream Blender MCP documentation uses `uvx`.

- [ ] Check:

```powershell
uv --version
uvx --version
```

- [ ] If absent, use current official Astral Windows installer documented by Blender MCP:

```powershell
# Download the official installer to a local file, inspect it and record its hash.
# Run the inspected file under the audited install scope; record version and rollback.
```

- [ ] Start a fresh shell and verify versions.
- [ ] Record versions in environment lock.

---

### Task 3: Register Blender MCP [P09-T03]

- [ ] Register:

```powershell
# Resolve UvxExe to the verified absolute executable path.
# Resolve BlenderPackage to blender-mcp==<the exact evaluated version> from the lock.
codex mcp add blender -- $UvxExe --from $BlenderPackage blender-mcp
codex mcp list
```

- [ ] Install addon:

```powershell
& $UvxExe --from $BlenderPackage blender-mcp install-addon
```

- [ ] Open Blender, enable installed MCP addon according to current upstream instructions.
- [ ] Do not load Amanda model yet.

---

### Task 4: Blender Tool Lab [P09-T04]

**Files:** `state/providers/blender-toolmap.yaml`, `tool-lab/blender/`.

- [ ] Inspect `/mcp` and record actual current tool names.
- [ ] Test read-only scene query on empty scene.
- [ ] Test creating exactly one cube in disposable `.blend`.
- [ ] Re-query object existence/properties.
- [ ] Save/close/reopen `.blend` and re-query.
- [ ] Test import/export format actually intended for Revit handoff.
- [ ] Read current upstream open issues for Codex schema/compatibility before promoting.
- [ ] Record PASS/DEGRADED/FAIL.

---

### Task 5: Rendering pipeline from verified BIM release [P09-T05]

- [ ] Choose export format based on validated Revit→Blender fidelity test (for example FBX/IFC/GLB if actually supported in the verified chain).
- [ ] Export from a **copy** of the validated release.
- [ ] Import to new Blender project whose metadata records source GOLDEN SHA256.
- [ ] Create controlled material translation map.
- [ ] Add lighting/environment.
- [ ] Add vegetation only from controlled assets/placeholders.
- [ ] Create named cameras.
- [ ] Render low-resolution previews first.
- [ ] Review previews.
- [ ] Render final resolution only after preview PASS.
- [ ] Keep renders under `deliverables/renders/<golden-release-id>/`.

---

### Task 6: APS need gate [P09-T06]

- [ ] Confirm a **specific required** local capability is `BLOCKED_BY_TOOL` after verified typed/custom/interchange fallbacks.
- [ ] If no concrete blocked capability exists, set APS scheduling decision `DEFERRED_OPTIONAL` (capability remains UNTESTED) and stop APS work.
- [ ] If one exists, write `tool-lab/aps/need-report.md` explaining exact capability and why local alternatives failed.

---

### Task 7: Audit official APS sample repos [P09-T07]

Current reference repos:
- `autodesk-platform-services/aps-sample-mcp-server-revit-automation`
- `autodesk-platform-services/aps-sample-revit-mcp-tools-bundle`

- [ ] Clone in experiment worktree only.
- [ ] Pin commits.
- [ ] Read README/source/config files.
- [ ] Record that the AppBundle sample currently describes itself as sample/proof-of-concept; do not treat it as hardened production middleware automatically.
- [ ] Audit credential locations, network/data flow, activity/AppBundle configuration, rollback; verify the available APS engine version can read the target RVT before any cloud test.
- [ ] Run tool trust score.

---

### Task 8: APS secret boundary [P09-T08]

If APS remains justified:

- [ ] Create `.env.example` with **names only**, e.g. APS client ID variables.
- [ ] Store actual credentials in Windows Credential Manager or another approved local secret mechanism.
- [ ] Test redaction against APS logs.
- [ ] User handles Autodesk login/app authorization/MFA when prompted.
- [ ] Record user authorization for intended model/data upload, destination and cost limit unless already granted in this session. Use synthetic data for sandbox tests; never upload unrelated source files.

---

### Task 9: APS sandbox deployment/test [P09-T09]

- [ ] Build current official sample projects locally.
- [ ] Deploy only to a dedicated test APS app/project/activity.
- [ ] Use synthetic/disposable Revit cloud model/input.
- [ ] Run a harmless query or tiny model mutation.
- [ ] Verify output file/state independently.
- [ ] Record latency/cost/data-residency implications.
- [ ] Register APS capability only for the exact tested semantic operation.

---

### Task 10: Preserve local-first routing [P09-T10]

- [ ] `state/capabilities.yaml` keeps verified local providers at higher priority.
- [ ] APS entry has lower priority than every verified local path for same capability.
- [ ] Disable optional APS MCP when not actively needed if practical.
- [ ] Re-run doctor and regression after registration.
- [ ] Commit only nonsecret manifests/audits.

---

## Phase 09 Verification Gate

### GO
Optional capability works and remains isolated/nonmandatory.

### GO_WITH_LIMITATIONS
Optional provider unavailable; local GOLDEN pipeline unaffected.

### NO_GO
Optional integration becomes an unverified mandatory dependency, leaks secrets, or changes routing ahead of verified local providers.
