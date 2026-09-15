<#
.SYNOPSIS
    Remove derived local state that git already ignores, with a dry-run first.

.DESCRIPTION
    Nothing removed by this script is tracked by Git or irreplaceable:

    - .tmp-* scratch (probes, pytest basetemps, isolated drill roots, logs);
    - tool caches (.mypy_cache, .pytest_cache, .ruff_cache);
    - __pycache__ bytecode outside the provisioned virtualenvs and vendors;
    - the stray System.Collections.Specialized.OrderedDictionary file left by a
      PowerShell redirection accident;
    - .venv-lockcheck, a verification-only virtualenv reproducible from
      requirements.lock.txt (see docs/superpowers/plans/04-design-engine.md).

    It never touches: .venv, .venv-topologic, .venv-environmental, .dotnet,
    vendor/, revit/lab, tool-lab results, docs, state or any tracked file.

.PARAMETER Apply
    Actually delete. Without it the script only prints the plan.

.PARAMETER IncludeLockcheckEnv
    Also remove .venv-lockcheck (419 MB, rebuildable from the tracked lock).

.EXAMPLE
    pwsh -File scripts/cleanup-local.ps1
    pwsh -File scripts/cleanup-local.ps1 -Apply -IncludeLockcheckEnv
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$IncludeLockcheckEnv
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$prefix = $root + '\'
Set-Location -LiteralPath $root

function Test-InsideRoot {
    param([string]$Path)
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if (-not $item) { return $null }
    if (-not $item.FullName.StartsWith($prefix)) {
        throw "refusing a target outside the repository root: $($item.FullName)"
    }
    return $item
}

$trackedScratch = @(git ls-files | Where-Object { $_ -match '(^|/)\.tmp-' })
if ($trackedScratch.Count -gt 0) {
    throw "tracked files exist under .tmp-*; refusing to run: $($trackedScratch -join ', ')"
}

$targets = New-Object System.Collections.Generic.List[object]
Get-ChildItem -LiteralPath $root -Force -Filter '.tmp-*' | ForEach-Object { $targets.Add($_) }

$names = @(
    'System.Collections.Specialized.OrderedDictionary',
    '.git-commit-msg.tmp',
    '.mypy_cache',
    '.pytest_cache',
    '.ruff_cache'
)
if ($IncludeLockcheckEnv) { $names += '.venv-lockcheck' }
foreach ($name in $names) {
    $item = Test-InsideRoot (Join-Path $root $name)
    if ($item) { $targets.Add($item) }
}

function Get-TargetBytes {
    param($Item)
    if ($Item.PSIsContainer) {
        $sum = (Get-ChildItem -LiteralPath $Item.FullName -Recurse -Force -File -ErrorAction SilentlyContinue |
            Measure-Object Length -Sum).Sum
        if ($null -eq $sum) { return [int64]0 }
        return [int64]$sum
    }
    return [int64]$Item.Length
}

$plan = foreach ($item in $targets) {
    [pscustomobject]@{
        Path = $item.FullName.Replace($prefix, '')
        Kind = $(if ($item.PSIsContainer) { 'dir' } else { 'file' })
        MB   = [math]::Round((Get-TargetBytes $item) / 1MB, 2)
    }
}

$pycache = @(
    Get-ChildItem -LiteralPath $root -Recurse -Force -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -notlike "$root\.venv*\*" -and
            $_.FullName -notlike "$root\vendor\*" -and
            $_.FullName -notlike "$root\.dotnet\*"
        }
)

$totalMB = [math]::Round((($plan | Measure-Object MB -Sum).Sum), 1)
Write-Host "cleanup plan: $($plan.Count) targets, $totalMB MB, plus $($pycache.Count) __pycache__ directories"
$plan | Sort-Object MB -Descending | Select-Object -First 12 | Format-Table -AutoSize | Out-String | Write-Host

if (-not $Apply) {
    Write-Host 'dry run only; re-run with -Apply to delete'
    return
}

$failed = New-Object System.Collections.Generic.List[string]
function Remove-Target {
    param([string]$Path)
    try {
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
    }
    catch {
        # Sandbox ACLs can deny a specific cache directory even when the rest of
        # the tree is writable; report it instead of aborting the whole sweep.
        $script:failed.Add($Path + ' -> ' + $_.Exception.Message.Split([char]10)[0])
    }
}
foreach ($item in $targets) { Remove-Target $item.FullName }
foreach ($directory in $pycache) { Remove-Target $directory.FullName }

$leftScratch = @(Get-ChildItem -LiteralPath $root -Force -Filter '.tmp-*').Count
$leftPycache = @(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notlike "$root\.venv*\*" -and $_.FullName -notlike "$root\vendor\*" -and $_.FullName -notlike "$root\.dotnet\*" }).Count
Write-Host "removed $($plan.Count) targets and $($pycache.Count) __pycache__ directories"
Write-Host "remaining scratch=$leftScratch pycache=$leftPycache"
if ($failed.Count -gt 0) {
    Write-Host "could not remove $($failed.Count) item(s):"
    $failed | ForEach-Object { Write-Host ('  ' + $_) }
}
