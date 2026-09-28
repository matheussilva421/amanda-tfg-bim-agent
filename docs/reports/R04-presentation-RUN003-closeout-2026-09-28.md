# RUN-003 R04 presentation closeout

Date: 2026-09-28
Scope: supplemental presentation work from the accepted P6 checkpoint. No P7/R05 or R06 work was performed.

## Reconciliation and evidence

- Source geometry: `revit/production/evidence/AMANDA-RUN-003-R04/P6-T01-CANON-011-RECONCILED-20260926.rvt`, SHA-256 `8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326`.
- Presentation derivative: `revit/production/presentation/RUN-003-R04-ORIENTACAO-20260928/AMANDA-RUN-003-R04-PRESENTATION-20260928.rvt`. Its saved checkpoint is `snapshots/AMANDA-RUN-003-R04-PRESENTATION-FINAL-20260928.rvt`, SHA-256 `45bac6f94fc8fec465ea52c20fe6cd5a37c8159466a19fcff0b1eb329dc19d4b` (5,009,408 bytes). The model was cold-closed and reopened with Revit 2027 audit, with no upgrade.
- Fresh post-reopen readback compared the 25 baseline spatial objects row by row: 7 masses, 14 floors, 4 roofs; same ElementIds, UniqueIds, categories, names, and bounding boxes at 1e-8 m tolerance; 0 differences, 0 unreadable rows, complete coverage. Horizun query fingerprint: `1aac5d79b05b159a`.
- Sheet `R04-01` (ElementId 331392) is `R04 Prancha de implantação e orientação`, A1 metric title block (type 4428), with one implantation viewport and 29 text notes. The notes map sectors A–M and reconcile the 20-person, 626 m² internal / 260 m² external official program without adopting service-board areas as official areas.
- Export packet: one A1 sheet PDF, six one-page A3 view PDFs, and six PNG captures. All PDFs were rendered and visually reviewed; the A1 page is 841 × 594 mm and does not exceed its title block. The infant view was recaptured with a temporary focus on mass 328658 and playground floor 329971; the view was restored after capture.
- Provider evidence at cold reopen: Horizun 1.3.3 HEALTHY, Revit 2027 build 27.2.0.39 / PID 9128, active path matched, registry 73/73, tools 80/80, zero other clients.

## Limitations and decisions

- These are presentation and orientation views of conceptual massing. Interior partitions, doors/windows, furniture, playground equipment, and detailed construction are not represented by this packet.
- The child plan export shows the child mass and playground surface as simple outlines; the focused PNG shows both surfaces more clearly. The A1 legend identifies the relationship.
- The Autodesk A1 title block retains generic consultant/project placeholder fields. Site coordinates remain locally normalized; no cadastral boundary, topographic survey, or true north is claimed.
- No GeoNatal research, RC01 change, P6 source edit, writer-lease release, P7/R05 write, or R06 work occurred. S01/S02/R12 were not reused.

## State and verification

- `PROJECT_STATE.yaml` and `state/task-graph.yaml` remain unchanged: next task P7-T01, phase P7 PENDING, task BLOCKED_BY_TOOL at the runner transport gate. This closeout does not advance that task.
- No source code changed, so no automated test suite was added or run. Revit readback, close/reopen, checkpoint, PDF page geometry, SHA-256, and visual checks are recorded in `revit/production/presentation/RUN-003-R04-ORIENTACAO-20260928/exports/FINAL-20260928/RUN003-R04-PRESENTATION-MANIFEST.json`.
- Detailed export files and per-file Horizun manifests are in `revit/production/presentation/RUN-003-R04-ORIENTACAO-20260928/exports/FINAL-20260928/`.

## Resume

Keep the current RUN-003 presentation writer lease intact. Do not reopen the P6 source for editing or start P7/R05/R06 from this packet. The formal next task remains P7-T01 and must wait for its own provider/runner gate and authorization.
