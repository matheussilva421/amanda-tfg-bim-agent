# Handoff — reconciliação de início de sessão (2026-09-22)

## Escopo

Foi executado o protocolo de início do repositório após a retomada desta
sessão. Não houve escrita BIM, alteração de código, alteração de
`PROJECT_STATE.yaml`, promoção de checkpoint/export/GOLDEN ou alteração de
artefatos de produção.

## Estado autoritativo observado

- `PROJECT_STATE.yaml`: `PHASE_08`, `PENDING`, `GO_WITH_LIMITATIONS`,
  `next_task=P08-T08`, `last_completed_task=P06-T14`,
  `current_checkpoint=null`, `state_revision=161`.
- `state/status.md`: 159 tarefas; `P08-T08` é a única tarefa `READY`; lease do
  escritor `FREE`; Revit registrado como `27.2.0.39`; provider preferencial
  `horizun`.
- Bloqueios ativos: `SITE_TOPOGRAPHY`, `SITE_BOUNDARY`, `SITE_OCCUPANCY`,
  `SITE_FRONTAGE_COUNT` e `SITE_TRUE_NORTH`.
- O plano filho ativo é `docs/superpowers/plans/08-amanda-production-run.md`;
  `P08-T08` cria a massagem conceitual dos três finalistas.
- Foram observados os processos Revit PID `15608` e `39808`, ambos
  responsivos, mas sem `MainWindowHandle`. A presença do processo não foi
  usada como prova de provider ou documento ativo.

## Git e integridade de artefatos

`HEAD` e `origin/main` estão em `68d7391` (`docs: refresh project status
dashboard`). O working tree já contém alterações fora deste bloco:

- exclusões ACL-visíveis em `revit/lab/exports/p06t14/GOLDEN/RC01`;
- modificações geradas em `tool-lab/topologic/results/`;
- `.codex/`, o pacote corrigido, `release/` e `revit/production/` não
  rastreados.

As exclusões ACL permanecem não reconciliadas porque a leitura retorna
`Permission denied`; não foram restauradas, removidas ou adicionadas ao Git.
Os resultados e artefatos não rastreados também ficaram fora deste bloco.

## Pendências e retomada

1. Manter a produção parada até uma pessoa dispensar o modal nativo do Revit
   `Projeto não recentemente salvo` e tornar uma única sessão operável.
2. Repetir `horizun_health` e `get_document_info` somente read-only; confirmar
   independentemente PID e caminho do documento.
3. Obter save/close/reopen independente do R05.
4. Executar uma tentativa nova R01→R06, exigindo todos os registros
   `VERIFIED`; preservar o journal R06 falho anterior como histórico.
5. Só depois avaliar R07 e promover estado, checkpoint, export ou GOLDEN.

## Validações deste bloco

- `git status --porcelain=v2`: confirmou as alterações preexistentes listadas
  acima.
- Leitura de `PROJECT_STATE.yaml`, `state/status.md`, `state/blockers.yaml`,
  `state/task-graph.yaml` e handoffs de 22/09: concluída.
- Verificação de caminhos GOLDEN: bloqueada por ACL; nenhum conteúdo foi
  interpretado como removido.
- Inspeção de processos Revit: dois processos responsivos, sem janela
  acessível; nenhuma ação foi tomada.

## Status final do bloco

Nenhum teste de código foi necessário. O próximo agente deve retomar pela
recuperação humana da UI do Revit e pela sondagem read-only do provider, sem
alterar o working tree pré-existente.
