# Handoff — provider live sem Revit alcançável (2026-09-22)

## Estado atual

O trabalho continua em `PHASE_08`, com `P08-T08` como próxima tarefa e sem
checkpoint promovido. Nenhuma escrita BIM, save/close/reopen, alteração de
`PROJECT_STATE.yaml` ou promoção de export/GOLDEN ocorreu neste bloco.

## Evidência live nova

Foi executada uma sondagem read-only usando `McpProbeTransport(timeout=8)`:

```text
horizun_health: Error: no Revit is reachable. Is Revit running with the Horizun add-in loaded?
get_document_info: Error: no Revit is reachable. Is Revit running with the Horizun add-in loaded?
```

Os processos observados foram Revit PID `15608` e `39808`, ambos responsivos,
mas sem `MainWindowHandle` (`0`). A superfície de UI disponível para esta
sessão não expôs aplicações nativas, portanto não houve tentativa de clicar,
selecionar PID ou fechar processo.

A instalação local foi confirmada, sem reinstalação:

- Revit 2027, file version `27.2.0.39`, product version `20260716_1515(x64)`;
- `Horizun.addin`, `RevitCortex.addin` e `Amanda.ToolLab.Host.addin` presentes em
  `%APPDATA%\\Autodesk\\Revit\\Addins\\2027`;
- `horizun-mcp.exe` presente em `%LOCALAPPDATA%\\Programs\\Horizun\\MCP\\server`;
- o journal Revit mais recente registra o carregamento do Horizun e eventos de
  transação, mas isso é histórico e não substitui a sondagem live atual.

## Ações locais concluídas

- `python -m amanda_agent status` executado; `state/status.md` agora registra o
  `HEAD` atual.
- `python -m amanda_agent doctor` executado; `state/environment-report.json`
  atualizado com o ambiente observado.
- Removidos somente estes temporários regeneráveis do bloco atual:
  `.tmp-pytest-r08-point-final`, `.tmp-pytest-r08-point-final-full`,
  `.tmp-pytest-r08-point-full`, `.tmp-pytest-r08-point-green`,
  `.tmp-pytest-r08-point-red` e `.tmp-pytest-current-focused`.
- Preservados RVTs, checkpoints, journals, fontes, artefatos STUDY, GOLDEN e
  temporários históricos de diagnóstico.

O driver de produção foi executado em dry-run até R13:

```text
planned stages: R01 ... R13
layout hash: 9410f296b0d3a258a51971a6e2a35cd404f8018ca28ba5d6f36003516808539d
template: C:\\ProgramData\\Autodesk\\RVT 2027\\Templates\\Default_M_PTB.rte
dry run: nothing written
```

Esse resultado valida o planejamento local e o template selecionado; não é
prova de execução no Revit.

## Retomada exata

1. Uma pessoa deve tornar uma única sessão Revit 2027 visível e operável,
   dispensando o modal nativo caso esteja aberto, sem `Save As` e sem alterar o
   arquivo-alvo.
2. Repetir `horizun_health` e `get_document_info` read-only; confirmar PID e
   caminho do documento ativo.
3. Confirmar save/close/reopen independente do R05 existente.
4. Executar uma tentativa nova R06 com o compilador atual, exigindo `30/30
   VERIFIED`; preservar o journal falho anterior como histórico.
5. Somente após R06 verde continuar R07→R13, R14 QA, R15 cold reopen, exports e
   preparação do pacote final.

## Git

- O dashboard e o relatório de ambiente desta sondagem foram publicados junto
  com este handoff.
- O working tree ainda contém alterações/artefatos anteriores fora deste bloco,
  incluindo exclusões ACL-visíveis em `revit/lab/exports/p06t14/GOLDEN/RC01`,
  resultados Topologic e a árvore `revit/production`.
