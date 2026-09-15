# Handoff P06 QA validators — 2026-09-15

## Escopo e status

Athena implementou os tasks P06-T01..P06-T09 no write set delegado. Os
validadores são locais, gratuitos e fail-closed; nenhum Autodesk APS/Forge,
AutoCAD ou dependência paga foi usado. As evidências são sintéticas ou
injetadas, portanto não representam validação em Revit real nem aceitação FINAL.

| Task | Status | Evidência |
|---|---|---|
| P06-T01 | PASS | `tests/unit/test_qa_models.py`: 6 passed |
| P06-T02 | PASS | `tests/unit/test_program_qa.py`: 6 passed |
| P06-T03 | PASS | `tests/unit/test_model_qa.py`: 6 passed |
| P06-T04 | PASS | `tests/unit/test_warning_delta.py`: 3 passed |
| P06-T05 | PASS | `tests/unit/test_architecture_qa.py`: 4 passed |
| P06-T06 | PASS | `tests/unit/test_accessibility_qa.py`: 5 passed |
| P06-T07 | PASS | `tests/unit/test_ifc_qa.py`: 3 passed |
| P06-T08 | PASS | `tests/unit/test_pdf_qa.py`: 3 passed |
| P06-T09 | PASS | `tests/unit/test_dwg_qa.py`: 3 passed |

## Arquivos criados ou alterados

- `src/amanda_agent/qa/__init__.py`
- `src/amanda_agent/qa/models.py`
- `src/amanda_agent/qa/program.py`
- `src/amanda_agent/qa/model.py`
- `src/amanda_agent/qa/warnings.py`
- `src/amanda_agent/qa/architecture.py`
- `src/amanda_agent/qa/accessibility.py`
- `src/amanda_agent/qa/ifc.py`
- `src/amanda_agent/qa/pdf.py`
- `src/amanda_agent/qa/dwg.py`
- `state/known-warnings.yaml`
- `tests/unit/test_qa_models.py`
- `tests/unit/test_program_qa.py`
- `tests/unit/test_model_qa.py`
- `tests/unit/test_warning_delta.py`
- `tests/unit/test_architecture_qa.py`
- `tests/unit/test_accessibility_qa.py`
- `tests/unit/test_ifc_qa.py`
- `tests/unit/test_pdf_qa.py`
- `tests/unit/test_dwg_qa.py`

Este handoff é o arquivo adicional exigido pela tarefa. Não foram editados
`commands/**`, `release/**`, `qa/persistence.py`, `qa/visual.py`,
`recovery/**`, `cli.py`, `state/task-graph.yaml` ou `PROJECT_STATE.yaml`.

## Decisões técnicas

- `QaReport` deriva `result` de checks/issues e usa precedência fail-closed:
  CRITICAL ou check obrigatório FAIL resulta em FAIL; check obrigatório
  BLOCKED/SKIPPED, check ausente no perfil ou issue de input ausente resulta em
  BLOCKED_BY_INPUT; issues opcionais resultam em PASS_WITH_WARNINGS.
- A reconciliação de programa recebe um modelo de programa injetado ou YAML e
  usa apenas `logical_id`, quantidade e regras de área configuradas. Ambientes
  internos e externos são reconciliados pelo mesmo caminho.
- QA geométrico consome evidência de query, incluindo ids duplicados, hosts,
  salas, limites do terreno, níveis e delta de contagem; não confia em retorno
  de escrita.
- O baseline de warnings tem `schema_version`, `severity_map_version`, regex,
  texto, severidade, status, razão e proveniência. Warning conhecido continua
  conhecido; warning sem baseline permanece NEW/REVIEW com evidência de query e
  nunca é auto-ignorado.
- Arquitetura compara grafo aprovado/BIM e políticas injetadas de fluxo público,
  serviço, jardim e métricas shelter/transição/cidade.
- Acessibilidade separa continuidade de rota por grafo/geometria de dimensões
  numéricas. Dimensão só usa regra com `status: VERIFIED` e `source`; ausência
  bloqueia o check. Checks não suportados aparecem como SKIPPED com motivo.
