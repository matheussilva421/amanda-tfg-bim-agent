# AMANDA-RUN-001 — comparação dos finalistas

**Status deste documento:** DRAFT/PENDING — insumo de P08-T09. A recomendação abaixo é delegada ao agente e aguarda revisão de Amanda/Matheus. Este documento não altera `state/`, não grava seleção no decision-register e não muda o status de nenhuma tarefa.

**Caminho canônico:** o plano `docs/superpowers/plans/08-amanda-production-run.md` fixa `solutions/finalists/comparison.md` para P08-T09. O mesmo caminho aparece no plano combinado de revisão. Portanto, este é o arquivo canônico; não foi usado o fallback `design-engine/runs/AMANDA-RUN-001/finalists/comparison.md`.

**Data da análise:** 2026-09-15 23:49:41 -03:00. **Dados examinados:** somente os artefatos dos dois finalistas, o programa/site em disco e o código de scoring/refinamento citado abaixo. Os PNGs `floorplan` e `zoning` dos dois candidatos foram inspecionados visualmente.

## Resultado executivo

| Critério | AMANDA-RUN-001-F01 | AMANDA-RUN-001-F02 |
|---|---:|---:|
| status / hard violations | `VALIDATED` / `[]` | `VALIDATED` / `[]` |
| `requirements_version` / `site_version` | `requirements-v1` / `site-v1` | `requirements-v1` / `site-v1` |
| geometria | hash `5bc3622e...9803ca` | hash `f76d48ca...6ef495e` |
| blocos | 6; áreas 53, 209, 52, 80, 81, 151 m² | 6; mesmas áreas e logical IDs |
| salas | 52; mesmos logical IDs, geometrias diferentes | 52; mesmos logical IDs, geometrias diferentes |
| área líquida interna | 626,0 m² | 626,0 m² |
| área externa programada contabilizada | 260,0 m² | 260,0 m² |
| pavimentos | 1,0 | 1,0 |
| `gross_footprint_m2` | **779,2601058453175 m²** | **1269,3525498596537 m²** |
| `net_to_gross_factor` | 0,8033261234654565 | 0,49316480285103936 |
| `weighted_total` | **0,8415491821831452** | **0,8415491821831452** |
| `approval_hash` | `67e502d8d224c069320bbaa8faacb704f1a29dc75440b711442df1abd621c08b` | `bc34cdbe95bf41c904ea75a6bf0fa559150bd7ed351ce6104c54624f296d1293` |

Origem da tabela: `solution.json`, `metrics.json`, `validation.json`, `penalties.json` e `geometry.geojson` em [F01](../../design-engine/runs/AMANDA-RUN-001/finalists/AMANDA-RUN-001-F01/) e [F02](../../design-engine/runs/AMANDA-RUN-001/finalists/AMANDA-RUN-001-F02/). Os dois `artifact-manifest.json` foram rechecados contra os bytes em disco; todas as entradas de ambos os manifestos conferiram.

## Implantação e previews

As geometrias dos blocos, macrozonas, salas e espaços externos não são iguais, embora preservem os mesmos identificadores e áreas programáticas. No `geometry.geojson` e no SVG, F01 organiza as sete macrozonas como faixas verticais: `SEC-07` ocupa o lado x=0–22,19 e `SEC-01` o lado x=133,16–155,35. F02 as organiza como faixas horizontais: `SEC-07` ocupa y=0–22,19 e `SEC-01` y=133,16–155,35. O quadrado do site é o mesmo placeholder planar.

Nos `floorplan.png`, F01 mostra os seis blocos azuis como retângulos altos e estreitos separados na faixa central; F02 mostra os mesmos seis blocos como retângulos largos e baixos, distribuídos verticalmente. Nos `zoning.png`, a troca aparece como sete bandas verticais em F01 contra sete bandas horizontais em F02. Os espaços externos verdes ficam no canto inferior esquerdo do placeholder nos dois; F01 forma um arranjo compacto em duas linhas, enquanto F02 se alonga predominantemente na horizontal. Isso descreve a implantação no plano local do artefato, sem atribuir norte, frente ou acesso reais.

