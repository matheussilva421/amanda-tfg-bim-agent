# Handoff - Fase 07A (autonomia) e inicio da Fase 03 (inteligencia de projeto)

Data: 2026-09-15
Projeto: Amanda TFG BIM Agent
Handoff anterior: docs/notes/2026-09-15-fase-01-fundacao-handoff.md (secoes 2, 7 e 8)
Objetivo canonico: C:\\Users\\slvma\\.codex\\attachments\\bca1fd4d-06ed-4df9-a08f-c9fbc9ae3db2\\goal-objective.md

## 1. Resumo

A pendencia P-1 foi fechada: o PROJECT_STATE deixou de mentir. As treze tarefas da Fase 01 foram registradas como PASS com a saida real dos testes como evidencia, e a fase foi encerrada com gate GO_WITH_LIMITATIONS, abrindo a PHASE_03.

O plano 07A foi iniciado e quatro tarefas estao concluidas e commitadas. A Fase 03 foi iniciada com seis subagentes em paralelo.

## 2. O que foi implementado nesta sessao

### P-1 - reconciliacao do PROJECT_STATE (concluido)

Nao existia nenhum comando capaz de mover o estado, por isso ele continuava em PENDING / P01-T01 depois de treze tarefas implementadas, testadas e commitadas. Foram criados:

- src/amanda_agent/state/advance.py: complete_task, set_phase_gate, complete_phase. Uma tarefa so conclui com evidencia textual e status de desfecho; registry e estado sao gravados na mesma chamada com CAS em state_revision; toda conclusao vai para state/task-history.yaml.
- src/amanda_agent/commands/advance.py: camada de CLI, incluindo run_advance_phase, que se recusa a fechar uma fase que ainda tem tarefas abertas.
- Comandos novos em cli.py: advance, advance-phase, phase-gate, task-graph.
- status passou a mostrar o conjunto READY real do registry de tarefas, e nao apenas a fase grosseira.

Resultado: P01-T01..P01-T13 gravadas PASS com a saida por modulo como evidencia; PHASE_01 fechada com GO_WITH_LIMITATIONS; PHASE_03 aberta em P03-T01; revision 15. Verificado em processo novo: status le de volta PHASE_03 e last task P01-T13.

### P07-T01 - AGENTS.md de producao (concluido)

AGENTS.md na raiz com as catorze regras de producao, protocolo de inicio e de fim de sessao e as skills Superpowers exigidas. Coberto por tests/policy/test_agents_policy.py.

### P07-T02 - grafo de dependencia de tarefas (concluido)

- src/amanda_agent/state/tasks.py: TaskRecord e TaskRegistry. READY exige que toda dependencia dura esteja PASS ou PASS_WITH_WARNINGS; BLOCKED_BY_INPUT propaga somente ao ramo dependente; dependencia desconhecida e ciclo sao rejeitados antes do uso.
- src/amanda_agent/state/build_task_graph.py: deriva state/task-graph.yaml dos planos canonicos. 159 tarefas em PHASE_00..09, com as dependencias de fronteira e explicitas que a prosa apenas sugeria.

### P07-T10 - redacao de seguranca (concluido)

src/amanda_agent/security/redaction.py: mascara tokens bearer, chaves de API, client secrets, senhas, cabecalhos de autorizacao e blocos de chave privada, em payloads estruturados e em texto livre. Preserva tipo de erro, host, codigo HTTP e diagnostico comum. Ha teste provando que o EventLog mascara o segredo antes de persistir e que o arquivo em disco nao contem o token nem a senha.

### P07-T16 - maquina de intervencao humana (concluido)

src/amanda_agent/state/human_gate.py. Sob AGENT_DELEGATED, escolhas rotineiras de tipologia, material, finalista, premissa provisoria de STUDY, pacote ja autorizado pelo modelo de permissao da plataforma e fallback ja testado NAO emitem gate. Emitem gate apenas: UAC, autenticacao/MFA, licenca, dado essencial apos esgotar o caminho de STUDY, selecao arquitetonica (somente se o usuario revogar a delegacao), acao externa irreversivel, custo externo, permissao de plataforma realmente ausente, trabalho nao salvo de terceiros e mudanca material do programa ja selecionado.

O primeiro teste encontrou um excesso de zelo real: um pacote ja autorizado emitia PLATFORM_PERMISSION. A condicao passou a exigir que a permissao esteja de fato ausente.

