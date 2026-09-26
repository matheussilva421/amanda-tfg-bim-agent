# Status dashboard

Source: live files in the project workspace. Missing values remain `NOT_RECORDED`.

## Phase and task progress

- Phase: `P4` — bim-00
- Phase status: `RUNNING`
- Next task: `P4-T01`
- Last recorded task: `P3-T01`
- Tasks: 182 total; READY: (none)
- `P1`: 1/1 PASS
- `P2`: 1/1 PASS
- `P3`: 1/1 PASS
- `P4`: 0/1 PASS
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

- Preferred provider: `horizun`
- `custom-api`: AVAILABLE (fallback-last-resort)
- `horizun-revit-mcp`: UNREACHABLE (primary)
- `revitcortex`: NOT_PROBED_THIS_SESSION (fallback-typed)

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
- Revit stage: `PRE_R04`
- Current checkpoint: `revit/production/checkpoints/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY-PRE-R04.rvt`

## Writer lease

- Status: `HELD`
- Owner: `amanda-P4-T01-RUN003-R04`
- Fencing generation: `2`

## Git verification

- Last verified commit: `21848db0d5eb2defd2cfb5baffbe9e057b004a4e`
- Observed HEAD: `21848db0d5eb2defd2cfb5baffbe9e057b004a4e`
