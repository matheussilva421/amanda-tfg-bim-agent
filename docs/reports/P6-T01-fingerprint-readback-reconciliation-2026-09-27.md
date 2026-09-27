# RUN-003 P6 fingerprint readback reconciliation

**Status:** reconciled for this exact checkpoint readback only. P7-T01/R05 remains pending until the health-first runner completes the live write and persistence gates.

## Evidence

The accepted P6 checkpoint remains `revit/production/evidence/AMANDA-RUN-003-R04/P6-T01-CANON-011-RECONCILED-20260926.rvt`, SHA-256 `8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326`. Its manifest and bytes match. The original accepted fingerprint `4636abc6b294829b` remains unchanged in the P6 evidence.

The exact-checkpoint diagnostic is `revit/production/journals/R05-2f373fcb3511-p6-readback-diagnostic-559bb4edc356.json`, SHA-256 `d2d0cec6bd53c37b211a9eed168a2959009f05ba577cd7f0dd7dce63d73072d6`. It records a compact-query fingerprint of `2f12a578c8451f3f` and a detailed-query fingerprint of `1aac5d79b05b159a`. Both payloads reported 25 readable objects with complete coverage: 7 masses, 14 floors, and 4 roofs.

The detailed typed rows are sorted by ElementId and bound by SHA-256 `3732c3c44c405a6453df8157243b7695b442b9969c979c141c6e829011940c0d`. Validation matched all seven mass bounds and the two administrative floor identities to P6 authority; all five external-area surfaces (260 m² total, PDF authority), three separate access-route bounds, and four one-to-one roofed connector footprints also matched. The connector check confirms plan bounds align, floor tops are at 0 m, roof bounds are 2.9–3.025 m, no enclosing walls exist, and the accepted patio intrusion is zero.

## Reconciliation and limit

The two observed fingerprints differ from the historical fingerprint and from each other while the exact checkpoint SHA and full typed row digest remain fixed. This is consistent with query projection or serialization sensitivity, but the cause is **unresolved**. The historical acceptance value has not been replaced, and the original P6 report, checkpoint, and acceptance record have not been edited.

The additive record `revit/production/evidence/AMANDA-RUN-003-R04/p6-readback-fingerprint-reconciliation.json` allows the production runner to recognize only this precise chain: the same checkpoint path and SHA, both exact observed fingerprints, the diagnostic file hash, 25 complete rows, the row digest, and the P6 geometry invariants above. Any changed fingerprint, checkpoint, diagnostic bytes, row identity, or geometry fails closed. This addendum does not set the original P6 acceptance gate to a new PASS and does not authorize a different checkpoint or design.

No Revit model write, save, or checkpoint occurred during this reconciliation. The next authorized action remains the health-first RUN-003 R05 runner; it must independently confirm the live checkpoint readback and then complete R05 WRITE → READ → VERIFY, save, checkpoint, close/reopen, and final readback before P7-T01 can pass.
