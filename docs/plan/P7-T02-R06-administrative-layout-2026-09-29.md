# P7-T02 / R06 — Administrative layout implementation plan

Date: 2026-09-29  
Status: PREPARED / NOT AUTHORIZED TO EXECUTE UNTIL P7-T01 PASS  
Tracking: https://github.com/matheussilva421/amanda-tfg-bim-agent/issues/1

## Purpose

Implement the administrative internal layout after the R05 architectural shell is proven saved, checkpointed, cold-reopened and read back. The detailed source record is `docs/inputs/2026-09-29-amanda-administrative-layout.md`.

## Hard prerequisites

- P7-T01 / R05 = PASS.
- `revit_stage = R05`.
- R05 checkpoint hash verified.
- R05 post-reopen typed readback PASS.
- Current spec/plan/DEC-011 loaded.
- No unresolved canonical deviation affecting the admin shell dimensions.

## Authority

- Official room quantities/areas: official program PDF.
- Spatial organization: four canonical boards + P1 reconciliation.
- Administrative dimensional direction: Amanda 2026-09-29 input / DEC-011.
- Dark CAD sketch: adjacency reference only where non-conflicting.

## Implementation sequence

1. **Baseline readback**
   - query the R05 admin shell on both levels;
   - verify 20 × 10 m study envelope or record the actual verified shell bounds;
   - verify Level 1 and Level 2 relationships;
   - snapshot existing wall/void/core geometry.

2. **Ground-floor layout**
   - place internal partitions for the twelve official spaces listed in the source input;
   - keep psychology, social work, legal service, meeting, reception/intake sequence and the official support spaces on ground;
   - preserve protected entrance, corridor, stair and elevator/core;
   - do not add the sketch DML.

3. **Upper-floor layout**
   - place coordination, secretary/admin, team, staff dining/copa, multiuse/groups and staff sanitary/vestiary;
   - create the 5 m² upper support/archive only as derived architectural support, never as a duplicate official REQ-04-06;
   - preserve the 10 m² veranda as semi-open/non-official internal useful area;
   - preserve stair/elevator/core.

4. **Dimension reconciliation**
   - treat Amanda dimensions as nominal clear-space targets;
   - reconcile them against wall thickness, core/circulation and shell geometry;
   - record actual clear dimensions and area deltas without changing official target areas to make the model pass.

5. **Independent readback**
   - verify partition IDs, levels, bounds and room-boundary topology;
   - verify no official requirement is duplicated or omitted;
   - verify derived support and veranda are classified separately from official internal rooms.

6. **Visual QA**
   - ground-floor plan;
   - upper-floor plan;
   - admin section showing both levels;
   - compare against Board 02 and Amanda direction.

7. **Persistence**
   - SAVE → checkpoint → CLOSE → exact REOPEN → typed readback.
   - R06 only reaches PASS after persistence/readback evidence.

## Scope guard

R06 creates internal layout/partitions. It must **not** pull work forward from:

- R07: hosted doors, windows and openings;
- R08: formal Revit Rooms and official area schedule;
- R10: furniture/equipment.

Simple temporary analytical markers may be used only if the existing stage contract allows them and they are removed/reconciled before PASS.

## Acceptance

- all twelve official ground-floor spaces are topologically represented once;
- six official upper-floor spaces are represented once;
- the upper derived support is not counted as a second official archive;
- veranda remains semi-open and outside official 626 m² internal useful total;
- public/technical sequence stays ground; coordination/staff/group functions stay upper;
- dimension targets are traceable to Amanda's input;
- no DML is introduced into admin ground from the non-authoritative sketch;
- typed post-reopen evidence is complete;
- tests and task/state evidence pass.
