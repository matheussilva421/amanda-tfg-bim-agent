# P4-T01 — pesquisa de fontes oficiais do sítio

**Pesquisa realizada em:** 25/09/2026. **Escopo:** busca limitada a fontes públicas primárias da Prefeitura do Natal, Governo do RN/PMRN/SESED e Diário Oficial/registro oficial. Termos cobertos: BPChoque/CPChoque, Av. Miguel Castro, cadastro/lote/parcela, topografia/levantamento, transferência/realocação/disponibilidade, frentes e norte. Nenhuma agência foi contatada; não houve pedido e-SIC, login, cópia local persistida de artefato, acesso a RVT/Revit ou alteração de estado do projeto.

## Achados — fatos e limites

### 1. Parcela, levantamento e referência geodésica

- O Código de Obras de Natal (LC 258, 26/12/2024, arts. 61–62) prevê consulta a informações fundiárias, edilícias e topográficas e certidões como localização e limites. A lei descreve instrumentos municipais; não fornece a certidão ou geometria deste terreno. [Código de Obras, Prefeitura do Natal](https://www.natal.rn.gov.br/storage/app/media/semurb/legislacao/leis/4-LeiComplementar258_CodigodeObras27122024.pdf)
- Um documento municipal de contratação cadastral, associado ao processo SEMPLA-20240895527 em 02/12/2024, especifica produtos vetoriais até o lote, referências geoespaciais (incluindo SIRGAS 2000/UTM) e prevê fechamento de polígonos com medidas levantadas em campo quando necessário. É uma especificação de serviço; não constitui evidência de que o levantamento ou a entrega tenham sido executados para este terreno. [Documento da Prefeitura do Natal](https://www2.natal.rn.gov.br/_anexos/compras/anexo_num_3926.pdf)
- A página inicial do GeoNatal lista camadas de lotes e curvas de nível. A ligação [“Lotes - Zona Sul”](https://geomapas.natal.rn.gov.br/uploads/lotes_zona_sul_12_02_2025_c4ba6dc4ecd731c091a580ac0faaf898.geojson) serve um GeoJSON estático. Registro da resposta lida em memória em 25/09/2026: HTTP 200; `Content-Length: 27172090`; `Last-Modified: Thu, 15 May 2025 12:46:12 GMT`; `type=FeatureCollection`; 40.568 feições; CRS superior `urn:ogc:def:crs:OGC:1.3:CRS84`; SHA-256 `15cfb8ffee88e4e1371b9a1d4a5cf160e632ccff6aac6a3930f1768a0c163fae`. Isso confirma que uma coleção pública de lotes é servida pelo portal, mas não confirma sua atualidade/certificação nem qual feição corresponde ao terreno deste projeto; nenhuma geometria foi atribuída ao lote do TFG. A camada de curvas de nível é anunciada, mas não teve conteúdo verificado para este terreno.
- Em 25/09/2026, outras rotas no mesmo domínio oficial exibiam páginas de apostas/aplicativos e conteúdo promocional alheio a cartografia, inclusive conteúdo marcado como atualizado em 16/09/2026. **Anomalia de conteúdo:** isso não demonstra que as camadas estejam comprometidas; por cautela, elas não foram usadas para identificar o terreno e sua procedência/aplicabilidade específica permanece pendente. [GeoNatal](https://geomapas.natal.rn.gov.br/), [rota com conteúdo de apostas](https://geomapas.natal.rn.gov.br/app/2026-05-13/cadastro-ganhou/), [outra rota com conteúdo alheio à cartografia](https://geomapas.natal.rn.gov.br/app/Neymar-crian%C3%A7a.html)
- **Resultado limitado:** existe uma coleção pública de polígonos de lotes, mas esta pesquisa não identificou uma feição que possa ser validamente vinculada ao terreno do projeto. Não foi validado levantamento/topografia/datum específico do lote.

### 2. Ocupação e decisão de realocação/disponibilidade

- A Carta de Serviços da PMRN, marcada **“Atualizada em 03 de fevereiro de 2026”**, lista o **BPChoque** com endereço institucional “Av. Miguel Castro, s/n, bairro Lagoa Nova, em Natal/RN”, além de contato e comando. Isso prova que esse endereço foi publicado pela PMRN para o BPChoque naquela carta/data. Não equivale a vistoria da ocupação física, não delimita o lote e não identifica separadamente a CPChoque. [Carta de Serviços PMRN](https://www.transparencia.rn.gov.br/docs/orgaosdogoverno/cartasdeservico/Carta_de_Servi%C3%A7os_PMRN.pdf)
- O Diário Oficial do Estado de 07/05/2026 contém ato subscrito pelo comando do BPChoque, evidência de atividade administrativa oficial da unidade nessa data; não localiza essa atividade no lote em estudo. [DOE-RN, 07/05/2026](https://webdisk.diariooficial.rn.gov.br/Jornal/12026-05-07.pdf)
- **Fonte do próprio TFG, não fonte oficial:** o texto extraído do caderno, P29, afirma ocupação atual por unidade operacional ativa, assume realocação como premissa de projeto e exclui sua viabilidade administrativa do escopo. O plano de acompanhamento pergunta “E a Companhia de Polícia de Choque, para onde vai?” e registra a realocação como premissa declarada. São afirmações e pendência do trabalho acadêmico, não prova independente de ocupação, titularidade, transferência ou disponibilidade. [TFG, P29](../../project/provenance/extracted/source-extracts/TFG_Amanda_2026__2_TEXTOS_PARA_O_CADERNO__01_textos_prontos_para_colar.docx.txt#L26) · [Plano de acompanhamento](../../project/provenance/extracted/source-extracts/TFG_Amanda_2026__1_COMECE_AQUI__02_plano_de_acompanhamento.pdf.txt#L234)
- **Resultado limitado:** esta busca não encontrou decisão oficial pública de transferência/realocação ou declaração de disponibilidade do terreno; tampouco encontrou confirmação oficial da ocupação física atual do lote. O endereço institucional da carta permanece evidência parcial de endereço publicado.

### 3. Número de frentes e norte verdadeiro

A página do GeoNatal anuncia camadas de lotes/logradouros e curvas de nível. A camada de lotes existe como GeoJSON público, mas nenhuma feição foi vinculada ao terreno do projeto; tampouco foram extraídas cotas aplicáveis ao lote da camada de curvas. Essas camadas permanecem pendentes de validação específica. Esta busca não encontrou outra fonte oficial pública e verificável que determine o número de frentes do lote ou o azimute/referência de norte verdadeiro aplicável ao terreno.

## Rechecagem da Carta de Serviços PMRN

**O que comprova:** na atualização impressa de 03/02/2026, a PMRN publicou o BPChoque, seu endereço institucional na Av. Miguel Castro, s/n, Lagoa Nova, Natal, e dados de contato/comando.

**O que não comprova:** identidade ou limites cadastrais do lote; que o endereço corresponda ao polígono de estudo; ocupação física contínua e atual daquele terreno; situação dominial; levantamento, cotas, datum ou CRS; número de frentes; norte verdadeiro; decisão de remoção/transferência; nem disponibilidade para outro uso. Assim, a carta não libera `SITE_BOUNDARY`, `SITE_TOPOGRAPHY` ou `SITE_OCCUPANCY`.

## Bloqueios e efeito na retomada

| Entrada formal | Estado após a busca | Evidência/limite |
|---|---|---|
| `SITE_BOUNDARY` | **BLOCKING — não resolvido** | GeoNatal serve uma coleção de lotes em CRS84, mas nenhuma feição foi validamente ligada ao terreno do projeto. |
| `SITE_TOPOGRAPHY` | **BLOCKING — não resolvido** | Nenhum levantamento oficial do terreno ou datum de elevação encontrado nesta busca. |
| `SITE_OCCUPANCY` | **BLOCKING — não resolvido** | Há endereço institucional publicado do BPChoque; ocupação física do lote e ato de disponibilidade/transferência não foram confirmados. |
| `SITE_FRONTAGE_COUNT` | **DEGRADING — não resolvido** | Nenhuma contagem oficial verificável encontrada nesta busca. |
| `SITE_TRUE_NORTH` | **DEGRADING — não resolvido** | Nenhum bearing oficial verificável encontrado nesta busca. |

**Efeito:** nenhum bloqueio foi formalmente resolvido ou reclassificado. `PROJECT_STATE.yaml` permanece fora do escopo desta pesquisa; ao retomar, `P4-T01` continua sendo o `next_task` e `BLOCKED_BY_INPUT`. A Carta de Serviços e as afirmações do TFG não autorizam selecionar o lote, presumir sua liberação, fixar implantação/orientação ou emitir BIM-00.
