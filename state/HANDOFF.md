# Current Handoff

## Current state — P7-T01/R05 blocked at partial recovery

Authorization remains limited to P7-T01/R05 on RUN-003. R06 and later remain NOT STARTED.

- Formal state is revision 249: P7-T01 is BLOCKED_BY_TOOL, stage R04, and R05_PARTIAL_RECOVERY_UNVERIFIED is the active blocker. RUNNER_TRANSPORT_UNREACHABLE was resolved through the official runner in the elevated current-user context. `PROJECT_STATE.last_verified_commit` points to `1df883bb4cbf6fbe8bd75481019c55214449cc3e`.
- The official runner at 22:21:31Z and 22:34:27Z passed live health, zero-other-client, exact target/build/PID 12660, command registry 73/73, provider tools 80/80, MCP tools/list 80, full_write, and mcp_paused=false. The live model failed the accepted P6 element-count gate and entered guarded recovery. At 22:34:27Z the English Area reading for ElementId 331188 was state=absent, unit=m2, with no measured value/provenance. Localized Área remains unconfirmed by live takeoff. No value or unit was inferred; runner lease was released; no R05 write/save/checkpoint occurred.
- Latest diagnostic-only P6 readback: revit/production/journals/R05-2f373fcb3511-p6-readback-diagnostic-8d2a63c9f246.json. Exact checkpoint manifest verified, 25 typed rows and complete coverage; acceptance_gate_passed=false and model_write_performed=false. Open target remains 5,152,768 bytes at its prior 2026-09-27 mtime. Do not hash or close it. Project writer lock is absent.
- Recent elevated read-only process inspection classified PID 12660 as Revit 2027 at the expected executable path, with RevitAPI and Horizun loaded, a usable window handle, and SessionId 5. PID 3364 has neither module nor a window handle; leave it untouched. The next official runner must freshly verify the exact active RUN-003 document.
- The local TDD change requests Area and Área as distinct typed m2 takeoff quantities. It uses Área only when Area is explicitly absent and the localized reading is measured with provenance; other English states fail closed. If both readings are measured, their decimal values must agree within an inclusive 0.01 m2. The selected parameter flows into recovery evidence; no geometry_area fallback is used.
- Independent review found that ULP tolerance could accept a value just over 0.01 m2, then found downstream `math.isclose` could reject the permitted exact boundary. RED tests reproduced both. Decimal(str(value)) now preserves the inclusive boundary in both the parameter comparison and geometry validator; the exact-boundary test exercises query through recovery validation, and a just-over case is rejected. Targeted Area/geometry tests pass 11/11. The combined seven-module R05 suite plus state gates passes 183 tests, with one unrelated R04 evidence-hash test deselected and zero failures. Scoped diff check and YAML parsing pass. Ruff retains eight pre-existing findings (seven TRY004 and one RUF059); the introduced import-order finding was corrected. Final independent read-only re-review found no findings.
- Implementation/test/evidence commit `1df883bb4cbf6fbe8bd75481019c55214449cc3e` and formal-state commit `d21b4840cf5eaa23ac428f7d1cd5e6da5d0d3e3e` are on `main`. The normal sandboxed remote check failed, but the non-forced elevated push succeeded and a fresh elevated `git ls-remote` confirmed `origin/main` at `d21b4840cf5eaa23ac428f7d1cd5e6da5d0d3e3e`. This final handoff update is a separate pending documentation change. RC01 ACL-visible deletions and frozen R04 presentation outputs remain untouched and unstaged.

Next: commit and push this final handoff update, then perform a fresh read-only check of PID 12660 and the writer lock before one exact R05-only runner invocation. The 600-second quiet window after 22:34:27Z elapsed at 22:44:27Z. Require fresh health, exclusive-client status, exact target/build/PID, provider/tool/write controls, runner-managed lease, P6 reconciliation, and all eight measured m2 readings before any R05 write. Then continue WRITE → independent READ → VERIFY → SAVE/CHECKPOINT → CLOSE/REOPEN/READBACK. Stop at R05.

    .\.venv\Scripts\python.exe scripts\run_amanda_production.py --rvt 'revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt' --resume-run003-study --reuse-existing-run003-lease --max-stage R05 --revit-pid 12660 --execute

## Previous update — P7-T01/R05 after the 22:21 runner attempt (superseded)

Authorization remains limited to P7-T01/R05 on RUN-003. Do not execute R06 or later.

- `PROJECT_STATE.yaml` is revision 248; P7-T01 remains `BLOCKED_BY_TOOL`, stage remains R04, and R06 is NOT STARTED. Code commit `58cd0ac5c78a74a35214cc120e20638ace20f6e3` adds bounded diagnostics for invalid Area readings.
- The original transport blocker is resolved for the official runner in the elevated current-user context. At 2026-09-28 22:21:31Z it passed health, zero-other-client, exact target/build/PID 12660, command registry 73/73, unrestricted provider tools 80/80, MCP tools/list 80, `full_write`, and `mcp_paused=false`. Sandboxed attempts had failed discovery because of the owner-only ACL. No token was read.
- Current blocker is `R05_PARTIAL_RECOVERY_UNVERIFIED:BLOCKING`. The live RUN-003 model failed the accepted P6 element-count check and entered guarded recovery for the known unsaved partial. The exact eight-floor Area takeoff rejected ElementId 331188 at the measured-m2 gate. No unit/value was inferred; no R05 write, save, or checkpoint occurred. The runner released its lease.
- Diagnostic-only P6 readback: `revit/production/journals/R05-2f373fcb3511-p6-readback-diagnostic-4df7d40a2c35.json`; checkpoint manifest verified, 25 typed rows, complete coverage, but acceptance_gate_passed=false and model_write_performed=false. The open target remains 5,152,768 bytes with its prior 2026-09-27 mtime; do not hash or close it. Writer lock is absent.
- TDD for bounded failure details: the new test failed first because state/unit were omitted; after implementation, the diagnostic and incomplete-reading tests passed 2/2. Broader R05 suite: 157 passed, 1 unrelated R04 evidence-hash test deselected, 0 failed. The task-graph/dashboard/state-consistency gate passed 21/21 after the formal blocker transition. Ruff retains 8 existing runner findings.
- Code/data commit: `58cd0ac5c78a74a35214cc120e20638ace20f6e3`; prior state commit `999f8bacc107fd7a4fbf5e6fdfcd7e2e443bf633` was pushed to GitHub. The new state revision 248 is not yet committed/pushed. A fresh `ls-remote` failed over TCP 443. RC01 deletions and R04 presentation files remain untouched and unstaged.

The latest provider request returned at 22:21:31Z. Do not call Horizun again before 22:31:31Z. After that, recheck Revit PID and lock state, publish the current state, then run the exact R05-only runner once. Its invalid-reading error now prints only bounded state/unit/value-type metadata, never the numeric measurement. Continue only if exact partial/P6 reconciliation and all eight measured m2 readings pass; then finish R05 WRITE → READ → VERIFY → SAVE/CHECKPOINT → CLOSE/REOPEN/READBACK. Stop at R05.

``` powershell
.\.venv\Scripts\python.exe scripts\run_amanda_production.py --rvt 'revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt' --resume-run003-study --reuse-existing-run003-lease --max-stage R05 --revit-pid 12660 --execute
```

## Previous update — P7-T01/R05 before the 22:21 runner attempt (superseded)

Authorization remains limited to P7-T01/R05 on RUN-003. Do not start R06 or later.

- `PROJECT_STATE.yaml` is revision 247; `P7-T01` remains `BLOCKED_BY_TOOL`, `revit_stage` remains R04, and R06 is NOT STARTED. The latest locally verified code commit is `c679db483dede056cd0223488f8444d45cf2b229`.
- The ACL hypothesis is now supported by a discriminating run: ordinary sandboxed `.venv` runner attempts failed at `horizun_health` with “no Revit is reachable”; the same official runner in the current user's elevated context reached typed health/session checks, selected Revit PID 12660, acquired and released the normal writer lease, and entered P6/partial recovery. No discovery token was read. This proves the access context changes discovery behavior, while the provider's full readiness gates still need fresh live evidence.
- That live attempt stopped before any R05 write because the existing `horizun_query_model` Area value for `FLOOR-RES_PAV_A-L1` contained no unit. No unit was inferred. The runner closed the inspected P6 checkpoint without saving and released its lease. The diagnostic `revit/production/journals/R05-2f373fcb3511-p6-readback-diagnostic-77140d89d42a.json` records the 25-row readback and the accepted/observed fingerprint mismatch; it is diagnostic-only, not an acceptance pass.
- The implementation now requires a clean, complete provider command registry; an unrestricted tool pack; `full_write`; `mcp_paused=false`; and an unpaginated MCP `tools/list` matching provider health, all on the same MCP process. During partial recovery it requests Area for exactly the eight known floors through `horizun_quantities` with an explicit `m2` contract, and fails closed on incomplete coverage, identity, unit, or provenance. TDD and focused suites pass; live use of these new gates is pending.
- Test command: `.venv\\Scripts\\python.exe -m pytest tests/unit/test_run_amanda_production.py tests/unit/test_production_layout_bim.py tests/unit/test_run003_study_authorization.py tests/unit/test_bim_production_contract.py tests/unit/test_persistence_plan.py tests/unit/test_mcp_probe_transport_pinning.py tests/unit/test_bim_transport_env.py -q -k "not test_production_registry_binds_r04_mass_and_preview_visibility_to_lab_proof"` -> 156 passed, 1 deselected, 0 failed. The deselected R04 lab-evidence hash mismatch predates this task. Ruff reports 10 existing findings (8 in the runner and 2 transport annotations); no new finding remains. Scoped `git diff --check` passed.
- The code/tests/diagnostic are committed as `c679db483dede056cd0223488f8444d45cf2b229`. The state/handoff update is pending its own commit. A fresh GitHub ref read previously failed over TCP 443; remote status is not verified. RC01 deletions and R04 presentation artifacts remain unstaged and untouched.
- Revit PIDs 12660 and 3364 were recently responsive; PID 3364 remains untouched. The RUN-003 document remains open. Do not hash or close it. No R05 save, model write, or checkpoint has occurred. Recheck the process and ensure the project lock is absent before the next invocation.

Next, after publishing the state update, perform one exact `.venv` production-runner invocation with `sandbox_permissions=require_escalated`. Do not use a separate Horizun client. Require current health, zero other clients, exact RUN-003 path/build/PID, the complete registry/tool-list/full-write/unpaused gates, runner-managed lease, P6 reconciliation, and all eight explicit `m2` Area readings before any R05 write. Continue through R05 WRITE → independent READ → VERIFY → SAVE/CHECKPOINT → CLOSE/REOPEN/READBACK and capture evidence only if every gate passes. Stop at R05. On failure, update this handoff and wait a full 600 seconds before another provider call.

```powershell
.\.venv\Scripts\python.exe scripts\run_amanda_production.py --rvt 'revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt' --resume-run003-study --reuse-existing-run003-lease --max-stage R05 --revit-pid 12660 --execute
```

- State validation: focused task-graph/dashboard gate passed 18/18; all four edited YAML files parsed; scoped diff check passed. A wider legacy migration command returned 3 failures because its frozen assertions still expect the former P4 snapshot while this checkout is at P7 and P4-T01 is PASS. No current state was changed to satisfy those historical assertions.

## Previous update — P7-T01/R05 transport discovery (superseded)

The user explicitly authorizes P7-T01/R05 on RUN-003. Current authorization is R05 only; do not execute R06 or later. The update above supersedes this transport discovery diagnosis.

- The exact objective file was reread. `PROJECT_STATE.yaml` is now revision 246; P7-T01 remains `BLOCKED_BY_TOOL`, `revit_stage` remains R04, and `last_verified_commit` remains the runner code commit `73f71e0c15bb169d88729c0530bffafc975a81c0`.
- A second invocation of the `.venv` production runner returned the same `no Revit is reachable` error. It stopped at `horizun_health`; no PID pinning, capability/target/checkpoint reads, lease acquisition, or model operation followed. The 600-second quiet window has now elapsed. No standalone Horizun client was used.
- Fresh `Get-Process` evidence at 21:18:25 UTC found Revit PIDs 12660 and 3364 responding, with start times 20:25:29Z and 20:42:24Z. `journal.0037.txt` previously bound PID 12660, its Horizun startup, and the exact RUN-003 working document path. `Get-CimInstance Win32_Process` was denied by the sandbox, so no current command-line/window-title claim is made. PID 3364 was not touched.
- Official Horizun documentation locates discovery under `%USERPROFILE%\.horizun`. The current file is `C:\Users\slvma\.horizun\discovery\revit-2027-12660.json`, 2,689 bytes, last modified at 20:27:14Z. Ordinary sandbox reads and ACL inspection were denied. An approved elevated, read-only ACL inspection reported owner `DELL-G15-5530\slvma` and one non-inherited FullControl allow entry for that same user. The discovery contents were not opened because they contain a token. This raises the hypothesis that the restricted runner child cannot read the owner-only discovery file; it is not yet proven.
- The next discriminating action is one invocation of the exact R05-only production runner in the current user's unsandboxed context, allowing the process to read its ACL-protected discovery file without displaying the token. If auto-review rejects that command, stop and record the rejection. If health fails again, stop runner/provider calls for another 600 seconds and keep the blocker. If health passes, continue only through runner-enforced health, client-count, exact target/build/PID, lease, P6 and partial-floor/Area gates before any R05 write.
- Live Revit window inventory was not available through the current computer-use surface (`apps` returned empty); the current process response plus journal binding are recorded as partial live evidence. Require the runner's typed exact-document health before a lease or write.
- The writer lock is absent. The open working RVT remains unhashable while Revit holds it; last pre-open hash remains `F5BEEB6BF7D544710EA3A35DDE2B8A880E78FC4E284E12CB4A90E1BCCF982B19`. No save, close, write, checkpoint, or R05 model change occurred.
- State/doc validation: YAML parsed 3/3. Focused repository-hygiene, status-consistency, and task-graph checks initially exposed two stale dashboard/handoff text contracts; after restoring the required current-state wording, the final command passed 30/30. Scoped `git diff --check` passed.
- Local `main` is `898694a68b8fb2d0b48b908f2918eacbe96ee1bc`; commits through this state were pushed successfully earlier. The current `git ls-remote` could not connect to GitHub over port 443, so a fresh remote SHA is unavailable. Pre-existing RC01 deletions and untracked R04 presentation artifacts remain unstaged and untouched.

```powershell
.\.venv\Scripts\python.exe scripts\run_amanda_production.py --rvt 'revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt' --resume-run003-study --reuse-existing-run003-lease --max-stage R05 --revit-pid 12660 --execute
```

