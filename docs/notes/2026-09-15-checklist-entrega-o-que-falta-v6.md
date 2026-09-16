# Checklist de entrega — o que falta (V6)

Data: 2026-09-15. Visão complementar à V5, concentrada nos arquivos de entrega e na limpeza local; a V5 já registra o retrato geral do fluxo (`docs/notes/2026-09-15-o-que-falta-simples-v5.md:5-13,75-83`).

## 1. Em uma frase — o que falta hoje

Hoje há fontes, dados canônicos, dois finalistas e provas de laboratório/estudo, mas ainda não há RVT de produção nem documentação emitida a partir dele; faltam seleção formal para BIM, compilação R01–R13, QA R14, RC frio R15 e os exports/relatórios correspondentes; o pacote `bim/releases/GOLDEN-001/` e o selo GOLDEN ainda não existem, e o estado não registra seleção, etapa Revit ou checkpoint (`PROJECT_STATE.yaml:7-19`; `state/status.md:7-11,52-54`; `state/task-history.yaml:1980-1994`); enquanto topografia, limite, ocupação, frentes e norte permanecerem sem comprovação, qualquer release precisa declarar escopo `STUDY` e `FINAL` continua bloqueado (`state/blockers.yaml:3-120`; `docs/superpowers/plans/08-amanda-production-run.md:320-329`).

## 2. Checklist de entrega

| Artefato | Situação | Evidência | O que falta | Quem faz |
|---|---|---|---|---|
| RVT de produção | não existe | `revit/production/working/AMANDA_WORKING_001.rvt` não encontrado; há RVTs em `revit/lab/`; destino previsto em `docs/superpowers/plans/08-amanda-production-run.md:170-176` | criar o arquivo de trabalho, registrar hash e fazer save/close/reopen | agente; humano só em diálogo/licença/UAC |
| Plantas | existe só em STUDY | `design-engine/runs/AMANDA-RUN-001/finalists/AMANDA-RUN-001-F01/floorplan.svg` e `.png`; documentação exigida em `docs/superpowers/plans/08-amanda-production-run.md:218-229` | gerar plantas do modelo Revit escolhido, cotar, etiquetar e validar | agente; humano revisa visual/acadêmico |
| Cortes | não existe | nenhum corte no pacote atual; requisito em `docs/superpowers/plans/08-amanda-production-run.md:220-227` | criar cortes arquitetonicamente significativos e seus previews | agente; humano revisa visual |
| Elevações | não existe | nenhum arquivo de elevação no pacote atual; requisito em `docs/superpowers/plans/08-amanda-production-run.md:220-227` | criar elevações e revisar legibilidade | agente; humano revisa visual |
| Pranchas | parcial | requisito acadêmico de 4–6 A1 ainda `PROVISIONAL`, sem evidência, com Amanda como autora (`project/requirements/academic-deliverables.yaml:73-85`); sheets Revit previstas em `docs/superpowers/plans/08-amanda-production-run.md:223-229` | montar pranchas, revisar composição e fechar a quantidade institucional | agente monta; Amanda valida e assina |
| Tabelas/quantitativos | parcial | `project/requirements/program.json` e CSV de laboratório `tool-lab/horizun/exports/LAB_HORIZUN_DOC_ambientes.csv`; schedules/area summary ainda são requisitos (`docs/superpowers/plans/08-amanda-production-run.md:223-225,261-271`) | extrair tabelas de salas/portas/janelas e quadro de áreas do RVT de produção | agente |
| IFC | parcial | existe IFC de laboratório em `tool-lab/horizun/exports/LAB_HORIZUN_DOC.ifc` e IFC-fonte hipótese em `TFG_Amanda_2026/4_PROJETO_E_CALCULOS/07_modelo_BIM_HIPOTESE.ifc`; export/parse do RC faltam (`docs/superpowers/plans/08-amanda-production-run.md:261-264`) | exportar o RC, validar com IfcOpenShell e colocar o IFC no pacote | agente |
| PDF | parcial | existe PDF de laboratório em `tool-lab/horizun/exports/LAB_HORIZUN_DOC.pdf` e PDF-fonte; PDF das sheets ainda é pendente (`docs/superpowers/plans/08-amanda-production-run.md:265-266`) | exportar sheets, conferir páginas e previews não vazios | agente |
| DWG | parcial | existe DWG de laboratório `tool-lab/horizun/exports/LAB_HORIZUN_DOC.dwg` e DXF-fonte hipótese; exportação/limitação de validação ainda faltam (`docs/superpowers/plans/08-amanda-production-run.md:267-268`) | exportar DWG do RC, validar o que o parser suportar e registrar limites | agente |
| PNG/previews | existe só em STUDY | finalistas têm `floorplan`/`zoning` PNG/SVG; a produção exige preview de cada sheet (`docs/superpowers/plans/08-amanda-production-run.md:136-145,218-229`) | gerar previews das vistas/sheets selecionadas e fazer fila de revisão visual | agente; humano revisa imagens |
| Relatórios de QA/área/acessibilidade | parcial | há preflight/site reports, mas não há `QA_REPORT_RC01.md`, `PROGRAM_COMPLIANCE.md` ou `ACCESSIBILITY_REPORT.md`; requisitos em `docs/superpowers/plans/08-amanda-production-run.md:233-243,303-309` | rodar R14, reconciliar áreas/programa, declarar acessibilidade suportada e registrar limitações | agente; humano valida o que não for automatizável |
| Proveniência | parcial | manifests e versões existem em `project/provenance/source-manifest.yaml`, `source-inventory.json` e `source-versions.yaml`; o `provenance.json` do release não existe, embora seja exigido em `docs/superpowers/plans/08-amanda-production-run.md:297-316` | amarrar fontes, decisões, hashes, provider e versão ao RC/GOLDEN | agente |
| Pacote final | não existe | `bim/releases/GOLDEN-001/` não encontrado; árvore esperada em `docs/superpowers/plans/08-amanda-production-run.md:292-316` | montar staging com RVT, exports, previews, manifest e todos os relatórios | agente; Amanda fornece/valida itens acadêmicos |
| GOLDEN-001 | não existe | `bim/releases/GOLDEN-001` não encontrado; promoção só após precondições em `docs/superpowers/plans/08-amanda-production-run.md:275-288` | publicar diretório novo, verificar hash pós-cópia, marcar imutável e liberar lock | agente; decisão acadêmica continua humana |

