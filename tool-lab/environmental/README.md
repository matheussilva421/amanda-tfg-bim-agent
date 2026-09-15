# P04-T21 — Ambiente Ladybug/Honeybee

Decisão observada: **ADOTAR_COM_LIMITES**.

O ambiente é opcional e isolado em `.venv-environmental`; o solver heurístico
central em `src/amanda_agent` não depende dele. O lock foi resolvido em wheels
locais e instalado com `--no-index --require-hashes`.

## Comandos executados

```powershell
$env:PYTHONIOENCODING='utf-8'
& './.venv/Scripts/python.exe' -m venv '.venv-environmental'
& './.venv-environmental/Scripts/python.exe' -m pip index versions ladybug-core
& './.venv-environmental/Scripts/python.exe' -m pip index versions lbt-honeybee
& './.venv-environmental/Scripts/python.exe' -m pip download --disable-pip-version-check --no-cache-dir --only-binary=:all: --dest './tool-lab/environmental/wheels' 'ladybug-core==0.44.59' 'lbt-honeybee==0.9.467'
& './.venv-environmental/Scripts/python.exe' -m pip install --disable-pip-version-check --no-cache-dir --no-index --find-links './tool-lab/environmental/wheels' --require-hashes -r './tool-lab/environmental/requirements-lock.txt'
& './.venv-environmental/Scripts/python.exe' -m pip check
& './.venv-environmental/Scripts/python.exe' './tool-lab/environmental/probe.py'
```

`pip index` retornou `ladybug-core 0.44.59` e `lbt-honeybee 0.9.467` como
versões mais recentes no índice consultado. A instalação aceitou 34 wheels;
`pip check` retornou `No broken requirements found.`. Os arquivos baixados,
seus tamanhos e SHA-256 estão no relatório e os 34 hashes conferem com este
lock.

## Licença e composição

Não foi encontrada indicação de licença paga, assinatura ou ativação comercial
nos metadados dos 34 wheels. O stack Ladybug/Honeybee reporta AGPL-3.0; o
OpenStudio reporta BSD3; outras dependências reportam MIT/BSD ou expressões
SPDX equivalentes. `honeybee-radiance-folder` não declara licença no metadata,
portanto isso permanece uma lacuna de metadata, não uma aprovação legal.

`lbt-honeybee` é uma distribuição agregadora. Ela instalou, entre outros,
`honeybee-energy 1.124.0`, `honeybee-radiance 1.66.288`,
`honeybee-openstudio 0.7.2`, `openstudio 3.11.0` e `cupy-cuda12x 13.6.0`.
Nenhum desses componentes foi instalado globalmente.

## O que foi realmente provado

- Imports Python de Ladybug EPW/Sunpath, Honeybee Model, Honeybee Energy,
  Honeybee Radiance, Honeybee Display e OpenStudio passaram.
- `ladybug --help`, `honeybee --help`, `honeybee-energy --help`,
  `honeybee-radiance --help` e `honeybee-openstudio --help` passaram.
  `honeybee-energy --version` retornou `1.124.0`, `honeybee-radiance` retornou
  `1.66.288` e `honeybee-openstudio` retornou `0.7.2`.
- Os grupos raiz `ladybug --version` e `honeybee --version` retornam exit 1
  com `RuntimeError: 'ladybug'/'honeybee' is not installed. Try passing
  'package_name' instead.`. Isso é registrado como limitação do CLI de grupo;
  os sub-CLIs específicos funcionam.
- O EPW usado é explicitamente sintético e determinístico, não uma estação
  meteorológica medida: `Natal/RN/BRA`, WMO `999999`, timezone `-3.0`, ano
  `2021`, `8760` horas, `1270148` bytes,
  SHA-256 `76da4b9dd7f902ede76e5bec81b0ee6dffdb369e17b9caca8c0b919a6c6862b4`.
  O probe validou também estatísticas de temperatura e cálculo solar com
  `ladybug-core` puro.
- O executável real EnergyPlus foi encontrado em
  `C:\Program Files\NREL\OpenStudio CLI For Revit 2027\EnergyPlus\energyplus.exe`
  e retornou `EnergyPlus, Version 24.1.0-9d7789a3ac`.
- O caso EnergyPlus usa a entrada congelada
  `fixtures/honeybee_energy_minimal_24_1.idf`, SHA-256
  `cba98d3ea4597f180e9821bb2b630d4f1541e0c49cf516031a85161e6c6ffb58`, e o
  EPW sintético. Dois runs retornaram exit 0, sem `** Fatal **`, e geraram
  `.eso`, SQLite e `eplustbl.csv` não vazios. Os hashes semânticos coincidiram:
  `.eso` `295adf57b413bed2ca3b9c6d318235b539e1efb35155ad8865b5968f7cbb33f9`,
  SQLite `f73b8d0ab058738173f9eb9a988f41bb97cadfefd07b501c6e6cf4a11e1808bb`
  e tabela `385e0fc15cfcdad9cd80637677d79773ec57b90fb20eaead58ac84948fd55998`.
  A saída é rotulada `SIMULATED` no nível semântico validado.

O EnergyPlus grava `YMD=...` do momento da execução nos arquivos nativos; os
hashes brutos podem mudar por esse metadata. O probe normaliza somente esse
campo transitório para comparar os dados semânticos. O caso mínimo produziu
warnings não fatais, incluindo sizing sem objetos de sizing e temperatura de
solo default; eles ficam nos `eplusout.err` dos dois runs.

## Limites que impedem adoção plena

`rtrace.exe` e `oconv.exe` do Radiance não foram encontrados no PATH, em
`C:\EnergyPlus`, `C:\Radiance`, `C:\Program Files` ou `C:\Program Files (x86)`;
nenhum executável Radiance foi executado. O binding OpenStudio e os módulos
Python Honeybee Radiance não substituem esses motores. A instalação também não
tem `ReadVarsESO.exe`; por isso o caso usa outputs nativos sem `-r`, e não
declara o pós-processamento CSV como prova independente.

Assim, `energyplus_solver=PASS`, `radiance_solver=UNTESTED` e
`core_engine_impact=UNBLOCKED`. Para uma receita Radiance ser rotulada
`SIMULATED`, ainda faltam os executáveis reais (`rtrace` e `oconv` no mínimo),
suas versões, um caso Radiance sintético offline e dois outputs validados com
hash semântico estável. Para uma receita EnergyPlus equivalente, a prova
`SIMULATED` deste spike já existe, com a ressalva do metadata `YMD`.

## Artefatos

- `probe.py`: probe reexecutável e fail-closed para fixture/IDF alterados.
- `requirements-lock.txt`: 34 distribuições com hashes SHA-256 dos wheels.
- `fixtures/synthetic_natal_2021.epw`: EPW sintético de 8760 horas.
- `fixtures/honeybee_energy_minimal_24_1.idf`: entrada IDF congelada e hashada.
- `results/environmental-probe.json`: evidência estruturada, incluindo imports,
  CLIs, licenças, EPW, engines e os dois runs.
- `results/energyplus-run-1/` e `results/energyplus-run-2/`: outputs reais do
  EnergyPlus usados na comparação.
- `HANDOFF.md`: estado curto e instruções de retomada.
