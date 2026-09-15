# Handoff P05-T13 a P05-T16 — estágios arquitetônicos

Data: 2026-09-15  
Agente: Daenerys / LUNA XHIGH  
Repositório: `C:\Users\slvma\Downloads\Github\Projeto Amanda`

## Resumo

Foram implementados os planejadores desired-state puros para R05 casca arquitetônica, R06 layout interno, R07 aberturas hospedadas e R08 ambientes. Todos recebem `PreflightRequest`, recusam modos ou capacidades incompatíveis com `StagePreflightError`, montam `DesiredState` sem importar bridge do Revit e encaminham operações somente por `StageToolInvoker` injetado. Cada estágio também possui verificador independente baseado em `verify_write`.

O grafo de tarefas não foi alterado nem avançado. P05-T13, P05-T14, P05-T15 e P05-T16 permanecem `PENDING` para que o orquestrador registre a evidência deste handoff.

## Arquivos deste write set

Criados:

- `src/amanda_agent/bim/stages/shell.py`
- `src/amanda_agent/bim/stages/layout.py`
- `src/amanda_agent/bim/stages/openings.py`
- `src/amanda_agent/bim/stages/rooms.py`
- `tests/unit/test_stage_shell.py`
- `tests/unit/test_stage_layout.py`
- `tests/unit/test_stage_openings.py`
- `tests/unit/test_stage_rooms.py`
- `docs/notes/2026-09-15-p05-architecture-stages-handoff.md`

Removidos: nenhum.

Não foram editados `massing.py`, `external.py` ou arquivos de outros agentes.

## Implementação por tarefa

### P05-T13 / R05 — casca arquitetônica

`plan_shell_stage` e aliases relacionados derivam paredes a partir dos polígonos dos ambientes, deduplicam uma fronteira compartilhada pela chave geométrica estável e conservam a topologia sem paredes coincidentes. Os elementos gerados incluem paredes externas e internas, pisos, lajes e cobertura, com espessura, material, tipo controlado, linha de localização, vínculos de host e IDs de aberturas.

O catálogo padrão controla `EXT_WALL_01` e `INT_WALL_01`. O estágio aceita elementos externos já planejados ou um `external_planner` injetado para o modelo vinculado; não cria `external.py` nem acessa Revit. Os requisitos externos podem ser despachados como desired elements junto com a casca.

O preflight exige as capacidades de criação de parede, piso, laje e cobertura, além de vínculo quando há modelo externo. A verificação reconsulta cada ID e valida unicidade, geometria e propriedades essenciais.

### P05-T14 / R06 — layout interno

`plan_layout_stage` cria divisórias internas deduplicadas a partir das fronteiras compartilhadas dos ambientes, mantendo IDs lógicos e geometria de centro de parede. As relações de `design/adjacency.py` são avaliadas; relação obrigatória que não passa causa recusa tipada. Rotas fornecidas são avaliadas com `design/flows.py` e áreas fora do intervalo declarado são registradas como divergência, sem deformar a geometria.

O preflight exige `revit.create_internal_wall` e a verificação independente confirma os elementos e os resultados de execução do invoker.

### P05-T15 / R07 — aberturas

`plan_openings_stage` gera portas e janelas hospedadas em elementos `WALL`. Cada abertura exige família/tipo existente no catálogo fornecido; ausência causa `OpeningCatalogError`, sem download ou fallback externo. Dimensões são finitas e positivas, portas têm largura livre mínima configurável (padrão `0.80 m`) e duas conexões, e janelas exigem peitoril explícito dentro dos limites configurados.

O estágio rejeita host ausente ou não parede, dimensões inválidas, peitoril omitido ou fora do intervalo e aberturas coincidentes. O preflight exige `revit.create_opening`; a verificação reconsulta host, família, tipo, dimensões, peitoril e vínculos de conectividade.

### P05-T16 / R08 — ambientes

`plan_rooms_stage` usa os setores e espaços do programa canônico, expande quantidades, gera exatamente um ambiente por `logical_id` esperado e numera por setor. Valida geometria, colocação, fechamento, duplicidades e IDs redundantes. A reconciliação conserva a área calculada exata e marca `DIVERGENCE` quando há diferença acima da tolerância; não arredonda nem altera o polígono.

O estágio registra área útil interna, área externa fora do escopo de Rooms e capacidade. Os invariantes do programa são `626.0 m²` úteis internos e capacidade máxima de `20` pessoas. Ambientes não colocados ou não fechados são recusados. O preflight exige `revit.create_room`; a verificação reconsulta IDs, metadados, área e estado de fechamento.

## Decisões técnicas

- Reuso de `BimStage`, `DesiredElement`, `DesiredState`, `StageOperation`, `StageToolInvoker`, `run_preflight`, `dispatch_operations` e `verify_write` já existentes.
- Planejamento separado da execução: nenhuma escrita real no Revit foi feita nesta fase.
- Chaves hash estáveis para fronteiras compartilhadas, evitando duplicação entre ambientes e preservando a identidade lógica.
- Catálogo de paredes controlado no código do estágio e catálogo de famílias/tipos explicitamente fornecido pelo chamador.
- Divergências de área são dados de reconciliação e warnings; a geometria fonte não é ajustada para fazer a soma fechar.
- `external_planner` é uma dependência injetável para permitir testes e integração com os elementos externos sem acoplar os estágios ao módulo ou bridge do Revit.

