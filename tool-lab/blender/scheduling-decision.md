# Blender rendering scheduling decision

> Historical decision record from 2026-09-15. The project now uses the single
> active specification and plan in `docs/spec/CURRENT.md` and
> `docs/plan/CURRENT.md`; `PROJECT_STATE.yaml` and `state/HANDOFF.md` control
> current task selection. Reopen this decision only under the conditions below
> and current project authority.

Date: 2026-09-15
Decision: `DEFERRED_OPTIONAL`
Capability: `blender_rendering`
Capability status: `UNTESTED`
Scope: STUDY support only; no production dependency is introduced.

## Decision basis

The current academic scope in `project/requirements/academic-deliverables.yaml`
contains eleven deliverables. They cover caderno, visits, metaprojeto,
preliminary study, anteprojeto, boards, memorials, defense, authorship and
institutional submission. There is no deliverable for a photorealistic render.

`project/requirements/program-summary.md` fixes the adopted program at 20
people, 626 m² of useful internal area and 260 m² of programmed external area.
It defines the program and its provisional sizing limits; it does not require a
rendering artifact.

P08 Task 19 requires a `preview/` directory and P08 export tasks require sheet
previews and selected PNG previews. Those are previews of Revit boards/views
and exports. They do not establish a requirement for a separate Blender
photorealistic render. The production path already has a verified Revit PNG
export capability in `tool-lab/reports/provider-benchmark.md`.

Because the required previews are supplied by Revit views/boards, installing
Blender solely for optional presentation would add an unneeded dependency.
Blender remains outside the current production path and no model is sent to a
rendering tool.

## Evidence recorded

Command:

```powershell
rg -n --no-heading -i "render|preview|PNG" project/requirements/academic-deliverables.yaml project/requirements/program-summary.md
```

Observed output on 2026-09-15: no matches in the two requirements files. The
plan snapshot archived in Git history recorded Revit board/view previews and
explicitly permitted `DEFERRED_OPTIONAL` with an `UNTESTED` capability when a
separate render was not required.

## Conditions to reopen

Reopen this decision only when an updated academic/institutional requirement
explicitly asks for photorealistic stills or animation, or when Amanda
explicitly requests them for the STUDY presentation. Before execution, the
following must be recorded:

1. a validated Revit release/export copy and its SHA-256;
2. a free/open-source tool choice and exact versions;
3. Blender installation and MCP/tool-lab authorization within that scope;
4. a disposable import/fidelity check before any final render; and
5. low-resolution preview review before a final-resolution render.

Until those conditions exist, `blender_rendering` stays `UNTESTED` and the
decision stays `DEFERRED_OPTIONAL`.
