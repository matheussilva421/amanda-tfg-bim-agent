# Verificação da cadeia Phase 00

Data da verificação: 2026-09-15. Escopo: P00-T01, P00-T02 e P00-T03. Este
relatório registra o estado observado; não atualiza `PROJECT_STATE.yaml`,
`state/task-graph.yaml` ou `state/task-history.yaml`.

## P00-T01 — repositório, pacote de planos e exclusões

Comandos executados:

```text
Get-Location
=> C:\Users\slvma\Downloads\Github\Projeto Amanda

git rev-parse --show-toplevel
=> C:/Users/slvma/Downloads/Github/Projeto Amanda

git status --short --branch
=> ## main
=> existem arquivos não rastreados de sessões paralelas; nenhum foi revertido

git remote -v
=> nenhuma saída; remote não configurado
```

`docs/review/package_review.py` existe (4.575 bytes) e foi lido antes da
verificação. Na implementação avaliada naquela data, ele escrevia o diretóriode planos estruturados e um ZIP de planos. Esses artefatos foram arquivados na
recuperação de 2026-09-24; esta descrição é evidência histórica, não o fluxo
atual. O inventário ativo está em `docs/plan/CURRENT.md` e `docs/spec/CURRENT.md`.
`docs/review/package-validation.json`; por isso não foi executado diretamente,
pois esses caminhos estão fora do write set desta tarefa. A mesma lógica de
separação de seções foi executada em memória:

```text
generated_sections=10
manifest_entries=10
canonical_hash_mismatches=[]
derived_hash_mismatches=[] (comparação com normalização de fim de linha Windows)
```

O manifesto persistido registra `generated_plans=10`,
`broken_local_links=0`, `verified_hashes=22` e `status=PASS_PACKAGE`. O hash
SHA-256 do `state/task-graph.yaml` no momento do relatório é
`7EDC072F44CAC1C787A51A8C2111C4F86318C96CB9B13CF80A6D8859F8EEC17D`.

Todas as regras obrigatórias do plano já estavam presentes no `.gitignore`,
incluindo `.venv/`, `vendor/`, fontes privadas, locks/logs privados e
extensões Revit. Nenhuma alteração foi necessária.

Pendência: não há destino Git configurado; nenhum remote ou repositório remoto
foi criado.

## P00-T02 — diagnóstico de ordem de plano

Arquivos desta implementação:

- `src/amanda_agent/state/plan_order.py`: API somente leitura
  `diagnose_plan_order()` e alias `verify_plan_order()`.
- `tests/policy/test_plan_order.py`: três testes comportamentais.

O diagnóstico valida as arestas entre fases e mantém separados os ramos
`revit` (`01 → 07A → 02`), `solver` (`01 → 03 → 04`) e `production` (a
convergência em `05` até `08`). Estados `BLOCKED_BY_TOOL`,
`BLOCKED_BY_INPUT` e `CRITICAL_FAILURE` são agregados por ramo, sem propagar
um bloqueio Revit ao ramo solver. A API não grava a entrada.

TDD e lint:

```text
$env:PYTHONIOENCODING="utf-8"; & "./.venv/Scripts/python.exe" -m pytest tests/policy/test_plan_order.py -q -p no:cacheprovider --basetemp=".tmp-pytest-luna-p00t02-red"
=> coleta falhou por ModuleNotFoundError: amanda_agent.state.plan_order
=> RED esperado antes da implementação

$env:PYTHONIOENCODING="utf-8"; & "./.venv/Scripts/python.exe" -m pytest tests/policy/test_plan_order.py -q -p no:cacheprovider --basetemp=".tmp-pytest-luna-p00t02-green"
=> 3 passed, 0 failed

& "./.venv/Scripts/python.exe" -m ruff check "src/amanda_agent/state/plan_order.py" "tests/policy/test_plan_order.py"
=> All checks passed
```

Leitura do grafo real:

```text
diagnose_plan_order(state/task-graph.yaml)
=> 159 tarefas; 9 arestas entre fases
=> passed=False
=> MISSING_PHASE_DEPENDENCY: PHASE_01 -> PHASE_03
=> MISSING_PHASE_DEPENDENCY: PHASE_01 -> PHASE_07A
=> branches: revit=PENDING, solver=PENDING, production=PENDING
```

Essas duas lacunas são o resultado real do grafo atual e não foram corrigidas,
porque `state/task-graph.yaml` é estado centralizado e está fora do write set.
Não há evidência de mutação do arquivo durante esta tarefa.

## P00-T03 — verificação global

Os diretórios `tests/geometry` e `tests/solver` podem ser criados por trabalho
paralelo; cada resultado abaixo conserva o timestamp em que foi observado.

1. Gate rápido, 2026-09-15T09:56:12-03:00:

```text
$env:PYTHONIOENCODING="utf-8"; & "./.venv/Scripts/python.exe" -m pytest tests/unit tests/geometry tests/solver -q -p no:cacheprovider --basetemp=".tmp-pytest-luna-p00t03-a"
=> exit_code=4
=> ERROR: file or directory not found: tests/geometry
=> 0 testes executados; 0 passed; 0 failed
```

2. Suíte não-Revit, 2026-09-15T09:56:26-03:00:

```text
$env:PYTHONIOENCODING="utf-8"; & "./.venv/Scripts/python.exe" -m pytest tests -m "not revit" -q -p no:cacheprovider --basetemp=".tmp-pytest-luna-p00t03-b"
=> 324 passed, 1 skipped, 12 failed
=> status vermelho, exit_code=1
```

Falhas principais: 9 testes em `tests/providers/test_toolmaps.py` não
encontram `state/providers/horizun-toolmap.yaml`; 3 testes em
`tests/solver/test_hard_constraints.py` encontram `TypeError` em
`src/amanda_agent/design/constraints.py:_matches` e `AttributeError` ao
tratar geometria de macro como objeto sem `.area`. Esses arquivos pertencem a
trabalho paralelo e não foram modificados.

3. Doctor, 2026-09-15T09:57:27-03:00. A saída foi direcionada a uma pasta
temporária para não sobrescrever `state/environment-report.json`:

```text
& "./.venv/Scripts/python.exe" -m amanda_agent doctor
=> exit_code=0; report gerado
=> git AVAILABLE; codex AVAILABLE; powershell AVAILABLE; dotnet AVAILABLE
=> python312 MISSING (não crítico)
=> revit DETECTED 20260716_1515(x64), file 27.2.0.39
```

4. Status, 2026-09-15T09:57:40-03:00:

```text
& "./.venv/Scripts/python.exe" -m amanda_agent status
=> exit_code=0
=> phase PHASE_02; status PENDING; next task P00-T01; revision 49
=> ready: P00-T01 P02-T05 P04-T02
=> writer lease free; 5 blockers abertos
```

`state/status.md` não existe. `PROJECT_STATE.yaml` existe e registra
`phase_gate: GO_WITH_LIMITATIONS`, `phase_status: PENDING` e
`last_completed_task: P02-T03`. Não foi encontrado manifest de release/GOLDEN
no projeto; `state/install-manifest.yaml` é o manifest do provider instalado,
não um release manifest.

## Estado final e retomada

Nenhum commit, push, remote, alteração de estado central ou alteração de
arquivo de outro agente foi feito. A cadeia Phase 00 não pode ser declarada
completa: o diagnóstico real tem duas dependências ausentes e os gates globais
possuem diretórios ausentes e falhas paralelas. Para retomar, o agente
integrador deve decidir sobre o remote, corrigir o grafo centralizado em uma
alteração coordenada, aguardar os testes de Geometry/Solver e repetir a matriz
P00-T03.
