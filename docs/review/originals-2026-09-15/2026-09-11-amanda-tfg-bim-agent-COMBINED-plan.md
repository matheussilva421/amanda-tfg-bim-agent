# Amanda TFG BIM Agent — Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Use `superpowers:using-git-worktrees` at execution time when starting from an existing repository. Use TDD for code, systematic debugging for failures, and verification-before-completion before claiming any task/phase is complete.

**Goal:** Build a local-first, fault-tolerant Codex-controlled architecture/BIM pipeline that ingests Amanda's TFG sources, proves Revit integrations on this PC, generates architectural alternatives, compiles an approved alternative into Autodesk Revit 2027, validates it, and emits an immutable GOLDEN release.

**Architecture:** One orchestration plan plus independent child plans. Every child plan produces testable software/evidence and ends in a `GO`, `GO_WITH_LIMITATIONS`, or `NO_GO` gate. Revit production writes are forbidden until the Tool Lab has generated a verified Capability Registry.

**Tech Stack:** Windows, Autodesk Revit 2027 Education, Codex CLI, Git, PowerShell, Python 3.12 x64, pytest, Pydantic, Typer, OR-Tools, Shapely, NetworkX, IfcOpenShell; optional TopologicPy/Ladybug/Honeybee; .NET 10; Horizun Revit MCP; RevitCortex; optional Blender MCP and Autodesk APS fallback.

**Spec:** `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`

## Global Constraints

- Detect the exact installed Revit 2027 build; never assume it.
- Local-first. APS/cloud is last-resort fallback only.
- Maximum local autonomy; stop only for UAC, authentication/licensing, essential missing source data, final architectural selection, or irreversible external action.
- One active writer per RVT.
- Never write to files whose path identifies them as `GOLDEN`, `MASTER`, or source originals.
- Every BIM write follows `WRITE → READ → VERIFY`.
- A tool-returned success flag is not evidence of actual model mutation.
- No `UNTESTED` provider may touch Amanda production.
- Source facts, derived constraints, and design hypotheses are separate data classes.
- Requirements are immutable during optimization.
- Missing topography remains missing; do not fabricate elevations/declivities.
- Dependency/provider/Revit updates occur only in maintenance branches and require regression before promotion.
- Every task ends in `PASS`, `PASS_WITH_WARNINGS`, `DEGRADED`, `BLOCKED_BY_INPUT`, `BLOCKED_BY_TOOL`, `FAILED_ROLLED_BACK`, or `CRITICAL_FAILURE`.

## Current upstream contracts to re-check before installation

At execution time, Codex must re-open these upstream sources, record their current commit/release, then pin the exact commit used:

- Horizun Revit MCP: `https://github.com/HorizunGroup/horizun-revit-mcp`
  - Current source-build docs support Revit 2023–2027.
  - Current `AGENTS.md` requires exact .NET SDK `10.0.400` for the source build.
  - Current source install command: `powershell -ExecutionPolicy Bypass -File .\install.ps1`.
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

## Plan Map

```text
00 MASTER
   |
   v
01 FOUNDATION / ENVIRONMENT / STATE
   |
   v
02 REVIT TOOL LAB / PROVIDERS
   |\
   | \
   v  v
03 PROJECT INTELLIGENCE        07 AUTONOMY / RECOVERY / SECURITY
   |                               |
   v                               |
04 DESIGN ENGINE                   |
   |                               |
   v                               |
05 BIM COMPILER <------------------+
   |
   v
06 QA / RELEASE / EXPORTS
   |
   v
08 AMANDA PRODUCTION RUN
   |
   v
09 OPTIONAL RENDER / CLOUD
```

## Child Plans

1. `01-foundation-environment-state.md`
2. `02-revit-tool-lab-providers.md`
3. `03-project-intelligence.md`
4. `04-design-engine.md`
5. `05-bim-compiler.md`
6. `06-qa-release-exports.md`
7. `07-autonomy-recovery-security.md`
8. `08-amanda-production-run.md`
9. `09-optional-render-cloud.md`

---

### Task M1: Initialize repository from the approved bundle

**Files:**
- Create: `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`
- Create: `docs/superpowers/plans/*.md`
- Create: `.gitignore`

**Interfaces:**
- Consumes: this bundle.
- Produces: the canonical Git repository.

- [ ] **Step 1: Create repository root**

```powershell
$RepoRoot = Join-Path (Get-Location) "amanda-tfg-bim-agent"
New-Item -ItemType Directory -Force -Path $RepoRoot | Out-Null
Set-Location $RepoRoot
git init
```

Expected: empty Git repository.

- [ ] **Step 2: Create documentation directories**

```powershell
New-Item -ItemType Directory -Force -Path "docs/superpowers/specs","docs/superpowers/plans" | Out-Null
```

- [ ] **Step 3: Copy the approved design spec and plan files from the supplied bundle**

After copying, verify:

```powershell
Get-ChildItem docs/superpowers/specs
Get-ChildItem docs/superpowers/plans
```

Expected: exactly one approved design spec plus master and nine child plans.

- [ ] **Step 4: Create `.gitignore`**

```gitignore
.venv/
.venv-*/
.tools/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
.env.*
!.env.example
logs/raw/
revit/lab/**/*.rvt
revit/production/working/*.rvt
bim/checkpoints/*.rvt
bim/releases/**/*.rvt
*.0001.rvt
*.0002.rvt
*.0003.rvt
*.slog
```

- [ ] **Step 5: Commit baseline**

```powershell
git add docs .gitignore
git commit -m "docs: add approved Amanda BIM design and implementation plans"
```

Expected: clean `git status`.

---

### Task M2: Enforce plan dependency order

**Files:**
- Modify later: `PROJECT_STATE.yaml`

**Interfaces:**
- Consumes: child phase gates.
- Produces: controlled phase advancement.

- [ ] Execute Plan 01. If `NO_GO`, stop.
- [ ] Execute Plan 02. If core Revit capabilities are not green, stop production work.
- [ ] Execute Plan 03 and Plan 07 after Plan 02; parallelize only independent files/tasks.
- [ ] Execute Plan 04 after canonical requirements/site schemas are stable.
- [ ] Execute Plan 05 only after at least one typed Revit provider plus a verified core fallback are in the Capability Registry.
- [ ] Execute Plan 06 and require cold save/close/restart/reopen verification.
- [ ] Execute Plan 08 only after all synthetic regression fixtures pass.
- [ ] Execute Plan 09 only after a local synthetic and/or Amanda GOLDEN path is stable.

---

### Task M3: Global completion verification

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
Get-Content bim/releases/GOLDEN-001/manifest.json | ConvertFrom-Json | Format-List
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
3. read only the child plan for the current phase plus interfaces it consumes;
4. create/use an isolated worktree as Superpowers requires;
5. use TDD for each code task;
6. record evidence for each Revit tool task;
7. commit after every independently testable task;
8. update `PROJECT_STATE.yaml` after task completion;
9. never skip a phase gate because a downstream component “probably works”.
# Foundation, Environment, Persistent State, and CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`. Use TDD for code, systematic debugging for failures, verification-before-completion before phase PASS.

**Goal:** Create the Python control plane, detect the real Windows/Revit/Codex/.NET environment, snapshot configurations, establish durable project state, single-writer locking, logs, and `doctor/status/resume/rollback` commands.

**Architecture:** A Python 3.12 package owns project state and deterministic policy. Environment probes are isolated so they can be unit tested. Bootstrap never edits Amanda RVTs.

**Tech Stack:** Python 3.12 x64, Typer, Pydantic v2, PyYAML, Rich, pytest, PowerShell, Git.

**Spec:** `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`

## Global Constraints

- Revit is already installed; do not reinstall it.
- Detect Revit by installed files/metadata.
- Plan 02 source-build of Horizun requires exact .NET SDK 10.0.400.
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

### Task 1: Bootstrap Python package and CLI

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

- [ ] **Step 3: Create minimal CLI**

```python
# src/amanda_agent/cli.py
import typer

app = typer.Typer(no_args_is_help=True)

@app.command()
def doctor() -> None:
    typer.echo("doctor: bootstrap implementation pending")

@app.command()
def status() -> None:
    typer.echo("status: bootstrap implementation pending")

@app.command()
def resume() -> None:
    typer.echo("resume: bootstrap implementation pending")

@app.command()
def rollback() -> None:
    typer.echo("rollback: bootstrap implementation pending")
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

- [ ] **Step 6: Verify test RED→GREEN**

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

### Task 2: Canonical paths

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

### Task 3: Project-state models

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
    next_task: str = "ENV-001"
    selected_design: str | None = None
    revit_stage: str = "R00"
    current_checkpoint: str | None = None
    blockers: list[str] = Field(default_factory=list)
    last_verified_commit: str | None = None
```

