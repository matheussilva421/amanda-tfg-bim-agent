# Handoff P05-T09..T23 — perfis e lacunas BIM

Data: 2026-09-15  
Agente: Arya / LUNA XHIGH  
Status: perfis, artefatos externos, subaplicação CLI e E2E R01..R13 concluídos localmente; registro no root `cli.py` permanece pendente.

## Escopo e restrições vigentes

- Checkout compartilhado: `C:\Users\slvma\Downloads\Github\Projeto Amanda`.
- Não criar branch/worktree e não executar `git add`, `commit`, `push`, `checkout`, `reset` ou `amanda_agent advance`.
- Preservar as alterações paralelas já existentes em `PROJECT_STATE.yaml`, `state/task-graph.yaml`, `state/task-history.yaml` e `src/amanda_agent/cli.py`.
- Write set deste bloco: perfis, artefatos externos, testes BIM/solver/integração e este handoff. `cli.py` e `src/amanda_agent/bim/stages/**` permanecem fora do escopo.
- Python de validação: `./.venv/Scripts/python.exe` com `$env:PYTHONIOENCODING='utf-8'`.

## Fatos verificados nesta retomada

- Git está em `main...origin/main`; há alterações não commitadas e muitos helpers `.tmp-*` não rastreados. Os `.tmp-*` existentes foram preservados.
- `PROJECT_STATE.yaml` ainda registra P02/PENDING, enquanto o grafo canônico mantém P05-T09..T23 como PENDING. A ordem explícita do pedido atual é a autoridade operacional deste bloco; os arquivos de estado não foram editados.
- `src/amanda_agent/bim/models.py` define `DesiredElement`; `bim.units` usa metros no domínio e pés na fronteira Revit.
- `src/amanda_agent/bim/external.py`, `src/amanda_agent/design/profiles.py`, `design-engine/config/profiles.yaml`, os testes pedidos e `tests/integration/` não existiam no início desta retomada.
- O catálogo de fontes foi consultado em 2026-09-15. Foram usadas URLs públicas da Anvisa/BVS-MS, Planalto, MDS e FNAS; nenhum paywall foi usado.

## Bloco concluído: perfis de programa

Arquivos criados:

- `src/amanda_agent/design/profiles.py`
- `design-engine/config/profiles.yaml`
- `tests/solver/test_design_profiles.py`

Contrato implementado:

- `load_profiles(path)` lê YAML com `yaml.safe_load`, recusa arquivo ausente/symlink, estrutura inválida, IDs duplicados, citations não resolvidas, shares que não totalizam 1 e capacidade acima de 20.
- `select_profile(id, allow_provisional=False)` usa o último catálogo carregado e recusa perfil provisional sem opt-in explícito. Aceita catálogo opcional para testes/uso isolado.
- `check_capacity(profile, people, allow_provisional=False)` valida contagem inteira não negativa e retorna `True` até 20 pessoas, `False` acima do teto; também recusa perfil provisional sem opt-in.
- Cada dimensão numérica é um `CitedNumber` com `citation_id`; valores provisórios exigem `confidence: low`.
- Perfis: `ambulatorial`, `internacao` e `centro-dia`, cada um com setores, shares, mínimo de salas, privacidade, área por pessoa, requisitos mandatórios, adjacências `mandatory`/`permitted`/`undesired` e citations.
- Shares e áreas que não foram localizados como medição oficial permanecem explicitamente provisórios. O registro não transforma essas escolhas em conformidade normativa.

## TDD e validação dos perfis

RED inicial:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/solver/test_design_profiles.py -q -p no:cacheprovider --basetemp=.tmp-pytest-profiles-red
```

Resultado: erro de coleta esperado — `ModuleNotFoundError: No module named 'amanda_agent.design.profiles'`.

GREEN após implementação mínima:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/solver/test_design_profiles.py -q -p no:cacheprovider --basetemp=.tmp-pytest-profiles-green
```

