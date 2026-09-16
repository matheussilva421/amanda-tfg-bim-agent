# O que falta — retrato simples

> SUPERSEDED 2026-09-15: retrato atual em `docs/notes/2026-09-15-o-que-falta-simples-v5.md`; fica como histórico.
> A v3 erra a contagem (diz 134 PASS/15 PENDING; o grafo tem 136/13) e afirma que
> faltam `journal` durável e `tool-lab/reports/bim-compiler-e2e.md`, que existem.

Data: 2026-09-15. Esta nota é o resumo canônico para o dono.

## Onde estamos

- O projeto continua em STUDY. Há 159 tarefas; P08-T07 foi o último PASS.
- As duas tarefas READY são P06-T14 e P08-T08. A próxima oficial é P06-T14.
- O Revit 2027 está instalado e em uso. Faltam os RVTs de produção, não o Revit.
- Há duas finalistas de estudo, F01 e F02, mas ainda não há escolha única registrada.
- P07-T17 e P07-T19 estão SUSPENDED; a primeira exige sessão nova e a segunda reboot real.

## O que falta

- P06-T14: executar QA R14→R16 no laboratório, salvar, fechar, reabrir a frio,
  validar IFC/PDF/DWG, gerar hashes e provar a integridade do pacote.
- P08-T08: criar e verificar massas conceituais no Revit para as finalistas.
- P08-T09: comparar e registrar uma única escolha com approval_hash.
- P08-T10..P08-T14: criar AMANDA_WORKING_001.rvt e compilar R01–R13 com
  WRITE→READ→VERIFY e documentação.
- P08-T15..P08-T19: QA, RC, reabertura a frio, exports, relatórios e GOLDEN-001.
- A avaliação ambiental dos finalistas é HEURISTIC, não simulação.
- P05 ainda não entrega BIM_PLAN.md/json, CLI bim claim/record-result, journal
  durável nem tool-lab/reports/bim-compiler-e2e.md.
- Faltam dados reais do terreno: topografia, limites, uso atual, frentes e norte.
- Amanda ainda precisa revisar a arquitetura, desenhos, memoriais, autoria, defesa
  e submissão institucional. Blender/render e APS/cloud são opcionais suspensos.

## Divergência conhecida

- PROJECT_STATE.yaml traz blockers: [], enquanto state/blockers.yaml lista cinco
  bloqueios do terreno: SITE_TOPOGRAPHY, SITE_BOUNDARY, SITE_OCCUPANCY,
  SITE_FRONTAGE_COUNT e SITE_TRUE_NORTH.
- Sem RVT de produção, dados de terreno e revisão humana, não há entrega FINAL nem
  TFG_COMPLETE.

## Próximo passo

P06-T14, após o preflight confirmar alvo permitido, lock livre e provider alcançável.
Com o MCP indisponível, o drill deve falhar explicitamente e não registrar PASS.

Verificado por auditoria em 2026-09-15.
