# Handoff incremental — R07 live openings — 2026-09-22

## Resumo

R07 foi concluído no RVT canônico de produção em Revit 2027/Horizun live. O
plano compilado tinha 87 operações: 52 portas e 35 janelas. Todas foram
aplicadas com `horizun_create_elements`, `units=m`, e retornaram
`verified_applied`; depois o arquivo foi salvo, fechado, reaberto pelo caminho
exato e reconsultado.

Target ativo atual:

`revit/production/working/AMANDA_WORKING_001.rvt`

## Evidência live

- Provider: Horizun 1.3.3; Revit 2027 build 27.2.0.39; PID 25996; contract
  hash `8b9600f5274d7dffb6e5bd5f`; outros clientes: 0.
- Mapeamento pré-write: 78 paredes e 78 marcas únicas; nenhum host ausente.
- R07: 87 requested, 87 created_verified; 52 portas e 35 janelas.
- Pós-reopen: resumo independente do modelo = 3719 elementos, categoria
  `Abertura em parede reta retangular` = 87, Paredes = 78, coverage completa,
  0 ilegíveis.
- Save: `saved_verified`; hash
  `be46acdde8cba35e301befc36a36bd2d140c8bfb2b4528cfa940830dd36655b8`;
  4.198.400 bytes.
- Close/reopen: `closed_verified` → `opened_verified`, Revit 2027, sem upgrade,
  sem descarte de alterações.
- Preview real: `revit/production/previews/R07-openings-3D-20260922.png`,
  1400×865, view `AMANDA R06 3D STUDY`, view restaurada, não calibrada.
- Checkpoint: `R07-openings-20260922.rvt` e manifesto, manager verify `True`.

## Correções importantes

1. O plano usa metros. Uma correção inicial das duas paredes de galeria foi
   feita em pés, detectada pela caixa independente e removida com delete typed
   verificado 2/2. As paredes foram recriadas em `units=m`, verificadas nas
   caixas esperadas e salvas no checkpoint corretivo `R06-gallery-host-correction-metres-20260922.rvt`.
2. `wall_opening` não aceita `level_id` no contrato live; o campo foi removido.
3. A pós-condição `opening_corners` exige ordenação geométrica específica:
   portas e janelas horizontais usaram `min/max`; janelas verticais preservaram
   a orientação do plano, exceto `WINDOW-034` e `WINDOW-038`, que passaram na
   variante `vertical_cross_c`. Os probes recusados foram rollback-confirmed e
   não foram repetidos com a mesma chave.

## Arquivos criados/alterados

- `docs/reports/delivery-mode/R07-live-evidence-2026-09-22.json`
- `revit/production/journals/R07-live-20260922.json`
- `revit/production/previews/R07-openings-3D-20260922.png`
- `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R07-openings-20260922.rvt`
- `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R07-openings-20260922.rvt.manifest.json`
- `PROJECT_STATE.yaml`, `state/task-graph.yaml`, `state/status.md`

## Testes e validações

- Live typed dry-run/apply: 87/87 verificados.
- Save/close/reopen/requery: PASS; 87 openings independentes no resumo do
  modelo, coverage completa, 0 ilegíveis.
- Checkpoint manager verify: `True`.
- Preview real capturado e restaurado; classificação `STUDY`, não calibrado.

## Bloqueios mantidos

`SITE_TOPOGRAPHY`, `SITE_BOUNDARY`, `SITE_OCCUPANCY`, `SITE_FRONTAGE_COUNT` e
`SITE_TRUE_NORTH` continuam explícitos. Não há claim FINAL/GOLDEN.

## Retomada exata

1. Reconfirmar `git status --short --branch`, provider health e writer lease.
2. Manter `AMANDA_WORKING_001.rvt` como target ativo único; não reabrir os
   checkpoints para write.
3. Executar R08 (rooms) com WRITE → READ → VERIFY no target canônico; antes de
   repetir qualquer operação, reconciliar por query/idempotency.
4. Publicar checkpoint R08, salvar/fechar/reabrir e reconsultar antes de
   seguir para R09.
5. Remover os temporários de inspeção `.tmp-r07-plan.json` e
   `scripts/.tmp_plan_r07_inspect.py` somente após o relatório ser preservado.

Fim do handoff incremental.