- [ ] Test JSON/YAML-safe model dump.
- [ ] Commit.

---

### Task 4: Atomic YAML state store

**Files:**
- Create: `src/amanda_agent/state/store.py`
- Test: `tests/unit/test_state_store.py`

**Interfaces:** `StateStore.load`, `StateStore.save`.

- [ ] Write round-trip test and assert no `.tmp` remains.
- [ ] Implement atomic replace:

```python
from pathlib import Path
import os, yaml
from amanda_agent.models.state import ProjectState

class StateStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> ProjectState:
        return ProjectState.model_validate(yaml.safe_load(self.path.read_text(encoding="utf-8")))

    def save(self, state: ProjectState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(yaml.safe_dump(state.model_dump(mode="json"), sort_keys=False), encoding="utf-8")
        os.replace(temp, self.path)
```

- [ ] Run tests.
- [ ] Commit.

---

### Task 5: Single-writer lock

**Files:**
- Create: `src/amanda_agent/state/locks.py`
- Test: `tests/unit/test_writer_lock.py`

**Interfaces:** `WriterLock.acquire(owner)`, `release`, `inspect`.

- [ ] Test two writers cannot acquire same lease.
- [ ] Implement exclusive file creation with owner/PID/host/timestamp JSON.
- [ ] Test release and stale lock inspection.
- [ ] Commit.

---

### Task 6: Detect actual Revit 2027 installation

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
- [ ] Gate `NO_GO` if no Revit 2027 install is returned.
- [ ] Store exact build in environment report.
- [ ] Commit.

---

### Task 7: Probe Codex/Git/PowerShell/Python/.NET

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

- [ ] Ensure exact SDK `10.0.400` exists for Horizun source build.
- [ ] If WinGet lists exact 10.0.400:

```powershell
winget show Microsoft.DotNet.SDK.10 --versions
winget install -e --id Microsoft.DotNet.SDK.10 --version 10.0.400 --accept-package-agreements --accept-source-agreements
```

- [ ] If WinGet does not list it, install project-local from Microsoft's official install script:

```powershell
New-Item -ItemType Directory -Force ".tools\dotnet" | Out-Null
Invoke-WebRequest https://dot.net/v1/dotnet-install.ps1 -OutFile ".tools\dotnet-install.ps1"
powershell -ExecutionPolicy Bypass -File ".tools\dotnet-install.ps1" -Version 10.0.400 -InstallDir ".tools\dotnet"
& ".\.tools\dotnet\dotnet.exe" --version
```

Expected: `10.0.400`.

- [ ] Commit code, not local SDK binaries.

---

### Task 8: Snapshot Codex config and Revit add-in inventory

**Files:**
- Create: `src/amanda_agent/bootstrap/snapshots.py`
- Test: `tests/unit/test_snapshots.py`

- [ ] Write redaction test for keys containing TOKEN/SECRET/PASSWORD/API_KEY/AUTHORIZATION.
- [ ] Implement redaction.
- [ ] Snapshot current config before provider installation:

```powershell
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Dest = "state\snapshots\$Stamp"
New-Item -ItemType Directory -Force $Dest | Out-Null
if (Test-Path "$env:USERPROFILE\.codex\config.toml") {
  Copy-Item "$env:USERPROFILE\.codex\config.toml" "$Dest\codex-config.toml"
}
Get-ChildItem "C:\ProgramData\Autodesk\Revit\Addins\2027" -Recurse -ErrorAction SilentlyContinue |
  Select-Object FullName,Length,LastWriteTime |
  ConvertTo-Json -Depth 5 |
  Set-Content "$Dest\revit-addins-2027.json"
```

- [ ] Redact copied text before any Git staging.
- [ ] Commit only code/metadata safe for Git.

---

### Task 9: Structured JSONL logger

**Files:**
- Create: `src/amanda_agent/logging.py`
- Test: `tests/unit/test_logging.py`

- [ ] Test one record has timestamp/task/operation/provider/status.
- [ ] Implement append-only JSONL writer.
- [ ] Ensure redaction occurs before raw exception payloads are persisted.
- [ ] Commit.

---

### Task 10: `doctor`

**Files:**
- Create: `src/amanda_agent/commands/doctor.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_doctor.py`

**Interfaces:** writes `state/environment-report.json`, returns nonzero on critical failure.

- [ ] Test missing Revit 2027 is critical.
- [ ] Test missing .NET 10.0.400 is critical before Plan 02.
- [ ] Test missing Codex is critical.
- [ ] Wire probes into report.
- [ ] Run `python -m amanda_agent doctor` on live PC.
- [ ] Commit.

---

### Task 11: `status`, `resume`, `rollback`

**Files:**
- Create command modules and tests.

- [ ] `status` is read-only and prints phase, next task, blocker count, writer lease, Revit stage.
- [ ] `resume` refuses when a blocker starts with `BLOCKING:`.
- [ ] `rollback` validates source checkpoint hash and copies it to a **new** working filename.
- [ ] `rollback` rejects target filenames containing `golden`, `master`, `source` case-insensitively.
- [ ] Test all four conditions.
- [ ] Commit.

---

### Task 12: Initialize durable state files

**Files:**
- Create: `PROJECT_STATE.yaml`
- Create: `state/bim-environment.lock.yaml`
- Create: `state/blockers.yaml`
- Create: `state/tool-health.yaml`

- [ ] Serialize default `ProjectState` with the real code.
- [ ] Record actual Revit build, Python, Codex, Git, PowerShell, .NET SDKs.
- [ ] Initialize topography as `UNKNOWN_UNTIL_INGEST`, not as a numeric value.
- [ ] Commit state baselines.

---

---

### Task 13: Add the idempotent `bootstrap` command

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
- exact Revit 2027 build recorded;
- Codex detected;
- .NET 10.0.400 available;
- snapshots created;
- state files valid;
- no stale writer lease;
- Git clean.

### NO_GO
Any critical item above fails. Plan 02 must not begin.
# Revit Tool Lab, Provider Validation, and Capability Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`. Use TDD for registry/policy code, systematic debugging for every provider failure, and verification-before-completion before promoting any capability.

**Goal:** Install Horizun and RevitCortex from pinned source, prove their capabilities against the actual Revit 2027 build in disposable models, prove a custom Revit API fallback, inject failures, and build the deterministic Capability Registry used by production.

**Architecture:** Nothing in this plan touches Amanda production. Every provider gets its own disposable RVT copies. Codex discovers the **actual** MCP tool catalog after installation and records a semantic toolmap; no tool names are invented from documentation. Promotion requires independent model re-query and save/reopen persistence.

**Tech Stack:** Revit 2027, .NET 10, Horizun Revit MCP, RevitCortex, Codex MCP, C#, Python/Pydantic/pytest.

**Spec:** `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`

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

### Task 1: Capability registry models

**Files:**
- Create: `src/amanda_agent/models/capability.py`
- Create: `src/amanda_agent/tools/registry.py`
- Test: `tests/unit/test_capability_registry.py`

**Interfaces:** `CapabilityRegistry.record`, `CapabilityRegistry.preferred`.

- [ ] **Step 1: Write failing selection test**

```python
from pathlib import Path
from amanda_agent.models.capability import CapabilityStatus, ProviderCapability
from amanda_agent.tools.registry import CapabilityRegistry

def test_registry_never_selects_failed_provider(tmp_path: Path):
    registry = CapabilityRegistry(tmp_path / "capabilities.yaml")
    registry.record("create_wall", ProviderCapability(provider="horizun", status=CapabilityStatus.FAIL, priority=10))
    registry.record("create_wall", ProviderCapability(provider="revitcortex", status=CapabilityStatus.PASS, priority=20))
    assert registry.preferred("create_wall").provider == "revitcortex"
```

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
    revit_build: str | None = None
    save_reopen: bool = False
    warnings_delta: int = 0
    evidence: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
```

- [ ] **Step 3: Selection rules**
  1. select only `PASS` or `PASS_WITH_WARNINGS`;
  2. prefer `PASS`;
  3. lowest numeric priority wins;
  4. provider name is deterministic tie-breaker.

- [ ] **Step 4: Persist YAML atomically and test round-trip**
- [ ] **Step 5: Run test and commit**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_capability_registry.py -v
git add src/amanda_agent/models/capability.py src/amanda_agent/tools tests/unit/test_capability_registry.py
git commit -m "feat: add deterministic capability registry"
```

---

### Task 2: Circuit breaker

**Files:**
- Create: `src/amanda_agent/tools/circuit_breaker.py`
- Test: `tests/unit/test_circuit_breaker.py`

