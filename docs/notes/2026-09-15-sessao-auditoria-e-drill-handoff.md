# Handoff — sessão de auditoria dos planos, limpeza local e drill P06-T14

Data: 2026-09-15 (sessão da noite).
Pedido do dono: "crie um subagent para analisar os planos e me dizer de forma
simples o que falta", com as regras permanentes: só subagentes LUNA; nada pago
ou premium; Revit em uso; apagar da pasta local o que não é mais necessário.

## Subagentes LUNA usados (agent_type luna = gpt-5.6-luna xhigh)

1. Auditoria adversarial dos planos (01a0a7a2-4a61-7bd3-9d96-6293d03716fe,
   "Galileo") — somente leitura. Confirmou o retrato e apontou correções e
   lacunas que a nota anterior omitia.
2. Consolidação de notas + preflight do drill (01a0a7b3-af20-75d0-ad8c-963a83babcdb,
   "Sartre").
3. Fechamento das lacunas P05 (CLI/journal/E2E) (01a0a7b3-b038-78b3-bd46-65a9499e4d16,
   "Heisenberg").
4. Harness do drill de release (01a0a7a7-395e-7062-b960-4ba26b892fd8, "Planck").

## Resultado da auditoria (retrato confirmado)

- 159 tarefas: 136 PASS, 2 PASS_WITH_WARNINGS (P02-T17, P08-T01), 13 PENDING,
  8 SUSPENDED, 0 BLOCKED literal.
- PENDING: P06-T14; P08-T08..P08-T19. SUSPENDED: P07-T17, P07-T19,
  P09-T03..P09-T05, P09-T07..P09-T09.
- Último PASS: P08-T07. Próxima oficial: P06-T14. READY: P06-T14 e P08-T08.
- AUSENTES confirmados: bim/releases/GOLDEN-001/, revit/production/working/
  AMANDA_WORKING_001.rvt, solutions/finalists/comparison.md,
  tool-lab/reports/bim-compiler-e2e.md, BIM_PLAN.md/json.

### Correções à nota anterior

- O Revit 2027 está instalado e em uso; faltam os RVTs de produção.
- P08-T08 também está READY; P06-T14 é só a próxima oficial.
- P07-T17 também está SUSPENDED (não apenas P07-T19).
- A análise ambiental dos finalistas é HEURISTIC, não simulação ambiental.
- PROJECT_STATE.yaml traz blockers: [] contra os 5 bloqueios de
  state/blockers.yaml (divergência registrada, não corrigida nesta sessão).

### Lacunas que a nota não citava

- P05-T07/T22/T23 estão PASS mas faltam BIM_PLAN.md/json, CLI bim claim/
  record-result, journal durável e o relatório E2E
  (docs/superpowers/plans/05-bim-compiler.md:157-176,371-410).
- P08-T09 ainda precisa comparison.md, seleção única APPROVED_FOR_BIM e
  approval_hash; selected_design segue nulo.

## Achado crítico desta sessão (P06-T14 bloqueado por terreno, não por código)

O add-in Horizun está carregado e o pipe \.pipeHorizun-30736 existe, mas
toda chamada ao MCP responde "Error: no Revit is reachable" desde ~21:26
(repr. às 21:44 e 21:52). O Revit PID 30736 segue vivo e Responding=True.

Leitura do journal do Revit (journal.0017.txt):

- 20:39:54 — TaskDialog_Project_Not_Saved_Recently respondido "Salvar o projeto";
- 20:57 e 21:41 — "License Idle: Enter" repetidos;
- 21:19 e 21:26 — pares de Register/Unregister DialogBoxShowing + FailuresProcessing
  sem qualquer chamada de ferramenta entre eles.

Interpretação: o ping-pong vem do lado do Revit (sessão inativa/licença em idle e
diálogo de salvamento), não do transporte. O processo responde à janela, mas não
atende o add-in dentro de um timeout de ~1 s.

Ação necessária do dono (não posso clicar): clicar em Revit (PID 30736) para
trazê-lo ao primeiro plano e responder ao diálogo pendente de salvar/não salvar.
Enquanto isso, a prova física do P06-T14 (salvar, fechar, reabrir a frio e
exportar IFC/PDF/DWG reais) fica BLOCKED, e o grafo não foi reescrito para PASS.

## P06-T14 — o que ficou provado e o que não

- Provado (harness sintético): scripts/bim_release_drill.py com 6 testes verdes —
  QA R14, sequência de persistência, exports com validadores, manifest com
  hashes, promoção R16 e rejeição assertada de segunda promoção. O harness é
  deliberadamente local e NÃO inicia Revit nem MCP (declarado no --help).
- NÃO provado (físico): salvar/fechar/reabrir o Revit, exports reais via
  horizun_export, hash do RVT real e a promoção do GOLDEN de laboratório.
  P06-T14 permanece PENDING no grafo.

## Limpeza local (pedido do dono)

- scripts\cleanup-local.ps1 -Apply, duas passagens: 11 __pycache__ na primeira,
  4 alvos (2,2 MB: .mypy_cache, .ruff_cache, .pytest_cache, .tmp-luna-p05-journal-red)
  + 13 __pycache__ na segunda. Estado final: remaining scratch=0 pycache=0.
- Peso atual da pasta: vendor 354 MB (fontes do Horizun/RevitCortex, gitignorado
  e exigido pelo build), .dotnet 770 MB (SDK de build, gitignorado), tool-lab 172 MB
  (quase tudo tool-lab/environmental 160 MB), .git 27 MB, docs 55 MB,
  revit 100 MB (RVTs de laboratório).
- Nada foi apagado fora do que o script já cobre; os candidatos pesados são
  reconstruíveis mas ativos, então ficam para uma decisão explícita do dono.

## Testes

- .\.venv\Scripts\python.exe -m pytest tests/unit/test_bim_release_drill.py -q
  -> 6 executados, 6 passaram, 0 falharam (verificado de forma independente
  pelo agente principal, não só pelo worker).
- A suíte ampla não foi rodada nesta sessão; a última medida conhecida é
  792 passed, 1 failed (test_topologic_spike.py, falha externa de PyPI).

## GitHub

- Commit abe34c2 "feat: add synthetic release drill" no main, push feito pelo
  worker do drill (scripts/bim_release_drill.py, tests/unit/test_bim_release_drill.py).
- Segue sujo (não commitado): PROJECT_STATE.yaml, src/amanda_agent/bim/providers/
  horizun.py, state/status.md, state/task-graph.yaml, state/task-history.yaml,
  tests de bim, tool-lab/topologic/results/topologic-spike.json (reescrito pela
  suíte ampla) e os arquivos novos de docs/notes, scripts/bim_lab_drill.py,
  src/amanda_agent/bim/{lab_fixture,runner}.py.

## Pendências e retomada exata

1. Dono: trazer o Revit 30736 ao primeiro plano e responder ao diálogo pendente.
2. Agente: confirmar get_document_info; se responder, executar a parte física do
   P06-T14 no RVT de laboratório (salvar -> fechar -> reabrir -> re-QA -> exports
   IFC/PDF/DWG -> manifest -> GOLDEN R16 -> assertar rejeição).
3. Agente: reconciliar state/status.md (painel diz PHASE_02 e P08-T07 READY) com
   o grafo; registrar PROJECT_STATE com blockers ativos; fechar as lacunas P05
   reportadas pelos workers; restaurar tool-lab/topologic/results/topologic-spike.json
   antes do próximo commit.
4. Só depois: P08-T08 (massas conceituais) em paralelo com P06-T14.
