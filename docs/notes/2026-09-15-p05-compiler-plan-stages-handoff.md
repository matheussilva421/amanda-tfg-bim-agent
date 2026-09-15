# P05 BIM compiler — T07–T12 handoff

**Data:** 2026-09-15  
**Agente:** Tyrion (LUNA XHIGH)  
**Escopo:** P05-T07, P05-T08, P05-T09, P05-T10, P05-T11 e P05-T12

## Estado

O estado atual do working tree foi conferido antes da implementação. O grafo
`state/task-graph.yaml` ainda apresentava T07–T12 como `PENDING`; ele não foi
alterado, pois o orquestrador é responsável pelo fechamento das tarefas. Não
houve escrita em Revit, provider real, arquivo GOLDEN ou checkpoint de modelo.

T12 foi incluída nesta fila conforme o esclarecimento do orquestrador. O
estágio R04 agora transforma blocos métricos do design engine em desired-state,
exige altura fornecida pelo conteúdo de projeto, valida área de projeção,
centroide, dimensões, rotação, separação e contenção no sítio, e recusa
`DETAILED_BIM` sem seleção vinculada ao conteúdo.

## Arquivos deste bloco

- `src/amanda_agent/bim/plan.py` — plano ordenado por estágio, NOOP idempotente,
  seleção estrita de capability, modo de execução e rollback por operação.
- `src/amanda_agent/bim/verification.py` — estados tipados de escrita, leitura,
  verificação e resultado da operação, com motivos tipados de falha/recusa.
- `src/amanda_agent/bim/stages/project.py` — verificador independente de
  identidade e naming do R01.
- `src/amanda_agent/bim/stages/site.py` — desired element de Toposolid por
  planner injetado ou `bim.external.place_toposolid`; a identidade externa é
  preservada em `external_logical_id` e normalizada para `SITE-TOPO-01`.
- `src/amanda_agent/bim/stages/levels.py` — desired-state R03 de níveis,
  grelhas e referências; nível sem evidência/provabilidade é recusado.
- `src/amanda_agent/bim/stages/massing.py` — desired-state R04 de blocos de
  massa e adaptação da saída de `design.blocks.generate_blocks`.
- `tests/unit/test_bim_plan.py` — ordenação, rollback, NOOP e gates de modo.
- `tests/unit/test_bim_verification.py` — RED/green do modelo write-read-verify.
- `tests/unit/test_stage_project.py` — verificação independente do R01.
- `tests/unit/test_stage_site.py` — planner externo injetado e regressão R02.
- `tests/unit/test_stage_levels.py` — níveis, grid provisório, referências e
  recusa de elevação não comprovável.
- `tests/unit/test_stage_massing.py` — métricas R04, integração com blocos do
  design engine, overlap e seleção detalhada não vinculada.
- `docs/notes/2026-09-15-p05-compiler-plan-stages-handoff.md` — este handoff.

`src/amanda_agent/bim/external.py` já existia no working tree por trabalho
paralelo e foi apenas consumido; não foi criado nem editado por este bloco.

## Decisões técnicas

- `CONCEPT_ONLY` é limitado a R04; `SYNTHETIC_LAB` exige `fixture=True`; e
  `DETAILED_BIM` exige solução elegível com `approval_hash` calculado sobre o
  conteúdo atual.
- Um `NOOP` permanece em `skipped_noops` para auditoria, mas não vira comando
  de escrita.
- Cada mutação planejada carrega `RollbackPlan` com ação inversa e regras de
  reconsulta independente.
- O sucesso reportado pelo provider nunca é o veredito final: uma consulta
  ausente produz leitura `MISSING` e verificação `FAIL`.
- `generate_blocks` não fornece altura. O R04 preserva essa fronteira e não
  inventa altura; o chamador precisa anexar uma altura comprovada.
- O planner de Toposolid externo pode gerar seu próprio ID estável. O estágio
  mantém o ID gerenciado do R02 e registra o ID externo em propriedade de
  auditoria.

## Evidência TDD

REDs observados antes das correções:

- plano/verificação/levels/massing: erro de importação por estados tipados e
  módulos ainda inexistentes;
- planner externo de site: `TypeError` por `toposolid_planner` ausente;
- verificador de projeto: importação sem `verify_project_initialization`;
- nível não comprovável: `ValidationError` por `is_provable` ausente;
- enriquecimento R04: centroid/área/separação ausentes;
- adaptação de `generate_blocks`: 1 falha e 4 deselected, inicialmente por
  altura ausente e metadados extras (`sector_id`, `area_m2`, `demand_m2`);
- integração com `external.place_toposolid`: 3 falhas por ID externo não
  normalizado.

Verde final por tarefa, com Python do projeto e `-p no:cacheprovider`:

| Tarefa | Comando alvo | Resultado |
| --- | --- | --- |
| T07 | `tests/unit/test_bim_plan.py` | 8 passed |
| T08 | `tests/unit/test_bim_verification.py tests/unit/test_verification.py` | 7 passed |
| T09 | `tests/unit/test_stage_project.py` | 15 passed |
| T10 | `tests/unit/test_stage_site.py` | 11 passed |
| T11 | `tests/unit/test_stage_levels.py` | 3 passed |
| T12 | `tests/unit/test_stage_massing.py` | 5 passed |
| integração | `tests/integration/test_bim_synthetic_compile.py` | 1 passed |

Lint do write set:

```text
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m ruff check \
  src/amanda_agent/bim/plan.py src/amanda_agent/bim/verification.py \
  src/amanda_agent/bim/stages/levels.py src/amanda_agent/bim/stages/massing.py \
  src/amanda_agent/bim/stages/project.py src/amanda_agent/bim/stages/site.py \
  tests/unit/test_bim_plan.py tests/unit/test_bim_verification.py \
  tests/unit/test_stage_levels.py tests/unit/test_stage_massing.py \
  tests/unit/test_stage_project.py tests/unit/test_stage_site.py
```

Resultado: `All checks passed!`. `git diff --check` não reportou erro; apenas
avisos normais de conversão LF/CRLF do Git.

## Git, pendências e retomada

Não foram executados `git add`, `commit`, `push`, `checkout`, `reset` ou
`complete_task`, conforme instrução do orquestrador. O working tree continua
compartilhado e contém alterações de outros agentes; não revertê-las.

A validação entregue é unitária e sintética. Permanecem como próximos gates o
provider/lab aprovado, a escrita real com leitura independente, save/reopen e
checkpoint formal de cada estágio, além do fechamento de T07–T12 pelo grafo.

Para retomar, reexecutar os alvos da tabela, revisar o diff apenas dos arquivos
deste handoff e então entregar este documento junto com os números ao
orquestrador. Não chamar `amanda_agent advance`.
