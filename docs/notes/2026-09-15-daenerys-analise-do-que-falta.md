# Análise do que falta — 15/09/2026

> SUPERSEDED 2026-09-15: retrato atual em `docs/notes/2026-09-15-o-que-falta-simples-v5.md`; esta análise fica como histórico.

## Onde estamos

`PROJECT_STATE.yaml` aponta `PHASE_02` (`revit-tool-lab-providers`), status `PENDING`, gate `GO_WITH_LIMITATIONS`, próxima tarefa `P06-T14` e última tarefa concluída `P08-T05`.
O grafo/CLI registra 159 tarefas: 134 `PASS`, 2 `PASS_WITH_WARNINGS`, 15 `PENDING` e 8 `SUSPENDED`. As duas tarefas prontas são `P06-T14` e `P08-T06`.
Já existem o estado/canonização do programa de 20 pessoas, a base de estudo congelada, o run `AMANDA-RUN-001` e duas candidatas de estudo (`F01` e `F02`). O run teve 144 tentativas, 2 candidatas válidas e 142 duplicadas; o ambiente ainda não foi avaliado.
Não há projeto selecionado, estágio Revit ou checkpoint atual registrados. `state/status.md` está uma revisão atrás sobre a contagem da fase 08; usei o grafo e o CLI como estado operacional mais recente.

## O que falta

As tarefas abaixo são todas as que não estão exatamente `PASS`, incluindo as duas concluídas apenas com ressalvas.

### PHASE_02 — laboratório Revit

- `P02-T17` — `PASS_WITH_WARNINGS`: completar quatro casos de falha com RVT descartável, chamada real e reconsulta independente. **Bloqueada** até existir sessão de escrita Revit.

### PHASE_06 — QA e release de laboratório

- `P06-T14` — `PENDING`: executar o ensaio sintético R14→R16, incluindo persistência a frio, QA, IFC/PDF/DWG, hashes, previews e GOLDEN de laboratório. **Não bloqueada; READY no CLI**, aguardando execução.

### PHASE_07B — recuperação

- `P07-T17` — `SUSPENDED`: provar retomada em uma nova sessão Codex. **Bloqueada** porque a sessão seguinte precisa ser realmente nova; a sessão atual não pode simular esse resultado.
- `P07-T19` — `SUSPENDED`: provar o procedimento de retomada após reinício. **Bloqueada** porque não houve reboot autorizado nem nova sessão; o `RESUME_AFTER_REBOOT.md` atual está deliberadamente desatualizado.

### PHASE_08 — produção Amanda

- `P08-T01` — `PASS_WITH_WARNINGS`: preflight executado, mas o veredito é `PRODUCTION NO-GO`; faltam evidências de runtime em escopo de produção e teste Revit marcado como tal.
- `P08-T06` — `PENDING`: refinar, pontuar e ordenar as candidatas. **Não bloqueada; READY no CLI**. Existe `refinement-summary.json`, mas o grafo ainda não mudou para `PASS`.
- `P08-T07` — `PENDING`: avaliar solar/ventilação das finalistas. **Bloqueada** pela dependência pendente `P08-T06`.
- `P08-T08` — `PENDING`: criar massas conceituais Revit para até três opções. **Bloqueada** por `P08-T07`.
- `P08-T09` — `PENDING`: comparar opções, escolher uma e registrar a decisão delegada com hash. **Bloqueada** por `P08-T08`.
- `P08-T10` — `PENDING`: criar o RVT de produção Amanda. **Bloqueada** por `P08-T09`.
- `P08-T11` — `PENDING`: compilar R01–R04, do início do projeto à massa. **Bloqueada** por `P08-T10`.
- `P08-T12` — `PENDING`: compilar R05–R08, incluindo ambientes e layout interno. **Bloqueada** por `P08-T11`.
- `P08-T13` — `PENDING`: compilar R09–R12, incluindo acessibilidade, mobiliário, paisagismo e materiais. **Bloqueada** por `P08-T12`.
- `P08-T14` — `PENDING`: criar documentação R13: plantas, cortes, elevações, tabelas, áreas, pranchas, cotas e previews. **Bloqueada** por `P08-T13`.
- `P08-T15` — `PENDING`: executar QA completo R14 e gerar o relatório de QA. **Bloqueada** por `P08-T14`.
- `P08-T16` — `PENDING`: criar RC R15, fechar, reiniciar o Revit e reabrir para conferir persistência. **Bloqueada** por `P08-T15`.
- `P08-T17` — `PENDING`: exportar e validar IFC, PDF, DWG, PNG, tabelas e hashes. **Bloqueada** por `P08-T16`.
- `P08-T19` — `PENDING`: preparar o pacote final, relatórios, proveniência e estado das entregas acadêmicas. **Bloqueada** por `P08-T17`.
- `P08-T18` — `PENDING`: promover o pacote R16 para GOLDEN imutável. **Bloqueada** por `P08-T19`, além de exigir QA, persistência e exports aprovados.

### PHASE_09 — extensões opcionais