## 3. Decisoes tecnicas

1. O registry de tarefas e derivado dos planos markdown, com excecoes explicitas codificadas; nao e re-derivado de prosa.
2. Conclusao de tarefa sempre exige evidencia textual. Verde sem prova e recusado pelo proprio codigo.
3. Fechar fase e o momento em que um gate vira afirmacao, entao advance-phase recusa enquanto houver tarefa aberta na fase.
4. Um gate humano carrega o que bloqueia e o que continua: uma fronteira de Revit ou provider para a Fase 02 e tudo que consome provider provado, sem arrastar PHASE_03/04.
5. Over-gating e tratado como defeito, nao como cautela.

## 4. Testes

Comando: .venv\\Scripts\\python.exe -m pytest tests/unit tests/bootstrap tests/policy -q -p no:cacheprovider --basetemp=".tmp-pytest"

- Antes desta sessao: 64 executados, 64 aprovados.
- Ao final deste bloco: 115 executados, 115 aprovados, 0 falhados.
- Novos arquivos de teste: test_task_graph.py (8), test_state_advance.py (9), test_advance_cli.py (13), test_state_persistence_roundtrip.py (4), test_agents_policy.py (1), test_security_redaction.py (4), test_human_gate.py (11).

Os flags -p no:cacheprovider e --basetemp continuam obrigatorios por causa do blocker B-001.

## 5. Git

- 6513932 feat(07A): task dependency graph, evidence-gated advance CLI and Phase 01 reconciliation
- 9adffdb feat(07A): human-intervention gate that knows when NOT to ask

Nenhum remote configurado: o push continua impossivel ate o usuario criar o repositorio. Os commits locais estao em main.

## 6. Em andamento no momento deste handoff

Seis subagentes rodando em paralelo, em areas de escrita disjuntas:

- 07A: P07-T03/T04 (session start e end), P07-T05/T06 (budgets e blockers), P07-T11/T12/T13 (trust, discovery, maintenance).
- Fase 03: P03-T01/T02/T03 (manifest, provenance, ingest), P03-T05/T06/T12 (pdf, requirement models, regulations), P03-T10/T11 (site models e geometria).

As edicoes dos subagentes caem diretamente neste workspace, portanto o commit final deve conferir a suite completa antes de gravar.

## 7. Pendencias

1. B-001 (DEGRADING, acao do usuario): ACLs quebradas em %LOCALAPPDATA%\\Temp\\pytest-of-slvma e .pytest_cache. Reparo exige PowerShell elevado:
   takeown /F "C:\\Users\\slvma\\AppData\\Local\\Temp" /R /D Y
   icacls "C:\\Users\\slvma\\AppData\\Local\\Temp" /reset /T /C
   icacls "C:\\Users\\slvma\\Downloads\\Github\\Projeto Amanda\\.pytest_cache" /reset /T /C
2. Sem remote Git: push impossivel ate o usuario criar o repositorio.
3. Divergencia menor de ambiente: o probe python312 do doctor diz MISSING embora o venv seja 3.12.14. Corrigir o probe ou registrar a divergencia.
4. Wart menor: test_unknown_dependency_and_cycle_are_rejected cobre dependencia desconhecida mas nao assere o ciclo.

## 8. Ainda nao validado (nao declarar como feito)

- Licenca e inicializacao do Revit. O Revit esta DETECTADO (2027, build 20260716_1515, file 27.2.0.39), o que nao prova licenciamento nem inicializacao.
- Nenhum add-in ou MCP Revit instalado. A pasta %APPDATA%\\Autodesk\\Revit\\Addins\\2027 existe e esta vazia.
- Nenhuma modelagem, nenhum RVT, nenhuma exportacao.

## 9. Retomada

    cd "C:\\Users\\slvma\\Downloads\\Github\\Projeto Amanda"
    git log --oneline -4
    .venv\\Scripts\\python.exe -m amanda_agent status
    .venv\\Scripts\\python.exe -m amanda_agent task-graph
    .venv\\Scripts\\python.exe -m pytest tests/unit tests/bootstrap tests/policy -q -p no:cacheprovider --basetemp=".tmp-pytest"

Proximo passo: reconciliar os subagentes em andamento, conferir a suite completa e seguir a Fase 03 (P03-T04 inventario, T07 compilacao do programa de 20 pessoas, T13 suite de integridade de proveniencia, T14 validate-only, T15 registro de decisoes).