Há previews 2D (`floorplan.png/svg` e `zoning.png/svg`) para os dois finalistas. Não há preview 3D nos diretórios dos finalistas; nenhum foi inventado ou produzido nesta tarefa. A criação de massing Revit/3D permanece dependente de P08-T08.

## De onde vem o `gross_footprint_m2`

Cada sala publicada possui `net_area_m2`, `gross_footprint_m2`, `wall_thickness_m=0,2`, `shafts_m2=0` e `circulation_m2=0`. Em `src/amanda_agent/design/rooms.py:184-196`, o cálculo é:

```text
wall_area = perímetro da geometria da sala × 0,2
gross_footprint_m2 = net_area_m2 + wall_area
```

Em `src/amanda_agent/design/rooms.py:205-216`, o accounting da refinação soma `gross_footprint_m2` de todas as salas. Depois, `src/amanda_agent/design/refinement.py:286-302` acumula esse accounting por bloco e `src/amanda_agent/design/refinement.py:345-351` recalcula `wall_area_m2` a partir do bruto menos o líquido. A soma independente dos 52 valores por sala fecha com o accounting publicado:

| Soma independente dos quartos | F01 | F02 |
|---|---:|---:|
| `sum(room.net_area_m2)` | 626,0000000000002 m² | 626,0000000000002 m² |
| `sum(room.gross_footprint_m2)` | **779,260105845318 m²** | **1269,35254985965 m²** |
| `geometry.accounting.gross_footprint_m2` | **779,260105845318 m²** | **1269,352549859654 m²** |
| diferença da soma para o accounting | ≈ 0 m², arredondamento binário | ≈ 0 m², arredondamento binário |
| `wall_area_m2` | 153,2601058453173 m² | 643,3525498596534 m² |

Assim, o bruto não vem da soma das áreas dos blocos — que permanece 626 m² —, mas da soma das áreas líquidas das salas acrescidas dos perímetros de parede. A orientação/alongamento altera os perímetros das salas: F02 usa faixas muito rasas ao longo da largura do bloco, produzindo mais parede contabilizada; F01 usa faixas mais profundas, produzindo menos parede. Os valores publicados fecham.

## Por que a nota é idêntica

**Fato destacado:** a nota `0,8415491821831452` é exatamente igual nos dois finalistas apesar de F02 ter **490,0924440143362 m²** a mais de `gross_footprint_m2` que F01. A causa está determinada no pipeline atual:

1. `src/amanda_agent/design/refinement.py:568-629` constrói `raw_metrics` sem qualquer dimensão `gross_footprint_m2`, `wall_area_m2` ou `net_to_gross_factor`.
2. `program_compliance` usa somente o desvio entre `internal_net_area_m2`/`external_area_m2` contabilizados e os alvos do programa; ambos têm 626,0/260,0, logo 1,0.
3. `privacy_security` usa a sequência fixa de níveis dos setores presentes `[0, 1, 2, 2, 3, 5]`, não o perímetro ou a forma; ambos dão 0,5.
4. `adjacency` usa as distâncias médias entre blocos. A evidência publicada é idêntica nos dois: `mean_interblock_distance_m=36,2962350928524` e `score=0,9415912467362131`. A implantação ortogonal preserva essas distâncias e o perímetro do site placeholder.
5. `circulation` conta somente quantos dos seis resultados têm `ok=true` (`sum(bool(ok))/6`); não usa a distância do caminho. Os dois têm cinco rotas `ok` e a rota de emergência `ok=false` por cruzar residência privada, portanto 0,8333333333333334. As distâncias são diferentes: residente F01/F02 = 328,63157506165516/219,21778441518398 m; emergência = 364,8676431648442/224,39436557278236 m.
6. `accessibility` compara três salas requeridas com três salas geradas e dá 1,0. `green_integration` compara apenas 260,0 m² externos gerados com 260,0 m² requeridos e dá 1,0.
7. `compactness` usa `unary_union` dos polígonos dos seis blocos e a razão área/perímetro em `refinement.py:612-614`; não usa o bruto das salas. As formas de bloco são ortogonais entre os finalistas, preservando o resultado 0,06141644628426339.
8. `constructability` é atribuído literalmente como `1.0` em `refinement.py:624-627` depois que as violações duras passam; portanto não discrimina o excesso de parede ou de área. `concept_fidelity` também é 1,0 nos dois.

