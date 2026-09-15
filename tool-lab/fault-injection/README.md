# P02-T17 — Fault-injection matrix

## Veredito

Status do laboratório: **PARTIAL**.

O runner foi executado em 15/09/2026 contra o alvo configurável
`synthetic-offline-horizun`. A saída real está em
`results/p02-t17-matrix-2026-09-15-final.json` e contém 8 casos: 4 `PASS` offline,
4 `SKIPPED_NEEDS_REVIT`, 0 `FAIL` e 0 `BLOCKED` no formato do runner.
Os arquivos equivalentes sem o sufixo `-final` são uma execução anterior e não
são a referência deste veredito.

Os quatro `PASS` são evidência sintética do cliente/controle local. Eles não
promovem Horizun ou RevitCortex a provider PASS no Revit. O bloqueio de
aceitação do P02-T17 continua para os casos que exigem fixture RVT descartável,
chamada real e reconsulta independente.

## Resultado por caso

| Caso | Resultado | Classe esperada | O que foi provado |
|---|---|---|---|
| FI-001 — invalid element ID | `SKIPPED_NEEDS_REVIT` | E01 | Precisa provar rejeição da entrada e ausência de mutação no provider real. |
| FI-002 — nonexistent family/type | `SKIPPED_NEEDS_REVIT` | E01 | Precisa provar ausência de mutação por consulta/hash independente. |
| FI-003 — hosted element without host | `SKIPPED_NEEDS_REVIT` | E04; E05 se houver vazamento | Precisa provar transação recusada/revertida e ausência de órfão. |
| FI-004 — MCP disabled/disconnected | `PASS` (`SYNTHETIC_OFFLINE`) | E02 | O alvo sintético recusou a chamada sem falso sucesso. |
| FI-005 — Revit closed | `PASS` (`SYNTHETIC_OFFLINE`) | E02 | O alvo sintético retornou provider unavailable sem falso sucesso. |
| FI-006 — invalid batch item after valid items | `SKIPPED_NEEDS_REVIT` | E04; E05 se houver persistência parcial | Precisa comparar contagem/IDs antes e depois em cada provider. |
| FI-007 — repeated equivalent failure ×3 | `PASS` (`PROJECT_CODE_OFFLINE`) | E02 | O `CircuitBreaker` real abriu `OPEN` na terceira falha equivalente e bloqueou a chamada ordinária seguinte. |
| FI-008 — timeout on long read | `PASS` (`SYNTHETIC_OFFLINE`) | E03 | O runner observou timeout, verificou antes de retry e não repetiu enquanto o estado estava `IN_DOUBT`. |

O campo `summary.blocked` vale zero porque o runner representa a dependência de
Revit como `SKIPPED_NEEDS_REVIT`. Em termos de gate do plano, FI-001, FI-002,
FI-003 e FI-006 estão **BLOCKED** até existir Revit aberto com uma cópia nova
da fixture e um operador humano para confirmar o fluxo. Nenhuma chamada Revit
foi automatizada nesta execução.

## Runner

O runner aceita `--matrix`, `--results`, `--target`, `--target-config` e
`--breaker-state`. `--target` identifica o alvo no JSON; o adaptador fornecido
é deliberadamente offline. Um JSON de configuração pode substituir o nome do
provider/build, limiar do breaker, timeout e o estado retornado pela verificação
de timeout.

Execução usada:

```powershell
$env:PYTHONIOENCODING='utf-8'
& './.venv/Scripts/python.exe' 'tool-lab/fault-injection/run_matrix.py' `
  --target 'synthetic-offline-horizun' `
  --results 'tool-lab/fault-injection/results/p02-t17-matrix-2026-09-15-final.json' `
  --breaker-state 'tool-lab/fault-injection/results/p02-t17-breaker-2026-09-15-final.yaml'
