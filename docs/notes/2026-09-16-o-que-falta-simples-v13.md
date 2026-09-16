# O que falta para o projeto terminar — v13

Data da leitura: 2026-09-16.

## Onde estamos

O projeto já tem a base de dados, o gerador de alternativas, os testes e a ponte com o Revit; ainda não tem modelo de produção, entrega GOLDEN selada ou prova de uso no arquivo final. O estado vivo registra 159 tarefas: 136 PASS, 2 PASS_WITH_WARNINGS, 13 PENDING, 8 SUSPENDED e 0 FAIL; a última tarefa aprovada é P08-T07 e a próxima é P06-T14. Há duas finalistas registradas, F01 e F02, mas selected_design continua null. Revit 2027 está aberto e Horizun 1.3.3 está HEALTHY com full_write; a janela viva mostra LAB_ROUTE_PROBE, portanto LAB_R01_TEMPLATE.rte não foi confirmado como o documento aberto.

## O que falta, em ordem

1. **Ensaio técnico P06-T14.** Falta testar a cadeia R14→R16 em arquivo descartável: QA, salvar, fechar, abrir a frio, reconsultar, exportar, conferir hashes e rejeitar sobrescrita de GOLDEN. Quem faz: agente/IA. Tamanho: G.
2. **Retomada segura P07-T17 e P07-T19.** Falta provar uma sessão nova e uma retomada depois de reinício autorizado, com doctor, status, saúde, checkpoint e reconsulta. Quem faz: agente/IA, com janela de reinício liberada pelo dono. Tamanho: M.
3. **Massas conceituais P08-T08.** Falta criar no Revit as massas das finalistas em CONCEPT_ONLY, R01–R04, com leitura, preview, salvar, fechar e reabrir; o run tem F01 e F02, não uma terceira candidata. Quem faz: agente/IA. Tamanho: G.
4. **Escolha registrada P08-T09.** Falta comparar as massas e registrar exatamente uma solução APPROVED_FOR_BIM com hash, mantendo a revisão da Amanda como AMANDA_REVIEW_PENDING. Quem faz: agente/IA; Amanda revisa depois. Tamanho: M.
5. **Liberação do preflight P08-T01.** Falta fechar as provas de runtime, fallback, crosswalk, build, escopo PRODUCTION e estado do arquivo antes de escrever na produção. Quem faz: agente/IA; o dono fornece dados externos quando necessário. Tamanho: G.
6. **Modelo de produção P08-T10 a P08-T14.** Falta criar o RVT de trabalho e compilar R01–R13, dos níveis e massas à documentação, com WRITE→READ→VERIFY e checkpoint após cada etapa. Quem faz: agente/IA. Tamanho: G.
7. **QA e entrega P08-T15 a P08-T19.** Faltam QA R14, candidato R15, reabertura a frio, IFC/PDF/DWG/PNG validados, pacote final T19 e só então promoção R16 GOLDEN em caminho novo. Quem faz: agente/IA, com revisão visual humana quando solicitada. Tamanho: G.
8. **Trabalho acadêmico da Amanda.** Faltam caderno, visitas/levantamento, metaprojeto, estudo preliminar, anteprojeto, pranchas, memoriais, defesa, autoria e submissão; isso corre em paralelo e não é concluído por um GOLDEN técnico. Quem faz: dono, com validação acadêmica. Tamanho: G.

## Travado e por quê

### Bloqueio real: falta informação externa

- **SITE_TOPOGRAPHY — BLOCKING:** faltam levantamento, cotas e datum; bloqueia declividade, drenagem e acessibilidade altimétrica finais.
- **SITE_BOUNDARY — BLOCKING:** falta polígono cadastral ou georreferenciado com sistema de coordenadas; 24.135 m² é área informada, não limite legal.
- **SITE_OCCUPANCY — BLOCKING:** falta confirmar uso atual do lote e a premissa de realocação da unidade policial com o órgão responsável.
- **SITE_FRONTAGE_COUNT — DEGRADING:** falta documento que resolva a divergência entre três e quatro frentes.
- **SITE_TRUE_NORTH — DEGRADING:** falta azimute ou desenho com referência de norte verdadeiro; os resultados solares são de estudo.
- **REGULATION_APPLICABILITY:** o registro de decisões ainda marca fontes consolidadas e anexos como PENDING_VERIFICATION; é condição para afirmação FINAL, embora não seja um dos cinco IDs de blocker oficiais.

### Pendência normal de execução

- **P02-T17 está PASS_WITH_WARNINGS:** quatro dos oito casos de falha são sintéticos e quatro ficaram SKIPPED_NEEDS_REVIT; fechar a prova exige RVT descartável, chamada real e reconsulta independente.
- **Crosswalk:** create_grid e create_roof continuam sem registered_entry; a rota é recusada até haver entrada e evidência exatas. O crosswalk agora é carregado e nomeia essa lacuna.
- **Evidência de produção:** as 11 capabilities estão em escopo PROVIDER e 0 em PRODUCTION; HEALTHY prova o provider, não o uso no RVT da Amanda.
- **P09 é opcional:** Blender e APS estão suspensos por decisão registrada. Só voltam com pedido real de render ou bloqueio local comprovado; não impedem o caminho local.

## O que depende de você (dono)

