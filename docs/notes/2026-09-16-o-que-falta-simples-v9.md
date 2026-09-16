# O que falta — versão simples (v9)

Data: 2026-09-16  
Escopo: leitura dos planos e do estado atual. Nenhuma execução do Revit/MCP.

## Situação em uma linha

São **159 tarefas**: **136 PASS**, **2 PASS_WITH_WARNINGS**, **13 PENDING**, **8 SUSPENDED** e **0 FAIL**. A próxima tarefa registrada é **P06-T14**. O campo `next_task` não existe literalmente em `state/task-graph.yaml`; o valor `P06-T14` está em `PROJECT_STATE.yaml` e `state/status.md`.

Comando de contagem usado:

```powershell
rg -c '^[[:space:]]{4}status: PASS\r?$' state/task-graph.yaml; rg -c '^[[:space:]]{4}status: PASS_WITH_WARNINGS\r?$' state/task-graph.yaml; rg -c '^[[:space:]]{4}status: PENDING\r?$' state/task-graph.yaml; rg -c '^[[:space:]]{4}status: SUSPENDED\r?$' state/task-graph.yaml; rg -c '^[[:space:]]{4}status: FAIL\r?$' state/task-graph.yaml
```

## O que já está pronto

- **Fase 00:** base do projeto e ordem das tarefas — 3/3 PASS.
- **Fase 01:** ambiente local, estado persistente e comandos básicos — 13/13 PASS.
- **Fase 02:** testes dos provedores e das capacidades em laboratório — 19 PASS e 1 PASS_WITH_WARNINGS; falta provar o uso em produção.
- **Fase 03:** leitura, organização e rastreabilidade das fontes — 15/15 PASS.
- **Fase 04:** geração e comparação das alternativas de projeto — 22/22 PASS.
- **Fase 05:** compilador e estágios BIM R01–R13 em plano sintético — 23/23 PASS.
- **Fase 06:** ferramentas de conferência e entrega — 14/15 PASS; falta o ensaio completo de entrega.
- **Fase 07A:** regras de segurança e controle — 11/11 PASS.
- **Fase 07B:** recuperação e continuidade — 6 PASS; 2 tarefas ficaram suspensas para sessão nova e reinício real.
- **Fase 08:** preparação do estudo — 6 PASS, 1 PASS_WITH_WARNINGS e 12 pendentes; há um ajuste de nomes em andamento, mas ainda não é o modelo final.
- **Fase 09:** decisão de não usar render/nuvem agora — 4/10 PASS; 6 tarefas opcionais suspensas.

## O que falta

| Bloco | O que falta | Tarefas | Do que depende |
|---|---|---|---|
| Ensaio de entrega | Salvar, fechar, reabrir, exportar e conferir uma cópia em laboratório | P06-T14 | Revit aberto e documento descartável de laboratório |
| Continuidade | Provar retomada em uma sessão nova e depois de reiniciar o computador | P07-T17, P07-T19 | Sessão nova do Codex e reinício autorizado por humano |
| Massas do estudo | Desenhar no Revit as opções F01/F02 e conferir medidas | P08-T08 | Ajuste/validação dos nomes internos das capacidades e acesso funcional ao Revit |
| Escolha da opção | Registrar formalmente uma opção como pronta para continuar no BIM; Amanda revisa depois | P08-T09 | P08-T08 concluída e comparação dos finalistas |
| Arquivo de trabalho | Criar o RVT de trabalho oficial do projeto | P08-T10 | Escolha registrada e preflight de produção liberado |
| Modelagem principal | Fazer R01–R04, R05–R08 e R09–R12: base, paredes, ambientes, acessibilidade, mobiliário, exterior e materiais | P08-T11, P08-T12, P08-T13 | RVT de trabalho, capacidades de escrita e dados verificados |
| Pranchas | Fazer R13: plantas, cortes, fachadas, tabelas, cotas, etiquetas e pranchas | P08-T14 | Modelagem principal concluída |
| Conferência e entrega | QA R14, candidato R15, reabertura a frio, IFC/PDF/DWG, relatórios e pacote GOLDEN | P08-T15, P08-T16, P08-T17, P08-T19, P08-T18 | Modelo completo, exportações válidas e provas de persistência |
| Render e nuvem | Instalar/testar Blender ou APS somente se surgir necessidade real | P09-T03, P09-T04, P09-T05, P09-T07, P09-T08, P09-T09 | Pedido explícito de render/nuvem; APS ainda exigiria necessidade bloqueada e autorização |