**Resume boundary:** first perform that single runner attempt with `sandbox_permissions=require_escalated`, and make no direct Horizun call. On health failure preserve P7-T01 as blocked and update this handoff. On health success follow only R05 gates; R06 remains NOT STARTED.

## Previous update — P7-T01/R05 live runner gate (superseded)

## 2026-09-28 — P7-T01/R05 live runner gate (continuation)

Authorization from `C:\Users\slvma\.codex\attachments\2d812ca3-d648-4941-bd6e-a2f73697395c\goal-objective.md` is limited to P7-T01/R05 on RUN-003. R06 and later remain NOT STARTED.

- Runner correction committed as `73f71e0c15bb169d88729c0530bffafc975a81c0`. TDD RED reproduced two ordering failures: an unhealthy provider could acquire the lease, and a healthy provider saw lease acquisition before `horizun_health`. Moving study lease acquisition behind typed health, session validation, and PID target selection made both tests pass. Command `\.venv\Scripts\python.exe -m pytest tests/unit/test_run_amanda_production.py -q`: 89 passed, 0 failed. The combined R05 suite passed 221 tests with one unrelated pre-existing R04 visibility-evidence test deselected; that test's registry hash disagrees with the committed evidence file. Fresh R05 dry-run planned 704 operations (9 floors, 7 roofs, 688 walls), R05 only. Targeted `git diff --check` passed. Ruff reported nine baseline findings, none on the changed lines.
- Revit 2027 build `27.2.0.39` was brought to the foreground through the computer-use UI. The exact RUN-003 working path was entered in Revit's Open dialog. Journal `journal.0037.txt` starts at `17:25:30.744` Fortaleza time, matching process 12660's `20:25:29.671Z` start; it names `Session12660_P0MainQueue`, records Horizun MCP 1.3.3.0 starting, then records the exact RUN-003 path opened and its `DocSymbol`. This binds the active RUN-003 document and loaded add-in to PID 12660. A second responding Revit process, PID 3364, also exists; do not terminate it. The runner's typed health still cannot discover the Revit session, so health, zero-other-client status, and typed active-document readback remain unverified.
- The first runner invocation used global Python and stopped before runner startup because `ortools` was missing. The corrected `.venv` invocation planned only R05 and then received `Error: no Revit is reachable` from `horizun_health`. It stopped before PID pinning, capability/target/checkpoint reads, lease acquisition, or any model operation. The direct Horizun tool was not called.
- `state/locks/revit-writer.lock` is absent. The exact working RVT is open and locked by Revit; size remains 5,152,768 bytes and mtime remains `2026-09-27T09:30:38.2675368Z`. Its last readable pre-open SHA-256 was `F5BEEB6BF7D544710EA3A35DDE2B8A880E78FC4E284E12CB4A90E1BCCF982B19`; hashing it now fails because the open process holds it. No save or close was requested. Treat the current on-disk hash as unverified and preserve the open document unchanged.
- The runner request had returned by `2026-09-28 20:56:15 UTC`; use that as the conservative start of the 600-second quiet window. Do not contact Horizun again before `2026-09-28 21:06:15 UTC`, and do not use a separate MCP client. Before a retry, recheck the live process/journal and preserve PID 12660 as the current candidate. Use the exact R05 command below with the freshly confirmed PID. If its own health still says no Revit is reachable, stop and keep P7-T01 blocked; do not acquire/release a lease or substitute a direct tool call.

```powershell
.\.venv\Scripts\python.exe scripts\run_amanda_production.py --rvt 'revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt' --resume-run003-study --reuse-existing-run003-lease --max-stage R05 --revit-pid <fresh-active-Revit-PID> --execute
```
- Local code commit is `73f71e0c15bb169d88729c0530bffafc975a81c0` on `main`; the state/handoff closeout is `821b2aa92697a0dab71fe79a0dce8699f3e4ba60`. Both were pushed to `origin/main`, and `git ls-remote origin refs/heads/main` returned `821b2aa92697a0dab71fe79a0dce8699f3e4ba60`. Existing RC01 deletions and the untracked R04 presentation package remain untouched and unstaged.

**Resume boundary:** P7-T01 remains `BLOCKED_BY_TOOL`; no live R05 write, save, checkpoint, or cold-reopen verification occurred. After the quiet window, require runner health, zero other clients, exact active RUN-003 path/build/PID, lease and P6 reconciliation, then continue only through R05 WRITE → READ → VERIFY and its save/close/reopen/readback gates. Stop at R05.

## 2026-09-28 — Pacote final R04 para orientação (ZIP) — sessão concluída

Entrega intermediária R04 finalizada e empacotada para a orientadora, a partir do checkpoint P6 aceito, sem tocar em R05/R06 nem em RC01.

- Derivado de apresentação salvo e verificado: `revit/production/presentation/RUN-003-R04-ORIENTACAO-20260928/AMANDA-RUN-003-R04-PRESENTATION-20260928.rvt`, SHA-256 `bf5f05050679191a0bf2ce4b731441aa20306dd36cfe426a3f2f37c33c42121a`, 5.013.504 bytes. Checkpoint final (cópia byte a byte) em `snapshots/AMANDA-RUN-003-R04-PRESENTATION-FINAL-ORIENTADORA.rvt`, mesmo hash.
- Ciclo SAVE → CLOSE → REOPEN com auditoria (Revit 2027, sem upgrade) executado; leitura tipada dos 25 elementos espaciais com fingerprint `1aac5d79b05b159a` antes e depois — 25/25, GEOMETRY_DIFFERENCES = 0 (comparação tipada campo a campo; a extração bruta da API difere apenas por ruído de conversão de 4,4e-7 m, documentado).
- Prancha A1 (`R04-01`, folha 331392) reorganizada: desenho maior à esquerda, título no topo, programa oficial e ressalvas, coluna de setores A–M e organização do programa à direita. Title block genérico Autodesk removido (delete tipado verificado, 1 + 9 em cascata) e substituído por carimbo acadêmico desenhado na folha (TFG, projeto, Aluno(a): Amanda, prancha, etapa, data 28/09/2026, escala 1:300, número R04-01, moldura e divisórias), sem inventar instituição/orientadora/matrícula/endereço.
- Correção do Pavilhão D na prancha: “F — Residencial D — pavilhão comunitário: convivência, refeitório e copa” e “Residencial: 3 pavilhões de dormitórios/família + 1 pavilhão comunitário.”; descrições A/B/C alinhadas ao contrato canônico; programa oficial inalterado.
- Vistas finais: 01 implantação (331218), 02 isométrica geral (331230, rótulos discretos), 03 residencial (331241, A/B/C/D com D comunitário), 04 administrativo (331252, rótulo “2 pavimentos”), 05 serviços/capacitação (331283), 06 infantil + playground (331571, vista 3D nova com massa e playground) e 07 corte do administrativo (331581, “Nível 1/Nível 2”). Massas reativadas nas plantas, cores de setor por vista (overrides de exibição) e enquadramentos por crop/seção calculados — nenhuma geometria alterada.
- Pacote: `revit/production/presentation/RUN-003-R04-ORIENTACAO-20260928/delivery/AMANDA-TFG-R04-ORIENTADORA-20260928.zip`, 16.604.517 bytes, SHA-256 `bcc00f88ea6db7f7b940445e1a2be6afbb60fd8f9e7bd35fe68975732ae2c83a`; 56 arquivos conferidos por `SHA256SUMS.txt` após extração em pasta temporária (`AMANDA-TFG-R04-ORIENTADORA-20260928.zip.verification.json`, 0 problemas). O ZIP contém prancha, 7 PDFs de vistas, 8 PNGs, os três RVTs (P6, derivado editável e checkpoint final), relatórios, README, manifesto e evidências; caminhos internos relativos.
- Relatório final: `docs/reports/R04-orientadora-final-package-2026-09-28.md` (com o SHA-256 do ZIP). README da entrega: `LEIA-ME-ORIENTADORA.md` no pacote, com “ABRIR PRIMEIRO: 01_PRANCHA/R04-01-PRANCHA-A1.pdf”.
- Lease de escrita: readquirido pelo mecanismo normal do projeto (`WriterLock.acquire(reclaim_abandoned=True)`, geração 2, keeper PID 57852) após o dono anterior (PID 7860) estar comprovadamente morto; liberado ao fim da sessão pelo próprio token do owner. Nenhum force-release, nenhum lock removido à mão.
- P7-T01/R05 continua pendente e bloqueado pelo gate de transporte do runner; R06 não iniciado; RC01 intocado; GeoNatal não pesquisado; S01/S02/R12 não reutilizados.

### Limite exato de retomada

O pacote R04 para orientação está fechado e verificado. Não iniciar R05/R06 a partir dele. Para uso da orientadora, basta o ZIP em `delivery/`; para novas alterações de apresentação, abrir o derivado salvo, trabalhar e repetir SAVE → CLOSE → REOPEN → readback tipado (25/25) antes de reexportar e reempacotar.

## 2026-09-28 — R04 presentation packet closeout (supplemental)

The presentation-only R04 board and six supporting views are saved from the accepted P6 source in a dedicated RUN-003 derivative. This is supplemental evidence for the P6/R04 design study; it does not start or advance P7/R05 or R06.

- Source checkpoint SHA-256: `8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326`. Final presentation checkpoint: `revit/production/presentation/RUN-003-R04-ORIENTACAO-20260928/snapshots/AMANDA-RUN-003-R04-PRESENTATION-FINAL-20260928.rvt`, SHA-256 `45bac6f94fc8fec465ea52c20fe6cd5a37c8159466a19fcff0b1eb329dc19d4b`, 5,009,408 bytes.
- The saved derivative was closed and reopened with Revit 2027 audit, without upgrade. Fresh model readback matched the pre-presentation baseline row by row: 25/25 spatial elements, 7 masses + 14 floors + 4 roofs, zero identity/name/bounds differences at 1e-8 m tolerance, zero unreadable rows, complete coverage. The active file reported `is_modified=false` after export/capture.
- Sheet `R04-01`, ElementId 331392, has the A1 metric title block, one viewport, and 29 notes. The A1 PDF is 1 page at 841 × 594 mm. Six one-page A3 view PDFs and six PNGs are saved under `revit/production/presentation/RUN-003-R04-ORIENTACAO-20260928/exports/FINAL-20260928/`; see `RUN003-R04-PRESENTATION-MANIFEST.json` and `docs/reports/R04-presentation-RUN003-closeout-2026-09-28.md` for hashes and mapping.
- Visual review passed for the board and six exports. The child plan is a mass/playground-surface orientation view, not a detailed play design; its focused PNG uses a temporary crop around current elements 328658 and 329971 and confirms view restoration. The A1 title block still contains generic Autodesk consultant/project placeholders. Site coordinates remain normalized and unsurveyed.
- Horizun was HEALTHY at cold reopen (1.3.3; Revit 2027 build 27.2.0.39, PID 9128; exact document path matched; 73/73 registered commands; 80/80 tools visible; no other clients). Preserve the live RUN-003 presentation lease; do not release or reclaim it here.
- No P6 source edit, GeoNatal search, RC01 edit, S01/S02/R12 reuse, P7/R05 write, or R06 work occurred. `PROJECT_STATE.yaml` and `state/task-graph.yaml` remain unchanged: P7-T01 is still next and blocked at the runner transport gate; phase P7 remains PENDING.
- No code changed, so no automated tests were run. Verification consisted of provider/target health, cold reopen/audit, fresh typed geometry readback, checkpoint hash verification, PDF page geometry, SHA-256 inventory, and rendered visual review. Packet commit `dbbd658` is on `main` and push to `origin/main` succeeded. Only the curated `FINAL-20260928` directory, report, and handoff were staged; earlier captures/PDF drafts, baseline, snapshots, and the live lease keeper remain preserved outside that commit. Pre-existing RC01 deletions remained unstaged and untouched.

### Exact resume boundary

Treat this presentation derivative and its snapshot as read-only evidence unless a new task expressly authorizes presentation changes. Do not start P7/R05 or R06 from this closeout. For the formal next task, resolve the existing runner transport blocker and follow the current P7 task gate; preserve the RUN-003 lease until its original owner releases it normally.

## Historical 2026-09-27 — R04 presentation deliverable attempt (superseded above)

That was the status at the time of the 2026-09-27 handoff. It is superseded by the completed presentation closeout above.

- Read-only checks confirm the P6 checkpoint `revit/production/evidence/AMANDA-RUN-003-R04/P6-T01-CANON-011-RECONCILED-20260926.rvt` is Revit 2027, non-workshared, 4,960,256 bytes, with SHA-256 `8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326`, matching its manifest. Horizun is HEALTHY on Revit 2027 build 27.2.0.39, PID 56064; target selection is explicit, registry clean, 80/80 tools visible, and no document is open.
- The existing P6 capture manifest is bound to this checkpoint. It contains nine current captures. The child/playground attempt is excluded as near-blank; the only readable child/playground image is explicitly reference-only from the earlier `R04-T01` checkpoint. Do not present that older image as a current P6 capture.
- P6 readback names the seven masses in order: admin `328657`, child `328658`, residential `328659`–`328662`, services/capacitation `328663`. Site surfaces are patio `329943` (80 m²), therapeutic garden `329950` (80 m²), horta `329957` (30 m²), exercise `329964` (30 m²), playground `329971` (40 m²). The public administrative route is `331177`; the other two route marks and bounds are known, but their individual ElementIds must be resolved by a fresh typed query. The accepted top capture currently names only 15 of the 25 spatial elements, so it is insufficient for the requested complete implantation view.
- Candidate source views are implantation plan `8251`, overall isometric `328677`, admin mass `328688` plus floor plans `312`/`695`, residential `328699`, services `328710`, child `328721`. The current child view is not adequate for child plus playground; recapture or create a presentation view framing both current IDs. The P6 fingerprint reconciliation artifact also reports `p6_acceptance_gate_passed: false` and differing query fingerprints; for this presentation, establish a fresh typed geometry baseline from the byte-identical derivative before changing views, and independently compare the same spatial-element rows after save/reopen.
- A read-only Luna 6 xhigh subagent review was attempted as a sidecar but the agent-thread limit rejected the spawn; no agent ran, and no other model/agent was used.
- `state/locks/revit-writer.lock` still names `amanda-P7-RUN003-production`, generation 2, PID 28364, document identity `revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt`. The Windows process-start check inside the canonical `WriterLock` API returns the exact recorded start time `2026-09-26T22:38:20Z`, and `is_held_by_live_owner()` is true. An attempted `acquire(reclaim_abandoned=True)` correctly refused. Do not unlink, rewrite, bypass, or force-release this active lease. The current Codex thread has no attached terminal session for its `input()` keeper, and the P7 owner thread was not located in the visible thread list.
- An elevated read-only ancestry check traced PID 28364 → 20440 (`python.exe`) → 10592 (`pwsh.exe`) → 26712 (`codex-command-runner`) → 36324 (`codex.exe`), all in Windows SessionId 3. Thread history did not expose the originating tool `session_id`; OS PIDs are not substitutes for that session id. Release only through the original keeper's own input channel.
- The unrelated P7/R05 formal task remains unchanged in `PROJECT_STATE.yaml` and `state/task-graph.yaml`; this presentation request does not authorize P7/R05 or R06. RC01 deletions remain pre-existing and untouched. Only Luna 6 xhigh subagents are permitted; none were used.
- Resume only after the existing lease owner releases through its own keeper (`input()` prompt), then acquire a fresh lease through `src/amanda_agent/state/locks.py`, generation-fenced. Copy the P6 checkpoint byte-for-byte to a dedicated presentation path, verify the copy hash, inspect/read the active derivative, and make view/sheet/annotation-only changes. Verify geometry unchanged, reopen/read back, export and visually inspect all requested views and sheet, then update the formal state/handoff and Git evidence. Keep R05 and R06 unstarted.

