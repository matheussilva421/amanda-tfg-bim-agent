# O que falta para o projeto terminar — v14

Data da leitura: 2026-09-16.

## Onde estamos

- O grafo vivo tem 159 tarefas: 136 `PASS`, 3 `PASS_WITH_WARNINGS`, 12 `PENDING`, 8 `SUSPENDED` e 0 `FAIL`.
- `PROJECT_STATE.yaml` registra `last_completed_task: P06-T14`, `next_task: P08-T08` e `state_revision: 155`.
- P06-T14 fechou o ensaio sintético R14→R16 com 71 artefatos e 26 testes focados registrados; ele ainda não é uma prova feita no Revit real.
- Revit 2027 está vivo no build `27.2.0.39`; o Horizun 1.3.3 está saudável, com `full_write` e contrato `8b9600f5274d7dffb6e5bd5f`.
- O documento aberto registrado é `revit/lab/probe/LAB_ROUTE_PROBE.rvt`, com 3749 elementos; `LAB_R01_TEMPLATE.rte` não está confirmado como aberto.
- Há 11 capacidades `PASS`, 0 `FAIL` e 0 `UNTESTED`, mas todas têm `evidence_scope: PROVIDER`; `PRODUCTION` = 0.
- Existem duas finalistas, F01 e F02; `selected_design` continua vazio, não há RVT de produção e não há `bim/releases`.

O `state/status.md` está atrasado. Ele ainda diz `next task: P06-T14` e mostra o HEAD antigo `abe34c2`. O estado usado aqui é `PROJECT_STATE.yaml` + `state/task-graph.yaml`; para Git, a leitura atual mostra worktree limpo, `main...origin/main` em `0/0` e HEAD `d20dc44`. A primeira leitura desta sessão mostrou dezenas de arquivos sujos, como já informado pelo dono. A segunda leitura, mais recente, não mostra alterações não commitadas. O aviso antigo de worktree sujo em P08-T01 precisa ser rechecado.

O cabeçalho do plano combinado ainda diz que implementação e aceitação Revit estão `NOT_RUN`. Isso está desatualizado para a base de código e para o laboratório dos provedores. Continua correto para a aceitação de produção: o que falta é provar o caminho no uso previsto. O plano combinado continua sendo a fonte das exigências; o grafo e o estado vivo mandam no status das tarefas.

## O que falta, em ordem

1. **P08-T08 — massas conceituais das finalistas.** Falta gerar as massas de F01 e F02 em `CONCEPT_ONLY`, nos estágios R01→R04, com conferência de medidas, preview e salvar/fechar/reabrir; o plano fala em até três, mas só há duas finalistas. Quem faz: agente/IA. Tamanho: G. Hoje: pronto para iniciar no estudo, mas o `semantic-crosswalk` ainda deixa `revit.create_grid` sem entrada registrada, o que bloqueia o PASS completo dessa etapa até o agente fechar essa lacuna.

2. **P08-T09 — escolha formal.** Falta registrar uma única solução como `APPROVED_FOR_BIM`, com hash e versões vinculadas; a comparação existente recomenda F01, mas continua `DRAFT/PENDING` e F01/F02 têm a mesma nota porque o orçamento bruto não foi avaliado como critério. Quem faz: agente/IA; Amanda revisa depois. Tamanho: M. Hoje: bloqueado pela conclusão de P08-T08; a revisão da Amanda não é uma espera obrigatória enquanto a delegação continuar válida.

3. **P02-T17 — quatro casos reais da matriz de falhas.** Faltam testar em RVTs descartáveis o ID inválido, família/tipo inexistente, elemento hospedado sem host e lote com item inválido, sempre com chamada real e reconsulta independente. Quem faz: agente/IA. Tamanho: M. Hoje: pronto para execução em laboratório quando a janela Revit for usada; os quatro casos seguem `SKIPPED_NEEDS_REVIT`.

4. **P07-T17 e P07-T19 — retomada entre sessões.** Falta provar a retomada em uma sessão Codex realmente nova e, separadamente, após um reinício autorizado, com saúde do provedor, checkpoint e reconsulta. Quem faz: agente/IA; o dono autoriza o reinício real. Tamanho: M. Hoje: P07-T17 está bloqueado pela exigência de uma sessão nova; P07-T19 está bloqueado até existir a janela de reinício autorizada.