Em `metrics.json`, `solar_heuristic` e `ventilation_heuristic` são `null` e estão em `not_evaluated`. `src/amanda_agent/design/scoring.py:84-109` exclui valores ausentes e redistribui seus pesos entre as dimensões avaliadas. Os dois recebem os mesmos valores, pesos e contribuições; por isso o total também é o mesmo. O `weights.yaml` registra 0,18/0,14/0,10/0,10/0,12/0,06/0,06/0,06/0,05/0,08/0,05; os dois pesos ambientais ausentes somam 0,12 e são reponderados.

## Programa e critérios de seleção

### FATOS

- `project/requirements/program.json:18-27` fixa 626,0 m² úteis internos, 260,0 m² externos e estimativa de **783–814 m² fechados construídos**. A reconciliação do programa está `ok=true`.
- Os seis logical IDs de bloco são `SEC-01-block-1`, `SEC-02-block-1`, `SEC-03-block-1`, `SEC-04-block-1`, `SEC-05-block-1` e `SEC-06-block-1`; a sequência de áreas é 53, 209, 52, 80, 81 e 151 m² nos dois artefatos.
- Comparação literal da estimativa fechada com o bruto: F01 tem 779,2601058453175 m², portanto fica **3,7398941546825 m² abaixo do piso**; F02 tem 1269,3525498596537 m², portanto **estoura o teto em 455,3525498596537 m²**. Logo, nenhum está dentro da faixa; F01 é o único próximo/aderente por magnitude e F02 é o que estoura.
- `validation.json` dá `status=PASS` e `hard_violations=[]` nos dois, mas o check `gross_area_budget` está `NOT_EVALUATED` na resolução de bloco. Esse PASS não valida a faixa 783–814.
- Privacidade: ambos têm `privacy_security=0,5`, `privacy_gradient=1,0` e não registram transição pública direta para residencial.
- Fluxos: ambos têm `circulation=0,8333333333333334`; cinco dos seis fluxos estão `ok`, e a emergência falha com `private_residential_access`, 17 cruzamentos, nos dois.
- Acessibilidade potencial: ambos têm `accessibility=1,0`, com `required_accessible_rooms=3` e `generated_accessible_rooms=3`.
- Solar e ventilação: ambos estão `NOT_EVALUATED`; `site.true_north` é nulo. Não há nota solar/ventilação real para desempatar.
- Espaço externo: ambos contabilizam 260,0 m² para os cinco espaços programados de 80, 80, 30, 30 e 40 m²; `green_integration=1,0`. A posição relativa difere nos previews.
- Constructabilidade registrada: ambos têm `constructability=1,0`; essa igualdade é efeito do código e dos checks duros, não uma validação executiva de custo, estrutura ou parede.
- Proveniência: `WHY_THIS_OPTION.md` descreve os mesmos pontos fortes e trade-offs para ambos; `artifact-manifest.json` confirma os artefatos publicados, com hashes distintos para as geometrias e previews.

### RESTRIÇÕES

