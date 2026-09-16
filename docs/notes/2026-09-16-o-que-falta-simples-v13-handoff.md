# Handoff — subagente LUNA xhigh lê os planos e resume o que falta (2026-09-16)

## O que foi feito

- Subagente LUNA xhigh (Beauvoir, id `01a0a91c-b39c-7ee2-af5f-e0cf218546bd`) leu os planos,
  o estado e as análises anteriores e produziu
  `docs/notes/2026-09-16-o-que-falta-simples-v13.md` (o resumo simples pedido pelo dono).
- Limpeza local autorizada: removidos `.tmp/introspect.py`, `.tmp/fix_caps.py`,
  `.tmp/pytest-full.txt` e os basetemps `.tmp/pt`, `pt2`, `pt3` (caminho conferido antes de
  cada remoção). `.tmp/` ficou vazio e é ignorado pelo git.
- `scripts/cleanup-local.ps1` em simulação: 0 alvos de arquivo + 30 diretórios `__pycache__`.
  Nada disso foi aplicado neste turno.

## Divergência medida (importante para a próxima escrita BIM)

- O documento aberto no Revit **não é** `LAB_R01_TEMPLATE.rte`: `get_document_info` devolve
  `revit/lab/probe/LAB_ROUTE_PROBE.rvt`, Revit 2027, build `27.2.0.39`, 3749 elementos.
  Qualquer escrita deve reconferir o documento alvo antes do primeiro passo (regra WRITE→READ→VERIFY).
- Ponte viva e saudável: Horizun 1.3.3, `contract_hash 8b9600f5274d7dffb6e5bd5f`.

## Estado do grafo (conferido pelo subagente nos arquivos ao vivo)

- 159 tarefas: 136 PASS, 2 PASS_WITH_WARNINGS, 13 PENDING, 8 SUSPENDED, 0 FAIL.
  `next_task: P06-T14`; fase `PHASE_06 qa-release-exports: PENDING`.
- Bloqueios registrados: SITE_TOPOGRAPHY, SITE_BOUNDARY e SITE_OCCUPANCY (BLOCKING);
  SITE_FRONTAGE_COUNT e SITE_TRUE_NORTH (DEGRADING).
- Ordem do que falta na v13: P06-T14 → P07-T17/T19 → P08-T08 → P08-T09 → P08-T01 →
  P08-T10..T14 → P08-T15..T19 → itens acadêmicos humanos.

## Custo

- Nenhum item pago, premium ou com assinatura é necessário no caminho local.
  APS/Forge permanece DEFERRED_OPTIONAL, sem credencial.

## GitHub

- `origin` = https://github.com/matheussilva421/amanda-tfg-bim-agent.git — confirmado **PRIVADO**.
- `main` estava sincronizado em `42de45f` no início do turno; ver o commit deste turno abaixo.

## Pendências

- P06-T14 continua sendo a próxima tarefa; usar `revit/lab/exports/p06t14/` (vazio) como destino.
- Consolidar (sem apagar) `docs/notes/*-o-que-falta-simples-v3..v13.md` e os handoffs antigos: decisão do dono.
- PDFs da raiz são fonte registrada em `project/provenance/source-inventory.json`: só remover com autorização explícita.
- Nunca apagar: `docs/source/`, `TFG_Amanda_2026/`, `vendor/`, `.venv*/`, `.dotnet/`, `tool-lab/`, `state/`, `project/provenance/`.

## Comandos de retomada

```powershell
& '..venvScriptspython.exe' -X utf8 -m pytest tests -q --no-header -p no:cacheprovider --basetemp='..tmppt4' --ignore=tests/unit/test_topologic_spike.py
& '..venvScriptspython.exe' -X utf8 -m amanda_agent.cli bim status --project-root .
```