## Current state — P7-T01/R05 blocked at production runner transport

This is the sole active resume point. P4-T01/BIM-00, R04, and P6-T01 remain complete. P7-T01 is `BLOCKED_BY_TOOL` because the approved production runner's installed stdio transport cannot reach the Revit session, although the direct app Horizun health call can. Current authorization is R05 only. R06 and later stages require their own task gates, and completing R05 does not start R06.

### 2026-09-27 current gates and resume state

- The direct Horizun health reports HEALTHY via `mcp__horizun_revit__horizun_health`: Horizun 1.3.3; Revit 2027 build 27.2.0.39, PID 38296; active saved document exactly matched `revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt`; active-document match was `Matched`; 73/73 registry commands and 80/80 visible tools; `full_write`, unpaused, zero other clients. Revit completed the call on its UI thread in 2183 ms.
- The exact R05-only production runner then started `C:\Users\slvma\AppData\Local\Programs\Horizun\MCP\server\horizun-mcp.exe` (file version 1.3.3.0). Its own first health response was `Error: no Revit is reachable. Is Revit running with the Horizun add-in loaded?` The runner stopped before capability/client validation, exact target selection, checkpoint, or model read. It printed `using existing RUN-003 lease` / `existing RUN-003 lease retained`; no R05 write, save, or checkpoint occurred. The reason the two transport paths disagree is unresolved. Do not route a model write around the runner.
- Read-only process/config checks narrowed but did not resolve the discrepancy: the installed runner executable/version matches Horizun client PID 1708, and `discovery/revit-2027-38296.json` exists with PID 38296, protocol 2, add-in 1.3.3, and the matching Revit session start. The discovery JSON was read with elevated access while emitting only key names and safe PID/version/time fields; no secret values were displayed. The remaining difference appears to be per-process discovery/connection state, but its cause is not established.
- The current writer-lock file still names owner `amanda-P7-RUN003-production`, generation 2, PID 28364, heartbeat `2026-09-26T22:38:20Z`; PID 28364 is still an unrelated-to-Revit Python process. The runner retained this lease. Do not delete, replace, or reclaim it until its ownership is safely resolved.
- Earlier read-only UI inspection recorded a minimized Revit window; after activation the captured window content was Chrome. That visual observation is older than the successful direct Horizun health call, which proves the API bridge can address the exact active RUN-003 document. It does not explain why the production runner's stdio server cannot discover it.
- `PROJECT_STATE.yaml` and `state/blockers.yaml` now record `RUNNER_TRANSPORT_UNREACHABLE:BLOCKING`. P7-T01 remains `BLOCKED_BY_TOOL`, phase P7 remains pending, and it remains the next task. Its graph entry has four evidence items. No R05 persistence evidence exists; P6 fingerprint reconciliation and the eight partial floors/Area checks remain mandatory.
- Unsupported Area units still fail closed. The error retains the raw provider unit, normalized unit, and logical ID. Supported m²/ft² conversion rules are unchanged.
- Current operational authorization is P7-T01/R05 only. DEC-010 remains historical context. Do not start R06; it requires its own task gate.
- Before this live attempt, focused tests passed 118/118; plan-order passed 8/8; compileall, three YAML parses, and scoped `git diff --check` passed. The updated status expectations reproduced RED (4 failed, 26 passed) before the new blocker/state update; the focused consistency/graph/hygiene command now passes 30/30. Ruff reports 11 pre-existing findings, with none on changed production lines.
- The P7 sanitation micro-commit `eaa0e67e3a0aac8e2f49760e3597382071fe303d` is on `main` and push to `origin/main` succeeded (`9e19186..eaa0e67`). The runner-transport state/handoff update is commit `293d89f06e45aeacce435a3059f061c976c23e6c`; its push succeeded (`eaa0e67..293d89f`), and local `main` matched `origin/main` at that SHA. Pre-existing RC01 deletions remain unstaged and untouched.
- This follow-up updates `PROJECT_STATE.yaml`, `state/blockers.yaml`, `state/status.md`, `state/task-graph.yaml`, this handoff, `tests/project/test_repository_hygiene.py`, `tests/unit/test_status_checkpoint_consistency.py`, and `tests/unit/test_task_graph.py`. No production code or Revit model file changed in this follow-up.
- Only Luna 6 xhigh subagents are permitted. A Luna 6 xhigh review was requested earlier but could not start because the active-agent thread limit is full; no other subagent/model was used. Local second-pass review remains the available review evidence.
- No further Horizun or runner call was made after the failed runner health request. First reconcile the installed stdio transport's discovery/configuration using read-only checks; do not repeat calls while the mismatch remains unexplained. Then use only the exact R05-only runner below, and only after its own health/client/exact-target gates can pass. Preserve the lease and model; any failed preflight leaves P7-T01 incomplete.

```powershell
.venv\Scripts\python.exe scripts\run_amanda_production.py --rvt 'revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt' --resume-run003-study --reuse-existing-run003-lease --max-stage R05 --revit-pid 38296 --execute
```

### 2026-09-27 R05 partial reconciliation implementation

- After the previous 600-second shared-client window expired, the exact R05-only runner passed Horizun health, the zero-other-client check, Revit 2027 PID 38296 selection, exact RUN-003 target identity, and retained the existing RUN-003 lease. It opened/read the exact P6 checkpoint and reconciled compact/detailed fingerprints to the recorded 25-row digest `3732c3c44c405a6453df8157243b7695b442b9969c979c141c6e829011940c0d`.
- The live target matched P6 plus the eight journaled floor additions by ElementId/UniqueId/category and preserved the exact P6 baseline rows. Guarded recovery closed the target without saving, reopened the exact path, then stopped because the post-reopen query still applied the 25-element P6 count gate. No new R05 operations, save, or checkpoint occurred.
- Target metadata at that readback was 5,152,768 bytes / 2026-09-27 09:30:38Z versus the P6 checkpoint's 4,960,256 bytes / 2026-09-26 21:34:00Z. `Get-FileHash` was denied while Revit held the target open. Preserve it; do not overwrite, delete, save, or duplicate the floors.
- The runner wrote diagnostic-only `revit/production/journals/R05-2f373fcb3511-p6-readback-diagnostic-0df224235764.json` (SHA-256 `b944255f50568e388d57b0e5a84ec6c407c504c1c2642dea7fbb715d3a48e867`). It describes the exact P6 checkpoint readback only; it does not contain the reopened target rows and does not mark P6 acceptance anew.
- TDD has added an exact-eight-floor reconciliation against the current R05 operation plan. The runner checks typed ElementId/UniqueId/category/name, XY bounds, Revit Area, and resolved level name, filters only those eight exact floor operations, and merges their independent readback records into the stage result. A mismatch fails closed before new R05 writes.
- The typed query contract exposes bounds and parameters but no floor-outline vertices. The check therefore proves extents, area, level, and identity; it does not claim vertex-for-vertex equality of the curved residential contours. The prior typed write records remain supporting evidence, and the final saved-stage readback must still pass.
- A second R05-only runner attempt around 12:34Z passed the fresh health/capability, target PID/build, and retained-lease gates, and reconciled the P6 checkpoint to the 25-row digest. It then failed closed in `_query_r05_level_names` because that helper treated all 704 stage operations as floor operations. The stack unwound through the guarded checkpoint cleanup; no new R05 operation, model write, save, or checkpoint ran. Diagnostic `revit/production/journals/R05-2f373fcb3511-p6-readback-diagnostic-104062613e0c.json` records `model_write_performed=false` (SHA-256 `96aeb03316dca4222c8142e68846b1a97bb41f220a47a9cdcc7e6d9bd8372e4a`). The RUN-003 lease was retained.
- TDD reproduced the level-query bug in RED, then GREEN after `_query_r05_level_names` was narrowed to the exact eight journaled floor IDs and checked each capability. The local full-plan test then caught the same assumption in `_validate_known_r05_partial_geometry` (RED); it now filters and validates the exact floor subset too (GREEN). Current focused local gates pass: runner unit suite 79/79, repository/state hygiene 12/12, and `compileall` succeeds. Ruff still reports nine baseline findings; the new/changed code introduces none. Local second-pass review found no additional acceptance-path issue. The requested Luna 6 xhigh review could not spawn because the app agent-thread limit is full; no other subagent was used.
- Corrected runner and evidence are committed on `main` as `5225d343824c5099487286f2779c64ada7c7777f`; the state pointer is set to that verified code commit. State/handoff commit `27b08aa` was pushed, advancing `origin/main` from `783b089`. The provider cooldown ends at 12:44:07Z.
- A third health-first R05-only runner around 12:44Z passed provider/capability, target PID/build, lease, and P6 digest gates. It reached partial-floor comparison and stopped because a Revit floor's display `Name` did not equal the logical ID, although ElementId/UniqueId/category had already matched. This is not a stable identity field. It failed before any R05 write/save/checkpoint. Diagnostic `revit/production/journals/R05-2f373fcb3511-p6-readback-diagnostic-2814233abec1.json` records `model_write_performed=false`, 25 P6 rows, digest `3732c3c44c405a6453df8157243b7695b442b9969c979c141c6e829011940c0d`, and SHA-256 `d87a07720d631c157058984428064dd32883828d7d092c858f9c8ad33524d38a`.
- TDD reproduced that name assumption in RED; GREEN removes display-name equality while preserving exact ElementId/UniqueId/category linkage and all bounds/Area/level checks. Current scoped tests pass 79/79 and 12/12, and `compileall` passes. Code/evidence commit `964070e915427999c295d1f9b0d32910afec61ed` contains the fix; `last_verified_commit` targets it. State/handoff commit `6b99cf9` was pushed, advancing `origin/main` from `8352e7e`. The current provider request was around 12:44Z; use 12:55:36Z as the conservative end of its 600-second client window. No direct Horizun call is permitted. After cooldown and local gates, retry only R05. R06 stays `NOT STARTED`.
- After the 12:55:36Z quiet deadline, an R05-only runner attempt around 12:56Z passed live health/capability, target, lease, P6 checkpoint/digest, and the exact eight-floor identity/bounds/level checks. It then failed closed because the typed Revit `Area` unit was not recognized. No R05 writes, save, or checkpoint occurred. Diagnostic-only `revit/production/journals/R05-2f373fcb3511-p6-readback-diagnostic-ee99ee2f171a.json` has SHA-256 `edd6f4b86c33fc82705ed8826828ce45d8e7d18475640bb00f6895b08b5de043`, records `model_write_performed=false` and the 25-row P6 digest `3732c3c44c405a6453df8157243b7695b442b9969c979c141c6e829011940c0d`, but does not contain the partial-floor Area payload or rejected unit string.
- TDD added explicit m²/square-metre and ft²/square-foot aliases, converts ft² with `0.09290304`, retains the reported source unit in evidence, and rejects unknown units. The production-runner unit suite passes 87/87, repository hygiene 12/12, and task-graph/status consistency 17/17; `compileall`, YAML parsing, and scoped `git diff --check` pass. Ruff still reports the same nine baseline findings, none on the new lines. An independent local review found no additional issue. A Luna 6 xhigh review was attempted, but the app rejected it because the agent-thread limit is full; no other subagent was used.
- Code, regression tests, the P6 readback diagnostic, and formal P7-T01 pending-state updates are committed on `main` as `581cacb30ca679f4d08549f7536f01315bad0257`; `PROJECT_STATE.yaml` revision 242 points to this verified code commit. State/handoff commits through `1670e0d7c87bec0689f2ba588d860aba6290792e` were pushed to `origin/main`; the latest push exited 0 and advanced `a46e7df..1670e0d main -> main`. Local `HEAD` and `origin/main` matched `1670e0d7c87bec0689f2ba588d860aba6290792e`. A subsequent `git ls-remote` could not connect to GitHub on TCP 443, so a separate live ref read is unavailable. RC01 deletions remain unstaged.
- The next exact R05-only runner attempt at 13:11Z stopped at its first gate: `horizun_health` returned `Error: no Revit is reachable. Is Revit running with the Horizun add-in loaded?` It did not reach capabilities, targetability, checkpoint inspection, or model readback. The existing RUN-003 lease was retained; no Revit/model/checkpoint write occurred. Use 13:21:07Z as the conservative end of this call's 600-second quiet window. Resume only with the same health-first R05 runner after that time; do not call Horizun directly. R05 remains `PENDING`; R06 is `NOT STARTED`.
- The post-cooldown retry at about 13:22Z returned the same `no Revit is reachable` health error. It again stopped before capabilities, targetability, checkpoint, or model access and retained the RUN-003 lease; no model write/save/checkpoint occurred. Read-only OS checks found only Revit PID 38296, responsive at the Revit 2027 executable, with `Horizun.Revit.dll` loaded but `MainWindowHandle=0` and an empty title; this does not prove the interactive target is available. No process or UI action was taken. The conservative quiet-window end is 13:32:14Z. Retry only through the health-first runner after that time. R05 remains `PENDING`; R06 is `NOT STARTED`.
- The third health-first retry at about 13:32Z, after the 13:32:14Z quiet deadline, returned the same `no Revit is reachable` response. It again stopped before provider capabilities, targetability, checkpoint, or model access and retained the RUN-003 lease. No Revit/model/checkpoint write occurred. This is the third consecutive runner failure on the same provider/session condition. Do not retry until the interactive Revit session is restored and targetable; the conservative quiet-window end is 13:42:35Z. Then use only the exact R05 runner below. R05 remains `PENDING`; R06 is `NOT STARTED`.

