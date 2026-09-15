# Evidência — Design e Compare CLI (P04-T22)

Data da verificação: 2026-09-15.

## Entradas canônicas descobertas

O CLI lê exatamente:

- `project/requirements/program.json`
- `project/site/site.json`
- `project/provenance/source-manifest.yaml` e os arquivos imutáveis sob `docs/source/` para validar proveniência e hashes

Cada execução nova é publicada em `design-engine/runs/<RUN_ID>/run.json`.
`compare <RUN_ID>` salva `design-engine/runs/<RUN_ID>/finalist-matrix.json`.
O diretório existente nunca é sobrescrito.

## Comandos executados

```powershell
$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest tests/unit/test_design_cli.py -v -p no:cacheprovider --basetemp=.tmp-pytest-p04t22-final-focused
```

Resultado: 3 testes executados; 3 passaram; 0 falharam. Status: PASS.

```powershell
$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -c "from pathlib import Path; from amanda_agent.commands.design import load_canonical_inputs; x=load_canonical_inputs(Path.cwd()); print('source state', len(x['requirements']), len(x['site']))"
```

Resultado: exit code 0; `source state 7 15`.

```powershell
$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m pytest tests/unit -q -p no:cacheprovider --basetemp=.tmp-pytest-unit-full-p02t20-p04t22
```

Resultado: 370 testes coletados; 369 passaram; 0 falharam; 1 foi ignorado.
Status: PASS.

## Contratos verificados

- `design --run-id RUN-001` valida manifesto, proveniência, schema, totais,
  geometria da fronteira e topografia antes de executar o pipeline.
- Uma alteração no arquivo imutável do manifesto é recusada e não cria o
  diretório do run.
- Os testes calculam hashes antes/depois de `program.json` e `site.json`; os
  hashes permanecem iguais.
- `compare RUN-001` imprime a matriz e grava JSON com identificador, seed,
  status, hash geométrico, métricas e violações duras.
- A geração usa o pipeline determinístico existente e não faz chamadas Revit.
  No probe read-only de 3 seeds com os dados canônicos reais: 3 candidatos,
  0 finalistas e 3 rejeições; o resultado foi preservado como estado do
  pipeline, sem fabricar finalistas.

## Handoff

- Alterações principais: criação de `design.py` e `compare.py`, registro dos
  comandos em `cli.py` e testes comportamentais em `test_design_cli.py`.
- Decisão técnica: o estudo aceita a fronteira planar placeholder válida como
  limitação explícita; fonte mutável, manifesto divergente ou JSON inválido
  interrompem a execução antes da publicação.
- GitHub: nenhum add/commit/push foi executado por instrução da tarefa; o
  worktree mantém alterações prévias do usuário.
- Rechecagem final: `test_design_cli.py` terminou com 3 pass, 0 fail; Ruff e
  `git diff --check` também terminaram verdes.
- Pendência honesta: os dados canônicos reais ainda não geram um finalista no
  probe executado; investigar o pipeline de geração/refino é uma tarefa
  posterior, sem relaxar restrições ou inventar uma alternativa.
- Retomada: rodar o teste focado, chamar `design --run-id` com um identificador
  novo em uma cópia/ambiente de estudo, e então chamar `compare` para revisar a
  matriz persistida.
