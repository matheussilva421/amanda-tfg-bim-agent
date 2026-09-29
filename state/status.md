# Status dashboard

Source: live files in the project workspace. Missing values remain `NOT_RECORDED`.

## Phase and task progress

- Phase: `P7` — detailed-production
- Phase status: `PENDING`
- Next task: `P7-T01` (R05 architectural shell; blocked after failed stage attempt)
- Last recorded task: `P6-T01`
- Tasks: 193 total; P7-T01 is `BLOCKED_BY_TOOL` until live R05 persistence gates pass
- Current authorization: P7-T01/R05 only; authorization ends at R05. Every later stage needs its own task gate; R05 completion does not start R06.
- Current blocker: `R05_STAGE_OPERATIONS_UNRECONCILED:BLOCKING`. Around 00:40-00:41Z on 2026-09-29 the official runner passed health/readiness, zero-other-client, exact RUN-003 target/build/PID 12660, command registry 73/73, provider tools 80/80, MCP tools/list 80, full_write, mcp_paused=false, P6/partial reconciliation, and all eight measured m2 Area/provenance gates. It dispatched R05 and recorded 704 operations: 15 VERIFIED (eight prior floors plus seven new live writes) and 689 FAILED (688 wall-type lookups and one multi-loop service roof). Persistence is null; no save, checkpoint, or independent post-failure readback occurred. The runner released its lease.
- Failure journal: `revit/production/journals/R05-0751bf08af96.json`. Code now resolves wall type ID `250` and splits the multi-loop service roof into four deterministic one-loop patches. Recovery now requires complete typed `horizun_get_dimension_references` edge geometry for all seven writes, including the service-floor courtyard void, planned elevations, matching lower profiles, and vertical edges; model-query Z bounds must agree. No live edge readback has run, so the seven in-memory writes remain unreconciled. Preserve the target active and unsaved; R06 remains NOT STARTED.
- Fresh read-only inspection around 02:37Z found the writer lock absent; Revit PID 3364 has a visible Revit 2027.2 main window, while PID 12660 has no main window. This does not prove provider binding or the active document. Do not use a historical PID; the official runner must dynamically select the process and prove the exact RUN-003 target and readiness. The prior on-disk target record is 5,152,768 bytes with last write `2026-09-27T09:30:38Z`; do not hash while open.
- Offline gates: the focused R05/state suite passed 274 tests, 0 failed, with one unrelated R04 lab-evidence hash case deselected. The official runner dry-run planned only R05 and wrote nothing. Scoped `git diff --check` passed; Ruff retains eight pre-existing findings and no new ones. Fix commit `52e3e81` is pushed. After publishing state revision 252, run one official R05-only attempt with dynamic PID selection. If fresh geometry reconciliation fails, stop without save/close; if it passes, continue the remaining R05 operation and persistence/readback/visual gates. Never execute R06.
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

## Provider health and current R05 recovery

Preferred provider: `horizun`; all model operations must go through the official
production runner. The last live attempt, around 00:40-00:41Z on 2026-09-29,
passed health/readiness, zero-other-client, exact RUN-003 target/build, provider
registries and write controls, P6/partial reconciliation, and all eight measured
m2 Area/provenance gates. It dispatched R05 but failed on 688 wall type lookups
and one multi-loop service roof. Journal:
`revit/production/journals/R05-0751bf08af96.json`. The seven new service-floor
and roof writes remain in-memory and have no independent post-failure readback;
there was no save or checkpoint, and the runner released its lease.

The offline fix commit `52e3e81310c3b4b0134d1d05f271c1c34a22da78` is pushed.
Wall type resolution now uses source-backed ElementId 250, and the service roof
uses four deterministic one-loop patches. Recovery requires complete typed
`horizun_get_dimension_references` edge geometry, including exact identities,
closed horizontal rings and the service-floor courtyard void, elevations within
1 mm, matching top/bottom footprints, vertical edges on the expected profile,
and matching model-query Z bounds. No fresh live edge readback has occurred;
the active blocker remains `R05_STAGE_OPERATIONS_UNRECONCILED:BLOCKING`.

Read-only process/lock inspection around 02:37Z found no writer lock, PID 3364
with a visible Revit 2027.2 main window, and PID 12660 without one. This does not
prove provider binding or the active document. The next invocation must use the
official runner without a pinned PID and dynamically prove the exact target and
readiness. State revision 252 records this boundary. The 600-second quiet window
after the last provider activity has elapsed. Do not hash, save, or close the
target before live recovery; do not start R06.

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
- `R05_PARTIAL_RECOVERY_UNVERIFIED` [RESOLVED, 2026-09-28]: the official runner reconciled exact P6 readback, partial geometry, and all eight measured m2 Area/provenance readings.
- `R05_RESUME_DISPATCH_UNVERIFIED` [RESOLVED, 2026-09-29]: the official runner passed recovery and dispatch gates and entered R05.
- `R05_STAGE_OPERATIONS_UNRECONCILED` [BLOCKING, P7-T01 only]: the failed stage left seven verified but unsaved writes in the open model and 689 operations failed. Reconcile those writes by fresh typed readback before retry.

## Design and Revit recovery

- Selected design: `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`
- Revit stage: `R04`
- Current checkpoint: `revit/production/evidence/AMANDA-RUN-003-R04/P6-T01-CANON-011-RECONCILED-20260926.rvt`

## Writer lease

- Status: `NOT_ACQUIRED` (project lock file absent)
- The latest runner attempt acquired and released the normal lease; the project lock is absent now. It left seven verified stage writes in the still-open in-memory target, with no save or checkpoint. Historical owner PID 28364 is not current evidence.
- Do not manually create, release, or reclaim a lease. Reconcile the live partial first, then use only the official production runner in the current user context that owns the discovery ACL.

## Git verification

Current continuation is state revision 252, based on implementation commit `52e3e81` (`fix(r05): reconcile failed shell writes by geometry`), pushed to `origin/main`. This state/handoff closeout records that fix and the still-open live-reconciliation blocker. The failed official runner left seven unsaved in-memory R05 elements; independent live geometry readback is still required before resuming. RC01 deletions and presentation artifacts remain untouched and outside the scoped closeout.

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