### 2026-09-27 explicit R05 authorization and health-first retry

- The user-provided `C:\Users\slvma\.codex\attachments\01b76853-5ab7-4aa1-9d85-52233700ef84\goal-objective.md` explicitly authorizes P7-T01/R05 for `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`, ending at R05. The prior automatic-review authorization hold is superseded; no R06 or later stage is authorized in this task.
- A fresh standalone `horizun_health` call returned HEALTHY: Horizun 1.3.3; Revit 2027 build 27.2.0.39, PID 38296; active saved target path exactly matched RUN-003; 73/73 registry commands, 80/80 visible tools, full_write/unpaused, and zero other clients. It reported two open documents and RUN-003 active.
- The exact health-first production runner was then invoked with `--max-stage R05`. Its own health response detected client PID 1708 (the standalone health call) 29 seconds old while runner client PID 8124 was current. `_validate_revit_session` failed closed on the 600-second zero-other-client gate before target selection, document info, checkpoint readback, or model access. It printed that the existing RUN-003 lease was retained. No Revit/model/checkpoint write occurred; P7-T01 remains `PENDING`.
- Do not call Horizun directly during the quiet window. After at least 600 seconds from the runner's health request (use 11:35Z or later as the conservative retry time), invoke only `.venv\Scripts\python.exe scripts\run_amanda_production.py --rvt 'revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt' --resume-run003-study --reuse-existing-run003-lease --max-stage R05 --revit-pid 38296 --execute`. Preserve the lease and target. If the runner passes health, client, target, capability, checkpoint, fingerprint, and partial-floor recovery gates, continue only through R05 WRITE → READ → VERIFY and save/checkpoint/cold-reopen/readback. Any failed gate leaves R05 pending. R06 stays NOT STARTED.

### 2026-09-27 fingerprint reconciliation update

- The latest health-first runner call (~10:07Z) passed health, client, target, and lease checks, opened/read the exact P6 checkpoint, and reproduced the accepted-vs-observed fingerprint discrepancy. It wrote `revit/production/journals/R05-2f373fcb3511-p6-readback-diagnostic-559bb4edc356.json`. Cleanup closed the P6 inspection without saving and reactivated the target. No R05 write, save, or checkpoint occurred.
- Added `revit/production/evidence/AMANDA-RUN-003-R04/p6-readback-fingerprint-reconciliation.json` and `docs/reports/P6-T01-fingerprint-readback-reconciliation-2026-09-27.md`. The addendum keeps historical `4636abc6b294829b`; it records compact `2f12a578c8451f3f`, detailed `1aac5d79b05b159a`, checkpoint SHA `8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326`, diagnostic SHA `d2d0cec6bd53c37b211a9eed168a2959009f05ba577cd7f0dd7dce63d73072d6`, and 25-row digest `3732c3c44c405a6453df8157243b7695b442b9969c979c141c6e829011940c0d`. The reason fingerprints differ remains unresolved; the addendum is exact-checkpoint readback evidence and does not re-mark the P6 acceptance gate.
- TDD recorded RED for the missing reconciliation module, the runner's missing detailed-query fallback, and compact-versus-detailed row geometry comparison, then GREEN. The state consistency gate first failed on its stale expected handoff heading; the test was updated to the current pending-live-retry state. The final combined production/state/provider/plan-order suite passed 227/227. `git diff --check` passed. Ruff import ordering introduced by this change was fixed; the remaining 9 Ruff findings are pre-existing.
- Local second-pass review found that compact and detailed payload bounds were not yet compared. A new RED regression changed the compact bbox while keeping the detailed rows intact; the runner initially accepted it. The gate now requires exact ElementId sets, equal bboxes, and equality of identity fields when present; the regression is GREEN. No other acceptance-path issue remained in the local review. The requested Luna 6 xhigh review spawn was rejected because the app agent-thread limit is full. No other subagent was used.
- Code/evidence commit `f96995af4d381bffb16b646f9d36e189bc426b09`, state commit `4e04bac54143540eba8273390c23f5f1c6183e82`, and handoff push-status commit `170cb4fe6e5ae962abbae4980d628dd3c847fdaa` are on `main`. Push output confirmed `main` advanced through `170cb4f`; local `origin/main` also resolves to that SHA. `git ls-remote` could not reach GitHub (TCP 443 unavailable), so the live remote-ref reread is unverified. The verified focused command passed 227/227; Ruff remains at 9 pre-existing findings and `git diff --check` is clean for scoped files.
- After both reconciliation commits were pushed, the production runner invocation for R05 was rejected by automatic approval review before process launch. The reviewer stated that the explicit user authorization visible in the current conversation covers P4/R04, while P7/R05 authorization appears only in assistant/tool history and does not authorize a persistent Revit write. No runner code ran, no Horizun health call occurred, and no Revit/model/lease operation was attempted by that invocation. Do not retry or route around the block. P7-T01 remains `PENDING` until the user explicitly authorizes the RUN-003 R05 write in the current conversation.
- No provider call has followed the ~10:07Z call; the ten-minute quiet window has elapsed. RC01 and all other unrelated protected deletions remain untouched and unstaged.

**Resume only after explicit authorization:** run `.venv\Scripts\python.exe scripts/run_amanda_production.py --rvt 'revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt' --resume-run003-study --reuse-existing-run003-lease --max-stage R05 --revit-pid 38296 --execute`. The runner must call `horizun_health` first and independently pass provider identity/capability, Revit 2027 PID, exact target, zero-other-client, lease, P6 checkpoint, and exact reconciliation checks. If green, continue immediately through R05 WRITE → READ → VERIFY and save/checkpoint/close/reopen/final readback. If any gate fails, preserve the target/journal/lease and leave P7-T01 pending.

- The authorized live R05 runner attempt reached WRITE/READ and ended `FAILED` at 8/705 verified records. The eight verified additions are floors for the four residential pavilions and four child-sector plates. The remaining 697 operations failed typed validation: external wall type reference `250` did not resolve, roof absolute-Z did not match its level-relative offset, and service profiles included a 0.119 mm edge. The runner did not save, checkpoint, or cold-reopen.
- Failed journal, now committed for exact recovery: `revit/production/journals/R05-2f373fcb3511.json`. The working target on disk remains 4,960,256 bytes with its pre-attempt timestamp, 2026-09-26 21:34:00Z. The live Revit document may still hold the eight unsaved additions. Do not save or retry writes blindly.
- Code fixes: resolve external walls by source-backed template type name `Genérico - 250 mm`; simplify R05 profiles with topology preservation and a 1 mm Hausdorff/edge bound; set roof profile vertices to the accepted absolute top elevation while preserving the relative offset. Courtyard holes remain in profiles.
- Recovery guard: when the live 33-element document differs from P6, require the exact fixed journal and element identities; verify the P6 checkpoint manifest; open that checkpoint in Revit without upgrade; require its accepted 25-element fingerprint; compare every baseline ElementId, UniqueId, category, name, and bounding-box coordinate to the live partial; then close the P6 inspection document without saving and discard the eight known unsaved additions. Any mismatch must fail before closing the working target. This path is unit tested but has not yet run live.
- TDD evidence: focused regressions first failed for the missing geometry/comparator behavior, then passed. The focused suite passed 182/182. The R05-only dry-run confirmed the four canonical PNG hashes and unchanged P6 approval/layout hashes and wrote nothing. Ruff reports only existing findings elsewhere in these modules; changed lines have no Ruff finding. `git diff --check` passed.
- Code/journal commit `02ed2d334b18714dbedc5d6ec78ced305f8d0f55` and state/handoff commit `b601c2d2dc7a827d5ae8c90a8fa8899a38e9ae32` are on `main`; `git push origin main` succeeded and `git ls-remote` confirmed exact origin/main SHA `b601c2d2dc7a827d5ae8c90a8fa8899a38e9ae32`. Protected RC01 ACL-visible deletions remain unstaged and untouched.
- A subsequent runner attempt correctly called `horizun_health` first but received an untyped payload. Validation stopped before transport pinning, capability checks, target selection, document info, or model access. The existing RUN-003 lease was retained; the working file still has its P6 size/timestamp; local process inspection found Revit PID 38296. No standalone Horizun call followed. The provider result content was not captured, so a repeated untyped response requires better diagnostic output before further action.
- TDD added actual counts/categories to the known-partial-model guard error: the regression first reproduced the previous generic error (`RED`), then passed with the detailed rejection (`GREEN`). The expanded focused production suite passed 183/183. R05-only dry-run still binds the four board hashes and P6 approval/layout hashes and plans only R05. The diagnostic source/test commit `b9022e1092877218c1e8d862ff7d4a621f61c62d` is on `main`; push and remote SHA verification succeeded.
- The next health-first runner call (about 06:35:53Z) passed the health schema and transport-identity checks, then stopped in the zero-other-client guard before Revit target selection. `clients_seen` contained the current `horizun-mcp` client PID 14596 (age 0, alive) and PID 28628 (`unknown`, age 595 seconds, not alive). This is still inside the provider's 600-second shared-session window. The RUN-003 lease was retained. No target/document read, checkpoint inspection, close, save, or model write occurred. The working RVT remains 4,960,256 bytes with its 2026-09-26 21:34:00Z timestamp; hashing it while Revit holds it open was denied by the OS. No standalone Horizun calls were made.
- After the quiet window, a new health-first runner call (about 06:47Z) passed the shared-client guard, selected Revit PID 38296, and retained the existing RUN-003 lease. The live query returned 33 rows, complete coverage, zero unreadable, and summary categories `Massa=7`, `Pisos=22`, `Telhados=4`. P6 baseline readback correctly rejected 33 instead of 25, then the recovery guard refused before checkpoint inspection because rows did not expose expected `element_id`, `unique_id`, and `category` keys (`row_categories={}`). No checkpoint was opened; no document was closed, saved, or written. The RVT remains 4,960,256 bytes at 2026-09-26 21:34:00Z.
- TDD added safe row-shape diagnostics: the test first failed because the guard omitted field names (`RED`), then the implementation reported row types and up to three sets of field names without row values (`GREEN`). Focused production suite passed 184/184. Ruff reported 121 existing E/F findings in the two modules, with zero findings on the new code lines. State/task graph/store gates passed 24/24 and the three state YAML files parsed. Commit `709661c65511305796681f659b0c1c3ccca5464e` is pushed and the remote SHA matches. The next runner will capture the actual row field names; no aliases will be accepted until independently validated against the complete P6 fingerprint and journaled eight-floor set.
- The official local `horizun_query_model` contract allows explicit `return_fields`. TDD first failed because baseline and checkpoint/recovery queries did not request identity fields, then passed after all four relevant readbacks requested `unique_id`, `category`, and `name`. The focused suite remains 184/184. Commit `3eb4618776b4967d2b0ae8596543d67a7dc9783c` is pushed and verified. This request change has not yet been exercised live; numeric ElementId remains required and the recovery comparison remains exact.
- The next runner passed the shared-client gate and selected Revit PID 38296. Explicit identity fields let it validate the known partial and open the exact P6 checkpoint without upgrade. The live response used `status=opened`, `opened_now=true`, `active_document_verified=true`, exact `path`/`opened_from`, `host_version=2027`, `file_version_before_open=2027`, `upgraded=false`, and `version_guard=checked`; the old guard expected `opened`, `path_matches_request`, and `upgraded_on_open`, so it stopped before querying the checkpoint. The exception path completed its no-save checkpoint close and target reactivation without a cleanup error. No R05 write/save/checkpoint occurred. TDD changed the runner to validate the returned exact-path/version contract on P6 inspection, P6 reopen, and post-stage cold reopen. It requires every field above; 12 negative cases and the recovery/persistence tests pass. Focused suite: 197/197. Commit `81bc4bde32b2411b1516d959f2970cf91579655f` is pushed and remote verified.
- With the current open-result validator, the next runner passed health/client/target/lease, validated the 33-row partial, and opened the exact accepted P6 file as Revit 2027 without upgrade. The checkpoint query passed count/category/mass/ElementId validation but its `result_set_fingerprint` differed from the accepted P6 value. The old error omitted both values; no full row comparison or partial discard followed. Guarded exception cleanup closed the inspection without saving and reactivated the target; no cleanup error was reported. No model write/save/checkpoint occurred. TDD preserves the original compact query signature for the accepted fingerprint, requests identity fields in a separate detailed P6 query, and compares every P6 row with the target after excluding the eight journaled floors. Fingerprint mismatch errors now include expected and observed strings. Focused suite: 198/198. Commit `e73ee60ca8bf8449fe1b04a73fc938849202b551` is pushed and remote verified; this two-query approach is not yet live-verified.
- Latest health-first runner (~07:26Z) passed health/client/target/lease and retained the existing lease. The target still had the known unsaved 8-floor partial, so baseline count validation routed to guarded recovery. The exact P6 file opened as Revit 2027 without upgrade; count/category/mass/ElementId checks passed, but the compact query returned fingerprint `2f12a578c8451f3f` instead of accepted `4636abc6b294829b`. Exception cleanup closed the P6 inspection without saving and did not close or save the partial target. No R05 stage write/save/checkpoint occurred. Local P6 bytes remain 4,960,256 bytes with SHA-256 `8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326`, matching the manifest. Do not waive the mismatch or change the checkpoint. Luna 6 xhigh review dispatch hit the app agent-thread limit; review remained local. Wait until 07:36:30Z before another runner attempt.
- TDD applied the documented fresh-verification cache policy: RED added assertions for `cache_mode="bypass"` to both compact P6 reads and both failed because the argument was absent; GREEN added the argument to the baseline and checkpoint queries. The focused production suite passes 198/198. Commit `7be2101276053e88c9f778dfe58f00e9743e97e4` is pushed to `main`. This diagnostic change has not been exercised live; the fingerprint mismatch remains an active gate. Retry only after 07:36:30Z.
- Live retry at about 07:37Z still returned fingerprint `2f12a578c8451f3f` instead of accepted `4636abc6b294829b`, so cache use does not explain the mismatch. Recovery called checkpoint close with `save_on_close=false`, but its result was `None`; the runner could not verify closure. `_activate(target)` completed before this close attempt; active document/open-document count after the attempt is unverified. No R05 write/save/checkpoint occurred. Preserve the lease and journal; do not issue another provider call before 07:50:00Z.
- The 07:50Z health-first retry failed immediately because `horizun_health` returned an untyped payload. The runner stopped before transport PID pinning, capabilities, Revit target selection, document reads, or writes. It retained the existing RUN-003 lease. Post-close active/open-document state remains unknown; the working target and P6 checkpoint still need a runner-led health/readback. No R05 write/save/checkpoint occurred. Wait until at least 08:00:30Z before another provider call.
- TDD added bounded diagnostics for untyped health replies: absent JSON-RPC reply, malformed result shape, content types, MCP error code/message, and a 160-character text preview. RED reproduced the missing diagnostics; GREEN passes three response-shape cases. Focused production suite: 201/201. Commit `0a8db3c5898a59b66daf89b5c7b709c9365e70d2` is pushed. No Horizun call has followed the 07:50Z failure; the quiet window has elapsed. Retry through the health-first runner only.
- The ~08:02Z health-first runner call returned an untyped `horizun_health` response whose bounded text reported a Revit modal titled `Projeto não recentemente salvo`; the runner stopped before transport PID pinning, capabilities, target/document access, or writes, and retained the RUN-003 lease. Read-only UI inspection around 08:04Z showed the RUN-003 target active and tabs for P6 and `HZ_ANCHOR_2027`; no modal was visible then. No UI control was clicked and no document was saved or closed. The target and accepted P6 checkpoint were last verified byte-identical at 4,960,256 bytes and SHA-256 `8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326`. The health/UI discrepancy and the P6 fingerprint mismatch (`2f12a578c8451f3f` vs accepted `4636abc6b294829b`) remain unresolved; no R05 write/save/checkpoint occurred. The provider quiet deadline was 08:12:30Z and has elapsed.
- The ~09:40Z health-first runner passed provider/client selection, selected Revit PID 38296, and retained the RUN-003 lease. It verified the known 33-element unsaved partial, then opened/activated the exact P6 checkpoint, which the bridge reported as already open (`status=already_open_activated`, exact path, host/file 2027, `upgraded=false`). The strict new-open validator rejected that no-op activation because fields such as `opened_from` and `version_guard` were absent. The recovery exception handler closed the checkpoint with `save_on_close=false` and reactivated the target; the original validation error remained visible, so no cleanup failure was reported. No model write/save/checkpoint occurred. P7-T01 remains pending. Preserve the existing P6 fingerprint requirement; this attempt did not issue the checkpoint query. The conservative quiet deadline is 09:51:00Z.
- The ~09:51Z retry passed health/client/target/lease and reopened the exact P6 checkpoint as Revit 2027 without upgrade. Its compact typed query passed the 25-element count, complete coverage, categories, mass bounds, and required floor-ID checks, but again returned `2f12a578c8451f3f` instead of accepted `4636abc6b294829b`. The runner stopped before R05; guarded exception cleanup closed P6 without saving and reactivated the target, with no cleanup error. No model write/save/checkpoint occurred. TDD now adds a bounded diagnostic-only JSON containing the verified checkpoint SHA, accepted/observed fingerprints, a canonical row digest, and the 25 typed rows (ElementId, UniqueId, category, name, bounds); the mismatch still raises and cannot pass the recovery gate. The regression was observed RED then GREEN; focused production suite passed 202/202. Ruff has the same 9 baseline findings (8 in runner, 1 in test), with none introduced. After this code and handoff are pushed, run the health-first runner once to create the readback diagnostic, then review it without relaxing acceptance.
- The recorded RUN-003 writer lease owner is `amanda-P7-RUN003-production`, PID 28364, generation 2. Revalidate it through the runner; never reclaim or release it. Use only `gpt-6-luna` with `xhigh` if a subagent can be started. One Luna 6 xhigh review spawn was attempted but the app's agent-thread limit was full, so this continuation used local review.

