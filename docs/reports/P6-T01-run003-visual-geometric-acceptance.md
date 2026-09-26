# P6-T01 — RUN-003 R04: reconciliação canônica visual e geométrica

**Atualização:** 2026-09-26 23:23 UTC
**Status:** `PASS` — `CANON-011` passa para a topologia espacial do `STUDY` normalizado. R05–R13 ficam autorizados pelo DEC-010 após este gate; esta aceitação não valida cômodos internos, dados cadastrais ou aprovação pessoal.

## Autoridade e escopo

A comparação usa exatamente as quatro pranchas em `docs/source/canonical/`, na ordem implantação, administrativo, residencial e serviços, vinculadas pelos hashes registrados no JSON de evidência. `docs/source/programa_necessidades.pdf` continua sendo a autoridade quantitativa: capacidade de 20 pessoas, 626 m² internos úteis e 260 m² externos programados. Nenhuma área, quantidade ou capacidade oficial foi alterada. As áreas anotadas nas pranchas orientam forma e organização, não substituem áreas oficiais de salas.

O RUN-003 é um `STUDY` local normalizado, não levantado. As relações cardeais abaixo descrevem a organização relativa do estudo; não afirmam norte geográfico, limite cadastral, disponibilidade do lote, topografia ou ajuste legal.

## Estado real após a reconciliação

O alvo exato `revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt` foi salvo, fechado, reaberto sem upgrade e lido novamente. O checkpoint P6 é `revit/production/evidence/AMANDA-RUN-003-R04/P6-T01-CANON-011-RECONCILED-20260926.rvt`, SHA-256 `8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326`, 4.960.256 bytes. O manifesto do checkpoint confere com o arquivo e `CheckpointManager.verify_checkpoint` retornou `True`.

A consulta tipada pós-reabertura retornou os 25 elementos do escopo (7 massas, 14 pisos e 4 coberturas), cobertura completa e zero ilegíveis; fingerprint `4636abc6b294829b`. Uma consulta completa separada retornou 4.573 elementos, cobertura total e zero ilegíveis. As capturas recentes e seus hashes estão em `revit/production/evidence/AMANDA-RUN-003-R04/views/p6-canon-011-20260926/p6-canon-011-captures.json` e estão vinculadas ao novo checkpoint/fingerprint.

## Comparação das quatro pranchas

### 01 — Implantação

- Administrativo na borda pública sul; a massa ocupa x=[−5,5] m, y=[−52,−32] m.
- Residencial protegido ao norte/interior, com quatro volumes independentes A, B, C e D comunitário.
- Serviços/capacitação a sudeste, em composição curva com seis anéis internos envolvendo pátio/jardim.
- Setor infantil a oeste, próximo ao playground oficial de 40 m²; o jardim terapêutico permanece central e a horta a leste.
- Percursos públicos/administrativos, público/serviços e carga são elementos separados. A rota pública do administrativo termina na borda sul do envelope. As larguras são hipóteses de estudo, sem afirmar portas ou acessos cadastrais.
- As cinco áreas externas modeladas continuam em 80/80/30/30/40 m² (260 m²), de acordo com o PDF.

## Divergências administrativas — decisão reversível para o STUDY

| Evidência | Alternativas consideradas | Impacto e decisão | Teste, correção e readback |
|---|---|---|---|
| O piso administrativo anterior media 237,407 m²; a prancha 02 indica aproximadamente 200 m² por pavimento. | Manter 237,407 m²; ou aproximar o envelope da prancha sem alterar a soma de áreas úteis do PDF. | Manter o excesso ampliaria o envelope em 37,407 m² (18,7%) por pavimento e afastaria a volumetria da referência. Para o STUDY reversível, foi adotado 10 × 20 m = 200 m² por piso. A planta interna e o programa permanecem sob autoridade do PDF e serão testados em R06. | O teste espacial primeiro falhou contra o valor anterior; após a correção tipada, os pisos 331163/331170 retornaram 200,0 m² cada e a massa 328657 retornou 10 × 20 m por pavimento. `CANONICAL_DEVIATION-ADM-001` registra `RESOLVED_FOR_STUDY`; `approval_received=false`. |
| O piso superior estava em 3,2 m enquanto o Nível 2 estava em 4,0 m. | Mover o piso para 4,0 m mantendo o nível; ou baixar o nível para 3,2 m. | O contrato ativo do estudo é Nível 2 = 4,0 m. O piso superior foi alinhado a esse datum, mantendo o volume de estudo com 6,4 m de altura. | Testes de nível e elevação foram atualizados primeiro. Readback pós-reabertura confirmou Nível 2 e piso 331170 em 4,0 m, offset 0,0 m. O programa oficial não foi alterado. |

### 02 — Administrativo / acolhimento

A massa administrativa existente foi ajustada para 10×20 m por pavimento e 6,4 m de altura de estudo. Os pisos novos são IDs 331163 e 331170: o térreo no Nível 1 a 0,0 m e o superior no Nível 2 a 4,0 m. A leitura `HOST_AREA_COMPUTED` mediu 2.152,782083 ft², equivalente a 200,0 m² por piso. O caminho público 331177 alcança a borda sul em y=−52 m. Assim, o footprint aproximado da prancha e o nível da placa superior estão geometricamente reconciliados no estado atual do estudo.

O registro `CANONICAL_DEVIATION-ADM-001` foi atualizado para `RESOLVED_FOR_STUDY`, com os IDs e hashes do novo checkpoint. `approval_received` permanece `false`; esta alteração não atribui aprovação pessoal a Amanda e não altera áreas úteis do programa.

