# P1-T01 — Reconciliação das quatro pranchas

**Resultado:** reconciliação de geometria e atribuições concluída em modo pré-modelo. Nenhum artefato BIM foi emitido e nenhuma escrita no Revit ocorreu.

## Autoridades verificadas

| Fonte | Identidade |
|---|---|
| `01_implantacao.png` | SHA-256 `30d009357a095e7794e0e915dcd2fdb04cd6b9aab9f4d13f5663ed54d6f20240` |
| `02_administrativo.png` | SHA-256 `123b95633ae1be643da84f2226c6337d65a74f7d1337d6b27d94bdead1c3a263` |
| `03_residencial.png` | SHA-256 `5b96c2d5cc770742ee32d51b83b25993fe8b8a1638bf94da56ba8ef771031381` |
| `04_servicos.png` | SHA-256 `c56b806f805d9c4aa1e6015ba6b56ac960204066721f93ef08cbadfb312c0386` |
| Programa oficial | [`programa_necessidades.pdf`](../../source/programa_necessidades.pdf), SHA-256 `11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17` |

O perfil e o manifesto validam os quatro caminhos e hashes byte a byte. O programa mantém capacidade simultânea de **20 pessoas**, **626 m² internos** e **260 m² externos**. As áreas estimadas de referência continuam 783–814 m² fechados e 850–950 m² cobertos.

## Geometria e atribuições reconciliadas

- **Implantação:** residências protegidas no norte/interior; bloco administrativo junto à borda pública sul; serviços/capacitação no sudeste; setor infantil a oeste/centro-oeste junto ao playground; jardim terapêutico central; horta a leste. Entrada pública do conjunto e acesso de carga/serviço são pontos distintos.
- **Administrativo:** térreo contém recepção, espera, triagem, registro, controle, psicologia, serviço social, jurídico, reunião, arquivo/apoio técnico, copa comunitária e sanitário acessível. Os ambientes oficiais são SEC-01 REQ-01-01 a 05; SEC-04 REQ-04-01 a 04 e REQ-04-06; e SEC-05 REQ-05-03/04 (8 m² e 5 m²). A copa e o sanitário mantêm os IDs/áreas do PDF, mas seguem a localização explícita da prancha 02; não são duplicados no bloco de serviços. O superior contém multiuso/grupos, coordenação, secretaria/administrativo, equipe, refeitório/copa e sanitário/vestiário de funcionários (REQ-04-05 e REQ-06-01 a 05). O PDF tem um único REQ-04-06 de 5 m²: ele está no térreo; o rótulo superior duplicado “Apoio/Arquivo 5 m²” não cria outro ambiente.
- **Residencial:** quatro pavilhões independentes. A contém dois quartos individuais, dois duplos e dois banheiros comuns; B contém dois triplos familiares, o quarto familiar ampliado e dois banheiros comuns; C contém quarto acessível, o terceiro quarto duplo, um banheiro comum e um acessível; D contém convivência, refeitório e copa residenciais. A prancha 03 desenha seis células de banheiro comum; o PDF exige cinco. Mantemos os cinco ambientes oficiais (distribuição 2/2/1) e um banheiro acessível; a sexta célula permanece símbolo gráfico não aditivo, sem identificação inequívoca de qual célula é excedente. O pátio protegido de 80 m² permanece livre entre eles e recebe circulação externa/semiaberta coberta.
- **Serviços/capacitação:** o footprint retangular genérico foi substituído por uma composição curva conectada que envolve um pátio de projeto. Esse pátio não é um ambiente do programa e não entra nos 260 m² externos. O bloco sudeste contém SEC-05 REQ-05-01/02 e SEC-06 REQ-06-06 a 15, cada um uma vez nas áreas oficiais; REQ-05-03/04 ficam no térreo administrativo conforme a prancha 02. Acesso de pedestres pelo campus e acesso de carga junto ao ambiente oficial de carga/descarga são separados.
- **Infantil:** brinquedoteca (24 m²), apoio pedagógico/estudos (18 m²), banheiro (6 m²) e depósito de brinquedos (4 m²) permanecem no bloco oeste e próximo ao playground.

## Prancha 04 × programa oficial

As áreas na coluna da prancha são leitura gráfica e **não** são usadas para dimensionar ou somar o programa. As 12 etiquetas de ambiente com área somam 289 m² na prancha; isso não inclui pátio nem circulação.