- `P09-T03` — `SUSPENDED`: registrar Blender MCP. **Suspensa** porque a renderização foi adiada em `P09-T01`.
- `P09-T04` — `SUSPENDED`: executar Tool Lab Blender. **Suspensa** por `P09-T03` e pela decisão de não abrir a extensão sem necessidade de render.
- `P09-T05` — `SUSPENDED`: montar pipeline de renderização. **Suspensa** por `P09-T04`; só reabre com necessidade explícita e release BIM validado.
- `P09-T07` — `SUSPENDED`: auditar exemplos APS. **Suspensa** porque o gate APS `P09-T06` deu `NO-GO`: não há capacidade local comprovadamente bloqueada.
- `P09-T08` — `SUSPENDED`: criar a fronteira de segredos APS. **Suspensa** por `P09-T07` e pelo `NO-GO` do gate APS.
- `P09-T09` — `SUSPENDED`: testar deployment APS em sandbox. **Suspensa** por `P09-T08`; não houve sandbox, credencial ou teste cloud.

## O que falta de verdade para a entrega final

Verifiquei os caminhos com `Test-Path` e listei os arquivos com `Get-ChildItem`/`rg --files`.

- **RVT:** há 21 RVTs, todos em `revit/lab/`, para testes. `revit/production/working/AMANDA_WORKING_001.rvt` não existe; `bim/releases/GOLDEN-001` também não existe.
- **Plantas:** existem apenas plantas/zoning PNG e SVG das duas candidatas de **STUDY** em `design-engine/runs/AMANDA-RUN-001/finalists/`. Não são pranchas finais.
- **Cortes e elevações:** não encontrei arquivos de entrega com esses nomes nem um conjunto R13 de vistas Revit.
- **Pranchas:** não existe diretório `deliverables` nem arquivo separado de prancha. A quantidade de 4–6 A1 está apenas como expectativa provisória no cadastro acadêmico.
- **Tabelas:** existe `tool-lab/horizun/exports/LAB_HORIZUN_DOC_ambientes.csv`, mas é export de laboratório; as tabelas de portas/janelas/ambientes e o quadro final de áreas ainda dependem de R13/R17.
- **IFC/PDF/DWG:** existem `LAB_HORIZUN_DOC.ifc`, `.pdf` e `.dwg` em `tool-lab/horizun/exports`, e existe o IFC de fonte `07_modelo_BIM_HIPOTESE.ifc`. São fonte/estudo/lab; não são exports do modelo Amanda GOLDEN.
- **Relatórios:** existem relatórios de processo em `docs/reports/`, mas não existem `QA_REPORT_RC01.md`, `RUN_SUMMARY.md`, `AUTONOMY_REPORT.md` nem o pacote final com manifest, proveniência e reports.
- **Entregas acadêmicas:** `project/requirements/academic-deliverables.yaml` registra 11 itens: 10 `PENDING` e 1 `PROVISIONAL`; todos são obrigatórios para `TFG_COMPLETE` e todos requerem ação humana.

## Bloqueios que dependem de mim (Amanda)

- Fornecer ou validar levantamento/topografia com datum (`SITE_TOPOGRAPHY`), polígono cadastral/georreferenciado (`SITE_BOUNDARY`), uso atual do lote e premissa de realocação (`SITE_OCCUPANCY`), número de frentes (`SITE_FRONTAGE_COUNT`) e norte verdadeiro (`SITE_TRUE_NORTH`). Sem isso, o estudo planar pode continuar, mas ficam bloqueadas as verificações finais de área, implantação, acessibilidade altimétrica, orientação, regularização e disponibilidade do terreno.
- Realizar/atestar visitas e levantamento de campo, revisar o caderno, metaprojeto, estudo preliminar, anteprojeto, memoriais, pranchas, autoria, defesa e submissão institucional. O software não pode produzir ou atestar essas atividades.
- Revisar a arquitetura escolhida pelo agente quando ela for registrada. O contrato atual permite continuar com `AMANDA_REVIEW_PENDING`; essa revisão humana continua necessária para a entrega acadêmica.
- Participar da sessão humana do Revit quando os testes reais forem autorizados: iniciar o Revit 2027, responder eventual diálogo de segurança do add-in e confirmar que a licença/sessão permite escrita. A presença do executável detectado não prova licença nem aceitação operacional.
- APS/Forge e outras rotas pagas estão deliberadamente suspensas. O gate APS deu `NO-GO` e o proprietário não quer serviços pagos; não há login, credencial, upload ou custo a providenciar.

## Próximos 3 passos

1. Executar `P06-T14`, o ensaio sintético de release, para fechar a validação de QA, persistência e exports do pipeline.
2. Fechar `P08-T06` e `P08-T07`, documentar a baixa diversidade das duas finalistas e registrar a escolha arquitetônica delegada com `AMANDA_REVIEW_PENDING`.
3. Amanda fornecer os dados do lote e participar da sessão Revit; então executar `P08-T08`–`P08-T19` até obter QA, exports e o pacote R16 GOLDEN.

Git local: branch `main` acompanha `origin/main`, HEAD observado por `git rev-parse HEAD` `8f01572e47979b9d0f66e0f01039a3a99fc710ed`; a árvore já estava suja antes desta análise. Não fiz commit nem push.

Base consultada: `START_HERE_FOR_CODEX.md`, `PROJECT_STATE.yaml`, `state/task-graph.yaml`, `state/status.md`, os 10 planos em `docs/superpowers/plans/`, `PLAN_SELF_REVIEW.md`, `docs/notes/2026-09-15-revisao-planos-handoff.md`, CLI `status/task-graph/resume` e verificações do disco.
Validação desta análise: arquivo lido novamente em UTF-8 e 84 linhas; não executei pytest adicional porque a tarefa foi documental e somente leitura.