**Resume:** after pushing the diagnostic code and handoff, use only this health-first runner command under the approved host context:

```powershell
.venv\Scripts\python.exe scripts/run_amanda_production.py --rvt 'revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt' --resume-run003-study --reuse-existing-run003-lease --max-stage R05 --revit-pid 38296 --execute
```

The runner's first provider operation must be `horizun_health`. Continue only if health, pinned transport identity, capabilities, Revit 2027 build 27.2.0.39/PID 38296, exact targetability, zero-other-client rule, and existing lease all pass. If the shared-client guard still fails, stop and reset the ten-minute quiet window from that health call. Preserve the exact P6 manifest and SHA. The accepted P6 fingerprint remains mandatory. On mismatch, the runner now writes a read-only diagnostic artifact with the exact checkpoint SHA and 25 identity/geometry rows, then stops. Review that artifact against P6 evidence; do not accept the mismatch by assumption. If the readback reconciles through exact evidence, update the acceptance record and task graph explicitly before retrying R05. If any gate fails, preserve the lease and journal, do not save the partial target, and leave P7-T01 pending. No GeoNatal; no RC01/S01/S02/R12; no R06+; no FINAL/GOLDEN.

## Prior closeout — P4-T01 R04

## Historical continuation — 2026-09-26 (P4-T01 / RUN-003 R04 geometry completion)

This snapshot predates the closeout review corrections above and below. Use it
for geometry-write details only; its revision 195 and capture notes are not the
current repository state.

The user requested resuming P4-T01 in the visible, interactive Revit 2027 session. BIM-00 had already passed, so this continuation completed its authorized R04 real-model geometry. No GeoNatal search, RC01 change, R05 write, or reuse of S01/S02/R12 occurred. S02 remains `STALE_BY_CANONICAL_REFERENCE_EXPANSION`; its lease was absent and was not reclaimed.

### Live Revit and write scope

Fresh Horizun health: 1.3.3 `HEALTHY`; Revit 2027 build 27.2.0.39, PID 38296; registry 73/73 clean and 80/80 tools visible. `horizun_target` selected the one running Revit. RUN-003 target was active and matched by exact path. Two documents were open (RUN-003 and `HZ_ANCHOR_2027`); other Horizun clients: 0. The exclusive lease owner during write was `amanda-P4-T01-RUN003-R04`, generation 2, bound to the exact target.

Target: `revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt`.

Typed rehearsal passed 18/18; the committed transaction created 14 floors and four roofs. Additions: two admin floor plates; five official external surfaces (80/80/30/30/40 m²); four open-sided covered residential connectors plus roofs; three separately marked public/admin, public/service, and cargo paths. There were no rooms or R05 shell elements. The existing seven masses remained the spatial base.

### Persisted evidence

Revit save changed the target from SHA-256 `7097faf9b92a812e6488bed39b0dc573d37fe23790671179cd28cba607761095` / 4,612,096 bytes to `33a99c7c760125da434017210b7ea2d506a3914ae59e002769a14138cca27b49` / 4,952,064 bytes. Checkpoint: `revit/production/evidence/AMANDA-RUN-003-R04/R04-T01-RUN003-POST-SAVE.rvt`; manifest hash/size match. A placeholder in the manifest provenance SHA was corrected to the verified model SHA, then `CheckpointManager.verify_checkpoint` returned `True` again.

The target was closed and reopened from the exact path in Revit 2027 without upgrade. Final typed query after reopen returned 25 objects (7 masses, 14 floors, 4 roofs), complete coverage and zero unreadable. The target remains active. Revit visual evidence is `revit/production/evidence/AMANDA-RUN-003-R04/views/r04-canonical-site-revit-2026-09-26.png` (2400×1459, SHA-256 `c3759ce98fe38e2eff63c0a09c8a91f635d5636b1289e4f917158a616d979b0f`). It is a cropped wireframe supporting capture; it does not close CANON-011.

### Open reconciliation items

- Admin plates are 237.407 m² each versus the board's approximate 200 m² label (+37.407 m² / +18.7%). The upper plate face is at 3.2 m while Revit `Nível 2` is at 4.0 m (−0.8 m offset). Both remain open; no official PDF area was altered.
- The four residential masses are A/B/C family pavilions and D communal. Four roofed, wall-free connectors have 2 m patio interfaces and no measured intrusion into the 80 m² patio. Bedroom counts and residential functions are not room assignments yet.
- The six-ring services/capacitation composition is curved and retained. Its board-listed functions and their official room-area assignments have not been modeled; the 446.501 m² source mass area is not an official programmed room area.
- The west child mass is adjacent to the 40 m² playground. Brinquedoteca, apoio pedagógico, bathroom and deposit are not modeled as rooms.
- Route widths (2/2/3 m) are study assumptions; paths are marked separately but doors and geographic/site access are not proven. Site boundary, topography, occupancy, frontage count and true north remain unresolved.

### Tests, files and Git closeout

Test-first record: the focused spatial test first failed at the intended RED status assertion while the evidence file was `RED`. After evidence implementation it exposed the literal `${save.sha256_after}` manifest placeholder; fixing it yielded GREEN. A pre-existing committed-graph test also reproduced the baseline rejection of P4→P5 and P5→P6. A new policy test was RED, then the narrowly scoped auxiliary-chain contract fix made it GREEN. Results: spatial/graph/state unit command, 21 passed; policy order command, 7 passed; `CheckpointManager.verify_checkpoint` returned `True`. The combined `test_status_dashboard.py` collection was blocked because the host Python lacks `ortools`; no dependency was installed or changed.

Updated evidence/report/state files: `r04-spatial-model-evidence.json`, `P4-T01-BIM-00-RERUN-2026-09-26.json`, the checkpoint manifest, the current Revit PNG, `tests/unit/test_run003_r04_spatial_evidence.py`, `tests/policy/test_plan_order.py`, `src/amanda_agent/state/plan_order.py`, `docs/plan/CURRENT.md`, both P4/P6 reports, `PROJECT_STATE.yaml`, `state/task-graph.yaml`, `state/task-history.yaml`, `state/status.md`, and this handoff. RVT and checkpoint binaries are local/ignored.

At task start, `main` and `origin/main` were both `da9b91ed17666ff192d57b610c33615e1f4aa767`. Do not stage broad paths: many pre-existing `revit/lab/exports/p06t14/GOLDEN/RC01/` deletions appear in `git status`; preserve them unstaged. Stage only the named R04 evidence, reports, state, manifest and test files. Record final commit and `git ls-remote` confirmation in this section before closing.

### Resume

`P6-T01` remains `PENDING`, `CANON-011` remains open, and `PROJECT_STATE.yaml` points to the new post-save checkpoint (revision 195). The next authorized work is scoped P6 visual/geometric acceptance and source-backed reconciliation of the open items; do not proceed automatically to R05. Preserve the live RUN-003 target and never alter RC01.

## Previous continuation — 2026-09-26 (P4-T01 and P5-T01 complete)

P4-T01 BIM-00 passed, then the user-authorized P5-T01 R04 write ran in the
actual Revit 2027 session. Horizun 1.3.3 health is `healthy`, contract
`8b9600f5274d7dffb6e5bd5f`, registry 73/73 clean, and PID 38296 is targetable.
At final live check the exact RUN-003 target was active, was the sole open
document, and had zero other clients. The RUN-003 writer lease was released
after model persistence closeout.

Seven canonical `OST_Mass` elements were written, queried, geometrically
read back, saved, checkpointed, closed, cold-reopened, and queried again. Save
returned target SHA-256
`120935963a19af4c654894d00f057304237ec7f98115f0eecb266e3a91aaef20` and size
4,603,904 bytes; the checkpoint file and manifest were independently rehashed
and match. Direct filesystem hashing of the target was denied while Revit held
it open. The independent typed queries confirm element identity and bounding
boxes after reopen. Python readbacks are marked
`self_reported_verified` / `host_verified=false`; retain that limitation.

The service-profile write first rolled back because a 0.119 mm edge was below
the live 0.7804 mm Revit ShortCurveTolerance. A new key and corrected script
removed one vertex with 0.0232 mm maximum deviation, preserved six interior
rings, and passed verification with 0.00000148 m² area difference. Coordinates
are local normalized, not surveyed; floor heights are provisional. Capture
attempts rolled back and produced no usable visual evidence, so CANON-011 and
P6 acceptance remain open. No R05, GeoNatal research, or RC01 edit occurred.

Evidence and next steps:

- Model evidence: `revit/production/evidence/AMANDA-RUN-003-R04/real-model-evidence.json`.
- Short report: `docs/reports/P5-T01-run003-r04-real-model.md`.
- POST-R04 checkpoint: `revit/production/checkpoints/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY-POST-R04.rvt` and its manifest.
- Focused adapter suite: 59 passed; no broad suite was run.
- GitHub: closeout evidence commit `ed1a7ab` was pushed to `origin/main`; the post-push `git ls-remote` matched local `main` at `ed1a7ab`. This final handoff/status refresh is included in a follow-up commit.
- Next task: P6-T01 visual/geometric acceptance against all four boards. R05 remains blocked until it passes.
- Formal pointer after task closeout: `PROJECT_STATE.yaml` revision 192, phase P6 `PENDING`, `last_completed_task: P5-T01`, `next_task: P6-T01`, `revit_stage: R04`; writer lease is free.
- Pre-existing deletions under `revit/lab/exports/p06t14/GOLDEN/RC01/` must remain untouched and unstaged.


## Formal state and safety

> Historical record follows. Older blocked-provider and no-write notes below
> describe prior checkpoints and are superseded by the current state section at
> the top of this file and `PROJECT_STATE.yaml` revision 196. Resume at P6-T01.

Repository recovery (P0), four-board reconciliation (P1-T01), identity
assignment (P2-T01), offline canonical QA (P3-T01), BIM-00 (P4-T01), and R04
model creation (P5-T01) are complete. `PROJECT_STATE.yaml` and the task graph
point to P6-T01 next. The source-bound identity is recorded at
`project/requirements/canonical-solution-identity.yaml`, while
the selected design is RUN-003 for normalized study only; final/detailed
eligibility remains false. The recovery anchor is
`pre-repository-recovery-2026-09-24`; the superseded P08 offline candidate is
preserved under `superseded-p08-t08-concept-offline-2026-09-24`.

## P4-T01 attempt — BIM-00 blocked

> Historical snapshot from the original P4-T01 attempt. Its eligibility and
> runtime observations below are superseded by the current state section at the
> top of this file; use that section and PROJECT_STATE.yaml for current state.

No BIM-00 evidence or authorization was emitted. RUN-003 remains
`OFFLINE_CANDIDATE`, `bim_eligible=false`, `revit_calls=0`, with
`selected_design=null`, `current_checkpoint=null`, and a detail decision marked
`BLOCKED_BY_INPUT` / `AMANDA_REVIEW_PENDING`. The hashes of all four canonical
boards, the official program PDF, and the P1 report were independently
recomputed and match the persisted identity. Values are recorded in
`docs/reports/P4-T01-bim00-blocker-report.md`.

There are preserved RVTs in the production tree, but none is bound as the
RUN-003 target; `revit/production/working/CURRENT.rvt` is absent. The writer
lock remains HELD by `amanda-P08-CAN-T09-R03` on superseded S02; it was not
released or reclaimed. No Revit process was running, so live provider health
was not established. Site topography, boundary, and occupancy remain blocking;
frontage count and true north remain unresolved/degrading.

