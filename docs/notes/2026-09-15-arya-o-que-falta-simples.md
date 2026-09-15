# O que falta para concluir — ARYA

Data: 2026-09-15.

## Onde estamos

O grafo atual tem 159 tarefas: **134 PASS / 15 PENDING / 8 SUSPENDED**, além de 2 `PASS_WITH_WARNINGS` (`state/task-graph.yaml`, resumido em `state/status.md`).
O estudo já tem o programa escolhido de 20 pessoas e duas alternativas de projeto: `AMANDA-RUN-001-F01` e `AMANDA-RUN-001-F02`.
Ainda não existe o arquivo Revit de produção, o pacote `GOLDEN-001` nem o conjunto final de pranchas e relatórios.
O Horizun mudou de situação: a parede é prova real de criação e releitura (`ElementId 328666`, `LAB_ROUTE_PROBE`), e hoje as 18 rotas do adaptador estão provadas ao vivo — 17 numa varredura e o `revit.create_project` isolado. O resultado consolidado `tool-lab/horizun/results/probe-routes-2026-09-15-live10-13.json` registra 18 de 18 PROVEN e 0 UNPROVEN. As rotas continuam provadas em documento LAB; a prova repetida em documento de produção ainda não aconteceu.
O que existe hoje é **STUDY**; não há base para declarar **FINAL** ou `TFG_COMPLETE`.

## O que falta

1. **Formalizar o refinamento dos candidatos — P08-T06.** O resumo e as pastas dos dois finalistas já existem, mas o grafo ainda diz `PENDING`; falta registrar a evidência para liberar a próxima etapa. Quem destrava: agente.

2. **Fazer o ensaio completo de entrega no laboratório — P06-T14.** Falta executar QA, salvar uma versão de teste, fechar e reabrir o Revit, conferir IFC/PDF/DWG, gerar os relatórios e provar que o pacote não pode ser sobrescrito. Quem destrava: agente com Revit de laboratório.

3. **Completar a recuperação entre sessões — P07-T17 e P07-T19.** Falta uma nova sessão real para provar a retomada e um reboot autorizado para provar o retorno após reinicialização. Quem destrava: agente para a nova sessão; Amanda e o hardware para autorizar e realizar o reboot.

4. **Comparar o ambiente e escolher uma alternativa — P08-T07 a P08-T09.** Falta avaliar sol, ventilação e os demais critérios, criar as massas conceituais no Revit e registrar uma escolha única. Hoje a escolha ainda não está registrada como projeto ativo e a avaliação ambiental está `NOT_EVALUATED`. Quem destrava: agente e Revit; Amanda faz a revisão arquitetônica.

5. **Criar e preencher o Revit de produção — P08-T10 a P08-T14.** Falta criar `AMANDA_WORKING_001.rvt`, levar a alternativa escolhida pelas etapas R01–R13 e produzir plantas, cortes, fachadas, tabelas, cotas e vistas. As 18 rotas do adaptador Horizun já têm prova ao vivo em documento LAB; falta a reexecução sobre o documento de produção conforme cada uma for usada. Quem destrava: agente, Revit e hardware disponível.

6. **Testar, exportar e selar a entrega técnica — P08-T15 a P08-T19.** Falta QA completo, candidato R15 com reabertura a frio, exports, hashes, `manifest`, `provenance`, relatórios e publicação do `bim/releases/GOLDEN-001/`. Quem destrava: agente com Revit; Amanda revisa o resultado visual e arquitetônico.

7. **Resolver os dados reais do terreno — P08-T03 e verificações finais do site.** Ainda faltam topografia, polígono cadastral, uso atual e realocação da CPChoque, número de frentes e norte verdadeiro. O retângulo atual é apenas uma hipótese de estudo; sem esses dados, o resultado pode ser STUDY, mas não FINAL. Quem destrava: Amanda, levantamento/visita de campo e fonte cadastral; o agente registra e refaz as verificações.