- [ ] Test three consecutive equivalent failures open breaker.
- [ ] Implement states `CLOSED`, `OPEN`, `HALF_OPEN`.
- [ ] Success resets failure counter.
- [ ] An OPEN breaker prevents further same-provider calls for the capability in the current session.
- [ ] Commit.

---

### Task 3: Evidence record model

**Files:**
- Create: `src/amanda_agent/tools/evidence.py`
- Test: `tests/unit/test_evidence.py`

**Interfaces:** each capability test stores provider, tool, input fixture, raw output path, model-query evidence, warning delta, duration, save/reopen result, artifact hashes.

- [ ] Write validation test requiring model-query evidence for write PASS.
- [ ] Implement model.
- [ ] Test that `success=true` without independent evidence cannot serialize as capability PASS.
- [ ] Commit.

---

### Task 4: Clone/audit/pin/build/install Horizun from source

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

- [ ] **Step 4: Verify exact .NET SDK**

```powershell
dotnet --list-sdks
```

Expected: `10.0.400` available. If project-local, prepend `.tools\dotnet` to PATH for this build.

- [ ] **Step 5: Run upstream source installer**

```powershell
Push-Location vendor/horizun-revit-mcp
powershell -ExecutionPolicy Bypass -File .\install.ps1
Pop-Location
```

Expected: detects Revit 2027; builds matching add-in and MCP server; verifies installed binaries.

- [ ] **Step 6: Find installed MCP executable and hash it**

```powershell
$HorizunExe = Get-ChildItem "$env:LOCALAPPDATA\Programs\Horizun\MCP" -Recurse -Filter horizun-mcp.exe -ErrorAction Stop |
  Select-Object -First 1 -ExpandProperty FullName
$HorizunExe
Get-FileHash $HorizunExe -Algorithm SHA256
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

Snapshot `$env:USERPROFILE\.codex\config.toml` first. Ensure the `horizun-revit` table has `startup_timeout_sec = 120` and `tool_timeout_sec = 600`, preserving every other server.

- [ ] **Step 9: Write install manifest**

Record source URL, commit, installed exe path, SHA256, Revit build, SDK version, config snapshot path, rollback procedure.

- [ ] **Step 10: Commit audit/manifests**

```powershell
git add tool-lab/horizun/source-audit.md state/install-manifest.yaml state/bim-environment.lock.yaml
git commit -m "chore: install and pin Horizun Revit MCP"
```

---

### Task 5: Create immutable disposable Revit baseline fixture

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

### Task 6: Discover actual Horizun MCP tool catalog

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

### Task 7: Horizun read-only smoke

**Artifacts:** `revit/lab/horizun/LAB_HORIZUN_READ.rvt`, `tool-lab/horizun/results/read-smoke.json`.

- [ ] Copy baseline to Horizun read fixture.
- [ ] Open copy in Revit.
- [ ] Invoke mapped health/document/read tools.
- [ ] Verify returned document path is disposable copy.
- [ ] Capture baseline element summary and warning count.
- [ ] Re-query after reads and assert no mutation.
- [ ] Promote read capabilities only with evidence.

---

### Task 8: Horizun `create_level` persistence test

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

### Task 9: Horizun `create_wall` persistence test

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

### Task 10: Horizun floor and room tests

- [ ] Fresh baseline copy for floor.
- [ ] Create 6 m × 4 m floor (target 24 m²).
- [ ] Verify area, level, polygon, warnings, persistence.
- [ ] Fresh baseline copy for room.
- [ ] Create verified 4 m × 4 m enclosure.
- [ ] Place named/numbered room.
- [ ] Verify placed/enclosed/area/persistence.
- [ ] Record both capabilities.

---

### Task 11: Horizun hosted/documentation/export matrix

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

### Task 12: Horizun Toposolid/site test

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

### Task 13: Clone/audit/build/deploy RevitCortex

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
$CortexExe = Get-ChildItem vendor/RevitCortex -Recurse -Filter RevitCortex.Server.exe |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1 -ExpandProperty FullName
$CortexExe
```

- [ ] Register:

```powershell
codex mcp add revitcortex -- $CortexExe
codex mcp list
```

- [ ] Record commit/path/hash/config snapshot/rollback.
- [ ] Commit audit/manifests.

---

### Task 14: Discover Cortex tools and prove bridge

- [ ] Open fresh Cortex lab RVT.
- [ ] Turn the RevitCortex ribbon `Cortex Switch` ON; it is off by default in current docs.
- [ ] Confirm bridge is localhost only.
- [ ] Confirm Codex `/mcp` sees server/tools.
- [ ] Generate actual `revitcortex-toolmap.yaml` from catalog.
- [ ] Validate no placeholders.
- [ ] Record current port/settings and logs.

---

### Task 15: A/B Cortex smoke using identical fixtures

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

### Task 16: Custom C# Revit API fallback proof

**Files:** `tool-lab/custom-api/CreateLabWall.cs`, result report.

- [ ] Write exact C# that retrieves a known level, converts meters to Revit internal units, creates one 5 m wall at 3 m height inside a transaction, logs returned ElementId, and throws on missing prerequisites.
- [ ] Execute only through a provider's verified code-execution capability in disposable file.
- [ ] Re-query independently.
- [ ] Save/close/reopen.
- [ ] Register `custom_csharp:create_wall` only if PASS.

---

### Task 17: Fault-injection matrix

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

### Task 18: Crash/recovery drill

- [ ] Create/hash known-good disposable checkpoint.
- [ ] Persist task as RUNNING.
- [ ] Make one mutation in working copy.
- [ ] Terminate only the disposable Revit session unexpectedly.
- [ ] Start new Revit process.
- [ ] Open last PASS checkpoint.
- [ ] Reconnect preferred provider.
- [ ] Rerun health/read smoke.
- [ ] Confirm interrupted mutation is not marked PASS.
- [ ] Record drill PASS/FAIL.

---

### Task 19: Provider benchmark and final matrix

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

### Task 20: Add the `tool-lab` CLI surface

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
- Both MCPs source-pinned and connected.
- At least one typed provider passes core read/write/save/reopen for level/wall/floor/room.
- A typed fallback is verified for core operations.
- Custom API proof works.
- Fault injection + crash drill complete.
- No Amanda production file opened.

### GO_WITH_LIMITATIONS
Only noncore capability (for example Toposolid or one documentation feature) is degraded and a safe tested alternative exists.

### NO_GO
No stable typed provider can perform core read/write/persistence on this actual Revit 2027 build.
# Project Intelligence and Source Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for parser/schema code; systematic debugging for reconciliation failures.

**Goal:** Convert Amanda's TFG, program of needs, site material, and verified normative/source files into canonical structured project data with immutable provenance and an explicit missing-data registry.

**Architecture:** Source files are immutable. Extraction produces three separate classes: `SOURCE_FACT`, `DERIVED_CONSTRAINT`, and `DESIGN_HYPOTHESIS`. Canonical JSON/YAML is schema-validated and becomes the only input consumed by the Design Engine.

**Tech Stack:** Python 3.12, Pydantic, PyYAML, local PDF parser, Shapely/GeoJSON.

**Spec:** `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`

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

### Task 1: Source manifest and hashing

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

### Task 2: Provenance model

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

Each `SourceReference` includes source ID, page/line locator when available, extraction method, confidence, note.

- [ ] Test `SOURCE_FACT` without source ID is rejected.
- [ ] Test a hypothesis cannot claim fact class.
- [ ] Implement.
- [ ] Commit.

---

### Task 3: Immutable ingest command

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

### Task 4: Ingest the two known Amanda documents when available to Codex

**Expected sources:** Amanda TFG PDF and program-of-needs PDF.

- [ ] Search the explicitly provided input folder/path, not the entire user's home drive.
- [ ] If either source is absent, set production blocker `BLOCKED_BY_INPUT:SOURCE_DOCUMENTS`, but keep synthetic development usable.
- [ ] When present, assign stable IDs `SRC-TFG-001`, `SRC-PROGRAM-001` for this source version.
- [ ] Compute hashes.
- [ ] Verify copied bytes match hashes.
- [ ] Keep PDFs private/local; commit them only if repository policy explicitly allows source documents. Manifests can be committed independently.

---

### Task 5: PDF text extraction adapter

**Files:**
- Create: `src/amanda_agent/ingest/pdf.py`
- Test: `tests/unit/test_pdf_adapter.py`

- [ ] Add a local parser dependency only after a small compatibility test; prefer PyMuPDF or pypdf based on actual extraction quality.
- [ ] Create fixture PDF with two pages and known text.
- [ ] Test page-number-preserving extraction.
- [ ] Store extracted text under `project/provenance/extracted/` with source hash.
- [ ] Never treat OCR output as authoritative when selectable text exists.
- [ ] Commit parser choice/version to environment lock.