P4 contract hardening added mandatory binding and comparison for the official
program SHA-256, repository commit, and `PROJECT_STATE.yaml` revision/raw SHA.
Focused gate tests: 41 passed; combined gate/status/state tests: 57 passed;
final focused closeout suite: 103 passed; Ruff and scoped diff check passed. The
tests first produced 38 failures and 1 pass before the fix.
Independent review found no Critical, Important, or Minor findings. Code and
plan contract are committed as `bc494683f9d9b154c40bdc8069a3dfa48710c665`;
`last_verified_commit` points there. State revision is 182.

### Recheck — 2026-09-25

An official RN government PMRN service charter updated 2026-02-03 lists BPChoque
at Av. Miguel Castro, s/n, Lagoa Nova, Natal
([source](https://www.transparencia.rn.gov.br/docs/orgaosdogoverno/cartasdeservico/Carta_de_Servi%C3%A7os_PMRN.pdf)).
This is partial evidence of the published institutional address. It does not
identify the cadastral parcel or establish an approved transfer, so
`SITE_OCCUPANCY` remains `BLOCKING` for claiming site availability. The other
site fields remain unverified: placeholder boundary, missing topography,
unresolved frontage conflict, and no verified true-north bearing.

An independent read-only audit confirmed RUN-003 is still unselected and
ineligible, with no exact target/checkpoint; CANON-011 remains pending human
visual acceptance. The lease remains held for S02 and was not changed. No Revit
process or document was opened or written. `P4-T01` remains the retry pointer;
P5/R04 and R05 remain unauthorized. A fresh `git ls-remote` could not reach
GitHub in this session; local `HEAD` and `origin/main` both pointed to
`f367e99bd65268ba4ea665225808f771ac9c11cd` before these documentation updates.
The recheck commit `05684895699053409ccc39ad78045ba45ef73d38` was subsequently
pushed, and a fresh `git ls-remote --heads origin main` confirmed that commit
at `refs/heads/main`. This handoff status correction is being committed as a
fast-forward follow-up. The pre-existing RC01 deletions were not staged or
changed.

### Historical: P4-T01 continuation — scoped study selection and BIM-00 hardening (2026-09-25)

> Superseded by the 2026-09-26 P4/P5 closeout at the top of this file.

- The previously recorded site-data dependency was too broad for normalized
  academic STUDY. Successor decision `DEC-CANONICAL-DETAIL-004` selects RUN-003
  only through R04 with `LOCAL_NORMALIZED_STUDY_NOT_SURVEYED`; Amanda review
  remains pending and CANON-011 still requires a real four-board comparison
  before R05. The content approval hash is not personal approval.
- `PROJECT_STATE.yaml` revision 185 records RUN-003 as the current reversible
  study selection. Site blockers are DEGRADING for this scope; final/site claims
  remain constrained by `project/site/missing-data.yaml`. The current P4 blockers
  are unreachable Horizun provider, writer lease held for superseded S02, and no
  exact RUN-003 target/checkpoint.
- The generated current study snapshot is
  `design-engine/runs/AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C-study-detail-004/`.
  It binds detail decision 004 (hash
  `29d70f0e830708a3926abad14877f4c3941418630c5f0225b0bf5924f2dabd8b`) and
  content approval `961b6edc95bd097fe600b2ce968aacdf28876bf3c587b788a0b2358baddfc0b0`.
  Its manifest verifies 6/6 files; QA remains 17 PASS, 0 FAIL, CANON-011
  BLOCKED; it records `bim_eligible=false` and `revit_calls=0`. Original P3
  snapshot remains preserved at its original path.
- R04 mass payloads carry `design_scenario=STUDY` and the typed coordinate mode.
  BIM-00 refuses untyped/mismatched coordinate modes. R04 mass writer now
  preserves base elevation and interior rings, and completion requires separate
  geometry readback from the Revit model before verification. Model readback
  geometry/identity now override self-reported write payload fields; failed
  readback removes the geometry claim so runner verification fails closed.
- Regression tests for independent review findings reproduced RED: FINAL plans
  could pass BIM-00 and blocked P4-T01 was also recorded as completed. The new
  scenario/state regressions reported 4 failures and 62 passes before fixes.
  BIM-00 now requires STUDY; the last completed task is P3-T01; the old resume
  instructions are explicitly superseded. The focused BIM-00/R04/readback/
  geometric suite previously passed 154 tests. Review follow-up also requested
  explicit claim scope in the dashboard and a historical label on the older
  pre-DEC-004 section. Both changes have regression coverage; independent
  confirmation approved with no remaining findings. The final 19-module focused
  suite passed 270/270 and scoped Ruff passed. Record diff check, snapshot hash,
  manifest 6/6 validation, and QA 17 PASS/0 FAIL/CANON-011 BLOCKED are verified.
  Record commit and push below at closeout.
- Read-only Revit diagnostics: Revit 2027 PID 38152 responds but has no
  targetable main window; `horizun_health` failed with no reachable Revit.
  No RVT was opened and no Revit write, BIM-00 authorization, R04 or R05 was
  performed. S02 lease remains untouched.
- Resume P4-T01 only after a targetable/healthy provider, safe resolution of the
  S02 writer lease, and an exact RUN-003 target/checkpoint are evidenced. Rebind
  current commit/state/source hashes then rerun BIM-00; do not advance R05
  until CANON-011 passes.

### P4-T01 Git closeout

Implementation commit `3c816cb2e5bfb84b318ec043196551446fb70e9d` and state
closeout commit `9d3b255f3ffbb4aee4eae915d80522e397a39f91` are on `main`.
The final handoff/status closeout is also committed and pushed as a fast-forward;
a fresh `git ls-remote origin refs/heads/main` after that push matched local
`main`. Staging was limited to the 40 explicit P4-T01 paths; no RC01 path was
staged or changed. Temporary staging copies used for the ACL-restricted
snapshot were removed after their bytes were verified.

### Bounded official-source research — 2026-09-25

`docs/reports/P4-T01-site-source-research-2026-09-25.md` records a read-only
search of official municipal and state sources. It found no verifiable
project-specific cadastral polygon, site survey/topography/datum, physical
occupancy confirmation or transfer/availability decision, frontage count, or
true-north bearing. The PMRN service charter supports only a published BPChoque
institutional address; the municipal law and procurement specification are
routes/specifications, not parcel data, although the municipal specification
does describe geospatial references/products. GeoNatal serves a public 40,568-
feature lot GeoJSON collection with CRS84, but no feature was linked to this
project parcel; the served file alone does not establish currentness or
site-specific applicability. Unrelated content was also observed on alternate
routes, which is an anomaly of content and does not prove the official layers
are compromised. No site blocker was resolved or reclassified; `P4-T01` stays
`BLOCKED_BY_INPUT`. The task-graph CLI validated
182 registered tasks, with no ready task. No test suite, Revit, or RVT was run
or opened. No BIM authorization or R04/R05 work occurred. The research delta
was committed as `4723b3c9d352289b88e133bae1c67fa405198487` and pushed; a fresh
`git ls-remote --heads origin main` verified that SHA on the remote. The
pre-existing RC01 deletions were not staged.

The read-only environment doctor exited 0: Git, Codex, PowerShell and .NET were
available; Revit 2027 was detected, but no Revit process was running. The venv
Python is 3.12.14 even though the host-only probe reports `python312 MISSING`;
live provider health remains unverified. The S02 writer lease was not touched.
Automatic approval review rejected matching cadastral features to the project
site using its area/neighborhood/street description because it could identify
a third-party parcel. No feature was assigned to this project; obtain explicit
user approval before any site-specific match.

The GeoNatal response metadata correction and approval-review blocker note were
independently reviewed and committed as
`3ed955662d8ca340205e266b9175691aeaaf7ec4`; the commit was pushed, and a fresh
remote read confirmed `origin/main` at the same SHA.

Resume only P4-T01 after the canonical selection is approved/eligible, required
site inputs are resolved, an exact target and separate checkpoint are
designated, and the writer lease/provider can produce fresh passing evidence.
Do not choose an existing RVT by filename, reclaim the S02 lease, reuse S02 as
the solution, or run R04/R05. P5 remains unauthorized.

P0 completed without Revit/model activity. All recovery evidence is transferred
to `docs/reports/repository-recovery.md`; `.recovery/` was removed after the
RVT and evidence checks. Preserve the private program and TFG PDFs locally;
they are intentionally ignored by Git. Five site conditions (three BLOCKING,
two DEGRADING) remain, and the held writer lease is unchanged. P1-T01 completed
without Revit/model activity. At P1-T01 closeout the solution identity was
unset and S02 was stale; P2-T01 has since assigned the source-bound identity
recorded above. Five site conditions (three BLOCKING, two DEGRADING) remain;
the held writer lease was not changed.

### Follow-up after explicit user authorization — GeoNatal candidate recheck (2026-09-25)

The user authorized read-only matching using only public GeoNatal location,
street, area, and geometry data, and expressly excluded owner, CPF, private
registration, title, and titularity searches/inferences. The official portal's
`Logradouros` linework places the shared Prudente de Morais / Miguel Castro node
at `[-35.21356846, -5.82163110]` in CRS84. Filtering the portal-hosted `Lotes —
Zona Sul` collection found a nearest large Lagoa Nova polygon with published
`area=20,817.519`; its boundary is approximately 7.5 m from the Prudente de
Morais line and 8.5 m from the Miguel Castro line. Its published area value is
about 13.7% below the TFG's approximate 24,135 m². The shared road-intersection
node is west of the candidate envelope by roughly 10 m, and the portal layer's
units, accuracy, survey date, and cadastral
certification for this feature are not established. Classification is
`PROVISIONAL_CANDIDATE`, not an adopted site boundary. Details and source URLs
are in `docs/reports/P4-T01-site-source-research-2026-09-25.md`.

`SITE_BOUNDARY` remains unresolved; no blocker or formal task status changed.
The candidate does not authorize cadastral placement, final-area claims, or
BIM-00. No owner/CPF/private registration/title/titularity field was searched
or inferred, no local GIS copy was saved, and no external cadastral data,
task graph, PROJECT_STATE, lease, Revit, or model was changed. P4-T01 remains
`BLOCKED_BY_INPUT`; do not advance R04/R05 or perform a Revit write from this
research result.

## P3-T01 closeout — canonical QA and candidate

Generated offline candidate `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`
with identity fingerprint
`4b1275558a6c2c40828dbba1422c0063703c182fd9d7b800b36a448499a073c4`. It binds
all four current board hashes, the official 20-person / 626 m² internal /
260 m² external program PDF, and the P1-T01 report. Layout hash:
`7fde3e34a162167ce27fe2e3158a38f446882816a7c81bb326d486bdfaaae2e2`;
candidate content approval hash:
`eea4a342a4d732cbc986a16d01d93e3981e79a5931f8d99ebef82c61d24299ec`;
detail-decision hash:
`f37c5c8c2f4f43e957429bd05dbc659012a7f6eaa0b0be65e23cbf7f47c43efc`.
The approval hash is a deterministic content binding, not Amanda approval or
BIM authorization. `DEC-CANONICAL-DETAIL-003` remains provisional,
`BLOCKED_BY_INPUT`, and `AMANDA_REVIEW_PENDING`.

P3 QA requires exactly one each of CANON-001..018: **17 PASS, 0 FAIL,
CANON-011 BLOCKED**, zero critical failures. The normal CLI and direct builder
both validate the persisted P2 identity against live sources including the P1
report. A forged self-consistent report hash regression was first reproduced
RED and then passed GREEN. A second RED/GREEN regression rejects duplicate/missing
QA IDs. Independent review and re-review verified both fixes and no CLI
regression. The final state review found no Critical/Important issues and one
Minor gap in negative phase-edge coverage; tests now cover P1→P2, P2→P3, and
P3→P4.

Focused command:
`.venv/Scripts/python.exe -m pytest tests/unit/test_build_canonical_pavilion_run.py tests/unit/test_canonical_solution_identity.py tests/unit/test_production_selection.py tests/unit/test_canonical_qa.py tests/unit/test_decision_register.py tests/project/test_repository_hygiene.py tests/policy/test_plan_order.py -q`
— **74 passed**. State/task/session routing suite — **55 passed**. Changed-file Ruff and `git diff --check` pass. The builder
regenerated RUN-003 deterministically; its six artifact-manifest entries all
match recorded SHA-256 and byte counts. `bim_eligible=false`, `revit_calls=0`,
`selected_design=null`; no Revit access/write and no R04/R05 activity.

Broader downstream check
`.venv/Scripts/pytest.exe tests/unit/test_production_layout_bim.py -q` returned
**26 passed, 5 failed**. All five failures are R04 planning preflights at
`projection_area: MASS-SERVICE_CAPACITATION`; this is recorded as an R04
readiness blocker and was not modified in P3. Board 03's six drawn common-WC
cells vs five official rooms, Board 02/04 repeated or relabeled support areas,
and Board 04 unpriced training functions remain explicitly reconciled in the
P1 report. CANON-011 visual acceptance and site verification remain pending.

P3 writer/QA correction commit `0957a516c09a97075c820d105ccdebac3c4cacc4`,
phase-order correction commit `d85456ea5d0d5c1c6e849f18846be52bf53f95c5`,
and P4 gate contract commit `bc494683f9d9b154c40bdc8069a3dfa48710c665` are
on `main`. P4-T01 is formally `BLOCKED_BY_INPUT`; it remains the retry pointer.
Do not run R04/R05 or write Revit from this handoff. Do not touch or stage RC01
paths.

## P2-T01 closeout — identity only

Assigned `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C` with fingerprint
`4b1275558a6c2c40828dbba1422c0063703c182fd9d7b800b36a448499a073c4`. The
identity binds, in profile order, all four current canonical board hashes, the
official `programa_necessidades.pdf` hash, and the P1-T01 report hash. The
identity-only implementation lives in
`src/amanda_agent/production/canonical_identity.py`; the machine record and
short reconciliation report are `project/requirements/canonical-solution-identity.yaml`
and `docs/reports/P2-T01-canonical-solution-identity.md`.

`SELECTION_SOLUTION_ID` and `PROJECT_STATE.selected_design` remain null;
`approval_hash` is null. No layout, `DesignSolution`, BIM-00, Revit/RVT access or
write, R04, or R05 work occurred. S02 remains
`STALE_BY_CANONICAL_REFERENCE_EXPANSION`. The focused identity, selection,
state, repository-hygiene, and plan-order gate passed **41/41**; changed-file
Ruff is recorded at closeout. `P2-T01` is PASS and `P3-T01` is the next
authorized pending task; P3 was not started.

Focused command:
`.venv/Scripts/python.exe -m pytest tests/unit/test_canonical_solution_identity.py tests/unit/test_production_selection.py tests/unit/test_canonical_state_migration.py tests/project/test_repository_hygiene.py tests/policy/test_plan_order.py -q`
— 41 passed. Changed-file Ruff command:
`.venv/Scripts/ruff.exe check src/amanda_agent/production/canonical_identity.py tests/unit/test_canonical_solution_identity.py tests/unit/test_canonical_state_migration.py tests/project/test_repository_hygiene.py`
— all checks passed. Scoped `git diff --check` passed. TDD evidence: identity
tests first failed because the module was absent; after implementation they
reached 11 passed/1 failed only because the required persisted manifest had not
yet been generated. An independent review found that an internally consistent
but incorrect board or reconciliation hash could reach the writer. A new RED
case reproduced it; the writer now recomputes the live identity first, and
both source-hash regressions pass. The state-routing regressions failed against
the old P2 pointer and passed after the formal P3 transition. The reviewer
recheck then found stale wording from the P1 closeout; the handoff now labels it
as historical. Final independent read-only review returned **APPROVE**, noting
the writer/source binding fix, exact source hashes, null selection/approval,
and P3-T01 as the next pending task. P2 implementation commit on `main`:
`aa1975a` (`feat: assign canonical solution identity P2-T01`). State-only
closeout commit `b563953` set `last_verified_commit` to this tested
implementation commit. Both commits were pushed; a fresh remote read confirmed
`origin/main` at `b563953` before this handoff/status refresh.

RC01 preflight used read-only inspection. The normal sandbox listed 34 tracked
paths as deleted because it could not enumerate the protected directory. An
authorized elevated read found 36 physical files: all 34 tracked files match
the Git index after clean filters; the other two are ignored `.rvt`/`.rte`
files. This is an ACL visibility issue, not repository data loss. No RC01 path
was restored, edited, staged, or included in this task.

To resume, start from `main`, read the required current documents in the order
in `START_HERE.md`, verify `PROJECT_STATE.yaml` and the P3-T01 dependency, then
execute only P3-T01's non-Revit canonical hard checks and P3 layout/approval
generation if those checks pass. Do not begin BIM-00 or Revit/R04/R05 from this
handoff.

## Current documentation flow

Start with `START_HERE.md`, then read `AGENTS.md`, `PROJECT_STATE.yaml`,
`docs/spec/CURRENT.md`, `docs/plan/CURRENT.md`, `docs/decisions/DECISIONS.md`,
and this handoff. The four active canonical images are normalized under
`docs/source/canonical/`; prior board images remain byte-identical under the
historical source path. Source and evidence inventories are covered by the
immutable manifest plus `SOURCE_MANIFEST.json`.

## P1-T01 closeout — four canonical boards

P1-T01 is implemented from `main`; the implementation binds the exact four
canonical image hashes and the official PDF hash. The crosswalk, geometry,
capacity/area authority, and remaining board/program discrepancies are in
`docs/reports/P1-T01-four-board-reconciliation.md`. The official 20-person,
626 m² internal, and 260 m² external program was not changed. The active
decision register now supersedes the three-source and S02 decisions while
preserving their signed history; the new solution identity remains unset and
`AMANDA-RUN-002-PAVILION-S02` remains stale.

Verification: the focused 11-module suite passed 100/100; changed-file Ruff
passed; `git diff --check` passed when scoped to P1-T01 files. A repository-wide
diff check also encountered pre-existing deleted GOLDEN/RC01 paths that deny
read access; those unrelated deletions remain unstaged and untouched. Independent
review by Huygens found no technical reconciliation blocker but withheld full
approval until commit/push, and asked that the historical decision-register
note below be clarified; it is now marked as a P0 checkpoint and superseded.
Follow-up review by Herschel verified the four-source decision, Board 03 count,
deviation schema/output hash, S01/S02 status, and task pointers, then found that
`AMANDA-RUN-002-PAVILION-S01` could still authorize selection and that the review
status wording here conflicted with the task graph. A regression test failed
for that alias and passed for the existing S01; the selection guard now rejects
both historical linear identities, and this handoff records those findings
instead of saying evidence is still pending. Implementation commit
`0d3fc94474f2a0d0944e10db6c602ce223aa7bc7` was pushed and a fresh remote read
confirmed `origin/main` at that SHA. Herschel's follow-up then caught the second
linear S01 alias; the fix and its regression test are in commit
`0d27fef6d068d471ac0bfe8b8634e902e08ed091`, which was pushed. A fresh remote
read confirmed `origin/main` at that SHA. Final independent review by Laplace
returned **APPROVE** for P1-T01: both historical S01 identifiers are rejected,
the task pointers and handoff agree, all four boards and the official program
are bound, and no BIM/R04/R05/Revit activity occurred. That reviewer ran the
two-case S01 regression only (2 passed; 6 deselected). The full focused gate
passed 100/100 and changed-file Ruff passed. `PROJECT_STATE.yaml` records
`0d27fef6d068d471ac0bfe8b8634e902e08ed091` as the last verified implementation
commit; the final handoff/state-only closeout commit is separate.

Open discrepancies are documented in the report: Board 03 draws six common
bathroom cells while the official PDF specifies five; the exact extra graphic
cell is not identifiable. Board 02/04 repeat or relabel archive, copa, and
sanitary functions with inconsistent areas/counts. Board 04 labels computer
and workshop uses without official room/area equivalents, and several support
labels do not map one-to-one. The PDF quantities/areas remain authoritative.
Canonical visual check CANON-011 remains blocked pending later Revit evidence;
P1-T01 made no Revit writes or BIM artifact. Next task: P2-T01 only; no R04/R05
or Revit work is authorized by this handoff.

## Historical P0 recovery log — reference only; superseded by current state above

## Completed work

- Tasks 1–6 are complete and pushed; the Task 6 close commit is
  `6e9995765316c321e6820c5f0cde23638dc07b46`.
- Task 7 normalized the four canonical board paths, preserved historic board
  images and source evidence, and reconciled the source validators. Its focused
  gates passed 18/18; supplemental source-manifest tests passed 5/5. Independent
  review approved the work after a direct ingest-validator rejection test was
  added. Task 7's implementation commit is
  `f5da48d5c25f7f2b33e3a09c7fe0a7c30485e27a`; the pushed documentation closeout
  is `fe1e5ea287cfb5dec75877a278349a7ab519e1ec`.
- Task 7's additional historical check found a pre-existing digest mismatch in
  `test_p08_freeze_binds_versions_and_current_file_hashes`: 4 passed, 1 failed.
  `decision-register.yaml` was unchanged by Task 7; retain this failure for the
  final report rather than rebinding the historical freeze.

## Task 8 complete

The hygiene test for absence of legacy plan/spec/handoff trees was added and
first run RED as expected. The old root instructions, 13 child plans, one
legacy spec, 88 notes/handoffs, 33 package-review artifacts, stale 2026-09-16
handoff report, and all four tracked plan ZIP archives have now been removed
from the active tree. Their blobs remain in the safety tag/Git history.
Independent review confirmed all four ZIP hashes and manifests, then requested
two fixes: one stale Blender report route and missing final gate evidence. Both
are fixed and recorded. A follow-up review found one cleanup-script comment
still naming a deleted plan; a hygiene test caught it RED, the route was
removed, and the GREEN result is recorded. Two standalone tool-lab handoffs
were removed after their findings were confirmed in maintained README/task
history; the detailed P02-T15 record was renamed as evidence and remains linked
from its result report. Final review approved the staged diff.

The ignored 13-file text-extraction cache was moved to
`project/provenance/extracted/source-extracts/`; its manifest paths were
updated and all records resolve. Original source files remain in the source
tree. `.gitignore`, `AGENTS.md`, the current spec and decisions, source
inventory routing, task registry plan paths, session/reboot handoff writers,
repository hygiene tests, historical report pointers, this handoff, and the
recovery report are updated. The final focused suite passed 73/73 and Ruff
passed across changed operational Python and focused test files. Commit
`5d95d12ce87559d0e986ce4db1dc880c550c8534` is on `main` and `origin/main`.
Elevated status confirmed 36 RC01 files intact and one worktree. The only
remaining named handoff is this file. No Revit/model action occurred. See
`docs/reports/repository-recovery.md` for the command, detailed evidence, and
known historical freeze mismatch.

## Task 9 complete; independent review approved

The independent review approved the inventory, hashes, retention decisions,
and recorded test evidence. It found one stale handoff status; the status was
corrected and the scoped re-review approved the correction. Commit
`c4adceb70c3824dba50c8ef3010472b94664b6f4` is on `main` and was pushed to
`origin/main`; fresh remote verification confirmed all four refs match.
The report/handoff closeout commit `1290ba3e83ed44fee4a447a7b6e6d6aad92604d1`
was also pushed and verified against the remote.

The 112-row RVT baseline is classified: 31 `LAB_FIXTURE`, 4
`CHECKPOINT_R04`, 4 `CHECKPOINT_R06`, 1 `CHECKPOINT_R08`, 1
`HISTORICAL_LINEAR_R12`, and 71 `UNKNOWN`. All `UNKNOWN` files remain
preserved. The historical linear model was moved by path only to
`revit/production/archive/linear-r12-superseded.rvt`; its 4,345,856-byte
SHA-256 remains
`ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29`. The
manifest now sits at `revit/production/archive/manifest.json`. Three byte-
identical S02 working duplicates are in `.recovery/rvt-duplicates/` until
Task 13; the S02 file named by the writer lease remains in place and
`revit/production/working/CURRENT.rvt` remains absent. No Revit process or
model content was opened or modified.

The signed decision register keeps its original historical `source_refs`
string because `approval_hash` binds that value. A proposed path update failed
register validation and was reverted without rebinding the hash; the current
archive path is recorded by the manifest, active selection history, and
recovery report.

Fresh Task 9 checks: R12 path guards 4/4; historical decision source test
1/1; state-store/status-dashboard 10/10; status CLI exited 0 and reported the
existing writer lease as HELD. The full production-runner unit module had
14/15 passing; its unchanged R04 routing fixture expected a lock exception
after the current acceptance gate returns early. The focused path checks passed
when run with `.venv/Scripts/python.exe -m pytest`; the bare `pytest.exe`
launcher could not import the local `scripts` namespace. Independent review
approved, implementation commit `c4adceb70c3824dba50c8ef3010472b94664b6f4`
and closeout commit `1290ba3e83ed44fee4a447a7b6e6d6aad92604d1` were pushed,
and remote main matched after the closeout push. `PROJECT_STATE.yaml` remains
at `RECOVERY-VALIDATE`.

## Task 10 complete; independent review approved (historical P0 checkpoint)

The 43-path design-engine baseline is fully classified in
`.recovery/design-engine-classification.json`: 4 active generator configs,
37 stale-evidence fixtures (including all seven S02 artifacts), 2 invalid
predecessor run logs recoverable from the safety tag, and 0 unknown paths.
Only the two invalid predecessor logs were removed from the active tree; their
SHA-256 values and exact tag recovery are in
`docs/reports/repository-recovery.md`. `design-engine/current/` remains absent.

At the Task 10/P0 recovery checkpoint, the signed decision register had not
changed. Its root-level S02 source_ref target,
`design-engine/runs/AMANDA-RUN-002-PAVILION/solution.json`, was absent from the
worktree, baseline, and recovery tag; the nested S02 finalist artifacts were
stale evidence. This is historical recovery context only. P1-T01 subsequently
updated the active register: the previous three-source and S02 detail records
are formally superseded with their signed history preserved, and
`DEC-CANONICAL-PARTI-002` binds the four current boards plus the official PDF.
See `project/requirements/decision-register.yaml` and the P1-T01 report.

Task 10 focused tests: 72 passed, 0 failed across `test_design_refine.py`,
`test_p08_t07_environmental_pass.py`, `test_bim_solution_compiler.py`,
`test_production_layout_bim.py`, `test_build_canonical_pavilion_run.py`,
`test_canonical_reference.py`, `test_canonical_pavilion_layout.py`,
`test_canonical_qa.py`, and `test_production_selection.py`. An expanded
10-module run including `test_canonical_state_migration.py` passed 76/76. No
full suite or Revit/model action occurred. Independent review approved the
scoped changes with no actionable findings. Implementation commit
`051161520f4725ffa6c650e39b6b128ffb43e09a` is pushed; fresh remote verification
matched `origin/main` at that SHA. The elevated view confirmed one worktree and
only `.recovery/` untracked. Task 11 began after the Task 10 closeout was
verified.

## Exact resume

Task 11 cleanup and Task 12 branch retirement are complete and independently
reviewed. Task 13 is now in progress: finish the final evidence, tests, and
document audit before removing `.recovery/` or setting the formal next task to
P1-T01. Do not use `git clean` to delete; preserve gate evidence, source files,
RVTs, and release artifacts.

## Task 11 complete; independent review approved

The read-only `git clean -ndX` preview listed 241 would-remove paths and two
vendor repositories it would skip. The preview and root-temp metadata are saved
under `.recovery/`. The preview includes protected
source PDFs/documents, provenance extractions, raw logs, production/checkpoint
RVTs, the live writer lock, all virtual environments, `.recovery/`, and
`.superpowers/`; these are not cleanup targets.

The preview has 134 root `.tmp-*` entries (104 scripts, 24 directories, and six
test log/text files), 32 `__pycache__` directories, and `.pytest_cache/`.
Preserve these six historical gate logs unchanged:
`.tmp-pytest-r05-canonical-full2.log`, `.tmp-pytest-r05-tree.log`,
`.tmp-y5.txt`, `.tmp-y7.txt`, `.tmp-y8.txt`, and `.tmp-y9.txt`. Also preserve
`.tmp-pytest-delivery-r11/`, referenced by the committed R11 evidence. The five
`.tmp-pytest-y5/` through `.tmp-pytest-y9/` basetemp directories are protected
test-output trees (four contain 1,679 files each; y7 contains 25); default
access was denied, and elevated read-only inspection confirmed generated
pytest outputs. Keep them for evidence.

The remaining root `.tmp-*.py` files are ignored scratch candidates. A static
AST pass parsed all 104 without executing them; their filenames have no
tracked source references. Some contain file-write or provider-call paths,
but no script was run. A scan of 345 nested `.rvt`/`.rfa`/`.rte` test fixtures
across root temp directories found only 6,149 bytes total (largest 53 bytes);
no actual Revit model is in that group.

Two other pytest scratch trees contain nested junctions, each targeting its
own `area-restrita` test fixture. Preserve both trees and do not move or
recursively remove them:
`.tmp-p08-t08-full/test_junction_escape_identity_0/revit/production/working`
and
`.tmp-p08-t08-full-available/test_junction_escape_identity_0/revit/production/working`.
The exact resolved targets are inside the matching test directories.

The explicit target manifest is recorded at
`.recovery/task11-approved-delete-manifest.csv` with its path list at
`.recovery/task11-approved-delete-list.txt`: 153 candidates (120 root scratch
entries, 32 `__pycache__` directories, and `.pytest_cache/`). The 120 root
entries are 104 scripts and 16 test-scratch directories; all resolved paths
stay inside the workspace and the selected directories have no nested
reparse points. Removed exactly those 153 paths with explicit
`Remove-Item -LiteralPath`, never `git clean`. Post-delete verification found
all targets absent, zero failures, all 14 excluded root temp evidence paths
present, and the fresh dry-run equal to the original set minus the removals:
88 paths remain, with no new or missing entries. `.ruff_cache/` and every
other unclassified path remain. Independent reviewer Carson approved the
exact 153-path delta, the 241-to-88 preview reconciliation, and the 14
preserved evidence paths with no actionable findings. Push and verify this
report/handoff closeout before Task 12.

The exact preserved paths include the six historical test log/text files,
`.tmp-pytest-delivery-r11/`, `.tmp-pytest-y5/` through `.tmp-pytest-y9/`, and
`.tmp-p08-t08-full/` plus `.tmp-p08-t08-full-available/` because they contain
internal test junctions. Production/checkpoint RVTs, private sources, raw
logs, provenance, writer lock, environments, `.recovery/`, `.superpowers/`, and
vendor repos remain preserved. No Revit/model action or tests occurred.

## Task 12 complete; independent review approved

Retired both obsolete branches after classifying their history. The local and
remote `codex/canonical-pavilion-migration` tips were already ancestors of
`main` (local comparison `20 0`, remote-tracking comparison `22 0`); remote
deletion succeeded and local `git branch -d` removed the merged ref.

The P08 branch had exactly two commits beyond `main`: `e5c9a0e` adds an
offline R01–R04 concept-candidate bundle for legacy `AMANDA-RUN-001-F01/F02`,
and `125c7d9` closes its handoff. It is not current four-board production
work and was not merged. Its complete history is preserved by the published
annotated tag `superseded-p08-t08-concept-offline-2026-09-24`, which peels to
`125c7d956d40fab6c358e4c6702199b4eac4d854`. The remote branch was deleted;
the local ref was removed by exact-OID `git update-ref -d`, not `branch -D`.

The recovery tag `pre-repository-recovery-2026-09-24` remains published and
peels to `30cc3b0f7860dfb5e46299402585213d1ac2d02b`. Fresh post-deletion
remote verification showed `origin/main` at `64d6b94503202fe7d29396efeb26e1e57f84b2c0`,
both old branch refs absent, and both tags present. Local status shows one
worktree on `main` and only `.recovery/` untracked. Independent reviewer
Pascal approved the branch proof, preservation tags, and post-deletion state.
No tests or Revit/model operations were run during this task.

## Task 13 complete; independent review approved

The `.recovery/` crosswalk was committed before deletion. All 15 items
(12,196,838 bytes) are accounted for in the recovery report, with zero reparse
points. The 112-row RVT inventory matched all retained paths; the three
quarantined copies matched retained checkpoints byte for byte. Their redundant
copies were removed, leaving 109 RVTs under `revit/`; RC01 still has 36 files
and its manifest/model hashes match the earlier verification.

The current structure is one plan (`docs/plan/CURRENT.md`), one spec
(`docs/spec/CURRENT.md`), and this sole active handoff. No ZIP is tracked or
present under `docs/`; `docs/notes/` and the old plan/spec/review directories
are absent. The source manifest remains present with 20 assets.

TDD readiness change: the first test failed because P1-T01 was absent from the
task registry. The registry now has P1-T01 as its only READY task and suspends
legacy `P08-CAN-T09` through `P08-CAN-T19`; no task was marked complete. The
focused gate passed 76/76 across repository hygiene, state/dashboard/task graph,
plan order, canonical references/layout/QA, source manifest, and provenance.
`amanda_agent status` exits 0 with phase P1 READY, next P1-T01, zero pending
tasks, five site conditions (three BLOCKING, two DEGRADING), and writer lease
HELD by `amanda-P08-CAN-T09-R03`. The lease was not changed. Independent
reviewer Halley approved the final recovery state. No Revit/model action.

## Git checkpoint

Task 9 implementation commit: `c4adceb70c3824dba50c8ef3010472b94664b6f4`;
report/handoff closeout commit: `1290ba3e83ed44fee4a447a7b6e6d6aad92604d1`.
Both were pushed. After the closeout push, a fresh `git ls-remote` check
confirmed `HEAD = main = origin/main` at
`1290ba3e83ed44fee4a447a7b6e6d6aad92604d1` and exactly one worktree.
Task 13 removed `.recovery/` after the full hash inventory and report transfer.
The three redundant quarantine copies were removed only after matching their
retained checkpoints; all 109 unique RVTs remain under `revit/`.

## Historical P4 continuation — normalized study audit and candidate search (2026-09-25)

This subsection records the earlier pre-DEC-CANONICAL-DETAIL-004 snapshot. Its
selection, eligibility, site-scope, and resume statements are superseded by the
active P4-T01 continuation above; use that section and `PROJECT_STATE.yaml`.

The user supplied explicit authorization for a read-only public candidate
search and asked to continue through later gates when they pass. The search
found only a `CANDIDATE` geographic context (Lagoa Nova / Av. Miguel Castro / a
rounded institutional GeoNatal point). It did not identify a parcel polygon
that can be tied to the TFG's approximate 24,135 m² site. No lot is
`PROVISIONAL` or `VERIFIED`; no owner, CPF, title or private records were
searched. Evidence is added to
`docs/reports/P4-T01-site-source-research-2026-09-25.md`.

An independent read-only audit found that missing site evidence and
`AMANDA_REVIEW_PENDING` should not alone prevent a reversible normalized
academic `STUDY` through R04. Existing site-data and preacceptance code already
allows that scope. The gaps still block cadastral placement, final grading,
legal frontage/setback/orientation statements, and actual availability or
transfer claims. The current P4 record still lacks a typed site-coordinate
mode, and the project state/spec wording needs an explicit normalized-study
scope before the gate can be issued. Human approval remains pending.

The first focused run of the R04 planner/provider suite had 5 failures, all at
`projection_area: MASS-SERVICE_CAPACITATION`: R04 exported only the outer
polygon ring and filled the six internal voids. TDD regressions reproduced the
missing-ring behavior in both planning and the generated Revit route. The
implementation now carries all interior rings into the R04 geometry, computes
net area including the voids, and makes independent geometry verification
reject a readback with a missing ring. Focused validation is **39 passed** for
`test_stage_massing.py`, the complete `test_production_layout_bim.py`, and the
mass provider route. Independent code review is still pending. A Ruff pass
reported existing violations in the touched legacy modules plus a new test
`exec` lint finding; the test lint finding must be addressed and changed-file
checks rerun.

No Revit process was started and no RVT was opened or written. A read-only
Horizun health call returned “no Revit is reachable.” The S02 lease remains
untouched; the recorded owner PID was not running and no Revit process was
present, but lease transition criteria and an exact RUN-003 target/checkpoint
have not yet been completed. `PROJECT_STATE.yaml` still points to P4-T01 and
still has no selected design/checkpoint. RC01 deletions remain untouched and
unstaged.

**Resume:** superseded. Continue from the latest `P4-T01 continuation` section
above and its explicit blocker list. Do not repeat already completed coordinate
binding, R04 ring/readback, or offline snapshot work.

## P4-T01 continuation — GeoNatal scope and Revit startup retry (2026-09-25)

- The user authorized read-only matching against public GeoNatal location,
  street, area, and geometry fields only. The existing report identifies a
  `PROVISIONAL_CANDIDATE` polygon (published `area=20,817.519`; the layer does
  not declare the unit) near the Prudente de Morais / Miguel Castro intersection;
  that node is outside the polygon. Its numeric value is 13.7% below the TFG's
  approximate 24,135 m² only if both values use the same unit. It is not an
  adopted cadastral boundary. No owner, CPF, private registration, title,
  or titularity data was queried or inferred. Details remain in
  `docs/reports/P4-T01-site-source-research-2026-09-25.md`.
- Health before and after the Revit retry returned `no Revit is reachable`.
  Revit PIDs 38152 and 40124 had no main window, `RevitAPI.dll`, or
  `Horizun.Revit.dll`, and no journal newer than 2026-09-24; they were stopped
  after these checks. A single clean launch from the Revit 2027 install folder
  created PID 31152, but after 40 seconds it still had no window/API/add-in and
  no new journal. No RVT was opened or written. Do not terminate PID 31152
  without a fresh safety check.
- S02 writer lease was left untouched. `CURRENT.rvt` and the exact RUN-003
  target/checkpoint remain unbound. `PROJECT_STATE.yaml` revision is 186;
  P3-T01 remains last completed and P4-T01 remains `BLOCKED_BY_INPUT`.
- Validation this continuation: `python -m amanda_agent status` exited 0 and
  showed P4-T01 blocked; `horizun_health` failed before and after startup. No
  test suite was run because no implementation changed. Earlier focused test
  results remain recorded in the P4 blocker report.
- Repository at entry was `main` / `origin/main` `4322402`; commit `79ba478`
  containing the provider retry record was pushed to `origin/main` successfully.
  This final dashboard/handoff closeout is included in the current main update.
  Pre-existing ACL-protected RC01 deletions remain untouched and unstaged.
  Changed files: `PROJECT_STATE.yaml`,
  `docs/reports/P4-T01-bim00-blocker-report.md`, `state/task-graph.yaml`,
  `state/HANDOFF.md`, and the CLI-refreshed `state/status.md` (observed HEAD
  `79ba478`).

**Resume:** obtain an observable interactive Revit 2027 session with Horizun
loaded (the current PID 31152 is not usable), then run `horizun_health`. Only
after health passes, bind a fresh RUN-003 target/checkpoint, verify and safely
reclaim the stale S02 lease using the project lock API, refresh gate bindings,
and run BIM-00. Do not use S02, do not write to Revit before BIM-00 PASS, and do
not advance R05.

## P4-T01 R04 closeout follow-up — 2026-09-26

This detailed closeout record adds evidence for the current state section at
the top of this file; it is not a second resume block. Earlier P4
startup/provider/lease blocker instructions above are historical and superseded
by the completed BIM-00 and R04 evidence below; do not repeat GeoNatal research,
startup diagnostics, or lease recovery.

The real RUN-003 R04 geometry is already saved, checkpointed, cold-reopened,
and typed-readback verified. The target/checkpoint SHA-256 is
`33a99c7c760125da434017210b7ea2d506a3914ae59e002769a14138cca27b49`; the
post-reopen query returned 25 elements (seven masses, 14 floors, four roofs),
complete coverage, zero unreadable. BIM-00 passed. No R05 or RC01 operation was
performed. Do not search GeoNatal again. S02 remains
`STALE_BY_CANONICAL_REFERENCE_EXPANSION`; its lease file was absent and was not
reclaimed. RUN-003's lease is free.

Fresh live check: Horizun 1.3.3 HEALTHY, Revit 2027 build 27.2.0.39, PID
38296; 73/73 registered commands, 80/80 tools visible, target exact-path
matched and active, two documents open (RUN-003 and HZ anchor), zero other
clients. The writer lease is released.

After the saved R04 reopen, current-model captures were exported for top
implantation, massing, overall perspective, administration, residential,
services, and child sector, plus a child/playground plan crop. Their PNGs,
dimensions, hashes, source view IDs, and temporary-view restoration status are
in `revit/production/evidence/AMANDA-RUN-003-R04/current-view-captures.json`.
All temporary options in the accepted capture set report restoration verified.
One earlier capture request combined orientation with a temporary crop and
returned `view_restored=false`; that image was excluded. Its operation did not
write geometry. Screenshots support review only; the plan is wireframe and the
internal room functions are not modeled, so CANON-011 remains open.

The Board-02 administrative footprint difference is now a formal
`CANONICAL_DEVIATION` in `docs/decisions/CANONICAL_DEVIATIONS.yaml`:
237.407316 m² per floor versus the board's approximate 200 m² (+37.407316 m²,
+18.703658%). The record is `OPEN_FOR_REVIEW`, lists alternatives, and binds
the board, official PDF, RUN-003 source geometry, input checkpoint, and output
checkpoint by SHA-256. No alternative was approved; official program quantities
and areas remain unchanged. The separate upper-plate/Level-2 mismatch remains
open in the P6 report.

TDD follow-ups each demonstrated the expected RED before implementation:
`test_canonical_deviation_record.py` failed while the formal record was absent;
`test_run003_view_capture_evidence.py` failed while the capture manifest was
absent. Both now pass with the status/checkpoint, R04 spatial, task graph, and
state-store modules (25 passed in the final combined run). P4→P6 ordering
passed 7/7. The passing commands were:

- `$env:PYTHONPATH='src'; python -m pytest -q --confcutdir=tests/unit tests/unit/test_canonical_deviation_record.py tests/unit/test_run003_view_capture_evidence.py tests/unit/test_status_checkpoint_consistency.py tests/unit/test_run003_r04_spatial_evidence.py tests/unit/test_task_graph.py tests/unit/test_state_store.py`
- `$env:PYTHONPATH='src'; python -m pytest -q --confcutdir=tests/policy tests/policy/test_plan_order.py`

An initial attempt omitted `PYTHONPATH=src` and failed module collection; the
corrected commands above passed. A dashboard test that imports `ortools`
remains unavailable in the host Python; no dependency was installed.

Files in this closeout: formal deviation register and decision update, P4/P6
reports, eight current PNGs and capture manifest, regression tests, dashboard,
`PROJECT_STATE.yaml` (revision 196, next `P6-T01`), task graph/history, and this
handoff. First-review findings were fixed and the current focused gates pass;
final follow-up review and commit/push status are recorded in the current-state
block at the top. Do not stage the pre-existing RC01 ACL-visible deletion entries.

**Exact resume:** the P4-T01/RUN-003 closeout is committed and published on
`main`; the remote ref was verified against local `HEAD`. Continue from
`PROJECT_STATE.yaml` revision 196 with `P6-T01` pending and CANON-011 open.
Resolve P6 visual/geometric gaps only when requested; do not advance R05, alter
RC01, or repeat GeoNatal research.
