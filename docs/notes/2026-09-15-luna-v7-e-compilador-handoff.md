# Handoff — análise LUNA v7 e compilador de solução

Data: 2026-09-15. Sessão: análise simples do que falta (pedido do dono) + avanço do
compilador que faltava para P08-T08.

## Resumo do que foi feito

1. Dois subagentes LUNA XHIGH (únicos autorizados pelo dono) rodaram em paralelo:
   - Linnaeus (análise, somente leitura): escreveu
     `docs/notes/2026-09-15-o-que-falta-simples-v7.md`.
   - Turing (implementação, TDD): escreveu `src/amanda_agent/bim/solution_compiler.py`
     e `tests/unit/test_bim_solution_compiler.py`.
2. Verificação independente do compilador contra o `solution.json` REAL do F01:
   4 planos R01→R04, 0 operações no R02 (PLANAR_PLACEHOLDER + 2 blockers), 1 nível +
   1 grid + 1 PROJECT_ORIGIN provisório no R03, 6 blocos a 3,2 m no R04, identidade
   (solution_id + approval_hash) presente em todos.
3. Limpeza local aplicada: `scripts/cleanup-local.ps1 -Apply` removeu 3 `__pycache__`
   (0 targets, 0 MB). Estado final: scratch=0, pycache=0.

## Arquivos criados

- `docs/notes/2026-09-15-o-que-falta-simples-v7.md` (LUNA Linnaeus)
- `src/amanda_agent/bim/solution_compiler.py` (LUNA Turing, 13.855 bytes)
- `tests/unit/test_bim_solution_compiler.py` (LUNA Turing, 4.292 bytes)
- este handoff

## Decisões técnicas relevantes

- Altura dos blocos: não existe em nenhuma fonte ⇒ `PROVISIONAL_ASSUMPTION` de 3,2 m,
  declarada no plano (nunca silenciosa).
- R02 em estudo usa `PLANAR_PLACEHOLDER`: 0 operações e blockers preservados.
  Não inventar topografia.
- Nível / origem / grid A são provisórios e rotulados como tais.
- `site_version` real é a string `"site-v1"`; o compilador deriva `1` só para o
  `SiteModel` e preserva a string original.
- CONCEPT_ONLY recusa R05 em diante com erro explícito (a janela é até R04).

## Achado que importa para P08-T08

Os 6 blocos do F01 somam `626,0000 m²` = `internal_net_area_m2`.
O `gross_footprint_m2` do accounting é `779,2601 m²`. A verificação de métricas do
P08-T08 deve comparar o massing contra a área CERTA (626 de áreas de bloco, não 779,26),
ou aplicar o `net_to_gross_factor` 0,8033 de forma explícita. Comparar contra 779,26
sem essa nota produziria um falso "mismatch".

## Achados da comparação F01 x F02 (verificados nesta sessão)

- Os dois são `VALIDATED`, `hard_violations: []`, mesmos 6 logical_ids de bloco e
  MESMAS áreas de bloco (53, 209, 52, 80, 81, 151 m²). As geometrias dos blocos DIFEREM;
  macrozonas e rooms diferem.
- `internal_net_area_m2` = 626,0 e `external_area_m2` = 260,0 nos dois; `storeys` = 1,0.
- `gross_footprint_m2` do accounting: **F01 = 779,26** e **F02 = 1.269,35**. A soma dos
  `gross_footprint_m2` por room fecha exatamente com o accounting em ambos.
- O orçamento aceito do programa é 783–814 m² construídos fechados: **F01 fica dentro**
  (779,26, ligeiramente abaixo) e **F02 estoura** (1.269,35, ~1,6x).
- `metrics.json` dos dois tem `weighted_total` IDÊNTICO = `0,8415491821831452`, com
  `raw_metrics` idênticos e `solar_heuristic`/`ventilation_heuristic` em `not_evaluated`.
  `penalties.json` traz `soft_penalties` idênticos.
