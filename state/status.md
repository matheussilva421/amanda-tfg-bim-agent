# Status dashboard

Source: live files in the project workspace. Missing values remain `NOT_RECORDED`.

## Phase and task progress

- Phase: `P7` — detailed-production
- Phase status: `PENDING`
- Next task: `P7-T01` (R05 architectural shell; authorization ends at R05; local gates pass, latest runner stopped because Revit was unreachable)
- Last recorded task: `P6-T01`
- Tasks: 193 total; P7-T01 remains PENDING until live R05 write/readback/checkpoint pass
- `P1`: 1/1 PASS
- `P2`: 1/1 PASS
- `P3`: 1/1 PASS
- `P4`: 1/1 PASS
- `P5`: 1/1 PASS
- `P6`: 1/1 PASS
- `P7`: 0/9 PASS
- Latest R05-only runner attempt (2026-09-27 13:11Z) stopped at `horizun_health`, which returned `Error: no Revit is reachable. Is Revit running with the Horizun add-in loaded?` It did not reach capability, targetability, checkpoint, or model gates. The existing RUN-003 lease was retained; no write/save/checkpoint occurred. Retry only after the conservative 13:21:07Z quiet-window end.
- The preceding runner attempt (~12:56Z) passed health/capability, target/lease, P6 checkpoint/digest, and known-floor identity/bounds/level checks, then failed closed on an unsupported typed `Area` unit before R05 writes. Diagnostic `R05-2f373fcb3511-p6-readback-diagnostic-ee99ee2f171a.json` has SHA-256 `edd6f4b86c33fc82705ed8826828ce45d8e7d18475640bb00f6895b08b5de043`, records no model write, and contains the 25-row P6 digest. TDD added supported m²/ft² unit conversions with source-unit evidence and fail-closed rejection for unknown units. Production-runner unit tests pass 87/87; `compileall` and scoped `git diff --check` pass. Ruff reports the same 9 baseline findings, none on changed lines. Luna 6 xhigh review could not start because the app agent-thread limit is full; no other subagent was used. R05 remains `PENDING`; authorization ends at R05.
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

The latest health-first runner call was at about 13:11Z. It failed its first
health gate with `no Revit is reachable`, before capabilities, targetability,
checkpoint inspection, or model access. The existing RUN-003 lease was
retained, and no model write/save/checkpoint occurred. The conservative
10-minute quiet window ends at 13:21:07Z; no direct Horizun calls should be made.

The user's explicit authorization covers RUN-003 P7-T01/R05 and ends at R05.
The local retry path now compares the eight existing floor rows with current
R05 plan identity, XY bounds, Area, and level, filters only those exact
operations, and merges their records into stage verification. The typed query
contract does not expose floor-outline vertices; exact contour equality is not
claimed. The preceding ~12:56Z live attempt passed those checks but rejected an
unsupported typed `Area` unit before R05 writes; the local parser now converts
known m²/ft² aliases and rejects unknown units. Its focused runner suite passes
87/87. P7-T01 remains `PENDING` until live R05 and persistence gates pass.

The additive record
`revit/production/evidence/AMANDA-RUN-003-R04/p6-readback-fingerprint-reconciliation.json`
binds the exact checkpoint SHA, prior diagnostic SHA, both observed query
fingerprints, and the 25-row identity/geometry digest. The runner will require
those exact values, current compact/detailed bounds agreement, and geometry
relations against the P6 spatial evidence. The historical P6 acceptance remains
unchanged; the fingerprint cause is unresolved. Earlier focused
production/state/provider suite plus state-consistency and plan-order gates:
227/227. Current scoped gates: production runner 87/87, repository hygiene
12/12, task-graph/status consistency 17/17, YAML parsing, and `compileall`
passed. Ruff reports the same 9 pre-existing
findings; changed lines add no finding. Local second-pass review found no
additional acceptance-path issue. The requested Luna 6 xhigh review could not
spawn because the app agent-thread limit is full; no other subagent was used.
Next action is the health-first R05-only runner.
The reconciliation/state commits are pushed through `170cb4f`; a subsequent
`git ls-remote` could not reach GitHub over TCP 443. The explicit R05
authorization and current resume route are recorded in the active handoff.
P7-T01 remains PENDING.

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
no cadastral/north/site-availability claim is made. DEC-010 records conditional
authorization for the bounded RUN-003 R05–R13 sequence after P6 PASS; the user
has since explicitly authorized that sequence. Independent Luna 6 xhigh review
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

## Design and Revit recovery

- Selected design: `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`
- Revit stage: `R04`
- Current checkpoint: `revit/production/evidence/AMANDA-RUN-003-R04/P6-T01-CANON-011-RECONCILED-20260926.rvt`

## Writer lease

- Status: `HELD_FOR_P7`
- Owner: `amanda-P7-RUN003-production` (PID 28364, alive)
- Fencing generation: `2`

## Git verification

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
bounded P6/DEC-010 RUN-003 authorization, P6-derived wall heights, and R05-only
dispatch are implemented; the focused suite passes 81/81 and the R05 dry-run
produces only R05. Persistence compares typed pre-save and post-reopen bounds
as well as identity, and every attempt retains its own journal. A local follow-up
lets the host-profile loader read ACL-blocked selection inputs from committed
Git blobs after a PermissionError without restoring files; missing inputs still
fail closed. The same follow-up narrows the stage grant and planner to exactly
R05 per task and rejects direct R06 preflight. Final independent Luna 6 xhigh
review found no P1/P2 findings; the six R05 modules passed 77/77 and the
expanded combined R05 plus task-state command passed 101/101. The write attempt
was blocked by automatic approval review because the available explicit
authorization then named R04. The user's later RUN-003 R05-R13 authorization
supersedes that hold. Five host-profile attempts after direct target verification
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
