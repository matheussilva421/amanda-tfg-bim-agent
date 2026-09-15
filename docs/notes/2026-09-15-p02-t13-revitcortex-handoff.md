# Handoff — P02-T13 RevitCortex (clone/audit/build/deploy)

## Estado em uma linha

O RevitCortex está clonado no commit pinado `8b2556d`, auditado, compilado, publicado e
instalado em escopo de usuário, e registrado no Codex como servidor MCP `revitcortex`
(288 ferramentas, servidor 2.0.0). Falta apenas o **restart do Revit** para o add-in carregar
pela primeira vez e o `Cortex Switch` ser ligado — isso é o P02-T14.

## Por que o Revit não foi fechado

O plano de T13 começa com "Feche o Revit normalmente". O Revit está aberto (pid 39140, iniciado
11:17:44) com o laboratório Horizun. Fechá-lo exigiria coordenar com o dono e, mais importante,
**não era necessário**: o add-in nunca havia sido carregado nesse processo, então nenhum arquivo
de destino estava travado. O único motivo real do pre-flight é evitar substituir DLL carregada.
A decisão está registrada no cabeçalho do script de deploy.

## Arquivos

| arquivo | papel |
|---|---|
| `tool-lab/revitcortex/source-audit.md` | relatório de auditoria (11262 B) |
| `tool-lab/revitcortex/deploy-revitcortex-2027.ps1` | deploy user-scope reprodutível (SDK isolado) |
| `tool-lab/revitcortex/publish-server.ps1` | publica o servidor e grava o manifesto; falha em ambiguidade |
| `tool-lab/revitcortex/server-publish-manifest.json` | hash, bytes, tfm e caminho do exe |
| `tool-lab/revitcortex/tool-catalog.json` | catálogo bruto do `tools/list`, 288 ferramentas |
| `tool-lab/revitcortex/evidence/codesigning-backup.json` | estado do trust antes de qualquer mudança |
| `tool-lab/revitcortex/evidence/codex-config.toml.snapshot` | snapshot do config global (sem segredos) |

## Decisões

1. **Escopo de usuário, não de máquina.** `C:\ProgramData\Autodesk\Revit\Addins` não existe e
   `IsInRole(Administrator)` é `False`. O vendor já traz `deploy-userscope.ps1` exatamente para isso.
2. **SDK isolado.** O SDK global é 8.0.422, e o plugin `Release R27` targeta `net10.0-windows7.0`
   (o Revit 2027 roda em .NET 10). Instalei o SDK 10.0.401 em `.dotnet/` (gitignored), sem tocar
   no SDK da máquina.
3. **Exe resolvido por manifesto, não por "mais novo".** O script lança se a publicação não
   contiver exatamente um `RevitCortex.Server.exe`.
4. **`EnableCodeExecution` fica `false`.** É o portão do `send_code_to_revit` (executa C# dentro do
   Revit). Default já é false e assim permanece por decisão de projeto.
5. **Read-only mode não foi ligado.** Existe e seria o freio mais rápido, mas o plano precisa de
   escrita. Fica documentado como alavanca de emergência.
6. **Trust de assinatura NÃO foi escrito.** O add-in é `NotSigned`; o Revit vai mostrar o diálogo
   Security no próximo start. Pré-registrar `A1B2C3D4-...-EF1234567890 = 1` é ação do dono, e o
   backup em `codesigning-backup.json` deixa qualquer escolha reversível.

## Testes e verificações

| verificação | resultado |
|---|---|
| `dotnet build -c Release` (servidor) | 0 avisos, 0 erros |
| `dotnet build -c "Release R27"` (plugin) | 0 erros, 5 avisos preexistentes do vendor |
| deploy | `OK R27 -> ...\Addins\2027\RevitCortex (19 DLLs)`, 76 arquivos |
| handshake MCP contra o exe publicado | servidor `RevitCortex 2.0.0`, protocolo `2024-11-05`, **288 tools** |
| `codex mcp list` | `revitcortex` **enabled** no caminho exato |
| varredura de segredos no snapshot | sem `sk-`, `ghp_`, `ghs_`, `Bearer`, `eyJ` |

Hash do plugin instalado: `E01135D08A2EBCB13A8DBBCD2914E3E51637B5825A802008A59F2BE7E6C325F9`.
Hash do servidor publicado: `958B4B6703D7A1EF3B093CEFE22FB3C11D192D443178D77486A5462ECE8CA671`.

## Divergências registradas

- **173 (README) vs 288 (binário).** O mapa de ferramentas de T14 tem de sair do catálogo, não da doc.
- **Release sem gating de licença.** `LicenseBootstrap.cs` resolve `Gate = null` em Release; é
  comportamento upstream em `8b2556d`, não algo que configuramos.

## Rollback

1. Fechar Revit e o cliente MCP.
2. Remover `%APPDATA%\Autodesk\Revit\Addins\2027\RevitCortex.addin` e a pasta `RevitCortex\`.
3. `codex mcp remove revitcortex`.
4. `%USERPROFILE%\.revitcortex\` e um eventual valor em `CodeSigning` são independentes do add-in.

## Próximo passo

**P02-T14.** Requer, como ação do dono, fechar e reabrir o Revit (o add-in carrega no start e o
diálogo Security aparece porque o add-in não é assinado), e então ligar o `Cortex Switch` na fita
`RevitCortex`. Depois disso o T14 é meu: confirmar bridge localhost-only, confirmar `/mcp`,
gerar `revitcortex-toolmap.yaml` do catálogo real, validar sem placeholders e registrar porta,
settings e logs.
