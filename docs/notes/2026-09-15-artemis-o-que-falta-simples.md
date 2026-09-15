# O que falta — análise Artemis

## Onde o projeto está hoje

O projeto já tem a base de código, o grafo com 159 tarefas, o programa adotado de 20 pessoas, o estudo `AMANDA-RUN-001` com duas finalistas e vários arquivos de laboratório Revit. O grafo conta 134 `PASS`, 2 `PASS_WITH_WARNINGS`, 15 `PENDING` e 8 `SUSPENDED`. `PROJECT_STATE.yaml` aponta `PHASE_02`, próxima tarefa `P06-T14`, gate `GO_WITH_LIMITATIONS`, sem projeto selecionado e sem checkpoint. O Revit 2027 foi detectado, o provider Horizun e seus adaptadores existem, e a sondagem ao Revit está salva; suas rotas novas continuam marcadas `UNPROVEN`, portanto ainda não provam uma escrita de produção.

## O que falta, por fase

- **00 — pronta documentalmente.** As 3 tarefas estão `PASS`; falta executar o restante do programa, pelo agente principal.
- **01 — pronta.** As 13 tarefas estão `PASS`; não há tarefa aberta nesta fase, e o agente usa essa base para continuar.
- **02 — em andamento com ressalva.** 20/20 estão concluídas, mas `P02-T17` é `PASS_WITH_WARNINGS`: quatro falhas ainda precisam de chamada real no Revit e reconsulta independente. Destrava uma sessão Revit controlada.
- **03 — pronta para estudo, limitada.** 15/15 estão `PASS`; faltam topografia, polígono cadastral e regras verificadas para fechar a entrega final. Amanda fornece os dados; o agente verifica as regras.
- **04 — pronta para estudo.** 22/22 estão `PASS`; falta usar uma alternativa no fluxo Revit, porque o motor sozinho não cria o modelo final. O agente destrava essa etapa.
- **05 — pronta só no laboratório.** 23/23 estão `PASS` em compilação sintética; falta ligar e provar o fluxo completo no Revit de produção. O agente faz isso em sessão Revit controlada.
- **06 — em andamento.** `P06-T14` está `PENDING` e `READY`; falta concluir o ensaio sintético R14→R16 com QA, reabertura fria e exports. O agente e o Revit de laboratório destravam.
- **07 — parcial.** 07A está 11/11 `PASS`; `P07-T17` e `P07-T19` estão `SUSPENDED` porque exigem uma sessão nova real e um reboot real. O dono destrava essas provas.
- **08 — em andamento.** `P08-T01` tem ressalvas e `P08-T05` está `PASS`. `P08-T06` já foi executada: existem o resumo e as duas pastas de finalistas, além do teste dedicado; o grafo ainda mostra `PENDING`, faltando registrar o `PASS`. `P08-T07` até `P08-T19` aguardam a sequência ambiental, seleção, Revit, QA e release.
- **09 — suspensa e opcional.** Blender/render está adiado; APS ficou `NO-GO` e suspenso por decisão do dono. Amanda só reabre essa fase se mudar essa decisão; ela não trava a rota local.

## O que falta de verdade para a entrega final

Os caminhos abaixo foram conferidos com `Test-Path` e `Get-ChildItem`:

- `revit/production/working/AMANDA_WORKING_001.rvt` — ausente (`False`). Os 21 RVTs encontrados ficam em `revit/lab/`.
- `bim/releases/GOLDEN-001/` — ausente (`False`). Portanto também não existem o RVT/IFC final, `PDF/`, `DWG/`, `preview/`, `manifest.json`, `provenance.json` e os relatórios esperados nesse pacote.
- `deliverables/` — ausente (`False`). Não há pranchas finais, cortes, elevações, tabelas ou conjunto de vistas R13 de produção.
- `tool-lab/horizun/exports/` contém IFC, PDF, DWG, CSV e PNG de laboratório; esses arquivos não são a entrega Amanda GOLDEN.
- `docs/reports/QA_REPORT_RC01.md`, `RUN_SUMMARY.md` e `AUTONOMY_REPORT.md` — ausentes (`False`).
- `project/requirements/academic-deliverables.yaml` existe, mas seus 11 itens ainda estão 10 `PENDING` e 1 `PROVISIONAL`; não há base para declarar `TFG_COMPLETE`.

