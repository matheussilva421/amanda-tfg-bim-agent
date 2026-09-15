# Handoff — Amanda TFG BIM Agent — execução das fases 02/04 (2026-09-15)

## Estado em uma linha

O repositório tem remoto e está sincronizado. O add-in Horizun 1.3.3 está carregado e `healthy` no Revit 2027.2
educacional, e o perfil de permissão **passou a `full_write`** com `execute_python_ui_granted: true`, o que destravou
abrir, salvar e exportar documentos pelo MCP. Com isso **P02-T05 e P02-T07..T12 estão todos `PASS`**, inclusive o
Toposolid. Fases 00, 01, 03 e 07A fechadas; Fase 02 em 12/20 e Fase 04 em 19/22.

## Progresso por fase

| fase | PASS/total | observação |
|---|---|---|
| PHASE_00 | 3/3 | fechada |
| PHASE_01 | 13/13 | fechada |
| PHASE_02 | 12/20 | T01-T12 PASS; T13-T20 abertos (RevitCortex, fault injection, benchmark) |
| PHASE_03 | 15/15 | fechada |
| PHASE_04 | 19/22 | T01-T19 PASS; T20-T22 abertos (TopologicPy, Ladybug/Honeybee, CLI) |
| PHASE_05 | 0/23 | módulo `src/amanda_agent/bim/` implementado; tarefas ainda não registradas no grafo |
| PHASE_07A | 11/11 | fechada |
| demais | 0 | PHASE_06, 07B, 08, 09 |

Total do grafo: 159 tarefas, **73 PASS, 86 PENDING**. Prontas agora: `P02-T13` e `P04-T20`.

## O que mudou desde a versão anterior deste handoff

| commit | conteúdo |
|---|---|
| `e368093` | `chore(02)`: título/nível/parede (P02-T05, T07, T08) registrados |
| `48f0765` | `chore(02)`: piso e quarto (P02-T09, T10) |
| `e520c23` | `chore(02)`: matriz de documentação e exportação (P02-T11) |
| `ab471cf` | `feat(05)`: núcleo do compilador BIM — unidades, segurança, checkpoints, diff, plano e verificação |
| `dd40b88` | `feat(04)`: macrozonas, blocos, quartos, espaços externos, scoring, pareto, heurísticas ambientais, geração, pipeline e explain |
| `f33ec23` | `docs`: handoff das fases 02/04 |
| `dec9fd6` | `chore(04)`: fixtures de regressão (P04-T19) registradas |

## Bloqueio anterior: RESOLVIDO

`permission_profile = safe_write` recusava `DocumentSession`, `ExternalSideEffect`, `horizun_open_document`,
`horizun_save_document`, `horizun_relinquish_all`, `horizun_export`, `horizun_power_bi_push` e `horizun_create_family`.
O nível foi elevado **pelo dono, pela fita do Revit** (caminho exclusivo por design — `Ribbon.cs::BimModeCommand` usa
`Interference.WithDialogAnswer(DialogAnswer.Human)`, e nenhum pedido MCP pode elevar o próprio nível).

Evidência em `C:\Users\slvma\.horizun\settings.json`:

```json
{
  "execute_python_ui_granted": true,
  "execute_python_ui_granted_at_utc": "2026-09-15T10:47:23.9068297-03:00",
  "permission_profile": "full_write",
  "permission_profile_selected_from_revit_at_utc": "2026-09-15T13:50:37.2597575+00:00"
}
```

Dois detalhes que custaram rodadas e continuam valendo: o botão `Opciones avanzadas` fica **desabilitado sem documento
aberto** (`BimModeCommand` não declara classe de disponibilidade), e existem dois botões parecidos em painéis diferentes
da mesma aba — `Horizun RVT MCP → Permitir scripts` (Python) e `Producción BIM → Opciones avanzadas` (nível de permissão).
Ativar só o primeiro liga o Python e deixa o perfil em `safe_write`, porque um `settings.json` sem a chave
`permission_profile` lê como `safe_write`.

## Decisões tomadas (mantidas)

1. **Adaptador de janela para a ordem das fases**: `P03-T01` e `P07-T01` dependem de `P01-T13`, conforme a revisão
   dos planos, em vez de dependerem de uma fase posterior.
2. **`advance` fail-closed**: dependências não terminadas recusam o avanço; a exceção exige `--allow-unready` com
   motivo, e o motivo entra na evidência da tarefa.
3. **Sem auto-elevação de permissão**: ver a seção anterior.
4. **Fonte única do catálogo**: nenhum nome de ferramenta foi inventado; o mapa veio do contrato instalado
   (`horizun://contract/tools`, 80 ferramentas) e do `tools/list` (70). As 10 ferramentas só do contrato incluem
   `horizun_document_session`, `horizun_open_document`, `horizun_save_document`, `horizun_export` e `horizun_execute_python`.
5. **Repositório remoto** criado sob autorização explícita do usuário: privado, `amanda-tfg-bim-agent`,
   `https://github.com/matheussilva421/amanda-tfg-bim-agent`, com `origin` configurado e `main` rastreado.
