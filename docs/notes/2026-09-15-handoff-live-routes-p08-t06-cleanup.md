# Handoff - live route proof, P08-T06 PASS, local cleanup (2026-09-15)

Scope: finish the live Horizun route proof, close P08-T06 in the graph, update the
stale parts of the route note, run the local cleanup the owner asked for, and leave
a resume point for the next agent.

## 1. What was done

- LIVE13 proved `revit.create_project` on its own: it opened
  `revit/lab/probe/LAB_R01_TEMPLATE.rte`, a byte-identical copy of
  `Default_M_PTB.rte` (sha256
  `f1d90665e8cb441a9d6ab620a751ba6300cf96f7d3bcc42ad74f60ae80484825`), and
  `get_document_info` reported the requested title/path with
  `is_family_document: false` and 3230 elements.
- Consolidated matrix: `tool-lab/horizun/results/probe-routes-2026-09-15-live10-13.json`
  now reports 18 of 18 routes PROVEN and 0 UNPROVEN (17 in one sweep plus R01
  isolated through the new `--only` filter).
- Two real adapter defects were found by running the probe and fixed under TDD:
  the furniture route read `IsActive` from a placed `FamilyInstance`; the project
  route sent `template_path` where `horizun_document_session(operation=open)`
  requires `file_path`. Both had a fresh RED gate first and were re-proven live.
- `tool-lab/horizun/probe_capabilities.py` hardened: R01 only reports PROVEN when
  the open document really is the requested project and is not a family document,
  and the new `--only <capability>` filter runs one route at a time.
- P08-T06 recorded as PASS (state revision 151) using the regeneration test, the
  unchanged `run.json` sha256
  `09cb06cc0a3dcfc9dacad04e8263c72f6cc6fdc2aa8cf56c196a4542c57f54b4`, and the two
  published finalists `AMANDA-RUN-001-F01` / `-F02`.
- `docs/notes/2026-09-15-p08-provider-routes.md`: the four stale sections
  (Handoff status, Tests and validation, Live evidence and limitations, GitHub and
  resume instructions) were rewritten with the measured live state.
- `docs/notes/2026-09-15-arya-o-que-falta-simples.md`: the three Horizun
  statements were corrected from "1 of 18 proven" to the measured 18 of 18.
- Local cleanup executed with `scripts/cleanup-local.ps1 -Apply`: 195 targets and
  30 `__pycache__` directories removed, 4414.9 MB freed. Only `.pytest_cache`
  resisted removal with an ACL denial and was reported, not forced.
- Before the cleanup, helpers that actually solved live problems were promoted into
  `tool-lab/custom-api/runners/`: `revit-dialog-button.ps1` (the title+button modal
  clicker used to clear the "Projeto nao recentemente salvo" dialog),
  `enum-windows.ps1`, and `clear-security-dialogs.ps1`.

## 2. Files created, changed or removed

Changed:

- `src/amanda_agent/bim/providers/horizun.py` (furniture symbol resolution;
  document-session `file_path` forwarding)
- `tests/unit/test_bim_horizun_invoker.py` (two RED/GREEN tests and one corrected
  expectation)
- `tool-lab/horizun/probe_capabilities.py` (R01 identity guard, `--only`)
- `docs/notes/2026-09-15-p08-provider-routes.md`,
  `docs/notes/2026-09-15-arya-o-que-falta-simples.md`
- `state/task-graph.yaml`, `state/task-history.yaml`, `state/status.md`,
  `PROJECT_STATE.yaml` (P08-T06 PASS)

Created:

- `tool-lab/horizun/results/probe-routes-2026-09-15-live10-13.json`
- `tool-lab/custom-api/runners/revit-dialog-button.ps1`,
  `tool-lab/custom-api/runners/enum-windows.ps1`,
  `tool-lab/custom-api/runners/clear-security-dialogs.ps1`
- this handoff

Removed: local scratch only. No tracked file was deleted. `.tmp-*` scratch, tool
caches, and stray bytecode are gone; `.venv`, `.dotnet`, `vendor/`, `revit/lab`,
`state/`, `docs/` and every `tool-lab` result JSON were preserved.

## 3. Tests and validation

```text
python -m pytest tests/unit/test_design_refine.py tests/unit/test_design_cli.py -q -p no:cacheprovider --basetemp=.tmp-pytest-t2
8 passed, 0 failed

python -m pytest -q -p no:cacheprovider --basetemp=.tmp-suite51
777 passed, 0 failed in 25.00s
```

Live evidence: the consolidated probe result (18/18 PROVEN) plus the R01
`get_document_info` read. Manual validation: the installed template hash was
rechecked after the modal-dialog incident and is unchanged.

## 4. Known limitations

- The 18 routes are proven against LAB documents. Production-document re-proof
  has not happened; do not present LAB proof as production proof.
- The cleanup could not delete `.pytest_cache` (ACL denial). Harmless, ignored by
  Git, removable by hand.
- The Revit session still holds `LAB_R01_TEMPLATE` active plus `LAB_ROUTE_PROBE`
  and `LAB_R00_EMPTY` open. `Default_M_PTB` was closed without saving.
- Release-signature cleanup in `HKCU\...\Autodesk Revit 2027\CodeSigning`
  (keys `A7B3C1D2-4E5F-4061-8A9B-0C1D2E3F4A5B` and
  `5C4F2F28-CEB0-4B84-9EA5-15B6172A8C55`) is still pending and must be reverted
  before the final delivery claim.

## 5. How to resume

- Next READY task: `P06-T14`, the synthetic R14-R16 drill. The plan file
  `.tmp-drill-plan.json` was deleted by the cleanup because it is scratch;
  regenerate it, and use the real `Default_M_PTB.rte` path in the R01 template
  instead of the 32-byte placeholder.
- Then P07-T17 (new session) and P07-T19 (authorized reboot), which need Amanda.
- Run the full suite with a disposable `--basetemp=.tmp-*` and
`-p no:cacheprovider`; without it Windows raises `PermissionError [WinError 5]`.
- GitHub: commit and push the dirty tree from `main` (56 entries) before starting
  new work, so the live fixes are not lost.
