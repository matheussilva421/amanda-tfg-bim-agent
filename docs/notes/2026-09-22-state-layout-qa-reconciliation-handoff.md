# Handoff — reconciliação do status QA pré-modelo (2026-09-22)

## Correção registrada

`PROJECT_STATE.yaml` tinha uma projeção antiga:

```text
layout_qa: FAIL (25 checks, 1 failed, 5 MODEL_PENDING)
state_revision: 160
```

O relatório autoritativo atual
`docs/reports/p08-layout-qa.json` foi lido e confirmou:

```text
verdict=PASS; checked=25; failed=0; model_pending=5
```

O campo foi reconciliado para:

```text
layout_qa: PASS (25 checks, 0 failed, 5 MODEL_PENDING)
state_revision: 161
```

Esta atualização corrige somente o resumo derivado do QA STUDY. Ela não fecha
P08-T08, não altera `phase_status`, `next_task`, `revit_stage` ou
`current_checkpoint`, e não transforma os cinco checks `MODEL_PENDING` em PASS.

## Validação

```text
python -c "... qa_report ... state ..."
qa_report= PASS 25 0 5
state_layout_qa= FAIL (25 checks, 1 failed, 5 MODEL_PENDING)
state_revision= 160
```

Após a edição, o YAML foi mantido com os demais campos intactos. A próxima
validação de produção ainda depende de Revit alcançável, save/close/reopen e
WRITE→READ→VERIFY.

## Git

Este bloco deve publicar somente `PROJECT_STATE.yaml` e este handoff. As
alterações ACL-visíveis em `revit/lab/.../GOLDEN/RC01`, resultados Topologic,
pacotes e a árvore `revit/production` continuam fora do escopo.