6. **Documento ativo é lei**: `horizun_execute_python`, `save` e `audit_model` recusam agir sobre um documento que não
   seja o ativo e **não trocam de documento**. É preciso ativar antes; não existe flag de ativação em
   `horizun_document_session` (só `activate_other`, e apenas para `close`).

## Testes e validações

| comando | resultado |
|---|---|
| `pytest tests/providers -q -p no:cacheprovider --basetemp=.tmp-pytest-prov-4` | 11 passed, 0 failed |
| `python tool-lab/horizun/generate_toolmap.py --check` | toolmap is up to date |
| `pytest tests/regression` | 47 passed (fixtures do motor de projeto) |
| `pytest -q` (suíte completa, ver ressalvas abaixo) | 483 passed, 1 skipped com os `--ignore` conhecidos |
| `horizun_health` pela ponte MCP | `status: healthy`, `horizun_version 1.3.3`, `contract_hash 8b9600f5274d7dffb6e5bd5f`, `revit_build 27.2.0.39` |

Regra de execução obrigatória: `--basetemp` sempre único, porque o basetemp compartilhado herda ACLs quebradas em
`%LOCALAPPDATA%\Temp\pytest-of-slvma` e produz falhas fantasma. `$env:PYTHONIOENCODING='utf-8'` antes de qualquer
python, senão `UnicodeEncodeError` em cp1252.

## Pendências e próximos passos

1. **P02-T13** — clone/audit/build/deploy do RevitCortex em `vendor/RevitCortex`. Exige **fechar o Revit normalmente**
   antes; ao fim de P02-T12 o Revit 2027 está aberto com `LAB_HORIZUN_TOPO`.
2. **P02-T14..T20** — descoberta de tools do Cortex, smoke A/B, fallback C#, fault injection, crash drill, benchmark e CLI `tool-lab`.
3. **P04-T20..T22** — TopologicPy em `.venv-topologic`, Ladybug/Honeybee e CLI `design`/`compare`.
4. **P05-T01..T23** — o módulo `src/amanda_agent/bim/` já existe; falta registrar as tarefas no grafo com escopo honesto.
   Nota importante: **não existe invoker Horizun concreto** — `StageToolInvoker` é um `Protocol` abstrato em
   `src/amanda_agent/bim/stages/__init__.py`. Um invoker sobre `.tmp-hzpy.py`/`McpProbe` é candidato forte a tarefa própria.
5. **Limpeza pendente de autorização**: apagar `.venv-lockcheck` e os ~150 arquivos `.tmp-*`. O `.gitignore` cobre
   `.tmp-pytest/` e `.tmp-pytest-*/` apenas. Manter `.tmp-hz.py`, `.tmp-hzpy.py` e `.tmp-args.json` enquanto houver
   trabalho no Revit.
6. Handoff detalhado de P02-T12: `docs/notes/2026-09-15-p02-t12-toposolid-handoff.md`.

## Warts conhecidos que continuam valendo

1. `project/provenance/source-inventory.json` tem BOM — ler com `utf-8-sig`.
2. O probe `python312` do `doctor` diz MISSING embora o `.venv` seja 3.12.14. Falso negativo já registrado como evidência.
3. `test_unknown_dependency_and_cycle_are_rejected` não afirma o ciclo.
4. O ruff global tem achados preexistentes de outros agentes; não mexer.
5. Não existe `conftest.py`; os testes acham a raiz com `Path(__file__).resolve().parents[2]`.
6. `P02-T01.depends_on = P07-T13` é uma inversão preexistente do plano; não alterar sem decidir.
7. `rg` com glob no PowerShell falha (OS error 123); usar diretório sem glob.
8. `test_circuit_breaker` é flaky por ACL.
9. A Fase 02 mantém `phase_status: PENDING` mesmo com o phase gate fechado.
10. A existência de uma Scheduled Task "Horizun Codex Auto-Run" **não foi confirmada**. Não afirmar que existe;
   se for investigar, `Get-ScheduledTask | Where-Object TaskName -like '*Horizun*'` primeiro, e não desabilitar nada
   sem evidência.

## Como retomar

```powershell
cd "C:\Users\slvma\Downloads\Github\Projeto Amanda"
$env:PYTHONIOENCODING='utf-8'
& './.venv/Scripts/python.exe' -m amanda_agent status
& './.venv/Scripts/python.exe' -m amanda_agent task-graph
& './.venv/Scripts/python.exe' -m amanda_agent resume
```

Leitura obrigatória antes de agir: `START_HERE_FOR_CODEX.md`, `docs/notes/2026-09-15-revisao-planos-handoff.md`,
`docs/superpowers/plans/02-revit-tool-lab-providers.md` e este arquivo.

Objetivo canônico: `C:\Users\slvma\.codex\attachments\bca1fd4d-06ed-4df9-a08f-c9fbc9ae3db2\goal-objective.md`.