## 3. Próximos 5 passos em ordem

1. `P06-T14`: fechar o ensaio sintético R14→R16, que ainda está pendente no grafo (`state/task-graph.yaml:1975-1983`).
2. `P08-T08`: criar as massas conceituais Revit dos finalistas, salvar/reabrir e gerar previews (`state/task-graph.yaml:2403-2411`; `docs/superpowers/plans/08-amanda-production-run.md:136-145`).
3. `P08-T09`: comparar os finalistas, escolher uma solução e registrar `APPROVED_FOR_BIM`/hash com revisão de Amanda pendente (`state/task-graph.yaml:2412-2420`; `docs/superpowers/plans/08-amanda-production-run.md:149-166`).
4. `P08-T10`: criar `revit/production/working/AMANDA_WORKING_001.rvt` com writer lease e hash inicial (`state/task-graph.yaml:2421-2429`; `docs/superpowers/plans/08-amanda-production-run.md:170-176`).
5. `P08-T11`: compilar R01–R04 e, em cada estágio, fazer WRITE→READ→VERIFY, checkpoint e atualização do estado (`state/task-graph.yaml:2430-2438`; `docs/superpowers/plans/08-amanda-production-run.md:180-193`).

## 4. O que não precisa pagar

- Render Blender/nuvem: `P09-T03`, `P09-T04` e `P09-T05` estão `SUSPENDED` porque o gate marcou render como `DEFERRED_OPTIONAL`; não há render fotorrealista exigido (`state/task-graph.yaml:2511-2599`; `docs/superpowers/plans/09-optional-render-cloud.md:27-31,95-107`).
- APS/Forge: `P09-T07`, `P09-T08` e `P09-T09` estão `SUSPENDED` após `P09-T06` retornar `NO-GO`; não houve credencial, upload, app ou teste cloud (`state/task-graph.yaml:2600-2667`; `tool-lab/aps/need-report.md:10-24`).
- Assinaturas/rotas pagas: o gate registra que o proprietário proibiu APS/Forge por ser caminho pago/cloud e que a cadeia local já cobre as operações necessárias (`tool-lab/aps/need-report.md:16-24,32-50`). O caminho obrigatório P08 + QA/export local não exige esse gasto; a fase 09 é opcional (`2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md:77-89`).

## 5. Limpeza local — somente leitura

Medida atual por `Get-ChildItem -Recurse -File`; contagem por `git ls-files -- candidato` e `Measure-Object`. Nenhum item foi removido.