---

### Task 6: Program requirement schema

**Files:**
- Create: `src/amanda_agent/requirements/models.py`
- Test: `tests/unit/test_requirement_models.py`

**Interfaces:** `SpaceRequirement`, `SectorRequirement`, `ProgramRequirementSet`.

- [ ] Write tests rejecting zero/negative area and quantity.
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
    privacy_level: int = Field(ge=0, le=5)
    accessible: bool = False
    source_refs: list[str]

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

### Task 7: Compile the program of needs into canonical JSON

**Files:**
- Create at runtime: `project/requirements/program.json`
- Create: `project/requirements/program-summary.md`
- Test: `tests/project/test_amanda_program.py`

- [ ] Extract every program line item exactly from source.
- [ ] Assign stable logical IDs by sector/space instance.
- [ ] Record source quantity/target-area facts.
- [ ] Record source capacity reference (up to 20 simultaneous residents) as a fact.
- [ ] Reconcile source subtotals and overall internal/external totals.
- [ ] Add tests for known source totals and presence of accessible bedroom/bathroom requirements.
- [ ] Generate markdown summary from canonical JSON, never the reverse.
- [ ] Commit canonical JSON and tests.

---

### Task 8: Relations schema

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

### Task 9: Compile source-backed principles separately from design hypotheses

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

### Task 10: Canonical site schema

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

Topography enum:
- `MISSING`
- `PLANAR_PLACEHOLDER`
- `VERIFIED_TOPOGRAPHY`

- [ ] Test invalid self-intersecting boundary is rejected by Shapely.
- [ ] Test `MISSING` cannot carry invented elevation points.
- [ ] Commit.

---

### Task 11: Compile known site facts and missing-data registry

**Files:**
- Create: `project/site/site.json`
- Create: `project/site/missing-data.yaml`

- [ ] Record source-backed total site area/frontages.
- [ ] Record the four named street/frontage relationships as facts.
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

### Task 12: Regulation source registry

**Files:**
- Create: `src/amanda_agent/requirements/regulations.py`
- Create: `project/regulations/registry.yaml`
- Test: `tests/unit/test_regulation_registry.py`

Statuses: `IDENTIFIED`, `SOURCE_ACQUIRED`, `VERIFIED`, `SUPERSEDED`.

- [ ] Seed regulation names identified by Amanda's TFG without copying remembered numerical rules.
- [ ] Require source file/version/page/section before a numeric rule can become `DERIVED_CONSTRAINT`.
- [ ] Test an unverified numeric rule cannot be compiled as hard constraint.
- [ ] Commit.

---

### Task 13: Provenance integrity suite

**Files:** `tests/project/test_provenance_integrity.py`

- [ ] Every source fact has source ref.
- [ ] Every requirement logical ID unique.
- [ ] No unresolved numeric source placeholder silently became a number.
- [ ] No hypothesis exists in source-fact files.
- [ ] Source file hashes still match immutable copies.
- [ ] Program subtotal/global reconciliation passes.
- [ ] Commit.

---

### Task 14: One-command validation report

**Files:**
- Modify: `src/amanda_agent/commands/ingest.py`
- Runtime: `docs/reports/ingest-report.md`

- [ ] `amanda-agent ingest --validate-only` validates source hashes, canonical schemas, provenance, program totals, site status, regulation registry.
- [ ] Expected missing topography yields `GO_WITH_LIMITATIONS`, not corruption.
- [ ] Malformed canonical data yields nonzero exit.
- [ ] Report exact blocker IDs.
- [ ] Commit.

---

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
# Generative Design Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for all solver/geometry code; systematic debugging for infeasible models or nondeterminism.

**Goal:** Implement deterministic generation, validation, scoring, Pareto filtering, and explanation of architectural alternatives from canonical Amanda requirements/site data.

**Architecture:** OR-Tools CP-SAT solves discrete assignment decisions; Shapely is geometric truth; NetworkX handles graphs/path metrics. Resolution progresses site → macrozones → blocks → sectors → rooms. TopologicPy and Ladybug/Honeybee are optional enhancements and must not destabilize the core engine.

**Tech Stack:** Python 3.12, OR-Tools, Shapely, NetworkX, IfcOpenShell; optional TopologicPy, Ladybug/Honeybee.

**Spec:** `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`

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

### Task 1: Install and pin core design dependencies

**Files:**
- Modify: `pyproject.toml`
- Create: `requirements.lock.txt`

- [ ] Add:

