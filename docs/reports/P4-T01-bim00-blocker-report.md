# P4-T01 — BIM-00

**Status:** `BLOCKED_BY_INPUT` — BIM-00 não foi emitido nem passou.

## Seleção e limites do estudo

`DEC-CANONICAL-DETAIL-004` seleciona `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`
somente para um estudo acadêmico reversível, com coordenadas locais normalizadas,
até R04. `AMANDA_REVIEW_PENDING` continua; o hash de conteúdo não é aprovação
pessoal de Amanda. A candidata continua `bim_eligible=false` para produção final
e detalhamento.

Os dados ausentes do sítio limitam apenas as decisões que dependem deles:

- topografia: terraplenagem final e validação altimétrica de acessibilidade;
- limite cadastral: área do lote, recuos, implantação legal e licenciamento;
- ocupação/transferência: afirmação de disponibilidade ou transferência do lote;
- quantidade de frentes: acesso de esquina e recuos finais;
- norte verdadeiro: declaração de conformidade de orientação.

Esses pontos não impedem o estudo normalizado. R04 deve identificar suas massas
como `STUDY` e `LOCAL_NORMALIZED_STUDY_NOT_SURVEYED`, sem afirmar coordenadas,
limites ou elevações levantados. CANON-011 continua bloqueado até a comparação
geométrica/visual do R04 real com as quatro pranchas. R05 continua bloqueado até
CANON-011 passar.

## Bloqueadores atuais de BIM-00

- **Provider:** Revit 2027 build `27.2.0.39`, PID `38152`, responde ao sistema,
  mas tem `MainWindowHandle=0` e título vazio. `horizun_health` falhou em duas
  tentativas com `no Revit is reachable`. Manifesto e DLL do add-in existem,
  mas isso não prova provider ativo ou saudável. Não foi aberto documento RVT.
- **Writer lease:** o lock continua `HELD` por `amanda-P08-CAN-T09-R03` para o
  alvo obsoleto S02, PID antigo `33648`, heartbeat de `2026-09-23T22:18:55Z`.
  Não foi liberado, removido ou reivindicado; não há evidência suficiente para
  substituí-lo com segurança.
- **Alvo/checkpoint:** `revit/production/working/CURRENT.rvt` não existe e
  nenhum alvo ou checkpoint exato de RUN-003 foi escolhido/vinculado.

S02 permanece `STALE_BY_CANONICAL_REFERENCE_EXPANSION`; não foi usado como
solução ou alvo. Nenhum write no Revit foi feito; R04 e R05 não foram iniciados.

## Fontes e vínculo

A identidade RUN-003 segue vinculada às quatro pranchas canônicas, ao PDF do
programa oficial e ao relatório P1; a rechecagem anterior confirmou os hashes
registrados. O PDF oficial mantém capacidade de 20 pessoas, 626 m² internos e
260 m² externos. Nenhuma área foi alterada para acomodar geometria.