8. **Concluir a parte acadêmica — P03-T15.** O registro contém 11 entregas: 10 `PENDING` e 1 `PROVISIONAL`. Faltam caderno, visitas, metaprojeto, estudo preliminar, anteprojeto, pranchas, memoriais, defesa, autoria e submissão institucional. Quem destrava: Amanda e a instituição; o software não pode fazer visitas, declarar autoria ou submeter o TFG.

## O que Amanda precisa fazer

- Confirmar terreno, topografia, polígono, uso atual, realocação, número de frentes e norte.
- Fazer ou providenciar as visitas e o levantamento de campo.
- Revisar a alternativa escolhida, implantação, fluxos, ambientes, pranchas e memoriais.
- Produzir ou validar as entregas acadêmicas, autoria, defesa e submissão.
- Participar da sessão humana do Revit quando houver login, licença, segurança ou diálogo que só ela possa resolver.

## O que está bloqueado por custo

- **APS/Forge — P09-T06 a P09-T09:** rota em nuvem, com conta/autorização e possível cobrança. O plano já registrou `NO-GO`; não entra.
- **Blender e render — P09-T03 a P09-T05:** são opcionais e estão suspensos. Blender local não é necessariamente pago, mas render não é necessário para a entrega atual e não entra.
- Não comprar serviço, plano premium, assinatura ou crédito. A entrega seguirá pela rota local Revit/Horizun e pelos recursos já disponíveis.

## Como destravar

1. Registrar no grafo o `PASS` de P08-T06 usando o resumo e os dois finalistas já existentes.
2. Executar P06-T14 no arquivo de laboratório e guardar o pacote de teste.
3. Abrir uma nova sessão para P07-T17 e fazer o reboot autorizado de P07-T19.
4. Executar P08-T07, P08-T08 e P08-T09; escolher uma alternativa de estudo e registrar a decisão.
5. Reexecutar a matriz do Horizun no documento de produção: as 18 rotas já foram provadas em LAB, mas cada uso real precisa da sua própria releitura independente.
6. Com um único escritor Revit, executar P08-T10 a P08-T14 em modo STUDY até os dados do terreno serem confirmados.
7. Amanda confirma o terreno e revisa a arquitetura; o agente refaz somente as verificações afetadas.
8. Executar P08-T15 a P08-T19 e publicar GOLDEN apenas se QA, reabertura, exports e relatórios passarem.
9. Amanda conclui as entregas acadêmicas e a submissão institucional.

## Arquivos consultados

`START_HERE_FOR_CODEX.md`; `PLAN_SELF_REVIEW.md`; `docs/notes/2026-09-15-revisao-planos-handoff.md`; `2026-09-11-amanda-tfg-bim-agent-design.md`; `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md`; `PROJECT_STATE.yaml`; `state/status.md`; `state/task-graph.yaml`; `state/task-history.yaml`; `docs/notes/2026-09-15-artemis-o-que-falta-simples.md`; `state/capabilities.yaml`; `docs/superpowers/plans/06-qa-release-exports.md`; `docs/superpowers/plans/07-autonomy-recovery-security.md`; `docs/superpowers/plans/08-amanda-production-run.md`; `docs/superpowers/plans/09-optional-render-cloud.md`; `tool-lab/horizun/results/probe-routes-2026-09-15.json`; `tool-lab/horizun/results/probe-adapter-wall.json`; `tool-lab/horizun/results/probe-adapter-wall-verify.json`; `design-engine/runs/AMANDA-RUN-001/refinement-summary.json`; `project/requirements/academic-deliverables.yaml`; `project/site/site.json`; `project/site/missing-data.yaml`; `state/design-run-freeze.yaml`; `docs/reports/p08-preflight.md`; `docs/reports/p08-site-resolution.md`.

Os caminhos `docs/notes/2026-09-11-amanda-tfg-bim-agent-design.md` e `docs/notes/2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md` não existem nesta cópia; foram lidos os dois arquivos canônicos correspondentes na raiz.
