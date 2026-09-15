# Handoff — P09 optional render/cloud

Date: 2026-09-15
Worker: Zeus
Scope: P09-T01 through P09-T06, with a local-only verification note for
P09-T10.

## Current status

The optional-extension decision is documented. Photorealistic Blender
rendering is `DEFERRED_OPTIONAL`, APS/Revit Automation is `DEFERRED_OPTIONAL`
with an explicit `NO-GO`, and both optional capabilities remain `UNTESTED`.
No paid/cloud service, credential, Blender installation, Blender MCP
registration, addon, APS sample, cloud model or upload was used.

## Decisions and evidence

- P09-T01: the canonical academic deliverables list has no photorealistic
  render. P08 requires Revit board/view previews and selected PNG exports, so
  the Blender scheduling decision is `DEFERRED_OPTIONAL`.
- P09-T02: `uv` and `uvx` are functional at `0.12.1`, build
  `329541a50 2026-07-31 x86_64-pc-windows-msvc`.
  `uv.exe` is at
  `C:\Users\slvma\AppData\Local\hermes\bin\uv.exe` with SHA-256
  `F537CC65C1791D9A022132302B21ECD48CDF0A605A7B345809FBE8AF4E807D`.
  `uvx.exe` is at
  `C:\Users\slvma\AppData\Local\hermes\bin\uvx.exe` with SHA-256
  `5A25C39E939542D803B9B69630DE4FB2261157131A7427F2C03CEDEA29DACCF9`.
  Both files report `NotSigned`; no signature authenticity is claimed.
  Astral's official uv sources identify the license as `MIT OR Apache-2.0`.
- P09-T03 to P09-T05: not executed because Blender is absent from PATH and
  from the searched Windows roots. No Blender MCP package was resolved or
  downloaded. The exact deferred task contracts and resume path are in
  `tool-lab/blender/not-executed.md`.
- P09-T06: no `BLOCKED_BY_TOOL` match exists in the capability registry or
  provider benchmark. Horizun is the preferred local provider; RevitCortex's
  partial gaps do not block the tested local chain, and custom-api remains a
  proven fallback. The owner directive also prohibits APS/Forge paid/cloud
  use. P09-T07 to P09-T09 were therefore not executed.
- P09-T10: local-first order is `verifiable, sem acao necessaria`: Horizun
  priority `10`, custom-api priority `30`, no APS entry. The principal agent
  owns the graph marking.

## Files in this write set

Created:

- `tool-lab/blender/scheduling-decision.md`
- `tool-lab/blender/not-executed.md`
- `tool-lab/aps/need-report.md`
- `docs/reports/p09-optional-extensions.md`
- this handoff

Modified:

- `state/bim-environment.lock.yaml`: appended only
  `optional_versions.uv`; existing Revit/provider pins and concurrent changes
  were preserved.

Intentionally untouched:

- `state/task-graph.yaml`
- `PROJECT_STATE.yaml`
- `RESUME...`
- `src/amanda_agent/**`, `revit/**`, `project/**` and P08 files
- `state/capabilities.yaml` and `state/providers/blender-toolmap.yaml` (the
  latter was not created because P09-T04 did not run)

## Final verification

Commands already run:

```powershell
& 'C:\Users\slvma\AppData\Local\hermes\bin\uv.exe' --version
& 'C:\Users\slvma\AppData\Local\hermes\bin\uvx.exe' --version
Get-FileHash -LiteralPath 'C:\Users\slvma\AppData\Local\hermes\bin\uv.exe' -Algorithm SHA256
Get-FileHash -LiteralPath 'C:\Users\slvma\AppData\Local\hermes\bin\uvx.exe' -Algorithm SHA256
```

Observed: both version commands returned `0.12.1`; hashes are recorded above.

```powershell
Get-Command blender.exe; where.exe blender.exe
```

Observed: no records. Recursive searches of the six documented Windows roots
returned `matches: []`.

```powershell
Get-Command aps,forge,autodesk,autodesk-platform-services
Select-String -LiteralPath state/capabilities.yaml,tool-lab/reports/provider-benchmark.md -Pattern 'BLOCKED_BY_TOOL' -SimpleMatch
```

Observed: no command records and `capability_scan=NO_MATCHES`.

Focused project tests:

```text
tests/project/test_deliverable_scope.py: 7 passed, 0 failed
tests/providers/test_toolmaps.py: 11 passed, 0 failed
```

The isolated YAML check loaded `state/bim-environment.lock.yaml`,
`state/capabilities.yaml` and `project/requirements/academic-deliverables.yaml`
and returned `YAML_OK` for all three plus `OPTIONAL_UV_LOCK_OK`.

The static documentation validator returned:

```text
DOCUMENT_STATIC_CHECKS total=21 passed=21 failed=0
```

The final write-set check returned zero missing files, zero trailing-whitespace
matches, zero secret-pattern matches and zero `BLOCKED_BY_TOOL` matches.
`git diff --check -- state/bim-environment.lock.yaml` returned exit 0.

## GitHub and worktree

The live repository is on branch `main`, tracking `origin/main`, with a dirty
worktree containing parallel-agent edits and untracked work. The final status
snapshot showed `PROJECT_STATE.yaml` and `state/task-graph.yaml` already
modified, and the six write-set files present as added/modified entries. No
`git add`, commit, push, reset, checkout or worktree operation was performed by
this worker, per the owner instruction; any index state is therefore left for
the principal/concurrent agent to reconcile. The main agent must review this
write set and publish it with the other accepted changes.

## Resume instructions

1. Read this handoff, `docs/reports/p09-optional-extensions.md` and the two
   files under `tool-lab/blender/`.
2. Run the focused tests/checks recorded by the next update and inspect only
   this write set plus the lock append.
3. Have the principal agent mark P09-T01 through P09-T06 and the local P09-T10
   note in the task graph; this worker must not edit the graph.
4. Reopen Blender work only after an explicit render requirement and free-stack
   authorization. Reopen APS only after a concrete mandatory
   `BLOCKED_BY_TOOL`, an owner policy change/waiver, and a disposable test plan.
