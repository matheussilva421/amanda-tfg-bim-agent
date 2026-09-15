# P07-T18 — provider update isolation drill

Data: 2026-09-15  
Status: `PASS_WITH_LIMITATIONS` para o isolamento offline; nenhum update de
provider foi promovido.

## Limite de isolamento

O experimento foi montado em `.tmp-p07-isolation/` com cópias de
`tool-lab/fixtures/` e da matriz/mocks do fault runner. Não foi usado `git
worktree`, conforme a instrução desta tarefa. A versão real observada foi a
branch `main` no checkout compartilhado; o estado Git estava sujo por trabalho
paralelo. Uma worktree real isolaria o código-fonte, mas não `%APPDATA%` de
add-ins, configuração do Codex, portas, DLLs instaladas ou processos Revit.
Por isso um update real exigiria janela de manutenção, raiz de deployment
separada, um único dono do processo e backup/rollback verificados.

Não houve instalação, build, escrita em `%APPDATA%`, alteração da configuração
do Codex, abertura de Revit ou chamada a provider real.

## Execução

O runner offline existente foi executado contra a matriz de fault injection e
gravou todos os resultados em `.tmp-p07-isolation/results/`:

```powershell
$env:PYTHONIOENCODING='utf-8'
& './.venv/Scripts/python.exe' '.tmp-p07-isolation-run.py'
```

Resultado base da regressão Tool Lab:

| Total | PASS | FAIL | BLOCKED | SKIPPED_NEEDS_REVIT |
|---:|---:|---:|---:|---:|
| 8 | 4 | 0 | 0 | 4 |

O runner copiado foi também testado dentro da raiz de experimento:

```powershell
$env:PYTHONIOENCODING='utf-8'
& './.venv/Scripts/python.exe' -m pytest `
  '.tmp-p07-isolation/tool-lab/fault-injection/test_run_matrix.py' `
  -q -p no:cacheprovider --basetemp='.tmp-pytest-hades-isolation'
```

Resultado: `3 testes executados, 3 aprovados, 0 falhados`.

O experimento falho foi deixado deliberadamente em
`.tmp-p07-isolation/tool-lab/fault-injection/experiment-failing.yaml`: a cópia
da expectativa de `FI-004` foi alterada para um erro impossível de coincidir.
Isso produziu o resultado esperado para a demonstração de contenção:

| Total | PASS | FAIL | BLOCKED | SKIPPED_NEEDS_REVIT | exit code |
|---:|---:|---:|---:|---:|---:|
| 8 | 3 | 1 | 0 | 4 | 1 |

Esse FAIL pertence somente à matriz copiada; não é falha da produção nem foi
usado para alterar capabilities.

## Pinos de produção antes/depois

O arquivo de evidência completo é
`.tmp-p07-isolation/isolation-report.json`. O script recalculou SHA-256 antes e
depois para os dois pinos solicitados e para cada `.rvt` em
`revit/lab/**/*.rvt`: `21` arquivos RVT foram comparados e
`production_pins_unchanged=true`.

