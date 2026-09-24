# Historical close/reopen evidence — P02-T15

> This file preserves the detailed Revit close/reopen evidence observed on
> 2026-09-15. Its former handoff instructions are historical. Current execution
> is selected through `PROJECT_STATE.yaml` and `state/task-graph.yaml`.

Data: 2026-09-15

## Veredito

- `horizun_document_session close`: **PASS**.
- `horizun_document_session open`: **PASS**.
- Ciclo close/reopen e leitura independente dos IDs: **PASS**.
- T15 geral: **PASS_WITH_WARNINGS**. O ciclo de persistência fechou; a advertência anterior do ambiente continua real: o ambiente 328668 não tem área calculável porque a região não está fechada.

## Documento e segurança operacional

- O artefato que contém os IDs e o hash fornecido é `revit/lab/revitcortex/LAB_RC_DOC.rvt`.
- SHA-256 verificado antes/depois do ciclo: `8820C791781F7F411AAD5D3C8D044257A9130933FAB86E0D19FE18383D2059BA`.
- Tamanho verificado: `4.415.488` bytes.
- O arquivo imutável `revit/lab/baseline/LAB_R00_EMPTY.rvt` permaneceu em `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D`.
- A descrição recebida chama o documento de `LAB_HORIZUN_DOC.rvt`, mas esse é um arquivo diferente no checkout. Não foi substituído nem renomeado; a prova de hash/IDs aponta para `LAB_RC_DOC.rvt`.
- Antes da sessão, `Amanda.ToolLab.Host.addin` e `RevitCortex.addin` foram retirados da pasta compartilhada e guardados em `%TEMP%\Amanda-P02-T15-addin-hold`. O `Horizun.addin` permaneceu instalado.
- Depois, ambos foram restaurados e os hashes conferidos: Host `31B656141502BF1388A039F23B412FF236628870B701B0F657C78FD6FC7B64F6`; Cortex `C9E81E87D046E6D0A4F1BC71C7F2F56E775C32EDE78FFCDDA3CAF7F22A4AD94C`; Horizun `BAEAE873B9735067BCEE515D78E98E9F78D66705D202B1BFF34120D391B93B91`.

## Transcript do ciclo

- Instância própria iniciada: Revit 2027 PID `12744`, StartTime `2026-09-15T15:43:06.1074563-03:00`.
- `horizun_health` antes do close: saudável, build `27.2.0.39`, `permission_profile=full_write`, `mcp_paused=false`, documento ativo `LAB_RC_DOC` no caminho exato.
- Close: `closed=true`, `api_returned=true`, `doc.IsValidObject=false`, objeto removido de `Application.Documents`, `was_modified=false`, `disk_changed=false`, `bytes_before=4415488`, `bytes_after=4415488`.
- Close ativou o documento descartável `C:\Users\slvma\.horizun\anchor\HZ_ANCHOR_2027.rvt`; tempo da fila/execução: `2402 ms`.
- Open: `status=opened`, `opened_now=true`, `active_document_verified=true`, `path_is_the_one_requested=true`, versão do arquivo e host `2027`, `upgraded=false`; tempo da fila/execução: `2990 ms`.
- Leitura pós-reopen via `horizun_query_model`, `cache_mode=bypass`, `include_links=false`, `include_bounding_box=true`: `matched_total=11`, `returned=11`, `coverage_complete=true`, `unreadable_total=0`.
- IDs confirmados: `311`, `694`, `328657`, `328660`, `328668`, `328671`, `328673`, `328675`, `328689`, `328696`, `328711`.
- A parede 328657 continua com bbox `10000 x 200 x 3000 mm`; o piso 328660 com bbox `6000 x 4000 mm`; porta 328671 e janela 328673 continuam no nível 311; vista, tabela, folha e viewport continuam identificáveis. O ambiente 328668 sobreviveu, mas segue sem bbox/área calculável e com o warning de região aberta já registrado.
- `horizun_health` pós-reopen confirmou o mesmo documento ativo, PID `12744`, build `27.2.0.39`, dois documentos abertos (fixture + anchor) e perfil `full_write`.
- O Revit próprio foi encerrado apenas após prova `StartTime` observada igual à StartTime registrada; não houve encerramento de outro PID.

## Evidências

- `tool-lab/revitcortex/results/t15-close-live-args.json`
- `tool-lab/revitcortex/results/t15-close-live.json`
- `tool-lab/revitcortex/results/t15-open-live-args.json`
- `tool-lab/revitcortex/results/t15-open-live.json`
- `tool-lab/revitcortex/results/t15-reread-args.json`
- `tool-lab/revitcortex/results/t15-reread.json`
- `tool-lab/revitcortex/results/t15-health-open-2.json`
- `tool-lab/revitcortex/results/t15-health-after-reopen.json`
- `tool-lab/revitcortex/results/t15-close-reopen-summary.json`
- `tool-lab/revitcortex/results/t15-cortex-fixture.json`
- `tool-lab/revitcortex/results/t15-ab-comparison.md`

## Baselines em `revit/lab/**`

O inventário completo está em `t15-close-reopen-summary.json`. Os arquivos `.000N` de fixtures virgens que ainda existem coincidem com o baseline; os arquivos canônicos de cada exercício são cópias mutadas deliberadamente. O scan não encontrou alteração no baseline imutável nem no fixture T16 já aprovado.

## Historical follow-up recorded at the time

1. O resultado indicava consumir close/reopen no grafo do orquestrador.
2. T15 geral deveria permanecer `PASS_WITH_WARNINGS` enquanto o ambiente 328668 continuasse sem região fechada; a geometria do ambiente não foi declarada como 16 m².
3. O drill P02-T18 foi registrado separadamente; o relatório indicado era
   `tool-lab/custom-api/results/t18-drill-report.md` e
   `t18-drill-summary.json` como `PASS_WITH_WARNINGS`.

Esses encaminhamentos descrevem o estado daquela data e não são tarefas atuais.

## Git

Nenhum add, commit ou push foi executado. O working tree já continha alterações de outros agentes; somente os caminhos autorizados deste bloco foram tocados.
