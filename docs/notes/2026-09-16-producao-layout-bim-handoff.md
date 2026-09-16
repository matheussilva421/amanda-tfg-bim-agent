# Handoff - production architectural layout and its BIM driver (2026-09-16)

## What this session produced

The repository could plan Revit stages but had nothing to plan FROM: the design
engine stops at macrozone strips, so no wall, door, room or sheet could be
described and P08-T08 had no input. This session closed that gap with two new
modules and one production decision.

### 1. The architectural plan (src/amanda_agent/design/architectural_layout.py)

A single-storey double-loaded bar with a protected patio. It consumes the
canonical programme and returns exact metric geometry.

Measured result on project/requirements/program.json:

| quantity | value |
| --- | --- |
| programmed rooms placed | 52, every one at its canonical target area |
| net internal | 626.00 m2 (exact; no room stretched) |
| gallery (circulation) | 133.68 m2 at 1.50 m wide |
| partitions | 25.20 m2 |
| enclosed built area | 784.88 m2, inside the programme 783-814 m2 estimate |
| construction footprint | 808.38 m2 to the outer face |
| protected patio | 703.60 m2 |
| content hash | deterministic over rooms, gallery, patio and parameters |

The typology is a MEASURED decision, not a preference: a courtyard of two
separate wings, built from the same rooms with a gallery of the same width,
measures about 1050 m2 enclosed, roughly 30 percent over the adopted budget,
because it needs a second full gallery and a second set of external walls. Both
alternatives are recorded in the decision register.

### 2. The BIM driver (src/amanda_agent/production/layout_bim.py)

Turns that plan into R01-R13 stage plans. It is a pure function: no Revit, no
capability promotion, and no approximated operation. A capability the registry
cannot prove raises instead of being substituted.

Planned chain, measured:

| stage | operations | contents |
| --- | --- | --- |
| R01 | 1 | project on the installed template |
| R02 | 0 | no verified topography: records blockers, invents no ground |
| R03 | 4 | 1 level, 2 grids, 1 reference |
| R04 | 1 | massing surrogate of the footprint |
| R05 | 181 | 178 walls, floor, slab, roof |
| R06 | 30 | internal walls between neighbouring rooms |
| R07 | 87 | 52 doors onto the gallery, 35 windows on outer faces |
| R08 | 52 | rooms, reconciled to 626.00 m2, capacity 20 |
| R09 | 53 | accessible routes and the measured gallery width |
| R10 | 243 | furniture for 20 people |
| R11 | 25 | 5 landscape zones summing 260.00 m2 |
| R12 | 178 | a material per wall |
| R13 | 57 | 11 views, 4 tables, 5 sheets, viewports, dimensions, tags |

### 3. The selection record (src/amanda_agent/production/selection.py)

DETAILED_BIM requires a content-bound selection, and that gate is real. The
module produces a decision (DEC-P08-T09-SELECTION-001) and a DesignSolution
whose approval hash binds the geometry. Both are AGENT_DELEGATED with
AMANDA_REVIEW_PENDING; neither claims Amanda's personal approval.

## Files

Created:

- src/amanda_agent/design/architectural_layout.py
- src/amanda_agent/production/__init__.py
- src/amanda_agent/production/layout_bim.py
- src/amanda_agent/production/selection.py
- tests/unit/test_architectural_layout.py (15 tests)
- tests/unit/test_production_layout_bim.py (14 tests)
- docs/reports/p08-layout-study.png (review preview)

Changed:

- src/amanda_agent/bim/stages/project.py - template discovery now finds the
  stock Revit templates. It previously searched only for names containing
  architect/arquitet, and the stock templates are named Default_M_PTB.rte and
  similar, so R01 could never be planned on this machine.
- tool-lab/topologic/spike.py - the spike publishes a BLOCKED OBJ export with
  its cause instead of dying, and keeps library diagnostics off stdout so the
  report stays parseable. Offline, the topologicpy writer asks PyPI for its own
  version and raises when the answer is missing.