```toml
"ortools>=9.14,<10",
"shapely>=2.2,<3",
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

- [ ] Freeze exact resolved packages:

```powershell
.\.venv\Scripts\python.exe -m pip freeze | Sort-Object | Set-Content requirements.lock.txt
```

- [ ] Commit.

---

### Task 2: Design solution models

**Files:**
- Create: `src/amanda_agent/design/models.py`
- Test: `tests/solver/test_design_models.py`

**Interfaces:** `DesignSolution`, `MetricSet`, `ConstraintViolation`, `DesignStatus`.

- [ ] Write JSON round-trip test.
- [ ] Require fields: solution_id, run_id, seed, requirements_version, site_version, engine_version, archetype, geometry, metrics, hard_violations, soft_penalties, parents, status.
- [ ] Test `APPROVED_FOR_BIM` is explicit and not default.
- [ ] Commit.

---

### Task 3: Geometry primitives/tolerances

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

### Task 4: Hard-constraint engine

**Files:**
- Create: `src/amanda_agent/design/constraints.py`
- Test: `tests/solver/test_hard_constraints.py`

**Interfaces:** `validate_candidate(candidate, requirements, site) -> list[ConstraintViolation]`.

- [ ] Test room outside buildable site → violation.
- [ ] Test overlap → violation.
- [ ] Test required room missing → violation.
- [ ] Test required accessible room missing → violation.
- [ ] Test `MUST_BE_SEPARATED` broken → violation.
- [ ] Implement independent validators then aggregate.
- [ ] Assert hard violations are never converted to numeric soft penalties.
- [ ] Commit.

---

### Task 5: Adjacency graph

**Files:**
- Create: `src/amanda_agent/design/adjacency.py`
- Test: `tests/solver/test_adjacency.py`

- [ ] Build NetworkX graph from canonical relations.
- [ ] Test `MUST_ADJOIN` pass/fail.
- [ ] Test `SHOULD_BE_NEAR` penalty monotonically worsens with distance.
- [ ] Test `MUST_BE_SEPARATED` stays hard.
- [ ] Commit.

---

### Task 6: Flow graphs

**Files:**
- Create: `src/amanda_agent/design/flows.py`
- Test: `tests/solver/test_flows.py`

- [ ] Implement independent resident/child/staff/visitor/service/emergency graphs.
- [ ] Synthetic visitor route crossing private residential node must fail when policy forbids it.
- [ ] Service/resident path crossing may be a weighted soft penalty when configured.
- [ ] Compute path lengths and crossings deterministically.
- [ ] Commit.

---

### Task 7: Privacy gradient metric

**Files:**
- Create: `src/amanda_agent/design/privacy.py`
- Test: `tests/solver/test_privacy.py`

- [ ] Test direct public→privacy-5 transition is strongly penalized/invalid per configuration.
- [ ] Test public→controlled→technical→transition→residential scores better.
- [ ] Keep raw transition sequence in evidence.
- [ ] Commit.

---

### Task 8: Archetype configuration

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

### Task 9: OR-Tools macrozone solver

**Files:**
- Create: `src/amanda_agent/design/macrozones.py`
- Test: `tests/solver/test_macrozones.py`

- [ ] Write a three-sector RED test.
- [ ] Model sector-to-region assignment with CP-SAT.
- [ ] Encode required separation/adjacency and region capacity.
- [ ] Set solver random seed from run seed.
- [ ] Test two executions with same seed produce same assignment/order.
- [ ] Commit.

---

### Task 10: Block polygon generator

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

### Task 11: Room refinement

**Files:**
- Create: `src/amanda_agent/design/rooms.py`
- Test: `tests/solver/test_rooms.py`

- [ ] Start with synthetic 3-room rectangle.
- [ ] Enforce canonical area/min-dimension constraints only when they exist.
- [ ] Preserve room logical IDs.
- [ ] Reject overlaps and unreachable/orphan spaces.
- [ ] Verify candidate room areas sum plausibly against block area including circulation allowance.
- [ ] Commit.

---

### Task 12: External spaces as first-class geometry

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

### Task 13: Versioned scoring

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
- [ ] Weight changes alter total but never raw metrics.
- [ ] Store raw metrics and weighted total.
- [ ] Explicitly no aesthetics/beauty metric.
- [ ] Commit.

---

### Task 14: Pareto frontier

**Files:**
- Create: `src/amanda_agent/design/pareto.py`
- Test: `tests/solver/test_pareto.py`

- [ ] Known dominated vector fixture.
- [ ] Deterministic non-dominated filtering.
- [ ] Preserve tradeoff alternatives even when weighted total lower.
- [ ] Commit.

---

### Task 15: Fast solar/ventilation heuristics

**Files:**
- Create: `src/amanda_agent/design/environmental.py`
- Test: `tests/solver/test_environmental_heuristics.py`

- [ ] True-north-aware facade orientation.
- [ ] Apply source-backed Amanda orientation/wind findings as **project heuristics**, not universal truth.
- [ ] Label outputs `HEURISTIC`.
- [ ] Test expected relative score changes for east/west and wind exposure on synthetic case.
- [ ] Commit.

---

### Task 16: Deterministic generation

**Files:**
- Create: `src/amanda_agent/design/generate.py`
- Test: `tests/solver/test_generation_reproducibility.py`

- [ ] Generate fixed set with run ID and seed list.
- [ ] Canonicalize JSON ordering/float rounding before hash.
- [ ] Same seed/input/version produces same hash.
- [ ] Different seed yields at least one differing candidate on fixture.
- [ ] Store every seed with candidate.
- [ ] Commit.

---

### Task 17: Progressive pipeline

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

### Task 18: Explainability

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

### Task 19: Core regression fixtures

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

### Task 20: Optional TopologicPy spike

- [ ] Create isolated `.venv-topologic` so core solver cannot be broken.
- [ ] Install `topologicpy --upgrade`.
- [ ] Run minimal topology/graph operation.
- [ ] Record package/dependency versions, license, install conflicts, runtime value.
- [ ] Promote only if it adds a proven capability over NetworkX/Shapely.
- [ ] Otherwise mark optional capability DEGRADED/DEFERRED; core engine remains GO.

---

### Task 21: Optional Ladybug/Honeybee finalist environment

- [ ] Create isolated `.venv-environmental`.
- [ ] Install `ladybug-core` and `lbt-honeybee`.
- [ ] Verify imports/CLI.
- [ ] If a verified EPW is available, run one synthetic smoke simulation.
- [ ] Label genuine solver output `SIMULATED` only after reproducible run.
- [ ] Failure does not block core heuristic engine.

---

### Task 22: CLI `design` and `compare`

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
# BIM Compiler and Revit Desired-State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for compiler/policy code; systematic debugging for provider/Revit failures; verification-before-completion before stage promotion.

**Goal:** Compile a solution explicitly marked `APPROVED_FOR_BIM` into staged Revit 2027 checkpoints using the verified Capability Registry, with desired-state diffs, stable logical IDs, unit safety, provenance, checkpoints, and rollback.

**Architecture:** The Python compiler produces a read-only `BIM_PLAN.json`. Codex executes the plan through actual MCP tools selected from the Capability Registry. The compiler never decides architecture inside Revit; it reconciles desired state against current managed state and requests the smallest safe mutation set.

**Tech Stack:** Python 3.12, Revit 2027, verified Horizun/RevitCortex MCP capabilities, custom C# fallback, Shapely, IfcOpenShell.

**Spec:** `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`

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

### Task 1: Revit unit conversion library

**Files:**
- Create: `src/amanda_agent/bim/units.py`
- Test: `tests/unit/test_revit_units.py`

**Interfaces:** `meters_to_feet`, `feet_to_meters`, `sqm_to_sqft`, `sqft_to_sqm`.

- [ ] Write round-trip tests for 1 m, 10 m, 1 m², 24 m².
- [ ] Implement exact 1 ft = 0.3048 m conversion.
- [ ] Keep all Design Engine data metric; convert only at Revit boundary.
- [ ] Commit.

---

### Task 2: BIM stage and desired-element models

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

### Task 3: Safety Sentinel

**Files:**
- Create: `src/amanda_agent/bim/safety.py`
- Test: `tests/unit/test_bim_safety.py`

**Interfaces:** `assert_writable_target(Path)`.

- [ ] Test path containing `GOLDEN` rejected.
- [ ] Test `MASTER` rejected.
- [ ] Test `source` rejected.
- [ ] Test `revit/production/working/AMANDA_WORKING_001.rvt` accepted.
- [ ] Implement case-insensitive filename/path policy.
- [ ] Commit.

---

### Task 4: Checkpoint manager

**Files:**
- Create: `src/amanda_agent/bim/checkpoints.py`
- Test: `tests/unit/test_checkpoints.py`

**Interfaces:** create immutable stage copy + SHA256 manifest; verify hash before rollback.

- [ ] Test file copy hash equality.
- [ ] Test existing checkpoint path cannot be overwritten.
- [ ] Test GOLDEN cannot be used as writable checkpoint target.
- [ ] Implement.
- [ ] Commit.

---

### Task 5: Desired/current-state diff

**Files:**
- Create: `src/amanda_agent/bim/desired_state.py`
- Create: `src/amanda_agent/bim/current_state.py`
- Create: `src/amanda_agent/bim/diff.py`
- Test: `tests/unit/test_bim_diff.py`

Actions: `CREATE`, `UPDATE`, `REPLACE`, `NOOP`, `DELETE`.

- [ ] 17 correct + 1 missing desired room → one CREATE.
- [ ] Existing logical ID + equivalent geometry/properties → NOOP.
- [ ] Duplicate current logical ID → hard error.
- [ ] Unmanaged Revit elements are not deleted by default.
- [ ] Commit.

---

### Task 6: Destructive-change threshold

**Files:**
- Modify: `src/amanda_agent/bim/diff.py`
- Test: `tests/unit/test_destructive_threshold.py`

- [ ] Baseline threshold 10% of **managed** elements for DELETE/REPLACE.
- [ ] 11 destructive operations / 100 managed → block `HIGH_RISK_PLAN`.
- [ ] 5 / 100 may proceed only with a pre-operation checkpoint.
- [ ] Threshold config lives in versioned YAML.
- [ ] Commit.

---

### Task 7: BIM plan generator

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

### Task 8: Write-read-verify result model

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

### Task 9: Project initialization stage R01

**Files:**
- Create: `src/amanda_agent/bim/stages/project.py`
- Test: `tests/unit/test_stage_project.py`

- [ ] Preflight requires approved solution, healthy registry, correct Revit build.
- [ ] Template order: Amanda template copy if supplied and tested; else installed architectural template discovered on machine.
- [ ] Desired project metadata/naming is deterministic.
- [ ] Lab-execute R01 and save/reopen.
- [ ] Checkpoint `R01_PROJECT_INITIALIZED`.

---

### Task 10: Site stage R02

**Files:**
- Create: `src/amanda_agent/bim/stages/site.py`
- Test: `tests/unit/test_stage_site.py`

Modes:
- `PLANAR_PLACEHOLDER`: site boundary/reference only; no invented Z.
- `VERIFIED_TOPOGRAPHY`: may request Toposolid/grading capability.

- [ ] Test missing topography yields no Z points.
- [ ] Test verified point set creates desired Toposolid operation only if capability registry has a PASS provider.
- [ ] Run synthetic site through lab preferred provider.
- [ ] Verify extents/elevations and save/reopen.
- [ ] Checkpoint.

---

### Task 11: Levels/references R03

**Files:** `src/amanda_agent/bim/stages/levels.py`, tests.

- [ ] Generate only levels required by selected solution/topography.
- [ ] Do not invent structural grid/system.
- [ ] Verify name/elevation after write.
- [ ] Checkpoint.

---

### Task 12: Massing R04

**Files:** `src/amanda_agent/bim/stages/massing.py`, tests.

- [ ] Convert approved block polygons to simplified Revit masses/surrogate geometry supported by verified provider.
- [ ] Compare centroid, area, dimensions, rotation, separation, site containment against design JSON.
- [ ] Export 3D preview if verified capability exists.
- [ ] Reject any geometry mismatch beyond tolerances.
- [ ] Checkpoint.

---

### Task 13: Architectural shell R05

**Files:** `src/amanda_agent/bim/stages/shell.py`, tests.

- [ ] Exterior walls from approved polygons.
- [ ] Floors from closed loops.
- [ ] Simple approved roof representation.
- [ ] Controlled type catalog only (`EXT_WALL_01`, `INT_WALL_01`, etc.); no uncontrolled type proliferation.
- [ ] Query duplicate/off-axis/unjoined warnings.
- [ ] Save/reopen and checkpoint.

---

### Task 14: Internal layout R06

**Files:** `src/amanda_agent/bim/stages/layout.py`, tests.

- [ ] Convert room polygons to internal walls/boundaries.
- [ ] Preserve logical IDs independent of ElementId.
- [ ] Measure actual modeled room polygons.
- [ ] Accept configured area range; do not deform walls to chase exact decimals.
- [ ] Checkpoint.

---

### Task 15: Openings R07

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

### Task 16: Rooms R08

**Files:** `src/amanda_agent/bim/stages/rooms.py`, tests.

- [ ] Create/associate one room object per canonical room logical ID.
- [ ] Store name, number, sector, target area, privacy and source/requirement ID in managed metadata where safe.
- [ ] Query all rooms.
- [ ] Reject unplaced/not-enclosed/redundant managed rooms.
- [ ] Reconcile quantities/areas.
- [ ] Checkpoint.

---

### Task 17: Accessibility R09

**Files:** `src/amanda_agent/bim/stages/accessibility.py`, tests.

- [ ] Numeric rules loaded only from VERIFIED regulation registry.
- [ ] Build accessible route graph from entrance through required accessible spaces.
- [ ] If normative numeric data absent, output `BLOCKED_BY_INPUT` for those checks, never false PASS.
- [ ] Verify geometric checks supported by available source data.
- [ ] Checkpoint only for completed supported scope.

---

### Task 18: Furniture R10

**Files:** `src/amanda_agent/bim/stages/furniture.py`, controlled catalog, tests.

- [ ] Functional placeholders only after room geometry/clearances stabilize.
- [ ] Bedroom, psychology/technical, dining, office, child-area fixture sets are explicit.
- [ ] Use furnishings for spatial QA, not decorative randomization.
- [ ] Checkpoint.

---

### Task 19: Landscape R11

**Files:** `src/amanda_agent/bim/stages/landscape.py`, tests.

- [ ] Every programmed external space keeps logical ID and target area.
- [ ] Verify intended privacy/adjacency.
- [ ] Vegetation starts as controlled placeholders.
- [ ] West/privacy vegetation strategy can be represented only when it is part of approved option, not injected ad hoc.
- [ ] Checkpoint.

---

### Task 20: Materials R12

**Files:** `src/amanda_agent/bim/stages/materials.py`, `project/bim/material-catalog.yaml`, tests.

- [ ] Controlled catalog.
- [ ] No duplicate material names/types per run.
- [ ] Explicit material choices, traceable to selected design intent.
- [ ] Checkpoint.

---

### Task 21: Documentation R13

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

### Task 22: BIM CLI

**Files:**
- Create: `src/amanda_agent/commands/bim.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_bim_cli.py`

Commands:
- `amanda-agent bim plan --solution PATH`
- `amanda-agent bim verify-plan PATH`
- `amanda-agent bim status`

- [ ] Unapproved solution rejected.
- [ ] GOLDEN/source target rejected.
- [ ] `plan` never mutates Revit.
- [ ] Plan contains only tested provider chains.
- [ ] Commit.

---

### Task 23: Synthetic end-to-end BIM compile

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
# QA, Persistence, Export, and GOLDEN Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for QA/release code; verification-before-completion is mandatory before RC/GOLDEN promotion.

**Goal:** Implement model/program/architecture/accessibility/documentation QA, warning baselines, export validation, cold persistence tests, release manifests, hashes, and immutable GOLDEN promotion.

**Architecture:** QA consumes Revit query evidence and exported files. It does not trust write responses. A release candidate must survive save→close→process exit→restart→reopen→critical QA. GOLDEN promotion is a one-way new-directory operation.

**Tech Stack:** Python 3.12, Pydantic, IfcOpenShell, local PDF parser/renderer, verified Revit query/export capabilities.

**Spec:** `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`

## Global Constraints

- QA may block a build; it does not silently change requirements.
- Unknown warnings are never auto-ignored.
- GOLDEN is immutable.
- File existence is not sufficient export validation.
- IFC must parse.
- PDF page count/content preview must be checked.
- RC cannot promote without persistence evidence.

---

### Task 1: QA typed models

**Files:**
- Create: `src/amanda_agent/qa/models.py`
- Test: `tests/unit/test_qa_models.py`

Severities: `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
Result: `PASS`, `PASS_WITH_WARNINGS`, `FAIL`, `BLOCKED_BY_INPUT`.