| Candidato | Tamanho atual | Git rastreados | Arquivo do repo aponta? | Veredito |
|---|---:|---:|---|---|
| `.dotnet/` | 769,94 MB / 0,752 GB | 0 | sim: `scripts/cleanup-local.ps1:16-17`; build/runtime citado em `state/task-graph.yaml:604-605` | precisa autorização |
| `vendor/` | 354,44 MB / 0,346 GB | 0 | sim: `C:\Users\slvma\.codex\config.toml:130` aponta para `vendor/RevitCortex`; planos também o usam | inseguro |
| `tool-lab/` | 171,86 MB / 0,168 GB | 207 | sim: `scripts/cleanup-local.ps1:16-17`; contém exports e relatórios de provider | inseguro |
| `revit/` | 99,67 MB / 0,097 GB | 1 | sim: `docs/superpowers/plans/08-amanda-production-run.md:174`; abriga RVTs de laboratório | inseguro |
| `logs/` | 0,03 MB | 1 | sim: `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md:2910,3200` | precisa autorização |
| `.venv/` | 441,88 MB / 0,432 GB | 0 | sim: comandos de testes/doctor/status em `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md:159-183` | precisa autorização |
| `.venv-topologic/` | 376,05 MB / 0,367 GB | 0 | sim: isolamento exigido em `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md:2122` | precisa autorização |
| `.venv-environmental/` | 451,01 MB / 0,440 GB | 0 | sim: ambiente isolado em `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md:2133`; uso registrado em `state/task-history.yaml:1165` | precisa autorização |
| `TFG_Amanda_2026/` | 0,74 MB / 0,001 GB | 0 | sim: fontes esperadas e preservadas em `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md:1476-1484` | inseguro |
| `bim/` | 0 MB | 0 | sim: é o destino futuro do release em `docs/superpowers/plans/08-amanda-production-run.md:285,297-309` | precisa autorização |
| `bootstrap/` | 0,01 MB | 2 | sim: código de bootstrap previsto em `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md:264,552-614` | inseguro |
| `project/` | 0,10 MB | 13 | sim: dados canônicos/proveniência e site em `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md:1405,1469-1499` | inseguro |

Configuração do usuário: `C:\Users\slvma\.codex\config.toml:130` referencia `vendor/RevitCortex`; a busca `rg -n -i "vendor|\.dotnet"` não encontrou `.dotnet` nesse arquivo. O script de limpeza também documenta que preserva venvs, `.dotnet`, vendor, `revit/lab`, resultados do Tool Lab, docs, state e qualquer arquivo rastreado (`scripts/cleanup-local.ps1:16-20`).

## 6. Divergências e riscos

- O dashboard chama `P06-T14` e `P08-T08` de `READY`, mas o grafo mantém ambos os trabalhos ainda não concluídos; `P08-T08` segue `PENDING` (`state/status.md:7-11`; `state/task-graph.yaml:2403-2411`).
- Há freeze de inputs em escopo `STUDY`, mas `PROJECT_STATE.yaml` ainda tem `selected_design: null`; isso não é seleção arquitetônica final (`state/design-run-freeze.yaml:20-26`; `PROJECT_STATE.yaml:7-19`).
- O passe ambiental é `HEURISTIC`, sem simulação detalhada, e o norte/topografia continuam limitados (`design-engine/runs/AMANDA-RUN-001/environmental-pass.md:4-19,34-45`).
- IFC/DXF/PDF/DWG de laboratório ou hipótese não podem ser contados como exports do RC; o pacote final continua ausente (`docs/superpowers/plans/08-amanda-production-run.md:261-316`).
- O worktree já estava sujo antes desta nota; não foram feitos `git add`, commit ou push, conforme o limite de somente leitura do pedido.

## Registro para retomada

Planos consultados: `docs/superpowers/plans/00-master-implementation-plan.md:5`, `01-foundation-environment-state.md:5`, `02-revit-tool-lab-providers.md:5`, `03-project-intelligence.md:5`, `04-design-engine.md:5`, `05-bim-compiler.md:5`, `06-qa-release-exports.md:5`, `07-autonomy-recovery-security.md:5`, `08-amanda-production-run.md:5` e `09-optional-render-cloud.md:5`. O combined plan confirma fase 08 como produção Amanda e fase 09 como render/cloud opcional (`2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md:68-89`).

Retomada: começar pelo gate `P06-T14`; se o dono priorizar a cadeia de produção conceitual, usar `P08-T08` em escopo `STUDY`, mantendo os cinco bloqueios de terreno e sem remover os candidatos do radar sem autorização explícita.
