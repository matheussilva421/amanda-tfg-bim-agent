# Legacy layout builder reference classification

Search performed on 2026-09-23 with `rg -n "build_courtyard_layout" src scripts`.
Private `docs/source/` inputs are excluded from Git and are not needed for this
code-reference classification.

## Executable references

| File | Classification | Reason / boundary |
| --- | --- | --- |
| `src/amanda_agent/design/architectural_layout.py` | LEGACY implementation/export | The sole code definition and export of `build_courtyard_layout`; kept for historical comparison and adapter coverage, not an active production source. |
| `scripts/run_amanda_production.py` | MIGRATED canonical production entrypoint | Resolves `CanonicalPavilionLayout`; the active script has no reference to `build_courtyard_layout`. Its dry mode cannot acquire the writer lock or invoke a provider. |
| `tests/unit/test_architectural_layout.py` | LEGACY unit coverage | Tests the retained legacy builder contract. |
| `tests/unit/test_canonical_qa.py` | LEGACY negative control | Confirms the old single-bar layout fails canonical parti checks. |
| `tests/unit/test_layout_protocol.py` | LEGACY adapter coverage | Exercises the compatibility adapter from the old courtyard model to the shared protocol. |
| `tests/unit/test_production_layout_bim.py` | LEGACY fixture; Task 7 migration boundary | Keeps historic compiler coverage paired with `build_legacy_selection`; Task 7 replaces the BIM planning fixture with canonical multi-block cases. |
| `tests/unit/test_production_selection.py` | LEGACY history coverage | Builds the old layout only to prove it cannot become the active selection. |

The literal in `tests/unit/test_qa_layout_script.py` is a guard assertion that the active QA/drawing entrypoints do not import or call the legacy builder; it is not an executable builder reference.

## Policy/documentation references

The historical migration plan, preserved in Git history, and this report
mention the legacy builder as a migration rule. They do not execute it.

## Migrated active consumers

`scripts/run_amanda_production.py`, `scripts/qa_layout.py`, `scripts/render_study_sheets.py`, and the IFC/DXF exporters have no direct legacy builder import or call. The study PDF packager accepts only the normalized canonical implantation and two floor-plan previews, and refuses a stale pre-canonical QA report. The search finds only the legacy module's definition and its `__all__` export in `src/`; there are zero matches in `scripts/`.

## Gate status

The canonical preview is a normalized study diagram, not a visual regression pass. `CANON-011` remains BLOCKED until R04, R06, R08, R12, R13 and R15 have reviewed results tied to the three canonical board hashes. The historical linear R12 RVT remains hash-frozen and cannot be used as the new BIM base. See `MIGRATION_VERIFICATION.md` for current Task 10 test and dry-plan evidence.