| Arquivo | SHA-256 antes e depois |
|---|---|
| `state/bim-environment.lock.yaml` | `355fa0d4fa0c72680344d0b81e4770c29e6af39b9298fa09275b1706b32d81a1` |
| `state/capabilities.yaml` | `0912b244ff842697e47f1ce27e5543d46c227447e97c5c1c099c2e4c082a066d` |
| `revit/lab/baseline/LAB_R00_EMPTY.rvt` | `15e0f70df13a9ad0635a7651b3fedff59e76dcfe582c25a7ea759a4b0698299d` |
| `revit/lab/custom-api/LAB_CUSTOM_WALL.0004.rvt` | `15e0f70df13a9ad0635a7651b3fedff59e76dcfe582c25a7ea759a4b0698299d` |
| `revit/lab/custom-api/LAB_CUSTOM_WALL.rvt` | `8ccab171e89fa4ac414f9ca3c57b5c4161cd7ee6dd61f45f86529703ee281cb2` |
| `revit/lab/custom-api/T18_CRASH_WORK.rvt` | `8ccab171e89fa4ac414f9ca3c57b5c4161cd7ee6dd61f45f86529703ee281cb2` |
| `revit/lab/custom-api/T18_LAST_PASS.rvt` | `8ccab171e89fa4ac414f9ca3c57b5c4161cd7ee6dd61f45f86529703ee281cb2` |
| `revit/lab/horizun/LAB_HORIZUN_DOC.0001.rvt` | `15e0f70df13a9ad0635a7651b3fedff59e76dcfe582c25a7ea759a4b0698299d` |
| `revit/lab/horizun/LAB_HORIZUN_DOC.rvt` | `6a1544d3075f86219cec609010c2446608916f2be7b917386836e93b051d829c` |
| `revit/lab/horizun/LAB_HORIZUN_FLOOR.0002.rvt` | `962a1e6b5cbb1b7716eb9bf2f3a9d87f36e2e1507a5a1015216be42ecafd5b68` |
| `revit/lab/horizun/LAB_HORIZUN_FLOOR.rvt` | `b7ef11f9dd866594aaefcab376846373071173be5d73798eaba9056a084fe28b` |
| `revit/lab/horizun/LAB_HORIZUN_LEVEL.0001.rvt` | `15e0f70df13a9ad0635a7651b3fedff59e76dcfe582c25a7ea759a4b0698299d` |
| `revit/lab/horizun/LAB_HORIZUN_LEVEL.rvt` | `8b15d7360672d4cdafdf5742f031f6b11a17dbd4d9eba6d4fcde725586fb3025` |
| `revit/lab/horizun/LAB_HORIZUN_READ.rvt` | `15e0f70df13a9ad0635a7651b3fedff59e76dcfe582c25a7ea759a4b0698299d` |
| `revit/lab/horizun/LAB_HORIZUN_ROOM.0002.rvt` | `329ed4148b40c8b104edf35392489435350d5c3d9d26e7fbf1aa1403e72b4ceb` |
| `revit/lab/horizun/LAB_HORIZUN_ROOM.rvt` | `9bf42c556bd6a57e52aa3f1184c6f5500b776949fd0da34f9cd71aa1915b20c3` |
| `revit/lab/horizun/LAB_HORIZUN_TOPO.0001.rvt` | `15e0f70df13a9ad0635a7651b3fedff59e76dcfe582c25a7ea759a4b0698299d` |
| `revit/lab/horizun/LAB_HORIZUN_TOPO.0002.rvt` | `d1011d1bdce5f2777b790cc55b01699bc39eb048c80064715ffc11bf9b1981e6` |
| `revit/lab/horizun/LAB_HORIZUN_TOPO.rvt` | `5a66bfa4c79036232503ada4842b60c53f45ad4b3aa23b0141013e843b2021a6` |
| `revit/lab/horizun/LAB_HORIZUN_WALL.0001.rvt` | `15e0f70df13a9ad0635a7651b3fedff59e76dcfe582c25a7ea759a4b0698299d` |
| `revit/lab/horizun/LAB_HORIZUN_WALL.rvt` | `6fd0ab2dc2512847215a87e6af2d0294943958af9c5fe561cc3805f0ba558eb5` |
| `revit/lab/revitcortex/LAB_RC_DOC.0001.rvt` | `15e0f70df13a9ad0635a7651b3fedff59e76dcfe582c25a7ea759a4b0698299d` |
| `revit/lab/revitcortex/LAB_RC_DOC.rvt` | `8820c791781f7f411aad5d3c8d044257a9130933fab86e0d19fe18383d2059ba` |

## Limitações e retomada

Os quatro casos `SKIPPED_NEEDS_REVIT` continuam dependendo de fixture nova,
provider real, consulta independente e, quando aplicável, save/close/reopen.
O drill não promove provider, não atualiza `state/capabilities.yaml` e não
prova uma instalação real. A pasta de experimento e sua falha intencional ficam
preservadas para inspeção; qualquer uso posterior deve continuar fora da raiz
de deployment.