## Tarefas PENDING — lista exata

- **P06-T14 — Synthetic R14→R16 release drill:** destrava com o ensaio físico no Revit de laboratório, incluindo fechar, abrir, exportar e conferir hashes.
- **P08-T08 — Create conceptual Revit massing for top 3:** destrava com a execução do massing conceitual R01–R04 no Revit para os finalistas.
- **P08-T09 — Delegated architectural selection and later Amanda review:** destrava depois do massing, com o agente registrando a escolha e Amanda revisando depois.
- **P08-T10 — Create production working RVT:** destrava depois da escolha registrada e do preflight de produção liberado.
- **P08-T11 — Compile R01–R04:** destrava com o RVT de trabalho e as capacidades de escrita verificadas.
- **P08-T12 — Compile R05–R08:** destrava depois de R01–R04; faz a casca, o layout, as aberturas e os ambientes.
- **P08-T13 — Compile R09–R12:** destrava depois de R05–R08 e dos dados normativos/site que estiverem disponíveis.
- **P08-T14 — Compile R13 documentation:** destrava depois da modelagem; produz pranchas, vistas, tabelas e cotas.
- **P08-T15 — Run full R14 QA:** destrava com R13 pronto para conferir modelo, programa, site, acessibilidade, avisos e documentação.
- **P08-T16 — Create R15 Release Candidate:** destrava com QA aceitável e prova de salvar, fechar, reabrir a frio e conferir novamente.
- **P08-T17 — Export/validate RC:** destrava com o candidato R15 reaberto; exporta e valida IFC, PDF, DWG e imagens.
- **P08-T19 — Final deliverable package preparation before Task 18 promotion:** destrava com as exportações prontas, relatórios e hashes conferidos.
- **P08-T18 — Promote R16 GOLDEN:** destrava por último, depois de P08-T19, para publicar a versão oficial imutável.

## Tarefas SUSPENDED — lista exata

- **P07-T17 — Fresh-session recovery drill:** destrava em uma sessão nova do Codex, seguindo o roteiro de retomada e registrando a evidência real.
- **P07-T19 — Full reboot simulation/procedure:** destrava após um reinício real e autorizado, seguido do roteiro de retomada; simular sem reiniciar não conta.
- **P09-T03 — Register Blender MCP:** destrava se houver necessidade de render e o Blender estiver disponível para ser verificado.
- **P09-T04 — Blender Tool Lab:** destrava depois do registro do Blender, caso o render seja realmente pedido.
- **P09-T05 — Rendering pipeline from verified BIM release:** destrava com um BIM verificado/GOLDEN e uma necessidade concreta de render.
- **P09-T07 — Audit official APS sample repos:** destrava apenas se o portão APS voltar a indicar uma capacidade local bloqueada e houver autorização do dono.
- **P09-T08 — APS secret boundary:** destrava depois da auditoria APS e de uma necessidade real de usar nuvem; nenhuma credencial foi criada.
- **P09-T09 — APS sandbox deployment/test:** destrava depois do limite de segredo e de autorização para um teste de nuvem; nada foi enviado.

As tarefas da Fase 09 estão suspensas de propósito. Elas não impedem o caminho local do projeto.

## O que atrapalha, mas não é tarefa

- **Terreno/topografia:** faltam levantamento, cotas e datum; a representação atual é um plano provisório.
- **Limite do terreno:** falta polígono cadastral ou levantamento georreferenciado; a área de 24.135 m² é hipótese de estudo.
- **Uso atual do lote:** falta confirmar a ocupação atual e a premissa de realocação da unidade policial.
- **Número de frentes:** o material fala em três ou quatro; precisa ser resolvido com documento do terreno.
- **Norte verdadeiro:** falta azimute ou desenho com referência confiável; os resultados solares são apenas indicativos.

