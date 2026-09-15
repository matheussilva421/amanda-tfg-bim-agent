# Handoff — Amanda TFG BIM Agent — execucao das fases 02/04 (2026-09-15)

## Estado em uma linha

O repositorio tem remoto e esta sincronizado. O add-in Horizun 1.3.3 esta carregado e `healthy` no Revit 2027.2
educacional (PID 35036), mas o perfil de permissao permanece `safe_write`, o que recusa abrir, salvar e exportar
documentos pelo MCP. Isso trava P02-T05 (fixture) e P02-T07..T12 (smoke de leitura, nivel, parede, piso, quarto,
exportacoes e Toposolid). A Fase 00 esta fechada, a Fase 04 avancou ate P04-T08, e ha dois subagentes LUNA em voo.

## Progresso por fase

| fase | PASS/total | observacao |
|---|---|---|
| PHASE_00 | 3/3 | fechada nesta sessao |
| PHASE_01 | 13/13 | ja estava fechada |
| PHASE_02 | 5/20 | T01-T04 e T06 PASS; T05 e T07-T12 bloqueados pelo perfil `safe_write` |
| PHASE_03 | 15/15 | ja estava fechada |
| PHASE_04 | 8/22 | T01-T08 PASS |
| PHASE_07A | 11/11 | ja estava fechada |
| demais | 0 | PHASE_05, 06, 07B, 08, 09 |

Total do grafo: 159 tarefas, 55 PASS.

## O que foi feito nesta sessao (com commits)

| commit | conteudo |
|---|---|
| `7a05235` | `feat(00)`: diagnostico da ordem de fases — `src/amanda_agent/state/plan_order.py`, `tests/policy/test_plan_order.py`, `docs/reports/phase-00-verification.md` |
| `c51a97f` | `feat(00)`: ordem revisada entre fases aplicada ao grafo — `build_task_graph.py`, `state/task-graph.yaml` (`P03-T01->P01-T13`, `P07-T01->P01-T13`) |
| `9f60ded` | `feat(07a)`: recusar `advance` com dependencias abertas, com `--allow-unready "<motivo>"` registrado na evidencia |
| `fde2140` | `feat(02)`: mapa do catalogo Horizun a partir do contrato instalado — `state/providers/horizun-toolmap.yaml`, `tests/providers/test_toolmaps.py`, `tool-lab/horizun/*` |
| `3411fd9` | `chore`: Fase 00 e descoberta do catalogo Horizun registradas como PASS |
| `4fd68c1` | `feat(04)`: dependencias do motor de projeto declaradas e travadas — `pyproject.toml`, `requirements.lock.txt` (venv `.venv-lockcheck` provou imports + 354 testes) |
| `bb01bc8` | `feat(04)`: modelos, geometria, restricoes, adjacencia, fluxos, privacidade e arquetipos (P04-T02..T08) |
| `6e1f37c` | `chore`: tarefas do solver da Fase 04 registradas |

## Decisoes tomadas

1. **Adaptador de janela para a ordem das fases**: `P03-T01` e `P07-T01` passaram a depender de `P01-T13`,
   conforme a revisao dos planos, em vez de dependerem de uma fase posterior.
2. **`advance` fail-closed**: dependencias nao terminadas recusam o avanco; a excecao exige `--allow-unready`
   com motivo, e o motivo entra na evidencia da tarefa. `P02-T06` foi registrado assim porque `P02-T05` depende
   de lancamento humano do Revit.
3. **Sem auto-elevacao de permissao**: `Ribbon.cs::BimModeCommand` usa `Interference.WithDialogAnswer(DialogAnswer.Human)`
   e `Settings.cs::TrySetPermissionProfile` recusa escrita sem 3 chaves. Um pedido MCP nao pode elevar o proprio nivel.
   O caminho e exclusivo do dono pela fita: aba `Horizun Hub` -> painel `Produccion BIM` -> `Opciones avanzadas` ->
   `Que puede hacer el asistente?` -> `Modificar, exportar y manejar documentos` -> marcar `Entiendo lo que permite este nivel`
   -> `Activar este nivel`.
4. **O botao da fita exige documento aberto**: `BimModeCommand` nao declara classe de disponibilidade, entao a fita fica
   desabilitada na tela `[Inicio]` quando nao ha documento aberto.
5. **Fonte unica do catalogo**: nenhum nome de ferramenta foi inventado; o mapa veio do contrato instalado
   (`horizun://contract/tools`, 80 ferramentas) e do `tools/list` (70). As 10 ferramentas so do contrato incluem
   `horizun_document_session`, `horizun_open_document`, `horizun_save_document`, `horizun_export` e `horizun_execute_python`.
6. **Repositorio remoto criado** sob autorizacao explicita do usuario: privado, `amanda-tfg-bim-agent`,
   `https://github.com/matheussilva421/amanda-tfg-bim-agent`, com `origin` configurado e `main` rastreado.

## Testes e validacoes

| comando | resultado |
|---|---|
| `pytest -q -p no:cacheprovider --basetemp=".tmp-pytest-<unico>"` (suite completa) | 364 passed, 1 skipped — ultima execucao verde antes dos subagentes em voo |
| `pytest tests/unit tests/policy tests/project tests/providers` | 323 passed, 1 skipped |
| `pytest tests/solver tests/geometry` | 31 passed |
| `.venv-lockcheck` (venv limpo a partir de `requirements.lock.txt`) | imports de ortools/shapely/networkx/ifcopenshell PASS + 354 testes |
| `horizun_health` pela ponte MCP | `status: healthy`, `horizun_version 1.3.3`, `contract_hash 8b9600f5274d7dffb6e5bd5f`, `revit_build 27.2.0.39` |

