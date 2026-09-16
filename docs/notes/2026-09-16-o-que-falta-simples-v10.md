# O que falta para o projeto ficar pronto — v10

Data: 2026-09-16. Leitura somente-leitura dos planos e do estado. Nenhuma chamada ao Revit ou MCP foi feita.

## Situação em uma linha

São **159 tarefas**: **136 PASS**, **2 PASS_WITH_WARNINGS**, **13 PENDING**, **8 SUSPENDED** e **0 FAIL**. A próxima tarefa registrada é **P06-T14**. O projeto ainda não está pronto para uma entrega oficial.

Comando usado para contar o grafo atual:

`rg -o 'status: [A-Z_]+' state/task-graph.yaml | ForEach-Object { ($_ -split ': ')[1] } | Group-Object | Sort-Object Name`

Resultado: `PASS 136`, `PASS_WITH_WARNINGS 2`, `PENDING 13`, `SUSPENDED 8`.

As fases 00 a 05 não têm tarefas `PENDING` ou `SUSPENDED`; a Fase 02 inclui uma advertência (`PASS_WITH_WARNINGS`). Na Fase 06 falta o ensaio de entrega. A Fase 07B tem duas retomadas suspensas. A Fase 08 tem a preparação do estudo concluída, mas ainda não tem o modelo de produção. A Fase 09 é opcional e foi deixada suspensa.

## O que falta e de que depende

| Bloco | Tarefas | Do que depende |
|---|---|---|
| Ensaio de entrega | P06-T14 | P06-T15 está PASS; falta testar em documento descartável: salvar, fechar, abrir, exportar e conferir hashes. |
| Retomada segura | P07-T17, P07-T19 | P07-T17 depende de P07-T15 e de uma sessão nova do Codex. P07-T19 depende de P07-T18 e de um reinício real autorizado. |
| Massas do estudo e escolha | P08-T08, P08-T09 | P08-T08 depende de P08-T07 PASS e de escrita, leitura e conferência no Revit em modo `CONCEPT_ONLY`. P08-T09 depende do massing e da comparação dos finalistas. |
| RVT e modelagem principal | P08-T10, P08-T11, P08-T12, P08-T13 | Escolha registrada, preflight de produção liberado, capacidades com nomes/build conferidos e dados verificados. A cadeia é T10 → T11 → T12 → T13. |
| Pranchas, QA e entrega | P08-T14, P08-T15, P08-T16, P08-T17, P08-T19, P08-T18 | Modelagem completa → pranchas → QA → candidato RC → exportações validadas → pacote final T19 → GOLDEN T18. T18 só vem depois de T19. |
| Render e nuvem | P09-T03, P09-T04, P09-T05, P09-T07, P09-T08, P09-T09 | Só reabrir se houver pedido real de render. APS só pode voltar se uma capacidade local estiver comprovadamente bloqueada e houver autorização; não é necessário para o caminho local. |

## Tarefas PENDING — lista exata

- **P06-T14 — Synthetic R14→R16 release drill**
- **P08-T08 — Create conceptual Revit massing for top 3**
- **P08-T09 — Delegated architectural selection and later Amanda review**
- **P08-T10 — Create production working RVT**
- **P08-T11 — Compile R01–R04**
- **P08-T12 — Compile R05–R08**
- **P08-T13 — Compile R09–R12**
- **P08-T14 — Compile R13 documentation**
- **P08-T15 — Run full R14 QA**
- **P08-T16 — Create R15 Release Candidate**
- **P08-T17 — Export/validate RC**
- **P08-T19 — Final deliverable package preparation before Task 18 promotion**
- **P08-T18 — Promote R16 GOLDEN**

## Tarefas SUSPENDED — lista exata

- **P07-T17 — Fresh-session recovery drill**
- **P07-T19 — Full reboot simulation/procedure**
- **P09-T03 — Register Blender MCP**
- **P09-T04 — Blender Tool Lab**
- **P09-T05 — Rendering pipeline from verified BIM release**
- **P09-T07 — Audit official APS sample repos**
- **P09-T08 — APS secret boundary**
- **P09-T09 — APS sandbox deployment/test**

As seis tarefas suspensas da Fase 09 estão suspensas de propósito. Elas não impedem a produção local.

## O que atrapalha, mas não é tarefa

- **Topografia:** não há levantamento, cotas nem datum confiável. As marcações `[X]`, `[Y]`, `[Z]` e `[W]` continuam placeholders.
- **Limite do lote:** há somente a área informada de **24.135 m²**; falta polígono cadastral ou levantamento georreferenciado.
- **Uso atual:** falta confirmar a ocupação atual do lote e a premissa de realocação da unidade policial.
- **Número de frentes:** as fontes falam em três ou quatro; isso precisa vir de documento do terreno, não da contagem de nomes no texto.
- **Norte verdadeiro:** falta azimute ou desenho com referência confiável. Os resultados solares são apenas indicativos.

