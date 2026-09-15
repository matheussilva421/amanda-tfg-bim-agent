$ErrorActionPreference = 'Stop'

$RepoRoot = 'C:\Users\slvma\Downloads\Github\Projeto Amanda'
$RevitExe = 'C:\Program Files\Autodesk\Revit 2027\Revit.exe'
$AddinDir = Join-Path $env:APPDATA 'Autodesk\Revit\Addins\2027'
$HoldDir = Join-Path $RepoRoot '.tmp-t16-addin-hold'
$HostBin = Join-Path $RepoRoot 'tool-lab\custom-api\host\bin\Release\net10.0-windows7.0'
$HostAddinName = 'Amanda.ToolLab.Host.addin'
$HostJobPath = Join-Path $RepoRoot '.tmp-t16-host-job.json'
$WorkRvt = Join-Path $RepoRoot 'revit\lab\custom-api\LAB_CUSTOM_WALL.rvt'
$BaselinePath = Join-Path $RepoRoot 'revit\lab\baseline\LAB_R00_EMPTY.rvt'
$ResultPath = Join-Path $RepoRoot 'tool-lab\custom-api\results\t16-host-create.json'
$StatusPath = Join-Path $HostBin 'host-status.log'
$EvidenceDir = Join-Path $RepoRoot 'tool-lab\custom-api\results'
$EvidencePath = Join-Path $EvidenceDir 't16-run-log.txt'
$JournalDir = Join-Path $env:LOCALAPPDATA 'Autodesk\Revit\Autodesk Revit 2027\Journals'
$ExpectedBaselineSha256 = '15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D'
$TimeoutSeconds = 480
$RunStamp = Get-Date -Format 'yyyyMMdd-HHmmss'

New-Item -ItemType Directory -Force -Path $HoldDir, $EvidenceDir | Out-Null

$lines = New-Object System.Collections.Generic.List[string]
$held = New-Object System.Collections.Generic.List[object]
$process = $null
$startedStartTime = $null
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
    finally {
        $sha.Dispose()
    }
}

function Save-LaunchJob([int]$expectedPid) {
    $job = [ordered]@{
        mode = 'create'
        work_rvt = $WorkRvt
        standby_rvt = $BaselinePath
        result_path = $ResultPath
        status_path = $StatusPath
        expect_element_id_value = 0
        expected_pid = $expectedPid
        env_token = $token
    }
    $temporaryJobPath = "$HostJobPath.tmp"
    $job | ConvertTo-Json | Set-Content -LiteralPath $temporaryJobPath -Encoding UTF8
    Move-Item -LiteralPath $temporaryJobPath -Destination $HostJobPath -Force
    Log "job written path=$HostJobPath expected_pid=$expectedPid token_sha256=$(Hash-Text $token)"
}

