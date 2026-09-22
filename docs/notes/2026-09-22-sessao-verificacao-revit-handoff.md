# Handoff — sessão de verificação e bloqueio nativo do Revit (2026-09-22)

## Status

A sessão foi iniciada pelo protocolo de produção e terminou sem escrita BIM,
sem alteração de `PROJECT_STATE.yaml`, sem promoção de checkpoint/export/GOLDEN
e sem alteração de código. A tarefa persistida continua `P08-T08`, com
`PHASE_08` em `PENDING` e `GO_WITH_LIMITATIONS`.

A ponte Horizun continua bloqueada antes de qualquer leitura ou escrita pelo
modal nativo do Revit `Projeto não recentemente salvo` (`#32770`). As chamadas
read-only `horizun_health` e `get_document_info` foram enfileiradas, mas não
iniciaram: o Revit removeu cada pedido após aproximadamente 3000 ms porque o
modal não foi respondido. Portanto, não há nova evidência de documento ativo,
PID selecionado ou estado do modelo nesta sessão.

## Evidência coletada

- `PROJECT_STATE.yaml`: `next_task=P08-T08`, `last_completed_task=P06-T14`,
  `phase_status=PENDING`, `current_checkpoint=null`, `state_revision=160`.
- `state/status.md`: lease do escritor `FREE`; Revit `27.2.0.39`; Horizun
  `HEALTHY` no snapshot persistido, mas a prova live desta sessão ficou
  bloqueada pelo modal.
- Processos Revit presentes e responsivos: PID `15608` iniciado em
  `21/09/2026 20:04:06` e PID `39808` iniciado em `21/09/2026 21:42:29`.
  Ambos foram apenas observados; nenhum foi encerrado ou alterado.
- `revit/production/journals/R05.json`: histórico com `52/52 VERIFIED`.
- `revit/production/journals/R06.json`: histórico falho com `30/30 FAILED`
  por `Requested properties do not match the committed element.`; deve ser
  preservado como evidência histórica.
- A superfície Computer Use não expôs nenhuma aplicação nativa acessível,
  portanto o modal permaneceu sob controle humano.

## Git e arquivos

- `HEAD`, `origin/main` e `origin/HEAD`: `05635ae` (`docs: record R06 patch
  publication`).
- O remoto `origin` está configurado para o repositório Amanda.
- O working tree já continha alterações e artefatos não relacionados: exclusões
  ACL-visíveis em `revit/lab/exports/p06t14/GOLDEN/RC01`, modificações geradas
  em `state/`, `src/`, `tests/` e `tool-lab/`, além de `.codex/`, o pacote
  corrigido e `revit/production/`. Nenhum desses caminhos foi restaurado,
  removido ou incluído neste handoff.

## Decisões e limites

- Não iniciar produção enquanto o modal nativo impedir a verificação live.
- Não selecionar um dos dois PIDs apenas pela presença do processo.
- Não promover `PROJECT_STATE.yaml` a partir de testes offline, processos,
  saúde histórica da ponte ou journals antigos.
- Não executar `R06` sobre o journal existente; a próxima tentativa deve ser
  fresca e gerar journals/arquivo RVT próprios.

## Retomada exata

1. O proprietário deve localizar e dispensar `Projeto não recentemente salvo`
   na UI nativa do Revit, verificando todos os monitores, sem `Save As` e sem
   mudar o destino salvo pretendido.
2. Executar novamente `horizun_health` e `get_document_info` read-only; confirmar
   independentemente o PID Revit escolhido e o caminho do documento ativo.
3. Confirmar a persistência do R05 por save/close/reopen independente.
4. Executar uma tentativa normal nova até R06:

   ```powershell
   .\.venv\Scripts\python.exe scripts/run_amanda_production.py `
     --rvt revit\production\working\AMANDA_WORKING_001.rvt `
     --max-stage R06 --revit-pid <published-revit-pid> --execute
   ```

5. Exigir `VERIFIED` em todos os registros R01→R06 e parar no primeiro erro,
   warning que altere a aceitação ou readback não verificado. Só então avaliar
   R07; não atualizar `PROJECT_STATE.yaml` antes dessa evidência.

## Testes e validações

Não foram executados testes de código nesta sessão. Foram executadas apenas
leituras de Git/estado/journals/processos e duas sondagens read-only da ponte;
as sondagens foram bloqueadas pelo modal e não iniciaram trabalho.

## Pendências

- Dismissal humano do modal nativo.
- Revalidação live do provider/documento/PID.
- Gate independente de save/close/reopen para R05.
- Nova tentativa R01→R06 e promoção de estado somente após evidência completa.
