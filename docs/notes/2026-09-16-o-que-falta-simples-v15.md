# O que falta para o projeto terminar — v15

Data da leitura: 2026-09-16.

## Onde estamos

- O grafo tem 159 tarefas: 136 `PASS`, 3 `PASS_WITH_WARNINGS`, 12 `PENDING`, 8 `SUSPENDED` e 0 `FAIL`.
- A próxima tarefa é `P08-T08`; a última fechada foi `P06-T14`; a revisão do estado é 155. `PROJECT_STATE.yaml` está em `GO_WITH_LIMITATIONS`.
- O registro do dia confirma Revit 2027 no build `27.2.0.39`, Horizun 1.3.3 saudável, perfil `full_write` e o documento de laboratório `LAB_ROUTE_PROBE.rvt`.
- O estudo tem duas finalistas, F01 e F02, com 626 m² internos e 260 m² externos. A seleção ainda está vazia.
- Ainda não existe modelo de produção Amanda nem pacote `GOLDEN` de produção. O terreno continua provisório.

Fontes: `state/status.md:5-65`, `PROJECT_STATE.yaml:1-19`, `docs/notes/2026-09-16-p06-t14-release-drill-e-rota-stdio-handoff.md:7,46-47`, `state/revit-metadata.json:10,16-21,29`, `design-engine/runs/AMANDA-RUN-001/run.json:48,84-85`.

## O que já está pronto

- **Base e fontes:** estrutura do projeto, estado persistente, grafo de dependências e conferência das 23 fontes atuais. Não há fonte Amanda mais nova registrada. (`state/task-graph.yaml:2323-2337`)
- **Estudo:** programa congelado para 20 pessoas; foram geradas e refinadas duas alternativas, F01 e F02; a análise ambiental existente é heurística. (`state/task-graph.yaml:2367-2419`)
- **Laboratório Revit:** build exato detectado; o Horizun está registrado como ponte principal, com caminho de escrita, leitura independente e salvar/reabrir provados em arquivos descartáveis. (`state/bim-environment.lock.yaml:24-53`)
- **Release de laboratório:** o ensaio sintético R14→R16 fechou com manifesto, exportações, persistência e recusa de sobrescrita; ficou com aviso porque não é um RVT Amanda validado no Revit real. (`state/task-graph.yaml:1975-1995`)
- **Decisões opcionais:** renderização Blender foi adiada e APS ficou fora do escopo por enquanto; isso não bloqueia o caminho local. (`state/task-graph.yaml:2528-2679`)

## O que falta

A lista completa do grafo é: `PENDING` = `P08-T08` a `P08-T19`; `SUSPENDED` = `P07-T17`, `P07-T19`, `P09-T03`, `P09-T04`, `P09-T05`, `P09-T07`, `P09-T08` e `P09-T09`. (`state/task-graph.yaml:2229-2296,2420-2527,2566-2679`)

1. **P08-T08 — massas conceituais de F01 e F02.**
   - **O que é:** criar uma massa Revit separada para cada finalista, em `CONCEPT_ONLY`, somente nos estágios R01→R04, conferindo medidas, preview e salvar/fechar/reabrir.
   - **Por que importa:** é a primeira prova do estudo dentro do Revit e libera a escolha formal.
   - **O que trava:** a tarefa ainda não tem evidência; o plano exige registrar cada conferência e não avançar para produção. Existem duas finalistas, embora o título diga “top 3”. O cruzamento sem entrada registrada para grids precisa ser resolvido se a massa usar essa operação.
   - **Depende do dono:** não, para a execução técnica. (`state/task-graph.yaml:2420-2428`, `docs/superpowers/plans/08-amanda-production-run.md:136-145`, `state/providers/semantic-crosswalk.yaml:24-28`)

2. **P08-T09 — escolha formal.**
   - **O que é:** comparar F01/F02, escolher uma solução, gravar `APPROVED_FOR_BIM`, hash, versões e `AMANDA_REVIEW_PENDING`.
   - **Por que importa:** só uma solução pode seguir para o modelo detalhado.
   - **O que trava:** depende de P08-T08; `selected_design` ainda está vazio e `solutions/finalists/comparison.md` não foi encontrado no registro atual.
   - **Depende do dono:** não para a seleção técnica delegada; sim para a revisão acadêmica posterior. (`state/task-graph.yaml:2429-2437`, `PROJECT_STATE.yaml:18`, `design-engine/runs/AMANDA-RUN-001/environmental-pass.md:43-45`, `docs/superpowers/plans/08-amanda-production-run.md:149-166`)

