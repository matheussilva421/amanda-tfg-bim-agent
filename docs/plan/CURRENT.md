# Amanda TFG BIM Agent — Current Implementation Plan

## P0 — Repository Recovery (complete)

Repository recovery closed on 2026-09-24. The recovery report records branch consolidation, preservation tags, the single worktree, document migration, source/evidence/RVT retention, focused validation, and remote verification. No Revit/model action occurred during P0.

## P1 — Four-board reconciliation (P1-T01 complete)

P1-T01 binds exactly the four canonical boards and reconciles implantation, administration floors, residential pavilion membership, the curved service/capacitation courtyard, child-sector contents, and the official program. Its report records unresolved board-to-program differences without changing official areas. No Revit work or new solution identity was created.

## P2 — New canonical solution (P2-T01 complete)

P2-T01 assigned `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`, bound to exactly the four current canonical board hashes, the official program PDF hash, and the P1-T01 reconciliation report identity. The machine-readable record is `project/requirements/canonical-solution-identity.yaml`; `PROJECT_STATE.selected_design` remains null. This identity-only task created no layout or approval hash and authorized no BIM-00 or Revit write.

## P3 — Canonical QA and approval

P3-T01 generated offline candidate `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`, bound to the four boards, official program PDF, and P1-T01 report. The focused gate passed 74 tests; emitted QA is 17 PASS, 0 FAIL, CANON-011 BLOCKED. Direct builder calls revalidate the persisted identity against live sources, and the QA guard requires unique CANON-001..018 IDs. Independent re-review closed both code findings; final state review found no critical/important findings and its minor phase-edge test gap is closed. The candidate stays provisional, unselected, and ineligible for BIM; no Revit call or R04/R05 work occurred. Evidence: `docs/reports/P3-T01-canonical-qa-and-approval.md`.

## P4 — BIM-00

`P4-T01` establishes BIM-00 evidence and can authorize only the exact new
solution and target; it depends on P3-T01 and excludes R04/R05. Its evidence
must bind the `solution_id`, `layout_hash`, content `approval_hash`, exactly
four canonical board hashes, official program PDF SHA-256, target RVT path and
SHA-256, a separate checkpoint path and matching SHA-256, repository commit
SHA, and the `PROJECT_STATE.yaml` revision and raw-file SHA-256. Each binding
is compared to the active expected value; an unbound or mismatched value fails
closed. Required live checks include the writer lease, checkpoint, historical
R12 exclusion, canonical references, capability registry, Revit provider,
units, site-coordinate mode, family strategy, canonical selection, and
official program source. BIM-00 is an evidence/authorization gate only; it
does not execute an R04/R05 operation.

**Completed status (2026-09-26):** `P4-T01` passed BIM-00 against the exact
RUN-003 target, pre-R04 checkpoint, canonical sources, program, repository
commit, and state revision. `P5-T01` then wrote seven real Revit masses and
completed separate query/readback, save, POST-R04 checkpoint, close, cold
reopen, and fresh post-reopen queries. The detail is in
`docs/reports/P5-T01-run003-r04-real-model.md` and
`revit/production/evidence/AMANDA-RUN-003-R04/real-model-evidence.json`.
P5 is `PASS_WITH_WARNINGS`: Python geometry readbacks are explicitly
`self_reported_verified` (`host_verified=false`), while typed queries confirmed
all seven identities and bounding boxes both before and after reopen. One
sub-tolerance service-profile vertex was omitted within measured Revit
ShortCurveTolerance; six courtyard rings remain, and the measured area delta is
0.00000148 m². Both attempted visual captures rolled back; neither yielded a
usable artifact, so CANON-011 remains open.

Live closeout confirmed Horizun 1.3.3 healthy, Revit 2027 build 27.2.0.39,
clean 73/73 command registry, RUN-003 active as the sole open document, and no
other clients. The exclusive RUN-003 lease was released after persistence
verification. Save returned target SHA-256
`120935963a19af4c654894d00f057304237ec7f98115f0eecb266e3a91aaef20`; the
checkpoint file and manifest were independently rehashed and match. Direct file
hashing of the working RVT was denied while Revit held it open; cold reopen and
fresh typed queries verified the target contents.
Coordinates remain local normalized and unsurveyed; floor heights remain
provisional. All five site-data blockers remain open. No R05 operation occurred.
## P5 — R04 Revit

`P5-T01` is complete with `PASS_WITH_WARNINGS`; see the execution evidence
above. `P6-T01` is next: compare the saved R04 geometry to all four canonical
boards and close CANON-011. Revit visual acceptance is still pending because
the available capture attempts did not produce a usable image. R05 remains
blocked until P6 passes and is not authorized by this continuation.

## P6 — R04 visual/geometric acceptance

Compare real Revit output to all four boards. R05 is blocked until PASS.

## P7 — Detailed production

Run R05 through R13 with required regression gates.

## P8 — QA/RC

Run R14, R15 cold reopen, and exports.

## P9 — GOLDEN

Run R16 only after every required gate and documented deviation passes.

P0 through P5-T01 are closed. `PROJECT_STATE.yaml` and `state/task-graph.yaml`
point to P6-T01 as the next task. Historical plans are archive material in Git
history, not a second instruction source.
