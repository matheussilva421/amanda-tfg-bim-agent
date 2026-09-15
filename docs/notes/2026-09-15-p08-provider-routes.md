# P08 provider routes — 2026-09-15

## Live result — all 18 routes PROVEN

The probe was run against the disposable `LAB_ROUTE_PROBE` document in two
passes: `LIVE10` swept 17 routes, and `LIVE13` proved `revit.create_project` in
isolation. Consolidated evidence:
`tool-lab/horizun/results/probe-routes-2026-09-15-live10-13.json` (18/18
PROVEN). Every row below carries the live status now; the per-row history is in
the consolidated file and the run logs.

Two adapter defects were found by these runs and fixed with TDD:

1. `revit.create_project` sent `template_path`, which the installed
   `horizun_document_session` refuses on `open` (error: template_path is not
   applicable to operation open; nothing ran). The template now travels as
   `file_path`; opening it really opened the project (title `Default_M_PTB`,
   `is_family_document` false, 3230 elements).
2. `revit.create_furniture_element` read `IsActive` from a resolved id that can
   be a placed `FamilyInstance`, raising AttributeError: 'FamilyInstance'
   object has no attribute 'IsActive'. The script now resolves an instance to
   its `FamilySymbol` and refuses a non-symbol explicitly.

## Handoff status

The Horizun provider adapter now has an explicit route for every capability
emitted by the 13-stage synthetic BIM compiler. The compiler emits 18
capability values across R01–R13. This worker changed the provider, its unit
tests, this note, and the disposable live probe. In that original task no Revit
call was made; the live probe runs described below were executed afterwards by
the orchestrator, which owns the live Revit writer lease.
## Route matrix

