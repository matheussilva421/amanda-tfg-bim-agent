# Handoff — subagente LUNA V4 e reconciliação de estado

Data: 2026-09-15. Continuação da sessão de auditoria + drill.

## Pedido do dono neste bloco

Criar um subagente para analisar os planos e dizer de forma simples o que falta.

## O que foi feito

- Subagente LUNA xhigh **Newton** (id `01a0a7c3-06c0-7d63-abc8-abdf04e3b8fd`), escopo read-only
  fechado em dois arquivos. Ele leu os 9 planos de `docs/superpowers/plans/`, o combinado, o
  `START_HERE_FOR_CODEX.md`, `PLAN_SELF_REVIEW.md`, o grafo, o histórico, o `status.md`,
  `state/blockers.yaml`, `PROJECT_STATE.yaml` e as quatro notas antigas.
- Entregáveis do subagente: `docs/notes/2026-09-15-o-que-falta-simples-v4.md` (retrato simples)
  e `docs/notes/2026-09-15-subagente-luna-v4-handoff.md` (handoff da auditoria).
- Ele confirmou 159 Tasks nos planos e 159 IDs no grafo, sem Task órfã de nenhum lado.
- Corrigi, depois de verificar, o único erro factual da nota dele: ele chamou de divergência o
  `7/19 PASS` de PHASE_08 no `state/status.md`. Não é divergência —
  `src/amanda_agent/status_dashboard.py:63` conta `PASS_WITH_WARNINGS` como passed, e PHASE_08
  tem 6 PASS + 1 PASS_WITH_WARNINGS (`P08-T01`). A nota foi corrigida.
- Marquei `docs/notes/2026-09-15-o-que-falta-simples-v3.md` como SUPERSEDED, apontando para a V4.
- Limpeza local (`scripts\cleanup-local.ps1 -Apply`): 7 alvos + 17 `__pycache__` removidos,
  `remaining scratch=0 pycache=0`. Nada de `.venv*`, `vendor/`, `revit/lab` ou `tool-lab` foi tocado.
- Reconciliei o espelho legado de bloqueios: `PROJECT_STATE.yaml` tinha `blockers: []` e agora
  espelha os cinco de `state/blockers.yaml` (`SITE_TOPOGRAPHY:BLOCKING`,
  `SITE_BOUNDARY:BLOCKING`, `SITE_OCCUPANCY:BLOCKING`, `SITE_FRONTAGE_COUNT:DEGRADING`,
  `SITE_TRUE_NORTH:DEGRADING`), gravado via `StateStore.save(..., expected_revision=153)` →
  `state_revision 154`. Nada mais no arquivo mudou.

## Diagnóstico do Revit/MCP (medido neste bloco)

- O Revit 2027 pid 30736 está vivo (iniciado 17:03) com `LAB_R01_TEMPLATE.rte` aberto,
  build `27.2.0.39`, 3230 elementos; o add-in está em `full_write`
  (`C:\Users\slvma\.horizun\settings.json`).
- A rota MCP do app alcança o Revit: `horizun_health` → `healthy` (1.3.3) e
  `get_document_info` → `LAB_R01_TEMPLATE.rte`.
- O transporte stdio do projeto inicia o mesmo binário, mas **toda** chamada responde
  `Error: no Revit is reachable`. Causa medida: o sandbox nega, à identidade que roda o
  processo do projeto, acesso a `C:\Users\slvma\.horizun\discovery\revit-2027-30736.json`
  (`Access to the path ... is denied`; a ACL do diretório pai também é ilegível). Esse arquivo é
  o handshake entre o `horizun-mcp.exe` e o add-in.
- Consequência: `scripts\bim_lab_drill.py --preflight` falha fechado
  (`PROVIDER_UNREACHABLE`, exit 3) dentro do sandbox, o que é o comportamento correto. A metade
  física de `P06-T14` e `P08-T08` fica BLOCKED até o processo do projeto rodar fora desse
  sandbox. Registrei isso em `state/status.md` (horizun = `REACHABLE_FROM_APP_ONLY`).
- Escalação para rodar fora do sandbox foi recusada pelo auto-review com **erro de provider
  (400 `response_format type is unavailable now`)**, não por veredito de risco. O mesmo vale para
  `git add`/commit/push e `Remove-Item`. Isso está pendente para o dono.

## Testes executados

- `pytest tests/unit/test_bim_cli_journal_contract.py tests/unit/test_bim_lab_drill_preflight.py
  tests/unit/test_bim_runner.py tests/unit/test_p08_t07_environmental_pass.py
  tests/unit/test_bim_horizun_invoker.py -q` → 74 passed, 0 failed.
- `pytest tests/unit/test_state_store.py tests/unit/test_state_models.py
  tests/unit/test_state_persistence_roundtrip.py tests/unit/test_advance_cli.py -q` →
  28 passed, 0 failed (valida a reconciliação de estado).
- `pytest tests -m "not revit and not slow" -q` → **810 passed, 1 failed**. A falha é
  `tests/unit/test_topologic_spike.py::test_topologic_spike_measures_space_and_persists_json_report`,
  pré-existente e externa ao bloco: o script roda em `.venv-topologic` e falha ao resolver
  dependência (sem rede no sandbox). Esse teste reescreve
  `tool-lab/topologic/results/topologic-spike.json` e apaga o bloco `assessment`; restaurei o
  arquivo do blob do HEAD — conferido por hash, `3890efa4638b14d49eed182dea0634da74db064a` igual
  nos dois lados.

## Estado do Git

- HEAD `abe34c2` em `main`, `main...origin/main` sincronizado.
- **Nada foi commitado neste bloco.** O commit está pronto em conteúdo mas bloqueado: `git add`
  exige escrita em `.git`, que o sandbox não permite, e a escalação foi recusada pelo
  auto-review (erro de provider).
- Pendente de commit: `PROJECT_STATE.yaml`, `state/status.md`, `state/task-graph.yaml`,
  `state/task-history.yaml`, `src/amanda_agent/bim/providers/horizun.py`,
  `src/amanda_agent/commands/bim.py`, `tests/integration/test_bim_synthetic_compile.py`,
  `tests/unit/test_bim_horizun_invoker.py`, além dos novos `scripts/bim_lab_drill.py`,
  `src/amanda_agent/bim/{journal,lab_fixture,runner}.py`, quatro testes novos,
  `tool-lab/reports/bim-compiler-e2e.md`, `design-engine/runs/AMANDA-RUN-001/environmental-pass.*`
  e as notas `docs/notes/2026-09-15-*`.
- `tool-lab/topologic/results/topologic-spike.json` continua aparecendo como `M` apenas por
  cache de stat (blob idêntico ao HEAD); não precisa entrar no commit.

## Pendências e retomada

1. **Ação humana que mais destrava**: autorizar a execução do processo do projeto fora do
   sandbox (ou tornar `C:\Users\slvma\.horizun\discovery\` legível para ele). Sem isso o
   caminho tipado do projeto não fala com o Revit, mesmo com o Revit saudável.
2. Rodar `git add` + `git commit` + `git push` do bloco acima quando a escalação voltar a
   funcionar, ou o dono rodar manualmente.
3. `P06-T14` (drill físico) e `P08-T08` (massas conceituais) continuam PENDING; nenhum PASS foi
   registrado sem evidência física.
4. Depois: `P08-T09` (comparação + seleção única + `approval_hash`) → `P08-T10`..`P08-T19`
   (RVT de produção e `GOLDEN-001`).
5. Os cinco bloqueios do terreno seguem abertos e dependem de dados reais; só travam as quatro
   tarefas finais listadas em `state/blockers.yaml`.

