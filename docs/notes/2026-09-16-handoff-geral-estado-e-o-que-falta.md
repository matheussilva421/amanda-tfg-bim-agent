# Handoff geral — o que foi feito e o que falta

Data: 2026-09-16. Autor: agente Codex (sessão principal). Projeto: `Projeto Amanda` (TFG BIM agent).
Este documento é o handoff único pedido pelo dono nesta sessão: resume tudo o que já foi feito e tudo o que ainda falta. Não substitui os handoffs temáticos em `docs/notes/`; ele os indexa.

## 1. Estado em uma linha

159 tarefas = **136 PASS + 3 PASS_WITH_WARNINGS + 12 PENDING + 8 SUSPENDED, 0 FAIL**; próxima tarefa `P08-T08`; `state_revision: 155`; `PROJECT_STATE.yaml` em `GO_WITH_LIMITATIONS`; `selected_design: null`. Repositório limpo, branch `main`, HEAD `c864751`, sincronizado com `origin/main` (`https://github.com/matheussilva421/amanda-tfg-bim-agent.git`, privado). Nada pago, premium ou com assinatura foi usado.

## 2. O que já foi feito (por fase)

- **Fase 00 — fundação (3/3):** repositório, estado durável, ambiente travado (`state/bim-environment.lock.yaml`: Revit 2027 build `27.2.0.39`, `product_version 20260716_1515(x64)`), ordem revisada do plano mestre e diagnóstico de fase.
- **Fase 01 — fundação/ambiente/estado (13/13):** inventário de fontes, ingestão, estado persistente, gate de intervenção humana e CLI `advance` com evidência obrigatória.
- **Fase 02 — Tool Lab do Revit (20/20):** add-in Horizun 1.3.3 instalado a partir de fonte pinada (`cc4ea04e…`), catálogo mapeado (70 tools medidos vs 80 do contrato instalado), rotas de escrita provadas ao vivo, RevitCortex auditado e construído, toposolid provado, matriz de falhas e 18/18 rotas Horizun provadas (`tool-lab/horizun/results/probe-routes-2026-09-15-live10-13.json`). P02-T17 fechou com aviso: 4 de 8 casos de falha dependiam de Revit e ficaram `SKIPPED_NEEDS_REVIT`.
- **Fase 03 — inteligência de projeto (15/15):** registros de programa, terreno, norma e decisões; dados faltantes do terreno formalizados em `project/site/missing-data.yaml` e `state/blockers.yaml`.
- **Fase 04 — motor de projeto (22/22):** modelos de geometria, restrições, adjacências, fluxos, privacidade, arquétipos, macrozonas, blocos, salas, espaços externos, pontuação, pareto e heurísticas ambientais; spike opcional TopologicPy provado.
- **Fase 05 — compilador BIM (23/23):** núcleo do compilador, unidades, sentinel de segurança, checkpoints, diff, plano e verificação; compilador de solução e runner para estágios R01→R04.
- **Fase 06 — QA/release/exportações (15/15):** ensaio sintético de release R14→R16 executado (`scripts/bim_release_drill.py`), 71 artefatos versionados em `revit/lab/exports/p06t14/`, selo `GOLDEN/RC01/RELEASE_COMPLETE.json` = `SEALED`, recusa de segunda promoção comprovada. Ficou `PASS_WITH_WARNINGS` porque o R13 era marcador sintético de 53 bytes e as fronteiras close/restart/reopen eram simuladas.
- **Fase 07A — autonomia/segurança (11/11):** gate de intervenção humana, isolamento de segredos, retomada de sessão e recuperação de crash; perfil de permissão do add-in elevado a `full_write` com clique humano documentado.
- **Fase 08 — produção Amanda (7/19):** estudo gerado (`AMANDA-RUN-001`) com programa congelado de 20 pessoas; duas finalistas publicadas (F01 e F02) com `solution.json`, `metrics.json`, `validation.json`, `geometry.geojson`, plantas e zonas em PNG/SVG, `WHY_THIS_OPTION.md` e manifesto de artefatos.
- **Fase 09 — opcionais (4/10):** gate APS deu `NO-GO` (sem capacidade local bloqueada por ferramenta e rota paga fora de escopo); Blender adiado por falta de necessidade real.

## 3. O que foi feito nesta sessão (2026-09-16)

