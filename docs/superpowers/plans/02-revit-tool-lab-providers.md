> GERADO de [2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-02) em 2026-09-15. Edite o COMBINED e execute `docs/review/package_review.py`; não edite esta cópia. Caminhos operacionais no texto são relativos à raiz do projeto.

<a id="phase-02"></a>

# Revit Tool Lab, Provider Validation, and Capability Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`. Use TDD for registry/policy code, systematic debugging for every provider failure, and verification-before-completion before promoting any capability.

**Goal:** Install Horizun and RevitCortex from pinned source, prove their capabilities against the actual Revit 2027 build in disposable models, prove a custom Revit API fallback, inject failures, and build the deterministic Capability Registry used by production.

**Architecture:** Nothing in this plan touches Amanda production. Every provider gets its own disposable RVT copies. Codex discovers the **actual** MCP tool catalog after installation and records a semantic toolmap; no tool names are invented from documentation. Promotion requires independent model re-query and save/reopen persistence.

**Tech Stack:** Revit 2027, .NET 10, Horizun Revit MCP, RevitCortex, Codex MCP, C#, Python/Pydantic/pytest.

**Spec:** [design specification](../../../2026-09-11-amanda-tfg-bim-agent-design.md)

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
