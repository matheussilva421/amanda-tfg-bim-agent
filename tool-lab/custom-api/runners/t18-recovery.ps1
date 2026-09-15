$ErrorActionPreference = 'Stop'

$RepoRoot = 'C:\Users\slvma\Downloads\Github\Projeto Amanda'
$RevitExe = 'C:\Program Files\Autodesk\Revit 2027\Revit.exe'
$AddinDir = Join-Path $env:APPDATA 'Autodesk\Revit\Addins\2027'
$HoldDir = Join-Path $env:TEMP 'Amanda-P02-T18-recovery-addin-hold'
$CheckpointRvt = Join-Path $RepoRoot 'revit\lab\custom-api\T18_LAST_PASS.rvt'
$BaselineRvt = Join-Path $RepoRoot 'revit\lab\baseline\LAB_R00_EMPTY.rvt'
$InterruptedResult = Join-Path $RepoRoot 'tool-lab\custom-api\results\t18-interrupted-host-result.json'
$HealthOut = Join-Path $RepoRoot 'tool-lab\custom-api\results\t18-recovery-health.json'
$ReadArgs = Join-Path $RepoRoot 'tool-lab\custom-api\results\t18-recovery-read-args.json'
$ReadOut = Join-Path $RepoRoot 'tool-lab\custom-api\results\t18-recovery-read.json'
$EvidenceDir = Join-Path $RepoRoot 'tool-lab\custom-api\results'
$EvidencePath = Join-Path $EvidenceDir 't18-recovery-run-log.txt'
$CheckpointSha256 = '8CCAB171E89FA4AC414F9CA3C57B5C4161CD7EE6DD61F45F86529703EE281CB2'
$BaselineSha256 = '15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D'

New-Item -ItemType Directory -Force -Path $HoldDir, $EvidenceDir | Out-Null
$lines = New-Object System.Collections.Generic.List[string]
$held = New-Object System.Collections.Generic.List[object]
$process = $null
$startedStartTime = $null

function Log([string]$message) {
    $stamp = (Get-Date).ToString('o')
    $lines.Add("$stamp $message")
    Write-Host "$stamp $message"
}

