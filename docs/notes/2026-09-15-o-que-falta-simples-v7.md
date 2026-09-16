# O que falta para a entrega — V7

Data: 2026-09-15. Auditoria somente leitura do estado vivo e do disco.

## Em uma frase

Hoje existe um estudo com dois finalistas e uma cadeia local testada, mas ainda falta escolher formalmente a proposta, criar o RVT de produção, emitir os desenhos e exportações, fazer o QA final e fechar o pacote de entrega.

## Checklist de entrega

- **Proposta arquitetônica — EXISTE como STUDY:** dois finalistas em `design-engine/runs/AMANDA-RUN-001/finalists/AMANDA-RUN-001-F01/` e `F02/`; falta `comparison.md`, escolher um finalista e registrar `APPROVED_FOR_BIM` em `P08-T09`.
- **RVT de produção — NÃO EXISTE:** `Test-Path revit/production/working/AMANDA_WORKING_001.rvt = False` e `revit/production/candidates/ = False`; os RVTs encontrados estão somente em `revit/lab/`.
- **Plantas, cortes e elevações — PARCIAL:** existem `floorplan.svg/.png` e `zoning.svg/.png` dos dois estudos; não há corte ou elevação no run; faltam vistas cotadas e etiquetadas vindas do RVT escolhido, em `P08-T14`.
- **Pranchas e tabelas — NÃO EXISTEM em produção:** há uma prancha e uma tabela no arquivo de laboratório `LAB_HORIZUN_DOC`; faltam sheets, tabelas de ambientes/portas/janelas e quadro de áreas da Amanda, em `P08-T14`.
- **Exportações IFC/PDF/DWG — PARCIAIS:** `tool-lab/horizun/exports/LAB_HORIZUN_DOC.{ifc,pdf,dwg}` existem e são de laboratório; não há exportação do RVT Amanda, nem cópia em RC ou GOLDEN, em `P08-T17`.
- **QA final — NÃO EXISTE:** os validadores e testes sintéticos existem, mas `P06-T14` está PENDING e `P08-T15` ainda não rodou; não existem `QA_REPORT_RC01.md`, `PROGRAM_COMPLIANCE.md` ou `ACCESSIBILITY_REPORT.md`.
- **Pacote com proveniência — NÃO EXISTE:** os manifestos de fonte existem em `project/provenance/`; `bim/releases/GOLDEN-001/` e seu `provenance.json`, manifesto, relatórios e hashes não existem.
- **Limite STUDY/FINAL:** `state/design-run-freeze.yaml` está `FROZEN_FOR_STUDY`; `PROJECT_STATE.yaml` ainda tem `selected_design: null`, `revit_stage: null` e `current_checkpoint: null`.

## Próximos 5 passos, em ordem

Depois da `PHASE_06`, a ordem canônica é `PHASE_07B`, `PHASE_08` e `PHASE_09`; a fase 09 é opcional.

1. **P06-T14 — concluir o ensaio sintético R14→R16:** provar QA, reabertura fria, IFC, PDF, DWG e GOLDEN de laboratório antes de usar a cadeia na produção Amanda.
2. **P08-T08 — criar massas Revit dos finalistas:** verificar as duas opções no Revit, salvar, fechar e reabrir antes da escolha.
3. **P08-T09 — comparar e escolher a proposta:** registrar a escolha delegada, o hash e a revisão posterior de Amanda antes do BIM detalhado.
4. **P08-T10 — criar `AMANDA_WORKING_001.rvt`:** abrir o arquivo de produção com lease, segurança e hash inicial somente depois da escolha.
5. **P08-T11 — compilar R01–R04:** criar projeto, site de estudo, níveis e massa com `WRITE→READ→VERIFY` e checkpoint após cada etapa.

## O que trava hoje

**(a) O próprio agente ainda consegue fazer:** concluir `P06-T14`; criar as massas STUDY de `P08-T08`; montar a comparação e registrar a seleção em `P08-T09`; depois compilar, documentar, testar e exportar a proposta escolhida.

**(b) Está bloqueado:** topografia, polígono cadastral, ocupação/realocação, número de frentes e norte verdadeiro continuam pendentes em `state/blockers.yaml`; eles bloqueiam afirmações de implantação, área legal, acessibilidade altimétrica e `FINAL`. O preflight também registra zero capability com escopo `PRODUCTION`; as evidências atuais são de provider/laboratório. `P07-T17` e `P07-T19` seguem SUSPENDED, embora `P08-T01` tenha avançado com warnings.

**(c) Só uma pessoa pode fazer na mão:** fornecer ou atestar levantamento, limite e disponibilidade do terreno; revisar a proposta; fazer a revisão visual final; produzir ou validar caderno, visitas, metaprojeto, anteprojeto, pranchas acadêmicas, memoriais, autoria, defesa e submissão institucional. Esses itens continuam PENDING/PROVISIONAL em `project/requirements/academic-deliverables.yaml`.

**Estado vivo:** 159 tarefas: 136 PASS, 2 PASS_WITH_WARNINGS, 13 PENDING e 8 SUSPENDED. Não estão PASS: `P02-T17`, `P08-T01`; `P06-T14`, `P08-T08`, `P08-T09`, `P08-T10`, `P08-T11`, `P08-T12`, `P08-T13`, `P08-T14`, `P08-T15`, `P08-T16`, `P08-T17`, `P08-T18`, `P08-T19`; `P07-T17`, `P07-T19`; `P09-T03`, `P09-T04`, `P09-T05`, `P09-T07`, `P09-T08`, `P09-T09`.

**Correção do v6:** o diagnóstico principal estava correto. A atualização é que `P08-T02`–`P08-T07` agora estão PASS no grafo, mas continuam STUDY; o passe ambiental é HEURISTIC e ainda não existe `solutions/finalists/comparison.md`.

## Nada aqui exige pagamento

O caminho obrigatório documentado não exige pagamento adicional: usa Revit local já instalado, Horizun local e o fallback C# local, com exportações locais.

Evidência: `tool-lab/aps/need-report.md` marca APS/Forge como `DEFERRED_OPTIONAL` e `NO-GO`, sem credencial, aplicativo, upload ou teste cloud; `docs/reports/p09-optional-extensions.md` marca Blender como opcional e não executado; `tool-lab/revitcortex/licensing-finding.md` registra licença MIT e nenhum tier pago usado.

O disco comprova uso local e ausência de compra, assinatura ou chave criada neste projeto; ele não prova os termos comerciais da licença Autodesk já instalada. Portanto, não há gasto adicional previsto no caminho obrigatório.