- **P06-T14 registrado e commitado** (`d20dc44`): ensaio R14→R16 com manifesto, exportações, persistência e recusa de segunda promoção; 26 testes focados passaram.
- **Rota stdio do Horizun restaurada e comprovada ao vivo:** `health` = `healthy`, `get_document_info` = `LAB_ROUTE_PROBE`, `contract_hash 8b9600f5274d7dffb6e5bd5f`.
- **Compilador, runner, journal e crosswalk de produção commitados** (`aff860a`): `solution_compiler.py`, `runner.py`, `lab_fixture.py`, `journal.py`, `state/providers/semantic-crosswalk.yaml`, `scripts/bim_lab_drill.py` com teste de preflight.
- **Análises v13/v14/v15 do que falta** produzidas e commitadas (`a67adad`, `2cc501e`, `c864751`), com dashboard `state/status.md` regenerado pelo CLI canônico e `state/status.md`+nota commitados.
- **Limpeza local executada com script verificado** (`scripts/cleanup-local.ps1 -Apply`): removidos `.tmp-r16`, `.tmp-pytest-handoff` (319 MB) e 30 diretórios `__pycache__`; `remaining scratch=0 pycache=0`.
- **Suíte completa verde:** `pytest tests` → **822 passaram, 0 falharam** (33 s), excluído apenas `tests/unit/test_topologic_spike.py`.
- **Subagentes LUNA xhigh** usados para as análises de leitura (v12 e v15 escritas por subagente; v16 em andamento).

## 4. O que falta

### 4.1 Produção Revit (Fase 08 — 12 pendentes)

1. **P08-T08 — massas conceituais das finalistas** (próxima tarefa, READY). Criar um RVT separado por finalista em `CONCEPT_ONLY`, estágios R01→R04, com conferência de medidas, preview e salvar/fechar/reabrir. Não existe CLI para candidato conceitual real; o driver `scripts/bim_concept_candidates.py` ainda precisa ser criado (padrão de `scripts/bim_lab_drill.py`, com lock de escritor, revalidação de alvo e journals por estágio). O título diz "top 3" e só existem 2 finalistas — divergência a registrar.
2. **P08-T09 — escolha formal.** Comparar F01/F02, gravar `APPROVED_FOR_BIM` com `approval_hash` e marcar revisão de Amanda pendente. Hoje `selected_design: null` e `solutions/finalists/comparison.md` está em DRAFT/PENDING.
3. **P08-T10 a P08-T14 — modelo de produção e documentação:** RVT de trabalho e compilação R01→R13 (projeto, terreno, níveis, massa, paredes, ambientes, acessibilidade, mobiliário, paisagismo, materiais, documentação), com lease, `WRITE → READ → VERIFY` e checkpoint em cada etapa. Depende de P08-T09.
4. **P08-T15 a P08-T17 — QA, candidato e exportações:** QA R14, RC R15, reabertura a frio e validação de IFC/PDF/DWG/PNG, tabelas, páginas, hashes e relatórios.
5. **P08-T18/T19 — pacote final e GOLDEN:** preparar o pacote (T19), conferir caminhos e hashes, e só então promover R16 a `GOLDEN-001` (T18).

### 4.2 Lacunas técnicas que travam a escrita

- **Crosswalk sem entrada registrada:** `revit.create_grid` e `revit.create_roof` estão `registered_entry: null` em `state/providers/semantic-crosswalk.yaml`, com gap declarado. A rota (`horizun_create_elements`) está PROVEN no probe de 18/18, mas a regra do registry proíbe adivinhar o nome: o gap só vira entrada quando o arquivo de evidência prova exatamente aquele nome semântico.
- **Evidência só PROVIDER:** `state/capabilities.yaml` tem 11 entradas, todas `evidence_scope: PROVIDER`, **0 PRODUCTION**. Sem isso P08-T01 (liberação de produção) não fecha.
- **P02-T17 com aviso:** 4 de 8 casos de falha ainda `SKIPPED_NEEDS_REVIT`.

### 4.3 Retomada/recuperação (SUSPENDED)

- **P07-T17 — drill de sessão nova:** exige uma sessão Codex genuinamente nova lendo o estado e identificando a próxima tarefa; simular na mesma sessão não vale.
- **P07-T19 — simulação/procedimento de reinício completo:** exige reinício real autorizado.

### 4.4 Dados externos que só o dono resolve (BLOCKING)

- `SITE_TOPOGRAPHY`, `SITE_BOUNDARY`, `SITE_OCCUPANCY` — **BLOCKING**; `SITE_FRONTAGE_COUNT`, `SITE_TRUE_NORTH` — DEGRADING; `REGULATION_APPLICABILITY` em `PENDING_VERIFICATION`.
- Isso trava `final-altimetric-accessibility-validation`, `final-area-verification`, `final-grading` e `final-site-availability-claim`. O estudo planar provisório pode continuar.

### 4.5 Opcionais suspensos (não bloqueiam nada)

