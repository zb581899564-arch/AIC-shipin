param([string]$RunRoot = 'G:\ai\AIC视频\reports\round6_score_alignment\rematch_execution\rematch_exec_20261005T1215Z')
$ErrorActionPreference = 'Stop'
$packageLocal = Join-Path $RunRoot 'b_sft8b_package_v1'
$packageRemote = '/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_sft8b_package_v1'
$receiptPath = Join-Path $packageLocal 'bridge_registration.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Bridge already registered; never duplicate.' }
[System.IO.File]::WriteAllText($receiptPath, (@{pid=$PID;started_utc=[DateTime]::UtcNow.ToString('o');transfer_route='scp -J macmini';upload_authorized=$false} | ConvertTo-Json))
$deadline = [DateTime]::UtcNow.AddDays(3)
while ([DateTime]::UtcNow -lt $deadline) {
    $identity = & ssh macmini '/Users/choubk/codex-workspace/bin/run hostname' 2>&1
    $macOnline = $LASTEXITCODE -eq 0 -and "$identity".Trim() -eq 'choubkdeMac-Mini.local'
    if (-not $macOnline) { throw 'Mac live identity unavailable; no transfer bypass.' }
    $usage = & ssh macmini '/Users/choubk/codex-workspace/bin/run du -sk /Users/choubk/codex-workspace' 2>&1
    if ($LASTEXITCODE -ne 0 -or "$usage" -notmatch '^\s*(\d+)\s+') { throw 'Mac approved-root capacity query failed.' }
    $macWorkBytes = [long]$Matches[1] * 1024
    $capacityPath = Join-Path $packageLocal 'mac_capacity_latest.json'
    [System.IO.File]::WriteAllText($capacityPath, (@{status='PASS_LIVE_MAC_ROOT';utc=[DateTime]::UtcNow.ToString('o');work_bytes=$macWorkBytes;host='choubkdeMac-Mini.local';root='/Users/choubk/codex-workspace'} | ConvertTo-Json))
    & scp -J macmini $capacityPath "aic-inspur-home:${packageRemote}/mac_capacity_latest.pending.json"
    if ($LASTEXITCODE -ne 0) { throw 'Required Mac jump transfer failed.' }
    & ssh aic-inspur-home "mv ${packageRemote}/mac_capacity_latest.pending.json ${packageRemote}/mac_capacity_latest.json"
    if ($LASTEXITCODE -ne 0) { throw 'Capacity receipt atomic registration failed.' }
    $completionText = & ssh aic-inspur-home "if test -f ${packageRemote}/completion.json; then cat ${packageRemote}/completion.json; fi"
    if ($LASTEXITCODE -ne 0) { throw 'Remote package state UNKNOWN.' }
    if ("$completionText".Trim()) {
        $completion = "$($completionText -join [Environment]::NewLine)" | ConvertFrom-Json
        [System.IO.File]::WriteAllText((Join-Path $packageLocal 'completion.json'), ($completion | ConvertTo-Json -Depth 30))
        & scp -J macmini "aic-inspur-home:/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_dev_v1/decision.json" (Join-Path $RunRoot 'temporal_sft8b_dev_v1/decision.json')
        if ($LASTEXITCODE -ne 0) { throw 'Dev evidence copy failed.' }
        if ($completion.stage -ne 'PASS_COMPLETE_426_8B_PACKAGE_READY_FOR_DELIVERY') { throw "Remote gate STOP: $($completion.failure)" }
        $delivery = Join-Path $packageLocal 'delivery_01'
        if (Test-Path -LiteralPath $delivery) { throw 'Delivery directory already exists; preserve it.' }
        New-Item -ItemType Directory -Path $delivery | Out-Null
        foreach ($name in @('candidate_B_8B.zip','predictions.jsonl','provenance.jsonl','selected.jsonl','metadata.json','package.stage.json','independent_validation.json','spatial.stage.json')) {
            & scp -J macmini "aic-inspur-home:${packageRemote}/rematch_01/$name" (Join-Path $delivery $name)
            if ($LASTEXITCODE -ne 0) { throw "Mac jump delivery failed: $name" }
        }
        & python (Join-Path $packageLocal 'verify_delivery.py') $delivery
        if ($LASTEXITCODE -ne 0) { throw 'Local delivery bytes/CRC/independent strict acceptance failed.' }
        $receipt = @{status='PASS_LOCAL_UPLOADABLE_8B_PACKAGE';utc=[DateTime]::UtcNow.ToString('o');candidate=(Join-Path $delivery 'candidate_B_8B.zip');sha256=$completion.candidate_sha256;bytes=$completion.candidate_bytes;videos=426;uploaded=$false}
        [System.IO.File]::WriteAllText((Join-Path $packageLocal 'delivery_completion.json'), ($receipt | ConvertTo-Json -Depth 8))
        exit 0
    }
    Start-Sleep -Seconds 60
}
throw 'Bounded bridge deadline reached.'
