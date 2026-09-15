# RevitCortex — source audit (P02-T13)

Audited 2026-09-15 against the checkout in `vendor/RevitCortex` and the
user-scope deployment built from it during this task. Revit was **running** for
part of the audit (pid 39140, started 11:17:44 local), so the deploy script
deliberately skips the vendor pre-flight that refuses to run beside a live
Revit: the plugin had never been loaded into that process, so no target file was
held open. Everything below was read back from disk after the build.

## Exact revision

- Repository: `https://github.com/LuDattilo/RevitCortex.git`
- Local path: `vendor/RevitCortex` (gitignored; the vendor tree stays out of the published repo)
- Commit: `8b2556daefb2bf88f0a7a17bf28f2352fe0b0e33` (`8b2556d`)
- Commit date: 2026-07-08 17:58:26 +0200, subject *fix(elements): create_level honors dryRun (was ignored — created level regardless)*
- Working tree: clean, 504 commits reachable
- License: MIT (Luigi Dattilo, 2026)
- Versions: plugin `1.0.50`, server `2.0.0`

## What the upstream documentation promises

`README.md` claims, among other things, "173 MCP tools across 15+ categories"
and a "Read-only mode — global switch in settings blocks all write tools".
`docs/SECURITY.md` describes the code-execution sandbox, the audit log and the
confirm-before-destructive rule. Those three claims were the ones this audit set
out to confirm or contradict, because they decide how much of the tool may be
exposed to the agent unattended.

**173 versus 288.** The binary contradicts the README. A live MCP handshake with
the published server returns `server: RevitCortex 2.0.0`, `protocol: 2024-11-05`
and **288 tools**, not 173. The raw catalogue is stored beside this report as
`tool-catalog.json`. The README is a stale figure for an earlier tool set; the
288 list is the binding surface, and `revitcortex-toolmap.yaml` (P02-T14) must be
derived from the catalogue, not from the README.

## Prerequisites on this machine

- Revit 2027 `27.2.0.39`, .NET 10 runtime host (`RevitExtractor.runtimeconfig.json` declares `net10.0` / `Microsoft.NETCore.App 10.0.0`).
- Machine-wide .NET SDKs: `8.0.422` only. The plugin's `Release R27` configuration targets
  `net10.0-windows7.0`, so `dotnet restore -p:Configuration='Release R27'` fails with
  **NETSDK1045** against the machine SDK.
- Remedy applied: SDK **10.0.401** installed into the repo-local `.dotnet/` tree
  (gitignored) from `https://dot.net/v1/dotnet-install.ps1`
  (`-Channel 10.0 -InstallDir .dotnet -NoPath`, installer sha256
  `E8B873E18A81E5C4CD8AB69D84DAC8FEAD291D50B3C44633CD7FDDAD709A13D6`). The
  machine-wide SDK was left untouched. The server project keeps targeting
  `net8.0` and builds with either SDK.

