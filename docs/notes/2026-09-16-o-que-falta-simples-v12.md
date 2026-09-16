# O que falta para o projeto ficar pronto — v12

Data da leitura: 2026-09-16.

Esta nota é uma fotografia dos arquivos locais. Nesta rodada não executei Revit, MCP, testes de runtime nem instalações. Não alterei código, `state/` ou os planos.

## (a) Situação em uma linha

Existe um estudo digital com o programa escolhido e duas finalistas, mas ainda não existe no estado do projeto um modelo Revit de produção, uma entrega `GOLDEN` selada ou uma prova de uso em produção. O grafo tem **159 tarefas: 136 `PASS`, 2 `PASS_WITH_WARNINGS`, 13 `PENDING` e 8 `SUSPENDED`**. Portanto, o projeto ainda não está pronto para uma entrega oficial.

O programa adotado é de **20 pessoas**, conforme o PDF de necessidades. A hipótese de 42 pessoas da planilha foi rejeitada e não deve ser misturada ao programa escolhido.

## (b) O que falta hoje, item por item, e de que depende

1. **`P02-T17` — aviso do laboratório.** A matriz tem 8 casos: 4 passaram de forma sintética, 4 ficaram `SKIPPED_NEEDS_REVIT` e 0 falharam. Faltam os quatro casos que precisam de arquivo descartável do Revit. **Depende de:** sessão de laboratório e registro; a dependência formal é `P02-T16`, `PASS`.

2. **`P06-T14` — ensaio de entrega (`PENDING`).** No modelo sintético, falta salvar, fechar, reiniciar e reabrir Revit, consultar de novo, rodar QA, exportar IFC/PDF/DWG/PNG, conferir hashes e rejeitar sobrescrita de `GOLDEN`. **Depende de:** `P06-T15` `PASS` e execução real.

3. **`P07-T17` — retomada em sessão nova (`SUSPENDED`).** O roteiro e os testes estão preparados, mas uma nova sessão ainda precisa ler estado/handoff e encontrar a próxima tarefa sem usar o chat. **Depende de:** `P07-T15` e nova sessão de Codex.

4. **`P07-T19` — retomada depois de reinício (`SUSPENDED`).** Falta comprovar, após reinício autorizado, `doctor`, `status`, saúde do provider, reabertura do checkpoint e consulta independente. **Depende de:** `P07-T18` `PASS` e janela autorizada; não houve reinício real.

5. **`P08-T01` — preflight de produção (`PASS_WITH_WARNINGS`, sem liberação).** Confirmou fontes, build e suíte sem Revit, mas registrou zero evidência `PRODUCTION`, nenhum teste `revit` coletado e fallback incompleto. O veredito é `PENDENTE — STUDY FROZEN / PRODUCTION NO-GO`. **Depende de:** portões da seção (e), `P06-T15` e `P07-T19`.

6. **`P08-T08` — massas conceituais (`PENDING`).** Criar candidatas em `CONCEPT_ONLY`, somente R01–R04, com lease, salvamento, fechamento e reabertura. O run registra duas: `AMANDA-RUN-001-F01` e `F02`; o título fala em top 3, mas não há terceira registrada. **Depende de:** `P08-T07` `PASS` e execução controlada no Revit.

7. **`P08-T09` — escolha da alternativa (`PENDING`).** Comparar as opções e registrar exatamente uma `APPROVED_FOR_BIM` com hash. Hoje `selected_design: null`. **Depende de:** `P08-T08`. A escolha de rotina foi delegada ao agente; a revisão de Amanda é `AMANDA_REVIEW_PENDING`.

8. **`P08-T10` a `P08-T14` — RVT e modelagem (`PENDING`).** Faltam o RVT de trabalho; R01–R04; R05–R08, com paredes, layout e ambientes; R09–R12, com acessibilidade dentro das fontes verificadas, mobiliário, áreas externas e materiais; e R13, com pranchas, cortes, fachadas, tabelas e documentação. **Dependência:** cadeia `T10 → T11 → T12 → T13 → T14`, após seleção, preflight, lease e checkpoints válidos.

9. **`P08-T15` a `P08-T19` — QA e entrega (`PENDING`).** Faltam QA R14, candidato R15, reabertura a frio, exportações/validações, pacote e promoção para `GOLDEN`. A ordem é `T15 → T16 → T17 → T19 → T18`; `P08-T18` depende de `P08-T19`. **Depende de:** R13, QA, persistência, exportações, revisão visual, hashes e pacote novo/imutável.