5. **P08-T01 — liberar produção.** Falta transformar o `PASS_WITH_WARNINGS` em uma decisão de produção sustentada por testes runtime no escopo exato, rotas de fallback, crosswalk fechado e evidência `PRODUCTION`; hoje há 0 capacidades nesse escopo. Quem faz: agente/IA, com dados externos quando necessário. Tamanho: G. Hoje: bloqueado para produção; o estudo planar pode continuar.

6. **P08-T10 a P08-T14 — modelo de produção e documentação.** Falta criar o RVT de trabalho e compilar R01→R13, com lease, alvo seguro, leitura independente, conferência e checkpoint a cada etapa. Quem faz: agente/IA. Tamanho: G. Hoje: bloqueado por P08-T09 e pela liberação de produção de P08-T01.

7. **P08-T15 a P08-T17 — QA, candidato e exportações.** Faltam QA R14, RC R15 com reabertura fria e validação de IFC, PDF, DWG, PNG, páginas, hashes e relatórios. Quem faz: agente/IA; revisão visual humana entra quando a entrega exigir. Tamanho: G. Hoje: bloqueado até existir o modelo R13.

8. **P08-T19 — pacote final.** Falta montar e conferir o pacote completo, a proveniência, os relatórios e o status dos entregáveis acadêmicos antes da promoção. Quem faz: agente/IA, com validações humanas de autoria e apresentação. Tamanho: G. Hoje: bloqueado por P08-T17.

9. **P08-T18 — promoção R16.** Falta publicar um novo `GOLDEN-001` somente depois do pacote, QA, persistência, exportações e hashes; o caminho de release não pode ser sobrescrito. Quem faz: agente/IA. Tamanho: G. Hoje: bloqueado por P08-T19 e pelas provas de produção.

10. **Dados do terreno e normas.** Faltam topografia com datum, polígono cadastral com sistema de coordenadas, confirmação de ocupação/realocação, contagem de frentes, norte verdadeiro e aplicabilidade normativa verificada. Quem faz: Amanda, órgão responsável ou fonte externa; o agente registra e valida. Tamanho: G. Hoje: bloqueado até os dados existirem; o estudo provisório continua permitido.

11. **Entregas acadêmicas.** Faltam caderno, visitas/levantamento, metaprojeto, estudo preliminar validado, anteprojeto, pranchas, memoriais, defesa, autoria e submissão institucional. Quem faz: Amanda, com validação acadêmica. Tamanho: G. Hoje: bloqueado para declarar `TFG_COMPLETE`; pode avançar em paralelo ao estudo técnico.

## Travado e por quê

### 1. Bloqueio por dado externo real

- `SITE_TOPOGRAPHY` é `BLOCKING`: sem cotas e datum não há declividade, drenagem ou acessibilidade altimétrica final.
- `SITE_BOUNDARY` é `BLOCKING`: 24.135 m² é uma área informada, não um limite legal conferido.
- `SITE_OCCUPANCY` é `BLOCKING`: falta confirmar o uso atual e a premissa de realocação da unidade policial.
- `SITE_FRONTAGE_COUNT` é `DEGRADING`: o material ainda diverge entre três e quatro frentes.
- `SITE_TRUE_NORTH` é `DEGRADING`: falta azimute ou desenho com norte verdadeiro.
- `REGULATION_APPLICABILITY` continua `PENDING_VERIFICATION` no registro de decisões. Não é um dos cinco blockers principais do YAML, mas impede afirmações normativas finais.

Esses dados não devem ser preenchidos com estimativas. Eles bloqueiam verificações finais, mas permitem um estudo planar identificado como provisório.

### 2. Bloqueio por decisão ou dependência do dono

- `P07-T19` requer uma janela real e autorizada de reinício. Este turno não deve simular esse evento.
- As visitas, o levantamento, a autoria, a defesa e a submissão acadêmica dependem de Amanda.
- A revisão de Amanda em `P08-T09` é necessária para a aceitação acadêmica, mas não impede a seleção delegada e o desenvolvimento técnico enquanto essa delegação permanecer válida.

