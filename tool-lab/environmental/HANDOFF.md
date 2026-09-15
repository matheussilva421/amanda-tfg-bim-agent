# Handoff P04-T21 — 2026-09-15

## Estado

Task concluída no escopo autorizado, sem alterar `src/`, `tests/`, `state/`,
`PROJECT_STATE.yaml`, `tool-lab/custom-api/`, `tool-lab/revitcortex/` ou
`tool-lab/horizun/`. Nenhum `git add`, commit, push, checkout, reset ou
`complete_task` foi executado.

Decisão: **ADOTAR_COM_LIMITES**. O ambiente isolado `.venv-environmental`
contém `ladybug-core==0.44.59` e `lbt-honeybee==0.9.467`; 34 wheels foram
baixados para `tool-lab/environmental/wheels/`, hashados e instalados com
`--require-hashes`. `pip check` passou.

## Evidência

- Imports Ladybug/Honeybee/OpenStudio: PASS.
- CLIs `--help`: PASS; versões específicas Energy/Radiance/OpenStudio:
  `1.124.0`, `1.66.288`, `0.7.2`; grupos raiz Ladybug/Honeybee têm o erro de
  descoberta de metadata registrado no JSON.
- EPW sintético: Natal/RN/BRA, timezone `-3.0`, 2021, 8760 h, 1270148 bytes,
  SHA-256 `76da4b9dd7f902ede76e5bec81b0ee6dffdb369e17b9caca8c0b919a6c6862b4`.
- EnergyPlus real: `24.1.0-9d7789a3ac`, encontrado no OpenStudio CLI do Revit.
  Dois runs nativos retornaram 0, sem Fatal e com `.eso`/SQLite/tabela; hashes
  semânticos coincidem. Caso rotulado `SIMULATED`; `YMD` de execução é
  normalizado porque varia nos bytes brutos.
- Radiance real: `rtrace.exe` e `oconv.exe` ausentes; `radiance_solver=UNTESTED`.
  `ReadVarsESO.exe` também ausente, mas não é necessário para validar o output
  nativo deste spike.

Gate final fresco: `pip check` exit 0; `ruff check tool-lab/environmental/probe.py`
exit 0; duas execuções integrais de `probe.py` exit 0; o JSON foi byte-idêntico
nas duas (`SHA-256 625c34850502cdc59d71efb78094fc356150fe177b1354b635d2f5e8d80ce6e4`);
34/34 hashes do lock conferem.

## Arquivos e retomada

Artefatos principais: `README.md`, `requirements-lock.txt`, `probe.py`,
`results/environmental-probe.json`, `fixtures/*.epw`, `fixtures/*.idf`,
`results/energyplus-run-1/` e `results/energyplus-run-2/`.

Reexecutar no diretório do projeto:

```powershell
$env:PYTHONIOENCODING='utf-8'
& './.venv-environmental/Scripts/python.exe' -m pip check
& './.venv-environmental/Scripts/python.exe' './tool-lab/environmental/probe.py'
```

Próximo passo externo: o agente principal deve revisar/registrar o grafo e
commitar/pushar os artefatos autorizados. Não promover Radiance até instalar ou
localizar gratuitamente os binários reais e repetir o caso sintético com
outputs validados.