- [ ] Write serialization/aggregation tests.
- [ ] A CRITICAL issue forces overall FAIL.
- [ ] A missing-input issue cannot be converted to PASS.
- [ ] Commit.

---

### Task 2: Program reconciliation QA

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

### Task 3: Model/geometric QA

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

### Task 4: Warning baseline/delta

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

### Task 5: Architecture/concept QA

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

### Task 6: Accessibility QA status discipline

**Files:**
- Create: `src/amanda_agent/qa/accessibility.py`
- Test: `tests/unit/test_accessibility_qa.py`

- [ ] Route-continuity checks use geometry/graph data.
- [ ] Numeric dimensional checks use only VERIFIED regulation rules.
- [ ] Missing rule/source → `BLOCKED_BY_INPUT` for that check.
- [ ] Report unsupported checks explicitly.
- [ ] Commit.

---

### Task 7: IFC validator

**Files:**
- Create: `src/amanda_agent/qa/ifc.py`
- Test: `tests/unit/test_ifc_qa.py`

- [ ] Build or store a tiny valid IFC fixture.
- [ ] Parse via IfcOpenShell.
- [ ] Reject zero-byte/unparseable file.
- [ ] Count expected storeys/spaces/walls/doors on fixture.
- [ ] Production validator compares expected high-level counts/IDs where export preserves them.
- [ ] Commit.

---

### Task 8: PDF validator

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

### Task 9: DWG sanity validator

**Files:**
- Create: `src/amanda_agent/qa/dwg.py`
- Test: `tests/unit/test_dwg_qa.py`

- [ ] Verify path/nonzero size.
- [ ] If a compatible local DWG parser is already available/tested, inspect header/extents/layers.
- [ ] Otherwise verify export result, file signature/size and explicitly report `LIMITED_DWG_VALIDATION`; do not install AutoCAD solely for QA.
- [ ] Commit.

---

### Task 10: Persistence coordinator

**Files:**
- Create: `src/amanda_agent/qa/persistence.py`
- Test: `tests/unit/test_persistence_plan.py`

Required sequence:
1. save RC;
2. hash;
3. close Revit normally;
4. confirm process exits;
5. start Revit 2027 executable detected by Plan 01;
6. open RC;
7. reconnect preferred provider;
8. provider health;
9. critical model/program QA;
10. compare hashes/state expectations.

- [ ] Test promotion object refuses incomplete sequence.
- [ ] Commit.

---

### Task 11: Release manifest

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
- limitations/blockers accepted for release.

- [ ] Deterministic sorted JSON serialization.
- [ ] Missing required artifact hash blocks GOLDEN.
- [ ] Commit.

---

### Task 12: GOLDEN promoter

**Files:**
- Create: `src/amanda_agent/release/promote.py`
- Test: `tests/unit/test_release_promotion.py`

- [ ] QA FAIL blocks promotion.
- [ ] Persistence incomplete blocks promotion.
- [ ] Mandatory export validation incomplete blocks promotion.
- [ ] Existing GOLDEN directory cannot be overwritten.
- [ ] Promotion copies RC into a new release directory and verifies hash after copy.
- [ ] Commit.

---

### Task 13: QA/export CLI

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

- [ ] `qa` writes JSON + Markdown.
- [ ] export plan is read-only.
- [ ] promotion guard tested from CLI.
- [ ] Commit.

---

### Task 14: Synthetic R14→R16 release drill

**Artifacts:** lab release directories.

- [ ] Use Plan 05 synthetic R13 model.
- [ ] Run full supported QA; create R14 report.
- [ ] Save as new RC R15.
- [ ] Hash RC.
- [ ] Close Revit; verify exit.
- [ ] Restart cold; reopen RC; reconnect provider.
- [ ] Re-run critical QA.
- [ ] Export IFC; parse with IfcOpenShell.
- [ ] Export PDF; validate pages/previews.
- [ ] Export DWG; run supported validator.
- [ ] Generate manifest and artifact hashes.
- [ ] Promote lab GOLDEN R16.
- [ ] Attempt to promote over same GOLDEN path and assert rejection.

---

### Task 15: Visual-documentation review protocol

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
Only a nonmandatory visual/DWG-depth check is limited and explicitly reported.

### NO_GO
RC can promote without persistence/QA, GOLDEN can be overwritten, or invalid exports are accepted.
# Autonomous Operation, Recovery, Security, and Multi-Session Continuity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; systematic debugging for repeated failures; verification-before-completion before autonomy is considered safe.

**Goal:** Make the Codex workflow safe and resumable across long sessions, new chats, Revit crashes/hangs, Windows reboots, provider failures, and maintenance updates.

