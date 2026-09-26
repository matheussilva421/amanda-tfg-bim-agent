# P4-T01 — Continuação R04 do RUN-003

**Data:** 2026-09-26
**Resultado:** BIM-00 `PASS`; geometria R04 real adicionada, salva e reaberta no Revit; `PASS_WITH_WARNINGS`.

## Reconciliação executada

Os quatro arquivos `docs/source/canonical/01_implantacao.png` a `04_servicos.png` foram vinculados por hash. O programa oficial é `docs/source/programa_necessidades.pdf`: 20 pessoas, 626 m² internos e 260 m² externos. O PDF permaneceu autoridade de capacidade e área.

No alvo RUN-003 derivado de template limpo, gravação tipada criou 14 pisos e quatro coberturas: dois pisos administrativos; as cinco superfícies externas oficiais (80/80/30/30/40 m²); quatro circulações residenciais cobertas/semiabertas com coberturas; e três percursos marcados de acesso público/administrativo, público/serviços e carga. Após reabertura, a consulta tipada cobriu 25 elementos, com sete massas, cobertura completa e zero ilegíveis.

A composição curva de serviços/capacitação e seus seis vazios internos foram preservados. O pátio central de 80 m² permanece sem intrusão; os quatro conectores têm interfaces de 2 m. O playground de 40 m² foi aproximado da massa infantil oeste. Todas as relações permanecem em estudo local não levantado.

## Divergências abertas

- Piso administrativo superior: face a 3,2 m associada ao `Nível 2` a 4,0 m (offset −0,8 m). Área por pavimento medida: 237,407 m² versus rótulo aproximado de 200 m² na prancha (+18,7%).
- As pranchas listam funções, mas administrativo, serviços/capacitação e infantil ainda não têm salas/áreas funcionais modeladas. Não foram inventadas áreas para fazê-las caber.
- Os três percursos usam larguras 2/2/3 m como hipóteses locais. Não modelam portas nem estabelecem acesso cadastral/geográfico.
- Limites, topografia, ocupação, frentes e norte verdadeiro do lote continuam sem comprovação.

## Persistência e próximos passos

RVT salvo com SHA-256 `33a99c7c760125da434017210b7ea2d506a3914ae59e002769a14138cca27b49` (4.952.064 bytes); checkpoint e manifesto independentes conferidos; fechamento e reabertura do alvo exato em Revit 2027 sem upgrade; consulta tipada pós-reabertura completa. A captura wireframe é somente evidência auxiliar. O teste espacial focado passou (1); task graph/estado passaram (21); contrato de ordem P4-P6 passou (7); verificação do checkpoint retornou `True`. Uma coleta adicional do dashboard não pôde importar `ortools`, ausente no ambiente; nenhuma dependência foi instalada.

**Estado:** `P6-T01` permanece `PENDING` / `CANON-011 OPEN`. Próximo trabalho permitido: aceitação visual/geométrica P6-T01 e resolução documentada das divergências dentro do escopo autorizado. R05 não foi feito nem autorizado. RUN-003 foi usado; S01/S02/R12 e RC01 não foram usados/modificados; nenhuma nova pesquisa GeoNatal foi feita.
