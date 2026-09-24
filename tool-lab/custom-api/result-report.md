# P02-T16 — relatório final do fallback C#

## Veredito

`PASS_WITH_WARNINGS`: a prova de runtime passou em um Revit 2027 iniciado pelo
runner, com criação, reconsulta, geometria, save, close, reopen e reconsulta
pós-reabertura comprovados. O único aviso é a resolução conhecida de
`Microsoft.VisualBasic` (`MSB3277`) no SDK local: 3 avisos no projeto do
comando e 6 no host, sem erros C# e sem efeito observado no runtime.

O provider comprovado é
`transport_provider=custom_csharp_external_command`. A capability
`custom_csharp:create_wall` pode ser considerada elegível pelo gate de runtime;
este relatório não altera `state/*` nem o registro durável.

## Incidente anterior e correções verificadas

No ensaio anterior do P02-T16, `Amanda.ToolLab.Host.addin` estava na pasta de
add-ins compartilhada do usuário. O host postou `ExitRevit` e fechou a sessão
do proprietário; o journal `journal.0007.txt` registra
`<-desktop ExitNativeInstance` às 14:58:07. Nenhum documento real foi perdido.

O runtime atual verificou estas barreiras:

- `TryExitRevit()` não posta `ExitRevit`; o runner encerra somente o PID que
  ele iniciou, depois de comparar `StartTime`.
- `OwnershipGuard.Check` exige `job.ExpectedPid == Environment.ProcessId`, o
  token `AMANDA_LAB_HOST_TOKEN` igual ao `env_token` do job e o documento ativo
  com caminho exato igual a `work_rvt`.
- Stand-down não grava resultado nem altera o Revit.
- `CreateLabWall` chama `document.Regenerate()` dentro da transação antes de
  reler `get_BoundingBox(null)`; sem isso o ensaio falhava com
  `has no bounding box to verify`.
- `LabHostFiles.JobPath` lê `AMANDA_LAB_HOST_JOB`, com fallback apenas para o
  arquivo legado ao lado da assembly. O runner grava o job por execução e
  herda o token antes do `Start-Process`.
- Para fechar um documento, o host ativa o standby descartável
  `LAB_R00_EMPTY.rvt`; a API do Revit rejeita o fechamento do documento ativo.

## Implementação

- `CreateLabWall.cs`: comando independente dos bridges Horizun e RevitCortex;
  procura `Level 1`, um `WallType` básico, converte 5 m e 3 m, cria uma parede
  em transação, regenera, relê por `ElementId.Value` e valida bounding box.
- `host/LabHostApp.cs`: host externo, guard de propriedade, job por ambiente,
  reconsulta independente e ciclo seguro de standby/close/reopen.
- `CreateLabWall.csproj` e `host/Amanda.ToolLab.Host.csproj`: referências
  diretas às DLLs verificadas do Revit 2027, sem pacote NuGet da API.
- `test_custom_api_contract.py`: contratos offline para a API, ownership,
  job por execução e close/reopen seguro.
- `.tmp-t16-run.ps1`: runner com isolamento/restauração de add-ins, reset do
  RVT descartável, hashes, PID/StartTime, token, transcript e cópia do journal.

## Evidência final do runtime

| Gate | Resultado | Evidência |
|---|---|---|
| Revit | `PASS` | `Revit.exe` 2027, build `20260716_1515(x64)`, PID próprio `37224`, StartTime `2026-09-15T15:34:52.8062412-03:00` |
| Ownership | `PASS` | PID, StartTime, token herdado e `work_rvt` exato aceitos pelo host |
| Pré-requisitos | `PASS` | `LAB_CUSTOM_WALL`, projeto, `Level 1` e WallType básico |
| Criação | `PASS` | `ElementId.Value=328658`, `command_result=Succeeded`, uma parede nova |
| Reconsulta em sessão | `PASS` | `in_session`, comprimento `5 m`, altura `3 m`, nível `Level 1` |
| Save | `PASS` | `save_ms=384`; RVT final com 4.370.432 bytes |
| Close | `PASS` | standby ativado; `close-document` em `122 ms` |
| Reopen | `PASS` | `reopen-document` em `1917 ms` |
| Persistência | `PASS` | mesmo `ElementId.Value=328658`, 5 m × 3 m após reopen |
| Close final | `PASS` | standby ativado; work file fechado em `96 ms` |
| Resultado host | `PASS` | `total_ms=5702`, `outcome=PASS` |