## Fatos, restrições e hipóteses

### Fatos verificados

- As assinaturas públicas principais são `plan_shell_stage`, `plan_layout_stage`, `plan_openings_stage` e `plan_rooms_stage`.
- Os quatro arquivos de estágio não importam bridge do Revit.
- Os quatro planejadores produzem operações e desired-state antes de qualquer invocação.
- A suíte focada atual contém 6 testes de shell, 5 de layout, 6 de aberturas e 5 de ambientes.
- O módulo externo criado por outro agente está fora deste write set e foi apenas consumido por interface injetável quando necessário.

### Restrições aplicadas

- Working tree compartilhado: nenhuma branch, worktree, checkout, reset, commit ou push foi usado.
- Nenhum arquivo de terceiro foi revertido, apagado ou incorporado ao write set.
- Nenhum serviço pago, assinatura ou dependência nova foi adicionado.

### Hipóteses e limites

- A largura livre mínima de `0.80 m` é uma configuração de projeto do estágio; validações normativas adicionais podem ser aplicadas por um estágio de acessibilidade posterior.
- A área atual é calculada do polígono de entrada. A confirmação de área por faces acabadas e a escrita/consulta no Revit continuam sendo gates de integração posteriores.
- Elementos de setores externos são contabilizados na reconciliação do programa, mas não são emitidos como Rooms internos.

## TDD e validação

O fluxo RED → implementação mínima → GREEN foi executado por tarefa:

- RED inicial: cada novo arquivo de teste tinha 4 falhas pelo motivo esperado, módulo do estágio inexistente; depois da implementação, os quatro arquivos ficaram verdes.
- R07: teste de janela sem `sill_m` falhou primeiro (`DID NOT RAISE`), foi adicionada a exigência de peitoril explícito e o arquivo ficou em 5/5.
- R05: teste de planner externo falhou primeiro por argumento não aceito, foi adicionada a injeção `external_planner` e o arquivo ficou em 5/5 naquele checkpoint.
- R08: teste de numeração por setor falhou primeiro porque o segundo setor recebia o contador global, foi corrigido para contador por setor e o arquivo ficou em 5/5 naquele checkpoint.
- Verificadores: cada teste de verificação foi introduzido como RED por API ausente ou resultado incorreto e depois ficou verde.

Comandos e resultados finais:

```text
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit/test_stage_shell.py tests/unit/test_stage_layout.py tests/unit/test_stage_openings.py tests/unit/test_stage_rooms.py tests/solver/test_adjacency.py tests/solver/test_flows.py tests/solver/test_rooms.py -q -p no:cacheprovider --basetemp=.tmp-pytest-p05-final-focused --tb=short
36 testes executados; 36 passaram; 0 falharam. Verde.

$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/geometry -q -p no:cacheprovider --basetemp=.tmp-pytest-p05-final-geometry --tb=short
4 testes executados; 4 passaram; 0 falharam. Verde.

& './.venv/Scripts/ruff.exe' check <8 arquivos do write set>
Todos os checks passaram.

& './.venv/Scripts/ruff.exe' format --check <8 arquivos do write set>
8 arquivos já formatados.

$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m mypy src/amanda_agent/bim/stages/shell.py src/amanda_agent/bim/stages/layout.py src/amanda_agent/bim/stages/openings.py src/amanda_agent/bim/stages/rooms.py --show-error-codes
Sem erros.

$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit -q -p no:cacheprovider --basetemp=.tmp-pytest-p05-unit-full-final --tb=short
459 testes coletados; 458 passaram; 1 ignorado; 0 falharam. Verde.

$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit --ignore=tests/unit/test_stage_project.py -q -p no:cacheprovider --basetemp=.tmp-pytest-p05-unit-excluding-project-final --tb=short
444 testes coletados; 443 passaram; 1 ignorado; 0 falharam. Verde.
```

## GitHub e estado de retomada

O `git status --short` confirma que o working tree continua compartilhado e contém alterações e arquivos não rastreados de outros agentes, além dos oito arquivos deste write set. Por instrução explícita, não foi feito commit nem push; portanto não há SHA para informar e o GitHub ainda não foi atualizado por este agente.

Não houve checkpoint BIM nem evidência de escrita física, pois a fase exige desired-state puro. O próximo agente deve manter essa fronteira até o gate de integração com Revit.

Para retomar:

1. Preservar as alterações dos demais agentes e revisar este handoff junto aos quatro módulos e quatro testes.
2. Usar os comandos focados acima como smoke gate após qualquer integração.
3. Fazer o orquestrador registrar a evidência e fechar P05-T13 a P05-T16 no grafo, sem chamar `amanda_agent advance` neste contexto.
4. Antes de qualquer execução BIM futura, confirmar provider/mode, criar checkpoint exigido e executar leitura independente após cada escrita.

Pendências explícitas: integração real com Revit, consulta independente de elementos físicos, reconciliação de áreas acabadas, e decisão do integrador sobre commit/push quando o working tree compartilhado estiver pronto.