A [Carta de Serviços da Polícia Militar do RN](https://www.transparencia.rn.gov.br/docs/orgaosdogoverno/cartasdeservico/Carta_de_Servi%C3%A7os_PMRN.pdf)
publica o endereço do BPChoque na Av. Miguel Castro, s/n, Lagoa Nova. Isso não
identifica o polígono cadastral, não confirma que o endereço corresponde ao
lote do estudo e não comprova autorização de transferência. A pesquisa
geoespacial pública também não vinculou um lote único ao terreno de 24.135 m²;
ver `docs/reports/P4-T01-site-source-research-2026-09-25.md`.

Valores do candidato para uma tentativa futura, sujeitos a revalidação no gate:

- `solution_id`: `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`
- `layout_hash`: `7fde3e34a162167ce27fe2e3158a38f446882816a7c81bb326d486bdfaaae2e2`
- decisão vigente `DEC-CANONICAL-DETAIL-004`, hash da decisão:
  `29d70f0e830708a3926abad14877f4c3941418630c5f0225b0bf5924f2dabd8b`
- hash de conteúdo `approval_hash` do snapshot offline atual (não é aprovação
  humana): `961b6edc95bd097fe600b2ce968aacdf28876bf3c587b788a0b2358baddfc0b0`
- modo de coordenadas: `LOCAL_NORMALIZED_STUDY_NOT_SURVEYED`
- hashes das quatro pranchas e do PDF: registrados em `PROJECT_STATE.yaml`, na
  especificação atual e na decisão `DEC-CANONICAL-DETAIL-004`.
- alvo/checkpoint RUN-003: **NÃO VINCULADOS**

O snapshot offline que carrega a decisão vigente está em
`design-engine/runs/AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C-study-detail-004/`.
Seu manifesto confere seis arquivos; QA segue 17 PASS, 0 FAIL e CANON-011
BLOCKED, `revit_calls=0` e `bim_eligible=false`. O snapshot original de P3 foi
preservado no caminho original como histórico e não é a seleção atual.

O gate tipado compara também os hashes das pranchas, programa, commit, revisão e
SHA bruto de `PROJECT_STATE.yaml`; requer check separado para cada vínculo e
recusa divergências do modo de coordenadas.

## TDD e revisão

- BIM-00 isolado: **48 passaram** após RED/GREEN para a vinculação do modo de
  coordenadas tipado.
- Conjunto focado de R04/readback/geometria/BIM-00: **154 passaram** após
  regressão adicional que garante prevalência do readback real sobre payload de
  escrita auto-relatado.
- Gate consolidado de 15 módulos (BIM-00, providers/readback, R04, seleção,
  registro, task/state, sessão, status e plano): **235 passaram**.
- Contrato teste-first da decisão 004 versus snapshot P3: **2 RED**, depois
  implementação e alinhamento de seleção/registro, **3 passaram**; o snapshot
  004 foi gerado offline sem sobrescrever o snapshot P3.
- Antes das correções dos achados independentes, três testes reproduziram RED:
  massa marcada como verificada sem geometria lida; elevação base ignorada; e
  ausência de readback geométrico posterior à escrita.
- Regressão RED/GREEN adicional garante que geometria e identidade do readback
  do modelo substituam payloads auto-relatados pela escrita e que readback
  ausente não preserve uma geometria alegada.
- Revisão independente encontrou: (1) o gate aceitava cenário `FINAL` apesar
  da decisão 004 limitar a seleção a `STUDY`; (2) o estado marcava P4-T01 como
  concluído e bloqueado; (3) o handoff mantinha instruções de retomada antigas.
  Dois testes de cenário e as expectativas de estado reproduziram RED
  (4 falhas, 62 passes). Implementadas a recusa de cenário não-STUDY,
  `last_completed_task: P3-T01` com revisão de estado 184 e marcação explícita
  das instruções históricas como superadas. Revisão independente de confirmação
  aprovou os três fechamentos sem achados residuais. A revisão também pediu
  escopo explícito para severidades no dashboard e rótulo histórico na seção
  antiga do handoff; dois testes ficaram RED antes da implementação, e a
  confirmação independente final aprovou essas correções sem pendências.
- Suíte focada final: **270 passaram**, **0 falharam**, em 19 módulos BIM-00,
  providers/readback, R04 geometry, seleção/decisões, estado/task graph, sessão,
  status dashboard, repository hygiene e ordem do plano. Ruff dos arquivos
  Python alterados: **All checks passed**. `git diff --check` está limpo; o
  manifesto confirma 6/6 artefatos por tamanho e SHA-256. QA segue 17 PASS,
  0 FAIL, CANON-011 BLOCKED.

## Resultado e retomada

P4-T01 permanece `BLOCKED_BY_INPUT` por provider inacessível, lease S02 ainda
retido e ausência de alvo/checkpoint exatos. Não emitir BIM-00 nem executar R04
até esses fatos estarem resolvidos e os vínculos atualizados. A próxima tentativa
autorizada é P4-T01; não avançar R05 automaticamente. Depois do R04, comparar o
resultado real com as quatro pranchas para avaliar CANON-011. Preserve
`AMANDA_REVIEW_PENDING` e todos os limites de alegações de sítio.