3. **P02-T17 — quatro casos reais ainda não provados.**
   - **O que é:** testar em RVTs descartáveis ID inválido, família/tipo inexistente, elemento hospedado sem host e lote com item inválido, sempre com chamada real e nova leitura.
   - **Por que importa:** evita falso sucesso e mostra como o agente se recupera de erro antes de tocar produção.
   - **O que trava:** a tarefa está `PASS_WITH_WARNINGS`, mas só 4 de 8 casos passaram; 4 seguem `SKIPPED_NEEDS_REVIT`.
   - **Depende do dono:** não para a parte técnica; depende de uma sessão Revit de laboratório disponível. (`state/task-graph.yaml:791-835`, `docs/superpowers/plans/02-revit-tool-lab-providers.md:516-531`)

4. **P07-T17 — retomada em sessão nova.**
   - **O que é:** fechar a prova em uma sessão Codex realmente nova, lendo o estado e identificando a próxima tarefa sem reconstruir o histórico.
   - **Por que importa:** prova que o trabalho continua depois de uma conversa terminar.
   - **O que trava:** a simulação na mesma sessão não vale como aceite; o grafo deixou a tarefa `SUSPENDED` com protocolo apenas preparado.
   - **Depende do dono:** sim, para iniciar/abrir a sessão nova quando necessário. (`state/task-graph.yaml:2229-2249`, `docs/superpowers/plans/07-autonomy-recovery-security.md:348-357`)

5. **P07-T19 — retomada após reinício.**
   - **O que é:** executar a prova após reinício autorizado, conferindo estado, saúde do provedor, checkpoint e nova leitura.
   - **Por que importa:** cobre a perda de sessão do Windows/Revit.
   - **O que trava:** nenhum reinício real foi feito; a tarefa continua `SUSPENDED`.
   - **Depende do dono:** sim, para autorizar e executar o reinício. (`state/task-graph.yaml:2277-2296`, `docs/superpowers/plans/07-autonomy-recovery-security.md:372-383`)

6. **P08-T01 — liberação da produção.**
   - **O que é:** fechar o preflight com provas de runtime no escopo exato, rotas de recuperação e evidência `PRODUCTION`.
   - **Por que importa:** um provider saudável no laboratório não prova que todas as operações estão prontas para o modelo Amanda.
   - **O que trava:** continua `PASS_WITH_WARNINGS`; há 11 capacidades `PASS`, mas todas estão em `evidence_scope: PROVIDER`, com 0 em `PRODUCTION`. O preflight também registrou ausência de teste Revit marcado e rotas de fallback incompletas.
   - **Depende do dono:** não para a análise e execução técnica; pode exigir ação dele na janela Revit. (`state/task-graph.yaml:2297-2322`, `state/capabilities.yaml:5-201`, `docs/reports/p08-preflight.md:16-18`)

7. **P08-T10 a P08-T14 — modelo de produção e documentação.**
   - **O que é:** criar o RVT de trabalho e compilar R01→R13: projeto, terreno, níveis, massa, paredes, ambientes, acessibilidade, mobiliário, paisagismo, materiais e documentação.
   - **Por que importa:** transforma a escolha em um modelo verificável e documentado.
   - **O que trava:** depende de P08-T09 e da liberação de P08-T01; exige lease, alvo seguro, `WRITE → READ → VERIFY` e checkpoint em cada etapa. `revit.create_grid` e `revit.create_roof` continuam sem `registered_entry`, embora suas rotas estejam descritas como provadas; não se deve adivinhar um nome substituto.
   - **Depende do dono:** não para a execução técnica. (`state/task-graph.yaml:2438-2482`, `docs/superpowers/plans/08-amanda-production-run.md:170-229`, `state/providers/semantic-crosswalk.yaml:24-45`)

