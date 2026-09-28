# Status dashboard

Source: live files in the project workspace. Missing values remain `NOT_RECORDED`.

## Phase and task progress

- Phase: `P7` — detailed-production
- Phase status: `PENDING`
- Next task: `P7-T01` (R05 architectural shell; blocked at partial recovery verification)
- Last recorded task: `P6-T01`
- Tasks: 193 total; P7-T01 is `BLOCKED_BY_TOOL` until live R05 persistence gates pass
- Current authorization: P7-T01/R05 only; authorization ends at R05. Every later stage needs its own task gate; R05 completion does not start R06.
- Current blocker: `R05_PARTIAL_RECOVERY_UNVERIFIED:BLOCKING`. The 22:34:27Z live takeoff reported the English Area parameter state=absent for ElementId 331188; localized Área has not yet been queried live by the updated runner.
- Read-only process inspection classified PID 12660 as Revit 2027 with RevitAPI and Horizun loaded and a usable window handle. PID 3364 has neither module nor a window handle and remains untouched. The next official runner must freshly verify the active exact RUN-003 target.
- The official runner in the elevated current-user context passed live health, zero-other-client, exact target/build/PID 12660, command registry 73/73, provider tool registry 80/80, MCP tools/list 80, full_write, and mcp_paused=false at 22:21:31Z and 22:34:27Z. This resolves the sandbox discovery blocker; the discovery token was not read.
- The runner entered guarded recovery because the live model did not match the accepted P6 element count. Its diagnostic-only P6 readback contains 25 rows and complete coverage. English Area was absent with unit m2 and no measured value/provenance. No value or unit was inferred. No model save, R05 write, or checkpoint occurred; the runner released its lease. The open RUN-003 target remains 5,152,768 bytes with the prior 2026-09-27 mtime; do not hash or close it.
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
(version 1.3.3.0). At 22:21:31Z and 22:34:27Z the official runner reported command
registry 73/73, provider tools 80/80, MCP tools/list 80, full_write and
mcp_paused=false. Its exclusive-client and exact-target gates passed. Sandboxed
attempts failed discovery because the owner-only discovery ACL is unreadable in
that context; its token was not read. Do not route model writes through another
client. RUNNER_TRANSPORT_UNREACHABLE is resolved; the active gate is
`R05_PARTIAL_RECOVERY_UNVERIFIED:BLOCKING`.

The known partial entered guarded recovery after the live model failed the
accepted P6 element-count check. The 22:34:27Z exact eight-floor takeoff reported
English Area state=absent, unit=m2, value_type=None, and no measurement provenance
for ElementId 331188. The latest diagnostic is
revit/production/journals/R05-2f373fcb3511-p6-readback-diagnostic-8d2a63c9f246.json.
The 600-second quiet window ended at 22:44:27Z. Local code queries Area and
localized Área separately, uses Área only when Area is explicitly absent, and
requires provenance and measured m2; when both are measured, decimal values
must agree within an inclusive 0.01 m2. The exact-boundary path through geometry
validation and the just-over rejection pass locally. Combined focused R05/state
gates: 183 passed, 1 unrelated R04 evidence-hash test deselected, 0 failed.
Independent read-only re-review found no findings. Ruff has eight pre-existing
findings and no new findings on the changed lines. Implementation, tests, and
the diagnostic are committed as
`1df883bb4cbf6fbe8bd75481019c55214449cc3e`; formal state revision 249 points to
that commit, and its closeout commit is still pending. Do not use geometry_area
as a floor-plan substitute. Before the next call, commit the current state and
handoff, try the normal GitHub push, recheck PID 12660 and the lock, and use only
the exact R05 production runner.

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
- `R05_PARTIAL_RECOVERY_UNVERIFIED` [BLOCKING, P7-T01 only]: guarded recovery found English Area state=absent for ElementId 331188; localized Área still needs live measured-m2 confirmation. No R05 write/save/checkpoint occurred.

## Design and Revit recovery

- Selected design: `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`
- Revit stage: `R04`
- Current checkpoint: `revit/production/evidence/AMANDA-RUN-003-R04/P6-T01-CANON-011-RECONCILED-20260926.rvt`

## Writer lease

- Status: `NOT_ACQUIRED` (project lock file absent)
- The latest runner attempt acquired and released the normal lease; the project lock is absent now. Historical owner PID 28364 is not current evidence.
- Do not manually create, release, or reclaim a lease; the next attempt is through the production runner in the current user context that owns the discovery ACL.

## Git verification

Current continuation at state revision 248 is based on HEAD `0308605d77184e9661fd2a21f618234bc8a8f2d5`. Local implementation/tests and the current handoff/dashboard update are not yet committed. The latest `git ls-remote` failed because GitHub port 443 was unreachable; push state is unverified. No Revit model write occurred.

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