Resultado: 5 testes executados, 5 passaram, 0 falharam.

RED da reconciliação de shares:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/solver/test_design_profiles.py::test_profile_shares_must_account_for_the_complete_useful_area -q -p no:cacheprovider --basetemp=.tmp-pytest-profiles-share-red
```

Resultado: 1 falhou pelo motivo esperado — `DID NOT RAISE ProfileValidationError`.

GREEN final do bloco:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/solver/test_design_profiles.py -q -p no:cacheprovider --basetemp=.tmp-pytest-profiles-green2
```

Resultado: 6 testes executados, 6 passaram, 0 falharam.

## Bloco concluído: artefatos externos do Revit

Arquivos criados:

- `src/amanda_agent/bim/external.py`
- `tests/unit/test_bim_external.py`

Contrato implementado:

- `place_link(model_path, *, name, insertion)` recusa arquivo ausente/symlink, mantém a origem métrica e calcula a inserção em pés.
- `place_toposolid(footprint, *, elevation, name)` recusa menos de três pontos, área zero e valores não finitos; fecha o polígono e converte footprint/elevation para pés.
- `compute_true_north(azimuth_degrees)` preserva graus e fornece radianos para a fronteira do provider.
- `compute_georeference(lat, lon, elevation, *, epsg=4674)` valida latitude/longitude, EPSG e elevação; converte somente elevação para pés.
- Todos os builders são puros e só devolvem `DesiredElement`; não importam bridge nem executam Revit.
- O Toposolid usa `reference_level: null`, `reference_level_status: NOT_PROVEN` e nota de provenance `reference_level_proven: false`, sem inventar nível de referência.

TDD externo:

RED:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit/test_bim_external.py -q -p no:cacheprovider --basetemp=.tmp-pytest-external-red
```

Resultado: erro de coleta esperado — `ModuleNotFoundError: No module named 'amanda_agent.bim.external'`.

GREEN:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit/test_bim_external.py -q -p no:cacheprovider --basetemp=.tmp-pytest-external-green
```

Resultado: 8 testes executados, 8 passaram, 0 falharam.

RED adicional do formato de inserção usado pelos estágios:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit/test_bim_external.py::test_place_link_accepts_the_stage_mapping_insertion_shape -q -p no:cacheprovider --basetemp=.tmp-pytest-external-map-red
```

Resultado: 1 falhou pelo motivo esperado — o builder ainda não aceitava o mapping `x/y/z`.

GREEN após a correção mínima:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit/test_bim_external.py -q -p no:cacheprovider --basetemp=.tmp-pytest-external-green2
```

Resultado: 8 testes executados, 8 passaram, 0 falharam.

## Bloco concluído: subaplicação CLI BIM

Arquivos criados ou atualizados:

- `src/amanda_agent/commands/bim.py`
- `tests/unit/test_bim_cli.py`

Contrato implementado:

- `bim_app plan --solution PATH` lê e imprime um `BIM_PLAN.json` sem execução.
- `bim_app verify-plan PATH` imprime as regras independentes de write-read-verify.
- `bim_app status` informa o modo `SYNTHETIC_LAB` e que execução não é padrão.
- `bim_app execute --plan PATH --mode SYNTHETIC_LAB --fixture --execute` roda uma simulação determinística, explicitando `WRITE`, `READ` e `VERIFY`; sem `--execute`, sem `SYNTHETIC_LAB` ou sem `--fixture`, recusa.
- O simulador não abre Revit nem escreve o arquivo de plano; a execução real permanece dependente de um invoker injetado no pipeline.

TDD CLI:

RED inicial contra o root atual: 5 testes falharam com exit 2 porque o comando `bim` ainda não estava registrado em `cli.py`.

RED após isolar a subaplicação:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit/test_bim_cli.py -q -p no:cacheprovider --basetemp=.tmp-pytest-cli-red3
```

Resultado: erro de coleta esperado — `ModuleNotFoundError: No module named 'amanda_agent.commands.bim'`.

GREEN:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit/test_bim_cli.py -q -p no:cacheprovider --basetemp=.tmp-pytest-cli-green
```

