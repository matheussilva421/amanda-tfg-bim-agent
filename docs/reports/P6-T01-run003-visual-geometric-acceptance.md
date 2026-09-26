# P6-T01 — RUN-003 R04: evidência visual e geométrica

**Atualização:** 2026-09-26 17:32 UTC
**Status:** `PENDING` — `CANON-011` permanece aberto. Esta atualização registra a geometria R04 recém-salva; não encerra a aceitação nem autoriza R05.

## Referências e critérios

As quatro pranchas canônicas atuais foram vinculadas, nesta ordem: `01_implantacao.png`, `02_administrativo.png`, `03_residencial.png` e `04_servicos.png`. Seus SHA-256 são `30d00935…20240`, `123b9563…a263`, `5b96c2d5…31381` e `c56b806f…c0386`. O PDF oficial `docs/source/programa_necessidades.pdf` (SHA-256 `11daa9ef…14a17`) continua sendo a autoridade para capacidade de 20 pessoas, 626 m² internos úteis e 260 m² externos programados. Áreas impressas nas pranchas não foram tratadas como áreas oficiais.

Implantação segue em coordenadas locais normalizadas, não levantadas. As relações cardeais são interpretações do arranjo das pranchas no modelo de estudo; não comprovam norte geográfico, limites, frentes, topografia ou implantação cadastral.

## Geometria R04 criada e verificada no Revit

Após BIM-00 `PASS`, a gravação tipada adicionou 18 elementos ao RUN-003: 14 pisos e quatro coberturas. A consulta tipada independente após salvar, fechar e reabrir retornou 25 elementos no total (sete massas existentes, 14 pisos e quatro coberturas), cobertura completa e zero elementos ilegíveis.

- **Implantação:** cinco superfícies externas correspondem ao programa PDF: pátio protegido 80 m², jardim terapêutico 80 m², horta 30 m², exercícios 30 m² e playground 40 m². O administrativo permanece na borda pública sul; residencial no interior/norte do estudo; serviço/capacitação a sudeste; setor infantil a oeste; o jardim terapêutico ocupa a faixa central.
- **Acessos:** pisos distintos marcam `PATH-PUBLIC-ADMIN`, `PATH-PUBLIC-SERVICE` e `PATH-SERVICE-CARGO`. As larguras 2/2/3 m são hipóteses geométricas do estudo e não entram no programa. Os percursos públicos e de carga não se sobrepõem; portas e entradas edificadas não foram modeladas.
- **Administrativo:** pisos de térreo e superior foram modelados no envelope. A área medida é 237,407 m² por pavimento frente à indicação aproximada de 200 m² da prancha (+37,407 m² / +18,7%). A divergência está aberta. O nível Revit `Nível 2` está a 4,0 m enquanto a face superior do piso é 3,2 m (offset −0,8 m); isso também permanece registrado. Não foram modeladas salas nem atribuições de função.
- **Residencial:** há quatro massas independentes (A/B/C familiares e D comunitária) e quatro pisos com coberturas, sem paredes de fechamento. Cada circulação coberta tem interface de 2 m com o pátio; o pátio de 80 m² permanece livre, sem intrusão medida. Contagem de dormitórios por família e dormitório comunitário ainda não está modelada como salas.
- **Serviços/capacitação:** a composição curva existente envolve o pátio/jardim com seis anéis internos; não foi substituída por footprint retangular genérico. O percurso público chega pelo lado oeste e a rota de carga pelo lado leste. Funções impressas e áreas por função não foram convertidas em salas ou tomadas como áreas oficiais; a reconciliação funcional segue aberta.
- **Infantil:** a superfície de playground de 40 m² foi colocada junto à massa infantil oeste. Brinquedoteca, apoio pedagógico, banheiro e depósito não foram modelados como salas; a reconciliação funcional segue aberta.

## Persistência e evidência

Horizun 1.3.3 estava `HEALTHY`, registry 73/73 limpo, 80/80 ferramentas visíveis. Revit 2027, build 27.2.0.39, PID 38296; o arquivo RUN-003 exato estava ativo e targetable, sem outros clientes. Durante a gravação, o lease exclusivo `amanda-P4-T01-RUN003-R04` foi vinculado ao alvo e liberado após a verificação.

O salvamento alterou o arquivo de 4.612.096 para 4.952.064 bytes, SHA-256 de `7097faf9…761095` para `33a99c7c…cca27b49`. O checkpoint `R04-T01-RUN003-POST-SAVE.rvt` e manifesto foram verificados; o alvo foi fechado e reaberto no caminho exato sem upgrade. A leitura tipada pós-reabertura confirmou os 25 elementos.

A captura `views/r04-canonical-site-revit-2026-09-26.png` (2400×1459, SHA-256 `c3759ce9…d979b0f`) é uma vista wireframe real do Revit, com enquadramento parcial. Ela apoia a existência dos elementos, mas não fecha o critério visual CANON-011. As seis capturas P6 anteriores foram feitas antes deste salvamento e não representam o estado atual.

## Testes e decisão

`tests/unit/test_run003_r04_spatial_evidence.py` foi executado em RED antes da atualização do registro; encontrou o placeholder de SHA no manifesto. Corrigido o manifesto com o hash verificado. Resultado GREEN: 1 teste espacial aprovado. A validação focada adicional de `test_task_graph.py` e `test_state_store.py` passou com 21 testes; `tests/policy/test_plan_order.py` passou com 7. O teste novo da cadeia P4→P5→P6 também foi RED antes de adicionar essas arestas auxiliares ao contrato. `CheckpointManager.verify_checkpoint` retornou `True`. O Python padrão não contém `ortools`; a coleta do teste `test_status_dashboard.py` foi bloqueada por essa dependência ausente. Os testes focados foram executados com `--confcutdir`, sem instalar ou atualizar dependências.

**Decisão:** manter `P6-T01` `PENDING` e `CANON-011` aberto. As pendências são o desvio administrativo de área e nível, atribuições internas do administrativo/serviços/infantil e dormitórios, validação visual do conjunto e cinco limitações de dados do terreno. Nenhuma pesquisa GeoNatal ocorreu; RC01 não foi alterado; R05 não foi executado nem autorizado.