As funções da prancha foram reconciliadas textualmente no P1-T01, mas não foram modeladas como salas no R04. Térreo: recepção, controle, triagem/acolhimento, espera, registro, psicologia, serviço social, jurídico, reunião e apoios. Superior: coordenação, administrativo, equipe, funcionários, multiuso/grupos e apoios. A distribuição interna e as áreas úteis ainda exigem geometria de salas para validação BIM.

### 03 — Residencial

As quatro massas independentes permanecem e as quatro circulações cobertas/semiabertas não fecham o pátio central protegido. O estudo preserva a organização de três pavilhões familiares e um pavilhão comunitário. A reconciliação oficial de P1 mantém três dormitórios por família e um dormitório comunitário, conforme o arranjo aceito; quartos e banheiros não foram criados como salas no R04, portanto sua contagem e áreas ainda não têm readback BIM.

### 04 — Serviços / capacitação

O envelope continua curvo e centrado no pátio, sem retornar ao footprint retangular genérico. Os caminhos público e de carga permanecem distintos. A reconciliação funcional e de duplicidades da prancha 04 está registrada no P1-T01: usos impressos que não têm sala oficial própria são tratados como modo/subzona, e o PDF controla todas as quantidades e áreas. A geometria atual não contém salas internas que demonstrem essas atribuições ou áreas.

### Setor infantil

O volume oeste e a proximidade com a área verde/playground permanecem. P1-T01 reconcilia as quatro funções oficiais do setor infantil: brinquedoteca 24 m², apoio pedagógico 18 m², banheiro 6 m² e depósito 4 m². Nenhuma delas foi modelada como sala no R04; a reconciliação documental não é apresentada como validação geométrica interna.

## Evidência visual e seus limites

O manifesto P6 contém nove capturas atuais feitas após a reabertura, com vista, IDs, dimensões, hashes e estado de restauração. A implantação completa atual fornece o contexto de todas as zonas. A tentativa focal `child-playground-relation.png` foi excluída por estar visualmente quase vazia; a imagem focal antiga permanece identificada apenas como referência do checkpoint `33a99c7c…cca27b49`. O readback tipado atual revalidou os IDs 328658/329971 e suas caixas; a distância livre em planta é 2,976 m (limite de adjacência adotado: 3,0 m). Assim, a imagem histórica não é tratada como captura atual nem como única prova da relação. Nenhuma captura reivindica calibração pixel-modelo.

## Pendências e decisão

`CANON-011` e P6-T01 passam para o escopo declarado: geometria, implantação, organização e relações espaciais comparadas às quatro pranchas, com áreas externas conferidas contra o PDF. O readback confirma todas as relações espaciais aceitas; as duas divergências administrativas estão resolvidas para o STUDY.

As salas e atribuições internas não estão no R04. Não foram usadas como gate espacial de P6: R06 executa o layout interno; R08 cria as Rooms e verifica suas áreas conforme o PDF e o cruzamento P1-T01. Os cinco bloqueios de terreno limitam claims cadastrais, topográficos, de disponibilidade, orientação e acessibilidade altimétrica; não bloqueiam a topologia local normalizada. O estudo não reivindica conformidade cadastral, norte verdadeiro ou ajuste legal.

**R05 ainda não foi executado.** Após este PASS, a autorização operacional do usuário registrada em DEC-010 libera a sequência atual P7-T01 a P7-T09 (R05–R13), sem nova confirmação entre gates verdes. A identidade canônica segue sem aprovação pessoal atribuída; R14+ e GOLDEN não estão incluídos. Não houve pesquisa GeoNatal, operação em RC01, reutilização de S01/S02/R12 nem alteração do programa oficial. S02 permanece `STALE_BY_CANONICAL_REFERENCE_EXPANSION`.

## Testes e rastreabilidade

O teste espacial foi atualizado primeiro para as medidas pós-reabertura e falhou contra os valores antigos (L2 a 3,2 m em vez de 4,0 m), como esperado no RED. O teste do registro de divergência também falhou primeiro porque o status ainda estava `OPEN_FOR_REVIEW`; passou depois de o registro receber os IDs e hashes reconciliados. O teste de estado apontou o checkpoint desatualizado no dashboard e falha no formato do carimbo; ambos foram corrigidos antes do GREEN. A revisão independente do fechamento encontrou uma conclusão antiga ainda pendente no JSON e uma divergência de atribuição R06/R08; os testes de regressão ficaram RED antes de marcar a revisão antiga como superada e alinhar layout interno em R06 com criação/readback de Rooms em R08.

Resultado GREEN focado: `tests/unit/test_run003_r04_spatial_evidence.py`, `test_canonical_deviation_record.py`, `test_run003_view_capture_evidence.py`, `test_status_checkpoint_consistency.py`, `test_task_graph.py` e `test_state_store.py`: **27 passaram, 0 falharam**. O gate de política `tests/policy/test_plan_order.py` passou **8/8**, incluindo a nova dependência P6→P7 do RUN-003. Validação de parse YAML/JSON passou. `ruff` não está disponível no ambiente; nenhum pacote foi instalado. `python -m amanda_agent status` também não inicia porque o Python do host não tem `ortools`; o dashboard e o estado formal foram atualizados diretamente com o readback e os registros verificados.

Evidência principal: `revit/production/evidence/AMANDA-RUN-003-R04/r04-spatial-model-evidence.json`; manifesto visual P6: `revit/production/evidence/AMANDA-RUN-003-R04/views/p6-canon-011-20260926/p6-canon-011-captures.json`; reconciliação funcional oficial: `docs/reports/P1-T01-four-board-reconciliation.md`.