8. **P08-T15 a P08-T17 — QA, candidato e exportações.**
   - **O que é:** fazer QA R14, criar RC R15, reabrir a frio e validar IFC, PDF, DWG, PNG, tabelas, páginas, hashes e relatórios.
   - **Por que importa:** mostra se o modelo realmente abre, permanece correto e gera os arquivos de entrega.
   - **O que trava:** todas estão `PENDING` e dependem do modelo R13; o ensaio sintético anterior não substitui essa prova real.
   - **Depende do dono:** não para a execução; revisão visual e aceitação acadêmica podem exigir o dono. (`state/task-graph.yaml:2483-2509`, `docs/superpowers/plans/08-amanda-production-run.md:233-271`)

9. **P08-T19 e depois P08-T18 — pacote e GOLDEN.**
   - **O que é:** preparar o pacote final, conferir caminhos e hashes, e só então promover o R16 para um novo `GOLDEN-001`.
   - **Por que importa:** fecha a entrega técnica com proveniência, relatórios e proteção contra sobrescrita.
   - **O que trava:** P08-T19 depende de P08-T17; P08-T18 depende de P08-T19, QA, persistência, exportações e versões fixadas. Nenhuma tem evidência ainda.
   - **Depende do dono:** não para a montagem técnica; autoria, apresentação e aceitação acadêmica continuam humanas. (`state/task-graph.yaml:2510-2527`, `docs/superpowers/plans/08-amanda-production-run.md:275-317`)

10. **P09-T03, P09-T04 e P09-T05 — Blender.**
    - **O que é:** registrar Blender, testar a ferramenta e montar a renderização.
    - **Por que importa:** só se houver necessidade real de render externo.
    - **O que trava:** a necessidade foi adiada; não há registro Blender, laboratório executado, arquivo `.blend` ou render. Não bloqueia a produção Revit.
    - **Depende do dono:** não agora; sim se o requisito de render for reaberto. (`state/task-graph.yaml:2566-2615`, `docs/superpowers/plans/09-optional-render-cloud.md:58-110`)

11. **P09-T07, P09-T08 e P09-T09 — APS.**
    - **O que é:** auditar, proteger credenciais e testar a rota cloud.
    - **Por que importa:** seria uma alternativa para uma capacidade local comprovadamente bloqueada.
    - **O que trava:** o gate APS deu `NO-GO`: não há capacidade local `BLOCKED_BY_TOOL` e a rota paga ficou fora do escopo. Não bloqueia o caminho local.
    - **Depende do dono:** sim, se um dia houver autorização explícita para login, upload e custo. (`state/task-graph.yaml:2639-2683`, `docs/superpowers/plans/09-optional-render-cloud.md:111-155`)

12. **Dados do terreno e normas.**
    - **O que é:** obter topografia com datum, polígono cadastral com coordenadas, ocupação/realocação, número de frentes, norte verdadeiro e aplicabilidade normativa.
    - **Por que importa:** sem isso não há declaração final segura de declividade, acessibilidade altimétrica, área, disponibilidade, recuos e orientação.
    - **O que trava:** `SITE_TOPOGRAPHY`, `SITE_BOUNDARY` e `SITE_OCCUPANCY` são `BLOCKING`; `SITE_FRONTAGE_COUNT` e `SITE_TRUE_NORTH` são `DEGRADING`; `REGULATION_APPLICABILITY` está `PENDING_VERIFICATION`. O estudo planar provisório pode continuar, mas a validação final fica parada.
    - **Depende do dono:** sim, para fornecer fonte verificável ou obtê-la com o órgão responsável; o agente registra e valida. (`state/blockers.yaml:3-115`, `project/site/missing-data.yaml:4-102`, `project/requirements/decision-register.yaml:192-211`)

13. **Entregas acadêmicas.**
    - **O que é:** concluir caderno, visitas/levantamento, metaprojeto, estudo preliminar, anteprojeto, pranchas, memoriais, defesa, autoria e submissão.
    - **Por que importa:** o projeto técnico pronto não encerra o TFG.
    - **O que trava:** há 10 itens `PENDING` e 1 `PROVISIONAL`; todos exigem ação humana e são obrigatórios para `TFG_COMPLETE`.
    - **Depende do dono:** sim. (`project/requirements/academic-deliverables.yaml:6-151`)

## O que só o dono pode fazer

- Conferir na tela do Revit qual arquivo está ativo e clicar em diálogos de permissão quando aparecerem.
- Abrir uma sessão nova e autorizar o reinício real necessário para P07-T17/P07-T19.
- Fornecer ou obter os documentos verificáveis do terreno e confirmar a ocupação/realocação.
- Revisar a escolha arquitetônica e validar o material para uso acadêmico.
- Fazer visitas, autoria, defesa e submissão institucional.
- Fazer login ou autorizar serviço externo somente se uma necessidade de render/cloud for aprovada.

