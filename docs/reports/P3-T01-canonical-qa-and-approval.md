# P3-T01 — QA canônica e candidato

**Status:** PASS — revisão independente final sem achados.

## Identidade e fontes

O candidato é `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`, fingerprint
`4b1275558a6c2c40828dbba1422c0063703c182fd9d7b800b36a448499a073c4`. Ele
carrega exatamente estas quatro pranchas do perfil canônico:

- `01_implantacao.png` — `30d009357a095e7794e0e915dcd2fdb04cd6b9aab9f4d13f5663ed54d6f20240`
- `02_administrativo.png` — `123b95633ae1be643da84f2226c6337d65a74f7d1337d6b27d94bdead1c3a263`
- `03_residencial.png` — `5b96c2d5cc770742ee32d51b83b25993fe8b8a1638bf94da56ba8ef771031381`
- `04_servicos.png` — `c56b806f805d9c4aa1e6015ba6b56ac960204066721f93ef08cbadfb312c0386`

Também vincula o PDF oficial
`programa_necessidades.pdf` (SHA-256
`11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17`) e o
relatório P1-T01 (SHA-256
`8d297d9c35e0fcdec8b36e5857e03c9e992cbfeb9dab082dddf2106a2ed5025b`). O
programa oficial permanece em 20 pessoas, 626 m² internos e 260 m² externos.
Nenhuma área oficial foi ajustada para acomodar o estudo.

## Resultado estrutural

O QA emitiu 18 IDs distintos, CANON-001 a CANON-018: **17 PASS, 0 FAIL, 1
BLOCKED**, sem falhas críticas. CANON-011 permanece BLOCKED até que as etapas
Revit exigidas forneçam evidência visual. As demais verificações cobrem a
implantação sul/norte/oeste/sudeste/leste, administração em dois pavimentos,
quatro pavilhões residenciais, jardim central, circulação coberta externa,
composição curva de serviços com pátio, entradas pública e de carga separadas,
setor infantil junto ao verde/playground e correspondência quantitativa ao
programa.

Hashes do candidato:

- layout: `7fde3e34a162167ce27fe2e3158a38f446882816a7c81bb326d486bdfaaae2e2`
- aprovação de conteúdo: `eea4a342a4d732cbc986a16d01d93e3981e79a5931f8d99ebef82c61d24299ec`
- decisão de detalhe `DEC-CANONICAL-DETAIL-003`:
  `f37c5c8c2f4f43e957429bd05dbc659012a7f6eaa0b0be65e23cbf7f47c43efc`

O artefato foi gerado em
`design-engine/runs/AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C/`; os seis
arquivos do manifesto conferem em tamanho e SHA-256. `bim_eligible` é `false`,
`revit_calls` é `0`, `PROJECT_STATE.selected_design` continua `null`, e a
decisão segue provisória, `BLOCKED_BY_INPUT` e `AMANDA_REVIEW_PENDING`. O
`approval_hash` do artefato é um vínculo determinístico de conteúdo, não uma
aprovação humana nem autorização BIM. Este é o snapshot histórico produzido em
P3. Durante P4-T01, o sucessor delegado `DEC-CANONICAL-DETAIL-004` autorizou
somente estudo normalizado até R04; o snapshot atual correspondente foi gerado
separadamente em
`design-engine/runs/AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C-study-detail-004/`.
O snapshot P3 foi preservado sem sobrescrita.

## Divergências preservadas

- A prancha residencial mostra seis células de banheiro comum; o PDF oficial
  exige cinco. A sexta célula continua esquemática e não aditiva.
- As pranchas administrativa e de serviços repetem ou divergem em arquivo,
  copa e sanitário; a localização reconciliada segue a prancha administrativa,
  mas quantidade e áreas seguem o PDF.
- A prancha de serviços nomeia informática, costura/artesanato e
  empreendedorismo sem linhas/áreas oficiais individuais. São usos de
  capacitação, sem criação de áreas programáticas adicionais. As demais
  divergências de áreas e depósitos permanecem no relatório P1-T01.
- CANON-011 depende de validação visual posterior. A implantação é referência
  normalizada, não levantamento; topografia, limite, ocupação, quantidade de
  frentes e norte verdadeiro continuam com os estados registrados no projeto.

## Verificação e limites

- `.venv/Scripts/python.exe -m pytest tests/unit/test_build_canonical_pavilion_run.py tests/unit/test_canonical_solution_identity.py tests/unit/test_production_selection.py tests/unit/test_canonical_qa.py tests/unit/test_decision_register.py tests/project/test_repository_hygiene.py tests/policy/test_plan_order.py -q` — **74 passaram**.
- Testes de estado, task graph e session routing — **55 passaram**.
- Ruff nos arquivos Python alterados — **sem achados**.
- `.venv/Scripts/python.exe scripts/build_canonical_pavilion_run.py` — gerou/revalidou RUN-003; saída determinística, BIM inelegível e zero chamadas Revit.
- Manifesto do candidato — **6/6 artefatos** conferidos por tamanho e SHA-256.
- `.venv/Scripts/pytest.exe tests/unit/test_production_layout_bim.py -q` — **26 passaram, 5 falharam** no preflight R04, todas em `projection_area: MASS-SERVICE_CAPACITATION`. Registrado como bloqueio de planejamento R04; fora do P3 e não corrigido aqui.
- A primeira revisão independente encontrou um bypass de revalidação do hash P1 em chamadas diretas e a ausência da exigência de IDs QA únicos. Ambos foram reproduzidos RED, corrigidos e passaram GREEN. A rechecagem independente confirmou os dois fechamentos, ausência de regressão na CLI e nenhum achado novo; recomendou PASS para P3-T01.
- A revisão final do estado não encontrou achados críticos/importantes; fechou uma lacuna menor parametrizando o teste negativo para todas as arestas P1→P2, P2→P3 e P3→P4.

Nenhum acesso ou escrita Revit ocorreu durante P3. R04/R05 não avançaram. O próximo gate no plano vigente é P4-T01 (BIM-00), sem autorização implícita para R04/R05.
