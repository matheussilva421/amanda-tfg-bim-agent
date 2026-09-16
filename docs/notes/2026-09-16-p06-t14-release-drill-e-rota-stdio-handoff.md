# Handoff — P06-T14 (ensaio R14→R16), rota stdio restaurada e limpeza local

Data: 2026-09-16 (madrugada). Autor: agente Codex. Projeto: `Projeto Amanda` (TFG BIM agent).

## 1. Estado em uma linha

159 tarefas = **136 PASS + 3 PASS_WITH_WARNINGS + 12 PENDING + 8 SUSPENDED, 0 FAIL**; `next_task: P08-T08`; `state_revision: 155`. Revit 2027 vivo, add-in Horizun 1.3.3 `healthy`, `contract_hash 8b9600f5274d7dffb6e5bd5f`, perfil `full_write`. Nada pago, premium ou com assinatura foi usado.

## 2. P06-T14 — ensaio sintético de release R14→R16 → PASS_WITH_WARNINGS

O drill já existia em código (`scripts/bim_release_drill.py`, commit `abe34c2`, com `tests/unit/test_bim_release_drill.py`). Faltava executá-lo e registrar o resultado. Comando executado (exit 0):

```powershell
& '.venv\Scripts\python.exe' -X utf8 scripts\bim_release_drill.py --release-root '.\revit\lab\exports\p06t14' --release-id RC01 --execute
```

Saída resumida: `candidate: revit\lab\exports\p06t14\RC01`, `manifest: PASS`, `exports: PASS`, `persistence: PASS`, `second promotion refused: True`, `status: PASS`.

