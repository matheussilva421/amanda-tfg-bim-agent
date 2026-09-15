# Handoff — incidente do add-in de laboratorio e abertura da Fase 05

Data: 2026-09-15 (America/Fortaleza). Autor: sessao principal.

## 1. Incidente do add-in de laboratorio (ler antes de rodar qualquer Revit)

Ao preparar o P02-T16, um add-in proprio (`Amanda.ToolLab.Host`) foi registrado em
`%APPDATA%\Autodesk\Revit\Addins\2027\Amanda.ToolLab.Host.addin`. Essa pasta e
compartilhada por usuario: o add-in carrega em **todas** as instancias do Revit,
inclusive a sessao pessoal do dono. O host executou o job e postou `ExitRevit`,
fechando a sessao do dono (pid 39140).

`journal.0007.txt` registra `<-desktop ExitNativeInstance` as 14:58:07.

**Dano apurado: nenhum documento real foi perdido.** O `LAB_RC_DOC.rvt` havia
sido salvo as 14:48 (4.415.488 B) e o documento aberto pelo dono era a fixture
de laboratorio.

Correcoes aplicadas no codigo do host (compiladas, runtime ainda por revalidar):

1. `TryExitRevit()` deixou de postar `ExitRevit`.
2. `OwnershipGuard.Check` com tres gates: PID esperado igual a
   `Environment.ProcessId`; token de lancamento `AMANDA_LAB_HOST_TOKEN` presente
   no ambiente do processo e igual ao do job; documento ativo igual ao `work_rvt`
   descartavel.
3. Stand-down inerte: nao escreve resultado e nao altera estado do Revit.
4. `CreateLabWall.cs` chama `document.Regenerate()` dentro da transacao antes de
   reler o bounding box (sem isso o teste falhava com "has no bounding box to
   verify").

Regras obrigatorias para a proxima execucao: tirar o `.addin` da pasta
compartilhada fora da janela de execucao; injetar o token no ambiente do processo
iniciado e no job; provar `StartTime` antes de qualquer `Stop-Process`; matar
somente o PID que o proprio runner iniciou.

## 2. Tarefas fechadas neste bloco (com evidencia registrada no grafo)

| Task | Status | Evidencia principal |
| --- | --- | --- |
| P04-T21 | PASS | `.venv-environmental` com 34 wheels hasheados, `pip check` exit 0, EnergyPlus 24.1.0-9d7789a3ac com dois runs semanticamente identicos; Radiance fica `UNTESTED` |
| P04-T22 | PASS | `tests/unit/test_design_cli.py` 3 passed; 370 unit, 369 passed, 1 skip |
| P02-T20 | PASS (unready) | `tests/unit/test_tool_lab_cli.py` 9 passed; `tool-lab status/queue/verify-registry` provados |
| P05-T01 | PASS | `tests/unit/test_revit_units.py` 5 passed (round-trip 1 m, 10 m, 1 m², 24 m²; 1 ft = 0.3048 m) |
| P05-T02 | PASS | `tests/unit/test_bim_models.py` 4 passed (17 estagios, ids logicos duplicados recusados) |

P02-T20 foi registrado com `--allow-unready` porque depende de P02-T19
(benchmark de providers), que ainda espera a cadeia viva do Revit. O benchmark
continua em execucao e sera registrado quando chegar.

Suites de controle: `tests/unit tests/solver` = 428 passed, 1 skipped;
focados de BIM (`test_revit_units`, `test_bim_models`, `test_bim_plan`,
`test_bim_safety`, `test_checkpoints`, `test_bim_diff`,
`test_destructive_threshold`) = 43 passed.

Grafo apos este bloco: 159 tasks, PASS 81 + PASS_WITH_WARNINGS 1, PENDING 77.
PHASE_04 fechada (22/22).

## 3. Frente paralela aberta

Seis agentes LUNA XHIGH em paralelo, com write sets disjuntos:

- Hephaestus: cadeia Revit/Tool Lab (P02-T16, close/reopen do P02-T15, P02-T18).
- Tyrion: P05-T07..T11 (plano, write-read-verify, R01/R02 conferidos, R03).
- Athena: P05-T03..T06 (Safety Sentinel, checkpoints, diff, limiar destrutivo).
- Daenerys: P05-T13..T16 (casca, layout, aberturas, ambientes).
- Artemis: P05-T17..T21 (acessibilidade, mobiliario, paisagismo, materiais, documentacao).
- Arya: perfis de programa com citacoes, `bim/external.py`, CLI `bim` (P05-T22) e pipe sintetico (P05-T23).

## 4. Ajuste de repositorio

`.gitignore` passou a ignorar `tool-lab/**/.venv*/` e `wheels/`, porque o
wheelhouse do ambiente opcional tem 156 MB e e reproduzivel pelo lock hasheado
(os wheels continuam no disco, apenas fora do Git).

## 5. Pendencias e retomada

- T16 depende de revalidar o host em runtime com o ownership guard.
- T15 precisa do ciclo close/reopen do `LAB_HORIZON_DOC` para fechar como PASS.
- T18 (crash/recovery) usa o mesmo host como prova de propriedade.
- Restam no working tree artefatos por commitar de `tool-lab/**`, `state/*`,
  `src/amanda_agent/{cli.py,commands/*}`, `tests/unit/test_{tool_lab,design}_cli.py`.
- Rollback do registry de assinatura quando o lab fechar: remover os dois valores
  DWORD proprios em `HKCU\Software\Autodesk\Revit\Autodesk Revit 2027\CodeSigning`.
