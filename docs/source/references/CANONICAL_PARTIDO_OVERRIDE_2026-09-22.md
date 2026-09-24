# Override canônico — partido obrigatório das pranchas de 2026-09-22

## Decisão do usuário

As quatro pranchas canônicas incluídas neste pacote são a **fonte oficial de partido arquitetônico**. O projeto BIM deve ficar **materialmente igual às plantas**, não apenas inspirado nelas.

Esta instrução supersede a seleção linear atual `AMANDA-RUN-001-S01`, o arquétipo `COURTYARD_DOUBLE_LOADED_BAR` e qualquer justificativa anterior que tenha escolhido uma barra única por conveniência de área/construtibilidade.

## O que “igual às plantas” significa

O modelo final deve reproduzir, na máxima fidelidade compatível com dados verificados:

- **implantação em blocos/pavilhões**, e não uma barra única;
- **bloco administrativo/acolhimento** na interface pública, com a lógica da prancha administrativa;
- **bloco administrativo em dois pavimentos** conforme a prancha, salvo impedimento normativo/técnico demonstrado;
- **conjunto residencial em quatro pavilhões funcionais** ao redor de pátio/jardim: três pavilhões de dormitórios e um pavilhão de convivência/refeitório/apoio;
- **pátio/jardim terapêutico central** como elemento organizador;
- **setor infantil** integrado às áreas verdes;
- **serviços/capacitação** em bloco próprio conforme a prancha 04, com pátio/jardim, circulação coberta e acesso de carga/serviço separado do acesso principal;
- **percursos externos/cobertos** conectando os blocos;
- gradação **cidade → acolhimento → convivência/transição → abrigo/proteção**;
- escala residencial doméstica, acolhedora e paisagística.

## Fontes que continuam prevalecendo para números

As pranchas não substituem:

- `docs/source/programa_necessidades.pdf` para programa, capacidade e áreas;
- levantamento/polígono/topografia/norte verdadeiros quando forem verificados;
- normas aplicáveis com fonte/versionamento verificados.

Programa obrigatório:
- até 20 pessoas;
- 626 m² úteis internos;
- 260 m² externos programados;
- 783–814 m² fechados estimados;
- 850–950 m² cobertos estimados.

A hipótese de 42 pessoas permanece rejeitada/histórica.

## Política de desvio

A geometria/setorização das pranchas é canônica. Um desvio relevante só pode ocorrer por incompatibilidade demonstrada com programa oficial, terreno verificado, acessibilidade, norma ou construtibilidade. Todo desvio deve ser registrado como `CANONICAL_DEVIATION` contendo:

- elemento afetado;
- referência canônica;
- motivo verificável;
- alternativas tentadas;
- impacto;
- aprovação/autoridade da decisão;
- hashes de entrada e saída.

Não é permitido voltar à barra linear apenas porque ela é mais simples, barata de modelar ou cai melhor no intervalo estimado de área.

## Estado legado

O atual R12 linear do repositório é evidência histórica e deve ser arquivado como `SUPERSEDED_BY_USER_DIRECTION`. Preserve uma única cópia fechada/hashada para histórico; não a use como base geométrica do novo BIM.
