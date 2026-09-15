# P05-T03 a P05-T06 — handoff de safety, checkpoints e diff

Data: 2026-09-15  
Agente: Athena / LUNA XHIGH  
Repositório: `C:\Users\slvma\Downloads\Github\Projeto Amanda`

## Resumo

Implementados os quatro blocos P05 sob o write set delegado:

- P05-T03: Safety Sentinel fail-closed para alvos de escrita e operações
  destrutivas.
- P05-T04: checkpoints imutáveis com manifesto versionado, SHA-256,
  identidade documental, proveniência e restauração verificada.
- P05-T05: diff determinístico desired/current com identidade persistente,
  tolerâncias, divergência explícita e detecção de identidade Revit duplicada.
- P05-T06: limiar configurável para impacto destrutivo direto e em cascata,
  com cálculo/evidência, bloqueio de cascata desconhecida e override auditável.

## Arquivos alterados

Dentro do write set:

- `src/amanda_agent/bim/safety.py`
- `src/amanda_agent/bim/checkpoints.py`
- `src/amanda_agent/bim/diff.py`
- `tests/unit/test_bim_safety.py`
- `tests/unit/test_checkpoints.py`
- `tests/unit/test_bim_diff.py`
- `tests/unit/test_destructive_threshold.py`
- este handoff

`src/amanda_agent/bim/models.py` não precisou de mudança; os modelos
existentes já forneciam a base tipada necessária e foram preservados para os
agentes concorrentes.

## Decisões técnicas

### Safety Sentinel

- Alvos são resolvidos canonicamente e precisam estar dentro de roots
  allowlisted.
- GOLDEN, master, source, baseline e release são recusados por caminho,
  identidade de arquivo, hardlink, symlink, junction ou outro reparse point.
- O Sentinel compara caminho/ID do documento ativo e valida o writer lease,
  incluindo a identidade do documento no lease.
- Operações desconhecidas são críticas e recusadas por padrão.
- DELETE/REPLACE/REMOVE/PURGE/OVERWRITE/RESET/ROLLBACK exigem confirmação
  explícita; cascata desconhecida é recusa tipada mesmo com confirmação.
- Cada recusa tem `reason_code` e mensagem. A classificação inclui risco,
  impacto direto, cascata, total afetado e fração quando há denominador.
- O `CheckpointManager` recebe uma exceção estreita para publicar em um
  diretório convencional `checkpoint(s)`; a API pública do Sentinel continua
  recusando esse componente por padrão.
- Um manifesto vinculado apenas a `source_document_path` exige o caminho do
  documento atual no rollback; não há restauração sem evidência suficiente de
  identidade.

### Checkpoint manager

- A criação exige fonte existente, save estável e destino/manifesto ausentes.
- A publicação usa temporários no mesmo diretório, fsync, rename atômico e
  manifesto publicado por último.
- Hash e identidade da fonte são comparados antes/depois; hash, tamanho e
  identidade ficam no manifesto.
- Falhas após publicar o arquivo removem o alvo se o manifesto não foi
  publicado.
- Rollback verifica o manifesto antes de copiar, exige identidade documental
  atual quando o checkpoint é vinculado a um documento, não sobrescreve por
  padrão e verifica hash/tamanho depois da restauração.
- Checkpoint existente não é sobrescrito e GOLDEN/source/baseline/release
  continuam proibidos como destino.

### Diff e limiar destrutivo

- As operações são ordenadas por `logical_id` e ação para saída determinística.
- `DiffOperation.identity` expõe somente `logical_id`, `unique_id` e
  `document_id`; `element_id` continua tratado como identificador de sessão.
- Identidade persistente Revit duplicada gera `DuplicateCurrentIdentity`.
- Divergência de elemento gerenciado gera `UserDivergence` antes de UPDATE,
  REPLACE ou DELETE.
- CREATE/UPDATE/REPLACE/NOOP/DELETE permanecem separados; `type_changed` e
  dependentes gerenciados/não gerenciados entram no impacto destrutivo.
- O cálculo usa `impacto direto + cascatas` sobre `managed_count`.
- Cascata desconhecida bloqueia; zero baseline bloqueia qualquer destruição.
- Acima de 10% ou do máximo absoluto, o resultado é `HIGH_RISK_PLAN` e exige
  checkpoint, plano revisado e liberação explícita. O novo override exige
  `audit_reference`; sem referência ele permanece bloqueado.
- O resultado registra `calculation`, `impact_breakdown`,
  `override_requested`, `override_applied`, `audit_reference` e `evidence`.

