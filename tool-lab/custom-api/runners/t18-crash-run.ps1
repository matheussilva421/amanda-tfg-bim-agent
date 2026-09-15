$ErrorActionPreference = 'Stop'

$RepoRoot = 'C:\Users\slvma\Downloads\Github\Projeto Amanda'
$RevitExe = 'C:\Program Files\Autodesk\Revit 2027\Revit.exe'
$AddinDir = Join-Path $env:APPDATA 'Autodesk\Revit\Addins\2027'
$HoldDir = Join-Path $env:TEMP 'Amanda-P02-T18-addin-hold'
$HostBin = Join-Path $RepoRoot 'tool-lab\custom-api\host\bin\Release\net10.0-windows7.0'
$HostAddinName = 'Amanda.ToolLab.Host.addin'
$CortexAddinName = 'RevitCortex.addin'
$HostJobPath = Join-Path $RepoRoot '.tmp-t18-host-job.json'
$CheckpointRvt = Join-Path $RepoRoot 'revit\lab\custom-api\T18_LAST_PASS.rvt'
$WorkRvt = Join-Path $RepoRoot 'revit\lab\custom-api\T18_CRASH_WORK.rvt'
$StandbyRvt = Join-Path $RepoRoot 'revit\lab\baseline\LAB_R00_EMPTY.rvt'
$ResultPath = Join-Path $RepoRoot 'tool-lab\custom-api\results\t18-interrupted-host-result.json'
$HostStatusPath = Join-Path $HostBin 'host-status.log'
$EvidenceDir = Join-Path $RepoRoot 'tool-lab\custom-api\results'
$EvidencePath = Join-Path $EvidenceDir 't18-crash-run-log.txt'
$StatusEvidencePath = Join-Path $EvidenceDir 't18-host-status.log'
$JournalDir = Join-Path $env:LOCALAPPDATA 'Autodesk\Revit\Autodesk Revit 2027\Journals'
$CheckpointSha256 = '8CCAB171E89FA4AC414F9CA3C57B5C4161CD7EE6DD61F45F86529703EE281CB2'
$BaselineSha256 = '15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D'
$TimeoutSeconds = 240
$RunStamp = Get-Date -Format 'yyyyMMdd-HHmmss'

New-Item -ItemType Directory -Force -Path $HoldDir, $EvidenceDir | Out-Null
$lines = New-Object System.Collections.Generic.List[string]
$held = New-Object System.Collections.Generic.List[object]
$process = $null
$startedStartTime = $null
$crashMarkerSeen = $false
$crashBeforeSave = $false
$token = [Guid]::NewGuid().ToString('N')
$previousToken = [Environment]::GetEnvironmentVariable('AMANDA_LAB_HOST_TOKEN', 'Process')
$previousJobPath = [Environment]::GetEnvironmentVariable('AMANDA_LAB_HOST_JOB', 'Process')

function Log([string]$message) {
    $stamp = (Get-Date).ToString('o')
    $lines.Add("$stamp $message")
    Write-Host "$stamp $message"
}

function Hash-File([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Hash-Text([string]$value) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($value)
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToUpperInvariant()
    }
    finally { $sha.Dispose() }
}

function Save-LaunchJob([int]$expectedPid) {
    $job = [ordered]@{
        mode = 'create'
        work_rvt = $WorkRvt
        standby_rvt = $StandbyRvt
        result_path = $ResultPath
        status_path = $HostStatusPath
        expect_element_id_value = 0
        expected_pid = $expectedPid
        env_token = $token
    }
    $temporary = "$HostJobPath.tmp"
    $job | ConvertTo-Json | Set-Content -LiteralPath $temporary -Encoding UTF8
    Move-Item -LiteralPath $temporary -Destination $HostJobPath -Force
    Log "job written expected_pid=$expectedPid work_rvt=$WorkRvt token_sha256=$(Hash-Text $token)"
}

