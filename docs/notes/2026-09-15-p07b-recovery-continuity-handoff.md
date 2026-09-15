# P07B Recovery and Continuity Handoff

Date: 2026-09-15
Agent: Hades
Repository: `C:\Users\slvma\Downloads\Github\Projeto Amanda`
Mode: shared working directory; no worktree, staging, commit, push, or reboot

## Status

P07-T07, P07-T08, P07-T09, P07-T14, and P07-T15 are implemented in the assigned write set and covered by focused tests. P07-T18 is validated as an offline Tool Lab isolation drill with a deliberately failing experiment. P07-T17 and P07-T19 are prepared only: the fresh-session continuity confirmation remains for the main agent and was not simulated or claimed as PASS.

The live state read during this handoff was:

- phase: `PHASE_02` / `revit-tool-lab-providers`, status `PENDING`;
- last completed task: `P09-T10`;
- next task: `P06-T01`;
- READY task reported by `resume`: `P06-T01`;
- state revision: `123`;
- current checkpoint field: `null`;
- writer lease: free;
- preferred provider: `horizun`, health recorded as `HEALTHY`;
- Revit build recorded: `27.2.0.39`, product `20260716_1515 (x64)`;
- verified checkpoint used for resume evidence: `revit/lab/custom-api/T18_LAST_PASS.rvt`, SHA-256 `8ccab171e89fa4ac414f9ca3c57b5c4161cd7ee6dd61f45f86529703ee281cb2`;
- the task graph still leaves P07-T14/P07-T15 pending and P07-T17 dependent on P07-T15.

The state files were read from disk. Other agents changed shared state during this work; those changes were preserved.

## Implemented files

Owned production files:

- `src/amanda_agent/recovery/__init__.py`
- `src/amanda_agent/recovery/manager.py`
- `src/amanda_agent/recovery/watchdog.py`
- `src/amanda_agent/recovery/reboot.py`
- `src/amanda_agent/status_dashboard.py`
- `src/amanda_agent/session/summary.py`
- `src/amanda_agent/commands/status.py`
- `src/amanda_agent/tools/trust.py`
- `src/amanda_agent/tools/discovery.py`

Owned tests:

- `tests/unit/test_recovery_manager.py`
- `tests/unit/test_watchdog.py`
- `tests/unit/test_reboot_resume.py`
- `tests/unit/test_status_dashboard.py`
- `tests/unit/test_run_summary.py`
- `tests/unit/test_tool_trust.py`
- `tests/unit/test_tool_discovery.py`

Reports and continuity artifacts:

- `docs/reports/session-recovery-drill.md`
- `docs/reports/provider-update-isolation-drill.md`
- `docs/reports/reboot-resume-procedure.md`
- `RESUME_AFTER_REBOOT.md`
- this handoff

Scratch/evidence artifacts for the offline drill:

- `.tmp-p07-isolation-run.py`
- `.tmp-p07-isolation/`
- `.tmp-generate-resume.py`

The isolation directory intentionally retains the failing experiment and its JSON evidence until the main agent captures the result.

## Technical decisions

Recovery uses the existing checkpoint manifest and SHA-256 format from `src/amanda_agent/bim/checkpoints.py`. `select_checkpoint()` loads candidate manifests, recomputes file size and SHA-256, checks recorded PASS provenance where available, skips malformed or corrupted checkpoints, and selects the latest verified PASS checkpoint. `build_recovery_plan()` emits typed steps in this order: reopen checkpoint, reconnect preferred provider, healthcheck, re-query current state, then decide retry or fallback. An interrupted mutation ends in manual review and does not permit blind retry.

The watchdog exposes pure decision functions for `HEALTHY`, `BUSY`, `SUSPECTED_HANG`, `HUNG`, and `CRASHED`. A timeout alone produces `SUSPECTED_HANG`; force kill requires corroborating signals, grace handling, a normal-close attempt, matching owned PID and start time, verified persisted checkpoint/state, a disposable document, and explicit authorization. It never creates a new checkpoint for a hung process and never kills unknown user work.

Resume generation is deterministic, atomic, and redacts generated text. `RESUME_AFTER_REBOOT.md` records phase, last PASS task, reboot reason, checkpoint and hash, expected Revit/provider state, first verification commands, and next task. Its status is `PREPARED`, not a fresh-session validation claim.

The dashboard reads state, task graph, environment lock, tool health, capabilities, blockers, writer lease, design/stage/checkpoint fields, and Git HEAD from disk. Missing values render as `NOT_RECORDED` or `UNKNOWN`. The `status` command retains its existing stdout and additionally writes `state/status.md`.

Run summaries separate attempted, changed, passed, failed, rolled back, next tasks, log/evidence links, and provider/fallback use. Raw payloads are not dumped into the report.

Trust scoring preserves the nine required dimensions. Unknown license blocks automatic promotion; unsigned Windows binaries retain recorded risk when source build/provenance exists; official samples remain labeled as samples and are not production eligible by default. Discovery reports include repository/version/license/build/install/network/Revit/MCP/Codex/rollback/risk/capability fields and require Tool Lab validation before any production install.

