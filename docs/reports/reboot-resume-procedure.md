# P07-T19 — reboot/resume procedure (historical drill)

Data: 2026-09-15  
Status: `PREPARED_PARTIAL`; a máquina não foi reiniciada.

## Procedimento validado nesta sessão

Este registro descreve o procedimento observado na data acima; o fluxo ativo
usa o handoff único em `state/HANDOFF.md`.

Foi validada localmente a preparação do procedimento:

- o contexto de retomada foi gerado de forma determinística e com redaction;
- o checkpoint `revit/lab/custom-api/T18_LAST_PASS.rvt` foi lido pelo manifesto
  e seu SHA-256 foi recalculado: `8ccab171e89fa4ac414f9ca3c57b5c4161cd7ee6dd61f45f86529703ee281cb2`;
- o estado e o task graph foram lidos do disco, sem edição por este procedimento;
- o comando `status` preservou sua saída de terminal e atualizou o dashboard
  derivado `state/status.md`;
- `resume` preservou a saída existente e reportou a task READY observada;
- `doctor` e health do provider continuam sendo comandos explícitos da primeira
  verificação pós-reboot.

Na leitura usada para o artefato, `PROJECT_STATE.yaml` informou
`phase_id=PHASE_02`, `last_completed_task=P09-T10`, `next_task=P06-T01`,
`state_revision=123`, `current_checkpoint=null` e `last_verified_commit=null`.
O estado pode mudar por agentes paralelos; a sessão nova deve sempre reler os
arquivos, em vez de confiar nesta fotografia.

## Primeiros comandos pós-reboot

O agente principal deve abrir uma sessão nova no mesmo checkout e executar:

```powershell
Set-Location 'C:\Users\slvma\Downloads\Github\Projeto Amanda'
$env:PYTHONIOENCODING='utf-8'
Get-Content -Raw AGENTS.md
Get-Content -Raw PROJECT_STATE.yaml
Get-Content -Raw state/HANDOFF.md
git status --short --branch
& './.venv/Scripts/python.exe' -m amanda_agent doctor
& './.venv/Scripts/python.exe' -m amanda_agent status
& './.venv/Scripts/python.exe' -m amanda_agent tool-lab status
& './.venv/Scripts/python.exe' -m amanda_agent resume
```

Depois, registrar em evidência separada:

1. a task READY retornada pelo task graph e a razão de sua prontidão;
2. a saúde observada do Revit/provider e o build comparado ao lock;
3. o checkpoint reaberto e seu hash comparado ao manifesto;
4. a re-query de estado atual antes de qualquer retry;
5. a decisão de continuar, fallback ou bloqueio.

## O que não foi validado agora

A confirmação de que uma sessão Codex nova identifica a próxima task READY sem
que Amanda reexplique o contexto será feita pelo agente principal em sessão
nova. Ela não foi simulada nem deve ser declarada como PASS neste relatório.

Também não houve reboot físico, close/reopen de um processo Revit neste drill,
instalação de provider, alteração de add-in, alteração de `%APPDATA%` ou
force-kill. O ciclo vivo de provider permanece uma gate independente.

Se houver uma instalação futura que realmente exija reboot, preservar o
checkpoint, escrever novamente o resume com os valores reais, fechar o processo
normalmente, reiniciar somente na janela autorizada e iniciar pela sequência
acima. Não repetir uma mutação interrompida sem reabrir, healthcheck e re-query.
