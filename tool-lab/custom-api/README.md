# P02-T16 — Custom C# Revit API fallback

Este diretório contém um `IExternalCommand` independente dos bridges Horizun e
RevitCortex. O comando procura exatamente o nível `Level 1`, procura um
`WallType` básico, converte 5 m e 3 m com `UnitUtils.ConvertToInternalUnits`, e
cria uma única parede dentro de uma `Transaction`. Antes do commit ele relê a
parede pelo `ElementId`, usa `element.get_BoundingBox(null)` e verifica o
comprimento/altura. Qualquer pré-requisito ausente ou falha cancela a transação
e retorna `Result.Failed`.

O código usa `ElementId.Value`, compatível com a API do Revit 2027. O projeto
não referencia pacotes NuGet da API: o `.csproj` aponta diretamente para as
DLLs instaladas no caminho real `C:\Program Files\Autodesk\Revit 2027\`.

## Compilar

Feche o Revit antes de compilar ou registrar o add-in. A compilação usa o SDK
local do projeto, sem instalar ou reinstalar o Revit:

```powershell
$env:DOTNET_ROOT = (Resolve-Path '.\.dotnet').Path
& '.\.dotnet\dotnet.exe' build '.\tool-lab\custom-api\CreateLabWall.csproj' -c Release --nologo
```

O resultado esperado é
`tool-lab\custom-api\bin\Release\net10.0-windows7.0\Amanda.ToolLab.CustomApi.dll`.
Para uma instalação em outro caminho, somente se ela tiver sido verificada,
use `-p:RevitInstallPath='C:\caminho\Revit 2027'`; não adivinhe uma DLL.

## Registrar o `.addin`

Com o Revit fechado, crie o arquivo de usuário
`%APPDATA%\Autodesk\Revit\Addins\2027\Amanda.ToolLab.CustomApi.addin` com
o conteúdo abaixo. Substitua `Assembly` pelo caminho absoluto verificado da
DLL compilada. O `AddInId` é apenas a identidade deste comando de laboratório;
use outra identidade se já existir uma igual no perfil.

```xml
<?xml version="1.0" encoding="utf-8" standalone="no"?>
<RevitAddIns>
  <AddIn Type="Command">
    <Name>Amanda P02-T16 Custom API fallback</Name>
    <Assembly>C:\Users\slvma\Downloads\Github\Projeto Amanda\tool-lab\custom-api\bin\Release\net10.0-windows7.0\Amanda.ToolLab.CustomApi.dll</Assembly>
    <AddInId>5C4F2F28-CEB0-4B84-9EA5-15B6172A8C55</AddInId>
    <FullClassName>Amanda.ToolLab.CustomApi.CreateLabWall</FullClassName>
    <Text>Create lab wall (P02-T16)</Text>
    <Description>Independent Revit API fallback proof for one disposable lab wall.</Description>
    <VendorId>AMANDA</VendorId>
    <VendorDescription>Amanda TFG BIM Agent tool lab</VendorDescription>
  </AddIn>
</RevitAddIns>
```

Abra somente um arquivo RVT descartável, confirme que ele contém um nível
chamado `Level 1` e um tipo de parede básico, e execute **Create lab wall
(P02-T16)** na aba **Add-Ins**. Observe a mensagem do comando e o journal para
o `ElementId.Value` retornado. Não use um modelo Amanda, GOLDEN, MASTER ou
fonte original.

## Gate de runtime executado

O host independente `Amanda.ToolLab.Host` executou o comando em 15/09/2026
contra `revit/lab/custom-api/LAB_CUSTOM_WALL.rvt`, com o processo Revit
iniciado pelo runner e com `AMANDA_LAB_HOST_TOKEN` e
`AMANDA_LAB_HOST_JOB` herdados pelo filho. O runner reteve `Horizun.addin` e
`RevitCortex.addin`, recolocou apenas o host durante a execução e verificou os
hashes ao restaurar os três arquivos.

O host usa `revit/lab/baseline/LAB_R00_EMPTY.rvt` como standby porque a API do
Revit não permite fechar o documento ativo. Ele ativa o standby, fecha o work
file, reabre o mesmo work file e relê o elemento antes do fechamento final.
O gate registrou:

1. `transport_provider=custom_csharp_external_command`;
2. `ElementId.Value` observado no Revit/journal;
3. reconsulta independente do elemento e verificação do bounding box;
4. salvar, fechar e reabrir o mesmo arquivo descartável;
5. confirmação de que a parede persiste, com 5 m de comprimento e 3 m de altura.

6. `ElementId.Value=328658` relido após a reabertura, com 5 m × 3 m;
7. `transport_provider=custom_csharp_external_command` no relatório do gate.

O resultado está em `results/t16-host-create.json`, o transcript em
`results/t16-run-log.txt` e o journal copiado em
`results/t16-host-revit-journal.txt`. Python fora do Revit não invoca
mutations diretamente; ele apenas conduz o runner de laboratório.
