# P09 — optional rendering and cloud extensions

Date: 2026-09-15
Phase assessment: `GO_WITH_LIMITATIONS` for the optional-extension scope.
The local Revit path remains the selected path; Blender and APS are not
production dependencies.

## P09-T01 — immediate rendering need

Decision: `DEFERRED_OPTIONAL`.

The canonical academic deliverables file contains eleven human/BIM
deliverables and no photorealistic-render deliverable. The adopted
`program-summary.md` defines the 20-person program and areas, but no render
artifact. P08 Task 19 requires a `preview/` directory, and P08 export tasks
require Revit sheet/view previews and selected PNG previews. Those requirements
are satisfied by Revit view/board exports; they do not require a separate
Blender render.

Evidence command:

```powershell
rg -n --no-heading -i "render|preview|PNG" project/requirements/academic-deliverables.yaml project/requirements/program-summary.md docs/plan/CURRENT.md docs/spec/CURRENT.md
```

Historical observation from 2026-09-15: no matches in the two requirements files. P08 matches were
`floorplan/zoning SVG/PNG`, `preview export for every sheet`, `validate page
count/nonblank previews`, `export selected PNG previews`, and Task 19's
`preview/` directory.

The full rationale and reopening conditions are in
`tool-lab/blender/scheduling-decision.md`.

## P09-T02 — uv/uvx verification

Decision: `VERIFIED_LOCAL_TOOL_ONLY`; no installation was needed.

Fresh PowerShell invocations produced:

```text
uv 0.12.1 (329541a50 2026-07-31 x86_64-pc-windows-msvc)
uvx 0.12.1 (329541a50 2026-07-31 x86_64-pc-windows-msvc)
```

| Executable | Absolute path | SHA-256 | Authenticode |
| --- | --- | --- | --- |
| `uv.exe` | `C:\Users\slvma\AppData\Local\hermes\bin\uv.exe` | `F537CC65C1791D9A022132302B21ECD48CDF0A605A7B345809FBE8AF4E807D` | `NotSigned` |
| `uvx.exe` | `C:\Users\slvma\AppData\Local\hermes\bin\uvx.exe` | `5A25C39E939542D803B9B69630DE4FB2261157131A7427F2C03CEDEA29DACCF9` | `NotSigned` |

Commands used:

```powershell
& 'C:\Users\slvma\AppData\Local\hermes\bin\uv.exe' --version
& 'C:\Users\slvma\AppData\Local\hermes\bin\uvx.exe' --version
Get-FileHash -LiteralPath 'C:\Users\slvma\AppData\Local\hermes\bin\uv.exe' -Algorithm SHA256
Get-FileHash -LiteralPath 'C:\Users\slvma\AppData\Local\hermes\bin\uvx.exe' -Algorithm SHA256
```

The local provenance is limited to the observed absolute Hermes paths and
checksums; the files are unsigned, so no signature authenticity is claimed.
Astral's official uv README and workspace metadata state that uv is licensed
under `MIT OR Apache-2.0`:

- <https://github.com/astral-sh/uv/blob/main/README.md>
- <https://github.com/astral-sh/uv/blob/main/Cargo.toml>

The version and hashes are appended to
`state/bim-environment.lock.yaml` under `optional_versions.uv`. No
`blender-mcp` package was resolved or downloaded.

## P09-T03, P09-T04 and P09-T05 — Blender

Status: `NOT_EXECUTED` because P09-T01 deferred rendering.

The Blender search checked `Get-Command`, `where.exe`, and these Windows roots:

```text
C:\Program Files\Blender Foundation
C:\Program Files (x86)\Blender Foundation
C:\Users\slvma\AppData\Local\Programs\Blender Foundation
C:\Users\slvma\scoop\apps\blender
C:\ProgramData\chocolatey\bin
C:\Users\slvma\AppData\Local\Microsoft\WinGet\Packages
```

Observed output:

```json
{"get_command":[],"where":[]}
{"matches":[]}
```

No Blender, addon, MCP registration, tool map, import, fidelity test, `.blend`
file or render was created. `uvx --version` was run only as a local binary
check; `uvx --from ... blender-mcp` was not run.

The exact deferred work and resume path are recorded in
`tool-lab/blender/not-executed.md`. The planned
`state/providers/blender-toolmap.yaml` was intentionally not created because
P09-T04 did not execute.

## P09-T06 — APS need gate

Decision: `DEFERRED_OPTIONAL`; gate result `NO-GO`; capability
`aps_revit_automation: UNTESTED`.

The measured local matrix evaluates health/project info, model query, level,
wall, floor, room, hosted openings, views/sheets/schedules, Toposolid,
PDF/IFC/DWG/CSV/PNG export, document session, execute-Python and independent
re-read after reopen. Horizun is `PASS` for the required path. RevitCortex's
room failure and absent document cycle are recorded as provider-specific
limitations; the custom host remains a proven fallback for its tested scope.

Evidence command:

```powershell
Select-String -LiteralPath state/capabilities.yaml,tool-lab/reports/provider-benchmark.md -Pattern 'BLOCKED_BY_TOOL' -SimpleMatch
```

Observed output: `capability_scan=NO_MATCHES`.

The local APS/Forge lookup also returned no command records, no matching
installation directories and no matching environment-variable names. No
environment values were read.

The explicit NO-GO has two independent bases: no concrete required local
capability is blocked, and the owner prohibits APS/Forge because it is a paid
cloud/subscription route. Consequently P09-T07 through P09-T09 were not run.
The full capability list, evidence and reopening conditions are in
`tool-lab/aps/need-report.md`.

## P09-T10 — local-first routing

Status: `VERIFIABLE_LOCALLY_SEM_ACAO_NECESSARIA`.

`state/capabilities.yaml` keeps Horizun at priority `10` and custom-api at
priority `30`, with `preferred_provider: horizun`; no APS entry exists. This
local ordering can be checked without APS and requires no change in this
write set. The principal agent owns the task-graph marking.

## Untested and deferred boundaries

The following remain explicitly outside the verified set:

- Blender installation and Blender MCP registration;
- the Blender tool map and disposable `.blend` save/reopen test;
- Revit-to-Blender import/fidelity validation;
- low-resolution and final Blender renders;
- APS/Revit Automation, its samples, credentials, cloud model and deployment;
- P09-T07 through P09-T09.

These boundaries do not alter the current local provider selection or authorize
any paid installation.

## Validation record

The changed lock and the two existing YAML registries loaded successfully in an
isolated PyYAML check. The focused project tests returned:

```text
tests/project/test_deliverable_scope.py: 7 passed, 0 failed
tests/providers/test_toolmaps.py: 11 passed, 0 failed
```

`docs/review/validate_documents.py` returned
`DOCUMENT_STATIC_CHECKS total=21 passed=21 failed=0`. The final write-set
check found no missing file, trailing whitespace, secret-pattern match or
`BLOCKED_BY_TOOL` match; `git diff --check -- state/bim-environment.lock.yaml`
returned exit 0.
