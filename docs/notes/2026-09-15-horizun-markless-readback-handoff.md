# Handoff — readback de tipos sem ALL_MODEL_MARK

Data: 2026-09-15  
Escopo: `HorizunInvoker` e testes unitários do transporte falso.

## Concluído

- `level`, `grid` e `room` agora agendam `horizun_query_model` por categoria (`OST_Levels`, `OST_Grids`, `OST_Rooms`) com `return_fields` igual a `_READBACK_FIELDS`, `response_mode: compact` e `cache_mode: bypass`.
- O merge usa `_row_matches` para considerar somente as linhas que casam com o `logical_id`. A verificação só passa com exatamente uma correspondência, `unique_id` textual não vazio e `element_id` resolvido.
- Os tipos que usam `ALL_MODEL_MARK` mantêm o fluxo anterior.
- `wall_opening` não recebe uma consulta inventada. Embora `_query_arguments` aceite `element_ids`, `categories`, `name`, `level`, `parameters`, `bounding_box` e outros filtros, nenhum deles identifica de forma confiável o logical ID de uma abertura recém-criada; a abertura não carrega marca nem comentários. O resultado registra `readback_verified: False` e `readback_error` tipado com código `wall_opening_no_reliable_query_filter`.

## Arquivos alterados

- `src/amanda_agent/bim/providers/horizun.py`
- `tests/unit/test_bim_horizun_invoker.py`
- `docs/notes/2026-09-15-horizun-markless-readback-handoff.md`

## TDD e validação

RED inicial:

```text
./.venv/Scripts/python.exe -m pytest tests/unit/test_bim_horizun_invoker.py -k markless_typed_create_readback_matches_one_logical_id_row --basetemp=.tmp-luna-xhigh-red -p no:cacheprovider -q
```

Resultado: 3 falharam, 46 foram selecionados fora do filtro; falha esperada porque a última chamada ainda era `horizun_create_elements`.

RED ampliado antes da implementação:

```text
./.venv/Scripts/python.exe -m pytest tests/unit/test_bim_horizun_invoker.py -k "markless_typed_create or wall_opening_readback" --basetemp=.tmp-luna-xhigh-red2 -p no:cacheprovider -q
```

Resultado: 8 falharam, 46 foram selecionados fora do filtro; falha esperada por ausência do agendamento, do estado não verificado e do motivo tipado.

GREEN focado:

```text
./.venv/Scripts/python.exe -m pytest tests/unit/test_bim_horizun_invoker.py -k "markless_typed_create or wall_opening_readback" --basetemp=.tmp-luna-xhigh-green-focused-3 -p no:cacheprovider -q
```

Resultado: 8 passaram, 46 foram selecionados fora do filtro.

GREEN do arquivo relevante:

```text
./.venv/Scripts/python.exe -m pytest tests/unit/test_bim_horizun_invoker.py --basetemp=.tmp-luna-xhigh-file-2 -p no:cacheprovider -q
```

Resultado: 54 passaram, 0 falharam.

Lint do teste:

```text
./.venv/Scripts/python.exe -m ruff check tests/unit/test_bim_horizun_invoker.py
```

Resultado: passou. O lint conjunto também encontrou dois diagnósticos já existentes em `horizun.py`: `RUF100` e a chave literal `wall_opening` duplicada; eles ficaram fora do escopo.

## GitHub e limitações

- Git não foi executado, conforme instrução da tarefa; portanto não há commit SHA, status ou push a reportar.
- Não houve abertura/fechamento de Revit, chamada MCP real ou verificação física/persistência do modelo. A decisão de `wall_opening` está coberta pelo contrato local e pelos filtros aceitos no `_query_arguments`, mas continua sem prova de runtime real.

## Retomada

Revisar os dois diagnósticos preexistentes do `ruff` em uma tarefa separada. Para promover a decisão de `wall_opening` além do estado `False`, seria necessário obter do provider um filtro de consulta estável ou um readback pós-criação por `element_id`, com teste independente e evidência real.
