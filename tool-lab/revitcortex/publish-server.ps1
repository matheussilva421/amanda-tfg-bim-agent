# Publish the audited RevitCortex MCP server into one isolated directory and
# record a manifest that resolves the executable by verification instead of by
# "newest exe in the tree".
#
# The plan (P02-T13) requires exactly this: publish to one isolated output
# directory, resolve the executable from that publish manifest, verify framework,
# version and hash, and fail on ambiguity rather than picking whichever binary
# happens to be newest.
$ErrorActionPreference = 'Stop'

$RepoRoot   = (Resolve-Path (Join-Path $PSScriptRoot '..\..\vendor\RevitCortex')).Path
$DotnetRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\.dotnet')).Path
$OutDir     = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path + '\vendor\RevitCortex\publish\server'
$ManifestPath = Join-Path $PSScriptRoot 'server-publish-manifest.json'

$env:DOTNET_ROOT = $DotnetRoot
$env:PATH = "$DotnetRoot;$env:PATH"
$env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
$dotnet = Join-Path $DotnetRoot 'dotnet.exe'

if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }

Write-Host 'Publishing self-contained server (Release, win-x64)...'
& $dotnet publish "$RepoRoot\src\RevitCortex.Server\RevitCortex.Server.csproj" -c Release -o $OutDir --self-contained true -r win-x64 -v quiet 2>&1 | Select-Object -Last 8
if ($LASTEXITCODE -ne 0) { throw 'Server publish failed' }

# Resolve the executable by manifest. Ambiguity is a hard failure: if the
# publish produced anything other than exactly one RevitCortex.Server.exe, the
# recorded path would be a guess and every later step inherits that guess.
$exes = @(Get-ChildItem -Path $OutDir -Filter 'RevitCortex.Server.exe' -Recurse -File)
if ($exes.Count -ne 1) {
    throw "Expected exactly one RevitCortex.Server.exe under $OutDir, found $($exes.Count). Refusing to guess."
}
$exe = $exes[0]

$runtimeConfig = Join-Path $OutDir 'RevitCortex.Server.runtimeconfig.json'
if (-not (Test-Path $runtimeConfig)) { throw "runtimeconfig.json missing: $runtimeConfig" }
$rc = Get-Content -Raw $runtimeConfig | ConvertFrom-Json

$manifest = [ordered]@{
    captured_utc          = (Get-Date).ToUniversalTime().ToString('o')
    project               = 'src/RevitCortex.Server/RevitCortex.Server.csproj'
    configuration         = 'Release'
    runtime_identifier    = 'win-x64'
    self_contained        = $true
    publish_dir           = $OutDir
    exe_absolute_path     = $exe.FullName
    exe_relative_path     = $exe.FullName.Substring($RepoRoot.Length).TrimStart('\')
    exe_bytes             = $exe.Length
    exe_sha256            = (Get-FileHash $exe.FullName -Algorithm SHA256).Hash
    exe_count_in_publish  = $exes.Count
    target_framework      = $rc.runtimeOptions.tfm
    runtime_frameworks    = @($rc.runtimeOptions.frameworks | ForEach-Object { "$($_.name) $($_.version)" })
    dll_count             = (Get-ChildItem "$OutDir\*.dll").Count
    file_count            = (Get-ChildItem $OutDir -Recurse -File).Count
    sdk_used              = (& $dotnet --version)
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -Path $ManifestPath -Encoding UTF8
Write-Host ''
Write-Host "exe:      $($manifest.exe_absolute_path)"
Write-Host "bytes:    $($manifest.exe_bytes)"
Write-Host "sha256:   $($manifest.exe_sha256)"
Write-Host "tfm:      $($manifest.target_framework)"
Write-Host "dlls:     $($manifest.dll_count)"
Write-Host "manifest: $ManifestPath"

