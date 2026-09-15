# Handoff da Fase 01 - Fundacao, ambiente e estado duravel

Data: 2026-09-15
Projeto: Amanda TFG BIM Agent
Status: implementacao local verificada e commitada. Runtime Revit: NOT_RUN.
Handoff anterior (revisao dos planos): docs/notes/2026-09-15-revisao-planos-handoff.md

## 1. Objetivo e autorizacao

O objetivo integral esta registrado em C:\Users\slvma\.codex\attachments\f5c46716-64a7-4ed9-82e5-b3a7c149e76f\goal-objective.md: implementar e executar integralmente o Amanda TFG BIM Agent (pesquisa, ambiente, implementacao, decisoes arquiteturais, modelagem Revit, testes, correcoes, documentacao, exportacoes), sem parar em diagnostico.

O usuario autorizou execucao autonoma completa (selection_authority=AGENT_DELEGATED). A pendencia AMANDA_REVIEW_PENDING nao bloqueia a execucao.

Workspace: C:\Users\slvma\Downloads\Github\Projeto Amanda
Acesso: sistema de arquivos irrestrito (sandbox desativado), rede habilitada, approval policy never.

## 2. Estado verificado ao vivo (2026-09-15)

Git:

- 3162381 chore(repo): initialize Amanda TFG BIM agent repository
- 2d33935 feat: complete Phase 01 foundation, environment and durable state
- Branch main em 2d33935. Nenhum remote configurado (git remote -v vazio): nao houve push.
- 40 arquivos versionados: src 22, tests 13, bootstrap 2, project 1, .gitignore, pyproject.toml.

Testes: 64 executados, 64 aprovados, 0 falhados (6,36s).

doctor (execucao ao vivo, exit code 0):

    git         AVAILABLE git version 2.53.0.windows.3
    codex       AVAILABLE codex-cli 0.154.0-alpha.6.2
    powershell  AVAILABLE 5.1.26100.9444
    python312   MISSING
    dotnet      AVAILABLE 8.0.422
    revit       DETECTED  20260716_1515(x64)  (file 27.2.0.39)

O Python 3.14 esta instalado na maquina; o plano de controle usa o venv fixado em 3.12. Revit esta DETECTADO, o que nao prova licenciamento nem inicializacao bem-sucedida.

status:

- phase PHASE_01 (foundation-environment-state), status PENDING, next task P01-T01, revision 1, writer lease free, 0 blockers.

resume: todas as fases executaveis (PHASE_01 a PHASE_09).

bootstrap (execucao ao vivo) criou/confirmou: PROJECT_STATE.yaml, state/environment-report.json, state/bim-environment.lock.yaml, state/blockers.yaml, state/tool-health.yaml, state/revit-metadata.json. O diretorio state/snapshots/ existe e esta vazio (nenhum backup privado gravado ainda).

Inconsistencia de estado registrada como pendencia P-1: o PROJECT_STATE.yaml permanece com phase_status PENDING, next_task P01-T01, last_completed_task null, last_verified_commit null e state_revision 1, embora P01-T01..T13 estejam implementadas, testadas e commitadas em 2d33935. Ainda nao existe comando para marcar tarefa concluida ou gravar checkpoint; decidir a reconciliacao antes de declarar o gate da Fase 01 fechado.

## 3. O que foi implementado (P01-T01..T13, commit 2d33935)

Nucleo:

- paths.py: caminhos canonicos do projeto.
- redaction.py: redacao de segredos, aplicada na escrita dos logs.
- logging.py: logger JSONL append-only com redacao.
- models/state.py: modelos do estado duravel.
- models/tasks.py: Blocker tipado (severidade como campo explicito, nunca inferida de prefixo de id) e TaskGraph que rejeita dependencia desconhecida e ciclo. Este modulo vive aqui, e nao na fase de autonomia, para que status e resume funcionem desde o inicio.
- program.py: grafo revisado do programa (01 -> 07A -> 02; 01 -> 03 -> 04; (02+04) -> 05 -> 06 -> 07B -> 08; 09 opcional).
- state/store.py: store YAML com escrita atomica (CAS).
- state/locks.py: lease de escritor unico com owner token, pid, start time, host, heartbeat e fencing.

Ambiente:

- bootstrap/get-revit-metadata.ps1: leitura de metadados da instalacao.
- bootstrap/revit.py, bootstrap/environment.py, bootstrap/snapshots.py: deteccao de Revit, sondagem do ambiente e snapshots de configuracao.

Comandos:

- commands/doctor.py: diagnostico; separa o necessario universal (Codex, critico) do especifico de ramo (Revit bloqueia apenas a Fase 02). Exit code reflete falha global.
- commands/status.py e commands/rollback.py.
- commands/bootstrap.py: criacao idempotente do estado duravel.
- cli.py: comandos ligados. Apenas rollback sem --checkpoint retorna exit 2, de proposito.

Tarefas do plano cobertas: T01 a T13 de docs/superpowers/plans/01-foundation-environment-state.md.

## 4. Arquivos criados e alterados

Versionados em 2d33935: pyproject.toml, .gitignore, os 22 arquivos de src/amanda_agent, os 13 arquivos de tests/unit e tests/bootstrap, bootstrap/get-source-inventory.ps1, project/provenance/source-inventory.json.

Nao versionados no momento deste handoff:

