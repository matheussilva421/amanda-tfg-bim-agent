#requires -Version 5.1
<#
    Computes SHA-256 hashes and metadata for the canonical root documents and the
    private academic source bundle. Writes non-secret metadata only.

    Usage:  powershell -ExecutionPolicy Bypass -File .\bootstrap\get-source-inventory.ps1
#>
[CmdletBinding()]
param(
    [string]$Root,
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

if (-not $Root) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $Root = Split-Path -Parent $scriptDir
}

if (-not $OutputPath) {
    $OutputPath = Join-Path $Root 'project\provenance\source-inventory.json'
}

$rootFull = (Resolve-Path -LiteralPath $Root).Path

$canonical = @(
    'START_HERE_FOR_CODEX.md',
    'PLAN_SELF_REVIEW.md',
    '2026-09-11-amanda-tfg-bim-agent-design.md',
    '2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md',
    'docs/notes/2026-09-15-revisao-planos-handoff.md'
)

function Get-RelativePath([string]$basePath, [string]$fullPath) {
    $rel = $fullPath.Substring($basePath.Length).TrimStart([char]92, [char]47)
    return $rel.Replace([char]92, [char]47)
}

function New-Entry([System.IO.FileInfo]$file, [string]$basePath) {
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    [pscustomobject]@{
        path          = Get-RelativePath $basePath $file.FullName
        bytes         = $file.Length
        sha256        = $hash
        modified_utc  = $file.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')
    }
}

$entries = New-Object System.Collections.Generic.List[object]

foreach ($rel in $canonical) {
    $full = Join-Path $rootFull $rel
    if (Test-Path -LiteralPath $full -PathType Leaf) {
        $entries.Add((New-Entry (Get-Item -LiteralPath $full) $rootFull)) | Out-Null
    }
}

$academicRoot = Join-Path $rootFull 'TFG_Amanda_2026'
if (Test-Path -LiteralPath $academicRoot -PathType Container) {
    Get-ChildItem -LiteralPath $academicRoot -Recurse -File -Force |
        Sort-Object FullName |
        ForEach-Object { $entries.Add((New-Entry $_ $rootFull)) | Out-Null }
}

foreach ($extra in @('programa_necessidades.pdf')) {
    $full = Join-Path $rootFull $extra
    if (Test-Path -LiteralPath $full -PathType Leaf) {
        $entries.Add((New-Entry (Get-Item -LiteralPath $full) $rootFull)) | Out-Null
    }
}

Get-ChildItem -LiteralPath $rootFull -File -Filter 'TFG_Amanda*.pdf' |
    ForEach-Object { $entries.Add((New-Entry $_ $rootFull)) | Out-Null }

$report = [pscustomobject]@{
    schema_version   = 1
    generated_utc    = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    generator        = 'bootstrap/get-source-inventory.ps1'
    root             = $rootFull
    entry_count      = $entries.Count
    privacy          = 'metadata-and-hashes-only; no source content is copied into this report'
    entries          = $entries
}

$outDir = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Output ("source inventory: {0} entries -> {1}" -f $entries.Count, $OutputPath)