Artefatos gerados: **71 arquivos** entre `revit\lab\exports\p06t14\RC01\` e `revit\lab\exports\p06t14\GOLDEN\RC01\` — `model.rvt`, `exports\model.ifc`, `documentation.pdf`, `documentation.dwg`, `previews\page-0001.png`, `QA_REPORT.md`, `EXPORT_REPORT.md`, `persistence.json`, `manifest.json`, `plan-evidence\` (20 JSON + `synthetic-template.rte`) e `qa-reports\`. O selo `GOLDEN\RC01\RELEASE_COMPLETE.json` está `{"status":"SEALED"}`.

Testes focados:

```powershell
& '.venv\Scripts\python.exe' -X utf8 -m pytest tests/unit/test_bim_release_drill.py test_release_manifest.py test_release_promotion.py test_persistence_plan.py test_release_cli.py -q --basetemp='.tmp\pt4'
```

Resultado: **26 passaram, 0 falharam**.

Registro canônico no grafo:

```powershell
& '.venv\Scripts\python.exe' -X utf8 -m amanda_agent.cli advance --task P06-T14 --status PASS_WITH_WARNINGS --expected-revision 154 ...
```

→ `recorded P06-T14 PASS_WITH_WARNINGS`, `next task P08-T08`, `revision 155`.

### Ressalvas gravadas como evidência (motivo do PASS_WITH_WARNINGS)

- O fixture R13 é um **arquivo marcador sintético de 53 bytes** (`AMANDA-SYNTHETIC-R13`, `source-plan=P05`, `release-id=RC01`), não um RVT real.
- `close`, `restart`, `reopen` e `reconnect` são fronteiras simuladas (`simulated=True`).
- Portanto o drill prova a **cadeia de release** (manifesto, exportação, persistência, recusa de segunda promoção), não o comportamento do Revit real. Revit real e export real continuam em P08-T15/T16.

## 3. Descoberta: a rota stdio voltou a funcionar

- `C:\Users\slvma\.horizun\discovery\revit-2027-30736.json` voltou a ser legível (antes dava `PermissionError 13`). Contém `pipe_name: "Horizun-30736"`, `pid: 30736`, `auth_token`, `contract_hash 8b9600f5274d7dffb6e5bd5f`, `addin_version 1.3.3`, `protocol_version 2` e a lista de comandos.
- `McpProbeTransport` (stdio) funciona ao vivo: `horizun_health` → `healthy`; `get_document_info` → `LAB_ROUTE_PROBE`.
- Documento aberto no Revit: **`revit/lab/probe/LAB_ROUTE_PROBE.rvt`** (3749 elementos). `LAB_R01_TEMPLATE.rte` **não** está confirmado como documento aberto — conferir antes de qualquer escrita.
- `scripts\bim_lab_drill.py --rvt revit\lab\baseline\LAB_R00_EMPTY.rvt --preflight` → `REFUSED (protected filename/path component 'baseline' cannot be a writable target)`, exit 2. O sentinel está correto: nunca usar `baseline`, `release`, `GOLDEN`, `master`, `source` ou `checkpoint` como destino de escrita.

## 4. Limpeza local executada (pedido do dono)

- `pwsh -File scripts\cleanup-local.ps1 -Apply` → `removed 1 targets and 15 __pycache__ directories` (alvo: `.tmp-r16`).
- `.tmp\pt5` (423 arquivos, basetemp antigo do pytest) removido com script verificado: raiz conferida, alvo exatamente `<raiz>\.tmp`, `git ls-files .tmp` vazio (nada versionado dentro), topo apenas `pt5` e nenhum `.git` interno. Saída: `apagando ... 423 arquivos; topo = pt5`, `existe agora: False`.
- `.tmp\` ficou vazio e **não é ignorado pelo `.gitignore`** (o padrão é só `.tmp-*`); por isso ele ainda aparece como `?? .tmp/` no `git status`. Efeito inofensivo, mas convém não usar `.tmp/` como basetemp de novo — preferir `.tmp-pytest-*`, que é ignorado.
- **Não apagados** (exigem decisão explícita): os 2 PDFs da raiz (`TFG_Amanda Fernandes_ENTREGA 15.06.2026.pdf` e `programa_necessidades.pdf`), byte-idênticos aos de `docs/source/`, itens do `source-inventory.json` e lidos por `bootstrap/get-source-inventory.ps1:66`; também `logs\raw\` (evidência da instalação do Horizun) e os dois runs `design-engine\runs\AMANDA-RUN-001-invalid-2026-09-15{,-rooms}` — estes são evidência citada em `state/task-graph.yaml:2390` e `state/task-history.yaml:1964`, então apagar quebraria rastreabilidade.

## 5. Git

- `origin` = `https://github.com/mattheusilva421/amanda-tfg-bim-agent.git`, confirmado **privado**. Branch `main`, HEAD `a67adad` (docs v13), sincronizado com `origin/main`.
- **Há 19 arquivos modificados e ~35 não versionados** de trabalho anterior ainda sem commit (código: `src/amanda_agent/bim/providers/horizun.py`, `src/amanda_agent/bim/stages/__init__.py`, `src/amanda_agent/commands/bim.py`, `src/amanda_agent/models/capability.py`, `src/amanda_agent/tools/evidence.py`; estado: `PROJECT_STATE.yaml`, `state\*.yaml`, `state\status.md`; testes: 4 arquivos; novos: `src/amanda_agent/bim/{journal,lab_fixture,runner,solution_compiler}.py`, `scripts/bim_lab_drill.py`, `state/providers/semantic-crosswalk.yaml`, `solutions/`, 5 testes novos, `revit/lab/exports/`).
- O diff é grande e mistura P07/P08 com o registro do `advance`; decidir o write set e commitar em bloco temático antes de seguir para P08-T08, para não perder esse trabalho.

## 6. Próxima tarefa e retomada

Próxima: **P08-T08** — massas conceituais das finalistas em `CONCEPT_ONLY`, estágios R01→R04, com leitura de verificação, preview, save/close/reopen e rejeição de R05–R16 (`docs/superpowers/plans/08-amanda-production-run.md`, linhas 136–145).

```powershell
git status --short --branch; git log --oneline -3
& '.venv\Scripts\python.exe' -X utf8 -m amanda_agent.cli task-graph
& '.venv\Scripts\python.exe' -X utf8 -m amanda_agent.cli bim status --project-root .
```

## 7. Pendências conhecidas

- Commit do write set acumulado (19 modificados + ~35 novos).
- P08-T01: `state/capabilities.yaml` ainda é todo `evidence_scope: PROVIDER`, 0 PRODUCTION.
- P08-T09: `solutions/finalists/comparison.md` existe apenas como DRAFT/PENDING; `selected_design` continua `null`.
- P07-T17/T19 (SUSPENDED): exigem sessão nova genuína e reinício real; não auto-simular.
- Bloqueios de terreno por dado externo: `SITE_TOPOGRAPHY`, `SITE_BOUNDARY`, `SITE_OCCUPANCY` (BLOCKING); `SITE_FRONTAGE_COUNT`, `SITE_TRUE_NORTH` (DEGRADING); `REGULATION_APPLICABILITY` em `PENDING_VERIFICATION`.
- P02-T17 segue `PASS_WITH_WARNINGS` (4 de 8 casos de falha `SKIPPED_NEEDS_REVIT`).

