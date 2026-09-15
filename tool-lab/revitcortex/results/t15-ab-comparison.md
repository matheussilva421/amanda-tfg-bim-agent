# P02-T15 — comparação A/B Cortex versus Horizun

## Veredito

**PASS_WITH_WARNINGS no ciclo de persistência.** O RevitCortex criou e releu os elementos; o Horizun salvou, fechou o documento ativo por identidade de objeto, reabriu pelo caminho solicitado e releu todos os 11 ElementIds sem itens ilegíveis. A advertência remanescente é real e anterior ao close/reopen: o ambiente 328668 existe, mas não tem área calculável porque a região não está fechada.

## Fixture e identidade

- Fixture: `revit/lab/revitcortex/LAB_RC_DOC.rvt`.
- Baseline de origem: `revit/lab/baseline/LAB_R00_EMPTY.rvt`.
- Baseline SHA-256: `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D`.
- Fixture salva SHA-256: `8820C791781F7F411AAD5D3C8D044257A9130933FAB86E0D19FE18383D2059BA`.
- Tamanho salvo: `4.415.488` bytes.
- A referência textual `LAB_HORIZUN_DOC.rvt` não coincide com o arquivo que possui esse hash e esses IDs; `LAB_HORIZUN_DOC.rvt` foi preservado.

## Comparação por item

| Item | ElementId | Resultado pós-reopen |
|---|---:|---|
| Nível 1 | 311 | PASS, `Nível 1` |
| Nível 2 | 694 | PASS, `Nível 2` |
| Parede | 328657 | PASS, bbox `10000 x 200 x 3000 mm`, nível 1 |
| Piso | 328660 | PASS, bbox `6000 x 4000 mm`, nível 1 |
| Ambiente | 328668 | PASS de persistência; warning de região aberta e área nula permanecem |
| Porta | 328671 | PASS, instância identificada no nível 1 |
| Janela | 328673 | PASS, instância identificada no nível 1 |
| Vista | 328675 | PASS, `LAB RC Planta`, `FloorPlan` |
| Tabela | 328689 | PASS, `LAB RC Paredes`, `Schedule` |
| Folha | 328696 | PASS, `LAB Prancha 01`, `DrawingSheet` |
| Viewport | 328711 | PASS, `Título com linha` |

A releitura foi uma única consulta `horizun_query_model` com `element_ids` exatos, `cache_mode=bypass`, `include_links=false`, `include_bounding_box=true`: `matched_total=11`, `returned=11`, `coverage_complete=true`, `unreadable_total=0`.

## Close/reopen

- Revit próprio: PID `12744`, StartTime `2026-09-15T15:43:06.1074563-03:00`.
- Close: `closed=true`, `api_returned=true`, objeto removido de `Application.Documents`, `IsValidObject=false`, `was_modified=false`, `disk_changed=false`; ativou o anchor `HZ_ANCHOR_2027.rvt`. Tempo: `2402 ms`.
- Open: `status=opened`, `opened_now=true`, `active_document_verified=true`, `path_is_the_one_requested=true`, host/arquivo 2027, `upgraded=false`. Tempo: `2990 ms`.
- Health pós-reopen: saudável, build `27.2.0.39`, `permission_profile=full_write`, `mcp_paused=false`, documento ativo no caminho exato.

## Advertência conhecida

O ambiente 328668 foi criado no bloco anterior no ponto correto, mas o Revit reportou `Ambiente não está em uma região apropriadamente fechada`; área e volume não são afirmados. Isso não impediu a persistência do ElementId.

## Evidências

- `t15-close-live.json`
- `t15-open-live.json`
- `t15-reread.json`
- `t15-health-after-reopen.json`
- `t15-close-reopen-summary.json`
- `t15-cortex-fixture.json`

Nenhum add-in fora do Horizun foi deixado carregado durante a sessão: Host e Cortex foram movidos com hashes preservados e restaurados ao final. O baseline imutável e os fixtures virgens `.000N` conferidos permanecem intactos.
