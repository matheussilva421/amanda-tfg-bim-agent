# APS/Revit Automation need gate

Date: 2026-09-15
Scheduling decision: `DEFERRED_OPTIONAL`
Gate result: `NO-GO`
Capability status: `UNTESTED`

## Decision

No concrete local capability required by the current Amanda production plan is
`BLOCKED_BY_TOOL`. The verified local chain already covers document access,
model mutation, save/close/reopen, independent reread and the required export
path. RevitCortex has documented partial gaps, but the preferred Horizun path
and the custom-api fallback cover the relevant local operations.

The APS/Forge path is therefore deferred and receives an explicit NO-GO for
this phase for both reasons required by the owner:

1. there is no concrete local need that has reached `BLOCKED_BY_TOOL`; and
2. the owner prohibits APS/Forge because it is a paid/cloud subscription path.

No APS credential, app, activity, cloud model, upload, sample repository,
deployment or MCP registration was used or created. P09-T07 through P09-T09
remain unexecuted because the need gate did not pass.

## Local capabilities evaluated

The statuses below come from the measured matrix in
`tool-lab/reports/provider-benchmark.md` and the corresponding registry in
`state/capabilities.yaml`.

| Capability | Local evidence | Gate reading |
| --- | --- | --- |
| health / project info | Horizun `PASS` | available locally |
| read model / query elements | Horizun, RevitCortex and custom host evidence | available locally |
| create level | Horizun and RevitCortex `PASS` | available locally |
| create wall | Horizun, RevitCortex and custom-api `PASS` | available locally |
| create floor | Horizun and RevitCortex `PASS` | available locally |
| create room | Horizun `PASS`; RevitCortex `FAIL` with null area | preferred local path available |
| hosted door / window | Horizun and RevitCortex `PASS` | available locally |
| view / sheet / schedule | Horizun and RevitCortex `PASS` | available locally |
| Toposolid | Horizun and RevitCortex `PASS` | available locally |
| PDF / IFC / DWG / CSV / PNG export | Horizun `PASS` | available locally |
| document session | Horizun `PASS`; custom host fallback `PASS`; Cortex absent | available locally |
| execute Python in Revit | Horizun `PASS` | available locally |
| independent reread after reopen | Horizun `PASS`; custom host reread evidence | available locally |

The RevitCortex room limitation and absent document cycle are recorded as
provider-specific facts. They do not make the required local path blocked while
Horizun remains the preferred provider and the custom host remains the
last-resort fallback.

## Evidence commands and observed output

Command:

```powershell
Select-String -LiteralPath state/capabilities.yaml,tool-lab/reports/provider-benchmark.md -Pattern 'BLOCKED_BY_TOOL' -SimpleMatch
```

Observed output: no matches (`capability_scan=NO_MATCHES`).

Command:

```powershell
Get-Command aps,forge,autodesk,autodesk-platform-services -ErrorAction SilentlyContinue
Get-ChildItem Env: | Where-Object { $_.Name -match '(?i)^(APS|FORGE|AUTODESK)(_|$)' } | Select-Object -ExpandProperty Name
```

Observed output: no command records and no matching environment-variable names.
Only variable names were inspected; no environment values or credentials were
read or recorded.

The local registry also records `preferred_provider: horizun`, Horizun entries
at priority `10`, and custom-api at priority `30`. There is no APS entry.

## Conditions to reopen

Reopen the gate only if a mandatory local operation is first reproduced as
`BLOCKED_BY_TOOL` after rechecking the typed provider, custom fallback and
validated interchange/export alternatives, and the owner changes or expressly
waives the current no-paid/cloud directive. A reopened gate would additionally
need a synthetic/disposable RVT, an explicit destination and cost boundary,
separate credentials handled outside Git/logs, a pinned sample/tool version,
and an independent output verification plan.

## P09-T10 note

The local-first ordering is verifiable without APS and needs no action here:
the current registry keeps verified Horizun at priority 10 and the custom-api
fallback at priority 30, while no optional APS provider is registered. The
principal agent may mark P09-T10 as `verifiable, sem acao necessaria` in the
task graph; this worker does not modify that graph.
