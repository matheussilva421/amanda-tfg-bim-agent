# Relatório completo do projeto Amanda TFG BIM Agent — insumo para o próximo agente

**Data da leitura:** 2026-09-16 (análise ao vivo). **HEAD analisado:** `1e10f7c0008cc630006b56849104666673379cbe` (`docs: analise v16 do que falta (subagente LUNA + verificacao do agente)`, 2026-09-16 07:26 -03:00). **Branch:** `main` = `origin/main` (https://github.com/matheussilva421/amanda-tfg-bim-agent.git).

**Natureza deste documento:** análise de leitura. Nenhum arquivo de estado, tarefa, plano, modelo Revit ou artefato GOLDEN foi alterado para produzi-lo. A única escrita desta sessão é este relatório e o handoff que o acompanha, mais o commit/push desses dois arquivos.

**Como usar:** leia as seções 2, 3 e 7 antes de tocar em qualquer coisa; use a seção 8 como roteiro e a seção 6 como lista de problemas abertos. Onde houver divergência entre este relatório e um documento antigo de `docs/notes/`, vale o que este relatório mediu ao vivo — e a evidência está citada linha a linha.

---

## 1. Método e evidências examinadas

Leituras ao vivo nesta sessão:

- Git: `git status --short --branch`, `git log`, `git diff`, `git show HEAD:<path>`, `git ls-files`.
- Estado versionado: `PROJECT_STATE.yaml`, `state/task-graph.yaml`, `state/task-history.yaml`, `state/status.md`, `state/capabilities.yaml`, `state/blockers.yaml`, `state/tool-health.yaml`, `state/install-manifest.yaml`, `state/bim-environment.lock.yaml`, `state/design-run-freeze.yaml`, `state/known-warnings.yaml`, `state/environment-report.json`, `state/providers/semantic-crosswalk.yaml`.
- Planos: `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md` (raiz), `docs/superpowers/plans/00..09`, `PLAN_SELF_REVIEW.md`, `START_HERE_FOR_CODEX.md`, `AGENTS.md`, `RESUME_AFTER_REBOOT.md`.
- Código: `src/amanda_agent/**` (287 arquivos), `scripts/**`, `tests/**` (294 arquivos).
- Evidências de laboratório: `tool-lab/{horizun,revitcortex,custom-api,topologic,environmental,fault-injection,blender,aps,reports}`.
- Estudo: `design-engine/runs/AMANDA-RUN-001/**`, `solutions/finalists/comparison.md`, `project/requirements/**`, `project/site/**`, `project/provenance/**`.
- Sistema: processos (`Get-Process Revit*, horizun*`), ACLs (`Get-Acl`, `icacls`), `.horizun`, `state/locks`.
- Execução: suíte completa `.venv/Scripts/python.exe -m pytest -q` → **1 failed, 822 passed** (62,86 s); reprodução isolada do spike TopologicPy com traceback completo.

Divergências conhecidas entre documentos antigos e o estado vivo estão listadas na seção 6 (P-04).

---

## 2. Veredito em uma página

O **control plane está construído, instrumentado e majoritariamente verde**; a **metade de produção do TFG praticamente não começou**. Números do grafo vivo (`state/task-graph.yaml`): **159 tarefas — 136 PASS, 3 PASS_WITH_WARNINGS, 12 PENDING, 8 SUSPENDED, 0 FAIL**; `state_revision: 155`; `phase_gate: GO_WITH_LIMITATIONS`; `next_task: P08-T08`; `last_completed_task: P06-T14`.

O que existe e funciona: ingestão e proveniência das fontes da Amanda (23 documentos, `source-set-v1`, hashes conferidos), biblioteca de requisitos/programa (20 pessoas, 626 m² internos, 260 m² externos), design engine determinístico com dois finalistas publicados (`AMANDA-RUN-001-F01/-F02`), Tool Lab com três provedores Revit medidos, crosswalk semântico, compilador BIM R01→R13 com Safety Sentinel, checkpoints, journal e `WRITE → READ → VERIFY`, QA/export/release com selo de GOLDEN, recuperação/segurança/sessão, e uma suíte de 823 testes.

O que não existe: **nenhum modelo Revit de produção**, nenhum `revit/production/working/AMANDA_WORKING_001.rvt`, nenhum `bim/releases/GOLDEN-001/`, nenhuma exportação de produção (IFC/PDF/DWG/PNG do modelo real), nenhuma seleção formal `APPROVED_FOR_BIM`. `P08-T08` a `P08-T19` (12 tarefas) estão `PENDING`; `P07-T17`/`P07-T19` estão `SUSPENDED`; os dados de terreno que sustentam as validações finais são bloqueadores ativos.

Três fatos medidos agora que qualquer continuação precisa absorver antes de agir:

1. **As 34 entradas versionadas de `revit/lab/exports/p06t14/GOLDEN/RC01` estão inacessíveis por ACL** e aparecem como deletadas no `git status`. Não é perda de dado do RC: a cópia-fonte `RC01/` está intacta e legível (35 arquivos em disco, incluindo `model.rvt`), e o pacote selado tem 67 arquivos versionados (33 em `RC01/` + 34 em `GOLDEN/RC01`). É um diretório criado com DACL quebrada, o mesmo padrão B-001 já registrado. **Não commite essa deleção.**
2. **A suíte só fica 100% verde com rede.** Offline ela é 822/823: `tests/unit/test_topologic_spike.py` falha porque `topologicpy` consulta o PyPI para montar o cabeçalho do OBJ; sem rede, `Helper.Version()` devolve `None` e `OBJString` estoura `TypeError`. Falha pré-existente, já documentada em handoffs anteriores, confirmada hoje com traceback.
3. **O Revit não está em execução nesta sessão.** Existem apenas `RevitAccelerator` e seis processos MCP órfãos (`horizun-mcp` ×3, `RevitCortex.Server` ×3, iniciados 09:40 e 10:57 de hoje). Sem Revit vivo e sem confirmação humana na tela, `P08-T08` em diante não pode executar escrita.

---

## 3. Arquitetura e mapa do repositório

**Control plane (Python 3.12, venv pinado em `.venv`).** Pacote `src/amanda_agent` com CLI Typer (`python -m amanda_agent`) e os comandos: `version`, `doctor`, `status`, `task-graph`, `advance`, `phase-gate`, `advance-phase`, `resume`, `rollback`, `ingest`, `bootstrap`, `design`, `compare`, `tool-lab`, `bim`, `qa`, `export`, `release`.

| Área | Onde | Papel |
| --- | --- | --- |
| Estado durável | `state/` (`*.yaml`, `*.json`, `*.md`), `PROJECT_STATE.yaml` | grafo de tarefas, histórico, capabilities, blockers, tool-health, lock de ambiente, freeze do estudo, dashboard |
| Crosswalk/provider | `state/providers/*.yaml`, `src/amanda_agent/bim/providers/*` | rota semântica → ferramenta registrada do provedor, transporte MCP |
| Compilador BIM | `src/amanda_agent/bim/**` (`plan`, `runner`, `journal`, `safety`, `checkpoints`, `verification`, `stages/*`) | estágios R01→R13, journal, checkpoints, WRITE→READ→VERIFY |
| Design engine | `design-engine/config/*`, `src/amanda_agent/design/**` | geração determinística, scoring, refinamento, finalistas |
| QA/release | `src/amanda_agent/qa/**`, `src/amanda_agent/release/**` | QA de modelo/programa/acessibilidade/IFC/DWG/PDF, manifesto e promoção GOLDEN |
| Recuperação/segurança/sessão | `src/amanda_agent/recovery/**`, `security/**`, `session/**`, `state/locks.py`, `state/human_gate.py` | watchdog, retomada, lease único de escritor, redação, portões humanos |
| Laboratório | `tool-lab/**` | provas por provedor, fault-injection, TopologicPy, ambiental, Blender/APS adiados |
| Planos e revisão | raiz (`COMBINED`, `design`), `docs/superpowers/plans/00..09`, `docs/review/*` | plano mestre + 9 fases, cópias geradas e scripts de validação documental |
| Evidência Revit local | `revit/lab/{baseline,horizun,revitcortex,custom-api,probe,exports,release}` | RVTs descartáveis, checkpoints, ensaio sintético P06-T14 |
| Fontes privadas (fora do Git) | `TFG_Amanda_2026/**`, `docs/source/**`, PDFs da raiz | originais imutáveis; `.gitignore` protege |

Caminhos que o plano de produção espera e que **ainda não existem**: `revit/production/working/AMANDA_WORKING_001.rvt`, `bim/releases/GOLDEN-001/` (`bim/` existe e está vazio). Note que `.gitignore` ignora `*.rvt`, `*.rfa`, `*.rte` — o RVT do pacote final fica fora do Git por decisão registrada (LFS nunca aprovado).

---

## 4. O que já foi feito

| Fase | Plano | Tarefas | Resultado registrado |
| --- | --- | --- | --- |
| PHASE_00 | `00-master-implementation-plan.md` | 3 | 3/3 PASS — repositório sem realocar o bundle, ordem de dependência, verificação global |
| PHASE_01 | `01-foundation-environment-state.md` | 13 | 13/13 PASS — fundação, ambiente, estado persistente, CLI, bootstrap idempotente |
| PHASE_02 | `02-revit-tool-lab-providers.md` | 20 | 19 PASS + `P02-T17` PASS_WITH_WARNINGS — Tool Lab, Horizun/RevitCortex/custom-api, registry de capabilities |
| PHASE_03 | `03-project-intelligence.md` | 15 | 15/15 PASS — ingestão, proveniência, requisitos, programa decidido (20 pessoas) |
| PHASE_04 | `04-design-engine.md` | 22 | 22/22 PASS — solver, scoring, refinamento, CLI `design`/`compare`, spike TopologicPy opcional |
| PHASE_05 | `05-bim-compiler.md` | 23 | 23/23 PASS — unidades, Safety Sentinel, checkpoints, diff, planos, estágios R01→R13, CLI `bim`, compile sintético ponta a ponta |
| PHASE_06 | `06-qa-release-exports.md` | 15 | 14 PASS + `P06-T14` PASS_WITH_WARNINGS — QA, persistência, exports, manifesto e promoção GOLDEN (ensaio **sintético**) |
| PHASE_07A | `07-autonomy-recovery-security.md` | 11 | 11/11 PASS — AGENTS.md de produção, grafo, protocolos de sessão, budgets, blockers, watchdog, redação, trust, dashboard, human gate |
| PHASE_07B | `07-autonomy-recovery-security.md` | 8 | 6 PASS + `P07-T17`/`P07-T19` SUSPENDED — retomada em sessão nova e reinício real |
| PHASE_08 | `08-amanda-production-run.md` | 19 | 6 PASS + `P08-T01` PASS_WITH_WARNINGS + 12 PENDING — preflight, re-ingestão, site, freeze, run 001, refinamento, passe ambiental |
| PHASE_09 | `09-optional-render-cloud.md` | 10 | 4 PASS + 6 SUSPENDED — render/Blender adiado (`DEFERRED_OPTIONAL`), APS `NO-GO` |

Destaques de evidência já fechada:

- **Provedores:** `horizun` primário (commit `cc4ea04e9ecfe547ad349f22e0864019ce1ead1f`, server 1.3.3, `contract_hash 8b9600f5274d7dffb6e5bd5f`, perfil `full_write`, ciclo de documento provado); `revitcortex` 2.0.0 (typed fallback; `create_room` falhou e não tem ciclo de documento); `custom-api` (fallback de último recurso; `create_wall` + sessão de documento). Build Revit **27.2.0.39** (`20260716_1515(x64)`).
- **Instalação auditada:** `state/install-manifest.yaml` fecha a cadeia de verificação do binário Horizun (4/4 hashes conferem, commit stampado nas DLLs). Limitação registrada: SDK pinado **10.0.400 ausente** (máquina só tem 8.0.422) — rebuild/upgrade do provedor não é possível hoje.
- **Fontes:** 23 documentos, `source-set-v1`, `verify_ingested_sources.py` → 23 `MATCH`, 0 falhas; manifesto `sha256 0419094976aa7840f6bb5afc069cef133df07b58b3f6ce102271741a56740686`; `TFG_Amanda Fernandes_ENTREGA 15.06.2026.pdf` 54.553.582 B `16abe602…`; `programa_necessidades.pdf` 31.004 B `11daa9ef…`.
- **Estudo congelado:** `P08-DESIGN-RUN-001` `FROZEN_FOR_STUDY` com hash de 10 arquivos congelados (programa, site, pesos, perfis, arquétipos, tolerâncias, decision-register).
- **Ensaio de release:** `P06-T14` promoveu o pacote do ensaio em `revit/lab/exports/p06t14/{RC01,GOLDEN/RC01}` (71 artefatos físicos, 67 versionados) com `manifest=PASS`, `exports=PASS`, `persistence=PASS` e segunda promoção recusada. **É ensaio sintético**: fixture de 53 bytes, sem processo Revit e sem provider vivo; IFC/PDF reais ficam para P08-T15/T16.
- **Suíte de testes:** 294 arquivos, 823 testes coletados em 10 diretórios (`unit` 596, `solver` 65, `project` 25, `providers` 23, `regression` 23, `bootstrap` 10, `geometry` 4, `policy` 4, `integration` 1, `__pycache__` 0).

---

## 5. O que falta

### 5.1 Bloco de produção (PHASE_08, 12 tarefas PENDING — o caminho crítico)

Ordem e critérios extraídos de `docs/superpowers/plans/08-amanda-production-run.md`:

| Tarefa | Entrega | Critério de aceite | Trava atual |
| --- | --- | --- | --- |
| `P08-T08` (READY) | massing conceitual por finalista, `CONCEPT_ONLY`, R01→R04, preview 3D, save/close/reopen | lease único, métricas conferidas contra `solution.json`, R05–R16 recusados | **não existe driver de candidato conceitual**; `bim execute` só aceita `SYNTHETIC_LAB`; `revit.create_grid`/`create_roof` sem `registered_entry`; Revit não está vivo; o título fala em "top 3" e só há 2 finalistas |
| `P08-T09` | `solutions/finalists/comparison.md` + seleção delegada e `APPROVED_FOR_BIM` com `approval_hash` | exatamente uma solução aprovada por baseline; `amanda_review=AMANDA_REVIEW_PENDING` | documento existe em `DRAFT/PENDING`; recomendação não registrada em `state/`; depende de T08 |
| `P08-T10` | `revit/production/working/AMANDA_WORKING_001.rvt` | lease, Safety Sentinel no caminho, hash pré-build | depende de T09; diretório de produção inexistente |
| `P08-T11`–`P08-T14` | compilação R01→R13 (11 estágios: projeto, terreno, níveis, massa, casca, layout, aberturas, ambientes, acessibilidade, mobiliário, paisagismo, materiais, documentação) | por estágio: WRITE→READ→VERIFY, warning delta, checkpoint, PROJECT_STATE atualizado; após R08 reconciliação de áreas/quantidades (sala faltante = stop) | R09 e validações finais dependem de dados normativos/altimétricos que estão bloqueados |
| `P08-T15`–`P08-T17` | QA R14 completo, RC R15 com reabertura a frio real, exports IFC/PDF/DWG/PNG + hashes e tabelas | reabertura a frio compara QA crítica e divergência exige rollback ao último checkpoint PASS | exige Revit vivo real; hoje só há ensaio sintético |
| `P08-T19` → `P08-T18` | pacote final em staging (`AUTONOMY_REPORT.md`, `RUN_SUMMARY.md`, status acadêmico) e promoção para `bim/releases/GOLDEN-001/` sem sobrescrita | hash do RVT pós-cópia igual ao do RC; GOLDEN marcado imutável; RVT binário fora do Git | ordem registrada é T17 → T19 → T18; `bim/` vazio hoje |

### 5.2 Tarefas suspensas e pendências herdadas

- `P07-T17` (retomada em sessão nova) — exige encerrar esta sessão e abrir **outra sessão Codex genuína** que identifique a próxima tarefa READY sem reexplicação; simulação na mesma sessão não vale.
- `P07-T19` (reinício completo) — exige `RESUME_AFTER_REBOOT.md` regenerado, estado commitado, fechamento normal de Revit/Codex e sessão nova; nenhum reinício ocorreu até agora.
- `P02-T17` (matriz de injeção de falhas, PASS_WITH_WARNINGS) — 4 de 8 casos seguem `SKIPPED_NEEDS_REVIT`: `FI-001` elemento inválido, `FI-002` tipo de família inexistente, `FI-003` elemento hospedado sem hospedeiro, `FI-006` item inválido após itens válidos. Todos exigem documento Revit descartável e portão humano.
- `P08-T01` (preflight, PASS_WITH_WARNINGS) — as 11 capabilities de `state/capabilities.yaml` são todas `evidence_scope: PROVIDER`; **0 em `PRODUCTION`**.
- `P09-T03/T04/T05` (Blender) — `DEFERRED_OPTIONAL` com justificativa medida: não há entrega acadêmica que peça render fotorrealista e o Blender nem está instalado na máquina.
- `P09-T07/T08/T09` (APS) — gate `NO-GO` por dois motivos independentes: nenhuma capability local está bloqueada por ferramenta e a rota cloud é paga/fora de escopo.

### 5.3 Dados e decisões que dependem de terceiros

- **Terreno (bloqueadores ativos):** `SITE_TOPOGRAPHY`, `SITE_BOUNDARY`, `SITE_OCCUPANCY` [BLOCKING] e `SITE_FRONTAGE_COUNT`, `SITE_TRUE_NORTH` [DEGRADING]. Eles barram `final-grading`, `final-area-verification`, `final-altimetric-accessibility-validation`, `final-corner-and-setback-designation`, `final-orientation-compliance-statement` e `final-site-availability-claim`; permitem `schematic-macrozoning`, `planar-massing-study`, `schematic-sectorization`, `study-massing`, `study-scenario-development`, `study-orientation-reasoning` e `preliminary-access-split`.
- **Ambiente do dono:** confirmar o documento ativo na tela do Revit antes de cada escrita e clicar nos diálogos de permissão; abrir a sessão nova e autorizar o reinício real (P07-T17/T19); obter os documentos verificáveis do lote.
- **Acadêmico:** `project/requirements/academic-deliverables.yaml` tem 11 itens — 10 `PENDING` + 1 `PROVISIONAL` (pranchas "4-6 A1"), todos com `requires_human_action: true` e datas nulas. Nenhum `TFG_COMPLETE` pode ser declarado enquanto houver item pendente.

---

## 6. Problemas encontrados (com evidência)

### P-01 — [CRÍTICO, ambiente] GOLDEN/RC01 inacessível: 34 entradas versionadas marcadas como deletadas no Git

- `git status --short` mostra **34** entradas ` D` sob `revit/lab/exports/p06t14/GOLDEN/RC01/` — a árvore versionada inteira daquele diretório (`.md`, `.json`, `.ifc`, `.pdf`, `.dwg`, `.png`, `plan-evidence/*`) — e o aviso `could not open directory 'revit/lab/exports/p06t14/GOLDEN/RC01/'`.
- `Get-ChildItem`/`icacls`/`Get-Acl` no diretório retornam `Acesso negado` / `Attempted to perform an unauthorized operation`; o diretório-pai `GOLDEN` tem ACL herdada normal (`Dell-G15-5530\CodexSandboxUsers:(I)(OI)(CI)(M,DC)`).
- `RELEASE_COMPLETE.json` no HEAD mostra `{"manifest":"manifest.json","release":"RC01","status":"SEALED"}`; a promoção ocorreu hoje às 04:38 local (07:38 UTC), coerente com o registro de `P06-T14` em `state/task-history.yaml` (07:40:24Z).
- **A cópia-fonte `revit/lab/exports/p06t14/RC01/` está intacta e legível** (model.rvt, exports/, qa-reports/, plan-evidence/ com 20 arquivos). O dano é de acesso, não necessariamente de conteúdo.
- **Impacto:** o `git status` de qualquer sessão nova parece "sujo por deleção" e induz a dois erros opostos — commitar a deleção (quebra o selo do ensaio) ou tentar `git restore` (bloqueado pela ACL do `.git`, ver P-03).
- **Ação recomendada:** primeiro reparar a ACL em processo elevado (`takeown /f "<dir>" /r /d y` e `icacls "<dir>" /reset /T /C`), reabrir a listagem e só então reavaliar `git status`. Só restaurar do Git se os arquivos realmente não existirem mais. Enquanto isso, tratar esse ` D` como **pré-existente e não relacionado** a qualquer trabalho novo, e nunca incluí-lo em `git add`.

### P-02 — [ALTO, teste/fiabilidade] a suíte não é verde offline: `test_topologic_spike` depende de rede

- Comando: `.\.venv\Scripts\python.exe -m pytest -q` → **1 failed, 822 passed in 62,86 s**.
- Falha: `tests/unit/test_topologic_spike.py::test_topologic_spike_measures_space_and_persists_json_report`, `assert 1 == 0 where 1 = CompletedProcess(...).returncode`; o relatório persistido ficou `status: BLOCKED` com `error.type: TypeError`, `message: can only concatenate str (not "NoneType") to str`.
- **Causa raiz reproduzida com traceback** (executando `_build_geometry` + `_export_geometry` do spike com caminhos desviados para um diretório temporário):

```text
Helper.CheckVersion - Error: Could not fetch data from PyPI. Returning None.
  File "tool-lab/topologic/spike.py", line 164, in _export_geometry
    Topology.ExportToOBJ(
  File ".venv-topologic/Lib/site-packages/topologicpy/Topology.py", line 14461, in ExportToOBJ
    obj_string, mtl_string = Topology.OBJString(...)
  File ".venv-topologic/Lib/site-packages/topologicpy/Topology.py", line 17521, in OBJString
    "# topologicpy " + Helper.Version() + "\n",
TypeError: can only concatenate str (not "NoneType") to str
```

  Ou seja: a geometria é construída corretamente (12 vértices, 30 arestas, 20 faces, 24 m², 72 m³) e só a exportação OBJ quebra, porque `topologicpy.Helper.CheckVersion` busca `https://pypi.org/pypi/topologicpy/json` (timeout 10 s) e devolve `None` sem rede.
- É **pré-existente e conhecida**: já registrada em `docs/notes/2026-09-15-luna-plans-analysis-and-cleanup-handoff.md:21`, `2026-09-15-luna-v3-analysis-and-runner-integration-handoff.md:18` e `2026-09-15-luna-v7-e-compilador-handoff.md:79-80`. A afirmação "822 testes passando" do v16 vale apenas com rede disponível.
- **Efeito colateral:** o teste reescreve o arquivo rastreado `tool-lab/topologic/results/topologic-spike.json`. Nesta sessão o arquivo foi restaurado byte a byte a partir do HEAD e o `git diff` voltou a ficar vazio (mesma prática dos handoffs anteriores).
- **Ação recomendada:** manter o teste fora do caminho de release (ou marcar `slow`/`network`), e abrir correção própria: injetar a versão/atualizar `Helper._version`, stubar `Helper.CheckVersion`, ou exportar OBJ sem material — sempre em branch de manutenção, com regressão antes de promoção (AGENTS.md §"no mid-production dependency updates").

### P-03 — [ALTO, ambiente] `.git` tem `Deny Write` para o grupo do sandbox

- Sintoma histórico e recorrente: `fatal: Unable to create '.git/index.lock': Permission denied`, registrado em `docs/notes/2026-09-15-destravar-escrita-git-e-limpeza-handoff.md:21`, `2026-09-15-luna-v7-e-compilador-handoff.md:89-90`, `2026-09-16-analise-planos-luna-euler-handoff.md:45`.
- **Impacto:** dentro do sandbox, `git add/commit/push` falham; trabalho só entra no GitHub com escalação aprovada pelo dono (foi o caminho usado nesta sessão para publicar este relatório).
- **Ação recomendada:** manter a escalação como caminho oficial, ou corrigir a ACL do `.git` num processo elevado e registrar a decisão. Não contornar com `git --work-tree`/`GIT_DIR` alternativos.

### P-04 — [MÉDIO, estado] documentos de estado divergentes entre si

| Documento | O que diz | Conflito medido |
| --- | --- | --- |
| `PROJECT_STATE.yaml` | `phase_id: PHASE_06`, `phase_status: PENDING`, `next_task: P08-T08`, `last_completed_task: P06-T14`, `last_verified_commit: null`, `phase_gate: GO_WITH_LIMITATIONS` | `PHASE_06` está 15/15 PASS no grafo; a fase "aberta" real é PHASE_08 |
| `RESUME_AFTER_REBOOT.md` | `Phase: PHASE_02`, `Last PASS task: P09-T10`, `Next task: P06-T01`, checkpoint `T18_LAST_PASS.rvt` | incompatível com o grafo (P08-T08, P06-T14). O arquivo é uma preparação antiga de P07-T09; o checkpoint citado existe (`revit/lab/custom-api/T18_LAST_PASS.rvt`, 4.370.432 B, 15/09 15:35) |
| `state/status.md` | painel regenerado hoje (Observed HEAD `1e10f7c`) | é o documento mais fiel ao vivo; use-o como dashboard |
| `docs/notes/2026-09-16-o-que-falta-simples-v16.md` | análise mais recente do "o que falta" | correto no essencial; superestima a suíte (ver P-02) e não menciona P-01 |

- **Ação recomendada:** antes de executar, reconciliar `PROJECT_STATE.yaml`/`RESUME_AFTER_REBOOT.md` com o grafo (comando `status` regenera o painel; `advance-phase`/`phase-gate` fecham fase com evidência) e deixar explícito que `last_verified_commit` nulo é lacuna de verificação, não falha de Git.

### P-05 — [ALTO, ambiente] sem Revit vivo e com processos MCP órfãos

- `Get-Process Revit*` retorna apenas `RevitAccelerator` (Id 19132, 09:36). **Não há `Revit.exe`.**
- Permanecem seis processos órfãos de sessões anteriores: `horizun-mcp` (26152/09:40, 28524/09:40, 28284/10:57) e `RevitCortex.Server` (23004/09:40, 28388/09:40, 16784/10:57). São servidores MCP sem Revit para atender — ocupam portas/pipes e não valem como "provider HEALTHY" para escrita.
- `C:\Users\slvma\.horizun\discovery` está **vazio**: `Test-Path ...\revit-2027-30736.json` = `False`. Era exatamente esse arquivo que bloqueava a rota stdio do projeto por ACL (`docs/notes/2026-09-15-revit-vivo-escrita-bloqueada-handoff.md:18`, `2026-09-16-analise-planos-luna-euler-handoff.md:32`).
- **Ação recomendada:** antes de qualquer escrita, o dono abre o Revit 2027 com um RVT descartável em `revit/lab/`; então revalidar `horizun_health`/`read_model`, e só depois adquirir o lease. Processos órfãos devem ser encerrados (ou reaproveitados conscientemente) com registro no handoff.

### P-06 — [ALTO, contrato] crosswalk com dois buracos e registry sem escopo de produção

- `state/providers/semantic-crosswalk.yaml:24-28`: `revit.create_grid` → `route: horizun_create_elements`, `registered_entry: null`, `gap: no registered entry for grids; the route is proven but unregistered`.
- `state/providers/semantic-crosswalk.yaml:41-45`: `revit.create_roof` → idem para roofs.
- `state/capabilities.yaml`: 11 entradas `PASS`, todas `evidence_scope: PROVIDER`; `0` em `PRODUCTION` (confirmado também pelo preflight `P08-T01`).
- **Impacto:** grades e telhados são necessários em R03/R04 e no fechamento da documentação; sem entrada registrada, o compilador não tem rota aprovada e a escrita deve falhar fechada.
- **Ação recomendada:** provar `grid` ao vivo via `horizun_create_elements` com WRITE→READ→VERIFY, gravar evidência com sha256 e só então preencher `registered_entry`; o mesmo para `roof`. É pré-requisito de `P08-T08`/R04.

### P-07 — [ALTO, lacuna de código] não existe driver de candidato conceitual (bloqueia P08-T08)

- `src/amanda_agent/commands/bim.py:208-216`: `if mode != "SYNTHETIC_LAB": _fail(...)` e `SYNTHETIC_LAB requires --fixture`; `src/amanda_agent/bim/plan.py:337-339` reforça `SYNTHETIC_LAB is restricted to a fixture target; execution refused`.
- `scripts/` contém apenas `bim_lab_drill.py`, `bim_release_drill.py`, `cleanup-local.ps1`, `verify_ingested_sources.py`. **Não existe `scripts/bim_concept_candidates.py`** nem equivalente.
- O plano `08` Task 8 fala em "top 3", mas o run congelado publicou **2** finalistas.
- **Ação recomendada:** escrever primeiro o teste RED (`tests/unit/test_bim_concept_candidates.py`) e depois o driver, mantendo `CONCEPT_ONLY`, lease único, recusa de R05–R16 e save/close/reopen por candidato.

### P-08 — [MÉDIO, decisão] o score do design engine não discrimina os dois finalistas

- `solutions/finalists/comparison.md`: `weighted_total` **idêntico** (`0.8415491821831452`) para F01 e F02, apesar de `gross_footprint_m2` `779,2601` vs `1269,3525` m² (diferença de 490,09 m²) e `net_to_gross_factor` `0,8033` vs `0,4932`.
- Causas determinadas no código: `refinement.py` não coloca `gross_footprint_m2`/`wall_area_m2`/`net_to_gross_factor` em `raw_metrics`; `constructability` é atribuído literalmente `1.0`; `circulation` conta só rotas `ok`; `adjacency`/privacy empatam porque as distâncias publicadas são iguais; `solar_heuristic` e `ventilation_heuristic` estão `NOT_EVALUATED` (pesos 0,12 redistribuídos).
- `validation.json` dá `PASS` com `hard_violations: []`, mas `gross_area_budget` está `NOT_EVALUATED` — o PASS não valida a faixa 783–814 m² do programa.
- Leitura documental independente: F01 fica **3,74 m² abaixo do piso**; F02 **estoura o teto em 455,35 m²**. A recomendação `DRAFT/PENDING` aponta F01, e não foi registrada em `state/`.
- **Ação recomendada:** não tratar o empate numérico como desempate técnico; registrar a escolha delegada com `approval_hash` e justificativa documental, e considerar (fora do escopo imediato) corrigir o scoring para incluir envelope/parede.

### P-09 — [MÉDIO, ambiente] ACLs quebradas fora do repositório (B-001) e lixo de scratch

- `docs/notes/2026-09-15-fase-01-fundacao-handoff.md:131-135`: ACLs quebradas em `C:\Users\slvma\AppData\Local\Temp\pytest-of-slvma` e `.pytest_cache`; reparo exige PowerShell elevado: `icacls "<path>" /reset /T /C`.
- `tests/unit/test_circuit_breaker` foi registrado como flaky por ACL (`2026-09-15-fase-02-04-execucao-handoff.md:124`); regra vigente: `--basetemp` sempre único.
- Lixo local tolerado (todos ignorados pelo Git): `.tmp-pytest-relatorio` (**2.272** entradas, com RVTs de teste), `.tmp-pytest-sessionstart` (123), `.tmp-aclprobe.py`, `.tmp-survey.py`.
- **Ação recomendada:** rodar `scripts/cleanup-local.ps1` apenas após confirmar que nenhum processo está com arquivos abertos, e preservar `.venv`, `.venv-topologic` (376 MB, exigido por `tests/unit/test_topologic_spike.py`), `.venv-environmental` (451 MB, exigido por `tool-lab/environmental`) e `.dotnet`.

### P-10 — [MÉDIO, configuração] `.codex/config.toml` não rastreado pede sandbox total

- Arquivo untracked na raiz: `sandbox_mode = "danger-full-access"`, `approval_policy = "on-request"`, `approvals_reviewer = "auto_review"`, `model_verbosity = "low"`.
- A sessão atual **não** operou nesse modo (`workspace-write`), portanto o efeito é apenas potencial. Ainda assim, é a configuração mais permissiva possível convivendo com `AGENTS.md` fail-closed.
- **Ação recomendada:** decidir explicitamente entre versionar (e justificar) esse arquivo, mantê-lo ignorado por política, ou remover. Não deixar a decisão implícita.

### P-11 — [BAIXO, riscos de continuidade documental]

- `docs/notes/` tem **63** arquivos, incluindo 19 variações de "o que falta" (v3…v16, Artemis, Arya, Daenerys, checklist v6) e `docs/review/` guarda três snapshots dos mesmos quatro markdown canônicos (`originals-2026-09-15`, `before-program-baseline`, `before-delegated-decisions`). A raiz ainda tem dois ZIPs (planos revisados e superpowers plan).
- Risco concreto: um agente novo abre a v3/v5/v10 e age sobre estado velho.
- **Ação recomendada:** declarar em `START_HERE_FOR_CODEX.md` a trilha canônica (`state/status.md` → `PROJECT_STATE.yaml` → `RESUME_AFTER_REBOOT.md` → v16 → último handoff) e marcar os demais como históricos.
- Observação menor: `.gitignore` trava `*.rvt`; há 18 RVTs de laboratório em `revit/lab/` (14 em `horizun/`, 4 em `custom-api/`) e mais de uma centena de RVTs descartáveis criados por testes em `.tmp-pytest-*`. Se algum RVT precisar ser versionado (P08-T19), a política de LFS terá de ser aprovada antes — hoje não é.

### P-12 — [BAIXO, dívida técnica] scripts de laboratório são dependentes de um único provedor e de uma máquina

- `scripts/bim_release_drill.py`/`bim_lab_drill.py` codificam o ensaio sintético (fixture de 53 bytes, `simulated=True`). Eles **não** são evidência de produção; qualquer leitura apressada de `GOLDEN/RC01/RELEASE_COMPLETE.json` como "GOLDEN real" é um erro de interpretação.
- `P08-T01` também mostrou que não há fallback completo por capability: Horizun cobre a cadeia inteira; RevitCortex não tem ciclo de documento; custom-api cobre poucas operações. Manter fail-closed.

---

## 7. Travas e proibições para o próximo agente

1. **Não commite a deleção de `GOLDEN/RC01`** (` D` no `git status`) e não tente `git restore` antes de reparar a ACL. Isso é P-01.
2. Não escreva em `GOLDEN`, `baseline`, `MASTER`, `source` nem nos originais em `docs/source/` e nos PDFs da raiz.
3. Um escritor por vez: adquira `state/locks/revit-writer.lock` (hoje ausente = livre) antes de qualquer escrita; cada escrita é `WRITE → READ → VERIFY`; sucesso reportado pela ferramenta não é prova de mutação.
4. P08-T17 e P08-T18 não podem ser declarados PASS sem IFC/PDF/DWG reais do modelo de produção, com hashes e previews não vazios.
5. Não promova capability de `PROVIDER` para `PRODUCTION` sem medição própria; não use provedor `UNTESTED` na produção.
6. Não instale/atualize provider, SDK ou dependência durante produção; mudanças assim exigem branch de manutenção + regressão.
7. Não invente dados ausentes (topografia, polígono, norte, ocupação). Sem evidência, o estado é `PROVISIONAL_ASSUMPTION`/`NAO_ENCONTRADO`.
8. Não declare `TFG_COMPLETE` com entregas acadêmicas pendentes; a revisão da Amanda é `AMANDA_REVIEW_PENDING` e não é aprovação pessoal.
9. `amanda_agent doctor` e `amanda_agent status` **reescrevem arquivos rastreados** (`state/environment-report.json`, `state/status.md`). Rode-os conscientemente e commite junto, ou use leitura direta dos arquivos.
10. APS/cloud pago segue `NO-GO`; Blender segue adiado até existir necessidade real.

---

## 8. Roteiro recomendado (ordem sugerida)

1. **Saneamento de ambiente (dono):** reparar ACL de `revit/lab/exports/p06t14/GOLDEN/RC01` (`takeown` + `icacls /reset /T /C`) e conferir `git status`; encerrar os processos MCP órfãos; confirmar o estado do `.git` (P-03).
2. **Reconciliação de estado:** abrir sessão nova lendo `AGENTS.md`, `PROJECT_STATE.yaml`, `state/status.md`, v16 e este relatório; regenerar `status`/`task-graph`; registrar em handoff as divergências de P-04 resolvidas ou mantidas.
3. **Fechar o crosswalk:** provar `revit.create_grid` e `revit.create_roof` ao vivo com WRITE→READ→VERIFY + sha256 em RVT descartável; preencher `registered_entry` com evidência (P-06).
4. **Fechar a dívida de teste:** decidir e executar a correção de `test_topologic_spike` (marcar como opcional/rede ou corrigir a exportação) e registrar o resultado da suíte com e sem rede (P-02).
5. **P08-T08:** abrir o Revit 2027 com RVT descartável, obter lease, escrever o teste RED do driver de candidatos, criar `scripts/bim_concept_candidates.py`, gerar massing `CONCEPT_ONLY` R01→R04 de F01 e F02 com prévia 3D e save/close/reopen por candidato.
6. **P08-T09:** finalizar `solutions/finalists/comparison.md` (de `DRAFT/PENDING` para decisão registrada), gravar `APPROVED_FOR_BIM` com `approval_hash` e `amanda_review=AMANDA_REVIEW_PENDING` no decision-register.
7. **P08-T10→T14:** RVT de produção e compilação R01→R13 com checkpoint por estágio, reconciliação de áreas após R08 e stop-condition para sala requerida ausente.
8. **P08-T15→T17:** QA R14, RC R15 com reabertura a frio real, exports IFC/PDF/DWG/PNG, tabelas, hashes.
9. **P08-T19→T18:** preparar o pacote em staging, validar hashes, então publicar `bim/releases/GOLDEN-001/` sem sobrescrita e marcar imutável; decidir a política do RVT binário.
10. **P07-T17/P07-T19:** com o bloco acima fechado e evidência persistida, encerrar a sessão e executar os dois drills em sessão/inicialização realmente novas.
11. **Pendências humanas:** P02-T17 (4 casos com Revit), P08-T01 (capabilities de produção), dados do lote, itens acadêmicos.

---

## 9. Comandos de verificação (início de sessão)

```powershell
$env:PYTHONIOENCODING='utf-8'
cd 'C:\Users\slvma\Downloads\Github\Projeto Amanda'

# Git e estado (leitura)
git status --short --branch
git log --oneline -5
Get-Content -Raw PROJECT_STATE.yaml
Get-Content -Raw state\status.md

# Grafo e painel (doctor/status reescrevem arquivos rastreados — use com intenção)
.\.venv\Scripts\python.exe -m amanda_agent task-graph
.\.venv\Scripts\python.exe -m amanda_agent resume

# Suíte (offline: 1 falha conhecida em test_topologic_spike; aponte basetemp único)
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.tmp-pytest-<sufixo-unico>

# Proveniência das fontes
.\.venv\Scripts\python.exe scripts/verify_ingested_sources.py .

# Provedor vivo (somente com Revit aberto e confirmado na tela)
#   horizun_health → read_model → escrita descartável com WRITE → READ → VERIFY
```

---

## 10. Limites desta análise

- Não houve nenhuma interação com o Revit nem com os provedores MCP: as conclusões sobre provider são leitura de `state/tool-health.yaml`, `state/capabilities.yaml`, `state/bim-environment.lock.yaml` e da lista de processos.
- Não executei `doctor`, `status`, `advance`, `phase-gate` nem qualquer comando que reescreva estado — para não alterar `state/*` durante a análise.
- A falha de suíte foi reproduzida e diagnosticada, mas **não corrigida** (fora do escopo desta análise).
- Não abri os RVTs locais, os IFC/PDF/DWG do ensaio nem os PNGs dos finalistas; avaliei o que os manifestos, hashes e relatórios registram.
- Não auditei conteúdo de `TFG_Amanda_2026/` e `docs/source/` além dos hashes/tamanhos registrados na proveniência.
- Este relatório não substitui o handoff de retomada: ver `docs/notes/2026-09-16-relatorio-completo-handoff.md`.

---

## 11. Anexo — números e arquivos-chave

| Item | Valor medido |
| --- | --- |
| HEAD | `1e10f7c0008cc630006b56849104666673379cbe` (main = origin/main) |
| Grafo | 159 tarefas: 136 PASS, 3 PASS_WITH_WARNINGS, 12 PENDING, 8 SUSPENDED, 0 FAIL |
| Tarefa pronta | `P08-T08` |
| `state_revision` | 155 |
| Suíte | 823 testes coletados; 822 passed + 1 failed offline |
| Código | 287 arquivos em `src/amanda_agent`; 294 arquivos em `tests` |
| Capabilities | 11 PASS; 11 `PROVIDER`; 0 `PRODUCTION` |
| Bloqueadores | 3 BLOCKING + 2 DEGRADING (site) |
| Provider preferido | `horizun` (commit `cc4ea04`, server 1.3.3, `full_write`) |
| Build Revit | `27.2.0.39` / `20260716_1515(x64)` |
| SDK pinado do provider | requerido 10.0.400 — ausente (só 8.0.422) |
| Fontes | 23 documentos, `source-set-v1`, 23 `MATCH` |
| Finalistas | F01 (`approval_hash 67e502d8…`), F02 (`bc34cdbe…`), empate em `0.8415491821831452` |
| Tamanho do repositório | ~3,13 GB em disco (inclui `.venv` 441,9 MB, `.venv-topologic` 376 MB, `.venv-environmental` 451 MB, `.dotnet` 769,9 MB, `vendor` 354,4 MB — todos ignorados pelo Git) |

Arquivos que o próximo agente deve ler primeiro: `AGENTS.md`, `PROJECT_STATE.yaml`, `state/status.md`, `state/task-graph.yaml`, `docs/superpowers/plans/08-amanda-production-run.md`, `state/providers/semantic-crosswalk.yaml`, `state/capabilities.yaml`, `solutions/finalists/comparison.md`, `docs/notes/2026-09-16-o-que-falta-simples-v16.md`, `docs/notes/2026-09-16-handoff-geral-estado-e-o-que-falta.md`.