try {
    if (@(Get-Process -Name Revit -ErrorAction SilentlyContinue).Count -gt 0) {
        throw 'refusing T18 crash drill: Revit already running'
    }
    if (-not (Test-Path -LiteralPath $RevitExe)) { throw "Revit executable not found: $RevitExe" }

    $checkpointHashBefore = Hash-File $CheckpointRvt
    if ($checkpointHashBefore -ne $CheckpointSha256) {
        throw "last PASS checkpoint hash mismatch: observed=$checkpointHashBefore expected=$CheckpointSha256"
    }
    $baselineHashBefore = Hash-File $StandbyRvt
    if ($baselineHashBefore -ne $BaselineSha256) {
        throw "baseline hash mismatch: observed=$baselineHashBefore expected=$BaselineSha256"
    }
    Log "checkpoint PASS before sha256=$checkpointHashBefore bytes=$((Get-Item -LiteralPath $CheckpointRvt).Length)"
    Log "baseline before sha256=$baselineHashBefore bytes=$((Get-Item -LiteralPath $StandbyRvt).Length)"

    foreach ($old in @($ResultPath, $HostStatusPath, $HostJobPath, "$HostJobPath.tmp")) {
        if (Test-Path -LiteralPath $old) {
            $backup = Join-Path $EvidenceDir ((Split-Path -Leaf $old) + ".before-$RunStamp")
            Copy-Item -LiteralPath $old -Destination $backup -Force
            Remove-Item -LiteralPath $old -Force
            Log "previous artifact preserved=$backup"
        }
    }

    Copy-Item -LiteralPath $CheckpointRvt -Destination $WorkRvt -Force
    $workHashBefore = Hash-File $WorkRvt
    if ($workHashBefore -ne $CheckpointSha256) { throw "crash work copy mismatch: $workHashBefore" }
    Log "crash work reset from last PASS checkpoint sha256=$workHashBefore bytes=$((Get-Item -LiteralPath $WorkRvt).Length)"

    foreach ($name in @($HostAddinName, $CortexAddinName)) {
        $source = Join-Path $AddinDir $name
        $destination = Join-Path $HoldDir $name
        if (Test-Path -LiteralPath $destination) { throw "addin hold destination already exists: $destination" }
        if (-not (Test-Path -LiteralPath $source)) { throw "required shared add-in missing: $source" }
        $hash = Hash-File $source
        Move-Item -LiteralPath $source -Destination $destination
        $held.Add([pscustomobject]@{Name=$name;HeldPath=$destination;Sha256=$hash})
        Log "held addin $name sha256=$hash"
    }

    $hostHeld = @($held | Where-Object Name -eq $HostAddinName | Select-Object -First 1)[0]
    Move-Item -LiteralPath $hostHeld.HeldPath -Destination (Join-Path $AddinDir $HostAddinName)
    Log "placed only host addin sha256=$(Hash-File (Join-Path $AddinDir $HostAddinName))"

    $env:AMANDA_LAB_HOST_TOKEN = $token
    $env:AMANDA_LAB_HOST_JOB = $HostJobPath
    Log "runner environment set AMANDA_LAB_HOST_TOKEN and AMANDA_LAB_HOST_JOB before launch"

    $started = Start-Process -FilePath $RevitExe -ArgumentList ('"' + $WorkRvt + '"') -PassThru
    $process = $started
    $started.Refresh()
    $startedStartTime = $started.StartTime
    Log "started own Revit pid=$($started.Id) start_time=$($startedStartTime.ToString('o')) work_rvt=$WorkRvt"
    Save-LaunchJob $started.Id

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $started.Refresh()
        if ($started.HasExited) { Log "Revit exited before crash marker code=$($started.ExitCode)"; break }
        if (Test-Path -LiteralPath $HostStatusPath) {
            $status = Get-Content -LiteralPath $HostStatusPath -Raw
            if ($status -match 'step invoke-external-command: PASS') {
                $crashMarkerSeen = $true
                $hasSave = $status -match 'step save-document: PASS'
                Log "ownership guard accepted; mutation marker observed; save_marker_present=$hasSave"
                if (-not $hasSave) { $crashBeforeSave = $true }
                break
            }
        }
        Start-Sleep -Milliseconds 100
    }

    if (-not $crashMarkerSeen) { throw 'crash marker was not observed before timeout' }
    if (-not $crashBeforeSave) { throw 'mutation marker arrived after save; refusing to call this interrupted' }

    $owned = Get-Process -Id $started.Id -ErrorAction SilentlyContinue
    if (-not $owned) { throw 'Revit exited before controlled crash could be issued' }
    $startTimeMatch = $owned.StartTime.ToUniversalTime().Ticks -eq $startedStartTime.ToUniversalTime().Ticks
    Log "pre-crash ownership proof pid=$($owned.Id) observed_start=$($owned.StartTime.ToString('o')) expected_start=$($startedStartTime.ToString('o')) start_time_match=$startTimeMatch expected_pid_in_job=$($started.Id) token_sha256=$(Hash-Text $token) active_work_rvt=$WorkRvt"
    if (-not $startTimeMatch) { throw 'refusing crash: StartTime mismatch' }
    Stop-Process -Id $owned.Id -Force
    Log "crash simulated by stopping only owned pid=$($owned.Id) during the unsaved mutation flow"
    Wait-Process -Id $owned.Id -Timeout 20 -ErrorAction SilentlyContinue
    if (Get-Process -Id $owned.Id -ErrorAction SilentlyContinue) { throw 'owned Revit did not stop after crash simulation' }

    Start-Sleep -Seconds 2
    $resultPresent = Test-Path -LiteralPath $ResultPath
    $workHashAfter = Hash-File $WorkRvt
    $checkpointHashAfter = Hash-File $CheckpointRvt
    Log "post-crash result_present=$resultPresent work_sha256=$workHashAfter checkpoint_sha256=$checkpointHashAfter"
    if ($resultPresent) { Log 'WARNING: final host result exists; interrupted mutation boundary is not clean' }
    if ($workHashAfter -ne $CheckpointSha256) { Log 'WARNING: crash work bytes differ from checkpoint; inspect journal and recovery' }
    if ($HostStatusPath -and (Test-Path -LiteralPath $HostStatusPath)) {
        Copy-Item -LiteralPath $HostStatusPath -Destination $StatusEvidencePath -Force
        Log "host status copied sha256=$(Hash-File $StatusEvidencePath) bytes=$((Get-Item -LiteralPath $StatusEvidencePath).Length)"
    }
    $journal = Get-ChildItem -LiteralPath $JournalDir -File -Filter '*.txt' -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $startedStartTime.AddSeconds(-5) } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($journal) {
        $dest = Join-Path $EvidenceDir 't18-crash-host-revit-journal.txt'
        Copy-Item -LiteralPath $journal.FullName -Destination $dest -Force
        Log "host journal copied source=$($journal.Name) sha256=$(Hash-File $dest) bytes=$((Get-Item -LiteralPath $dest).Length)"
    }
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

    $hostShared = Join-Path $AddinDir $HostAddinName
    if ((Test-Path -LiteralPath $hostShared) -and -not (Test-Path -LiteralPath $hostHeld.HeldPath)) {
        Move-Item -LiteralPath $hostShared -Destination $hostHeld.HeldPath
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
        else { Log "restored addin $($item.Name) missing after cleanup" }
    }

    if (Test-Path -LiteralPath $HostJobPath) { Remove-Item -LiteralPath $HostJobPath -Force }
    if (Test-Path -LiteralPath "$HostJobPath.tmp") { Remove-Item -LiteralPath "$HostJobPath.tmp" -Force }
    $baselineHashAfter = Hash-File $StandbyRvt
    $checkpointHashAfter = Hash-File $CheckpointRvt
    Log "baseline after sha256=$baselineHashAfter intact=$($baselineHashAfter -eq $BaselineSha256)"
    Log "last PASS checkpoint after sha256=$checkpointHashAfter intact=$($checkpointHashAfter -eq $CheckpointSha256)"

    if ($null -eq $previousToken) { Remove-Item Env:AMANDA_LAB_HOST_TOKEN -ErrorAction SilentlyContinue }
    else { $env:AMANDA_LAB_HOST_TOKEN = $previousToken }
    if ($null -eq $previousJobPath) { Remove-Item Env:AMANDA_LAB_HOST_JOB -ErrorAction SilentlyContinue }
    else { $env:AMANDA_LAB_HOST_JOB = $previousJobPath }
    Log 'runner environment restored'

    $lines | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
    Write-Host "evidence written to $EvidencePath"
}