The vendor ships **two** deploy scripts, and the difference matters here:
`deploy.ps1` targets machine scope (`C:\ProgramData\Autodesk\Revit\Addins`), which
does not exist on this machine and would need elevation
(`IsInRole(Administrator)` is `False`). `deploy-userscope.ps1` targets
`%APPDATA%\Autodesk\Revit\Addins\2027\`, which is where every other add-in for
this user already lives. This task used user scope.

## Builds

| Target | Configuration | Result |
| --- | --- | --- |
| `src/RevitCortex.Server/RevitCortex.Server.csproj` | `Release` | 0 warnings, 0 errors |
| `src/RevitCortex.Plugin/RevitCortex.Plugin.csproj` | `Release R27` | 0 errors, 5 pre-existing warnings (CS8604, SYSLIB0014, CS8603 x2, CS0649 — all inside vendor code, none introduced here) |

## What is actually installed now

Add-in (user scope, beside the existing `Horizun.addin`):

| Artifact | Path | Bytes | SHA-256 |
| --- | --- | --- | --- |
| Add-in manifest | `%APPDATA%\Autodesk\Revit\Addins\2027\RevitCortex.addin` | 459 | `C9E81E87D046E6D0A4F1BC71C7F2F56E775C32EDE78FFCDDA3CAF7F22A4AD94C` |
| Plug-in assembly | `%APPDATA%\Autodesk\Revit\Addins\2027\RevitCortex\RevitCortex.Plugin.dll` | 491520 | `E01135D08A2EBCB13A8DBBCD2914E3E51637B5825A802008A59F2BE7E6C325F9` |
| Tools assembly | `%APPDATA%\Autodesk\Revit\Addins\2027\RevitCortex\RevitCortex.Tools.dll` | 2029568 | `09FA571025767065293A612A01441CCE48EDCE50335BC16FD846D1F22C7115A0` |
| Core assembly | `%APPDATA%\Autodesk\Revit\Addins\2027\RevitCortex\RevitCortex.Core.dll` | 70656 | `C6F14C75B6657195937CECFAF9F02088428F2109E322515E4DD0FF36D1DAB0F0` |

The payload directory holds 76 files, 19 of them assemblies. The manifest
declares `AddIn Type="Application"`, `FullClassName`
`RevitCortex.Plugin.RevitCortexApp`, `AddInId`
`A1B2C3D4-E5F6-7890-ABCD-EF1234567890` — distinct from Horizun's
`b8e5a2f0-3c1d-4e6a-9f2b-7a4c8d1e5f30`, so the two can coexist and are tracked
separately by Revit's own trust store.

Server:

| Artifact | Path | Bytes | SHA-256 |
| --- | --- | --- | --- |
| MCP server executable | `vendor/RevitCortex/publish/server/RevitCortex.Server.exe` | 152064 | `958B4B6703D7A1EF3B093CEFE22FB3C11D192D443178D77486A5462ECE8CA671` |

Self-contained `win-x64` publish, `net8.0`, 218 assemblies / 223 files, SDK
10.0.401. The executable is resolved through
`tool-lab/revitcortex/server-publish-manifest.json` rather than by picking the
newest file in the tree; the script fails closed if the publish does not contain
exactly one `RevitCortex.Server.exe`.

Reproducible from the repository by two committed scripts:
`tool-lab/revitcortex/deploy-revitcortex-2027.ps1` (add-in, isolated SDK) and
`tool-lab/revitcortex/publish-server.ps1` (server plus manifest).

## MCP surface

A live stdio handshake with the installed executable returned
**288 tools** (protocol `2024-11-05`). The full raw catalogue is committed at
`tool-lab/revitcortex/tool-catalog.json`; the same probe script the Horizun work
uses (`tool-lab/horizun/mcp_probe.py`, `--server`) was reused unchanged.

## Security posture (what the code actually enforces)

- **`send_code_to_revit` is the sharp tool.** It runs C# supplied by the client
  inside Revit, and it is gated by `EnableCodeExecution`, which defaults to
  **false** in `~/.revitcortex/settings.json`. Confirmed by reading
  `src/RevitCortex.Tools/Elements/SendCodeToRevitTool.cs` (the tool refuses when
  the setting is off) and the vendor's own `docs/2026-06-30-send-code-to-revit-usage-audit.md`,
  which independently recommends keeping it disabled. **This setting must stay
  false for the whole Amanda project.**
- The sandbox (`CodeSandboxV2.cs`) rejects `System.IO`, `System.Net`,
  `System.Diagnostics.Process`, `Microsoft.Win32`, `System.Reflection`,
  `System.Runtime.InteropServices`, `dynamic`, bare `Invoke(` / `GetTypes(`, and
  strips comments and string literals before matching so the check cannot be
  dodged by quoting. It is a guard rail, not a security boundary by itself, which
  is why the `EnableCodeExecution` gate in front of it matters more.
- **Read-only mode** is a global switch in settings that makes `CortexRouter`
  reject write tools. It is *not* on by default; this deployment did not enable
  it, because the Amanda plan needs writes. It remains the fastest way to freeze
  the add-in if a tool misbehaves.
- Destructive tools raise a native Revit confirmation dialog rather than
  deleting silently.
- `PathSafety.TryResolveSafe` confines file paths to directories under the user
  profile.
- Audit log: `~/.revitcortex/audit.jsonl`. Settings: `~/.revitcortex/settings.json`
  (neither exists yet on this machine — both are created on first run).
- Telemetry is opt-in and **off**: nothing is sent to `https://ingest.revitcortex.dev`
  unless explicitly enabled.
- The PBI "live" path opens an `HttpListener` bound to loopback on port 27016 and
  performs non-destructive operations only.
- Licensing deserves a plain note: in `Release` builds the license gate resolves
  to `null` (`Licensing/LicenseBootstrap.cs`, `LicenseGate.cs`), i.e. the vendor
  ships the release path fully functional and *without* a backend check, and says
  so in its own comments ("RELEASE before the real backend: fail-closed-honest").
  This is not a crack we applied — it is upstream behaviour at commit `8b2556d`.
- Server port: **8080** by default (`REVITCORTEX_PORT` environment variable or
  `~/.revitcortex/settings.json`).

## Codex registration state

`codex mcp list` shows `revitcortex` as **enabled**, pointing at the published
executable above, with `startup_timeout_sec = 120.0` and `tool_timeout_sec = 600.0`
matching the Horizun entry. `%USERPROFILE%\.codex\config.toml` carries exactly one
`[mcp_servers.revitcortex]` table; every other server
(`acervo-auditor-mcp`, `codex_app`, `cua_repl`, `horizun-revit`, `node_repl`,
`open-design`) is intact. A snapshot of the configuration taken during this task
is kept at `tool-lab/revitcortex/evidence/codex-config.toml.snapshot`; it was
scanned for tokens and contains none.

## Add-in trust

Revit persists an "Always Load" decision in
`HKCU\Software\Autodesk\Revit\Autodesk Revit 2027\CodeSigning` as a `REG_DWORD`
keyed by `AddInId`. Before this task the key held a single value —
`b8e5a2f0-3c1d-4e6a-9f2b-7a4c8d1e5f30 = 1` (Horizun, from the user's click
earlier today). That state is preserved as
`tool-lab/revitcortex/evidence/codesigning-backup.json`. RevitCortex is unsigned
(`NotSigned`), so without an equivalent entry Revit will raise the Security
dialog on the next start. Whether to pre-register
`A1B2C3D4-E5F6-7890-ABCD-EF1234567890 = 1` is a deliberate open decision
recorded in the handoff; the backup makes either choice reversible.

## Expected writes and network activity

- Add-in tree under `%APPDATA%\Autodesk\Revit\Addins\2027\` (manifest plus `RevitCortex\` payload).
- Publish tree under `vendor/RevitCortex/publish/server/` (gitignored).
- Durable state under `%USERPROFILE%\.revitcortex\` (settings, audit log) — created on first run.
- Client configuration: one `[mcp_servers.revitcortex]` table beside existing entries.
- Network: nothing is downloaded by the deploy. The MCP server speaks stdio to its client;
  the optional PBI listener binds loopback only; telemetry is off. No outbound call is made to
  install, register or run the bridge.

## Rollback / uninstall path

1. Close Revit and the MCP client.
2. Remove `%APPDATA%\Autodesk\Revit\Addins\2027\RevitCortex.addin` and the `RevitCortex\` payload directory.
3. `codex mcp remove revitcortex`.
4. `%USERPROFILE%\.revitcortex\` and the optional `CodeSigning` registry value are independent of the
   add-in and are removed only on explicit request.
5. The vendor checkout, the isolated `.dotnet/` SDK and the publish tree can be deleted wholesale;
   nothing outside the repository and the two Revit/Cortex paths above was touched.

## Consequences for Plan 02

- P02-T14 can proceed as soon as Revit has restarted once with the add-in loaded: the
  `Cortex Switch` is off by default and must be turned on in the ribbon before the bridge answers.
- P02-T15's A/B comparison is unaffected by the doc/binary tool-count divergence, but the tool map
  must be generated from `tool-catalog.json`, and every Horizun result already recorded stays valid
  because RevitCortex was never loaded during those runs.
- `EnableCodeExecution` is to remain `false`; no Amanda task may enable it. Where scripted behaviour is
  required, use dedicated typed tools or the planned C# fallback in P02-T16.