10. **Renderização Blender e APS.** `P09-T03`, `T04`, `T05`, `T07`, `T08` e `T09` estão `SUSPENDED`. Render foi `DEFERRED_OPTIONAL` e APS `NO-GO`, pois não há capability local bloqueada e rotas pagas estão fora do escopo. **Depende de:** pedido real de render ou bloqueio local comprovado; não impede a entrega local.

11. **Concluir o TFG como trabalho acadêmico.** O arquivo de entregáveis acadêmicos mantém pendentes, sob responsabilidade de Amanda, o caderno, visitas/levantamento, metaprojeto, estudo preliminar, anteprojeto, memoriais, defesa, autoria e submissão institucional. As pranchas aparecem como `PROVISIONAL`, com a quantidade de 4–6 A1 ainda dependente do regulamento institucional. **Depende de:** produção, validação e atos humanos de Amanda e da instituição. Mesmo um `GOLDEN` técnico não autoriza declarar `TFG_COMPLETE` automaticamente.

## (c) O que mudou desde a v11

**Não observei mudança nos fatos centrais desde a v11.** A leitura atual repete `state_revision: 154`, `last_completed_task: P08-T07`, `next_task: P06-T14`, fase `PHASE_06/PENDING`, gate `GO_WITH_LIMITATIONS` e os campos `selected_design`, `revit_stage` e `current_checkpoint` como `null`. A contagem fresca também repete 136 `PASS`, 2 `PASS_WITH_WARNINGS`, 13 `PENDING` e 8 `SUSPENDED`.

Os cinco bloqueadores do terreno continuam sem `resolved_utc`. O crosswalk ainda deixa `registered_entry: null` para `revit.create_grid` e `revit.create_roof`. O catálogo continua com 11 capabilities `PASS` em escopo `PROVIDER`, e zero em `PRODUCTION`.

A v12 esclarece que os quatro casos Revit de `P02-T17` são pendência do aviso, não falha, e que a cadeia é `P08-T15 → T16 → T17 → T19 → T18`. Não encontrei nova tarefa concluída depois de `P08-T07`.

Como o checkout compartilhado está sujo e a v11 está entre os arquivos não rastreados do workspace, esta comparação é contra os valores documentados e os arquivos atuais; não há um commit limpo da v11 que permita um diff histórico isolado.

## (d) O que depende do dono

Na prática, Amanda ou o órgão responsável precisa fornecer/confirmar estes dados. `requires_user_action` aparece como `false` nos cinco registros; isso não significa que os dados existam.

- **Topografia:** levantamento com cotas numéricas e datum. Hoje só há `[X]`, `[Y]`, `[Z]` e `[W]`; declive, drenagem e acessibilidade altimétrica final ficam sem prova.
- **Limite:** certidão/polígono cadastral ou levantamento georreferenciado com sistema de coordenadas. Os **24.135 m²** são afirmação de fonte; a geometria retangular é só referência de estudo.
- **Ocupação:** uso atual e possível realocação da unidade policial, para confirmar disponibilidade.
- **Frentes:** documento que resolva três ou quatro frentes; a contagem deve vir de levantamento/cadastro.
- **Norte verdadeiro:** azimute ou desenho confiável; os resultados solares atuais são somente de estudo.
- **Revisão e autoria:** revisar a solução delegada e produzir/validar entregáveis, visitas, autoria, defesa e submissão. O software não atesta esses atos.

O programa de 20 pessoas já foi escolhido e registrado. Amanda não precisa reabrir essa escolha para esta rodada; qualquer mudança futura exigirá nova decisão e nova validação.

## (e) Portões técnicos ainda abertos

1. **Crosswalk de `create_grid` e `create_roof`.** As duas rotas apontam para `horizun_create_elements`, mas ficam com `registered_entry: null`. Falta registrar entrada e evidência exatas, ou manter a operação bloqueada; não se deve adivinhar.

2. **Dois identificadores do build do Revit.** Metadata e lock conferem `fileVersion`/`selected_build = 27.2.0.39` e `productVersion = 20260716_1515(x64)`. Capabilities usam o segundo; crosswalk, o primeiro. Falta reconciliar os nomes em uma identidade única antes da produção.

3. **Zero entradas `PRODUCTION`.** Há 11 capabilities `PASS`, 0 `FAIL` e 0 `UNTESTED`, mas todas têm `evidence_scope: PROVIDER`; `PRODUCTION` = **0**. Isso prova laboratório/provider, não uso seguro no RVT. `HEALTHY` não muda o escopo.

4. **Preflight de runtime do Revit.** O relatório registra nenhum teste `revit` coletado; a suíte sem Revit teve 726 passados e 0 falhas. Ainda falta prova física em arquivo descartável, com save/close/reopen e consulta independente.

