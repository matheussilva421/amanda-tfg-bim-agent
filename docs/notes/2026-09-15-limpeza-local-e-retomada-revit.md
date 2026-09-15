# Handoff — limpeza da pasta local e retomada do Revit

Data: 2026-09-15 (turno 31). Orquestrador Codex.

## 1. Pedido do dono

«Lembre-se de apagar o que não é mais necessário na pasta local» e «vc não está
usando mais o revit?». As duas coisas são tratadas aqui: a limpeza fica
registrada e auditável, e o Revit volta a ser o caminho de produção ativo.

## 2. Inventário antes da limpeza (medido, não estimado)

| Área | Tamanho | Situação |
|---|---|---|
| `.tmp-*` (806 itens, 333 diretórios) | 13.448 MB | scratch: probes, basetemps de pytest, raízes de drill isoladas, logs |
| `.venv-lockcheck` | 419 MB | ambiente só de verificação, reconstruível do lock rastreado |
| `__pycache__` fora das venvs/vendor | 35 diretórios | bytecode derivado |
| `.mypy_cache`, `.pytest_cache`, `.ruff_cache` | ~21 MB | caches de ferramenta |
| `.dotnet` | 770 MB | **mantido**: SDK isolado que publica/deploya horizontes C# |
| `.venv`, `.venv-topologic`, `.venv-environmental` | 1.269 MB | **mantido**: `.venv-topologic` é exigido por `tests/unit/test_topologic_spike.py` |
| `tool-lab/environmental/wheels` | 156 MB | **mantido**: wheelhouse hasheado, evidência de P04-T21 |
| `vendor/horizun-revit-mcp`, `vendor/RevitCortex` | 354 MB | **mantido**: fontes vendorizadas com pins (P02-T10/T13) |
| `revit/lab/**` | 88 MB | **mantido**: checkpoints e baseline de P02 |

Nada do que foi apagado é rastreado pelo Git: o `git status` era vazio antes da
limpeza e nenhum `git ls-files` corresponde a `.tmp-*`.

## 3. Script de limpeza

`scripts/cleanup-local.ps1` (rastreado). Só apaga o que já está no
`.gitignore` e é reproduzível; recusa rodar se existir qualquer arquivo
rastreado casando `.tmp-*`, recusa alvos fora da raiz do repositório, e é
dry-run por padrão.

```powershell
pwsh -File scripts/cleanup-local.ps1                       # plano
pwsh -File scripts/cleanup-local.ps1 -Apply -IncludeLockcheckEnv
```

`-IncludeLockcheckEnv` é opt-in porque o ambiente de lockcheck é o artefato de
uma verificação declarada; o lock rastreado reconstrói o ambiente.

## 4. Helpers promovidos de scratch para o repositório

Antes da limpeza, os drivers reais foram promovidos (conteúdo idêntico):

- `.tmp-hz.py` → `tool-lab/horizun/hz_call.py`
- `.tmp-hzpy.py` → `tool-lab/horizun/hz_execute_python.py`
- `.tmp-t16-run.ps1` → `tool-lab/custom-api/runners/t16-create-wall.ps1`
- `.tmp-t18-crash-run.ps1` → `tool-lab/custom-api/runners/t18-crash-run.ps1`
- `.tmp-t18-recovery.ps1` → `tool-lab/custom-api/runners/t18-recovery.ps1`
- `.tmp-t18-checkpoint.py` → `tool-lab/custom-api/runners/t18-checkpoint.py`
- `.tmp-t16-click.ps1` → `tool-lab/custom-api/runners/revit-dialog-click.ps1`

Os runners continuam gravando artefatos transitórios em `.tmp-*` (job do host,
log, evidência), que a limpeza pode remover sem perda.

## 5. Retomada do Revit

O Revit não está em execução agora (verificado por `Get-Process`). O add-in
Horizun está instalado com `permission_profile: full_write` e
`execute_python_ui_granted: true`, e o único provider com ciclo de documento
completo é o `horizun` (`horizun_document_session` open/save/save_as/close).

A próxima tarefa READY que exige Revit vivo é **P06-T14** (drill sintético
R14→R16). O plano pede: QA completa sobre o modelo R13 do Plan 05, salvar o RC
provisório, hash, fechar o Revit, reiniciar frio, reabrir, reconectar o
provider, refazer a QA crítica, exportar IFC/PDF/DWG, gerar manifesto e
promover o GOLDEN R16 com tentativa de sobrescrita rejeitada.

Estado honesto do pipeline hoje: existe E2E sintético verde com invoker falso
(`tests/integration/test_bim_synthetic_compile.py`), mas nenhum caminho de
execução liga o compilador R01→R13 ao provider real do Revit. Construir esse
bridge é trabalho de código deste turno, não uma premissa.

## 6. Pendências

- Bridge de execução real (compilador → Horizun) antes do drill P06-T14.
- P08-T05 sem bloqueio de Revit (design run determinístico).
- P07-T17 e P07-T19 continuam SUSPENDED: exigem sessão Codex nova real e reboot
  real, respectivamente.