- O site é `STUDY_PLACEHOLDER` planar; `project/site/site.json` não fornece polígono cadastral, topografia, acessos candidatos ou norte verdadeiro. A contagem de frentes também está conflitante no próprio material de origem.
- A faixa 783–814 m² é uma estimativa aceita do programa, não foi convertida em hard check na validação atual; a comparação acima é uma checagem documental independente.
- Nenhuma conformidade normativa, dimensão mínima normativa, rota de fuga normativa, custo, estrutura, instalação ou desempenho ambiental físico foi verificada.
- P08-T09 exige uma comparação e uma escolha delegada; a escolha abaixo é `DRAFT/PENDING`, com `selection_authority=AGENT_DELEGATED` proposto, `decider=agent` e `amanda_review=AMANDA_REVIEW_PENDING`. Ainda não existe `APPROVED_FOR_BIM` neste documento.
- Não registrar esta proposta em `state/` e não alterar o status de P08-T09 são limites desta tarefa.

### HIPÓTESES

- A diferença de implantação visual pode ser lida como duas orientações alternativas do mesmo programa no plano local; sem norte, topografia ou acesso, não se pode afirmar que uma orientação seja solarmente melhor.
- O maior bruto de F02 é uma hipótese de maior envelope construtivo decorrente das faixas de salas e da soma de paredes; ele precisa ser rechecado no BIM antes de qualquer decisão executiva.
- A descrição de interface pública controlada e gradiente de privacidade em `WHY_THIS_OPTION.md` é hipótese de partido, não evidência de segurança operacional.

## Recomendação delegada — DRAFT/PENDING

Recomendo seguir **AMANDA-RUN-001-F01** para a próxima etapa BIM conceitual, condicionada à revisão posterior de Amanda/Matheus. O desempate é documental: as notas automatizadas empatam e não capturam o bruto; F01 é muito mais próximo da estimativa fechada aceita (779,2601 m² contra 783–814 m²) e acumula 153,2601 m² de parede contra 643,3525 m² em F02. F01 ainda precisa de ajuste/checagem para alcançar o piso de 783 m²; F02 exigiria uma redução de 455,3525 m² para não estourar o teto, além de revisão da implantação.

```yaml
selection_status: DRAFT_PENDING
proposed_solution_id: AMANDA-RUN-001-F01
selection_authority: AGENT_DELEGATED
decider: agent
timestamp: 2026-09-15T23:49:41-03:00
amanda_review: AMANDA_REVIEW_PENDING
approval_hash: 67e502d8d224c069320bbaa8faacb704f1a29dc75440b711442df1abd621c08b
state_registration: NOT_PERFORMED
task_status_change: NOT_PERFORMED
```

## Não verificado e retomada

Não foram verificados: **topografia real, norte verdadeiro, acesso/frentes reais e custo**. Também não foram verificados em campo ou em Revit o envelope construtivo, estrutura, instalações, acessibilidade normativa, segurança operacional, desempenho solar/ventilação ou aprovação de Amanda. Próxima retomada: revisar esta comparação, validar F01 contra a faixa de 783–814 m² no fluxo BIM autorizado, manter o hash/versão vinculados e somente então decidir se há base para uma seleção formal.

## Handoff desta análise

- Alteração desta sessão: criado somente `solutions/finalists/comparison.md`; nenhum arquivo de estado, tarefa, solução finalista ou artefato de terceiro foi revertido ou alterado.
- Validação executada: inspeção visual dos quatro PNGs; reconciliação PowerShell dos JSON; soma independente dos grossos por sala; conferência SHA-256 de todas as entradas dos dois `artifact-manifest.json`; verificação de seções/literais e espaços finais do documento. `pytest` não foi executado por instrução.
- GitHub: nenhum `git add`, commit ou push. O worktree permanece com alterações pré-existentes de outros agentes; o novo arquivo aparece como `?? solutions/finalists/comparison.md`.
- Retomada: revisão humana desta comparação; depois P08-T08/P08-T09 conforme o plano, sem promover esta proposta a `APPROVED_FOR_BIM` até a revisão e as verificações pendentes.