5. **Fallback completo e uso do crosswalk.** O preflight registra fallback incompleto. A busca encontra `load_with_crosswalk` definido em `src/amanda_agent/models/capability.py`, mas `status_dashboard.py` usa `CapabilityRegistry.load`; não encontrou chamada de `load_with_crosswalk`. Não foi validado em runtime.

6. **Checkout compartilhado.** Há trabalho não commitado. Antes da produção é preciso fixar a versão usada e preservar os demais trabalhos.

## (f) Próximos 3 passos práticos

1. Executar `P06-T14` somente no arquivo descartável de laboratório e completar as provas de retomada `P07-T17` e `P07-T19` nas sessões próprias, registrando resultados reais.
2. Fechar os portões técnicos da seção (e), atualizar o preflight para deixar claro o escopo aceito e então fazer `P08-T08`/`P08-T09` em `CONCEPT_ONLY`, escolhendo e registrando uma única alternativa.
3. Amanda fornecer/confirmar os dados do terreno; com os dados validados e o preflight liberado, seguir `P08-T10` até `P08-T19` e, em paralelo, completar os entregáveis acadêmicos humanos que forem necessários.

## (g) Registro do que foi lido e comandos usados

Foram lidos os arquivos pedidos:

- `AGENTS.md` e `START_HERE_FOR_CODEX.md`;
- `docs/superpowers/plans/00-master-implementation-plan.md` até `09-optional-render-cloud.md`, por fatias de títulos, tarefas críticas e portões finais;
- `2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md`;
- `state/task-graph.yaml`, `PROJECT_STATE.yaml`, `state/status.md`, `state/blockers.yaml`, `state/capabilities.yaml` e `state/providers/semantic-crosswalk.yaml`;
- `docs/notes/2026-09-16-o-que-falta-simples-v11.md`.

Também consultei o preflight, metadata/lock do Revit, dados do site, entregáveis acadêmicos, decisões, run atual e `src/amanda_agent` para confirmar fatos citados.

Comandos de leitura e conferência usados, sempre com padrões explícitos:

```powershell
git status --short --branch
rg --files -g 'AGENTS.md' -g 'START_HERE_FOR_CODEX.md' -g 'docs/superpowers/plans/0[0-9]-*.md' -g 'state/*.yaml' -g 'state/*.md'
rg -n --glob '0[0-9]-*.md' '^#|^##|^###' docs/superpowers/plans
rg -n -C 3 --glob '08-amanda-production-run.md' 'P08-T01|P08-T08|P08-T09|P08-T10|P08-T15|P08-T16|P08-T17|P08-T18|P08-T19|Production Completion Gate' docs/superpowers/plans
rg -n -C 3 'create_grid|create_roof|registered_entry|revit_build|evidence_scope' state/providers/semantic-crosswalk.yaml state/capabilities.yaml
rg -n --glob '*.py' 'load_with_crosswalk|CapabilityRegistry\.load|semantic-crosswalk|crosswalk' src/amanda_agent
```

Comando usado para reconfirmar a contagem do grafo:

```powershell
$lines = Get-Content -LiteralPath 'state/task-graph.yaml'; $current = $null; $items = @(); foreach ($line in $lines) { if ($line -match '^  (P\d{2}-T\d{2}):$') { $current = $Matches[1] } elseif ($current -and $line -match '^    status: (\S+)$') { $items += [pscustomobject]@{Id=$current;Status=$Matches[1]}; $current = $null } }; $items | Group-Object Status | Sort-Object Name | Select-Object Name,Count | Format-Table -AutoSize; "TOTAL=$($items.Count)"
```

Resultado observado: `PASS 136`, `PASS_WITH_WARNINGS 2`, `PENDING 13`, `SUSPENDED 8`, `TOTAL=159`. Não apareceu outro status de tarefa.

Comando usado para contar o escopo das capabilities:

```powershell
$scopes = rg -o --glob 'capabilities.yaml' 'evidence_scope: [A-Z_]+' state | ForEach-Object { ($_ -split ': ')[1] }; $scopes | Group-Object | Sort-Object Name | Select-Object Name,Count; "TOTAL_CAPABILITIES=$($scopes.Count)"; "PRODUCTION_COUNT=$(($scopes | Where-Object { $_ -eq 'PRODUCTION' }).Count)"
```

Resultado observado: `PROVIDER 11`, `TOTAL_CAPABILITIES=11`, `PRODUCTION_COUNT=0`. Nenhum Revit/MCP foi chamado e nenhum teste foi executado por esta análise.
