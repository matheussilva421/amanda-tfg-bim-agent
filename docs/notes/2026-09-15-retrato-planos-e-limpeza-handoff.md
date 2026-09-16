# Handoff - retrato dos planos + limpeza local

Data: 2026-09-15
Escopo: atendimento ao pedido "crie um subagent para analisar os planos e me dizer
de forma simples o que falta", com as correcoes do dono (nada pago; Revit em uso;
limpeza da pasta local).

## O que foi feito

1. Subagente LUNA (xhigh) em modo leitura executou o retrato dos planos e do estado
   vivo (grafo, status, PROJECT_STATE, planos 06/08/09, notas anteriores). Nada foi
   escrito pelo subagente; ele foi fechado apos o resultado.
2. Retrato salvo em docs/notes/2026-09-15-o-que-falta-simples-v3.md.
3. Limpeza local: "scripts\cleanup-local.ps1 -Apply" -> 0 alvos scratch e
   9 diretorios __pycache__ removidos; remaining scratch=0 pycache=0.
4. Verificacao viva do Revit (read-only): processo Revit PID 30736, build 27.2.0.39,
   documento aberto LAB_R01_TEMPLATE.rte (revit/lab/probe), 3230 elementos.

## Confirmacoes de estado (fatos)

- Nada pago/premium foi instalado ou usado: APS/Forge NO-GO, Blender/render adiado.
- HEAD na branch main acompanhando origin/main; ha alteracoes nao commitadas de
  blocos anteriores (ver "git status" abaixo).
- Writer lease em state/locks/revit-writer.lock: inexistente (FREE) na ultima checagem.

## Status do Git no momento do handoff

Modificados: PROJECT_STATE.yaml, src/amanda_agent/bim/providers/horizun.py,
state/status.md, state/task-graph.yaml, state/task-history.yaml,
tests/integration/test_bim_synthetic_compile.py, tests/unit/test_bim_horizun_invoker.py,
tool-lab/topologic/results/topologic-spike.json (reescrito pela suite ampla).
Nao rastreados: scripts/bim_lab_drill.py, src/amanda_agent/bim/lab_fixture.py,
src/amanda_agent/bim/runner.py, tests/unit/test_bim_runner.py,
tests/unit/test_p08_t07_environmental_pass.py, notas de docs/notes/2026-09-15-*,
design-engine/runs/AMANDA-RUN-001/environmental-pass.{json,md}.

## Testes

- Nenhum teste executado neste bloco (analise + limpeza apenas).
- Ultima suite ampla registrada: pytest tests -m "not revit and not slow" -q ->
  792 passed, 1 failed (tests/unit/test_topologic_spike.py, falha externa de PyPI).

## Pendencia imediata

Restaurar tool-lab/topologic/results/topologic-spike.json com "git restore --" antes
do proximo commit, ou aceitar a versao regerada conscientemente.

## Proximo passo

P06-T14 - Synthetic R14-R16 release drill. Ver docs/superpowers/plans/06-qa-release-exports.md
(Task 14) e state/task-graph.yaml (P06-T14). Envolve fechar e reabrir o Revit a frio,
por isso a execucao deve ser anunciada ao dono antes de comecar.
