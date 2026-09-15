# P02-T19 — Provider benchmark and final matrix

Date: 2026-09-15
Revit build: 27.2.0.39 (product_version 20260716_1515(x64))
Fixture policy: every measurement below comes from a disposable file under `revit/lab/`; no user model was opened or mutated.

## 1. Environment pins

| Component | Pin |
| --- | --- |
| Revit | 27.2.0.39 / 20260716_1515(x64), C:\Program Files\Autodesk\Revit 2027 |
| Horizun Revit MCP | server 1.3.3, source_commit cc4ea04e9ecfe547ad349f22e0864019ce1ead1f, contract_hash 8b9600f5274d7dffb6e5bd5f, 80 contract tools / 70 listed by the client |
| RevitCortex | server 2.0.0, source_commit 8b2556daefb2bf88f0a7a17bf28f2352fe0b0e33, 288 catalog tools, protocol 2024-11-05 |
| Custom C# host | Amanda.ToolLab.Host + Amanda.ToolLab.Command, net10.0-windows7.0 Release, own ExternalCommand invoked in-process by Revit 2027 |
| Python control plane | pinned 3.12 venv (.venv/Scripts/python.exe) |
| Dotnet | SDK 8.0.422 system-wide; local pinned SDK under .dotnet for the host build |

## 2. Capability matrix (measured)

Legend: PASS = proven on a disposable file with an independent re-read; PARTIAL = proven only in part; FAIL = refused or wrong; UNTESTED = never executed.

| Capability | Horizun | RevitCortex | Custom C# | Evidence |
| --- | --- | --- | --- | --- |
| health / project info | PASS | PASS | n/a | tool-lab/horizun/health-probe-2026-09-15.json; t15-cortex-fixture.json |
| read model / query elements | PASS | PASS | PASS (host re-read) | t15-reread.json (11 elements across 10 categories); t16-host-create.json |
| create level | PASS | PASS (reused existing ids 311/694) | PASS (fixture level in host) | t08-apply.json; t15-cortex-fixture.json |
| create wall | PASS (10 m x 3 m, type 398) | PASS (10 m x 3 m, type 398) | PASS (5 m x 3 m, Interior - 138 mm Divisoria) | t09-wall.json; t15-ab-comparison.md; t16-host-create.json |
| create floor | PASS (6 x 4 m, 24 m2) | PASS (bbox 6 x 4 m, 24 m2) | UNTESTED (command scope is create_wall) | t10-floor.json; t15-ab-comparison.md |
| create room | PASS (16 m2) | FAIL (area null, warning "Ambiente nao esta em uma regiao apropriadamente fechada") | UNTESTED | t10-room.json; t15-ab-comparison.md |
| create door / window (hosted) | PASS | PASS (HOST_ID_PARAM=328657) | UNTESTED | t11-dimension-references.json; t15-ab-comparison.md |
| create view / sheet / schedule | PASS | PASS (names and category diverge from the Horizun reference) | UNTESTED | t11-views-sheet.json, t11-schedule.json; t15-ab-comparison.md |
| create Toposolid | PASS | PASS | UNTESTED | t12-toposolid.json |
| export PDF / IFC / DWG / CSV / PNG | PASS | not available in Cortex contract | UNTESTED | t11-export-matrix.json + tool-lab/horizun/exports/* |
| document session (open / save / close / reopen) | PASS | FAIL (no document cycle in the contract at all) | PASS (host opened, saved, closed and reopened its own work file) | t15-close-live.json, t15-open-live.json, t15-reread.json; t16-host-create.json |
| execute Python inside Revit | PASS | not available in Cortex contract | n/a | resource horizun://security/current-profile (execute_python_allowed=true) |
| independent re-read after reopen | PASS (11/11 elements) | not possible without a document cycle | PASS (wall_count_after_reopen=1, geometry_matches_contract=true) | t15-reread.json; t16-host-create.json |

## 3. Ranking per criterion

Criterion weights follow the plan: reliability, model quality, save/reopen persistence, observability/error quality, warning cleanliness, speed.

| Criterion | Horizun | RevitCortex | Custom C# | Winner |
| --- | --- | --- | --- | --- |
| Reliability | 14 levels of work proven end-to-end without a refusal | 288 tools, but no document cycle and a room that failed to close its region | one command, 13/13 steps PASS | Horizun |
| Model quality | room 16 m2, floor 24 m2, openings hosted, Toposolid | wall/floor/hosted openings match; room area null | wall 5 x 3 m exact | Horizun |
| Save / reopen persistence | save 4366336 -> 4415488 B with hash, close verified by object identity, reopen verified by 11-element re-read | impossible (no document tool) | save, close, reopen and re-read all PASS | tie: Horizun and Custom C# |
| Observability / error quality | typed refusals with exact dialogs, per-step JSON | rich per-tool payloads, safety annotations parsed from source | AP1 13 step records with durations | tie: Horizun and Cortex |
| Warning cleanliness | 0 warnings after wall and floor; 1 room warning only when the region is open | 1 warning from the same room condition | 0 warnings | Horizun |
| Speed | table and export calls in the seconds range; save 384 ms class times | command responses ~90 ms, batch reads 1-2 s | command_ms 32, total 5702 ms including close/reopen | Custom C# for a single command, Horizun for a full pipeline |

## 4. Decision

**Preferred provider: Horizun (horizun-revit-mcp).**

The rules in the plan are applied literally:

- The tie rule is not even needed. Horizun wins reliability, model quality, warning cleanliness and pipeline speed outright, and it is the only provider that owns a document cycle, which every write capability needs for save/reopen proof.
- RevitCortex is **not** preferred: its evidence is materially worse, because it cannot save, close or reopen a document and it produced a room with a null area.
- The custom API is a **fallback**, not the primary path. It is the only option that survives both typed providers failing, and the host now proves it works, so it stays registered as a proven fallback rather than an untested one.
- No provider with status UNTESTED is preferred anywhere in this matrix.

## 5. Limits and open items

- This matrix is a snapshot of 2026-09-15. Any provider upgrade invalidates it and the toolmaps must be regenerated.
- RevitCortex room creation stays FAIL until a closed region is proven; this is a Cortex-side limitation, not a project decision.
- IFC, DXF and cloud paths are not inserted into the model; they stay export-only until their own tests exist (t11-export-matrix.json covers export, not re-import).
- The benchmark does not prove licensing, only that the tools answered correctly on disposable files.
