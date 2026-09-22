# Status dashboard

Source: live files in the project workspace. Missing values remain `NOT_RECORDED`.

## Phase and task progress

- Phase: `PHASE_08` — amanda-production-run
- Phase status: `PENDING`
- Next task: P08-T12
- Last PASS task: P08-T11 (PASS_WITH_WARNINGS)
- Tasks: 159 total; READY: P08-T12
- `PHASE_00`: 3/3 PASS
- `PHASE_01`: 13/13 PASS
- `PHASE_02`: 20/20 PASS
- `PHASE_03`: 15/15 PASS
- `PHASE_04`: 22/22 PASS
- `PHASE_05`: 23/23 PASS
- `PHASE_06`: 15/15 PASS
- `PHASE_07A`: 11/11 PASS
- `PHASE_07B`: 6/8 PASS
- PHASE_08: 11/19 PASS_WITH_WARNINGS
- `PHASE_09`: 4/10 PASS

## Environment

- Revit build: `27.2.0.39`
- Revit product version: `20260716_1515(x64)`

## Provider health

- Preferred provider: `horizun`
- `custom-api`: AVAILABLE (fallback-last-resort)
- `horizun-revit-mcp`: HEALTHY (primary)
- `revitcortex`: HEALTHY (fallback-typed)

## Capability counts

- PASS: 13
- FAIL: 0
- UNTESTED: 0

## Blockers

- `SITE_TOPOGRAPHY` [BLOCKING]: verified survey or topographic elevations for the lot
- `SITE_BOUNDARY` [BLOCKING]: surveyed or cadastral polygon in a stated coordinate system
- `SITE_OCCUPANCY` [BLOCKING]: confirmation of the current use of the lot and of the relocation premise for the police company unit
- `SITE_FRONTAGE_COUNT` [DEGRADING]: whether the lot has three or four frontages
- `SITE_TRUE_NORTH` [DEGRADING]: a verified true-north bearing with a source drawing datum

## Design and Revit recovery

- Selected design: `AMANDA-RUN-001-S01`
- Revit stage: R07
- Current checkpoint: revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R07-openings-20260922.rvt
- R07 live: 87 openings (52 doors, 35 windows), saved/closed/reopened/requeried; real STUDY preview preserved

## Writer lease

- Status: `FREE`
- Owner: `NOT_RECORDED`
- Fencing generation: `NOT_RECORDED`

## Git verification

- Last verified commit: `2a51cdb`
- Observed HEAD: `17b189c0d2a31bd0cdfcc223e9ca0668aefbe4e0`
