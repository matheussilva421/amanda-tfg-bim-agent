# Handoff — análise LUNA dos planos + limpeza local (2026-09-15)

Escopo do turno: pedido do dono "crie um subagent para analisar os planos e me
dizer de forma simples o que falta", com as restrições "só utilize subagents
LUNA XHIGH", "não quero pagar nada / nada premium" e "apagar o que não é mais
necessário". Nenhuma gravação BIM neste turno.

## O que foi feito

1. Subagente LUNA XHIGH (agent_type `luna` = gpt-5.6-luna xhigh, id
   `01a0a788-f1d9-7dc2-bfe2-63baa98a3ad1`, apelido do sistema McClintock)
   analisou os planos canônicos, os child plans, o grafo de tarefas e o estado
   vivo, em modo estritamente somente-leitura. Nenhum arquivo foi alterado por
   ele. Agente fechado depois do uso.
2. Reconferência viva do pai: Revit 2027 PID 30736 vivo, build 27.2.0.39,
   documento aberto `revit/lab/probe/LAB_ROUTE_PROBE.rvt` (3749 elementos);
   Horizun 1.3.3 HEALTHY, contract_hash `8b9600f5274d7dffb6e5bd5f`,
   `permission_profile=full_write`; writer lease FREE (sem `state/locks`).
3. Suíte ampla medida duas vezes ao vivo: `pytest tests -m "not revit and not
   slow" -q` -> 792 passed, 1 failed. A única falha é a conhecida e externa de
   `tests/unit/test_topologic_spike.py` ("Could not fetch data from PyPI"), já
   documentada em turnos anteriores.
4. Limpeza local: `scripts\cleanup-local.ps1 -Apply` removeu 3 alvos
   (.tmp-repro-check 318,61 MB, .tmp-turn-baseline 318,58 MB, .tmp-live) e 29
   diretórios `__pycache__` (~637 MB). Estado final: `remaining scratch=0
   pycache=0`.

## Contagens vivas do grafo

- 159 tarefas: 136 `PASS`, 2 `PASS_WITH_WARNINGS` (`P02-T17`, `P08-T01`),
  13 `PENDING`, 8 `SUSPENDED`, 0 `BLOCKED`.
- `PENDING`: `P06-T14`; `P08-T08`..`P08-T19`.
- `SUSPENDED`: `P07-T17`, `P07-T19`, `P09-T03`..`P09-T05`, `P09-T07`..`P09-T09`.
- Nota: a contagem do subagente diverge em 1 (ele leu 13 `PENDING` e 136
  `PASS`; a nota v2 deste mesmo dia registrou 14 `PENDING` / 135 `PASS`).
  A divergência está em `P08-T07`, que passou a `PASS` na revision 152. O
  grafo vivo é a fonte; a contagem do subagente bate com o grafo atual.
- `state/blockers.yaml`: 3 `BLOCKING` (`SITE_TOPOGRAPHY`, `SITE_BOUNDARY`,
  `SITE_OCCUPANCY`) + 2 `DEGRADING` (`SITE_FRONTAGE_COUNT`, `SITE_TRUE_NORTH`).

## Lacunas de entrega confirmadas por leitura

- Ausentes: `bim/releases/GOLDEN-001/`, `revit/production/working/AMANDA_WORKING_001.rvt`,
  `solutions/finalists/comparison.md`, `tool-lab/reports/bim-compiler-e2e.md`.
- `P05` (compilador BIM) tem lacunas de entrega além das tarefas pendentes:
  `BIM_PLAN.json/.md`, `bim claim`/`bim record-result` e o journal E2E.

## Arquivos criados/alterados

- criado: este handoff.
- removidos (não rastreados, derivados): `.tmp-repro-check`, `.tmp-turn-baseline`,
  `.tmp-live` e 29 `__pycache__`.
- nenhum arquivo rastreado foi alterado por este turno.

## Problema encontrado (precisa de decisão do dono)

- `tool-lab/topologic/results/topologic-spike.json` está modificado em relação
  ao HEAD. Causa: a suíte ampla reescreve esse relatório de evidência (comportamento
  conhecido, já registrado no handoff anterior). O HEAD permanece intacto.
- A tentativa de restaurar com `git restore -- tool-lab/topologic/results/topologic-spike.json`
  foi recusada pelo auto-review com erro de provedor (400
  `response_format type is unavailable now`), não por veredito de risco. Nenhum
  workaround foi tentado.
- Ação recomendada antes do próximo commit: rodar o restore acima (ou decidir
  conscientemente commitar a versão regerada).

## Decisões técnicas

- Subagente LUNA mantido somente-leitura para não colidir com o estado vivo nem
  com o lock do Revit.
- Nada pago/premium usado, instalado ou autorizado neste turno. APS/Forge segue
  `NO-GO` (P09-T06); Blender/render segue `DEFERRED_OPTIONAL` (P09-T01).

## Próximo passo

`P06-T14` (definida em `docs/superpowers/plans/06-qa-release-exports.md`):
ensaio sintético R14->R16 no Revit de laboratório usando a ponte nova
(`scripts/bim_lab_drill.py --execute`), QA R14, RC em caminho novo, hash,
fechar/reabrir a frio, exports IFC/PDF/DWG, manifest e prova de rejeição de
sobrescrita do GOLDEN. Antes de escrever: conferir writer lease, caminho alvo e
saúde do provedor; cada gravação exige releitura independente.
