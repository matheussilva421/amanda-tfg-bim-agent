SUPERSEDED por 2026-09-15-o-que-falta-simples-v5.md
# O que falta para terminar — V4

Data: 2026-09-15. Auditoria documental somente leitura.

## Onde estamos

O grafo tem 159 tarefas: 136 `PASS`, 2 `PASS_WITH_WARNINGS`, 13 `PENDING` e 8 `SUSPENDED` (contagem dos registros de `state/task-graph.yaml`; `state/status.md:7-11`). A fase atual é `PHASE_06`, a próxima tarefa é `P06-T14`, e `P08-T07` foi o último PASS (`PROJECT_STATE.yaml:3-9`; `state/status.md:7-10`). O projeto ainda está em revisão/estudo: não há projeto selecionado, estágio Revit ou checkpoint registrados (`START_HERE_FOR_CODEX.md:3-5`; `PROJECT_STATE.yaml:2,7-13`).

## O que falta, em ordem

- `P06-T14` — `PENDING`: fazer o ensaio sintético R14→R16 com QA, fechar/reabrir o Revit, exports, hashes e rejeição de sobrescrita. Para fechar, registrar todas essas evidências no release de laboratório; exige AÇÃO HUMANA para disponibilizar a sessão Revit/MCP (`state/task-graph.yaml:1975-1983`; plano 06 Task 14, `docs/superpowers/plans/06-qa-release-exports.md:253-269`).
- `P02-T17` — `PASS_WITH_WARNINGS`: repetir quatro falhas em RVT descartável com chamada real e reconsulta independente. Para fechar, provar FI-001, FI-002, FI-003 e FI-006 no Revit; exige AÇÃO HUMANA para tornar o Revit/MCP alcançável (`state/task-graph.yaml:791-808`; plano 02 Task 17, `docs/superpowers/plans/02-revit-tool-lab-providers.md:516-529`).
- `P07-T17` — `SUSPENDED`: provar a retomada em uma sessão Codex realmente nova. Para fechar, abrir a nova sessão, ler o estado e registrar PASS/FAIL; exige AÇÃO HUMANA (`state/task-graph.yaml:2212-2220`; plano 07 Task 17, `docs/superpowers/plans/07-autonomy-recovery-security.md:348-358`).
- `P07-T19` — `SUSPENDED`: provar a retomada depois de reinício. Para fechar, fazer reboot autorizado e executar a sequência pós-reboot; exige AÇÃO HUMANA: reboot real (`state/task-graph.yaml:2260-2268`; plano 07 Task 19, `docs/superpowers/plans/07-autonomy-recovery-security.md:372-383`).
- `P08-T01` — `PASS_WITH_WARNINGS`: o preflight ainda é `PRODUCTION NO-GO`, sem evidência runtime em escopo de produção. Para fechar, repetir o preflight com evidência de cada capability e Git limpo; pode exigir AÇÃO HUMANA para login/licença/diálogo do Revit (`state/task-graph.yaml:2280-2300`; plano 08 Task 1, `docs/superpowers/plans/08-amanda-production-run.md:28-49`).
- `P08-T08` — `PENDING`: criar e verificar massas conceituais Revit para até três finalistas. Para fechar, salvar/fechar/reabrir cada RVT conceitual e liberar o writer lease; exige AÇÃO HUMANA para a sessão Revit (`state/task-graph.yaml:2403-2410`; plano 08 Task 8, `docs/superpowers/plans/08-amanda-production-run.md:136-147`).
- `P08-T09` — `PENDING`: comparar as opções e registrar uma escolha única com `approval_hash`. Para fechar, gravar a seleção delegada e deixar a revisão da Amanda como `AMANDA_REVIEW_PENDING`; exige AÇÃO HUMANA depois para a revisão arquitetônica (`state/task-graph.yaml:2412-2420`; plano 08 Task 9, `docs/superpowers/plans/08-amanda-production-run.md:149-167`).
- `P08-T10`, `P08-T11`, `P08-T12`, `P08-T13`, `P08-T14` — `PENDING`: criar o RVT de produção e compilar R01–R13, incluindo documentação. Para fechar, executar cada estágio com WRITE→READ→VERIFY, checkpoint e previews; exige AÇÃO HUMANA quando houver login, licença ou diálogo Revit (`state/task-graph.yaml:2421-2465`; plano 08 Tasks 10-14, `docs/superpowers/plans/08-amanda-production-run.md:170-231`).
- `P08-T15`, `P08-T16`, `P08-T17`, `P08-T18`, `P08-T19` — `PENDING`: fazer QA, RC a frio, exports, relatórios, proveniência e publicar o `GOLDEN-001` (T19 prepara antes de T18). Para fechar, provar QA/persistência/exports, revisão visual e pacote sem sobrescrita; exige AÇÃO HUMANA para fechar/reabrir o Revit e para a revisão acadêmica/visual da Amanda (`state/task-graph.yaml:2466-2510`; plano 08 Tasks 15-19, `docs/superpowers/plans/08-amanda-production-run.md:233-315`).
- `P09-T03`, `P09-T04`, `P09-T05` — `SUSPENDED`: registrar Blender, testar o Tool Lab e montar render. Para fechar, primeiro reabrir a necessidade de render e depois concluir a cadeia; é opcional e não trava a rota local (`state/task-graph.yaml:2549-2590`; plano 09 Tasks 3-5, `docs/superpowers/plans/09-optional-render-cloud.md:58-110`).
- `P09-T07`, `P09-T08`, `P09-T09` — `SUSPENDED`: auditar, proteger segredos e testar APS em sandbox. Para fechar, existir capability local concretamente bloqueada e autorização própria; é opcional e continua suspenso pelo `NO-GO` do APS (`state/task-graph.yaml:2622-2660`; plano 09 Tasks 7-9, `docs/superpowers/plans/09-optional-render-cloud.md:111-157`).

