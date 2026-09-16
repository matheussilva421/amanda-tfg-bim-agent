# O que falta para o projeto ficar pronto — v11

Data: 2026-09-16. Esta nota foi feita em leitura somente-leitura dos arquivos do projeto. Não houve chamada ao Revit ou ao MCP.

## 1. Situação em uma linha

O grafo atual tem **159 tarefas: 136 PASS, 2 PASS_WITH_WARNINGS, 13 PENDING, 8 SUSPENDED e 0 FAIL**; a próxima tarefa é **P06-T14**, o ensaio de entrega em um arquivo descartável de laboratório.

O projeto ainda não está pronto para uma entrega oficial.

## 2. O que falta hoje e de que depende

- **P06-T14 — ensaio de entrega:** testar em arquivo descartável salvar, fechar, reabrir, exportar IFC/PDF/DWG/PNG, conferir os arquivos e seus hashes, e testar a recusa de sobrescrever um GOLDEN. **Dependência:** P06-T15 está PASS; falta executar o ensaio físico/documental previsto no plano.

- **P07-T17 — retomada em sessão nova:** abrir uma sessão nova e comprovar que ela encontra o estado, o handoff e a próxima tarefa sem reconstruir o histórico pelo chat. **Dependência:** P07-T15 está PASS, mas a prova exige uma sessão nova real.

- **P07-T19 — procedimento depois de reinício:** comprovar a sequência de retomada depois de um reinício autorizado, incluindo estado, saúde do provider e reconsulta do arquivo. **Dependência:** P07-T18 está PASS; a parte restante exige um reinício real/autorizado.

- **P08-T08 e P08-T09 — estudo e escolha:** criar as massas conceituais das finalistas em `CONCEPT_ONLY`, salvar/fechar/reabrir, comparar e registrar uma escolha delegada ao agente com revisão da Amanda pendente. O run atual registra as finalistas F01 e F02 e `selected_design: null`. **Dependência:** P08-T08 depende de P08-T07, que está PASS; P08-T09 só vem depois da massa e da comparação.

- **P08-T10 a P08-T14 — RVT e modelagem:** criar o RVT de trabalho e compilar R01–R13, desde projeto, site e níveis até modelo, ambientes e documentação. **Dependência:** exige escolha registrada, preflight de produção liberado, capabilities com nomes/build/evidência compatíveis, writer lease e checkpoints.

- **P08-T15 a P08-T19 e P08-T18 — QA e entrega:** fazer QA R14, criar o candidato R15, reabrir a frio, validar exportações, preparar o pacote e só então promover R16/GOLDEN. **Dependência:** a cadeia começa depois de R13; P08-T19 depende de P08-T17 e P08-T18 depende de P08-T19.

- **P09 — render e nuvem:** P09-T03, P09-T04, P09-T05, P09-T07, P09-T08 e P09-T09 continuam suspensas. **Dependência:** só devem voltar com pedido real de render ou com uma capability local comprovadamente bloqueada, além das autorizações próprias; não são necessárias para o caminho local.

## 3. O que mudou desde a v10

**Mudança ou esclarecimento no estado atual:** `PROJECT_STATE.yaml` agora está na revisão `154`; o dashboard atual informa `PHASE_06`, último PASS `P08-T07` e duas tarefas prontas: `P06-T14` e `P08-T08`. O grafo atual identifica os dois avisos como `P02-T17` e `P08-T01`; a v10 destacava explicitamente o aviso da Fase 02, sem nomear os dois.

**O que continua igual:** não encontrei nenhuma nova tarefa concluída depois da base da v10. A contagem, a próxima tarefa `P06-T14`, as 13 tarefas `PENDING`, as 8 `SUSPENDED`, os bloqueadores do terreno, `selected_design: null`, `revit_stage: null`, `current_checkpoint: null` e o veredito `STUDY FROZEN / PRODUCTION NO-GO` continuam iguais.

**O que não consegui verificar:** não executei Revit/MCP por regra desta tarefa. Portanto não confirmei escrita real, reabertura a frio, exportação, hashes de um novo release, capabilities em escopo de produção ou qualquer avanço físico de P06-T14/P08-T08. Também não confirmei os dados novos do terreno por fonte externa ou visita.

O relatório `docs/reports/p08-preflight.md` é mais antigo que o estado atual: ele ainda mostra 110 PASS, 1 aviso, 42 PENDING e 6 SUSPENDED. Por isso, para a situação atual, usei o grafo e o estado atuais, não aqueles números históricos.

## 4. O que depende do dono sobre o terreno

