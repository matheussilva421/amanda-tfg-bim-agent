> GERADO de [2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-07) em 2026-09-15. Edite o COMBINED e execute `docs/review/package_review.py`; não edite esta cópia. Caminhos operacionais no texto são relativos à raiz do projeto.

<a id="phase-07"></a>

# Autonomous Operation, Recovery, Security, and Multi-Session Continuity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; systematic debugging for repeated failures; verification-before-completion before autonomy is considered safe.

**Goal:** Make the Codex workflow safe and resumable across long sessions, new chats, Revit crashes/hangs, Windows reboots, provider failures, and maintenance updates.

**Architecture:** Filesystem state + Git are authoritative; chat memory is not. Session protocols, task dependency graph, locks, budgets, recovery manager, secret redaction, trust scoring, maintenance isolation, and status summaries govern autonomous work.

**Tech Stack:** Python 3.12, Git, PowerShell, Windows process inspection, YAML/JSON.

**Spec:** [design specification](../../../2026-09-11-amanda-tfg-bim-agent-design.md)

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
