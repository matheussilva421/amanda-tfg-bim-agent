# Handoff P05-T17 a P05-T21 — R09 a R13

Data: 2026-09-15  
Agente: Artemis (LUNA XHIGH)  
Escopo: acessibilidade, mobiliário, paisagismo, materiais e documentação  
Status: `IMPLEMENTADO_OFFLINE`; desired-state e preflight testados; runtime Revit `NOT_RUN`

## Resumo

Foram implementados cinco estágios puros em `src/amanda_agent/bim/stages/`. Cada
estágio produz `DesiredState`/`StageOperation`, seleciona capability pelo
`PreflightRequest` com build, schema e escopo exatos, e despacha somente por
`StageToolInvoker` injetado. Nenhum módulo importa bridge do Revit.

- P05-T17 / R09: grafo de rota desde a entrada, rotas, rampas/patamares,
  larguras de circulação, vagas e sanitários acessíveis. Parâmetros ausentes
  ficam como `STATUS_NAO_VERIFICADO`; regras numéricas só entram de linhas
  `VERIFIED` com `numeric_value` e `source_refs`. `compliance_claim_allowed`
  permanece sempre falso. `FINAL` é recusado quando falta regra, medição ou
  conectividade da rota.
- P05-T18 / R10: placeholders funcionais determinísticos por setor/espaço,
  incluindo quarto, dining, psicologia/técnico, escritório e área infantil.
  Família e tipo são obrigatórios e vêm de catálogo controlado; a capacidade
  do programa é limitada a 20 pessoas.
- P05-T19 / R11: cinco zonas externas padrão somam exatamente 260 m²
  (80 + 80 + 30 + 30 + 40), cada uma com desired elements de piso externo,
  vegetação, mobiliário externo e sombreamento, além da zona programada.
  Privacidade e adjacência são propriedades explícitas. Estratégia oeste só é
  aceita com `approved_design_option=True`.
- P05-T20 / R12: cada atribuição exige material registrado, tipo compatível,
  `source_ref`, justificativa e `design_intent`. Nomes duplicados no catálogo,
  tipos divergentes e materiais sem procedência são recusados.
- P05-T21 / R13: registry determinístico de plantas de situação/pavimento/
  cobertura, quatro seções por relação arquitetônica, elevações, quatro tabelas
  mínimas, folhas, viewports, cotas e etiquetas.

Todos os cinco estágios aceitam `external_elements` e um `external_planner`
callable para incorporar elementos de modelo vinculado, Toposolid, norte
verdadeiro ou georreferenciamento sem criar `external.py` nem inventar dados.

## Arquivos criados

- `src/amanda_agent/bim/stages/accessibility.py`
- `src/amanda_agent/bim/stages/furniture.py`
- `src/amanda_agent/bim/stages/landscape.py`
- `src/amanda_agent/bim/stages/materials.py`
- `src/amanda_agent/bim/stages/documentation.py`
- `tests/unit/test_stage_accessibility.py`
- `tests/unit/test_stage_furniture.py`
- `tests/unit/test_stage_landscape.py`
- `tests/unit/test_stage_materials.py`
- `tests/unit/test_stage_documentation.py`
- este handoff

Não foram alterados `stages/__init__.py`, `external.py`, catálogos externos,
`PROJECT_STATE.yaml`, `state/task-graph.yaml` ou arquivos de outros agentes.

## TDD e validação

RED observado antes da implementação: cada alvo falhou na coleta com
`ModuleNotFoundError` para o módulo de estágio ausente.

GREEN focado por task:

- `& './.venv/Scripts/python.exe' -m pytest tests/unit/test_stage_accessibility.py -q -p no:cacheprovider --basetemp=.tmp-pytest-artemis-t17-green3-0915a`: 5 passed.
- `& './.venv/Scripts/python.exe' -m pytest tests/unit/test_stage_furniture.py -q -p no:cacheprovider --basetemp=.tmp-pytest-artemis-t18-green3-0915a`: 4 passed.
- `& './.venv/Scripts/python.exe' -m pytest tests/unit/test_stage_landscape.py -q -p no:cacheprovider --basetemp=.tmp-pytest-artemis-t19-green3-0915a`: 5 passed.
- `& './.venv/Scripts/python.exe' -m pytest tests/unit/test_stage_materials.py -q -p no:cacheprovider --basetemp=.tmp-pytest-artemis-t20-green3-0915a`: 4 passed.
- `& './.venv/Scripts/python.exe' -m pytest tests/unit/test_stage_documentation.py -q -p no:cacheprovider --basetemp=.tmp-pytest-artemis-t21-green3-0915a`: 3 passed.

Validação final executada com `$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m ...`:

- testes atribuídos juntos: 21 passed, 0 failed;
- `tests/unit` excluindo apenas `test_checkpoint_label_is_r01_project_initialized`: 450 passed, 1 skipped, 1 deselected;
- `tests/project tests/policy`: 29 passed, 0 failed;
- `ruff check` nos dez arquivos do escopo: passou;
- `ruff format --check` nos dez arquivos do escopo: 10 arquivos já formatados;
- `mypy` nos cinco módulos de produção: `Success: no issues found`;
- `compileall` nos cinco módulos: exit 0.

A execução integral de `tests/unit` também foi feita. O resultado foi 448
passed, 1 skipped e 1 failed em
`test_checkpoint_label_is_r01_project_initialized`: o teste cria uma pasta
`checkpoints`, enquanto a alteração pré-existente em `src/amanda_agent/bim/checkpoints.py`
rejeita esse componente como alvo protegido. O diff confirma que
`checkpoints.py`, `test_stage_project.py` e outros arquivos relacionados são de
outros agentes; esse teste foi somente deselecionado na matriz final para
isolar a evidência deste write set. Nenhuma correção foi aplicada fora do
escopo autorizado.

## Validação manual e limites

Os testes usaram doubles `RecordingInvoker` e queries independentes sintéticas;
confirmaram despacho por estágio, IDs, propriedades, famílias/tipos,
procedência, relacionamentos e detecção de divergência. Não houve abertura,
mutação, save/reopen ou leitura independente de um documento Revit nesta
tarefa. Portanto, o resultado é `OFFLINE_READY`, não aceitação de provider nem
prova de execução em Revit.

O registro local de acessibilidade continua sem números NBR inventados: uma
fonte pública e gratuita, a regra numérica verificada e a medição geométrica
devem ser fornecidas ao planner/regulation registry antes de qualquer perfil
`FINAL`.

## GitHub e estado de retomada

Por instrução explícita da delegação, não foram executados `git add`, `commit`,
`push`, `checkout`, `reset` ou `advance`. O working tree compartilhado permanece
com alterações de outros agentes e os cinco módulos/testes/handoff acima
estão não rastreados neste momento. O orquestrador deve fechar P05-T17 a
P05-T21 usando os arquivos e números de teste deste documento.

Para retomar:

1. preservar todos os arquivos não relacionados e conferir novamente o estado
   do writer/ambiente antes de qualquer BIM write;
2. fornecer o `external_planner`/`external.py` do agente responsável e as
   entradas externas desejadas;
3. carregar o registry de capabilities para R09–R13 no build/schema/escopo
   exatos;
4. executar cada `plan_*_stage` em fixture ou documento descartável;
5. despachar somente após preflight e fazer READ→VERIFY independente para cada
   operação; registrar checkpoint apenas para o escopo concluído;
6. manter R09 como `STATUS_NAO_VERIFICADO`/`BLOCKED_BY_INPUT` enquanto faltarem
   medição e regra numérica verificadas.