### 3. Bloqueio que o próprio agente ainda pode destravar

- `P07-T17` pode ser encerrado em uma sessão Codex nova, seguindo o protocolo registrado.
- `P02-T17` pode fechar os quatro casos restantes em arquivos descartáveis do laboratório.
- O agente pode completar o crosswalk de `revit.create_grid` e `revit.create_roof` somente com nomes e evidências reais, sem adivinhar ferramentas.
- O agente pode atualizar o preflight de `P08-T01` depois dessas provas e separar claramente `PROVIDER` de `PRODUCTION`.
- Depois de P08-T08, o agente pode converter a comparação DRAFT em uma seleção formal em `P08-T09`, preservando a revisão posterior de Amanda.

## Próximos 3 passos executáveis hoje

1. Conferir o estado Git mais recente:

```powershell
git status --short --branch; git log -1 --oneline
```

Resultado esperado: `## main...origin/main`, nenhuma linha de alteração e HEAD `d20dc44` ou um commit posterior identificado.

2. Ler o próximo ponto do grafo:

```powershell
& '.venv\Scripts\python.exe' -X utf8 -m amanda_agent.cli task-graph
```

Resultado esperado: 159 tarefas, `P08-T08` como próxima tarefa, `P06-T14` em `PASS_WITH_WARNINGS`, 0 `FAIL` e 12 `PENDING`.

3. Conferir o estado BIM antes de qualquer execução:

```powershell
& '.venv\Scripts\python.exe' -X utf8 -m amanda_agent.cli bim status --project-root .
```

Resultado esperado: lease livre, seleção ainda não registrada, estágio e checkpoint não registrados, e nenhum RVT de produção declarado.

## O que NÃO falta

- A estrutura do projeto, o grafo de dependências, o controle de estado, o compilador BIM e os contratos de segurança já existem.
- A ingestão e reconciliação da fonte atual estão concluídas; não há fonte Amanda mais nova registrada.
- A base escolhida é a de 20 pessoas, com 626 m² internos e 260 m² externos; não é preciso reabrir essa decisão para voltar a 42 pessoas.
- O laboratório já provou o provedor Horizun e tem rota stdio funcional; o ambiente vivo é Revit 2027 com Horizun 1.3.3.
- O ensaio sintético de release R14→R16 já tem artefatos, manifesto, exportações sintéticas e recusa de sobrescrita; ele não precisa ser refeito como se estivesse pendente.
- F01 e F02 já têm JSON, geometria, fluxos, métricas, previews 2D e comparação; falta a massa Revit e a seleção formal.
- Blender e APS não são necessários agora. A rota APS permanece fora de escopo e sem custo.

## Riscos e limites

O escopo `STUDY` aceita a área planar provisória, hipóteses marcadas e seleção delegada ao agente. Isso permite avançar com as massas conceituais. O estudo não confirma lote, topografia, norte, norma, custo, estrutura, instalações ou aprovação institucional.

O escopo de produção exige alvo seguro, provedor testado para a operação, `WRITE → READ → VERIFY`, checkpoints, reabertura fria e exportações conferidas. Hoje o catálogo ainda tem escopo `PROVIDER` em todas as 11 entradas, e `P08-T01` continua com veredito de produção não liberado. O `GOLDEN` sintético do laboratório é evidência da cadeia de release, não um modelo Revit de Amanda.

O plano combinado exige até três massas, mas o run atual tem apenas F01 e F02. F01 fica abaixo da faixa estimada de 783–814 m² fechados, e F02 ultrapassa essa faixa; o código atual não usa esse bruto para separar as notas. A escolha precisa conservar essa limitação no registro.

Um `GOLDEN` técnico não conclui o TFG. O caderno, as visitas, o levantamento, as pranchas, os memoriais, a defesa, a autoria e a submissão institucional são trabalho acadêmico de Amanda e precisam de produção e validação humanas.

Esta análise somente leu o estado e os artefatos. Não executou Revit/MCP, pytest, instalação, `git add`, commit ou push. A única escrita prevista nesta atualização é este documento.