- project/requirements/decision-register.yaml and decisions.yaml - the two
  delegated T08 decisions (DEC-P08-T08-TYPOLOGY-001 and
  DEC-P08-T08-SITE-BOUNDARY-001), both superseding their T04 study versions.
- state/design-run-freeze.yaml - re-bound after the register changed, with the
  reason recorded.

## Tests

    .\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q

- 853 passed, 0 failed (was 1 failed, 822 passed before the change).
- 29 of those are the new layout and driver contracts.

## Not done, and deliberately so

- No Revit write yet. Revit 2027 build 27.2.0.39 is running with
  revit/lab/baseline/LAB_R00_EMPTY.rvt, and horizun reports HEALTHY with
  contract hash 8b9600f5274d7dffb6e5bd5f, but no stage has been executed
  against a model. Executing the chain is the next task.
- No RVT, IFC, PDF, DWG or preview of the real model exists. The only GOLDEN
  package is the synthetic fixture under revit/lab/exports/p06t14/.
- Site topography, boundary, occupancy, frontage count and true north remain
  blocking or degrading. R02 writes nothing because of it, and the FINAL
  profile stays blocked.
- P08-T08 to P08-T19 remain PENDING in state/task-graph.yaml.

## Exact resume point

1. Acquire state/locks/revit-writer.lock.
2. Execute the planned chain against
   revit/production/working/AMANDA_WORKING_001.rvt, stage by stage, with
   WRITE then READ then VERIFY and a checkpoint after each stage.
3. Run the R14 QA, build the R15 release candidate, cold-reopen it, and export.

## Working notes for whoever continues

- The phantom D entries under revit/lab/exports/p06t14/GOLDEN/RC01 in git
  status are the known broken-ACL artefact recorded as P-01. They are not real
  deletions. Never git add those paths and never git restore them.
- Wall logical ids must stay derived from the same endpoint digest the shell
  stage uses, or an opening will name a host that does not exist in the model.
- python -m pytest needs a unique --basetemp on this machine; the sandbox
  leaves restrictive ACLs on reused temporary directories.
## Addendum 5: IFC and DXF exports

Two more deliverable formats are now produced from the same plan, each behind
its own behavioural tests (13 new tests, all passing).

### IFC (src/amanda_agent/production/ifc_export.py)

A real IFC4 STEP file, written with ifcopenshell:

| entity | count |
| --- | --- |
| IfcProject / IfcSite / IfcBuilding / IfcBuildingStorey | 1 each |
| IfcSpace | 52, one per programmed room, each named with its logical id |
| IfcWall | 48 |
| IfcDoor | 52 |
| IfcWindow | 35 |
| IfcSlab | 2 |

docs/reports/study-exports/AMANDA_ESTUDO.ifc, 121,496 bytes. It was checked
three ways rather than asserted: the project's own validator returns PASS, all
52 spaces carry readable solid geometry through ifcopenshell.geom, and the first
space measures 2.38 x 4.20 m against its 10.00 m2 target.

One real API detail cost time and is worth recording: IFC4 gives IfcSpace no
ContainedInStructure inverse, so assign_container refuses a space and the
spatial structure must be written as IfcRelAggregates. The file is valid only
because the spaces decompose the storey.

### DXF (src/amanda_agent/production/dxf_export.py)

An AutoCAD R12 ASCII DXF written directly, 27,020 bytes, on seven layers
(walls, rooms, gallery, veranda, patio, openings, text), in metres via
$INSUNITS. 52 room labels, 87 opening marks.

A DWG needs Revit or a licensed CAD kernel, so DWG is not claimed: the export
report says in writing that this is a DXF and that the project's DWG validator
judges a DWG only when a real one exists.

Both exports carry the layout content hash and are deterministic across runs.

### What these are not

Neither is the model export. P08-T17 must still export IFC, PDF and DWG from the
real RVT once the bridge is reachable. These are the STUDY exports of the
delegated architecture: real files, validated, openable in a BIM viewer, and
traceable to the plan the model will be built from.