## Tests and commands

TDD RED was confirmed first:

```text
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit/test_recovery_manager.py tests/unit/test_watchdog.py tests/unit/test_reboot_resume.py tests/unit/test_status_dashboard.py tests/unit/test_run_summary.py -q -p no:cacheprovider --basetemp=.tmp-pytest-hades-red
```

Result: collection failed for the expected reason, five `ModuleNotFoundError` errors for the not-yet-created production modules.

Focused acceptance:

```text
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit/test_recovery_manager.py tests/unit/test_watchdog.py tests/unit/test_reboot_resume.py tests/unit/test_status_dashboard.py tests/unit/test_run_summary.py tests/unit/test_tool_trust.py tests/unit/test_tool_discovery.py -q -p no:cacheprovider --basetemp=.tmp-pytest-hades-p7
```

Result: `29 passed`, `0 failed`, 1.47 seconds.

Broad acceptance:

```text
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit tests/solver tests/policy -q -p no:cacheprovider --basetemp=.tmp-pytest-hades-all
```

Result: `611 passed`, `0 failed`, 19.86 seconds. The previously mentioned count of 525 is an older baseline; this run included the current repository test set and had no failure to classify as pre-existing.

Lint:

```text
& './.venv/Scripts/python.exe' -m ruff check src/amanda_agent/recovery src/amanda_agent/status_dashboard.py src/amanda_agent/session/summary.py src/amanda_agent/commands/status.py src/amanda_agent/tools/trust.py src/amanda_agent/tools/discovery.py tests/unit/test_recovery_manager.py tests/unit/test_watchdog.py tests/unit/test_reboot_resume.py tests/unit/test_status_dashboard.py tests/unit/test_run_summary.py tests/unit/test_tool_trust.py tests/unit/test_tool_discovery.py
```

Result: `All checks passed!`.

CLI smoke checks:

```text
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m amanda_agent status
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m amanda_agent resume
```

Both exited successfully. `status` preserved its existing console report and generated/updated `state/status.md`. `resume` reported `P06-T01` as the next/READY task. No live Revit or provider action was inferred from these commands.

P07-T18 offline drill:

```text
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' '.tmp-p07-isolation-run.py'
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest .tmp-p07-isolation/tool-lab/fault-injection/test_run_matrix.py -q -p no:cacheprovider --basetemp=.tmp-pytest-hades-isolation
```

Results: baseline `8 total / 4 pass / 0 fail / 4 skipped_needs_revit`; deliberate copied-fixture experiment `8 total / 3 pass / 1 fail / 4 skipped_needs_revit`, exit code `1`; copied Tool Lab tests `3 passed`. Production pins were unchanged: `state/bim-environment.lock.yaml`, `state/capabilities.yaml`, and all 21 `revit/lab/**/*.rvt` hashes matched before and after. Full hashes are recorded in `docs/reports/provider-update-isolation-drill.md` and `.tmp-p07-isolation/isolation-report.json`.

## Validation limits and continuation

No machine reboot was performed. No fresh-session handoff was performed. No live Revit reopen, provider reconnect, provider healthcheck, Tool Lab install, DLL/add-in installation, or force-kill path was executed. The real provider update version remains a study/procedure boundary: a true worktree would require a maintenance window and separate deployment/process ownership; the offline copied-fixture drill does not establish live provider safety.

P07-T17 remains `PREPARED_PARTIAL`. The main agent must start a new session and run the exact commands in `docs/reports/session-recovery-drill.md`, including reading `AGENTS.md`, `START_HERE_FOR_CODEX.md`, this handoff, `RESUME_AFTER_REBOOT.md`, and `PROJECT_STATE.yaml`, followed by `doctor`, `status`, and `resume`. The main agent must record whether the new session identifies the next READY task without human context. If `resume` still reports `P06-T01`, P07-T17 must not be promoted because the graph still depends on P07-T15.

P07-T19 remains `PREPARED_PARTIAL`. The main agent must execute the post-reboot procedure in `docs/reports/reboot-resume-procedure.md` after an actual reboot, then record fresh-session state, doctor/status/resume output, provider/Revit observations, and checkpoint read/verify evidence. This session intentionally did not reboot the machine.

## GitHub and ownership

Git mutations were intentionally not run because the owner explicitly prohibited `git add`, `git commit`, `git worktree`, and push operations for this delegated write set. The shared branch remains dirty due parallel agents; the observed HEAD during the work was `a15518fd5599038d4df230c612cfe4bfc1015ae7`. The main agent must inspect the complete shared diff, stage only the accepted changes, commit, push, and update task status. No claim of commit or push is made here.

## Exact resume

1. Preserve the current scratch evidence until the main agent records P07-T18.
2. In a fresh session, run the commands in `docs/reports/session-recovery-drill.md` and capture the actual next READY task.
3. For P07-T19, only after an authorized machine reboot, run the commands in `docs/reports/reboot-resume-procedure.md` and independently verify the checkpoint/provider/Revit state.
4. Re-read the reports and this handoff, update formal task state through the main agent, then run the relevant acceptance suite again after any integration changes.

