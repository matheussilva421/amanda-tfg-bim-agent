# Handoff — correção do QA pré-modelo e validação STUDY (2026-09-22)

## Status

Foi concluído um bloco independente de implementação enquanto a produção Revit
continua bloqueada pelo modal nativo `Projeto não recentemente salvo`.
Nenhuma escrita BIM, alteração de `PROJECT_STATE.yaml`, checkpoint, save/close/reopen
ou promoção FINAL/GOLDEN foi realizada.

A tarefa de produção permanece `P08-T08`, `PHASE_08=PENDING`, e os cinco checks
que dependem do modelo continuam `MODEL_PENDING`.

## Correção implementada

`run_checks` em `scripts/qa_layout.py` agora:

- agrega instâncias físicas com IDs `REQ-…#n` por `logical_id` base e informa a
  quantidade esperada ao reconciliador;
- limita a reconciliação pré-modelo aos ambientes internos realmente medidos;
- mantém o programa externo como uma verificação separada do total programado de
  260 m², sem fabricar geometrias externas ausentes.

Isso elimina um falso FAIL do QA: a planta tinha 52 ambientes internos com áreas
exatas, mas o adaptador passava IDs de instância e não fornecia os espaços
externos ao reconciliador genérico.

## Arquivos do bloco

- `scripts/qa_layout.py`
- `tests/project/test_layout_qa.py`
- `tests/unit/test_qa_layout_script.py`
- `docs/reports/p08-layout-qa.json`
- `docs/reports/p08-layout-qa.md`
- este handoff

## TDD e validação

RED observado antes da implementação:

```text
pytest tests/project/test_layout_qa.py::test_layout_reconciliation_scopes_to_observed_internal_rooms -q
1 failed: expected PASS, got FAIL
```

GREEN e regressão:

```text
pytest tests/project/test_layout_qa.py tests/unit/test_qa_layout_script.py tests/unit/test_program_qa.py -q
8 passed

pytest tests -m "not revit and not slow" -q -p no:cacheprovider
878 passed, 0 failed
```

QA derivado:

```text
python scripts/qa_layout.py
verdict: PASS; checks: 25; failed: 0; model_pending: 5
```

Entregáveis STUDY:

```text
python scripts/render_study_sheets.py
7 PNG + 7 SVG; layout hash 9410f296b0d3a258a51971a6e2a35cd404f8018ca28ba5d6f36003516808539

python scripts/build_study_package.py
7 páginas PDF; 7 previews; todas não vazias; blank check: PASS
```

Foi feita inspeção visual de `page-02.png` (planta) e `page-07.png` (corte).
Ambas estão legíveis e identificadas como STUDY. Isso não comprova RVT, IFC/PDF/DWG
exportados pelo Revit, persistência ou validação FINAL.

## Limites e retomada

- O modal nativo deve ser dispensado por uma pessoa na UI do Revit, verificando
  todos os monitores.
- Depois disso, repetir `horizun_health` e `get_document_info` read-only, confirmar
  PID/documento, fazer save/close/reopen independente do R05 e executar tentativa
  nova R01→R06 com WRITE→READ→VERIFY.
- O journal R06 falho existente permanece histórico; não deve ser reutilizado.
- Não promover `PROJECT_STATE.yaml`, exports ou GOLDEN a partir destes testes
  offline, do processo Revit ou do provider health histórico.

## Git

O working tree já tinha exclusões ACL-visíveis, alterações geradas e artefatos
não rastreados de blocos anteriores. Eles permaneceram fora deste bloco. O commit
e push deste escopo devem incluir somente os arquivos listados acima.
