# Handoff — ponto de inserção do R08 e cadeia local de referências (2026-09-22)

## Status

Foi concluído um bloco local e reversível de correção no compilador de produção.
O R08 agora traduz a geometria poligonal do ambiente para o ponto de inserção
exigido pelo comando tipado `revit.create_room`, usando o centróide medido do
polígono. A geometria completa permanece no payload para reconciliação de área.

Nenhuma escrita BIM, save/close/reopen, alteração de `PROJECT_STATE.yaml`,
checkpoint, exportação Revit ou promoção FINAL/GOLDEN foi realizada. A produção
continua bloqueada pelo modal nativo do Revit `Projeto não recentemente salvo`.

## Causa e correção

O stage de ambientes emitia o polígono completo, mas a ponte tipada precisa de
`point` para inserir um ambiente no Revit. O baseline reproduziu `KeyError:
'point'` no teste de contrato. O adaptador `_stamp` em
`src/amanda_agent/production/layout_bim.py` agora calcula o centróide do anel
válido e acrescenta `point: [x, y]` somente para `revit.create_room`.

Também foi conferida a cadeia de identidade local: 78 paredes são produzidas
por R05/R06, 20 hosts são consumidos por R07 e 78 alvos por R12; não há IDs
faltantes nos consumidores.

## Arquivos

- `src/amanda_agent/production/layout_bim.py`
- `tests/unit/test_production_layout_bim.py`
- este handoff

## TDD e validação

RED contra `HEAD` antes da correção:

```text
pytest tests/unit/test_production_layout_bim.py::test_rooms_stage_bridges_revit_room_insertion_point -q
1 failed: KeyError: 'point'
```

GREEN focalizado:

```text
\.\.venv\Scripts\python.exe -m pytest tests/unit/test_production_layout_bim.py tests/unit/test_stage_layout.py tests/unit/test_bim_horizun_invoker.py -q --basetemp .tmp-pytest-r08-point-green -p no:cacheprovider
77 passed
```

Regressão offline:

```text
\.\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q --basetemp .tmp-pytest-r08-point-full -p no:cacheprovider
878 passed, 0 failed
```

Checks adicionais:

- `py_compile` passou para o compilador alterado, teste e driver de produção.
- `git diff --check` passou no escopo alterado.
- A medição de referências confirmou zero host R07 e zero alvo R12 sem produtor
  em R05/R06.

## Limites e retomada

1. Um humano ainda precisa dispensar o modal nativo do Revit sem `Save As` e
   sem alterar o arquivo-alvo.
2. Repetir `horizun_health` e `get_document_info` read-only e confirmar um PID
   Revit e documento ativos.
3. Obter evidência fresca de save/close/reopen do R05.
4. Executar uma tentativa nova de R06 com WRITE→READ→VERIFY, exigindo 30/30
   registros `VERIFIED`; depois continuar somente se o journal for totalmente
   verificável.
5. Não promover `PROJECT_STATE.yaml`, exports ou GOLDEN a partir deste gate
   offline, de processos ativos ou de journals históricos/falhos.

## Git

O working tree já contém exclusões ACL-visíveis em
`revit/lab/exports/p06t14/GOLDEN/RC01`, alterações geradas em `state/` e
`tool-lab/`, além de artefatos não rastreados de produção e pacotes anteriores.
Esses caminhos ficam fora deste bloco. O commit deve incluir somente os dois
arquivos de código/teste e este handoff.

- Commit publicado: `f1563de` (`fix(revit): provide room insertion points`).
- Push: `origin/main` atualizado de `32eb550` para `f1563de`.
- O commit contém somente o compilador, o teste e este handoff.
