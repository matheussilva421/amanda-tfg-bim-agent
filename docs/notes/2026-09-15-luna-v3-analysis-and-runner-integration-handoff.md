# Handoff — análise simples (LUNA v3) e integração da ponte BIM

Data: 2026-09-15. Sessão: pedido do dono "crie um subagent para analisar os planos e me dizer de forma simples o que falta", além de "não pagar nada" e "apagar o que não é mais necessário".

## O que foi feito nesta sessão

1. Subagente LUNA XHIGH (nickname Pascal, id 01a0a769-96df-76b1-aed1-93d76c222d97) analisou os planos, o grafo e o estado vivo e produziu a nota simples:
   - `docs/notes/2026-09-15-o-que-falta-luna-v3.md` (13 PENDING confirmadas: P06-T14 e P08-T08..P08-T19; 8 SUSPENDED; 2 PASS_WITH_WARNINGS).
   - Gaps de entrega provados por rg: `BIM_PLAN.md/json` ausente (P05-T07); `bim claim`/`bim record-result` + journal ausentes (P05-T22); `tool-lab/reports/bim-compiler-e2e.md` ausente (P05-T23); `solutions/finalists/comparison.md` ausente (P08-T07 registrou `MISSING`).
2. Três subagentes LUNA XHIGH do bloco anterior concluíram e foram integrados:
   - A1 runner: `src/amanda_agent/bim/runner.py`, `src/amanda_agent/bim/lab_fixture.py`, `scripts/bim_lab_drill.py`, `tests/unit/test_bim_runner.py`, handoff `docs/notes/2026-09-15-bim-runner-bridge-handoff.md`.
   - A2 readback markless em `src/amanda_agent/bim/providers/horizun.py` (level/grid/room agora têm leitura independente; wall_opening segue `readback_verified=False` com erro tipado), testes em `tests/unit/test_bim_horizun_invoker.py`, handoff `docs/notes/2026-09-15-horizun-markless-readback-handoff.md`.
   - A3 P08-T07: `design-engine/runs/AMANDA-RUN-001/environmental-pass.json` + `.md`, teste `tests/unit/test_p08_t07_environmental_pass.py`, handoff `docs/notes/2026-09-15-p08-t07-environmental-pass-handoff.md`. Registrado PASS, revision 152.

## Testes executados (pai, após integração)

- Gate focado: `pytest tests/unit/test_bim_runner.py tests/unit/test_bim_horizun_invoker.py tests/integration/test_bim_synthetic_compile.py -q` -> 62 passed, 0 failed.
- Suíte ampla: `pytest tests -m "not revit and not slow" -q` -> 792 passed, 1 failed (test_topologic_spike.py, `.venv-topologic` offline; falha pré-existente e conhecida).
- O teste Topologic reescreve `tool-lab/topologic/results/topologic-spike.json`; o arquivo foi restaurado byte a byte a partir do HEAD (diff vazio confirmado com `git diff --quiet`).

## Limpeza local (pedido do dono)

- `scripts/cleanup-local.ps1 -Apply`: removidos 19 + 1 alvos e 41 direórios `__pycache__` (~1,72 GB + basetemps). `remaining scratch=0 pycache=0` fora dos venvs.
- Preservados: `.venv`, `.venv-topologic` (376 MB, exigido pelo teste spike), `.venv-environmental` (451 MB, exigido por `tool-lab/environmental`), `.dotnet`, `vendor/`, `revit/lab`, `state/`, `docs/`, evidências.
- `__pycache__` restantes (1646) estão todos dentro de `.venv*`; o script deliberadamente não os toca.

## Estado vivo

- Revit 2027 PID 30736 vivo, build 27.2.0.39; `permission_profile=full_write`; writer lease FREE; 5 blockers de site (3 BLOCKING, 2 DEGRADING).
- Próximas READY: `P06-T14` e `P08-T08`. Painel `state/status.md` regenerado com `amanda_agent status` (Next P06-T14, Last PASS P08-T07).
- Nada pago/premium foi usado ou autorizado; APS/Forge permanece NO-GO.

## Git

- Commit/push NÃO executados: `git add/commit` fora do sandbox foi rejeitado 5x pelo auto-review (erro de provedor 400 "response_format type is unavailable"), e dentro do sandbox `.git` é read-only (index.lock Permission denied). Nenhum workaround foi tentado.
- Comandos para o dono rodar:

```powershell
cd "C:\Users\slvma\Downloads\Github\Projeto Amanda"
git add -- state/status.md PROJECT_STATE.yaml state/task-graph.yaml state/task-history.yaml src/amanda_agent/bim/providers/horizun.py src/amanda_agent/bim/runner.py src/amanda_agent/bim/lab_fixture.py scripts/bim_lab_drill.py tests/unit/test_bim_runner.py tests/unit/test_bim_horizun_invoker.py tests/integration/test_bim_synthetic_compile.py tests/unit/test_p08_t07_environmental_pass.py design-engine/runs/AMANDA-RUN-001/environmental-pass.json design-engine/runs/AMANDA-RUN-001/environmental-pass.md docs/notes/
git commit -m "feat: add BIM execution runner bridge, markless readback and environmental pass"
git push
```

## Próximo passo

`P06-T14` (ensaio sintético R14-R16) usando a ponte nova: `scripts/bim_lab_drill.py` com `--execute` no laboratório, QA R14, RC em caminho novo, hash, fechar/reabrir a frio, exports IFC/PDF/DWG, manifest e prova de rejeição de sobrescrita do GOLDEN. Antes: conferir writer lock, saúde do provedor e alvo permitido.
