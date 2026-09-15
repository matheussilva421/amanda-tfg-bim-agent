# P08-T03 — Resolução do site

Data da resolução: 2026-09-15. Escopo: somente os arquivos de site/levantamento
do projeto e as fontes fornecidas pela Amanda. Este registro não transforma um
desenho de hipótese em levantamento, polígono cadastral ou cota altimétrica.

## Arquivos e escopos procurados

Foram inspecionados `project/site/**`, `TFG_Amanda_2026/**` e as cópias
imutáveis em `docs/source/**`. O conjunto de anexos contém 23 arquivos na pasta
`TFG_Amanda_2026` e 23 cópias correspondentes em `docs/source`; os 23 hashes do
manifesto conferem. Nos formatos relevantes, foram encontrados:

| Arquivo | Evidência observada | Classificação |
| --- | --- | --- |
| `docs/source/06_implantacao_HIPOTESE.dxf` | DXF AC1032 salvo por `ezdxf`; cabeçalho sem datum, sistema de coordenadas, matrícula ou pontos de levantamento; `EXTMIN`/`EXTMAX` não inicializados | HIPÓTESE de implantação, não levantamento |
| `docs/source/07_modelo_BIM_HIPOTESE.ifc` | IFC4 com `IFCSITE` nomeado “Lote CPChoque - Lagoa Nova”; arquivo nomeado HIPOTESE e modelo conceitual | Modelo BIM hipotético, não levantamento |
| `docs/source/TFG_Amanda Fernandes_ENTREGA 15.06.2026.pdf` | páginas 60–61 relatam área e frentes; as cotas permanecem `[X]`, `[Y]`, `[Z]`, `[W]`; o próprio texto registra a necessidade de conferência | Fonte acadêmica com lacunas explícitas |
| demais arquivos de `project/site/**` | `site.json` e `missing-data.yaml` já registravam boundary de estudo e topografia ausente | Registro canônico preservado |

Não foi encontrado, nesses escopos, arquivo de levantamento com extensão ou
conteúdo verificável (`DWG`, `SHP`, `GEOJSON`, pontos cotados ou memorial
topográfico), nem certidão/matrícula ou identificador cadastral. O DXF e o IFC
foram preservados como fontes históricas e não foram usados para inventar
elevações.

## Decisão

O nível verificável mais alto para o design run é:

`SITE_TOPOGRAPHY = PLANAR_PLACEHOLDER`

`site.json` permanece com `topography.source_state = MISSING`,
`topography.representation = PLANAR_PLACEHOLDER`, `elevation_points = []` e
`boundary.kind = STUDY_PLACEHOLDER`. A origem `(0, 0, 0)` continua sendo apenas
a convenção `LOCAL_DESIGN_PLANE`; não representa uma cota real.

Essa decisão permite zoneamento esquemático e estudo de massas sobre a
referência planar equivalente a 24.135 m². Ela não permite validar implantação
final, drenagem, acessibilidade altimétrica, área legal, recuos ou licenciamento.
Os bloqueadores `SITE_TOPOGRAPHY`, `SITE_BOUNDARY`, `SITE_FRONTAGE_COUNT` e
`SITE_TRUE_NORTH` permanecem no registro; a lista completa e as ações para
resolvê-los está em [missing-data.yaml](../../project/site/missing-data.yaml).

Confiança na decisão de ausência: **0,95** (`confidence: 0.95`). Confiança de que a geometria
provisória represente o lote real: **0,20**; ela continua explicitamente
provisória e restrita a `STUDY`.

Essa decisão deve ser lida explicitamente como `PROVISIONAL_ASSUMPTION`; ela não
autoriza converter a área retangular em limite cadastral, cota ou disponibilidade
real do terreno.

O portal oficial [GeoNatal](https://geomapas.natal.rn.gov.br/) confirma que a
Prefeitura publica camadas de quadras e parcelas (lotes), mas nenhuma parcela
identificada do CPChoque foi capturada no conjunto de fontes deste run. A
obtenção futura deve seguir a documentação de [limites da
SEMURB](https://www2.natal.rn.gov.br/semurb/paginas/File/Formularios/SEMURB-RequerimentoDGSIG.pdf)
e fornecer polígono, sistema de coordenadas e levantamento independente antes
de qualquer promoção para `VERIFIED_CADASTRAL` ou `VERIFIED_TOPOGRAPHY`.

Registro estruturado da resolução: `project/site/missing-data.yaml`,
`resolution.resolution_id = P08-T03-SITE-001`.
