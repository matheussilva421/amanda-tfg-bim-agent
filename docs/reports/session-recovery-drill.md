# P07-T17 — session recovery drill

Data: 2026-09-15  
Status desta preparação: `PREPARED_PARTIAL`  
Máquina: Windows / PowerShell 5.1

## Protocolo

O protocolo de recuperação preparado nesta sessão é:

1. classificar a falha como `CRASHED`, preservando a fronteira da mutação;
2. selecionar o último checkpoint com manifesto válido e SHA-256 recalculado;
3. reabrir esse checkpoint;
4. reconectar o provider preferido;
5. executar healthcheck;
6. reconsultar o estado atual do documento;
7. decidir `retry` ou `fallback` somente depois da reconsulta.

`src/amanda_agent/recovery/manager.py` implementa essa ordem. Quando a mutação
foi interrompida, o plano fica em `MANUAL_REVIEW` e `retry_allowed=false`; não
há reexecução cega.

O watchdog separado classifica `HEALTHY`, `BUSY`, `SUSPECTED_HANG`, `HUNG` e
`CRASHED`. Timeout isolado produz `SUSPECTED_HANG`. `HUNG` exige sinais
corroborantes e o período de graça. O force kill só é recomendado depois de
close normal, checkpoint/estado persistidos verificados, PID/StartTime próprios,
documento descartável/autorizado e autorização explícita.

## Evidência preparada agora

- Os testes focados de recovery, watchdog, reboot, dashboard e resumo passaram.
- `RESUME_AFTER_REBOOT.md` foi gerado atomicamente na raiz.
- O manifesto `revit/lab/custom-api/T18_LAST_PASS.rvt.manifest.json` foi lido e
  seu arquivo foi verificado por SHA-256; o hash é
  `8ccab171e89fa4ac414f9ca3c57b5c4161cd7ee6dd61f45f86529703ee281cb2`.
- A leitura de estado usada para o artefato registrou `PHASE_02`,
  `last_completed_task=P09-T10`, `next_task=P06-T01`,
  `current_checkpoint=null` e `state_revision=123`. O checkpoint acima foi
  obtido do manifesto físico e mantido separado do campo de checkpoint atual,
  que permanece ausente no estado.
- `state/status.md` foi gerado pelo comando `status`; ele é um derivado e não
  altera a revisão do estado por intenção do código.

Durante a preparação, agentes paralelos escreveram o estado compartilhado entre
leituras (`state_revision` passou por várias revisões e o último PASS observado
mudou de `P02-T18` para `P09-T10`). Essa concorrência é registrada como
limitação: a prova abaixo é uma fotografia do disco em cada comando, não uma
garantia de exclusividade sobre o estado enquanto outros agentes trabalham.

## Gate que permanece para uma sessão nova

A confirmação de que uma **nova sessão identifica a próxima task READY sem
contexto humano** será executada pelo agente principal em uma sessão nova. Ela
não foi simulada por código nesta sessão e não é declarada como PASS aqui.

Na sessão nova, executar exatamente:

```powershell
Set-Location 'C:\Users\slvma\Downloads\Github\Projeto Amanda'
$env:PYTHONIOENCODING='utf-8'
Get-Content -Raw AGENTS.md
Get-Content -Raw START_HERE_FOR_CODEX.md
Get-Content -Raw docs/notes/2026-09-15-p07b-recovery-continuity-handoff.md
Get-Content -Raw RESUME_AFTER_REBOOT.md
Get-Content -Raw PROJECT_STATE.yaml
git status --short --branch
& './.venv/Scripts/python.exe' -m amanda_agent doctor
& './.venv/Scripts/python.exe' -m amanda_agent status
& './.venv/Scripts/python.exe' -m amanda_agent resume
```

Registrar no próprio handoff da sessão nova: a task READY retornada, a fase,
blockers, health do provider, se o checkpoint foi reaberto e se houve re-query.
Se a saída continuar apontando `P06-T01`, `P07-T17` não deve ser promovida por
inferência: no grafo observado ela ainda depende de `P07-T15`.

## Limites

Nenhuma máquina foi reiniciada. Nenhum provider foi instalado ou atualizado,
nenhum add-in foi escrito e nenhum processo Revit foi fechado à força. A
preparação prova contratos locais e a integridade do arquivo de resume; não
prova a execução de uma sessão Codex nova nem um ciclo vivo de Revit/provider.