As duas verificações registradas no resultado são:

```text
in_session:  ElementId.Value=328658, length_m=5, height_m=3, geometry_matches_contract=true
after_reopen: ElementId.Value=328658, length_m=5, height_m=3, geometry_matches_contract=true
```

## Hashes

- Baseline `revit/lab/baseline/LAB_R00_EMPTY.rvt` antes/depois:
  `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D`;
  `4.366.336` bytes; intacto.
- `revit/lab/custom-api/LAB_CUSTOM_WALL.rvt` após o runtime:
  `8CCAB171E89FA4AC414F9CA3C57B5C4161CD7EE6DD61F45F86529703EE281CB2`;
  `4.370.432` bytes.
- `Amanda.ToolLab.CustomApi.dll`:
  `AA77B3B6F641E11C6E503FDEB98662C3A4EA29CE817C46DCBEA0FCE2EBC5B164`.
- `Amanda.ToolLab.Host.dll`:
  `41C56335A07327C398A5B6213D2F4D636B3B18C3F9D2BD03D93888D4379A64A4`.
- `t16-host-create.json`:
  `8CD174F15826303FFE3274F4BAC94720AA75126A23A6E99F81101E729685A0FA`.
- `t16-run-log.txt`:
  `F22FEA3F43EABF665A913F7C8CDB3CEACE8D9A1A5CEC17B3761D5DDDA6E115C1`.
- Journal copiado `t16-host-revit-journal.txt` (`journal.0011.txt`):
  `FD63E30BBE75EA68442E17EEFA4C8012BA41B226E4AF8FC1B97BDC8B9BB3A9BC`;
  `542.559` bytes.
- Add-ins restaurados com hash igual ao início:
  `Amanda.ToolLab.Host.addin` `31B656141502BF1388A039F23B412FF236628870B701B0F657C78FD6FC7B64F6`;
  `Horizun.addin` `BAEAE873B9735067BCEE515D78E98E9F78D66705D202B1BFF34120D391B93B91`;
  `RevitCortex.addin` `C9E81E87D046E6D0A4F1BC71C7F2F56E775C32EDE78FFCDDA3CAF7F22A4AD94C`.

## Testes e comandos

- RED do novo contrato: `pytest tool-lab/custom-api/test_custom_api_contract.py -q`
  → `1 failed, 1 passed`; faltava `AMANDA_LAB_HOST_JOB`.
- RED do close/reopen: mesmo teste → `1 failed, 2 passed`; Revit rejeitava
  `Document.Close` ativo e depois o host lia `Title` de objeto inválido.
- GREEN final: `pytest tool-lab/custom-api/test_custom_api_contract.py -q`
  → `3 passed, 0 failed`.
- Parser: `[System.Management.Automation.Language.Parser]::ParseFile(...)`
  → `PowerShell parse: PASS`.
- Build comando: `.dotnet\dotnet.exe build tool-lab\custom-api\CreateLabWall.csproj -c Release --nologo`
  → exit 0, 0 erros, 3 avisos `MSB3277`.
- Build host: `.dotnet\dotnet.exe build tool-lab\custom-api\host\Amanda.ToolLab.Host.csproj -c Release --nologo`
  → exit 0, 0 erros, 6 avisos `MSB3277`.
- Runtime: `& .\.tmp-t16-run.ps1` → exit 0; resultado host `outcome=PASS`.

## Arquivos de evidência

- `results/t16-host-create.json`
- `results/t16-run-log.txt`
- `results/t16-host-revit-journal.txt`

Os arquivos `*.before-20260915-*` preservam os artefatos das tentativas
anteriores e não são usados como resultado final.

## Próximo passo

Não registrar este resultado em `state/*` neste bloco. O orquestrador deve
consumir este relatório para atualizar P02-T16. O close/reopen do P02-T15 foi
executado separadamente e está documentado em
`tool-lab/revitcortex/results/t15-close-reopen-evidence.md`; o drill P02-T18 está em
`tool-lab/custom-api/results/t18-drill-report.md`.