Regra de execucao obrigatoria: `--basetemp` sempre unico, porque o basetemp compartilhado herda ACLs quebradas
em `%LOCALAPPDATA%\\Temp\\pytest-of-slvma` e produz falhas fantasma. `$env:PYTHONIOENCODING='utf-8'` antes de
qualquer python, senao `UnicodeEncodeError` em cp1252.

## Bloqueio atual

`permission_profile = safe_write`. Em `Settings.cs` o perfil `safe_write` recusa tudo que seja `DocumentSession`,
`ExternalSideEffect`, `read_only`-excedente, e por nome `horizun_open_document`, `horizun_save_document`,
`horizun_relinquish_all`, `horizun_export`, `horizun_power_bi_push` e `horizun_create_family`.
`C:\\Users\\slvma\\.horizun\\settings.json` ainda nao existe, entao o default e aplicado em memoria.

A acao foi pedida ao usuario em texto simples (exclusiva do dono). Enquanto ela nao chega, o que da para fazer
sem documento aberto e limitado: nenhuma ferramenta MCP responde ao bridge se houver dialogo modal em primeiro plano,
o que ja foi observado com o dialogo `Escolher o modelo` aberto.

## Pendencias e proximos passos

1. **P02-T05** — com um documento aberto no Revit: salvar exatamente em `revit/lab/baseline/LAB_R00_EMPTY.rvt`,
   fechar e reabrir uma vez sem escrita de provedor, hashear SHA256, registrar hash e resumo inicial de avisos em
   `tool-lab/fixtures/baseline-fixture.yaml` e `tool-lab/fixtures/baseline-manifest.json`.
2. **P02-T07** — copiar a fixture, abrir a copia, chamar `horizun_health`, `get_document_info`,
   `horizun_model_scan`/`horizun_audit_model` e `horizun_query_model`, provar que o caminho devolvido e a copia
   descartavel, capturar resumo de elementos e contagem de avisos, reconsultar e afirmar que nada mudou.
   Evidencia em `tool-lab/horizun/results/read-smoke.json`.
3. **P02-T08..T12** — nivel, parede, piso/quarto, matriz de documentacao/exportacao e Toposolid, cada um com
   copia descartavel nova e persistencia provada por salvar/fechar/reabrir.
4. **P02-T12 tem uma lacuna real**: o contrato nao cria Toposolid. As alternativas sao criar a superficie a mao no
   Revit e entao usar `horizun_grade_toposolid_around_floors`/`horizun_embed_floors_in_toposolid`, ou pedir Python
   via `horizun_request_python_access`. Nenhuma das duas esta provada nesta maquina.
5. **P04-T09..T18** — em execucao por subagente LUNA; integrar, rodar `pytest tests/solver tests/geometry`,
   commitar com staging explicito e registrar os `advance` em ordem.
6. **P05-T01..T08** — em execucao por subagente LUNA (modulo `src/amanda_agent/bim/`).
7. Limpeza: cerca de 30 arquivos `.tmp-*.py`, `.tmp-args.json`, `.tmp-broad3.log`, `.tmp-full1.log`,
   `.tmp-contract.json`, `.tmp-graph-before.json`, `.tmp-pytest-*/`, `.venv-lockcheck/`, `.tmp-release-run.ps1`.
   O `.gitignore` cobre `.tmp-pytest/` e `.tmp-pytest-*/` apenas. Manter `.tmp-hz.py` e `.tmp-args.json`
   enquanto houver trabalho no Revit.
8. Handoff: este arquivo.

## Warts conhecidos que continuam valendo

1. `project/provenance/source-inventory.json` tem BOM — ler com `utf-8-sig`.
2. O probe `python312` do `doctor` diz MISSING embora o `.venv` seja 3.12.14. Falso negativo ja registrado como evidencia.
3. `test_unknown_dependency_and_cycle_are_rejected` nao afirma o ciclo.
4. O ruff global tem achados preexistentes de outros agentes; nao mexer.
5. Nao existe `conftest.py`; os testes acham a raiz com `Path(__file__).resolve().parents[2]`.
6. `P02-T01.depends_on = P07-T13` e uma inversao preexistente do plano; nao alterar sem decidir.
7. `rg` com glob no PowerShell falha (OS error 123); usar diretorio sem glob.
8. A existencia de uma Scheduled Task "Horizun Codex Auto-Run" **nao foi confirmada**. Nao afirmar que existe;
   se for investigar, `Get-ScheduledTask | Where-Object TaskName -like '*Horizun*'` primeiro, e nao desabilitar nada
   sem evidencia.

## Como retomar

```powershell
cd "C:\\Users\\slvma\\Downloads\\Github\\Projeto Amanda"
$env:PYTHONIOENCODING='utf-8'
& './.venv/Scripts/python.exe' -m amanda_agent status
& './.venv/Scripts/python.exe' -m amanda_agent task-graph
& './.venv/Scripts/python.exe' -m amanda_agent resume
```

Leitura obrigatoria antes de agir: `START_HERE_FOR_CODEX.md`, `docs/notes/2026-09-15-revisao-planos-handoff.md`,
`docs/superpowers/plans/02-revit-tool-lab-providers.md` e este arquivo.

Objetivo canonico: `C:\\Users\\slvma\\.codex\\attachments\\bca1fd4d-06ed-4df9-a08f-c9fbc9ae3db2\\goal-objective.md`.