## O que está travado e por quê

- O terreno ainda não tem topografia/datum, polígono cadastral, uso/realocação confirmados, número de frentes nem norte verdadeiro; o estudo permanece `PLANAR_PLACEHOLDER` (`state/blockers.yaml:3-120`; `project/site/site.json:58,66,105-107`).
- Nesta auditoria, Revit/MCP fica tratado como inalcançável: há registro de que o Revit não estava em execução e de que não houve chamada real no bridge (`docs/notes/2026-09-15-limpeza-local-e-retomada-revit.md:58-74`; `docs/notes/2026-09-15-bim-runner-bridge-handoff.md:33-40`).
- O DWG tem somente validação limitada em STUDY: não há parser local aprovado; a checagem é assinatura/tamanho e `LIMITED_DWG_VALIDATION` (`state/task-graph.yaml:1898-1912`; plano 06 Task 9 e gate, `docs/superpowers/plans/06-qa-release-exports.md:152-160,288-291`).

## O que não falta

O journal durável e os comandos `bim claim`/`record-result` existem em `src/amanda_agent/bim/journal.py:99-318` e `src/amanda_agent/commands/bim.py:105-151`. O relatório `tool-lab/reports/bim-compiler-e2e.md:1-38` também existe, mas é `PASS_FIXTURE` e não prova Revit físico. P08-T06 e P08-T07 já estão `PASS`, com evidência registrada no histórico (`state/task-history.yaml:1970-1985`); portanto as notas que os tratavam como pendentes estão desatualizadas.

## Divergências conhecidas

`PROJECT_STATE.yaml` diz `blockers: []`, enquanto `state/blockers.yaml` mantém cinco bloqueadores (`PROJECT_STATE.yaml:1`; `state/blockers.yaml:2-120`). `state/status.md` diz `PHASE_08: 7/19 PASS`, mas o grafo atual tem 6 PASS, 1 warning e 12 PENDING nessa fase (`state/status.md:21`; `state/task-graph.yaml:2280-2510`). O painel também diz provider saudável, mas isso não supera o registro de Revit parado nem prova escrita (`state/status.md:29-34`; `docs/notes/2026-09-15-limpeza-local-e-retomada-revit.md:60-74`).

## Próximo passo

A única ação humana que mais destrava agora é iniciar/autorizar uma sessão Revit 2027 com login/licença/segurança resolvidos e MCP alcançável, mantendo o writer lease livre; então executar `P06-T14` no laboratório (`PROJECT_STATE.yaml:5`; plano 06 Task 14, `docs/superpowers/plans/06-qa-release-exports.md:253-269`). Nenhuma escrita física no Revit foi provada (`START_HERE_FOR_CODEX.md:3-5`; `tool-lab/reports/bim-compiler-e2e.md:5-7,36-38`).
