# P02-T18 — Crash/recovery drill (revisado 2026-09-15)

Escopo: provar, com um escritor unico e documentos descartaveis, que uma mutacao
interrompida por crash nao vira PASS, e que a recuperacao reabre o ultimo
checkpoint verificado, reconecta o provider e reexecuta health/read smoke.

## Ponto de partida

- Checkpoint do ultimo PASS: `revit/lab/custom-api/T18_LAST_PASS.rvt`
  sha256 `8CCAB171E89FA4AC414F9CA3C57B5C4161CD7EE6DD61F45F86529703EE281CB2` (4370432 B).
- Baseline descartavel: `revit/lab/baseline/LAB_R00_EMPTY.rvt`
  sha256 `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D` (4366336 B).
- Ambos os hashes foram conferidos antes do drill (`t18-crash-run-log.txt`).

## Crash simulado

- Runner: `.tmp-t18-crash-run.ps1` (run stamp 20260915-155648).
- Revit proprio: pid 16556, start time 2026-09-15T15:56:48.5563207-03:00, aberto
  diretamente no documento descartavel `T18_CRASH_WORK.rvt`.
- Token/job proprios: `AMANDA_LAB_HOST_TOKEN` novo + `.tmp-t18-host-job.json`
  (expected_pid=16556). O OwnershipGuard so aceitou porque o pid esperado era o
  proprio processo, o token casava e o documento ativo era o working descartavel.
- Mutacao: marcador `step invoke-external-command: PASS (62479 ms)` presente no
  `host-status.log` com `step save-document` AUSENTE — ou seja, o limite
  interrompido era a mutacao nao salva.
- Terminacao: `Stop-Process` somente no pid 16556, depois de
  `observed_start == expected_start` (True).

## Resultado pos-crash

- `tool-lab/custom-api/results/t18-interrupted-host-result.json` ausente
  (result_present=False): a mutacao interrompida nao produziu resultado final.
- Bytes do working copy continuaram iguais ao checkpoint
  (`8CCAB171...`), logo a mutacao nao foi persistida.
- Journal do host preservado: `t18-crash-host-revit-journal.txt` (476804 B,
  sha256 `8823E1CAFE13FDF1058D98F7713CDAC6FFD77FABBEC7CF2E0307DA914B1D6BD7`).
- `host-status.log` do crash preservado em `t18-host-status.log`.

## Recuperacao

- Primeira tentativa (`t18-recovery-health.json`): o novo Revit (pid 1500) nao
  respondeu em tempo ao provider e a sonda devolveu
  `no Revit is reachable`. Registrado como NAO-PASS e repetido, sem tratar a
  falha de aquecimento como falha de dados.
- Segunda execucao (`t18-recovery-run-log.txt`): novo Revit proprio pid 28172,
  checkpoint reaberto, provider Horizun reconectado, health + read smoke OK.
  Leitura: `matched_total=1`, elemento 328658 (`Paredes`, Level 1,
  bbox min [0, -69.25, 0] / max [5000, 69.25, 3000]),
  `coverage_complete=true`, fingerprint `123600575aea38fa` (`t18-recovery-read.json`).
- Estado restaurado: add-ins compartilhados de volta com hash identico
  (`Amanda.ToolLab.Host.addin` `31B65614...`, `RevitCortex.addin` `C9E81E87...`),
  baseline e checkpoint intactos depois do drill, ambiente do runner restaurado.

## Leitura de disciplina

O documento recuperado mostra somente a parede 328658 do checkpoint anterior.
A parede que o crash interrompeu (valor esperado de elemento 0 no job) nao
reaparece em nenhum artefato e nao foi marcada PASS em lugar algum; ela tambem
nao foi repetida as cegas — foi descartada junto com a copia de trabalho.

Veredito: PASS (drill executado em copia descartavel, com propriedade provada e
sem tocar modelo de usuario).
