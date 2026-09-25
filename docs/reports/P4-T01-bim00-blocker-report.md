# P4-T01 — BIM-00

**Status:** `BLOCKED_BY_INPUT` — gate BIM-00 não emitido.

## Verificações somente de leitura

- A identidade `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C` continua
  vinculada às quatro pranchas canônicas, ao PDF oficial e ao relatório P1;
  os hashes das quatro pranchas, do PDF e do relatório foram recalculados e
  conferem.
- A candidata RUN-003 segue `OFFLINE_CANDIDATE`, `bim_eligible=false`,
  `revit_calls=0` e não selecionada. `PROJECT_STATE.selected_design` e
  `current_checkpoint` são nulos. A decisão de detalhe continua
  `BLOCKED_BY_INPUT`, `AMANDA_REVIEW_PENDING` e
  `PROVISIONAL_PENDING_CANONICAL_GEOMETRIC_ACCEPTANCE`.
- Não há alvo RVT exato vinculado à candidata ou ao estado. Existem outros
  RVTs preservados no repositório, mas nenhum foi escolhido ou validado como
  alvo de RUN-003; `revit/production/working/CURRENT.rvt` não existe.
- O lock de writer continua `HELD` por `amanda-P08-CAN-T09-R03` para o alvo
  obsoleto S02. Não foi liberado nem reivindicado. Não havia processo Revit em
  execução, portanto não há evidência atual de saúde do provider.
- Permanecem os bloqueios de entrada `SITE_TOPOGRAPHY`, `SITE_BOUNDARY` e
  `SITE_OCCUPANCY`, além das pendências `SITE_FRONTAGE_COUNT` e
  `SITE_TRUE_NORTH`. O ajuste de sítio da candidata permanece não verificado.

## Correção do contrato BIM-00

O validador agora exige e compara, além dos vínculos existentes, o SHA-256 do
programa oficial, o SHA do commit, a revisão de `PROJECT_STATE.yaml` e o SHA-256
bruto desse arquivo. Cada vínculo requer seu próprio check PASS. Dados ausentes,
malformados ou divergentes recusam a autorização. Os fixtures usam RUN-003 e
caminhos sintéticos; S02 não é tratado como solução ou alvo vigente.

## Valores observados para uma futura tentativa

- `solution_id`: `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`
- `layout_hash`: `7fde3e34a162167ce27fe2e3158a38f446882816a7c81bb326d486bdfaaae2e2`
- content `approval_hash` (não é aprovação humana):
  `eea4a342a4d732cbc986a16d01d93e3981e79a5931f8d99ebef82c61d24299ec`
- hashes das pranchas, na ordem canônica:
  `30d009357a095e7794e0e915dcd2fdb04cd6b9aab9f4d13f5663ed54d6f20240`,
  `123b95633ae1be643da84f2226c6337d65a74f7d1337d6b27d94bdead1c3a263`,
  `5b96c2d5cc770742ee32d51b83b25993fe8b8a1638bf94da56ba8ef771031381`,
  `c56b806f805d9c4aa1e6015ba6b56ac960204066721f93ef08cbadfb312c0386`
- official program PDF SHA-256:
  `11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17`
- target RVT/checkpoint: **NOT SELECTED / NULL**
- code commit: `bc494683f9d9b154c40bdc8069a3dfa48710c665`
- `PROJECT_STATE.yaml`: revision `182`, raw SHA-256
  `d023087e0054539995fa2746bd6076b8a1292bb1ec22ed081589902575c9164f`

TDD do gate: primeiro RED (**38 falhas, 1 passou**); depois GREEN
(**41 passaram** no módulo focado). O grupo BIM-00/status/estado passou
**57/57**, e Ruff passou nos arquivos Python alterados.
Revisão independente do código: **sem achados Critical, Important ou Minor**.
Verificação final focada, incluindo repositório, estado, sessão e ordem do plano:
**103 passaram**; Ruff e `git diff --check` escopado passaram.

## Resultado e retomada

P4-T01 permanece bloqueado até que exista uma solução apta e aprovada, os dados
de sítio requeridos estejam resolvidos, um alvo RVT e checkpoint exatos sejam
designados, e lease/provider tenham evidência válida para BIM-00. Nenhum
documento Revit/RVT foi aberto ou alterado; nenhuma autorização BIM-00 foi
emitida. Não executar R04/R05 nem reutilizar S02. Após resolver as entradas,
retomar P4-T01 e gerar evidência contra os hashes, commit, revisão e estado
ativos; P5 só fica elegível depois do gate passar.