- IFC usa IfcOpenShell 0.8.5, rejeita zero-byte/header inválido/parse inválido,
  conta storeys/spaces/walls/doors/openings e valida mapeamentos logical_id ↔
  IFC GUID. Splits/merges exigem mapeamento explícito; contagens isoladas não
  provam fidelidade.
- PDF usa pypdf 6.0.0, pypdfium2 5.13.0 e Pillow para contar páginas,
  rasterizar todas as páginas, salvar previews e calcular páginas, blank_pages,
  sizes e sha256. Variância raster identifica página em branco como sinal de
  máquina e mantém a revisão visual separada.
- DWG não tem parser local aprovado/testado no repositório. A validação aceita
  assinatura `AC10xx` e tamanho não-zero e sempre reporta
  `LIMITED_DWG_VALIDATION`; não instala AutoCAD.

## Testes e resultados exatos

Cada conjunto isolado foi executado com `PYTHONIOENCODING=utf-8`, pytest da
`.venv`, `-p no:cacheprovider` e basetemp exclusivo:

```text
test_qa_models.py          6 passed
test_program_qa.py        6 passed
test_model_qa.py          6 passed
test_warning_delta.py     3 passed
test_architecture_qa.py   4 passed
test_accessibility_qa.py  5 passed
test_ifc_qa.py            3 passed
test_pdf_qa.py            3 passed
test_dwg_qa.py            3 passed
```

Matriz conjunta:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit/test_qa_models.py tests/unit/test_program_qa.py tests/unit/test_model_qa.py tests/unit/test_warning_delta.py tests/unit/test_architecture_qa.py tests/unit/test_accessibility_qa.py tests/unit/test_ifc_qa.py tests/unit/test_pdf_qa.py tests/unit/test_dwg_qa.py -q -p no:cacheprovider --basetemp=.tmp-pytest-athena-q6
```

Resultado: 39 testes executados, 39 passaram, 0 falharam (`1.35s` na última
execução conjunta).

Qualidade estática:

```text
ruff check [arquivos Athena] -> All checks passed!
mypy [10 arquivos src/amanda_agent/qa] -> Success: no issues found in 10 source files
```

Suíte ampla solicitada:

```powershell
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pytest tests/unit tests/solver -q -p no:cacheprovider --basetemp=.tmp-pytest-athena-all
```

Resultado: a coleta foi interrompida antes da execução por
`SyntaxError: tests/unit/test_release_promotion.py:55` (`project="Amanda TFG
BIM Agent"` dentro de um dict). O arquivo pertence ao bloco release fora do
write set Athena.

Para medir os testes executáveis, a mesma suíte foi rodada ignorando somente
esse arquivo:

```text
586 passaram, 13 falharam em 19.36s.
```

As 13 falhas são de `test_checkpoints.py`, `test_reboot_resume.py`,
`test_recovery_manager.py` e `test_stage_project.py`. Todas falham antes do
escopo QA porque `bim/checkpoints.py` trata o nome do basetemp
`.tmp-pytest-athena-all-except-release-2` como caminho protegido por conter
`checkpoint`; esse código e esses testes são de outros agentes.

## Retomada pelo agente principal

1. Preservar este handoff e validar o estado do Git antes de integrar; Athena
   não executou `git add`, `git commit`, `git push` nem alterou o grafo de tasks.
2. Integrar os arquivos Athena e avançar P06-T01..P06-T09 somente com a
   evidência individual/conjunta acima, mantendo os status de P06 separados da
   falha de coleta do release.
3. Corrigir ou coordenar o agente responsável por
   `tests/unit/test_release_promotion.py:55` antes de usar a suíte ampla como
   gate global.
4. Corrigir o conflito de nome no basetemp/proteção de
   `bim/checkpoints.py` no write set do agente BIM/recovery e repetir a suíte
   ampla com um basetemp que não contenha tokens protegidos.
5. Antes de declarar GO/FINAL, executar QA com evidência real do modelo,
   persistência fria, exports reais e revisão visual. A fixture IFC é apenas
   sintética; DWG permanece limited; blank PDF é somente sinal de máquina.
