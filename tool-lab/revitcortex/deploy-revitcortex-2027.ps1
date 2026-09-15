# RevitCortex user-scope deploy for Revit 2027.
#
# Replicated from vendor/RevitCortex/deploy-userscope.ps1 with two deliberate
# differences, both recorded in the audit report:
#
#   1. The .NET SDK on PATH is 8.0.422, which cannot target net10.0 and fails
#      the plugin build with NETSDK1045. Revit 2027 itself runs on .NET 10, so
#      this script uses the isolated SDK installed under .dotnet/ (10.0.401)
#      instead of touching the machine-wide SDK.
#   2. The "Revit is running" pre-flight is dropped. RevitCortex is not loaded
#      into the running Revit yet, so no target file is held open. The plugin
#      still only takes effect on the next Revit start.
#
# The vendor script is the authority for what a deploy copies; this file exists
# so the exact toolchain and target are reproducible from the repository.
$ErrorActionPreference = 'Stop'

$RepoRoot     = Join-Path $PSScriptRoot '..\..\vendor\RevitCortex'
$DotnetRoot   = Join-Path $PSScriptRoot '..\..\.dotnet'
$RepoRoot     = (Resolve-Path $RepoRoot).Path
$DotnetRoot   = (Resolve-Path $DotnetRoot).Path
$Configuration = 'Release R27'
$PublishDir   = Join-Path $RepoRoot 'publish\R27'
$UserAddinsDir = Join-Path $env:APPDATA 'Autodesk\Revit\Addins\2027'
$UserTargetDir = Join-Path $UserAddinsDir 'RevitCortex'

$env:DOTNET_ROOT = $DotnetRoot
$env:PATH = "$DotnetRoot;$env:PATH"
$env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
$dotnet = Join-Path $DotnetRoot 'dotnet.exe'

if (-not (Test-Path $dotnet)) { throw "Isolated .NET SDK not found: $dotnet" }
Write-Host "SDK: $(& $dotnet --version)"
Write-Host "Config: $Configuration"
Write-Host "Target: $UserTargetDir"

if (Test-Path $PublishDir) { Remove-Item $PublishDir -Recurse -Force }

Write-Host 'Publishing Plugin...'
& $dotnet publish -c "$Configuration" "$RepoRoot\src\RevitCortex.Plugin\RevitCortex.Plugin.csproj" -o $PublishDir --no-self-contained 2>&1 | Select-Object -Last 8
if ($LASTEXITCODE -ne 0) { throw 'Plugin publish failed' }

Write-Host 'Publishing Tools...'
& $dotnet publish -c "$Configuration" "$RepoRoot\src\RevitCortex.Tools\RevitCortex.Tools.csproj" -o $PublishDir --no-self-contained 2>&1 | Select-Object -Last 8
if ($LASTEXITCODE -ne 0) { throw 'Tools publish failed' }

# Wipe + recreate so stale satellite assemblies do not survive the deploy.
if (Test-Path $UserTargetDir) { Remove-Item $UserTargetDir -Recurse -Force }
New-Item -ItemType Directory -Path $UserTargetDir -Force | Out-Null
Copy-Item "$PublishDir\*" $UserTargetDir -Recurse -Force

Copy-Item (Join-Path $RepoRoot 'src\RevitCortex.Plugin\RevitCortex.addin') $UserAddinsDir -Force

$dllCount = (Get-ChildItem "$UserTargetDir\*.dll").Count
$exe      = Get-ChildItem "$UserTargetDir\RevitCortex.Plugin.dll" -ErrorAction SilentlyContinue
Write-Host ''
Write-Host "OK R27 -> $UserTargetDir ($dllCount DLLs)"
if ($exe) { Write-Host "Plugin assembly sha256: $((Get-FileHash $exe.FullName -Algorithm SHA256).Hash)" }