| Capability | Route | Required translation and pre-write reads | Status |
| --- | --- | --- | --- |
| `revit.create_project` | Typed `horizun_document_session(operation=open)` | `get_document_info` first; enforces Revit 2027; forwards the selected `template_path`; no logical element reference is invented. | **PROVEN** — independent get_document_info reports the requested project 'LAB_R01_TEMPLATE' at 'C:\\Users\\slvma\\Downloads\\Github\\Projeto Amanda\\revit\\lab\\probe\\LAB_R01_TEMPLATE.rte' after document_session.open |
| `revit.create_toposolid` | `horizun_execute_python` | `get_document_info` and `horizun_query_model(OST_Toposolid)` first; metric points become Revit feet; optional level/type IDs resolve through reads; script calls `Toposolid.Create`. | **PROVEN** — independent query returned ElementId 329210 |
| `revit.create_level` | `horizun_create_elements` row | `get_document_info` first; elevation is normalized from `elevation_m`; logical ID is retained as `AMANDA_LOGICAL_ID`. | **PROVEN** — independent query returned ElementId 329137 |
| `revit.create_grid` | `horizun_create_elements` row | `get_document_info` first; 2D endpoints become `[x,y,0]`; logical marker is attached. | **PROVEN** — independent query returned ElementId 329138 |
| `revit.create_reference` | `horizun_execute_python` | `get_document_info` and `horizun_query_model(OST_ReferencePlanes)` first; coordinate becomes metric `XYZ`; script selects a deterministic non-template plan view and calls `ReferencePlane.Create`. | **PROVEN** — independent query returned ElementId 329227 |
| `revit.create_mass` | `horizun_execute_python` | `get_document_info` and `horizun_query_model(OST_Mass)` first; footprint points become metric `XYZ`; script creates an extrusion and calls `FreeFormElement.Create`. | **PROVEN** — independent query returned ElementId 329226 |
| `revit.create_wall` | `horizun_create_elements` row | `get_document_info` first; logical level/type IDs use catalog lookup when declared, then `horizun_list_elements`, then an exact single-match check; final IDs are independently queried before the write. | **PROVEN** — independent query returned ElementId 329139 |
| `revit.create_internal_wall` | `horizun_create_elements` row | Same deterministic level/type translation as walls; coordinates are normalized and the semantic/logical markers are included. | **PROVEN** — independent query returned ElementId 329198 |
| `revit.create_floor` | `horizun_create_elements` row | Level/type logical IDs resolve from `OST_Levels`/`OST_Floors`; flat profiles become 3D metric points; referenced IDs are queried before creation. | **PROVEN** — independent query returned ElementId 329149 |
| `revit.create_slab` | `horizun_create_elements` row | Same typed floor route and translation. | **PROVEN** — independent query returned ElementId 329168 |
| `revit.create_opening` | `horizun_create_elements` row | `host_logical_id` is accepted as the compiler alias, resolves against `OST_Walls`, and is queried with the level before `wall_opening` creation; 2D endpoints gain `z=0`. | **PROVEN** — independent query returned ElementId 329207 |
| `revit.create_roof` | `horizun_create_elements` row | Level/type logical IDs resolve from `OST_Levels`/`OST_Roofs`; profile coordinates are normalized and queried before creation. | **PROVEN** — independent query returned ElementId 329183 |
| `revit.create_room` | `horizun_create_elements` row | Logical level resolves from `OST_Levels`; room point is normalized to 3D; the logical marker is attached. | **PROVEN** — independent query returned ElementId 329205 |
| `revit.create_accessibility_element` | `horizun_execute_python` | `get_document_info` and `horizun_query_model(OST_GenericModel)` first; `geometry.from`/`geometry.to` and property node IDs resolve against `OST_Rooms`; script creates a marked `DirectShape` solid. | **PROVEN** — independent query returned ElementId 329228 |
| `revit.create_furniture_element` | `horizun_execute_python` | `get_document_info` and `horizun_query_model(OST_Furniture)` first; host space resolves against `OST_Rooms`, and `type_id`/family/type resolves against `OST_Furniture`; script activates the symbol and calls `NewFamilyInstance`. | **PROVEN** — independent query returned ElementId 329229 |
| `revit.create_landscape_element` | `horizun_execute_python` | `get_document_info` and `horizun_query_model(OST_GenericModel)` first; `host_zone` resolves against `OST_Rooms` when supplied; area is converted to a deterministic metric box; script creates a marked `DirectShape`. | **PROVEN** — independent query returned ElementId 329231 |
| `revit.assign_material` | `horizun_execute_python` | `get_document_info` and `horizun_query_model(OST_GenericModel)` first; host logical ID resolves from the declared host category, with catalog lookup for declared type references; a fresh read of the host is embedded; script finds/creates `Material` and sets a writable material parameter. | **PROVEN** — independent query returned ElementId 329139 |
| `revit.create_documentation_element` | `horizun_execute_python` | `get_document_info` and `horizun_query_model(OST_Views)` first; view/table references resolve from `OST_Views`; script uses `ViewSheet.Create`, `ViewSchedule.CreateSchedule`, or `ViewPlan.Create` according to `documentation_kind`. | **PROVEN** — independent query returned ElementId 328782 |

The route choices are deliberately narrow. Existing rows use the verified
`horizun_create_elements` schema. Project creation uses the verified document
session operation. The eight semantic gaps use the verified
`horizun_execute_python` tool with deterministic scripts that call the
operation-specific Revit API. A capability name that is absent from the exact
map still raises `HorizunUnsupportedCapability`; no lookalike tool is selected.

## Translation and caching

Reads are performed before the mutation is sent. Every mutation first reads
`get_document_info` and checks an explicit target against the active document
when the provider returns an identity. Typed references then use, in order,
the stage resolution cache, IDs returned by an earlier successful stage, an
optional `horizun_catalog_lookup`, and a cached `horizun_list_elements` result.
Each logical reference must have exactly one matching row with an integer
ElementId. The final referenced IDs are passed to `horizun_query_model` with
`cache_mode=bypass` before the write.