## O que depende de você (Amanda)

- Fornecer ou confirmar topografia com datum, polígono cadastral, uso atual do lote, realocação da unidade, número de frentes e norte verdadeiro. O agente não pode inventar levantamento nem atestar situação do terreno.
- Fazer visitas e levantamento de campo, revisar a arquitetura e validar caderno, estudos, anteprojeto, memoriais, pranchas, autoria, defesa e submissão. São atos acadêmicos e de autoria humana.
- Participar da sessão humana do Revit para login/licença, diálogos e autorização de escrita. Arquivo instalado não prova licença nem aceitação operacional.

## O que o agente ainda pode fazer sozinho agora

- Registrar o `PASS` real de `P08-T06` no grafo, usando `refinement-summary.json`, as duas pastas de finalistas e `tests/unit/test_design_refine.py` como evidências.
- Executar `P06-T14` no laboratório e, depois, executar `P08-T07` com as duas finalistas.
- Fazer o dry-run de `scripts/cleanup-local.ps1`, revisar o plano de remoção e limpar apenas após a janela autorizada.
- Preparar o bridge compilador→Horizun, atualizar o estado/handoff e commitar o bloco revisado.

## Próximos 3 passos

1. Registrar `P08-T06` em `state/task-graph.yaml` pelo comando `python -m amanda_agent advance`, com as evidências já existentes.
2. Executar `P06-T14` conforme `docs/superpowers/plans/06-qa-release-exports.md`; a saída esperada é um release sintético de laboratório com QA, persistência e exports comprovados.
3. Rodar `P08-T07` e, com Amanda, resolver os dados do lote e a sessão Revit; então seguir `P08-T08`–`P08-T19` até `bim/releases/GOLDEN-001/`.

## Cuidados

APS é pago e está suspenso por decisão do dono. APS, Blender e render continuam suspensos; não são dependências da rota local. O Revit deve ter um único escritor, e toda escrita deve seguir `WRITE → READ → VERIFY`, com checkpoint antes de ações destrutivas.

Data da análise: 2026-09-15. Li `AGENTS.md`, `START_HERE_FOR_CODEX.md`, `PLAN_SELF_REVIEW.md`, `PROJECT_STATE.yaml`, `state/status.md`, `state/task-graph.yaml`, a análise anterior, o handoff da revisão, os 10 planos, os artefatos novos de P08-T06, os adaptadores/sondagem Horizun, os relatórios de retomada e o script de limpeza. Não rodei pytest nem MCP do Revit. Não fiz commit nem push.

Arquivos lidos: `AGENTS.md`; `START_HERE_FOR_CODEX.md`; `PLAN_SELF_REVIEW.md`; `PROJECT_STATE.yaml`; `state/status.md`; `state/task-graph.yaml`; `docs/notes/2026-09-15-revisao-planos-handoff.md`; `docs/notes/2026-09-15-daenerys-analise-do-que-falta.md`; `docs/superpowers/plans/00-master-implementation-plan.md` a `09-optional-render-cloud.md`; `design-engine/runs/AMANDA-RUN-001/refinement-summary.json`; `design-engine/runs/AMANDA-RUN-001/finalists/AMANDA-RUN-001-F01/`; `design-engine/runs/AMANDA-RUN-001/finalists/AMANDA-RUN-001-F02/`; `tests/unit/test_design_refine.py`; `src/amanda_agent/bim/providers/horizun.py`; `src/amanda_agent/bim/providers/transport.py`; `tests/unit/test_bim_horizun_invoker.py`; `tool-lab/horizun/results/probe-routes-2026-09-15.json`; `docs/notes/2026-09-15-p08-provider-routes.md`; `docs/notes/2026-09-15-limpeza-local-e-retomada-revit.md`; `scripts/cleanup-local.ps1`; `project/requirements/academic-deliverables.yaml`; `project/requirements/decision-register.yaml`; `project/site/site.json`; `project/requirements/program.json`; `docs/reports/p08-preflight.md`; `docs/reports/p08-site-resolution.md`; `docs/reports/p09-optional-extensions.md`; `docs/reports/session-recovery-drill.md`; `docs/reports/reboot-resume-procedure.md`.

Arquivo escrito: `docs/notes/2026-09-15-artemis-o-que-falta-simples.md`.
