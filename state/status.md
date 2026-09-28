# Status dashboard

Source: live files in the project workspace. Missing values remain `NOT_RECORDED`.

## Phase and task progress

- Phase: `P7` — detailed-production
- Phase status: `PENDING`
- Next task: `P7-T01` (R05 architectural shell; currently blocked at the provider gate)
- Last recorded task: `P6-T01`
- Tasks: 193 total; P7-T01 is `BLOCKED_BY_TOOL` until live R05 persistence gates pass
- Current authorization: P7-T01/R05 only; authorization ends at R05. Every later stage needs its own task gate; R05 completion does not start R06.
- Current blocker: `R05_PARTIAL_RECOVERY_UNVERIFIED:BLOCKING`; the official runner now passes provider readiness in the elevated user context, but guarded recovery cannot verify an explicit m2 Area reading for ElementId 331188.
- Historical `direct app Horizun health reports HEALTHY` snapshots used stale PIDs and do not establish the current session. Resume only after the production runner can target the active Revit 2027 RUN-003 document.
- The official runner in the elevated current-user context passed live health, zero-other-client, exact target/build/PID, command registry 73/73, provider tool registry 80/80, MCP tools/list 80, full_write, and mcp_paused=false. This resolves the sandbox discovery blocker; the discovery token was not read.
- The runner entered guarded recovery because the live model includes the known unsaved partial and does not match the accepted P6 element count. The checkpoint's diagnostic-only readback contains 25 rows and complete coverage. The exact Area takeoff failed its measured-m2 gate for ElementId 331188. No model save, R05 write, or checkpoint occurred. The lease is absent; the open RUN-003 target must not be hashed or closed. Last pre-open hash remains `F5BEEB6BF7D544710EA3A35DDE2B8A880E78FC4E284E12CB4A90E1BCCF982B19`.
- `P1`: 1/1 PASS
- `P2`: 1/1 PASS
- `P3`: 1/1 PASS
- `P4`: 1/1 PASS
- `P5`: 1/1 PASS
- `P6`: 1/1 PASS
- `P7`: 0/9 PASS

- `PHASE_00`: 3/3 PASS
- `PHASE_01`: 13/13 PASS
- `PHASE_02`: 20/20 PASS
- `PHASE_03`: 15/15 PASS
- `PHASE_04`: 22/22 PASS
- `PHASE_05`: 23/23 PASS
- `PHASE_06`: 15/15 PASS
- `PHASE_07A`: 11/11 PASS
- `PHASE_07B`: 6/8 PASS
- `PHASE_08`: 19/38 PASS
- `PHASE_09`: 4/10 PASS

## Environment

- Revit build: `27.2.0.39`
- Revit product version: `20260716_1515(x64)`

## Provider health

Preferred provider: `horizun`.

Earlier direct app health calls used stale PIDs. Journal `journal.0037.txt`
binds the exact RUN-003 document and Horizun add-in startup to PID 12660. The
official runner in the elevated user context passed typed health, zero-other-
client, exact-target/build/PID and all provider readiness gates; do not reuse
older health snapshots as current evidence.

The production runner starts
`C:\Users\slvma\AppData\Local\Programs\Horizun\MCP\server\horizun-mcp.exe`
(version 1.3.3.0). On 2026-09-28 22:21:31Z the official runner reported command
registry 73/73, provider tools 80/80, MCP tools/list 80, full_write and
mcp_paused=false. Its runner-enforced exclusive-client and exact-target gates
also passed. Sandboxed attempts failed discovery because the owner-only
discovery ACL is not readable in that context; its token was not read. Do not
route model writes through another client. The transport blocker is resolved;
the active gate is `R05_PARTIAL_RECOVERY_UNVERIFIED:BLOCKING`.

The known partial entered guarded recovery after the current model failed the
accepted P6 element-count check. The explicit Area takeoff failed for ElementId
331188; no measurement or unit was inferred. The latest request returned at
22:21:31 UTC; wait until 22:31:31 UTC before another Horizun call. Then retry
once through the exact R05-only runner, which now prints bounded state/unit/
value-type diagnostics for invalid readings. No standalone client, lease
bypass, save or model write is allowed before the recovery gates pass.

## Current RUN-003 R04 acceptance status

The P6 checkpoint SHA-256 is
`8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326`
(4,960,256 bytes). Its manifest agrees and `CheckpointManager.verify_checkpoint`
returned true. The exact target was cold-reopened without upgrade. Fresh typed
readback returned 25 spatial elements (7 masses, 14 floors, 4 roofs), complete
coverage, zero unreadable; complete model summary returned 4,573 with complete
coverage and zero unreadable.

P6 reconciled the admin envelope to 10×20 m per floor, aligned the upper plate
to Level 2 at 4.0 m, and connected the public admin route to the south edge.
The Board-02 divergence record is `RESOLVED_FOR_STUDY`; personal approval remains
false and official program areas/quantities were not changed. The five external
program spaces remain 80/80/30/30/40 m².

P6-T01 is `PASS` for normalized-study spatial topology / CANON-011. R06 owns the
internal layout; R08 owns Revit Room creation and official area readback. Nine
fresh views and one explicitly historical child/playground reference are documented in
`revit/production/evidence/AMANDA-RUN-003-R04/views/p6-canon-011-20260926/p6-canon-011-captures.json`.
The near-blank P6 relation attempt is excluded. Five site-data limits remain;
no cadastral/north/site-availability claim is made. DEC-010 preserves historical conditional
authorization for R05–R13 after P6 PASS. The current user authorization is only
P7-T01/R05; each later stage requires its own task gate, and R05 completion does not start R06. Independent Luna 6 xhigh review
reconfirmed P6 PASS for spatial topology only. Before R06, correct the 3/3/3
family-pavilion bedroom allocation conflict in current code/spec/report while
preserving official PDF quantities and areas; this does not block R05.

