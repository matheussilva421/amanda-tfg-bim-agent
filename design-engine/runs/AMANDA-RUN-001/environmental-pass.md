# P08-T07 — Environmental finalist pass

Run: `AMANDA-RUN-001`  
Classificação: `HEURISTIC`  
Método: `evaluate_environmental_heuristics`  
Finalistas avaliados: 2 de até 5

## Entradas e procedência

| Entrada | Valor usado | Procedência e tratamento |
| --- | ---: | --- |
| `true_north_deg` | `0.0°` | `project/site/site.json` informa `true_north: null`; `project/site/missing-data.yaml` e `state/blockers.yaml` mantêm `SITE_TRUE_NORTH`. O valor é somente `PLANAR_PLACEHOLDER`, sem representar norte verdadeiro. |
| `preferred_solar_orientation_deg` | `90.0°` | Leste convertido de E para 90° a partir do TFG, PDF p. 69, que considera o sol matinal favorável para dormitórios e permanência prolongada; também registrado em `P03-T09-SP-008`. |
| `wind_direction_deg` | `135.0°` | Sudeste convertido de SE para 135° a partir da diretriz de projeto registrada em `docs/review/...__01_textos_prontos_para_colar.docx.txt:P41`. O PDF p. 66 registra vento diurno predominante de Nordeste e vento noturno de Leste/Sudeste; por isso 135° é uma referência heurística de projeto, não média anual medida. |
| orientação de fachada | `0.0°` | Os dois `solution.json` não têm `facade_orientation_deg` nem `orientation_deg`; foi aplicado o default do avaliador e marcado como `EVALUATOR_DEFAULT`. |
| `opening_ratio` | `0.5` | Ausente nos dois finalistas; default do avaliador, sem schedule de esquadrias. |
| `wind_exposure` | `1.0` | Ausente nos dois finalistas; default do avaliador, sem modelo de obstrução/rugosidade. |

O teste de capability confirmou que não há capability ambiental de simulação registrada em `state/capabilities.yaml`. Assim, o workflow detalhado não foi executado e todos os resultados abaixo permanecem `HEURISTIC`.

## Métricas cruas e ponderadas

Os pesos são os congelados em `design-engine/config/weights.yaml`, versão 1. O total abaixo inclui as 11 dimensões porque solar e ventilação agora têm valores; cada contribuição já é `valor cru × peso`.

| Finalista | Solar cru (`HEURISTIC`) | Ventilação crua (`HEURISTIC`) | Solar ponderado | Ventilação ponderada | Total ponderado reequilibrado |
| --- | ---: | ---: | ---: | ---: | ---: |
| `AMANDA-RUN-001-F01` | 0.500000 | 0.305546 | 0.030000 | 0.018333 | 0.788896 |
| `AMANDA-RUN-001-F02` | 0.500000 | 0.305546 | 0.030000 | 0.018333 | 0.788896 |

As demais dimensões cruas, preservadas do passe P08-T06, são iguais nos dois finalistas: `program_compliance=1.000000`, `privacy_security=0.500000`, `adjacency=0.941591`, `circulation=0.833333`, `accessibility=1.000000`, `green_integration=1.000000`, `compactness=0.061416`, `constructability=1.000000` e `concept_fidelity=1.000000`. Os totais anteriores, com as duas dimensões ambientais ausentes e excluídas, eram `0.8415491821831452`.

O JSON contém as contribuições ponderadas completas por finalista, os hashes das geometrias e a evidência do avaliador.

## Limitações explícitas

- O resultado é `HEURISTIC` em todos os campos ambientais. Não há resultado `SIMULATED`.
- Não houve CFD, Radiance, análise de iluminância, cálculo de ganhos solares, velocidades de vento, conforto adaptativo ou desempenho anual.
- `SITE_TRUE_NORTH` está `DEGRADING`; a entrada `true_north_deg=0.0` é apenas `PLANAR_PLACEHOLDER` porque o site não fornece azimute verificável.
- Os finalistas não possuem azimute de fachada, taxa de abertura ou exposição ao vento. Os defaults `0.0`, `0.5` e `1.0` pertencem ao contrato do avaliador e não são medições do projeto.
- A fonte registra variação do vento entre dia e noite. A escolha de Sudeste representa uma referência de projeto documentada e não uma série anemométrica.
- A geometria é um plano local de estudo; o passe não prova orientação cadastral, topografia, implantação final nem desempenho físico em campo.

## Matriz comparativa

`solutions/finalists/comparison.md` não existe neste checkout. A matriz não foi atualizada; a ausência está registrada em `environmental-pass.json` para o próximo passe que for responsável pela comparação.