**Architecture:** Filesystem state + Git are authoritative; chat memory is not. Session protocols, task dependency graph, locks, budgets, recovery manager, secret redaction, trust scoring, maintenance isolation, and status summaries govern autonomous work.

**Tech Stack:** Python 3.12, Git, PowerShell, Windows process inspection, YAML/JSON.

**Spec:** `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`

## Global Constraints

- One Revit production writer lease.
- No dependency/provider update during production phase.
- UAC/login/MFA are human boundaries.
- Technical fallbacks already authorized by registry do not need human approval.
- Never disable firewall/antivirus as a convenience.
- No cracked software.
- Secrets are never written to Git/logs/reports.

---

### Task 1: Production `AGENTS.md`

**Files:**
- Create: `AGENTS.md`
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

### Task 2: Task dependency graph

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

### Task 3: Session start protocol

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

### Task 4: Session end protocol

**Files:**
- Create: `src/amanda_agent/session/end.py`
- Test: `tests/unit/test_session_end.py`

- [ ] Cannot cleanly end with a task still RUNNING unless state changes to an explicit suspended/blocker state.
- [ ] Requires relevant test command/result recorded.
- [ ] Requires project-state update.
- [ ] Requires next task ID.
- [ ] Requires checkpoint reference when BIM was mutated.
- [ ] Commit.

---

### Task 5: Retry/fallback/time budgets

**Files:**
- Create: `src/amanda_agent/state/budgets.py`
- Test: `tests/unit/test_budgets.py`

Default policy:
- idempotent read retry budget: 3;
- mutating call retry budget: 2, but only after verifying no partial mutation;
- fallback budget: 3 providers/strategies;
- task soft/hard time limits are per-task config;
- equivalent repeated error signatures trigger `LOOP_DETECTED`.

- [ ] Test read budget exhaustion.
- [ ] Test mutation retry denied when partial-mutation flag true.
- [ ] Test repeated signature loop detection.
- [ ] Commit.

---

### Task 6: Blocker registry

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
- [ ] Missing Autodesk login blocks cloud only, not local pipeline.
- [ ] Commit.

---

### Task 7: Recovery manager

**Files:**
- Create: `src/amanda_agent/recovery/manager.py`
- Test: `tests/unit/test_recovery_manager.py`

- [ ] CRASHED state selects last hash-verified PASS checkpoint.
- [ ] Interrupted mutation is never retried blindly.
- [ ] Recovery plan contains reopen, provider reconnect, healthcheck, current-state re-query, then decision retry/fallback.
- [ ] A corrupted checkpoint is skipped for earlier verified one.
- [ ] Commit.

---

### Task 8: Revit watchdog

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
- [ ] Force kill is last action after normal-close attempt and checkpoint/state persistence.
- [ ] Commit.

---

### Task 9: Reboot-resume file

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

### Task 10: Security redaction

**Files:**
- Create: `src/amanda_agent/security/redaction.py`
- Test: `tests/unit/test_redaction.py`

- [ ] Redact bearer tokens, API keys, client secrets, passwords, authorization headers, private-key blocks.
- [ ] Preserve error type/host/status code/diagnostic nonsecret text.
- [ ] All logger/reporter paths call redactor before persistence.
- [ ] Commit.

---

### Task 11: Tool trust scoring

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

### Task 12: Tool-discovery report

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

### Task 13: Maintenance/update guard

**Files:**
- Create: `src/amanda_agent/maintenance/policy.py`
- Test: `tests/unit/test_maintenance_policy.py`

- [ ] Block Revit/provider/critical dependency updates when phase is production build, QA, RC, or release.
- [ ] Allow updates only in maintenance/experiment branch/worktree.
- [ ] Provider/Revit update requires full provider + synthetic E2E regression.
- [ ] Commit.

---

### Task 14: Status dashboard

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

### Task 15: Run summary

**Files:**
- Create: `src/amanda_agent/session/summary.py`
- Test: `tests/unit/test_run_summary.py`

- [ ] Summarize attempted/changed/passed/failed/rolled-back/next.
- [ ] Link raw logs/evidence paths instead of pasting huge payloads.
- [ ] Include provider/fallback usage.
- [ ] Commit.

---

### Task 16: Human-intervention state machine

**Files:**
- Create: `src/amanda_agent/state/human_gate.py`
- Test: `tests/unit/test_human_gate.py`

Allowed human gate reasons only:
- `UAC_APPROVAL`;
- `AUTHENTICATION_OR_MFA`;
- `LICENSE_VALIDATION`;
- `ESSENTIAL_SOURCE_DATA`;
- `ARCHITECTURAL_SELECTION`;
- `IRREVERSIBLE_EXTERNAL_ACTION`.

- [ ] Routine package installation/provider fallback must not emit human gate.
- [ ] Commit.

---

### Task 17: Fresh-session recovery drill

**Artifact:** `docs/reports/session-recovery-drill.md`.

- [ ] Complete and commit a test task.
- [ ] Persist project state with exact next task.
- [ ] Close Codex completely.
- [ ] Start a new Codex session in repo.
- [ ] It must read AGENTS/state/current plan/git and identify exact next READY task without user re-explaining history.
- [ ] Record PASS/FAIL.

---

### Task 18: Provider-update isolation drill

- [ ] Create isolated experiment worktree/branch.
- [ ] Change provider fixture/mock or update an upstream provider only there.
- [ ] Run Tool Lab regression.
- [ ] Deliberately leave an experiment failing.
- [ ] Verify `main` provider pins and production checkpoints unchanged.
- [ ] Remove experiment worktree safely after report.

---

### Task 19: Full reboot simulation/procedure

Without rebooting unnecessarily, validate the procedure:

- [ ] Generate `RESUME_AFTER_REBOOT.md`.
- [ ] Persist/commit state.
- [ ] Close Revit/Codex normally.
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
# Amanda Production End-to-End Run Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; use verification-before-completion before every Revit stage and final release.

**Goal:** Run the completed, tested local pipeline on Amanda's real TFG: ingest sources, generate alternatives, select one architecture, compile it to Revit, validate, export, and produce the first immutable GOLDEN deliverable set.

**Architecture:** This phase adds almost no new infrastructure. If production reveals a missing capability, stop that operation and return to the relevant Tool Lab/implementation plan before the new capability can touch production.

**Tech Stack:** The validated stack from Plans 01–07.

**Spec:** `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`

## Global Constraints

- First plan allowed to create Amanda production RVTs.
- No UNTESTED capability in production.
- Missing verified topography blocks final grading, not necessarily schematic design.
- One architecture must be explicitly `APPROVED_FOR_BIM` before detailed Revit compile.
- Every provider invocation/evidence is logged.
- Every R-stage checkpoint retained until GOLDEN.

---

### Task 1: Production preflight

**Files:** read-only checks against state/config.

- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m amanda_agent doctor
.\.venv\Scripts\python.exe -m amanda_agent status
.\.venv\Scripts\python.exe -m pytest tests -m "not slow" -q
codex mcp list
```

- [ ] Confirm exact current Revit build equals the build tested in `state/bim-environment.lock.yaml`.
- [ ] Confirm preferred core capabilities are PASS.
- [ ] Confirm core fallback provider is PASS.
- [ ] Confirm no stale writer lease.
- [ ] Confirm Git clean.
- [ ] Confirm source-manifest hashes still match.
- [ ] If Revit/provider build changed, `NO_GO` until Plan 02 regression reruns.

---

### Task 2: Re-ingest/validate the latest Amanda sources

- [ ] Validate TFG and program PDFs against source manifest.
- [ ] Ingest every newer Amanda file supplied for the design run using a new source version, never overwrite old provenance.
- [ ] Regenerate canonical data only from the newly selected source set.
- [ ] Run project-intelligence tests.
- [ ] Commit source-version metadata and canonical-data change.

---

### Task 3: Resolve site data to highest verified level

- [ ] Inspect only user-supplied/project-scoped site files for boundary/survey/topography.
- [ ] If verified survey/topography exists, ingest/hash/validate and set `VERIFIED_TOPOGRAPHY`.
- [ ] If absent, use `PLANAR_PLACEHOLDER` and retain blockers for final grading/altimetric accessibility.
- [ ] Never convert TFG placeholders into invented elevations.
- [ ] Generate updated `project/site/missing-data.yaml`.

---

### Task 4: Freeze design-run inputs

Before generating options:
- [ ] validate source-backed principles;
- [ ] review design hypotheses file;
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

### Task 5: Generate production candidate run 001

Target baseline: 6 archetypes × 24 seeds = 144 macro candidates.

- [ ] Configure `AMANDA-RUN-001` for exactly 144 initial macro candidates.
- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m amanda_agent design --run-id AMANDA-RUN-001
```