function Hash-File([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToUpperInvariant()
}

try {
    if (@(Get-Process -Name Revit -ErrorAction SilentlyContinue).Count -gt 0) {
        throw 'refusing T18 recovery: Revit already running'
    }
    if ((Hash-File $CheckpointRvt) -ne $CheckpointSha256) { throw 'last PASS checkpoint hash mismatch before recovery' }
    if ((Hash-File $BaselineRvt) -ne $BaselineSha256) { throw 'immutable baseline hash mismatch before recovery' }
    $interruptedPresentBefore = Test-Path -LiteralPath $InterruptedResult
    Log "last PASS checkpoint before sha256=$(Hash-File $CheckpointRvt) bytes=$((Get-Item -LiteralPath $CheckpointRvt).Length)"
    Log "baseline before sha256=$(Hash-File $BaselineRvt) bytes=$((Get-Item -LiteralPath $BaselineRvt).Length)"
    Log "interrupted mutation result present before recovery=$interruptedPresentBefore"

    foreach ($name in @('Amanda.ToolLab.Host.addin', 'RevitCortex.addin')) {
        $source = Join-Path $AddinDir $name
        $destination = Join-Path $HoldDir $name
        if (Test-Path -LiteralPath $destination) { throw "recovery addin hold destination already exists: $destination" }
        if (-not (Test-Path -LiteralPath $source)) { throw "required add-in missing: $source" }
        $hash = Hash-File $source
        Move-Item -LiteralPath $source -Destination $destination
        $held.Add([pscustomobject]@{Name=$name;HeldPath=$destination;Sha256=$hash})
        Log "held recovery addin $name sha256=$hash; Horizun remains installed"
    }

    $started = Start-Process -FilePath $RevitExe -ArgumentList ('"' + $CheckpointRvt + '"') -PassThru
    $process = $started
    $started.Refresh()
    $startedStartTime = $started.StartTime
    Log "started new own Revit pid=$($started.Id) start_time=$($startedStartTime.ToString('o')) checkpoint=$CheckpointRvt"
    $health = $null
    $healthDeadline = (Get-Date).AddSeconds(180)
    while ((Get-Date) -lt $healthDeadline) {
        $started.Refresh()
        if ($started.HasExited) { throw "recovery Revit exited while waiting for provider: $($started.ExitCode)" }
        & (Join-Path $RepoRoot '.venv\Scripts\python.exe') (Join-Path $RepoRoot '.tmp-hz.py') horizun_health --out $HealthOut --chars 5000 | ForEach-Object { $lines.Add($_) }
        if (Test-Path -LiteralPath $HealthOut) {
            $healthReply = Get-Content -LiteralPath $HealthOut -Raw | ConvertFrom-Json
            $candidate = $healthReply.result.structuredContent
            if ($candidate -and $candidate.status -eq 'healthy') {
                $health = $candidate
                break
            }
        }
        Start-Sleep -Seconds 5
    }
    if (-not $health) { throw 'recovery provider did not become healthy before timeout' }
    Log "recovery provider health status=$($health.status) process_id=$($health.process_id) revit_version=$($health.revit_version) build=$($health.revit_build)"
    Log "recovery active document title=$($health.active_document.title) path=$($health.active_document.path)"
    Log "recovery controls permission_profile=$($health.operational_controls.permission_profile) mcp_paused=$($health.operational_controls.mcp_paused)"
    if ($health.status -ne 'healthy') { throw "recovery provider health was not healthy: $($health.status)" }
    if ([int]$health.process_id -ne $started.Id) { throw "recovery provider attached to wrong pid: $($health.process_id)" }
    if (-not [string]::Equals($health.active_document.path, $CheckpointRvt, [StringComparison]::OrdinalIgnoreCase)) { throw 'recovery active document is not the last PASS checkpoint' }

    $readArgs = [ordered]@{element_ids=@(328658);response_mode='full';cache_mode='bypass';include_links=$false;include_bounding_box=$true;coordinate_units='mm';max_rows=10;return_fields=@('category','name','family','type','type_id','level','source_model','source_kind')}
    $readArgs | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ReadArgs -Encoding UTF8
    & (Join-Path $RepoRoot '.venv\Scripts\python.exe') (Join-Path $RepoRoot '.tmp-hz.py') horizun_query_model --args-file $ReadArgs --out $ReadOut --chars 8000 | ForEach-Object { $lines.Add($_) }
    if (-not (Test-Path -LiteralPath $ReadOut)) { throw 'recovery read output was not written' }
    $readReply = Get-Content -LiteralPath $ReadOut -Raw | ConvertFrom-Json
    $read = $readReply.result.structuredContent
    Log "recovery read matched_total=$($read.matched_total) returned=$($read.returned) coverage_complete=$($read.coverage_complete) unreadable_total=$($read.unreadable_total)"
    if ($read.matched_total -ne 1 -or $read.returned -ne 1 -or $read.unreadable_total -ne 0 -or -not $read.coverage_complete) { throw 'recovery read smoke did not prove the checkpoint wall' }
    Log "recovery read wall element_id=$($read.rows[0].element_id) bbox=$((ConvertTo-Json $read.rows[0].bounding_box -Compress))"

    $owned = Get-Process -Id $started.Id -ErrorAction SilentlyContinue
    if (-not $owned) { throw 'recovery Revit process disappeared before controlled cleanup' }
    $startTimeMatch = $owned.StartTime.ToUniversalTime().Ticks -eq $startedStartTime.ToUniversalTime().Ticks
    Log "recovery cleanup ownership proof pid=$($owned.Id) observed_start=$($owned.StartTime.ToString('o')) expected_start=$($startedStartTime.ToString('o')) start_time_match=$startTimeMatch"
    if (-not $startTimeMatch) { throw 'refusing recovery cleanup: StartTime mismatch' }
    Stop-Process -Id $owned.Id -Force
    Wait-Process -Id $owned.Id -Timeout 20 -ErrorAction SilentlyContinue
    if (Get-Process -Id $owned.Id -ErrorAction SilentlyContinue) { throw 'recovery Revit did not stop after owned cleanup' }
    Log 'new recovery Revit stopped after health/read smoke'
}
finally {
    if ($process -and -not $process.HasExited) {
        $owned = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
        if ($owned -and $startedStartTime -and ($owned.StartTime.ToUniversalTime().Ticks -eq $startedStartTime.ToUniversalTime().Ticks)) {
            Log "finally ownership proven before stop pid=$($owned.Id)"
            Stop-Process -Id $owned.Id -Force
        }
        elseif ($owned) { Log 'finally ownership NOT proven; process left untouched' }
    }

    foreach ($item in $held) {
        $sharedPath = Join-Path $AddinDir $item.Name
        if ((Test-Path -LiteralPath $item.HeldPath) -and -not (Test-Path -LiteralPath $sharedPath)) {
            Move-Item -LiteralPath $item.HeldPath -Destination $sharedPath
        }
        if (Test-Path -LiteralPath $sharedPath) {
            $restoredHash = Hash-File $sharedPath
            Log "restored addin $($item.Name) hash_match=$($restoredHash -eq $item.Sha256) sha256=$restoredHash"
        }
        else { Log "restored addin $($item.Name) missing after recovery" }
    }

    Log "interrupted mutation result present after recovery=$(Test-Path -LiteralPath $InterruptedResult)"
    $checkpointHashAfter = $null
    $baselineHashAfter = $null
    for ($attempt = 1; $attempt -le 20; $attempt++) {
        try {
            $checkpointHashAfter = Hash-File $CheckpointRvt
            $baselineHashAfter = Hash-File $BaselineRvt
            break
        }
        catch {
            if ($attempt -eq 20) { throw }
            Start-Sleep -Milliseconds 500
        }
    }
    Log "last PASS checkpoint after sha256=$checkpointHashAfter intact=$($checkpointHashAfter -eq $CheckpointSha256)"
    Log "baseline after sha256=$baselineHashAfter intact=$($baselineHashAfter -eq $BaselineSha256)"
    $lines | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
    Write-Host "evidence written to $EvidencePath"
}