```

Saída observada:

```text
total: 8
pass: 4
fail: 0
blocked: 0
skipped_needs_revit: 4
```

O arquivo `results/p02-t17-breaker-2026-09-15-final.yaml` é a persistência real do
caso FI-007: `failure_count: 3` e `state: OPEN`.

## Investigação do breaker, retry e timeout

### Amanda (`src/amanda_agent`)

Existe um breaker persistente real em
`src/amanda_agent/tools/circuit_breaker.py`:

- `CircuitState` implementa `CLOSED`, `OPEN` e `HALF_OPEN`.
- O escopo é separado por provider, build Revit, capability e assinatura de
  erro; a configuração padrão abre após 3 falhas de saúde equivalentes.
- `FailureKind.INPUT` e `VALIDATION` não incrementam a saúde do provider.
- O estado é salvo em YAML por escrita temporária + `os.replace`.
- Um circuito `OPEN` só pode ir para `HALF_OPEN` por probe explicitamente
  somente-leitura após cooldown/remediação; o fechamento exige sucesso
  independente.

O controlador complementar em `src/amanda_agent/state/budgets.py` limita
retries de leitura, exige prova explícita de ausência de mutação para retry de
mutação, detecta três assinaturas equivalentes e leva timeout duro à
`RECONCILIATION`. Ele não substitui o breaker de saúde do provider.

O FI-007 prova diretamente o breaker de Amanda em isolamento. O FI-008 prova
somente a ordem do protocolo offline do runner. A integração real ainda precisa
usar a reconciliação do modelo/provider antes de retry.

### RevitCortex (`vendor/RevitCortex`)

A busca no código de runtime não encontrou um `CircuitBreaker`, estados
`OPEN/HALF_OPEN` ou persistência equivalente no vendor. O que existe é:

- `server/src/connection/RevitClient.ts`: timeout de conexão de 5 s, timeout de
  comando de 300 s, destruição do socket no timeout e rejeição de callbacks
  pendentes em erro/fechamento.
- `server/src/connection/ConnectionManager.ts`: mutex de conexão por chamada;
  não há retry ou circuito persistente.
- `src/RevitCortex.Server/Connection/RevitBridge.cs`: conexão TCP local,
  timeout de conexão de 5 s, timeout de comando configurável (300 s padrão) e
  `TimeoutException`/erro de socket; `RevitConnectionManager` serializa com
  `SemaphoreSlim`, sem breaker.
- `src/RevitCortex.Plugin/Threading/RevitThreadDispatcher.cs`: timeout da
  espera de evento e retorno `CortexErrorCode.Timeout`, com orientação explícita
  para verificar o estado do modelo antes de retry.
- `src/RevitCortex.Plugin/Threading/ToolExecutionHandler.cs`: se a execução
  termina depois do timeout, registra
  `completed_after_timeout (result discarded; model may have changed)`; isso é
  observabilidade de estado potencialmente divergente, não um breaker.
- `src/RevitCortex.Plugin/CortexRouter.cs`: ferramenta desabilitada e documento
  ausente retornam `InvalidInput`; não há mapeamento automático disso para o E02
  do plano.
- As ferramentas de escrita usam `Transaction` e retornam
  `TransactionFailed` quando o commit falha. Alguns lotes capturam erro por
  item e continuam dentro da mesma transação; atomicidade de FI-006 não pode
  ser inferida da leitura estática e deve ser medida por provider em fixture
  nova.

Assim, por camada, o P02-T17 pode provar o seguinte:

| Camada | Prova possível agora | Limite |
|---|---|---|
| Provider Revit/Horizun/Cortex | E01/E04/E05, ausência de mutação, órfão e atomicidade | Requer Revit vivo, fixture nova, consulta independente e save/close/reopen quando aplicável. |
| Cliente MCP | E02, envelopes de erro, bloqueio do breaker Amanda e ordem verify-before-retry | O runner offline não valida o catálogo MCP nem o processo real do provider. |
| Bridge local | indisponibilidade, fechamento de socket, timeout e conclusão tardia | O código Cortex não possui breaker; timeout não prova que a operação Revit não terminou. |

## Retomada do gate humano

Para cada caso `SKIPPED_NEEDS_REVIT`, copiar
`revit/lab/baseline/LAB_R00_EMPTY.rvt` para uma fixture exclusiva, abrir a cópia
no Revit 2027, executar a ferramenta real do provider escolhido, registrar o
retorno bruto, reconsultar o modelo e comparar contagem/IDs/host/hash. No lote,
registrar explicitamente se houve rollback completo ou persistência parcial.
Fechar/reabrir a cópia quando a operação tiver escrita. Atualizar o JSON com a
evidência real e manter `PASS` sintético separado de qualquer promoção de
capability.

## Testes e estado Git

Teste focado executado:

```powershell
$env:PYTHONIOENCODING='utf-8'
& './.venv/Scripts/python.exe' -m pytest `
  'tool-lab/fault-injection/test_run_matrix.py' `
  -p no:cacheprovider `
  --basetemp='.tmp-pytest-t17-green-0915b' -q
```

Resultado: 3 testes executados, 3 aprovados, 0 falhados; status verde.

Não foram executados `git add`, `git commit`, `git push`, `checkout`, `stash` ou
`reset`, conforme a regra dura da tarefa. O agente principal deve revisar e
versionar os arquivos desta área. Nenhum arquivo fora de
`tool-lab/fault-injection/` foi alterado como artefato da tarefa; os diretórios
temporários de pytest foram criados na raiz conforme o parâmetro obrigatório
`--basetemp`.