Resultado: 6 testes executados, 6 passaram, 0 falharam.

## Bloco concluído: compilação BIM sintética ponta a ponta

Arquivo criado:

- `tests/integration/test_bim_synthetic_compile.py`

O teste exerce os planners e dispatchers públicos de R01 a R13 com um
`DeterministicInvoker` injetado. O provider é sintético, registra as chamadas e
nunca abre Revit. A matriz verifica:

- ordem exata R01..R13;
- igualdade dos planos e das chamadas em duas execuções independentes;
- preflight `SYNTHETIC_LAB` com fixture e registry sintético aprovado;
- `verify_write` para cada operação;
- 13 checkpoints com hash, reopen verify e manifests em arquivos temporários;
- consolidação do estado final por `logical_id` quando R12 atualiza a parede com
  uma atribuição de material;
- `diff_states` final completamente em `NOOP`;
- ausência de bridge Revit e de escrita real do modelo.

RED do harness:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/integration/test_bim_synthetic_compile.py -q -p no:cacheprovider --basetemp=.tmp-pytest-e2e-red
```

Resultado: 1 falhou pelo motivo esperado — o harness não criava os diretórios
temporários antes de escrever as evidências do registry.

GREEN final:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/integration/test_bim_synthetic_compile.py -q -p no:cacheprovider --basetemp=.tmp-pytest-final-e2e
```

Resultado: 1 teste executado, 1 passou, 0 falharam.

## Próxima tarefa exata

Integrar `bim_app` no root `src/amanda_agent/cli.py` com `app.add_typer(bim_app, name="bim")` no trabalho do agente que já edita esse arquivo, e rerodar `tests/unit/test_bim_cli.py` contra o root para validar a integração. O harness E2E já está criado e todos os módulos R01..R13 estavam disponíveis nesta retomada.

## Pendências e bloqueios

- Não há ainda comando `bim` registrado; `src/amanda_agent/cli.py` já está sendo editado por outro agente e não deve ser tocado.
- O comando root ainda não foi validado porque o registro em `cli.py` continua sob responsabilidade do outro agente. A subapp passou isoladamente.
- Integração solicitada ao agente responsável por `cli.py`:
  `from .commands.bim import bim_app` e `app.add_typer(bim_app, name="bim")`.
- Não há lacuna de módulos no pipeline local desta retomada: R01..R13 possuem planners e dispatchers públicos e foram exercitados pelo E2E.
- A validação continua sintética; não há evidência de execução física no Revit nem de provider real.
- Nenhuma alteração foi publicada no GitHub por restrição explícita desta tarefa.

## Verificação final desta sessão

Testes focados, executados após a última alteração:

```text
tests/solver/test_design_profiles.py              6 passed
tests/unit/test_bim_external.py                  8 passed
tests/unit/test_bim_cli.py                       6 passed
tests/integration/test_bim_synthetic_compile.py  1 passed
```

Suíte BIM/stages relacionada: 137 testes passaram, 0 falharam.

Suíte completa `tests`: 637 passaram, 1 foi ignorado, 0 falharam.

Ruff nos arquivos deste bloco: `All checks passed!`.
`git diff --check` não encontrou erro de whitespace; os avisos exibidos são
apenas conversões de final de linha de arquivos já modificados por outros
agentes.

Status GitHub: sem `git add`, commit ou push, conforme a restrição explícita do
pedido. As alterações paralelas e os helpers `.tmp-*` foram preservados.

Retomada: após o outro agente registrar `bim_app` em `cli.py`, executar
`$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m amanda_agent.cli bim --help` e repetir o teste da subapp contra o root. Em seguida, o orquestrador pode fechar as tarefas com esta evidência; não executar `amanda_agent advance` neste checkout.