| Função/área impressa na prancha 04 | Linha oficial aplicável | Reconciliação |
|---|---|---|
| Sala Multiuso — 50 m² | SEC-05 Salão multiuso — 1 × 60 m² | A área oficial é 60 m² (diferença −10 m²). SEC-04 Sala multiuso/grupos — 1 × 30 m² é outra linha e outro setor. |
| Informática — 30 m² | Nenhuma sala oficial com esse nome | Uso sem área oficial própria. Pode ser estudado como modo de operação, sem assumir que o PDF o especifica nem criar área adicional. |
| Oficina de Costura e Artesanato — 40 m² | Nenhuma sala oficial com esse nome | Uso sem sala/área oficial individual. |
| Oficina Prática / Empreendedorismo — 40 m² | Nenhuma sala oficial com esse nome | Uso sem sala/área oficial individual. |
| Recepção / Orientação — 25 m² | SEC-01 Recepção — 1 × 10 m² | Diferença +15 m². “Orientação” não é linha oficial; acolhimento/triagem (12 m²) e controle de acesso (6 m²) são ambientes separados. |
| Sanitário Feminino Acessível — 18 m²; Masculino Acessível — 18 m² | SEC-05 REQ-05-04 — 1 × 5 m² | Prancha 04 mostra 2 ambientes/36 m²; o PDF pede 1/5 m² (+31 m² e diferença de quantidade) e não divide por sexo. A única sala oficial de 5 m² fica no térreo administrativo, onde a prancha 02 a desenha com área exata; os rótulos de 18 m² da prancha 04 não criam salas adicionais. |
| Apoio / Depósito — 12 m² | SEC-05 Depósito de cadeiras/material — 8 m²; SEC-06 Depósito geral — 6 m² | O rótulo não permite correspondência unívoca. Não se converte em um depósito oficial de 12 m². |
| DML — 6 m² | SEC-06 DML — 1 × 3 m² | Diferença +3 m² na prancha. |
| Rouparia / Almoxarifado — 15 m² | SEC-06 Rouparia — 6 m² e Almoxarifado — 8 m² | PDF separa duas salas, total 14 m²; prancha combina as funções (+1 m²). |
| Lavanderia — 20 m² | SEC-06 Lavanderia — 1 × 12 m² | Diferença +8 m² na prancha. |
| Copa de Apoio — 15 m² | SEC-05 REQ-05-03 — 1 × 8 m² | Diferença +7 m². A única copa comunitária oficial de 8 m² fica no térreo administrativo, onde a prancha 02 a desenha com área exata; a representação de 15 m² na prancha 04 não duplica o programa. A copa residencial SEC-02 (12 m²) é distinta. |

## Prancha 03 × programa oficial

| Elemento | Prancha 03 | Programa oficial | Reconciliação |
|---|---:|---:|---|
| Banheiros comuns | 6 células gráficas | SEC-02 REQ-02-06 — 5 × 3,5 m² | Modelar exatamente cinco (2 no pavilhão A, 2 no B e 1 no C), total oficial 17,5 m². A sexta célula não tem correspondência a uma sexta quantidade no PDF e fica como representação esquemática, sem novo ambiente/área. O banheiro acessível REQ-02-07 (4,5 m²) permanece uma unidade. |

O programa ainda exige depósito de cadeiras/material (8 m²), cozinha de produção (25 m²), despensa seca (6 m²), freezer/refrigerados (4 m²), resíduos (4 m²) e ambiente de carga/descarga (15 m²). A prancha não rotula todos com sala/área próprias. O acesso de carga marcado não mede nem substitui o ambiente de 15 m², que foi preservado como requisito oficial.

Na prancha 02, “Arquivo 5 m²” no térreo e “Apoio/Arquivo 5 m²” no superior repetem uma função/área que o PDF especifica uma única vez como SEC-04 REQ-04-06 (5 m²). A reconciliação mantém o ambiente no térreo junto ao atendimento; o rótulo superior é registrado como repetição gráfica, sem segunda sala oficial. A copa e o sanitário do setor oficial SEC-05 também aparecem com outras áreas/quantidades na prancha 04; essas representações não são contadas nem modeladas como novas instâncias.

Os rótulos sem área “Acesso principal pelo campus”, “Acesso principal”, “Acesso de serviço — carga e descarga” e “Circulação Coberta” não viram áreas programadas. “Pátio de Convivência / Jardim Central” também não permite fundir os dois espaços do PDF: pátio interno protegido de 80 m² e jardim terapêutico de 80 m² estão modelados separadamente.

## QA e estado

QA estrutural possui 18 verificações: CANON-001 a CANON-010 e CANON-012 a CANON-018 passam para a geometria reconciliada; CANON-011 permanece **BLOCKED** porque exige comparação visual de etapas Revit, fora de P1-T01. Os testes verificam as quatro referências exatas, zonas de implantação, pavimentos administrativos e apoios SEC-05 no térreo, composição residencial, pátio curvo/acessos, divergências das pranchas 02/04, programa e relação infantil/playground.

S02 permanece `STALE_BY_CANONICAL_REFERENCE_EXPANSION`. `SELECTION_SOLUTION_ID` continua sem identidade atual; o gerador recusa emitir run baseado em S02 e também rejeita as identidades lineares supersedidas `AMANDA-RUN-001-S01` e `AMANDA-RUN-002-PAVILION-S01`. Sem avanço para R04/R05 e sem escrita no Revit. P2-T01, atribuição de nova identidade, é a próxima tarefa pendente.
