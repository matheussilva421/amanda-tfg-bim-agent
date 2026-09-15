#requires -Version 5.1
<#
    Read-only Revit inventory. Inspects installed files and their version
    resources; never launches Revit and never modifies Autodesk state.

    Usage: powershell -ExecutionPolicy Bypass -File .\bootstrap\get-revit-metadata.ps1
#>
[CmdletBinding()]
param(
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scriptDir

if (-not $OutputPath) {
    $OutputPath = Join-Path $root 'state\revit-metadata.json'
}

function Get-Metadata([string]$exePath) {
    $v = (Get-Item -LiteralPath $exePath).VersionInfo
    [pscustomobject]@{
        productName    = $v.ProductName
        productVersion = $v.ProductVersion
        fileVersion    = $v.FileVersion
        companyName    = $v.CompanyName
        legalCopyright = $v.LegalCopyright
    }
}

$searchRoots = @()
foreach ($envName in @('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)')) {
    $base = [System.Environment]::GetEnvironmentVariable($envName)
    if ($base) { $searchRoots += (Join-Path $base 'Autodesk') }
}
$searchRoots = $searchRoots | Select-Object -Unique

$installations = New-Object System.Collections.Generic.List[object]
$notes = New-Object System.Collections.Generic.List[string]

foreach ($searchRoot in $searchRoots) {
    if (-not (Test-Path -LiteralPath $searchRoot -PathType Container)) { continue }
    Get-ChildItem -LiteralPath $searchRoot -Directory -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like 'Revit 20*' } |
        Sort-Object Name |
        ForEach-Object {
            $exe = Join-Path $_.FullName 'Revit.exe'
            $api = Join-Path $_.FullName 'RevitAPI.dll'
            if (-not ((Test-Path -LiteralPath $exe -PathType Leaf) -and (Test-Path -LiteralPath $api -PathType Leaf))) {
                $notes.Add(('incomplete installation at {0}' -f $_.FullName)) | Out-Null
                return
            }
            $meta = Get-Metadata $exe
            $digits = ($_.Name -replace '[^0-9]', '')
            $installations.Add([pscustomobject]@{
                productName    = $meta.productName
                productVersion = $meta.productVersion
                fileVersion    = $meta.fileVersion
                companyName    = $meta.companyName
                legalCopyright = $meta.legalCopyright
                installPath    = $_.FullName
                executablePath = $exe
                apiPath        = $api
                year           = if ($digits.Length -eq 4) { [int]$digits } else { $null }
            }) | Out-Null
        }
}

$report = [pscustomobject]@{
    schema_version     = 1
    generated_utc      = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    generator          = 'bootstrap/get-revit-metadata.ps1'
    machine            = $env:COMPUTERNAME
    searched_roots     = $searchRoots
    probe_status       = if ($installations.Count -gt 0) { 'DETECTED' } else { 'NOT_FOUND' }
    installation_count = $installations.Count
    ambiguous          = ($installations.Count -gt 1)
    installations      = $installations
    notes              = $notes
    scope              = 'read-only inventory; installed files do not prove licensing or a successful launch'
}

$outDir = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding UTF8

Write-Output ('revit inventory: {0} installation(s) -> {1}' -f $installations.Count, $OutputPath)
foreach ($note in $notes) { Write-Output ('note: ' + $note) }