- [ ] Store every seed, engine/input version.
- [ ] Record hard-constraint rejection count by rule.
- [ ] Verify zero hard-invalid candidate enters ranking.
- [ ] Preserve Pareto set.

---

### Task 6: Refine/rank top candidates

- [ ] Refine approximately top 15 macro options into block/room geometry.
- [ ] Re-run hard constraints after refinement.
- [ ] Compute all raw score dimensions.
- [ ] Apply frozen weights.
- [ ] Keep Pareto non-dominated set.
- [ ] Select top 5 for finalist analysis.
- [ ] Generate per-finalist:
  - `solution.json`;
  - geometry GeoJSON;
  - adjacency/flow graph exports;
  - metrics/penalties;
  - `WHY_THIS_OPTION.md`;
  - floorplan/zoning SVG/PNG.

---

### Task 7: Environmental finalist pass

- [ ] Run source-backed solar/ventilation heuristics on top 5.
- [ ] If detailed environmental capability is PASS, run the reproducible finalist simulation workflow.
- [ ] Mark outputs correctly as `HEURISTIC` or `SIMULATED`.
- [ ] Do not claim CFD/Radiance-type validation when only heuristic exists.
- [ ] Update comparison matrix with raw and weighted values.

---

### Task 8: Create conceptual Revit massing for top 3

For each finalist:
- [ ] create its own disposable production-candidate RVT;
- [ ] compile R01→R04 only;
- [ ] verify mass/site metrics against solution JSON;
- [ ] export 3D/site preview;
- [ ] save/close/reopen massing file;
- [ ] record provider tools/fallbacks;
- [ ] do not create detailed rooms/families/sheets yet.

---

### Task 9: Architectural selection gate

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

- [ ] Present top 3 to Amanda/Matheus.
- [ ] Record selected solution ID and selection note.
- [ ] If hybrid requested, create new solution with `parents=[...]`, rerun complete constraints/scoring/environmental pipeline, and include it as a new candidate—not an unvalidated manual splice.
- [ ] Set exactly one solution status to `APPROVED_FOR_BIM`.
- [ ] Commit selection record.

---

### Task 10: Create production working RVT

- [ ] Acquire `state/locks/revit-writer.lock`.
- [ ] Safety Sentinel verifies target path.
- [ ] Create `revit/production/working/AMANDA_WORKING_001.rvt` from tested project baseline/template.
- [ ] Hash pre-build state.
- [ ] Record session owner/provider health.

---

### Task 11: Compile R01–R04

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

### Task 12: Compile R05–R08

- [ ] R05 shell.
- [ ] R06 internal layout.
- [ ] R07 doors/windows/openings.
- [ ] R08 rooms.
- [ ] Run program quantity/area reconciliation after R08.
- [ ] Any missing required room is a stop condition before R09.

---

### Task 13: Compile R09–R12

- [ ] R09 accessibility to the extent supported by verified normative/site data.
- [ ] R10 functional furniture placeholders.
- [ ] R11 programmed exterior/landscape spaces.
- [ ] R12 approved material layer.
- [ ] Unsupported final compliance checks remain blockers, not green checkmarks.

---

### Task 14: Compile R13 documentation

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

### Task 15: Run full R14 QA

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

### Task 16: Create R15 Release Candidate

- [ ] Save to a new RC path.
- [ ] Hash RC.
- [ ] Close Revit normally.
- [ ] Confirm process exit.
- [ ] Start detected Revit 2027 executable cold.
- [ ] Reopen RC.
- [ ] Reconnect preferred provider.
- [ ] Re-run critical model/program/room/provider QA.
- [ ] If divergence appears, rollback to last R14 PASS checkpoint and debug.

---

### Task 17: Export/validate RC

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

### Task 18: Promote R16 GOLDEN

Preconditions:
- QA PASS or explicitly accepted noncritical limitation;
- persistence PASS;
- mandatory exports PASS;
- no unexplained critical warning/blocker;
- source/provider/input versions fixed.

- [ ] Generate final manifest.
- [ ] Copy RC into **new** `bim/releases/GOLDEN-001/`.
- [ ] Verify post-copy RVT hash equals RC hash.
- [ ] Mark GOLDEN immutable in project state/safety policy.
- [ ] Release writer lock.

---

### Task 19: Final deliverable package

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
- [ ] Generate final `RUN_SUMMARY.md`.
- [ ] Commit metadata/reports; keep RVT binary outside normal Git unless LFS policy is later approved.

---

## Production Completion Gate

### SUCCESS
GOLDEN release exists, reopens after a cold Revit restart, core QA passes, exports validate, provenance/provider/input versions are recorded.

### ACCEPTABLE LIMITATION
Missing verified topography/normative source remains explicitly reported and is not misrepresented as validated final grading/compliance.

### FAILURE
Any release uses untested provider behavior, fabricated source data, unresolved program mismatch, corrupted state, or no cold-reopen verification.
# Optional Rendering and Cloud Fallback Extensions Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; Tool Lab validation remains mandatory for optional providers.

**Goal:** Add optional Blender rendering and Autodesk APS/Revit Automation fallback **without** making either a hidden dependency of the local production pipeline.

**Architecture:** Blender consumes a verified release/export; it never edits the authoritative Revit GOLDEN. APS is registered only for a concrete blocked local capability, uses separate credentials, and stays below verified local providers in routing priority.

**Tech Stack:** Blender MCP/uvx, Blender, Autodesk APS Automation API samples, Codex MCP, existing local pipeline.

**Spec:** `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`

## Global Constraints

- Do not execute before local synthetic GOLDEN exists.
- Cloud remains fallback-only.
- Optional provider failure cannot invalidate a valid local GOLDEN.
- No credentials in Git/logs.
- Every optional MCP gets a Tool Lab and capability entry.

---

### Task 1: Determine immediate rendering need

- [ ] Read current Amanda deliverable requirements.
- [ ] If no render is required, mark Blender capability `DEFERRED_OPTIONAL` and do not install just for novelty.
- [ ] If renders are required, proceed.

---

### Task 2: Install/verify `uv` for Blender MCP

Current upstream Blender MCP documentation uses `uvx`.

- [ ] Check:

```powershell
uv --version
uvx --version
```

- [ ] If absent, use current official Astral Windows installer documented by Blender MCP:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

- [ ] Start a fresh shell and verify versions.
- [ ] Record versions in environment lock.

---

### Task 3: Register Blender MCP

- [ ] Register:

```powershell
codex mcp add blender -- uvx blender-mcp
codex mcp list
```

- [ ] Install addon:

```powershell
uvx blender-mcp install-addon
```

- [ ] Open Blender, enable installed MCP addon according to current upstream instructions.
- [ ] Do not load Amanda model yet.

---

### Task 4: Blender Tool Lab

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

### Task 5: Rendering pipeline from verified BIM release

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

### Task 6: APS need gate

- [ ] Confirm a **specific required** local capability is `BLOCKED_BY_TOOL` after verified typed/custom/interchange fallbacks.
- [ ] If no concrete blocked capability exists, mark APS `DEFERRED_OPTIONAL` and stop APS work.
- [ ] If one exists, write `tool-lab/aps/need-report.md` explaining exact capability and why local alternatives failed.

---

### Task 7: Audit official APS sample repos

Current reference repos:
- `autodesk-platform-services/aps-sample-mcp-server-revit-automation`
- `autodesk-platform-services/aps-sample-revit-mcp-tools-bundle`

- [ ] Clone in experiment worktree only.
- [ ] Pin commits.
- [ ] Read README/source/config files.
- [ ] Record that the AppBundle sample currently describes itself as sample/proof-of-concept; do not treat it as hardened production middleware automatically.
- [ ] Audit credential locations, network/data flow, activity/AppBundle configuration, rollback.
- [ ] Run tool trust score.

---

### Task 8: APS secret boundary

If APS remains justified:

- [ ] Create `.env.example` with **names only**, e.g. APS client ID variables.
- [ ] Store actual credentials in Windows Credential Manager or another approved local secret mechanism.
- [ ] Test redaction against APS logs.
- [ ] User handles Autodesk login/app authorization/MFA when prompted.
- [ ] Never upload unrelated source files.

---

### Task 9: APS sandbox deployment/test

- [ ] Build current official sample projects locally.
- [ ] Deploy only to a dedicated test APS app/project/activity.
- [ ] Use synthetic/disposable Revit cloud model/input.
- [ ] Run a harmless query or tiny model mutation.
- [ ] Verify output file/state independently.
- [ ] Record latency/cost/data-residency implications.
- [ ] Register APS capability only for the exact tested semantic operation.

---

### Task 10: Preserve local-first routing

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
