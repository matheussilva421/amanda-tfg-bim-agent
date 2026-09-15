# Evidência — Tool Lab CLI (P02-T20)

Data da verificação: 2026-09-15.

## Resultado

O módulo `python -m amanda_agent.cli` agora invoca o app Typer. A saída de
`tool-lab status` deixa de ser vazia e informa provider, commit, health e
contagens. `queue` prioriza capacidades `UNTESTED` requeridas e não imprime
caminho de arquivo de produção. `verify-registry` valida o provider preferido,
status das capacidades e evidência de save/reopen.

## Comandos executados

```powershell
$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest tests/unit/test_tool_lab_cli.py -v -p no:cacheprovider --basetemp=.tmp-pytest-p02t20-final-focused
```

Resultado: 9 testes executados; 9 passaram; 0 falharam. Status: PASS.

```powershell
$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m amanda_agent.cli tool-lab status
```

Resultado: exit code 0. Provider `horizun-revit-mcp`, commit
`cc4ea04e9ecfe547ad349f22e0864019ce1ead1f`, health `DETECTED`, contagens
`PASS 14`, `FAIL 0`, `UNTESTED 6`, Revit `27.2.0.39`.

```powershell
$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m amanda_agent.cli tool-lab queue
```

Resultado: exit code 0. 17 itens emitidos; 7 `UNTESTED` requeridos aparecem
antes de 10 `PASS`; nenhum caminho absoluto ou `AmandaProduction.rvt` aparece.

```powershell
$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m amanda_agent.cli tool-lab verify-registry
```

Resultado: exit code 1, esperado para o estado durável atual. O registro
recusa o provider preferido porque há capacidades `UNTESTED` e sem evidência de
save/reopen; isso é uma falha real do registro de capacidades, não uma falha de
roteamento do CLI.

## Handoff

- Arquivos da tarefa: `src/amanda_agent/commands/tool_lab.py`, `src/amanda_agent/commands/design.py`, `src/amanda_agent/commands/compare.py`, `src/amanda_agent/cli.py`, `tests/unit/test_tool_lab_cli.py` e `tests/unit/test_design_cli.py`.
- A correção RED/GREEN foi registrada em `test_module_invocation_renders_tool_lab_status`: antes, `stdout=''`; depois, 9/9.
- Não foram chamados `complete_task`, `git add`, `git commit`, `git push`, `checkout` ou `reset`.
- Rechecagem final: `test_tool_lab_cli.py` terminou com 9 pass, 0 fail; os
  JSONs de resultado Topologic foram restaurados byte a byte ao `HEAD`.
- Pendência operacional: testar as capacidades reais ainda `UNTESTED` com as evidências exigidas pelo plano antes de promover o registro.
- Retomada: executar os comandos acima; depois atualizar o registro de capacidades e repetir `verify-registry` somente quando houver evidência independente de cada escopo.