1. Obter e entregar levantamento topográfico com cotas e datum; não preencher os placeholders com estimativas.
2. Entregar certidão ou polígono cadastral/georreferenciado e informar o sistema de coordenadas.
3. Confirmar com o órgão responsável o uso atual do lote e a possibilidade de realocação.
4. Confirmar três ou quatro frentes e o norte verdadeiro usando documento do terreno.
5. Liberar uma janela para eventual reinício autorizado do computador/Revit quando o agente pedir a prova de retomada.
6. Ler a comparação finalista quando ela existir e informar correções; uma mudança cria nova decisão e nova validação.
7. Produzir e validar os itens acadêmicos pendentes, fazer a declaração de autoria, defesa e submissão institucional.
8. Avisar se renderização for realmente exigida; sem essa exigência, não há ação no Blender/APS.

## Riscos

- O arquivo aberto é LAB_ROUTE_PROBE, não o template indicado; uma escrita sem conferir o documento pode atingir o arquivo errado.
- Sem topografia, limite, ocupação, frentes e norte, a implantação final, área legal e acessibilidade altimétrica não podem ser afirmadas.
- Sem evidence_scope PRODUCTION e sem entradas de grid/roof, o preflight deve continuar recusando operações não comprovadas.
- Ainda não há selected_design, RVT de produção, RC ou GOLDEN; qualquer prazo depende da cadeia Revit real.
- Mesmo com GOLDEN técnico, a lista acadêmica humana continua impedindo declarar TFG_COMPLETE.

## Coisas que custam dinheiro

- Não encontrei pagamento, plano premium ou assinatura necessária para concluir o caminho local.
- APS/Forge seria uma rota opcional de nuvem; está em NO-GO/DEFERRED_OPTIONAL, sem credencial, upload ou uso, e não é necessário.
- Revit Education está instalado, mas os arquivos não comprovam custo ou situação de licença; não há compra nova registrada.
- Blender/uv aparecem como opcionais, com licença registrada MIT OR Apache-2.0; não são necessários para a entrega local.

## Candidatos a limpeza

- CANDIDATO A REVISAR: `.tmp/` — diretório existente e vazio.
- CANDIDATO A REVISAR: `design-engine/runs/AMANDA-RUN-001-invalid-2026-09-15/` — saída de testes inválidos.
- CANDIDATO A REVISAR: `design-engine/runs/AMANDA-RUN-001-invalid-2026-09-15-rooms/` — saída de testes inválidos.
- CANDIDATO A CONSOLIDAR, SEM APAGAR AGORA: `docs/notes/2026-09-16-o-que-falta-simples-v8.md` até `v12.md`.
- CANDIDATO A CONSOLIDAR, SEM APAGAR AGORA: `docs/notes/2026-09-16-analise-planos-luna-euler-handoff.md`, `...halley-handoff.md` e `...v12-handoff.md`.
- CANDIDATO A REVISAR: `logs/raw/`, `logs/raw/config.toml.before-horizun-registration` e `logs/raw/horizun-install.log`; podem ser evidência de instalação.
- NÃO ENCONTRADOS nos caminhos verificados: `.pytest_cache`, `.mypy_cache`, `.ruff_cache` e diretórios `basetemp-*`.
- NÃO APAGAR: qualquer arquivo ou pasta com `GOLDEN`, `MASTER` ou que seja release/checkpoint protegido.
- NÃO APAGAR: `docs/source/`, `TFG_Amanda_2026/`, `vendor/`, `.venv/`, `.venv-environmental/`, `.venv-topologic/`, `.dotnet/`, `tool-lab/`, `state/` e `project/provenance/`.

## Como conferi

- Arquivos-base lidos em fatias: `AGENTS.md`; `docs/AGENTS.md` foi procurado e não existe; `PROJECT_STATE.yaml`; `state/task-graph.yaml`; `state/status.md`; `state/task-history.yaml`; `state/blockers.yaml`; `state/bim-environment.lock.yaml`; `state/tool-health.yaml`; `state/environment-report.json`.
- Planos lidos por títulos, tarefas e gates: `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md` e todos os arquivos `docs/superpowers/plans/00-master-implementation-plan.md` até `09-optional-render-cloud.md`.
- Análises comparadas: `docs/notes/2026-09-16-o-que-falta-simples-v10.md`, `v11.md`, `v12.md` e `docs/notes/2026-09-16-crosswalk-producao-build-medido-handoff.md`.
- Estado complementar: `state/revit-metadata.json`, `state/capabilities.yaml`, `state/providers/semantic-crosswalk.yaml`, `state/providers/horizun-toolmap.yaml`, `project/requirements/academic-deliverables.yaml`, `project/requirements/decision-register.yaml`, `project/site/missing-data.yaml`, `project/provenance/source-versions.yaml` e `docs/reports/p08-preflight.md`.
- Comandos de leitura usados: `Get-Content -LiteralPath <arquivo> -TotalCount`; `Get-Content -LiteralPath <arquivo> | Select-Object -Skip <linha> -First <quantidade>`; `rg -n "PASS_WITH_WARNINGS|PENDING|SUSPENDED" state/task-graph.yaml`.
- Comandos de conferência usados: `Get-Process -Name "Revit" -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,MainWindowTitle,Path,StartTime`; `Get-ChildItem -LiteralPath <pasta> -Recurse -File`; e buscas `rg -n -C 2` para build, saúde, crosswalk, escopo, entregáveis e sobras.
- A contagem registrada foi conferida no grafo: 136 PASS, 2 PASS_WITH_WARNINGS, 13 PENDING, 8 SUSPENDED e total 159. O registro de testes principal informa 822 passados; eu não executei pytest.
- Não executei Git, Revit/MCP, instalações, testes ou alterações de código. A única escrita desta análise é este arquivo.