- **P09-T03/T04/T05 — Blender:** registrar, laboratório e pipeline de render. Adiado por falta de necessidade real.
- **P09-T07/T08/T09 — APS:** auditoria, segredo e sandbox cloud. `NO-GO`; nenhuma rota paga é necessária.
- **Entregas acadêmicas humanas:** 10 itens PENDING + 1 PROVISIONAL em `project/requirements/academic-deliverables.yaml` (caderno, visitas, metaprojeto, estudo preliminar, anteprojeto, pranchas, memoriais, defesa, autoria, submissão).

## 5. Testes e validações desta sessão

```powershell
.venv\Scripts\python.exe -X utf8 -m pytest tests -q --no-header -p no:cacheprovider --basetemp='.tmp-pytest-handoff' --ignore=tests/unit/test_topologic_spike.py
```

Resultado: **822 executados, 822 passaram, 0 falharam** (exit 0, 34,9 s).

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\cleanup-local.ps1 -Apply
```

Resultado: `removed 1 targets and 30 __pycache__ directories`; `remaining scratch=0 pycache=0`.

```powershell
.venv\Scripts\python.exe -X utf8 -m amanda_agent.cli task-graph
```

Resultado: `total 159`, `ready P08-T08`, `blocked P08-T09..P08-T16 (+3 more)`, `parallel P08-T08`.

## 6. Ambiente ao vivo (medido nesta sessão)

- **Revit:** processo `Revit` PID 30736 vivo, título `Autodesk Revit 2027.2 - EDUCACIONAL (NÃO COMERCIAL) - [LAB_ROUTE_PROBE - Planta de piso: Nível 1]`; build `27.2.0.39`.
- **Horizun:** perfil `full_write` confirmado em `C:\Users\slvma\.horizun\settings.json` (`permission_profile: full_write`, `execute_python_ui_granted: true`).
- **Documento ativo:** `LAB_ROUTE_PROBE.rvt` — divergente do último snapshot de saúde (que mostrou `LAB_R00_EMPTY`). Trocar o documento por um alvo descartável antes de qualquer escrita; `revit/lab/baseline/**` é protegido pelo sentinel e nunca pode ser destino.
- **Lock de escritor:** `state/locks/revit-writer.lock` livre.

## 7. Git

- Branch `main`, HEAD `c864751`, `main...origin/main` sem divergência, worktree limpo (nada pendente de commit).
- Remoto: `https://github.com/matheussilva421/amanda-tfg-bim-agent.git` (privado).

## 8. Pendências conhecidas do registro de estado

- `PROJECT_STATE.yaml` e `state/status.md` ainda mostram `last_verified_commit: NOT_RECORDED` apesar do Git alinhado — anotado nas análises v14/v15, não alterado para não inventar verificação.
- `docs/notes/2026-09-16-o-que-falta-simples-v15.md` cita HEAD `2cc501e`; o HEAD atual é `c864751`. O v16 (em produção por subagente LUNA) substitui o v15.
- `docs/reports/p08-preflight.md` é retrato histórico (revisão 123) e não deve ser usado como dashboard.

## 9. Próximos passos concretos

1. Confirmar na tela qual documento está ativo e deixar um RVT descartável seguro em `revit/lab/`.
2. Resolver o gap do crosswalk para `revit.create_grid` (e `revit.create_roof`): rodar experimento real no Tool Lab criando grid via `horizun_create_elements` em RVT de laboratório, com `WRITE → READ → VERIFY`, gravar JSON de evidência com sha256 em `tool-lab/horizun/results/`, adicionar entrada `operation: grid` em `state/capabilities.yaml` e só então preencher `registered_entry`.
3. Escrever `tests/unit/test_bim_concept_candidates.py` (RED) e criar `scripts/bim_concept_candidates.py`.
4. Executar P08-T08 para F01 e F02 em `revit/lab/candidates/`, com journals, checkpoints, save/close/reopen e conferência de métricas.
5. Fechar P08-T09 (comparação + escolha `APPROVED_FOR_BIM`) e seguir para P08-T10→P08-T19.

## 10. Como retomar

```powershell
cd 'C:\Users\slvma\Downloads\Github\Projeto Amanda'
git status --short --branch; git log --oneline -3
.venv\Scripts\python.exe -X utf8 -m amanda_agent.cli task-graph
.venv\Scripts\python.exe -X utf8 -m amanda_agent.cli status
```

Leia este arquivo, depois `docs/notes/2026-09-16-o-que-falta-simples-v15.md` (ou v16 quando existir) e o handoff temático mais recente em `docs/notes/`. Use sempre `--basetemp='.tmp-pytest-*'` (o `.gitignore` só cobre `.tmp-*`).