Python routes embed a canonical JSON request (`sort_keys=True`, compact
separators) and use a logical marker for idempotence. Material assignment has a
separate idempotence path because its logical ID commonly equals the host wall’s
logical ID; it re-applies the same material assignment instead of mistaking the
host for a completed material operation. Python statuses `failed` and `error`
are returned as failed `StageToolResult` values.

## Tests and validation

The adapter unit tests used the injected fake transport: no `hz_call.py`, Revit
process, document session, or save was involved in them. The live route probe ran
afterwards, separately, and is reported in the next section.

Focused route tests before the live work:

```text
.venv\Scripts\python.exe -m pytest tests/unit/test_bim_horizun_invoker.py -q -p no:cacheprovider --basetemp=.tmp-pytest-luna-green-20
30 passed, 0 failed
```

The generated eight Python route scripts were also parsed with the Python AST
parser: 8 parsed, 0 syntax failures. That is a static check and does not prove
Revit API execution.

The newly added tests had the required RED/GREEN progression. The RED gates
observed unsupported `create_mass`, missing logical-ID reads, missing nested
accessibility translation, generic-script bodies, and status promotion of a
script-reported failure. The corresponding focused GREEN gates passed before the
first handoff.

Running the live probe then found two real defects and each was fixed under TDD,
with a fresh RED gate first:

1. `revit.create_furniture_element` read `IsActive` from a resolved id that can be
   a placed `FamilyInstance`, raising AttributeError. The route now resolves an
   instance to its `FamilySymbol` and refuses a non-symbol explicitly.
2. `revit.create_project` sent `template_path` to `horizun_document_session`, whose
   installed contract only accepts `file_path` for operation 'open'. The live
   call returned an error saying template_path is not applicable to that
   operation and that nothing ran, so the route could never have worked. It now
   forwards the template as `file_path`.

After both fixes the focused file passed 46 tests and the required final suite
was re-run from the repository root:

```text
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=.tmp-suite50
777 passed, 0 failed in 27.44s
```
## Live evidence and limitations

The probe in `tool-lab/horizun/probe_capabilities.py` was run against the live Revit 2027
(27.2.0.39) / Horizun 1.3.3 writer lease: 17 routes in one sweep, then
`revit.create_project` isolated through the new `--only` filter. It still refuses
targets without `LAB_`/`LAB-` in the identity and requires `--confirm-live-lab`; R01
also requires `--template-path`. It reports `PROVEN` only after the provider
returns success and an independent `horizun_query_model` by the returned ElementId
succeeds. R01 uses an independent `get_document_info` read and now only reports
PROVEN when the open document really is the requested project and is not a family
document.

Consolidated result: `tool-lab/horizun/results/probe-routes-2026-09-15-live10-13.json`
reports 18 of 18 routes PROVEN and 0 UNPROVEN. Running the probe is what exposed
the two defects listed in the previous section, so this table is evidence from
execution and independent readback, not from static review.

The earlier P02-T12 Toposolid record stays a rehearsal of the installed build and
is not used as evidence for this table. Every PROVEN row above is backed by
that live run and carries the ElementId returned by an independent read after
the write.

The Python routes remain dependent on the active Revit document containing the
required level, view, family symbol, and writable host parameter. The adapter
refuses an absent or ambiguous logical reference; it does not invent a type,
host, view, or source coordinate. A future probe can therefore leave an
individual route UNPROVEN with a concrete provider error while the other routes
continue to be reported.
## GitHub and resume instructions

This worker performed no `git add`, commit, push, stash, checkout, or reset. The
branch still held unrelated edits from other workers, including state, design,
and tool-lab files, and those were preserved. The orchestrator owns the commit
and push for this note together with the rest of the measured work: the two live
route fixes, the probe hardening, the consolidated result file, and the P06/P08
state updates.

To resume, start in the repository root, inspect `git status`, run the required
final suite with a disposable `--basetemp`, and re-read the consolidated probe
result. Re-run the probe against a disposable LAB document whenever a route or
the add-in build changes, and never promote a row back to PROVEN without a fresh
independent readback.
