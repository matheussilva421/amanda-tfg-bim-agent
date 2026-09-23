# Legacy layout builder reference classification

Search performed on 2026-09-22 with `rg --hidden`, excluding Git internals and private `docs/source/` inputs.

## Executable references

| File | Classification | Reason / boundary |
| --- | --- | --- |
| `scripts/run_amanda_production.py` | ACTIVE, migration pending Task 8 | Still constructs the legacy layout. The active selection builder rejects it before any BIM write; do not invoke this runner until Task 8 migrates it. |
| `src/amanda_agent/design/architectural_layout.py` | LEGACY implementation | Kept for historic comparison and adapter coverage. It is not an eligible production source. |
| `tests/unit/test_architectural_layout.py` | LEGACY unit coverage | Tests the retained legacy builder contract. |
| `tests/unit/test_canonical_qa.py` | LEGACY negative control | Confirms the old single-bar layout fails canonical parti checks. |
| `tests/unit/test_layout_protocol.py` | LEGACY adapter coverage | Exercises the compatibility adapter from the old courtyard model to the shared protocol. |
| `tests/unit/test_production_layout_bim.py` | LEGACY fixture; Task 7 migration boundary | Keeps historic compiler coverage paired with `build_legacy_selection`; Task 7 replaces the BIM planning fixture with canonical multi-block cases. |
| `tests/unit/test_production_selection.py` | LEGACY history coverage | Builds the old layout only to prove it cannot become the active selection. |

The literal in `tests/unit/test_qa_layout_script.py` is a guard assertion that the active QA/drawing entrypoints do not import or call the legacy builder; it is not an executable builder reference.

## Policy/documentation references

`docs/superpowers/plans/11-canonical-pavilion-migration.md` and this handoff mention the legacy builder as a migration rule. They do not execute it.

## Migrated active consumers

`scripts/qa_layout.py`, `scripts/render_study_sheets.py`, and the IFC/DXF exporters have no direct legacy builder import or call. The study PDF packager accepts only the normalized canonical implantation and two floor-plan previews, and refuses a stale pre-canonical QA report. Task 8 remains responsible for the production runner.

## Gate status

The canonical preview is a normalized study diagram, not a visual regression pass. `CANON-011` remains BLOCKED until R04, R06, R08, R12, R13 and R15 have reviewed results tied to the three canonical board hashes. The historical linear R12 RVT remains hash-frozen and cannot be used as the new BIM base.