- **Topografia:** fornecer levantamento com cotas numéricas e o datum usado. Hoje só existem os placeholders `[X]`, `[Y]`, `[Z]` e `[W]`; isso bloqueia afirmações finais de declive, drenagem e acessibilidade altimétrica.
- **Limite do lote:** fornecer polígono cadastral ou levantamento georreferenciado com sistema de coordenadas. A área de **24.135 m²** sozinha não define o formato nem o limite legal.
- **Ocupação atual:** confirmar o uso atual do lote e se a premissa de realocar a unidade policial está autorizada ou correta.
- **Número de frentes:** confirmar em documento do terreno se são três ou quatro; o texto disponível contém as duas afirmações.
- **Norte verdadeiro:** fornecer azimute ou desenho/levantamento com referência confiável de norte verdadeiro. Os resultados solares atuais continuam apenas indicativos.

Topografia, limite e ocupação estão registrados como `BLOCKING`. Frentes e norte estão como `DEGRADING`: permitem um estudo planar limitado, mas não permitem afirmar a implantação final.

## 5. Portões técnicos ainda abertos

- **`create_grid` e `create_roof`:** o crosswalk registra as rotas, mas deixa `registered_entry: null` para os dois nomes. Falta registrar a capability correspondente e sua evidência antes de usar essas operações na produção.

- **Build do Revit com dois identificadores:** `state/capabilities.yaml` usa `20260716_1515(x64)`, enquanto `state/revit-metadata.json` e o lock usam `fileVersion/selected_build = 27.2.0.39`; `20260716_1515(x64)` aparece como `productVersion` da mesma instalação. A instalação parece ser a mesma, mas a identificação usada pelo catálogo ainda precisa ser reconciliada explicitamente.

- **Zero evidência de produção:** as 11 entradas do catálogo estão com `evidence_scope: PROVIDER`; há **0** entradas `PRODUCTION`. `PASS` no catálogo prova o provider/laboratório registrado, não o uso seguro no RVT da Amanda.

- **Crosswalk fora do caminho de produção:** a busca estática atual encontrou `load_with_crosswalk` apenas definido em `src/amanda_agent/models/capability.py`. O dashboard usa `CapabilityRegistry.load`, e não apareceu chamada de `load_with_crosswalk` em `src/amanda_agent`; continua sem prova de que o crosswalk seja aplicado antes do caminho de produção.

- **Preflight de runtime:** o relatório registra que nenhum teste marcado `revit` foi coletado e que não há fallback completo para todas as capabilities necessárias. Saúde do provider, por si só, não fecha esse portão.

## 6. Próximos 3 passos práticos

1. Executar P06-T14 em arquivo descartável de laboratório e registrar salvar, fechar, reabrir, exportar, validar e conferir hashes.
2. Em uma sessão nova, executar as provas de retomada pendentes quando autorizadas e fechar os portões de crosswalk, build e escopo `PRODUCTION`; depois fazer P08-T08 e P08-T09 em `CONCEPT_ONLY`.
3. O dono fornecer os cinco dados do terreno; após a validação, seguir para P08-T10 e a cadeia de modelagem, QA e entrega.

## 7. Registro da leitura e comandos de contagem

Foram lidos ou conferidos:

- `AGENTS.md`;
- `docs/notes/2026-09-16-o-que-falta-simples-v10.md`;
- `docs/notes/2026-09-16-analise-planos-luna-halley-handoff.md`;
- `state/task-graph.yaml`, `PROJECT_STATE.yaml`, `state/status.md`, `state/blockers.yaml`, `state/capabilities.yaml`;
- `state/providers/semantic-crosswalk.yaml` e `docs/reports/p08-preflight.md`;
- os dez planos `docs/superpowers/plans/00` a `09`;
- `state/revit-metadata.json` e `state/bim-environment.lock.yaml`, para conferir os dois identificadores de build;
- busca estática em `src/amanda_agent` para conferir se o crosswalk é carregado no caminho de produção.

Comando principal usado para contar os status:

```powershell
rg -o 'status: [A-Z_]+' state/task-graph.yaml | ForEach-Object { ($_ -split ': ')[1] } | Group-Object | Sort-Object Name
```

Resultado observado: `PASS 136`, `PASS_WITH_WARNINGS 2`, `PENDING 13`, `SUSPENDED 8`. A soma é 159 e não apareceu `FAIL`.

Comando usado para confirmar a soma por tarefa:

```powershell
$lines = Get-Content -LiteralPath 'state/task-graph.yaml'; $current = $null; $items = @(); foreach ($line in $lines) { if ($line -match '^  (P\d{2}-T\d{2}):$') { $current = $Matches[1] } elseif ($current -and $line -match '^    status: (\S+)$') { $items += [pscustomobject]@{Id=$current;Status=$Matches[1]}; $current = $null } }; $items | Group-Object Status | Sort-Object Name | Select-Object Name,Count | Format-Table -AutoSize; "TOTAL=$($items.Count)"
```

Resultado observado: `TOTAL=159`, com os mesmos quatro grupos de status. Não foram executados testes, commits, pushes, chamadas ao Revit/MCP ou alterações em `state/`, planos ou código; o único arquivo criado nesta tarefa é esta nota.
