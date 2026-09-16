# O que falta para o projeto terminar — v16

Data da leitura: 2026-09-16. Substitui o v15. Nota de leitura: **somente consulta**, sem escrita no Revit, sem `git add/commit/push` e sem alteração de estado.

## Onde estamos

- Grafo: **159 tarefas = 136 PASS + 3 PASS_WITH_WARNINGS + 12 PENDING + 8 SUSPENDED, 0 FAIL**; `ready = P08-T08`; `state_revision: 155`; `PROJECT_STATE.yaml` em `GO_WITH_LIMITATIONS`; `selected_design: null`.
- Revit 2027 vivo (build `27.2.0.39`), add-in Horizun com perfil `full_write`, documento ativo de laboratório `LAB_ROUTE_PROBE.rvt`; o lock de escritor está livre.
- Estudo `AMANDA-RUN-001` com programa congelado de 20 pessoas (626 m² internos, 260 m² externos) e **duas** finalistas publicadas: `AMANDA-RUN-001-F01` e `-F02`.

Fontes: `state/task-graph.yaml`, `state/status.md`, `PROJECT_STATE.yaml`, `design-engine/runs/AMANDA-RUN-001/finalists/`.

## O que falta

1. **P08-T08 — massas conceituais das finalistas** (próxima e única tarefa `ready`). Criar um RVT por finalista em `CONCEPT_ONLY`, estágios R01→R04, com conferência de medidas, preview e salvar/fechar/reabrir. **Trava:** ainda não existe driver para candidato conceitual real (o CLI `bim execute` só aceita `SYNTHETIC_LAB`), e `revit.create_grid`/`revit.create_roof` estão com `registered_entry: null` no crosswalk. O título fala em "top 3" mas só existem 2 finalistas.
2. **P08-T09 — escolha formal.** Comparar F01/F02 e gravar `APPROVED_FOR_BIM` com `approval_hash`; fica `AMANDA_REVIEW_PENDING` e não bloqueia. **Trava:** depende de P08-T08; `solutions/finalists/comparison.md` está em DRAFT/PENDING.
3. **P08-T10 a P08-T14 — modelo de produção.** RVT de trabalho e compilação R01→R13 (projeto, terreno, níveis, massa, paredes, ambientes, acessibilidade, mobiliário, paisagismo, materiais, documentação), com lease, `WRITE → READ → VERIFY` e checkpoint por etapa.
4. **P08-T15 a P08-T17 — QA, candidato e exportações.** QA R14, RC R15, reabertura a frio e validação de IFC/PDF/DWG/PNG, tabelas, páginas, hashes e relatórios.
5. **P08-T18/T19 — pacote final e GOLDEN.** Preparar o pacote antes de promover o R16 a `GOLDEN-001`.
6. **P08-T01 — liberação de produção** (hoje `PASS_WITH_WARNINGS`). As 11 capacidades de `state/capabilities.yaml` são todas `evidence_scope: PROVIDER`, **0 PRODUCTION**.
7. **P02-T17 — casos reais** (hoje `PASS_WITH_WARNINGS`): 4 de 8 casos de falha seguem `SKIPPED_NEEDS_REVIT`.
8. **P07-T17 — retomada em sessão nova.** Exige sessão Codex genuinamente nova; simulação na mesma sessão não vale.
9. **P07-T19 — retomada após reinício real.** Nenhum reinício foi feito; segue `SUSPENDED`.
10. **P09-T03/T04/T05 — Blender.** Adiado por falta de necessidade real; nada executado.
11. **P09-T07/T08/T09 — APS.** Gate `NO-GO`: nenhuma capacidade local está bloqueada por ferramenta e a rota paga ficou fora de escopo.
12. **Dados do terreno.** `SITE_TOPOGRAPHY`, `SITE_BOUNDARY` e `SITE_OCCUPANCY` são BLOCKING; `SITE_FRONTAGE_COUNT` e `SITE_TRUE_NORTH` são DEGRADING. Isso trava a validação final de declividade, acessibilidade altimétrica, área e disponibilidade do sítio — o estudo planar provisório pode continuar.
13. **Entregas acadêmicas.** 10 itens PENDING + 1 PROVISIONAL em `project/requirements/academic-deliverables.yaml`, todos humanos.

## O que só o dono pode fazer

- Confirmar na tela do Revit qual documento está ativo antes de cada escrita e clicar nos diálogos de permissão quando aparecerem.
- Abrir a sessão nova e autorizar o reinício real exigidos por P07-T17/P07-T19.
- Fornecer ou obter os documentos verificáveis do terreno (topografia, polígono, ocupação).
- Revisar a escolha arquitetônica, fazer autoria, visitas, defesa e submissão acadêmica.

## Não precisa de nada pago

O caminho é 100% local: Revit + Horizun (fonte aberta, construída localmente) + IFC/PDF/DWG gerados pelo próprio Revit + Blender local. O gate de APS deu `NO-GO` justamente porque não existe capacidade local bloqueada por ferramenta, e a rota cloud paga está fora de escopo em `docs/superpowers/plans/09-optional-render-cloud.md`. Nenhum serviço premium ou com assinatura foi usado até hoje.

## Próximos 5 passos concretos

1. Conferir o documento ativo no Revit e deixar um RVT descartável seguro em `revit/lab/` (nunca em `baseline/`, `GOLDEN/` ou `release/`).
2. Fechar o gap do crosswalk: provar `grid` ao vivo via `horizun_create_elements`, com `WRITE → READ → VERIFY`, gravar a evidência com sha256 e registrar a entrada antes de preencher `registered_entry`.
3. Escrever `tests/unit/test_bim_concept_candidates.py` (RED) e criar `scripts/bim_concept_candidates.py`.
4. Executar P08-T08 para F01 e F02, com journals, checkpoints e save/close/reopen.
5. Fechar P08-T09 e seguir para P08-T10→P08-T19.

## Mudança em relação ao v15

- O v15 citava HEAD `2cc501e`; o HEAD atual é `b62e144`.
- O v15 dizia que `solutions/finalists/comparison.md` "não foi encontrado"; o arquivo existe e está marcado como DRAFT/PENDING — é insumo de P08-T09.
- Confirmado nesta sessão: suíte completa com **822 testes passando** e limpeza local executada (`remaining scratch=0 pycache=0`).
- Novo handoff geral: `docs/notes/2026-09-16-handoff-geral-estado-e-o-que-falta.md`.
