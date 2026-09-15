# P09-T03 to P09-T05 — not executed

Date: 2026-09-15
Reason: P09-T01 decided `DEFERRED_OPTIONAL`; the current academic and
production deliverables require Revit view/board previews, not a separate
photorealistic Blender render.

Current state:

- Blender executable: absent from the PATH and from the searched Windows
  installation roots.
- Blender MCP: not installed and not registered with Codex.
- Blender addon: not installed or enabled.
- Blender tool map: not created; `state/providers/blender-toolmap.yaml` was
  intentionally left untouched because the Tool Lab did not run.
- Amanda model/release: not imported into Blender.
- Render outputs: none created.
- `uv`/`uvx`: available locally, but not invoked to resolve or install a
  Blender MCP package.

## P09-T03 — register Blender MCP

If the scheduling gate reopens, this task requires resolving an exact, approved
`blender-mcp` package version, registering it with the verified absolute
`uvx.exe` path, inspecting `codex mcp list`, running the package's addon
installation command, and enabling the addon in Blender. The Amanda model must
remain unloaded during this registration check. None of these actions occurred.

## P09-T04 — Blender Tool Lab

If registration is approved, the disposable Tool Lab must inspect the actual
MCP schema, query an empty scene read-only, create exactly one cube, re-query
its existence and properties, save/close/reopen a disposable `.blend`, and
re-query after reopening. It must also exercise the intended Revit handoff
format and record compatibility/open-issue findings before any capability is
promoted. The result must be classified `PASS`, `DEGRADED` or `FAIL`. No such
test or promotion occurred.

## P09-T05 — rendering pipeline

If the Tool Lab passes and a render is required, the next task must choose an
import/export format from a measured Revit-to-Blender fidelity check, operate on
a copy of a validated release, record the source GOLDEN SHA-256 in the new
Blender project, define controlled materials/lighting/environment and approved
placeholder vegetation, create named cameras, render low-resolution previews,
review them, and only then render final resolution under
`deliverables/renders/<golden-release-id>/`. No validated GOLDEN render source,
import, preview or final render exists in this checkout.

## Resume path

First update the scheduling decision with the new requirement and approval.
Then verify Blender and the exact package versions, execute P09-T03 and
P09-T04 on disposable state, and only after a Tool Lab result execute P09-T05
against a copied verified release. Preserve the local Revit GOLDEN as the
authority; Blender may consume an export but may not edit it.
