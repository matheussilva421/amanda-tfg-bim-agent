# Horizun Revit MCP — source audit (P02-T04)

Audited 2026-09-15 against the checkout in `vendor/horizun-revit-mcp` and the
installation already present on this machine. Revit was closed during the whole
audit (`Get-Process Revit` returned nothing).

## Exact revision

- Repository: `https://github.com/HorizunGroup/horizun-revit-mcp.git`
- Local path: `vendor/horizun-revit-mcp` (gitignored; source stays out of the published repo)
- Commit: `cc4ea04e9ecfe547ad349f22e0864019ce1ead1f` (`cc4ea04`)
- Working tree: clean
- `global.json`: SDK `10.0.400`, `rollForward: disable`, `allowPrerelease: false`

## What the upstream documentation promises

`AGENTS.md` and `README.md` define three things this audit had to confirm or
contradict: the installer refuses to run with Revit open and changes nothing when
it refuses; every installed binary is read back and compared (stamped commit plus
SHA-256) against what was staged; and installation and client registration are two
internal phases of one action, where the registration phase waits for active
clients to exit before editing their configuration.

## Prerequisites on this machine

- Revit 2027.2, product version `20260716_1515(x64)`, at `C:\Program Files\Autodesk\Revit 2027`.
- .NET SDKs present: `8.0.422` only. The pinned `10.0.400` required by `global.json` is **absent**;
  no `.tools/dotnet` tree exists either.
- Revit process: absent for the entire audit.

## What is actually installed now

| Artifact | Path | SHA-256 |
| --- | --- | --- |
| MCP server | `%LOCALAPPDATA%\Programs\Horizun\MCP\server\horizun-mcp.exe` | `178a7cc335ec80250c0f605010a7e092eca204f85417efa535f876dddeae908d` |
| Server assembly | `%LOCALAPPDATA%\Programs\Horizun\MCP\server\horizun-mcp.dll` | `dd360b3020e9c4ae652047015d0ba127a8fda2a68612e9ca53eb2bd4d3b1514f` |
| Add-in assembly | `%APPDATA%\Autodesk\Revit\Addins\2027\Horizun\Horizun.Revit.dll` | `3f70b2d5929d345573e039f47858b3d51b23a82ccf67cb03d0ab0116671a7218` |
| Add-in manifest | `%APPDATA%\Autodesk\Revit\Addins\2027\Horizun.addin` | `baeae873b9735067bcee515d78e98e9f78d66705d202b1bff34120d391b93b91` |

The binaries carry build timestamps of 2026-09-15 08:34, so this is a built-from-source
deployment rather than the published installer release.

The commit link is now **VERIFIED**, by three independent reads:

1. The installer wrote `%LOCALAPPDATA%\Programs\Horizun\MCP\manifest.json` (Schema 2)
   recording `Commit: cc4ea04e9ecfe547ad349f22e0864019ce1ead1f`, `CleanTree: true`,
   `SourceInstall: true` and `Config: Release`.
2. Every SHA-256 in that manifest was recomputed from the files in place and matches,
   4 of 4, including both Revit-side artifacts.
3. The 40-character commit stamp is present verbatim inside `horizun-mcp.dll`,
   `Horizun.Revit.dll` and the installer manifest itself.

So the deployed bridge and the pinned checkout are the same revision. What remains
unproven is behaviour, not provenance: `horizun_health` has never answered, because
Revit has not been started even once by the user.

The add-in manifests Revit-side state is pristine: `AddinsData\AddInsSettings.json` has
`DisableAllAddIns: false` and no per-add-in override, so nothing has silently disabled
the Horizun add-in.

## Codex registration state

`codex mcp list` shows `horizun-revit` as `enabled` pointing at the exact installed path,
and `%USERPROFILE%\.codex\config.toml` carries the Horizun-owned table with
`startup_timeout_sec = 120` and `tool_timeout_sec = 600`. Every other MCP server
(`acervo-auditor-mcp`, `cua_repl`, `node_repl`, `open-design`, `codex_app`) is intact.

`%LOCALAPPDATA%\Horizun\install-status.json` reports `state: waiting_for_client_exit`
with `running_clients: [Claude, Codex]` and the explicit note that no configuration has
been edited. The configuration is nevertheless already correct, so this record is a
stale pending marker from the installer, not an unfinished registration.

## Expected writes and network activity

- Add-in tree under `%APPDATA%\Autodesk\Revit\Addins\2027\` (manifest plus `Horizun\` payload).
- Server tree under `%LOCALAPPDATA%\Programs\Horizun\MCP\server\`.
- Durable state under `%USERPROFILE%\.horizun\` (owner-local add-in state).
- Client configuration: one `[mcp_servers.horizun-revit]` table, added beside existing entries.
- Network: the source-build path downloads nothing; the later check of `horizun_health` is local IPC.
  No outbound call is made to install or to run the bridge.

## Rollback / uninstall path

1. Close Revit and the MCP client.
2. Uninstall Horizun Revit MCP from Windows Installed apps, or remove the three trees above.
3. Remove the `[mcp_servers.horizun-revit]` table from `%USERPROFILE%\.codex\config.toml`
   (or run `codex mcp remove horizun-revit`).
4. `%USERPROFILE%\.horizun\` state and the local signing trust are kept by default and
   only purged on explicit request.

## Consequences for Plan 02

### Why the source installer was not re-run

Step 5 of P02-T04 asks for `install.ps1` to be executed from the checkout. It was
deliberately not re-run, for two reasons that this audit established rather than assumed:

- A deployment built from *this same commit* is already installed and verified end to end
  (commit stamp plus 4 of 4 hashes). Re-running the installer would overwrite a known-good,
  fully accounted tree to reach the same revision.
- `global.json` pins SDK `10.0.400` with `rollForward: disable`, and that SDK is absent
  from this machine. The installer's build step would therefore fail before it could
  produce the matching binaries.

The honest state is: the install exists, its provenance is proven, and re-installing it is
blocked on the missing SDK rather than on anything wrong with the install. Installing
`10.0.400` stays available as the unblocking step if a rebuild is ever needed.

- Horizun is **installed but never proven**. No capability may be recorded as PASS before
  `horizun_health` answers `status: healthy` and the read/write persistence tests run
  against a disposable fixture in P02-T05 onwards.
- The pinned SDK `10.0.400` is missing, so a rebuild is not currently possible. That only
  matters for rebuilding or upgrading; it does not block proving the installed bridge.
- Revit must be started by the user at least once to answer the unsigned add-in Security
  dialog with **Always Load**. That is the next user-exclusive action in this phase.
- The add-in is correct on disk while Revit is closed; nothing else about the bridge can be
  established without Revit running.
