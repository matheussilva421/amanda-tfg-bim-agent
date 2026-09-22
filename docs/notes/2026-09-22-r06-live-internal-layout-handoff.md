# Handoff incremental — R06 live internal layout — 2026-09-22

## Resumo

O target live de produção foi reconciliado e avançou de R05 para R06 em uma sessão Revit 2027 saudável, usando o provider Horizun live. O target é:

`revit/production/working/AMANDA_WORKING_001.20260921-213302.rvt`

R06 tem 30 paredes internas verificadas, a vista 3D persistida `AMANDA R06 3D STUDY`, preview de planta e preview 3D real. O arquivo foi salvo, fechado sem descartar alterações e reaberto pelo caminho exato; a leitura posterior confirmou o target ativo e os 30 elementos R06.

## Evidência live

- Provider: Horizun 1.3.3; Revit 2027 build 27.2.0.39; PID 25996; contract hash `8b9600f5274d7dffb6e5bd5f`; outros clientes: 0.
- R06 dry-run: 30 válidos, 0 inválidos; apply: 30/30 commit; readback independente: 30/30, coverage completa, 0 ilegíveis.
- Tipo R06: `Interior - 138 mm Divisória (1-hr)`, type 220, nível `LEVEL-01`, marca `LAYOUT-WALL-*`.
- Antes do write, foram removidas de forma verificada 26 paredes stale `LAYOUT-WALL-*` type 219 e 32 paredes compartilhadas stale `WALL-*`; nenhum row failed/still-in-use/unknown.
- Uma tentativa inicial de criação foi recusada/rollback por geometria stale e não foi repetida com a mesma chave; a reconciliação precedeu o batch final.
- Readback final após a vista: 3.630 elementos; 76 paredes; 3 pisos; 1 telhado; 1 massa; 3 níveis; 2 grids; 24 vistas; coverage completa; 0 ilegíveis.
- Save pós-vista: `saved_verified`; hash final `ebf18f98a8ac5548e65b677684a1ef467732f2055113bb0c24829db71c0a0d0a`; 4.124.672 bytes.
- Close: `closed_verified`, target deixou de ser o documento ativo via `HZ_ANCHOR_2027.rvt`, sem descarte e sem mudança no disco.
- Reopen: `opened_verified`, caminho exato, versão 2027, sem upgrade.
- Checkpoint manager: `verify_checkpoint(...) = True`.

## Arquivos criados/alterados

- `docs/reports/delivery-mode/R06-live-evidence-2026-09-22.json`
- `revit/production/journals/R06-live-20260922.json`
- `revit/production/previews/R06-live-Nivel-1-20260922.png`
- `revit/production/previews/R06-live-3D-20260922.png`
- `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R06-internal-layout-20260922.rvt`
- `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R06-internal-layout-20260922.rvt.manifest.json`
- `PROJECT_STATE.yaml`: checkpoint/R06, last task P08-T09, next P08-T10, revision 164.
- `state/status.md`: dashboard reconciliado.
- `state/task-graph.yaml`: P08-T08 e P08-T09 = `PASS_WITH_WARNINGS`; P08-T10 continua PENDING.
- `scripts/.tmp_run_r06_live.py`: removido após a tentativa local stdio provar apenas `no Revit reachable`; nenhum write de produção ocorreu por esse caminho.
- Handoff anterior R05 preservado: `docs/notes/2026-09-22-r05-live-persistence-handoff.md`.

## Seleção e decisão

- Solução: `AMANDA-RUN-001-S01`.
- Seleção: `AGENT_DELEGATED`.
- Approval hash: `bf7dcca735de166f100a6687f441ac7247ccf31f5e9e28a1bd4837591acba7ef`.
- `AMANDA_REVIEW_PENDING` permanece não bloqueante para desenvolvimento delegado.
- Comparação compact-bar vs dois wings/pavilhões registrada em `R05-design-comparison-2026-09-22.md`; os princípios visuais foram usados como DESIGN_REFERENCE, sem copiar escala, norte, terreno ou dimensões.
- Programa oficial preservado: até 20 pessoas, 626 m² internos, 260 m² externos, 783–814 m² fechados e 850–950 m² cobertos. A hipótese histórica de 42 pessoas não foi usada.

## Testes e validações

- Foco executado anteriormente neste bloco: `tests/test_p08_inputs.py tests/unit/test_production_layout_bim.py tests/unit/test_checkpoints.py` — 34 passed, 0 failed.
- Checkpoint pós-vista verificado com o gerenciador — `True`.
- Evidência live independente: save/close/reopen/query pós-reopen — PASS.
- Previews são `STUDY`, não calibrados e não provam implantação final ou conformidade normativa.

## Git

O checkout continua com alterações preexistentes não relacionadas (deletions em GOLDEN de lab, tool-lab, .codex, pacote delivery/release e outros). Não restaurar, limpar ou stagear essas alterações automaticamente. Os commits desta entrega são `880b0df` e `2a51cdb`, já enviados para `origin/main`; essas alterações continuam fora deles.

## Bloqueios e pendências

Mantidos: `SITE_TOPOGRAPHY`, `SITE_BOUNDARY`, `SITE_OCCUPANCY`, `SITE_FRONTAGE_COUNT`, `SITE_TRUE_NORTH`. O modelo live ainda é estudo arquitetônico; exports existentes IFC/PDF/DWG são STUDY.

Ainda pendente: P08-T10 canonical production promotion; R07–R13; R14 QA; R15 RC/cold reopen; IFC/PDF/DWG/previews finais; R16 GOLDEN. Não modificar o canonical/GOLDEN sem checkpoint e gate.

## Retomada exata

1. Confirmar `git status --short --branch`, provider health e writer lease.
2. Reabrir/reconfirmar o target timestampado acima; não usar o canonical como target de write.
3. Executar P08-T10 somente com checkpoint e comparação de bytes/hash do target; preservar o source/canonical.
4. Avançar para R07 usando WRITE → READ → VERIFY, checkpoint antes/depois e save-close-reopen antes de declarar PASS.
5. Se houver timeout, reconciliar o modelo por query antes de repetir qualquer key.
Fim do handoff incremental.