## Capability counts

- PASS: 15
- FAIL: 0
- UNTESTED: 0

## Blockers

Blocker severity applies to the affected tasks and claims; check state/blockers.yaml, the task graph, and PROJECT_STATE.yaml for phase-specific scope.

- `SITE_TOPOGRAPHY` [BLOCKING]: verified survey or topographic elevations for the lot
- `SITE_BOUNDARY` [BLOCKING]: surveyed or cadastral polygon in a stated coordinate system
- `SITE_OCCUPANCY` [BLOCKING]: confirmation of the current use of the lot and of the relocation premise for the police company unit
- `SITE_FRONTAGE_COUNT` [DEGRADING]: whether the lot has three or four frontages
- `SITE_TRUE_NORTH` [DEGRADING]: a verified true-north bearing with a source drawing datum
- `RUNNER_TRANSPORT_UNREACHABLE` [RESOLVED, 2026-09-28]: the official runner in the elevated current-user context passed live health, exclusive-client, exact-target, complete-registry, tools/list and write-control gates.
- `R05_PARTIAL_RECOVERY_UNVERIFIED` [BLOCKING, P7-T01 only]: the known unsaved partial failed the explicit measured-m2 Area gate for ElementId 331188. No R05 write/save/checkpoint occurred.

## Design and Revit recovery

- Selected design: `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`
- Revit stage: `R04`
- Current checkpoint: `revit/production/evidence/AMANDA-RUN-003-R04/P6-T01-CANON-011-RECONCILED-20260926.rvt`

## Writer lease

- Status: `NOT_ACQUIRED` (project lock file absent)
- Both current runner attempts failed at `horizun_health` before lease acquisition. Historical owner PID 28364 is not current evidence.
- Do not manually create, release, or reclaim a lease; the next attempt is through the production runner in the user context that owns the discovery ACL.

## Git verification

Current continuation: implementation commit `73f71e0c15bb169d88729c0530bffafc975a81c0` and state/handoff commit `821b2aa92697a0dab71fe79a0dce8699f3e4ba60` are pushed to `origin/main`; a fresh `git ls-remote origin refs/heads/main` returned the latter SHA. P7-T01 is still blocked; these commits contain no Revit model write.

P7-T01 health-schema/transport-pin commit `f25b5e9080b2c4a9b5994bec918743c584ad00cb`
is pushed to `origin/main`; a fresh `git ls-remote` matched. It contains the
strict health validator, pinned transport lifecycle, regression tests and
pending-task state only. No Revit model write occurred in that commit.

P6 PASS commit `13a2581aa13b2a580fc20fa9d5b27e3009569edd` was pushed from `main`;
`git ls-remote origin refs/heads/main` returned the same SHA. The R05 runner
and regression-test checkpoint `0848cd199ff4905abe0bcbf1ae7f857511c22c20` is
also on `main`; its push was verified by `git ls-remote`. It does not mark
P7-T01 PASS: the actual Revit stage is still pending. Preserve the pre-existing
deletions under `revit/lab/exports/p06t14/GOLDEN/RC01/`; they were not staged.

The P6 normalized-study acceptance does not create internal rooms or verify
their areas; R06 owns internal layout and R08 owns Revit Room/area readback. The
current authorization is P7-T01/R05 only; P6-derived wall heights and R05-only
dispatch are implemented. DEC-010 remains historical context. The focused suite passes 81/81 and the R05 dry-run
produces only R05. Persistence compares typed pre-save and post-reopen bounds
as well as identity, and every attempt retains its own journal. A local follow-up
lets the host-profile loader read ACL-blocked selection inputs from committed
Git blobs after a PermissionError without restoring files; missing inputs still
fail closed. The same follow-up narrows the stage grant and planner to exactly
R05 per task and rejects direct R06 preflight. Final independent Luna 6 xhigh
review found no P1/P2 findings; the six R05 modules passed 77/77 and the
expanded combined R05 plus task-state command passed 101/101. The write attempt
was blocked by automatic approval review because the available explicit
authorization then named R04. The current user authorization is P7-T01/R05 only;
later stages require their own task gate. Five host-profile attempts after direct target verification
stopped before P6 baseline readback because a recent second client was still
visible. No R05 write, save, or checkpoint occurred. After health was moved
before target selection, the ~03:36Z attempt reported only PID 40000
(`horizun-mcp`, age 0, alive) and stopped before selection. A follow-up raw
health call showed the authoritative count nested under `clients`; `clients_seen`
includes the caller and any distinct recent clients. The prior positive-count
self-exemption was incorrect and is superseded. Current tests now enforce
nested count handling, count/list consistency, and a zero-other-client gate;
fresh shell/runner/authorization/task-graph tests passed 71/71, YAML parsing
passed 3/3, and `git diff --check` passed. Luna 6 xhigh review is pending. The
corrected gate has not been tried live. A typed close rehearsal confirmed
`is_modified=false` and `would_discard_unsaved=false`; it made no session
change. The stage runner requires save, close-with-save, post-close checkpoint,
exact cold reopen, and complete typed geometry readback.