- Causa identificada: os três `block_checks` de `penalties.json` (`gross_area_budget`,
  `required_rooms`, `accessible_rooms`) estão todos `"unavailable at this resolution"`.
  Sem o check de orçamento de área, um finalista que estoura 1,6x o orçamento não é
  penalizado — é por isso que a nota empata. Isto é uma lacuna de avaliação a registrar,
  não um empate real de mérito.

## Nota de continuidade

O `comparison.md` canônico segue ausente (nenhum arquivo encontrado com esse nome no
repositório). Está sendo produzido como DRAFT com `selection_authority=AGENT_DELEGATED`
proposto; a seleção NÃO foi registrada em `state/` e nenhum status de tarefa foi alterado.

## Testes executados

- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_bim_solution_compiler.py -q`
  → 3 executados, 3 passaram, 0 falharam.
- `.\.venv\Scripts\python.exe -m pytest tests/unit -q --ignore=tests/unit/test_topologic_spike.py`
  → 629 executados, 629 passaram, 0 falharam.
- `.\.venv\Scripts\python.exe -m pytest tests/integration -q` → 1 executado, 1 passou.
- Suíte completa de unidade: 630 executados, 629 passaram, 1 falhou
  (`test_topologic_spike.py`, falha PREEXISTENTE e sem relação com este trabalho:
  o TopologicPy consulta o PyPI e sem rede devolve None, quebrando o script).

## Problemas encontrados

- `test_topologic_spike.py` reescreve o arquivo rastreado
  `tool-lab/topologic/results/topologic-spike.json`. Restaurado byte a byte a partir
  do blob do HEAD (`3890efa4638b14d49eed182dea0634da74db064a`) via `git cat-file -p`;
  `git diff --quiet` = 0. O `git status` ainda mostra ` M` apenas por metadado de
  fim de linha/stat (não há diferença de conteúdo).
- `git restore`/`git add` continuam impossíveis no sandbox: o `.git` tem ACL
  `Deny Write` para o grupo do sandbox (`Unable to create '.git/index.lock'`).

## Bloqueios (inalterados)

- Escrita no Revit e `git` barradas pelo revisor automático do app
  ("Provider error 400 … response_format type is unavailable now"), idêntico em 3 turnos.
- `gh auth status`: token de `matheussilva421` inválido.
- Revit 2027 vivo (pid 30736), `healthy`, add-in 1.3.3, build `27.2.0.39`,
  perfil `full_write`; documento aberto `LAB_R01_TEMPLATE.rte`.
- Sem topografia/cadastro ⇒ P08-T08 permanece STUDY.

## Restrições do dono (vigentes)

- NADA pago: sem APS/Forge, sem render em nuvem, sem assinatura.
- Só subagentes LUNA XHIGH.
- Apagar da pasta local o que não é mais necessário (feito o que era comprovadamente lixo).

## Próximo passo exato

P08-T08 (massing conceitual dos finalistas no Revit) usando `compile_solution_file`
para montar R01→R04. Antes de promover qualquer PASS, provar escrita física com
WRITE→READ→VERIFY. Enquanto a escrita estiver barrada, o trabalho independente
possível é a comparação dos finalistas (`comparison.md`) que a v7 aponta como ausente.

## Turno do subagente LUNA "Nash" (análise simples do que falta)

- Pedido do dono: "crie um subagent para analisar os planos e me dizer de forma simples o que falta".
- Spawn: `multi_agent_v1__spawn_agent` com `agent_type:"luna"` (gpt-5.6-luna, xhigh fixo),
  `fork_context:false`, `agent_id=01a0a825-aaf4-7c83-9090-0c45ea387aa2`, nick `Nash`.
- Escopo do subagente: SOMENTE LEITURA (proibido criar/editar arquivo, `git add/commit`,
  `pytest`, Revit). Resultado esperado: 7 seções em PT-BR simples, sem escrever arquivos.
- Leitura independente do coordenador neste turno, para âncora da resposta final:
  - `state/status.md`: fase `PHASE_06`, phase status `PENDING`, next task `P06-T14`,
    last PASS `P08-T07`, READY: `P06-T14`, `P08-T08`; `PHASE_06` 14/15, `PHASE_08` 7/19,
    `PHASE_09` 4/10, demais 0/3..23/23 conforme o painel.
  - `PROJECT_STATE.yaml`: `next_task: P06-T14`, `state_revision: 154`.
  - `state/task-graph.yaml`: `P06-T14` = *Synthetic R14→R16 release drill*, depends_on `P06-T15`
    (já PASS) ⇒ é executável agora; `P02-T05` (fixture LAB_R00_EMPTY.rvt) consta PASS.
  - Revit vivo por leitura direta: `horizun_health` = `healthy`, 1.3.3, contrato
    `8b9600f5274d7dffb6e5bd5f`, python_runtime `ready`; `get_document_info` = documento
    `LAB_R01_TEMPLATE` (`revit\lab\probe\LAB_R01_TEMPLATE.rte`), Revit 2027 build `27.2.0.39`,
    3230 elementos, shared coordinates em 0/0/0, norte verdadeiro 0°.
  - `C:\Users\slvma\.horizun\settings.json`: `permission_profile: full_write` e
    `execute_python_ui_granted: true` ⇒ a ação humana pedida ao dono está aplicada de fato.
  - Fixture confirmada em disco: `revit\lab\baseline\LAB_R00_EMPTY.rvt` existe.
- Limpeza local executada: `scripts\cleanup-local.ps1 -Apply` removeu 2 alvos
  (`.pytest_cache`, `.ruff_cache`) + 22 diretórios `__pycache__`; `remaining scratch=0 pycache=0`.
  Total da pasta 2803,2 MB / 44.884 arquivos. O script preserva de propósito
  `.venv`, `.venv-topologic`, `.venv-environmental`, `.dotnet` e `vendor\` (são gitignorados).
- Restauração de artefato: `tool-lab/topologic/results/topologic-spike.json` está idêntico ao HEAD
  (`git diff --quiet` retorna 0); o ` M` do `git status` é só normalização LF→CRLF de metadado.
- Bloqueios inalterados neste turno: escrita no Revit e `git add/commit/restore` barrados pelo
  revisor automático do app (mesmo `Provider error 400 … response_format type is unavailable now`);
  `git` também esbarra na ACL `Deny Write` no `.git`. Ainda assim `origin` existe
  (`github.com/matheussilva421/amanda-tfg-bim-agent`) e `main...origin/main` está 0/0.

### Resultado do LUNA "Nash" (concluído, somente leitura)

- Leitura própria confirmada pelo subagente: `state/status.md`, `state/task-graph.yaml`,
  `state/task-history.yaml`, `PROJECT_STATE.yaml` ⇒ 159 tarefas (136 PASS, 2 PASS_WITH_WARNINGS,
  13 PENDING, 8 SUSPENDED), `PHASE_06`, next `P06-T14`, revision 154, nenhum FAIL.
- Lista de "o que falta" (13 PENDING), na ordem que ele derivou dos planos:
  P06-T14 (drill R14→R16 no lab) → P08-T08 (massing conceitual dos finalistas) →
  P08-T09 (seleção delegada + review da Amanda) → P08-T10 (RVT de produção) →
  P08-T11 (R01–R04) → P08-T12 (R05–R08) → P08-T13 (R09–R12) → P08-T14 (documentação R13) →
  P08-T15 (QA completo R14) → P08-T16 (RC R15 + reabertura fria) → P08-T17 (exportar/validar) →
  P08-T19 (pacote final) → P08-T18 (GOLDEN-001 imutável). Ordem de fecho T17 → T19 → T18.
- Travas que ele apontou: topografia/limite/ocupação/frentes/norte verdadeiro sem comprovação
  (impede `FINAL` legal/altimétrico); preflight de produção sem evidência de produção
  (`P08-T01` PASS_WITH_WARNINGS); `P07-T17`/`P07-T19` SUSPENDED (sessão nova + reboot
  autorizado); `P02-T17` com 4 falhas ainda a testar num RVT descartável.
- Custo: ele respondeu **NÃO** para o caminho local obrigatório — Revit já instalado,
  Horizun/RevitCortex locais (RevitCortex MIT), IFC/PDF/DWG gerados localmente; APS/Forge
  figuraram como opcionais e pagos, fora do escopo; Blender opcional sem render obrigatório.
- Estimativa: ele não cravou horas (o plano não traz prazo confiável); faltam 13 PENDING.
- Não verificado por ele (declarado): não abriu o Revit, não existe RVT de produção nem
  `GOLDEN-001`, sem reabertura fria do RVT da Amanda, sem proxy de estrutura/instalações/custo,
  sem revisão visual final das pranchas, sem comprovação dos entregáveis acadêmicos.
- Fechado com `close_agent` (`previous_status: completed`). Nenhum arquivo foi criado pelo Nash.

### Escrita no Revit: ensaio OK, aplicação ainda barrada

- `horizun_health` expõe `operational_controls.permission_profile = "full_write"` e
  `mcp_paused = false` ⇒ a escolha humana do dono está realmente ativa no add-in.
- `horizun_create_elements` com `dry_run=true` (nível `LAB_PROBE_WRITE`) foi ACEITO: 1/1 válido,
  `change_preview.fingerprint 30dd00d648f07ed31ab7a3ef6f1e0cf68f30682c378f13840a2c5907f8caf73b`,
  `confirmation_token hz-dae42a8b5732f4cb3803fa2fb3d30c84` (expira 2026-09-16 03:11:37Z).
  Ou seja: a validação de argumentos e o token funcionam.
- `horizun_open_document` em `revit\lab\probe\LAB_ROUTE_PROBE.rvt` (documento descartável, para o
  teste de escrita real) foi REJEITADO pelo revisor automático do app com o mesmo
  `Provider error 400 … response_format type is unavailable now`. O bloqueio é do revisor do app,
  não do add-in: dry-run passa, ação que muta o documento para.
- `horizun_delete_verified` (dry run, id 221018) foi REJEITADO pelo mesmo revisor:
  `This action was rejected due to unacceptable risk. Reason: Automatic approval review failed:
  Provider error 400 ... response_format type is unavailable now`. O nivel de laboratorio
  `LAB_WRITE_PROBE` (221018) permanece no `LAB_R01_TEMPLATE.rte` salvo (sha256 `320cc1ca...`).
  Nao e GOLDEN nem producao: e o template de laboratorio. Retentar quando o revisor voltar.

### Fechamento do ciclo de sessao (2026-09-16)

- Reabertura a frio do `LAB_R01_TEMPLATE.rte` NAO feita: o Revit 2027 segue no mesmo processo
  (pid 30736) e `horizun_document_session` / `horizun_open_document` continuam barrados pelo
  revisor. A persistencia esta provada por hash em disco (`bytes_changed_on_disk: true`,
  `sha256_before f1d90665...` para `sha256_after 320cc1ca...`), nao por close/reopen. A reabertura
  a frio (P08-T16/P08-T18) continua aberta.
- Dois subagentes LUNA XHIGH somente-leitura mapearam o que falta: Nash (13 PENDING na ordem) e
  James (os mesmos 13, cada um com o que falta e de quem depende). Ambos confirmaram: nada pago
  e necessario. Nenhum dos dois escreveu arquivo nem abriu o Revit.
- `scripts\cleanup-local.ps1 -Apply` rodado: scratch e `__pycache__` de projeto zerados. `.dotnet`
  (769,9 MB, maior diretorio) permanece por design do script; remover exige autorizacao do dono.
- `git add` segue impossivel: `fatal: Unable to create '.git/index.lock': Permission denied` (ACL
  `Deny Write` em `.git`, nao o revisor). 12 rastreados modificados + ~30 nao rastreados, 0 deletado
  rastreado. `main...origin/main` = 0/0.

#### Instrucoes exatas de retomada (2026-09-16)

### Bloco seguinte (2026-09-16, continuacao)

- Subagente LUNA XHIGH "Hilbert" (somente leitura) refez a analise de planos a pedido do dono
  ("crie um subagent para analisar os planos e me dizer de forma simples o que falta"). Leitura:
  START_HERE, revisao-planos, COMBINED-plan, os 10 planos de `docs/superpowers/plans/`, estado vivo,
  `solutions/finalists/comparison.md` e os decision registers. Resultado reportado ao dono na
  resposta final. Agente fechado.
- Reconfirmado ao vivo: `horizun_health` verde (1.3.3, contract_hash 8b9600f5274d7dffb6e5bd5f),
  documento ativo `LAB_R01_TEMPLATE` em `revit/lab/probe/LAB_R01_TEMPLATE.rte` (3231 elementos),
  Revit 2027 / 27.2.0.39, pid 30736. Perfil do add-in: `full_write` confirmado em
  `%USERPROFILE%\.horizun\settings.json`.
- `horizun_document_session` (inspect) e `horizun_export` (pdf, dry run) rejeitados de novo pelo
  revisor automatico com o MESMO erro interno do provedor ("This response_format type is
  unavailable now"). Nao e o add-in: e a camada de aprovacao. `horizun_list_elements` tambem
  recusou por falta de `category` (validacao normal do add-in, nao bloqueio).
- Limpeza: `Remove-Item` (mesmo em `.tmp` de 1 byte e em `tool-lab/custom-api/obj`) e barrado pelo
  revisor. `scripts/cleanup-local.ps1 -Apply` roda mas reporta `0 targets, 0 MB` (nada a limpar).
  Levantamento do que sobra e por que NAO pode sair agora:
  * `.dotnet` 769,9 MB — SDK 10.0.401 instalado pelo projeto; nada no repo o referencia em runtime,
    mas e o unico SDK que compila `vendor/RevitCortex` e `vendor/horizun-revit-mcp`; apagar exige
    autorizacao explicita do dono (o revisor tambem barra a exclusao).
  * `.venv` 441,9 MB, `.venv-topologic` 376,1 MB, `.venv-environmental` 451,0 MB — os dois ultimos
    sao exigidos por testes (`tests/unit/test_topologic_spike.py` afirma
    `ISOLATED_PYTHON.is_file()`) e pelo handoff de P04-T21; recriaveis porem nao agora.
  * `vendor/` 354,4 MB — contem o `RevitCortex.Server.exe` que o `config.toml` do Codex usa como
    servidor MCP ativo; `.dll`/`bin`/`obj` somam ~200 MB mas o publish em uso nao pode sair.
  * `tool-lab/environmental/wheels/` 155,6 MB — 34 wheels ja instalados e referenciados no handoff.
  * `docs/source/` 52,8 MB + PDF identico na raiz (52,0 MB) — `source-manifest.yaml` marca
    `docs/source` como `immutable_path`; a copia da raiz tem o MESMO sha256
    (`16abe602ac50643482ce3c782780b4135fa8468b5ca814061fe426c8ca292a7e`) e e a unica duplicata
    segura de remover, mas tambem depende do revisor.
  * `revit/lab/**` 103,3 MB — os arquivos `.0001/.0002.rvt` estao citados com hash em
    `docs/reports/provider-update-isolation-drill.md`; remover invalidaria aquele relatorio.
- A sugestao de limpeza do dono foi respondida com esse levantamento; nada foi apagado neste bloco
  porque o revisor automatico rejeitou as exclusoes e o script do projeto nao encontrou alvos.

1. Tentar `horizun_delete_verified` (dry run) para o id 221018; se o revisor barrar, registrar e seguir.
2. P08-T08: compilar F01 com `compile_solution(..., registry=..., mode=CONCEPT_ONLY, max_stage=R04)`;
   registry de laboratorio: `build_lab_fixture_registry(root=...)` (`src/amanda_agent/bim/lab_fixture.py:79`);
   registry real: `CapabilityRegistry.load(state/capabilities.yaml)`.
3. Criar o RVT candidato exige `horizun_document_session` (`open` / `save_as`) - hoje recusado pelo
   revisor. A via que passa e escrever no `LAB_R01_TEMPLATE.rte` (`create_elements` + `save_document`).
4. P06-T14: drill sintetico verde (6 testes); falta a parte fisica (fechar/abrir a frio, IFC/PDF/DWG).

## Bloco seguinte (2026-09-16) - subagente Einstein: "o que falta", versao simples

- Pedido do dono: "crie um subagent para analisar os planos e me dizer de forma simples o que falta".
- Subagente **LUNA XHIGH "Einstein"** (`01a0a862-802c-7d60-aac8-92e752ce0b68`, `agent_type:"luna"`,
  `fork_context:false`, campo `message`), somente leitura, analisou planos, `state/status.md`,
  `PROJECT_STATE.yaml` e `state/task-graph.yaml`. Concluido e fechado com `close_agent({target})`.
- Numeros confirmados por leitura independente nesta sessao (o agente afirmou o mesmo):
  `PASS 136`, `PASS_WITH_WARNINGS 2`, `PENDING 13`, `SUSPENDED 8`, `FAIL 0` -> 159 tarefas,
  **85,5% concluido**. `next_task P06-T14`.
- Nota de handoff gerada: `docs/notes/2026-09-16-o-que-falta-simples-v8.md` (resumo para leigo).
- Anti-estouro de contexto usado: `Select-String`/`Select-Object -First` em vez de `rg -A 20+`;
  nenhuma varredura de arquivo grande inteiro.
- Nada foi alterado no Revit neste bloco. `.horizun/settings.json` relido: `permission_profile:
  full_write`, `execute_python_ui_granted: true`.

### Evidencias deste bloco (fechamento)

- `pwsh -File scripts/cleanup-local.ps1 -Apply` -> `removed 1 targets and 21 __pycache__
  directories`, `remaining scratch=0 pycache=0` (`.tmp-pytest-luna.log` de 0,00 MB e o cache do
  pytest). Nada de valor foi apagado.
- `.\.venv\Scripts\python.exe -X utf8 -m pytest tests/unit -q
  --ignore=tests/unit/test_topologic_spike.py -p no:cacheprovider` -> **629 passed, 0 failed**,
  26,37 s.
- Revit relido ao vivo: `horizun_health` `healthy` (1.3.3, contract_hash `8b9600f5274d7dffb6e5bd5f`,
  python `ready`); `get_document_info` -> `LAB_R01_TEMPLATE` em
  `revit/lab/probe/LAB_R01_TEMPLATE.rte`, 3231 elementos, Revit 2027 build `27.2.0.39`.
- **Git: bloqueado.** `git add` falha com `unable to create .git/index.lock: Permission denied`
  (ACL `Deny Write` em `.git`, incognoscivel pelo sandbox). A tentativa de `git add` com
  `require_escalated` foi **rejeitada pelo revisor automatico** com o mesmo erro de provedor
  (`This response_format type is unavailable now`), com a ordem de nao contornar. Logo, os arquivos
  ficam versionaveis localmente mas **nao commitados**; o remoto
  `https://github.com/matheussilva421/amanda-tfg-bim-agent.git` segue em `main...origin/main` 0/0.
- Limpeza medida (nada apagado alem do scratch): `.dotnet` 769,9 MB (SDK 10.0.401; unico SDK que
  compila `vendor/RevitCortex` e `vendor/horizun-revit-mcp` — **exige autorizacao explicita**),
  `.venv-environmental` 451,0 MB e `.venv-topologic` 376,0 MB (exigidos por
  `tests/unit/test_topologic_spike.py`), `.venv` 441,9 MB, `vendor` 354,4 MB (contem o servidor MCP
  ativo), `revit` 103,3 MB (citar em `docs/reports/provider-update-isolation-drill.md`),
  `tool-lab\custom-api\obj` 0,98 MB (artefato de build, seguro).
- **Duplicata segura encontrada**: `TFG_Amanda Fernandes_ENTREGA 15.06.2026.pdf` na raiz tem
  `54.553.582` bytes, **identico** ao de `docs/source/`; `programa_necessidades.pdf` na raiz tem
  `31.004` bytes, tambem identico ao de `docs/source/`. `docs/source` e `immutable_path`, entao a
  copia da raiz e a candidata a remocao (~52 MB) — mas o revisor bloqueia `Remove-Item`, entao
  segue medido e nao apagado.