try {
    $existing = @(Get-Process -Name Revit -ErrorAction SilentlyContinue)
    if ($existing.Count -gt 0) {
        throw ('refusing to start: Revit already running pid(s) ' + (($existing | Select-Object -ExpandProperty Id) -join ','))
    }

    if (-not (Test-Path -LiteralPath $RevitExe)) {
        throw "Revit executable not found: $RevitExe"
    }

    $baselineHashBefore = Hash-File $BaselinePath
    $baselineSizeBefore = (Get-Item -LiteralPath $BaselinePath).Length
    if ($baselineHashBefore -ne $ExpectedBaselineSha256) {
        throw "baseline hash mismatch before run: observed=$baselineHashBefore expected=$ExpectedBaselineSha256"
    }
    Log "baseline before sha256=$baselineHashBefore bytes=$baselineSizeBefore"

    $workHashBefore = Hash-File $WorkRvt
    $workSizeBefore = (Get-Item -LiteralPath $WorkRvt).Length
    Log "work fixture before sha256=$workHashBefore bytes=$workSizeBefore"

    foreach ($old in @($ResultPath, $StatusPath, $HostJobPath, "$HostJobPath.tmp")) {
        if (Test-Path -LiteralPath $old) {
            $backup = Join-Path $EvidenceDir ((Split-Path -Leaf $old) + ".before-$RunStamp")
            Copy-Item -LiteralPath $old -Destination $backup -Force
            Remove-Item -LiteralPath $old -Force
            Log "previous artifact preserved=$backup"
        }
    }

    Copy-Item -LiteralPath $BaselinePath -Destination $WorkRvt -Force
    $workFixtureHash = Hash-File $WorkRvt
    if ($workFixtureHash -ne $ExpectedBaselineSha256) {
        throw "disposable fixture reset failed: observed=$workFixtureHash expected=$ExpectedBaselineSha256"
    }
    Log "work fixture reset from baseline sha256=$workFixtureHash bytes=$((Get-Item -LiteralPath $WorkRvt).Length)"

    foreach ($name in @($HostAddinName, 'Horizun.addin', 'RevitCortex.addin')) {
        $source = Join-Path $AddinDir $name
        $destination = Join-Path $HoldDir $name
        if (Test-Path -LiteralPath $destination) {
            throw "addin hold destination already exists: $destination"
        }
        if (Test-Path -LiteralPath $source) {
            $hash = Hash-File $source
            Move-Item -LiteralPath $source -Destination $destination
            $held.Add([pscustomobject]@{ Name = $name; HeldPath = $destination; Sha256 = $hash })
            Log "held addin $name sha256=$hash"
        }
    }

    $hostRecord = @($held | Where-Object { $_.Name -eq $HostAddinName }) | Select-Object -First 1
    if (-not $hostRecord) {
        throw "required host addin was not present in shared folder: $HostAddinName"
    }

    Move-Item -LiteralPath $hostRecord.HeldPath -Destination (Join-Path $AddinDir $HostAddinName)
    Log "placed runtime addin $HostAddinName sha256=$(Hash-File (Join-Path $AddinDir $HostAddinName))"

    $env:AMANDA_LAB_HOST_TOKEN = $token
    $env:AMANDA_LAB_HOST_JOB = $HostJobPath
    Log 'AMANDA_LAB_HOST_TOKEN and AMANDA_LAB_HOST_JOB set in runner process before Start-Process'

    $started = Start-Process -FilePath $RevitExe -ArgumentList ('"' + $WorkRvt + '"') -PassThru
    $process = $started
    $started.Refresh()
    $startedStartTime = $started.StartTime
    Log "started Revit pid=$($started.Id) start_time=$($startedStartTime.ToString('o')) work_rvt=$WorkRvt"
    Save-LaunchJob $started.Id

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath $ResultPath) {
            Log 'result file appeared'
            break
        }
        if ($started.HasExited) {
            Log ("Revit pid=$($started.Id) exited before result with code " + $started.ExitCode)
            break
        }
        Start-Sleep -Seconds 5
        $started.Refresh()
    }

    $resultPresent = Test-Path -LiteralPath $ResultPath
    $started.Refresh()
    Log "result present=$resultPresent process_exited=$($started.HasExited)"

    if ($resultPresent) {
        Start-Sleep -Seconds 3
        $resultObject = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
        Log "host outcome=$($resultObject.outcome) total_ms=$($resultObject.total_ms)"
    }

    if (-not $started.HasExited) {
        $owned = Get-Process -Id $started.Id -ErrorAction SilentlyContinue
        if ($owned -and $owned.StartTime -eq $startedStartTime) {
            Log "ownership proven before stop pid=$($owned.Id) start_time=$($owned.StartTime.ToString('o'))"
            Stop-Process -Id $owned.Id -Force
            Log 'owned Revit process stopped by runner after host result'
        }
        else {
            Log 'ownership NOT proven at cleanup; leaving process alone'
        }
    }
    else {
        Log "Revit pid=$($started.Id) exit code $($started.ExitCode)"
    }

    Start-Sleep -Seconds 2
    if (Test-Path -LiteralPath $JournalDir) {
        $journal = Get-ChildItem -LiteralPath $JournalDir -File -Filter '*.txt' |
            Where-Object { $_.LastWriteTime -ge $startedStartTime.AddSeconds(-5) } |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($journal) {
            $journalEvidence = Join-Path $EvidenceDir 't16-host-revit-journal.txt'
            Copy-Item -LiteralPath $journal.FullName -Destination $journalEvidence -Force
            Log "host journal copied source=$($journal.Name) sha256=$(Hash-File $journalEvidence) bytes=$((Get-Item -LiteralPath $journalEvidence).Length)"
        }
        else {
            Log 'no Revit journal newer than owned process start was found'
        }
    }
}
finally {
    if ($process -and -not $process.HasExited) {
        $owned = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
        if ($owned -and $startedStartTime -and $owned.StartTime -eq $startedStartTime) {
            Log "finally ownership proven before stop pid=$($owned.Id) start_time=$($owned.StartTime.ToString('o'))"
            Stop-Process -Id $owned.Id -Force
            Log 'finally stopped owned Revit process'
        }
        elseif ($owned) {
            Log 'finally ownership NOT proven; process left untouched'
        }
    }

    foreach ($item in $held) {
        $sharedPath = Join-Path $AddinDir $item.Name
        if (-not (Test-Path -LiteralPath $sharedPath) -and (Test-Path -LiteralPath $item.HeldPath)) {
            Move-Item -LiteralPath $item.HeldPath -Destination $sharedPath
        }
        if (Test-Path -LiteralPath $sharedPath) {
            $restoredHash = Hash-File $sharedPath
            Log "restored addin $($item.Name) hash_match=$($restoredHash -eq $item.Sha256) sha256=$restoredHash"
        }
        else {
            Log "restored addin $($item.Name) missing after cleanup"
        }
    }

    if (Test-Path -LiteralPath $HostJobPath) {
        Remove-Item -LiteralPath $HostJobPath -Force
        Log 'removed per-run host job'
    }
    if (Test-Path -LiteralPath "$HostJobPath.tmp") {
        Remove-Item -LiteralPath "$HostJobPath.tmp" -Force
    }

    $baselineHashAfter = Hash-File $BaselinePath
    Log "baseline after sha256=$baselineHashAfter bytes=$((Get-Item -LiteralPath $BaselinePath).Length) intact=$($baselineHashAfter -eq $ExpectedBaselineSha256)"
    if (Test-Path -LiteralPath $WorkRvt) {
        Log "work fixture after sha256=$(Hash-File $WorkRvt) bytes=$((Get-Item -LiteralPath $WorkRvt).Length)"
    }

    if ($null -eq $previousToken) {
        Remove-Item Env:AMANDA_LAB_HOST_TOKEN -ErrorAction SilentlyContinue
    }
    else {
        $env:AMANDA_LAB_HOST_TOKEN = $previousToken
    }
    if ($null -eq $previousJobPath) {
        Remove-Item Env:AMANDA_LAB_HOST_JOB -ErrorAction SilentlyContinue
    }
    else {
        $env:AMANDA_LAB_HOST_JOB = $previousJobPath
    }
    Log 'AMANDA_LAB_HOST_TOKEN and AMANDA_LAB_HOST_JOB removed/restored in runner process'

    Log '--- host status log ---'
    if (Test-Path -LiteralPath $StatusPath) {
        foreach ($line in Get-Content -LiteralPath $StatusPath -Tail 60) {
            $lines.Add($line)
        }
    }
    else {
        $lines.Add('(no host status log was written)')
    }

    Log '--- result file ---'
    if (Test-Path -LiteralPath $ResultPath) {
        foreach ($line in Get-Content -LiteralPath $ResultPath) {
            $lines.Add($line)
        }
    }
    else {
        $lines.Add('(no result file was written)')
    }

    $lines | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
    Write-Host "evidence written to $EvidencePath"
}
