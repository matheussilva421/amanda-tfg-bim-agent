# Amanda TFG — fourth canonical reference handoff

Updated 2026-09-24.

## Source update

- Added the user-provided services/capacitation board as canonical reference 04: docs/source/references/canonical/04_bloco_servicos_capacitacao_canonico.png.
- SHA-256: d440039a9197d20625f321fe67396f571f5e4d8cde39bf4b7f33f9ad28036bd1; 2,165,247 bytes.
- Profile and manifest now declare four canonical references. The loader requires exactly four and verifies each image hash and byte size against the manifest.
- Updated the matrix, visual reference, canonical override, migration spec, and Plan 11.
- Preserve the new board's curved service/capacitation block, central courtyard relationship, covered circulation, public campus access, and separate service/loading access. Its room labels are approximate.
- Official program remains 20 people, 626 m² internal, 260 m² external, 783–814 m² enclosed estimate, and 850–950 m² covered estimate. Record material area reconciliation as CANONICAL_DEVIATION.

## Revit and acceptance state

- No Revit write occurred in this reference update.
- Existing S02 remains the earlier STUDY. Its three-board R04 acceptance and approval binding are stale; do not release S02 to R05.
- Before new geometry: verify the historical R12 archive/hash; run BIM-00 with all four references; take a fresh checkpoint; assign a collision-free solution/run ID. S03 is only a candidate until checked.
- Rebuild R04 and compare it against all four boards. Require fresh CANONICAL_GEOMETRIC_ACCEPTANCE before detailing.
- Required visual gates remain R04/R06/R08/R12/R13/R15. R16 stays blocked until regressions are documented.
- The blank default Nível 1 view screenshot was not acceptance evidence; the prior masses were in R04-CANONICAL-IMPLANTATION.

## Verification

- Focused canonical reference module: 8 passed using Python 3.14, the only installed interpreter.
- The isolated test invocation bypassed package initialization because importing amanda_agent.design.__init__ loads OR-Tools, which is absent here. A normal pytest collection therefore fails before running this module; the isolated focused module passed.
- No full approximately 929-test suite was run.

## Git and resume

- Branch: codex/canonical-pavilion-migration.
- The scoped canonical reference, loader, focused tests, Plan 11/spec, and this handoff are included in this closeout. Existing unrelated runner/layout modifications and generated-run deletions remain unstaged.
- Resume by reconciling source hashes and S02 state, then complete fresh BIM-00 and R04 visual/geometric acceptance before R05.