## Números do grafo

| Item | Valor | Fonte |
| --- | ---: | --- |
| PASS | 136 | CLI `task-graph`; `state/status.md:10-24` |
| PASS_WITH_WARNINGS | 3 | CLI `task-graph`; `state/task-graph.yaml:1975-1982,2297-2305` |
| PENDING | 12 | CLI `task-graph`; `state/task-graph.yaml:2420-2527` |
| SUSPENDED | 8 | CLI `task-graph`; `state/task-graph.yaml:2229-2296,2566-2679` |
| FAIL | 0 | CLI `task-graph` |
| Próxima tarefa | P08-T08 | `PROJECT_STATE.yaml:8-10` |
| Revisão | 155 | `PROJECT_STATE.yaml:19` |

## Divergências e coisas desatualizadas que você achou

- **v14:** `docs/notes/2026-09-16-o-que-falta-simples-v14.md:15` dizia que `state/status.md` apontava para P06-T14; hoje ele aponta para P08-T08 (`state/status.md:10`). A mesma linha do v14 citava HEAD `d20dc44`; o HEAD atual é `2cc501e` (`state/status.md:65`, `git log -1`).
- **Plano mestre:** `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md:9` e `docs/superpowers/plans/00-master-implementation-plan.md:11` dizem “implementation and Revit acceptance NOT_RUN”. Isso precisa separar as duas coisas: a implementação e o laboratório de providers já têm provas; a aceitação Revit em produção ainda não foi feita. A regra de não usar essa prova de laboratório como produção continua correta.
- **Registro Git incompleto:** `PROJECT_STATE.yaml:9` e `state/status.md:64` ainda dizem `last_verified_commit: NOT_RECORDED`, embora o Git esteja alinhado em `2cc501e`. O valor deveria ser registrado após uma verificação formal; não alterei esse arquivo nesta análise.
- **Preflight histórico:** `docs/reports/p08-preflight.md:11-22` registra revisão 123, próxima tarefa P06-T01 e checkout sujo. É um retrato antigo da execução do preflight, não o estado atual; não deve ser usado para substituir o dashboard.
- **Alteração observada no dashboard:** o Git estava limpo no início; durante as leituras permitidas, `state/status.md:65` passou de `d20dc44` para `2cc501e`. O diff contém somente essa linha; não alterei manualmente esse arquivo e não o reverti.
- **Documento Revit:** a nota do dia registra `LAB_ROUTE_PROBE.rvt` (`docs/notes/2026-09-16-p06-t14-release-drill-e-rota-stdio-handoff.md:46-47`), mas o snapshot `tool-lab/horizun/introspection/health-now.json:227-238` mostra `LAB_R00_EMPTY`. Antes de qualquer escrita, o arquivo ativo precisa ser conferido novamente.
- **Arquivo de comparação:** o v14 tratava a comparação como DRAFT; o registro atual informa que `solutions/finalists/comparison.md` não foi encontrado (`design-engine/runs/AMANDA-RUN-001/environmental-pass.md:43-45`).

Esta leitura não executou pytest, escrita no Revit, `git add`, commit ou push. O arquivo criado por mim é este v15; o estado final também contém a alteração observada em `state/status.md` descrita acima.

## Próximos 5 passos concretos

1. O dono confirma na tela o documento Revit ativo e deixa uma janela descartável segura para a prova; resolver a divergência `LAB_ROUTE_PROBE`/`LAB_R00_EMPTY` antes de escrever.
2. Executar `P08-T08` para F01 e F02 em `CONCEPT_ONLY`, com medidas, preview, salvar/fechar/reabrir e registro das ferramentas usadas.
3. Criar a comparação atual e concluir `P08-T09`, gravando uma única escolha `APPROVED_FOR_BIM` com revisão da Amanda pendente.
4. Fechar os quatro casos reais de `P02-T17`, completar as duas lacunas do crosswalk e concluir P07-T17/P07-T19; depois atualizar o preflight de produção.
5. Com os dados do terreno e o preflight liberado, executar P08-T10→P08-T19 na ordem segura, mantendo as entregas acadêmicas humanas em paralelo.
