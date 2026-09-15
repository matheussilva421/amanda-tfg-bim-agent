> GERADO de [2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-01) em 2026-09-15. Edite o COMBINED e execute `docs/review/package_review.py`; não edite esta cópia. Caminhos operacionais no texto são relativos à raiz do projeto.

<a id="phase-01"></a>

# Foundation, Environment, Persistent State, and CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`. Use TDD for code, systematic debugging for failures, verification-before-completion before phase PASS.

**Goal:** Create the Python control plane, detect the real Windows/Revit/Codex/.NET environment, snapshot configurations, establish durable project state, single-writer locking, logs, and `doctor/status/resume/rollback` commands.

**Architecture:** A Python 3.12 package owns project state and deterministic policy. Environment probes are isolated so they can be unit tested. Bootstrap never edits Amanda RVTs.

**Tech Stack:** Python 3.12 x64, Typer, Pydantic v2, PyYAML, Rich, pytest, PowerShell, Git.

**Spec:** [design specification](../../../2026-09-11-amanda-tfg-bim-agent-design.md)

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