Os três primeiros pontos estão marcados como `BLOCKING`; frentes e norte estão como `DEGRADING`. Eles permitem um estudo planar, mas impedem afirmar implantação final, área legal, acessibilidade altimétrica e orientação definitiva.

## Provas separadas por nível

### Provado fisicamente, segundo os registros de laboratório

O Revit 2027 foi detectado e os registros de laboratório apontam Horizun e RevitCortex saudáveis. O tool-lab registra rotas testadas em documentos descartáveis, com leitura independente e salvamento. Isso prova a ponte de laboratório, não o modelo final da Amanda.

O catálogo tem 11 entradas `PASS`, com hashes conferidos, mas todas estão em escopo `PROVIDER`. O registro de laboratório também documenta que a permissão do add-in estava em `full_write`. Ainda assim, uma tentativa que alteraria o documento foi barrada pelo revisor automático; não há prova equivalente de escrita em produção.

### Estudo local (`STUDY`)

Foram feitas 144 tentativas; restaram F01 e F02 como finalistas do estudo. A comparação atual é `DRAFT/PENDING`, propõe F01 e ainda não registra uma seleção em `state/` nem `APPROVED_FOR_BIM`.

O estudo usa `PLANAR_PLACEHOLDER`, sem topografia e sem norte real. Solar e ventilação estão como `HEURISTIC`, sem simulação física. O compilador foi exercitado em `CONCEPT_ONLY` até R04. F01 tem **779,2601 m²** brutos, abaixo do piso de 783 m²; F02 tem **1.269,3525 m²**, acima do teto de 814 m². A validação atual não avalia essa faixa como trava automática, portanto os números não significam aprovação.

### Bloqueado ou sem prova

Ainda não há RVT de produção final, massing físico dos finalistas, reabertura a frio do arquivo da Amanda, QA R14 completo, candidato R15, pacote IFC/PDF/DWG validado nem `GOLDEN-001`. Também não foram provados em produção estrutura, instalações, custo, segurança operacional, acessibilidade normativa ou desempenho ambiental físico.

Os portões atuais são:

1. O crosswalk de nomes tem duas lacunas declaradas: `create_grid` e `create_roof` estão sem entrada registrada. A rota foi encontrada, mas não está cadastrada para esses dois nomes.
2. O campo de build nas entradas do catálogo registra `20260716_1515(x64)`, enquanto o build vivo/metadata do Revit é `27.2.0.39`. Essa identificação precisa ser reconciliada antes de promover capacidade.
3. Há **zero capacidades com escopo `PRODUCTION`**. As 11 entradas do catálogo são `PROVIDER`.
4. Faltam dados de terreno/site: topografia, limite, ocupação, frentes e norte.

O preflight também registra que nenhum teste marcado `revit` foi coletado e que não há rota de fallback completa para cada capacidade requerida. Por isso o veredito continua: **STUDY congelado / PRODUCTION NO-GO**.

## Próximos 3 passos mais úteis

1. Fazer P06-T14 em documento descartável de laboratório e obter a prova completa de salvar, fechar, reabrir, exportar e conferir hashes.
2. Fechar os portões de nomes e build, provar `WRITE → READ → VERIFY` no escopo correto e então executar P08-T08/P08-T09 como estudo, mantendo a escolha claramente delegada e pendente de revisão.
3. Fornecer e validar topografia, limite cadastral, ocupação, número de frentes e norte verdadeiro; depois revalidar o modelo e seguir P08-T10 até P08-T19.

## Registro desta análise

Foram lidos o plano combinado da raiz, os dez planos em `docs/superpowers/plans/`, `state/task-graph.yaml`, `PROJECT_STATE.yaml`, `state/status.md`, `state/blockers.yaml`, `docs/reports/p08-preflight.md`, a v9 anterior, o handoff v7, `state/capabilities.yaml`, o crosswalk semântico, o metadata do Revit e a comparação atual dos finalistas.

Foi criado somente este arquivo: `docs/notes/2026-09-16-o-que-falta-simples-v10.md`. Nenhum arquivo de estado, plano, grafo, código, Revit ou MCP foi alterado. Não houve commit nem push; o checkout já estava sujo por trabalho anterior. Para retomar, usar este documento junto com `state/task-graph.yaml` e executar o primeiro passo autorizado, mantendo `STUDY` separado de produção.
