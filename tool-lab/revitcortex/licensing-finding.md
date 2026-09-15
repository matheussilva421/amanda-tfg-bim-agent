# RevitCortex licensing finding — no paid tier is required, and nothing here is bought

Task: P02-T14. Question asked by the owner, twice and in plain words: "Não quero pagar nada."
and "nada premium, que custe ou com assinatura." This note answers that question with the
artefacts that ship on this machine, so the answer can be re-checked instead of believed.

## Conclusion

RevitCortex is MIT-licensed upstream and the published binary that runs here contains no
license enforcement path. Nothing in this project was purchased, activated, subscribed or
keyed, and nothing needs to be. The product label "RevitCortex Premium" appears in the
add-in UI and in its localization table, but on the installed build there is no gate behind
it, no price, no store endpoint and no activation requirement.

## Evidence, by layer

### 1. Upstream license

`vendor/RevitCortex/LICENSE` (1091 B) is the MIT License, `Copyright (c) 2026 Luigi Dattilo`.
That is the whole legal frame: permission to use, copy, modify and distribute, with no fee,
no royalty and no seat count. It is checked into this repository at pinned commit
`8b2556daefb2bf88f0a7a17bf28f2352fe0b0e33`.

### 2. What the shipped code actually does about licensing

`src/RevitCortex.Plugin/Licensing/LicenseBootstrap.cs` has two mutually exclusive branches:

- The `#if DEBUG_R23 || ... || DEBUG_R27` branch builds a real `LicenseManager` backed by
  `DevLicenseBackend`, a local file-based dev backend whose plan table is
  `CORTEX-ACTIVE-2026`, `CORTEX-TRIAL-14`, `CORTEX-GRACE`. Its own comment says it exists so
  "the gate can be exercised live" and that "Debug builds never ship". There is no price, no
  remote authority and no payment call anywhere in it — it mints tokens locally from a file
  key store under the user profile.
- The `#else` branch, which is what a Release build compiles, is three lines of intent:
  `Gate = null; Manager = null; Backend = null;` under the comment "RELEASE before the real
  backend: fail-closed-honest. No FakeLicenseBackend (it accepts any key). Gate null => NO
  gating => app runs full".

`src/RevitCortex.Plugin/CortexRouter.cs` is where that null is consumed: the gate is stored
as `Licensing.LicenseGate? _licenseGate`, and the enforcement line is
`if (_licenseGate != null && !_licenseGate.Allows(toolName, IsToolReadOnly))`. A null gate
therefore skips the branch entirely. Even when a gate exists it blocks "only write" tools,
and the comment on the field records the null case as "today's behavior".

### 3. What the installed binary on this machine contains

The add-in installed under `%APPDATA%\Autodesk\Revit\Addins\2027\RevitCortex` is byte-identical
to the `Release R27` build output produced in P02-T13:

| File | Bytes | sha256 | Release build output |
| --- | --- | --- | --- |
| `RevitCortex.Plugin.dll` | 491520 | `E01135D08A2EBCB13A8DBBCD2914E3E51637B5825A802008A59F2BE7E6C325F9` | sha256 matches exactly |
| `RevitCortex.Core.dll` | 70656 | `C6F14C75B6657195937CECFAF9F02088428F2109E322515E4DD0FF36D1DAB0F0` | sha256 matches exactly |
| `RevitCortex.Tools.dll` | 2029568 | `09FA571025767065293A612A01441CCE48EDCE50335BC16FD846D1F22C7115A0` | Release R27 output |

A string scan of all 19 installed DLLs (ASCII and UTF-16LE) looked for `LicenseGate`,
`LicenseBootstrap`, `LicenseManager`, `DevLicenseBackend`, `license.gate_blocked`,
`dev-license-key.json`, `RevitCortex Premium`, the three dev keys and `license.json`:

- `RevitCortex.Plugin.dll` carries the type names `LicenseGate`, `LicenseBootstrap` and
  `LicenseManager` and the product label `RevitCortex Premium` — that is the code that
  *compiles into* the plugin, not proof that it was *built* in Debug. `DevLicenseBackend` is
  absent from the plugin assembly, which is where the Debug branch would have pulled it in
  through `LicenseBootstrap`.
- `RevitCortex.Core.dll` carries `LicenseManager` and `DevLicenseBackend` type names because
  Core compiles those source files regardless of configuration; the configured dev keys and
  the dev key file name did not surface as literals there, and `RevitCortex Premium` is not
  in Core at all.
- No DLL contains a licensing URL, a store link or a purchase endpoint.

The string scan alone cannot date the debug symbols, so the decisive test is the hash: the
installed DLL is the artifact of the Release configuration in which the `#else` branch runs.

### 4. Runtime behaviour confirms it

The ribbon exposes a `License & Account` button (`Commands/OpenLicense.cs`). Its activate
handler reads `LicenseBootstrap.Manager` and, when that is null, shows
`license.dev_transparent`, the string "Dev profile - licensing is transparent (always active)."
That dialog was not raised during the live session because the button has not been pressed;
the point is that with `Manager` null there is no key field to fill and no key to buy.
The write tools answered normally over the bridge while this finding was written, which is the
behaviour the null gate predicts.

### 5. Where the word "Premium" does come from

Two unrelated places, neither of them a Cortex paywall:

- `RevitCortex.Plugin` localization strings `license.gate_blocked` and
  `license.gate_suggestion` mention "RevitCortex Premium" only as the product name in the
  message that would be shown if a gate existed and refused a write tool.
- The vendor's Power BI documentation discusses Microsoft's Power BI Premium capacity as a
  property of the *user's* Microsoft tenant, in the context of scheduled refresh quotas. That
  is Microsoft licensing for a feature this project does not use.

A documentation scan for `purchase`, `price`, `EUR`, `USD`, `subscribe` and similar terms
over the pinned source returns no Cortex pricing surface. The only paid tiers named anywhere
in the tree belong to Microsoft Power BI.

## What this means for the owner's instruction

The instruction "não quero pagar nada" and "nada premium, que custe ou com assinatura" is
satisfied without any action: this project does not need, request or obtain a paid Cortex
tier, and the add-in as installed does not ask for one. No purchase, subscription, trial key
or activation is part of the current or planned work, and the fallback path in P02-T16 (a
first-party C# ExternalCommand compiled from `tool-lab/custom-api/`) depends on nothing but
the Revit API that is already licensed on this machine.

Two neighbouring edges are recorded here so nobody mistakes them later:

- The bridge listens on `127.0.0.1:8080` only (loopback, pid 39140), so nothing about the
  free tier requires exposing the machine to the network.
- `EnableCodeExecution` remains `false` in `~/.revitcortex/settings.json`. That is a separate
  safety setting, not a paid feature, and it stays off by project decision.
