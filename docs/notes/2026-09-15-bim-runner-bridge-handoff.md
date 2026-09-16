# Handoff — ponte do runner BIM

Data: 2026-09-15  
Agente: LUNA XHIGH  
Escopo: ponte pura R01–R13 para invoker injetado e drill sintético fail-closed.

## Entregue

- `src/amanda_agent/bim/runner.py`: `OperationRunRecord`, `StageRunResult`, `execute_stage` e `execute_chain`. Despacha na ordem, usa `read_payload`/`payload` como readback independente, chama `verify_write`, preserva erros, classifica `VERIFIED`/`FAILED`/`IN_DOUBT`, para após incerteza e recusa cadeia vazia, fora de ordem, duplicada ou com preflight falho.
- `src/amanda_agent/bim/lab_fixture.py`: construtor determinístico dos 13 planos sintéticos e registry sintético auxiliar.
- `tests/unit/test_bim_runner.py`: 7 testes de contrato.
- `tests/integration/test_bim_synthetic_compile.py`: usa o fixture novo e prova 13 estágios `VERIFIED` na ordem com invoker falso, preservando as asserções existentes.
- `scripts/bim_lab_drill.py`: dry-run padrão; `--execute` exige caminhos dentro de `revit/lab`, lock, sentinel, Horizun/MCP, checkpoint e journal por estágio.

## TDD e validação

RED:

```powershell
./.venv/Scripts/python.exe -m pytest tests/unit/test_bim_runner.py --basetemp=.tmp-luna-bim-runner-red -p no:cacheprovider -q --tb=short
```

5 falharam pelo motivo esperado: `ModuleNotFoundError` para `amanda_agent.bim.runner`.

GREEN:

```powershell
./.venv/Scripts/python.exe -m pytest tests/unit/test_bim_runner.py tests/integration/test_bim_synthetic_compile.py --basetemp=.tmp-luna-bim-final-focused -p no:cacheprovider -q --tb=short
```

8 passaram, 0 falharam. Também: 608 unitários passaram excluindo `tests/unit/test_topologic_spike.py`; ruff passou nos cinco arquivos; mypy passou em `runner.py`, `lab_fixture.py` e `bim_lab_drill.py`. A suíte unitária completa teve 608 pass e 1 falha externa no Topologic por consulta à PyPI/offline (`TypeError` após `Helper.CheckVersion`).

Smoke do script: dry-run retornou `python_exit=0`, 121 linhas de plano, sem Revit/MCP/lock/checkpoint persistente. `--execute` fora de `revit/lab` retornou `python_exit=2` antes do lock.

## Limitações e retomada

- Não foram executados Revit, MCP real, serviço pago, `--execute`, leitura física, save/reopen ou persistência BIM.
- O checkpoint/journal real do drill e a saúde do provider Horizun permanecem não provados até revisão do pai.
- Git foi explicitamente proibido nesta tarefa: sem `git status`, commit, push ou SHA; o GitHub não foi atualizado por este agente.
- Próximo passo: revisar este write set e, sob autorização separada do pai, executar somente um RVT/fixture descartável dentro de `revit/lab`, mantendo o bloqueio para GOLDEN/source/produção.