Esses dados não impedem adiantar a massa e o estudo planar. Eles impedem afirmar implantação final, área legal, acessibilidade altimétrica e conformidade definitiva.

## Separação honesta das provas

**Provado fisicamente no Revit, em laboratório:** o Revit 2027 identificado é o build `27.2.0.39`, compatível com o registro do ambiente; Horizun e RevitCortex aparecem saudáveis; e o relatório de rotas registra 18 rotas do adaptador provadas em um documento descartável, cada uma com leitura independente. Isso prova a ponte de laboratório. Não prova o modelo final da Amanda.

**STUDY/estudo local:** foram feitas 144 tentativas de projeto; 2 opções válidas sobraram, F01 e F02. Há comparação em rascunho, com recomendação provisória de F01. O estudo usa terreno planar provisório, sem norte real. Solar e ventilação estão marcados como `HEURISTIC`, e o compilador foi exercitado em `CONCEPT_ONLY` até R04. A opção ainda não está registrada como `APPROVED_FOR_BIM`.

**Bloqueado ou ainda sem prova:** não existe RVT de produção final, nem reabertura a frio desse arquivo, nem QA completo R14, nem candidato R15, nem pacote IFC/PDF/DWG validado para a entrega, nem `GOLDEN-001`. O preflight também registra zero capacidades com escopo `PRODUCTION`; as 11 entradas gerais do catálogo estão em escopo `PROVIDER`. Há um arquivo local de correspondência de nomes em andamento, mas ele ainda deixa `grid` e `roof` sem entrada registrada e não mudou os status do grafo.

## Por que a Fase 08 (modelagem) está parada

1. O dono já resolveu a primeira trava: o add-in está com permissão **`full_write`**. Isso permite escrever quando o restante do caminho estiver liberado.
2. Ainda existe uma trava local de nomes: o catálogo registra capacidades com nomes curtos, como `wall` e `level`, enquanto os estágios e o compilador pedem nomes completos, como `revit.create_wall` e `revit.create_level`. O sistema precisa reconhecer que são o mesmo pedido. Já há uma correspondência sendo montada, mas ela ainda tem lacunas para `grid` e `roof` e não foi convertida em prova de produção.
3. O modo **PRODUÇÃO** exige uma prova em uso real: build correto, capacidade correspondente, escrita, leitura independente, salvamento e reabertura. Hoje as provas gerais são de provedor/laboratório; nenhuma está marcada como `PRODUCTION`, e nenhum teste Revit marcado foi coletado no preflight.

Na prática, ainda não dá para gerar o modelo final pelo caminho oficial. Dá para adiantar a massa e a modelagem como **estudo**, depois que o ajuste dos nomes e a prova de produção forem resolvidos.

## Próximos 3 passos mais úteis

1. **Agente principal:** fechar P06-T14 no documento descartável, com salvar, fechar, reabrir e exportações. Esse passo dá a primeira prova completa de entrega.
2. **Agente principal:** ajustar a correspondência entre os nomes do catálogo e os nomes pedidos pelo compilador, refazer o preflight e, com a ponte liberada, executar P08-T08 como massing de estudo.
3. **Amanda/Matheus:** fornecer levantamento/topografia, limite cadastral, ocupação atual, número de frentes e norte verdadeiro. O agente incorpora esses dados e revalida as partes que hoje estão bloqueadas.

## Nota de honestidade e retomada

Nada foi pago. Nenhuma nuvem/APS foi usada. Os números deste relatório foram medidos no estado atual dos arquivos. A análise foi somente leitura e preservou as alterações já existentes no checkout.

GitHub no início da análise: branch `main` alinhada com `origin/main` em `abe34c2`; o checkout já estava sujo por alterações de outros trabalhos. Não foi feito commit nem push, conforme a restrição desta análise.

Para retomar: ler este relatório, `state/task-graph.yaml`, `PROJECT_STATE.yaml` e `docs/reports/p08-preflight.md`; depois executar somente a próxima tarefa autorizada, mantendo o estudo separado do modelo oficial.