## Evidência TDD RED → GREEN

Todos os ciclos foram executados primeiro com os testes novos falhando pelo
contrato ausente e depois com a implementação mínima verde.

| Task | RED | GREEN final |
|---|---:|---:|
| P05-T03 | 9 passed, 4 failed | 14 passed |
| P05-T04 | 6 passed, 4 failed | 11 passed |
| P05-T05 | 7 passed, 3 failed | 10 passed |
| P05-T06 | 7 passed, 4 failed | 11 passed |
| Borda de symlink quebrado | 13 passed, 1 failed | 14 passed |

Após a primeira rodada verde, a regressão de diretório `checkpoints` foi
reproduzida pelo estágio de projeto e corrigida; o teste direcionado terminou
com 25 aprovados. A borda adicional de identidade por caminho teve RED de 10
aprovados e 1 falha, seguido de 11 aprovados.

O P05-T04 teve uma execução intermediária que expôs duas correções de
robustez: `fsync` no handle `r+b` no Windows e filtro de componentes reservados
por token exato para não confundir diretórios temporários de pytest.

## Validação final

Ambiente: PowerShell 5.1, `./.venv/Scripts/python.exe`,
`PYTHONIOENCODING=utf-8`.

- `pytest tests/unit/test_bim_safety.py tests/unit/test_checkpoints.py tests/unit/test_bim_diff.py tests/unit/test_destructive_threshold.py -q -p no:cacheprovider --basetemp=.tmp-pytest-p05-focused-final2`
  - 46 executados, 46 aprovados, 0 falhas — verde.
- `pytest tests/unit/test_bim_cli.py tests/unit/test_bim_diff.py tests/unit/test_bim_external.py tests/unit/test_bim_models.py tests/unit/test_bim_plan.py tests/unit/test_bim_safety.py tests/unit/test_bim_verification.py tests/unit/test_checkpoints.py tests/unit/test_destructive_threshold.py -q -p no:cacheprovider --basetemp=.tmp-pytest-p05-bim-final2`
  - 75 executados, 75 aprovados, 0 falhas — verde.
- `pytest tests/unit/test_stage_project.py -q -p no:cacheprovider --basetemp=.tmp-pytest-p05-stage-project-final`
  - 15 executados, 15 aprovados, 0 falhas — verde.
- `ruff check` nos quatro módulos e quatro arquivos de teste — verde.
- `mypy --disable-error-code=import-untyped` nos quatro módulos BIM — 4
  arquivos verificados, sem problemas.
- `mypy` sem a flag encontrou somente a ausência ambiental de stubs
  `types-PyYAML` em `diff.py`; não houve erro de tipagem próprio dos módulos.
- `git diff --check` — sem erro de whitespace; apenas avisos normais de
  conversão LF/CRLF do Git no Windows.

Uma execução de `test_stage_project.py` + `test_stage_site.py` antes do último
ajuste teve 24 aprovados e 4 falhas. A falha de checkpoint foi corrigida pelo
allowlist estreito acima. As três falhas restantes em `test_stage_site.py`
vieram do `src/amanda_agent/bim/external.py` concorrente retornando um logical
ID `EXT-TOPOSOLID-*` incompatível com o contrato do estágio; esse arquivo está
fora do write set e não foi alterado.

## Estado Git e orquestração

- Branch: `main`, acompanhando `origin/main`.
- Não houve `git add`, commit, push, checkout, reset ou alteração de arquivos
  `.tmp-*`, conforme instrução explícita.
- O working tree já continha alterações de outros agentes em `PROJECT_STATE`,
  `state/task-graph.yaml`, estágios, CLI, verification, integrações e
  artefatos `tool-lab`; todas foram preservadas.
- P05-T03 a P05-T06 permanecem para fechamento pelo orquestrador; não foi
  chamado `amanda_agent advance` nem `complete_task`.
- Não há SHA de commit deste bloco porque commit/push foram proibidos nesta
  sessão.

## Retomada

1. Revalidar o working tree compartilhado antes de integrar, preservando as
   alterações dos outros agentes.
2. Reexecutar a suíte BIM final e o lint; se `external.py` continuar com
   logical ID externo, resolver essa integração no write set do estágio.
3. Inspecionar esta evidência e atualizar o grafo/orquestrador para fechar
   P05-T03, P05-T04, P05-T05 e P05-T06.
4. Antes de qualquer BIM write real, manter a sequência
   `WRITE -> READ -> VERIFY` e fornecer identidade do documento ativo, lease,
   checkpoint verificado e plano destrutivo auditado.
