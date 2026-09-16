# P08-T07 — Environmental finalist pass

Status: PASS no escopo do passe heurístico; sem simulação ambiental detalhada.

## Concluído

- Avaliados os dois finalistas disponíveis de `AMANDA-RUN-001` (limite do plano: 5) com `evaluate_environmental_heuristics`.
- Valores usados: `true_north_deg=0.0` como `PLANAR_PLACEHOLDER` porque `site.true_north` é nulo; Leste `90.0°` como preferência solar de permanência prolongada; Sudeste `135.0°` como referência de vento de projeto.
- Como os finalistas não têm azimute de fachada, taxa de abertura ou exposição ao vento, os defaults do avaliador (`0.0`, `0.5`, `1.0`) foram registrados como fallback, sem serem tratados como medições.
- Resultado igual nos dois: solar `0.5`, ventilação `0.3055456351736995`, total ponderado reequilibrado `0.7888960184315897`.
- Confirmada a ausência de capability de simulação ambiental em `state/capabilities.yaml`; `SITE_TRUE_NORTH` continua `DEGRADING` em `state/blockers.yaml`.
- `solutions/finalists/comparison.md` não existe; a ausência foi registrada no JSON.

## Arquivos

- `design-engine/runs/AMANDA-RUN-001/environmental-pass.json`
- `design-engine/runs/AMANDA-RUN-001/environmental-pass.md`
- `tests/unit/test_p08_t07_environmental_pass.py`

## Testes

- RED: `./.venv/Scripts/python.exe -m pytest tests/unit/test_p08_t07_environmental_pass.py -q --basetemp=.tmp-luna-p08-t07-red -p no:cacheprovider` — 1 falha esperada: artefato ausente.
- GREEN: `./.venv/Scripts/python.exe -m pytest tests/unit/test_p08_t07_environmental_pass.py tests/solver/test_environmental_heuristics.py -q --basetemp=.tmp-luna-p08-t07-green2 -p no:cacheprovider` — 3 passaram, 0 falharam.
- Gate design: `./.venv/Scripts/python.exe -m pytest tests/unit/test_p08_t07_environmental_pass.py tests/unit/test_design_cli.py tests/unit/test_design_refine.py tests/solver tests/regression/test_fixture_courtyard.py -q --basetemp=.tmp-luna-p08-t07-design -p no:cacheprovider` — 79 passaram, 0 falharam.
- Gate final após `advance`: mesmo subconjunto com `--basetemp=.tmp-luna-p08-t07-final` — 79 passaram, 0 falharam.

## Limitações e retomada

Não há prova de CFD, Radiance, iluminância, ganhos solares, velocidades de vento, conforto anual, orientação cadastral, topografia ou desempenho físico em campo. O passe deve permanecer rotulado `HEURISTIC`. Não foram executados comandos Git por instrução do worker.

## Advance

Comando autorizado: `./.venv/Scripts/python.exe -m amanda_agent advance --task P08-T07 --status PASS --evidence "environmental-pass.json/md: 2 finalistas HEURISTIC; solar=0.5; ventilation=0.3055456351736995; weighted=0.7888960184315897; 79 design tests passed; no environmental simulation capability; SITE_TRUE_NORTH DEGRADING"`

Saída exata:

```text
recorded     P08-T07 PASS
next task    P06-T14
revision     152
```