- PROJECT_STATE.yaml
- state/ (blockers.yaml, bim-environment.lock.yaml, environment-report.json, revit-metadata.json, tool-health.yaml, snapshots/)
- docs/ (notes, review, superpowers/plans)
- 2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md, 2026-09-11-amanda-tfg-bim-agent-design.md, PLAN_SELF_REVIEW.md, START_HERE_FOR_CODEX.md
- amanda-tfg-bim-agent-planos-REVISADOS-2026-09-15.zip (15 entradas) e amanda-tfg-bim-agent-superpowers-plan.zip (copia parcial dos planos), ambos duplicatas dos documentos ja presentes no repositorio.

Docs privados: docs/review/source-extracts/ esta no .gitignore e nao deve ser publicado.

Artefatos temporarios a limpar: .git-commit-msg.tmp (1.706 bytes) e .tmp-pytest/ (51 entradas, basetemp do pytest).

## 5. Decisoes tecnicas

1. Severidade de blocker e campo tipado, nunca inferida de prefixo de id.
2. O grafo do programa vive em codigo. Bloquear PHASE_02 bloqueia PHASE_05 e nao bloqueia PHASE_03 nem PHASE_04.
3. Expiracao de lease nunca concede posse: so a reclamacao com prova de inatividade no mesmo host, com fencing avancando.
4. Endurecimento de ACL do backup privado e opt-in (harden_acl=False). Uma ACL que quebra heranca e nega o dono e pior que o perfil do usuario e ainda bloqueia a limpeza do pytest.
5. doctor separa o necessario universal do especifico de ramo; o exit code reflete falha global.
6. Backup byte a byte (privado, ignorado) mais resumo redigido (versionado). Redigir o unico backup impediria rollback exato.
7. environment-report.json e diagnostico vivo, atualizado a cada execucao; os arquivos duraveis so sao criados se ausentes.

## 6. Testes e validacoes

Comando:

    .venv\Scripts\python.exe -m pytest tests/unit tests/bootstrap -q -p no:cacheprovider --basetemp=".tmp-pytest"

Resultado: 64 executados, 64 aprovados, 0 falhados. Status: verde (6,36s).

As duas opcoes extras (-p no:cacheprovider e --basetemp) sao obrigatorias hoje por causa do blocker B-001.

Validados tambem por execucao real: doctor, status, resume e bootstrap idempotente.

Nao validado: licenciamento e inicializacao do Revit, instalacao de add-in, qualquer modelagem. Nenhum add-in ou MCP Revit instalado (C:\Users\slvma\AppData\Autodesk\Revit\Addins\2027 existe e esta vazio).

## 7. Problemas encontrados

B-001 (DEGRADING, requer acao do usuario) - ACLs quebradas em diretorios criados sob o sandbox. Verificado ao vivo em 2026-09-15: C:\Users\slvma\AppData\Local\Temp\pytest-of-slvma e .pytest_cache retornam UnauthorizedAccessException. takeown falha por falta de elevacao de token. Reparo exige PowerShell elevado:

    takeown /F "C:\Users\slvma\AppData\Local\Temp" /R /D Y
    icacls "C:\Users\slvma\AppData\Local\Temp" /reset /T /C
    icacls "C:\Users\slvma\Downloads\Github\Projeto Amanda\.pytest_cache" /reset /T /C

O restante de Temp, o repositorio, src, tests, state e .venv foram verificados e estao OK.

B-002 (resolvido) - commit rejeitado por erro 400 do revisor; resolvido apos a desativacao do sandbox.

## 8. Pendencias e proximos passos

1. Gravar e commitar este handoff.
2. Commitar o restante nao versionado (PROJECT_STATE.yaml, state/, docs/, documentos canonicos da raiz e os dois ZIPs).
3. Limpar .git-commit-msg.tmp e .tmp-pytest/, ou ignora-los no .gitignore.
4. Reconciliar o PROJECT_STATE.yaml com a Fase 01 concluida (pendencia P-1 da secao 2).
5. Reconferir project/provenance/source-inventory.json (28 entradas, gerado em 2026-09-15T10:23:44Z) e os SHA-256 canonicos apos o commit final.
6. Gate da Fase 01: pytest completo, doctor, status, git status limpo, nenhum lease obsoleto.
7. Seguir o grafo: 07A (autonomia, recuperacao e seguranca) e 03 (inteligencia de projeto) nao dependem do Revit; 02 (Tool Lab) depende de escritor unico e de ambiente Revit.

## 9. Instrucoes de retomada

    cd "C:\Users\slvma\Downloads\Github\Projeto Amanda"
    git log --oneline -3
    .venv\Scripts\python.exe -m amanda_agent doctor
    .venv\Scripts\python.exe -m amanda_agent status
    .venv\Scripts\python.exe -m amanda_agent resume
    .venv\Scripts\python.exe -m amanda_agent bootstrap
    .venv\Scripts\python.exe -m pytest tests/unit tests/bootstrap -q -p no:cacheprovider --basetemp=".tmp-pytest"

## 10. Avisos

- Nao commitar state/snapshots/private/ nem logs/raw/ (privacidade; ja constam no .gitignore).
- Nao declarar validacao nao ocorrida: o Revit esta detectado, nao licenciado nem inicializado.
- Baseline do programa fixada em 20 pessoas, 626 m2 internos, 260 m2 externos, 783-814 m2 fechados e 850-950 m2 cobertos, conforme o PDF, confirmada por hash no handoff de revisao dos planos e nao por medicao nova.

