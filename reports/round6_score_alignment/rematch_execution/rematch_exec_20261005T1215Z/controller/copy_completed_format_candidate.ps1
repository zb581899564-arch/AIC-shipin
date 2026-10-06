$ErrorActionPreference = 'Stop'
$taskRoot = 'G:\ai\AIC视频\reports\round6_score_alignment\rematch_execution\rematch_exec_20261005T1215Z'
$taskController = Join-Path $taskRoot 'controller'
$taskRemote = '/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
$taskDestination = Join-Path $taskRoot 'delivery_A_FORMAT_01'
$taskStatus = Join-Path $taskController 'format_delivery_latest.json'
$taskCompletion = Join-Path $taskController 'format_delivery_completion.json'
$taskExpectedFinishLock = 'ddfdb728d19e49ef627b335ac622e3f7d7cef479c7c97064ee77c36e3bd901fe'

function Write-TaskStatus($value) {
    $value | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskStatus -Encoding utf8
}
function Invoke-TaskScp([string[]]$items) {
    & scp -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 -J macmini @items
    if ($LASTEXITCODE -ne 0) { throw 'Mac-routed artifact transfer failed; no direct fallback.' }
}

if (Test-Path -LiteralPath $taskCompletion) { throw 'Delivery receipt already exists; do not repeat.' }
try {
    $taskDeadline = (Get-Date).ToUniversalTime().AddHours(12)
    Write-TaskStatus @{stage='WAITING_REGISTERED_LINUX_CANDIDATE';pid=$PID;uploaded=$false;checked_utc=(Get-Date).ToUniversalTime().ToString('o')}
    while ($true) {
        & ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 aic-inspur-home "test -f $taskRemote/controller/format_pipeline_completion.json"
        if ($LASTEXITCODE -eq 0) { break }
        if ((Get-Date).ToUniversalTime() -ge $taskDeadline) { throw 'Bounded wait expired; remote status remains unconfirmed.' }
        Start-Sleep -Seconds 60
    }
    # Mac is verified live immediately before any file transfer.
    $taskMac = & ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 macmini '/Users/choubk/codex-workspace/bin/run uname -n'
    if ($LASTEXITCODE -ne 0 -or -not $taskMac) { throw 'Mac jump host unavailable; leave completed Linux artifacts untouched.' }
    New-Item -ItemType Directory -Path $taskDestination -ErrorAction Stop | Out-Null
    Invoke-TaskScp -items @("aic-inspur-home:$taskRemote/controller/format_pipeline_completion.json", "$taskDestination/pipeline_completion.json")
    Invoke-TaskScp -items @("aic-inspur-home:$taskRemote/controller/format_recovery_finish_lock.json", "$taskDestination/finish_lock.json")
    if ((Get-FileHash -LiteralPath "$taskDestination/finish_lock.json" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskExpectedFinishLock) {
        throw 'Completed continuation identity changed.'
    }
    $taskRemoteReceipt = Get-Content -LiteralPath "$taskDestination/pipeline_completion.json" -Raw | ConvertFrom-Json
    if ($taskRemoteReceipt.stage -ne 'PASS_COMPLETE_426_CANDIDATE_NOT_UPLOADED' -or $taskRemoteReceipt.videos -ne 426) {
        throw "Linux candidate not accepted: $($taskRemoteReceipt.stage) / $($taskRemoteReceipt.failure)"
    }
    Write-TaskStatus @{stage='COPYING_ACCEPTED_426_ARTIFACTS_VIA_MAC';pid=$PID;uploaded=$false;checked_utc=(Get-Date).ToUniversalTime().ToString('o')}
    Invoke-TaskScp -items @("aic-inspur-home:$taskRemote/controller/rematch_e2e_recovery_01.inventory.json", "$taskDestination/inventory.json")
    if ((Get-FileHash -LiteralPath "$taskDestination/inventory.json" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskRemoteReceipt.inventory_sha256) {
        throw 'Candidate artifact inventory identity mismatch.'
    }
    Invoke-TaskScp -items @('-r', "aic-inspur-home:$taskRemote/baseline_a_pts_v1/rematch_e2e_recovery_01", $taskDestination)
    $taskFolder = Join-Path $taskDestination 'rematch_e2e_recovery_01'
    $taskInventory = Get-Content -LiteralPath "$taskDestination/inventory.json" -Raw | ConvertFrom-Json
    $taskFolderResolved = [IO.Path]::GetFullPath($taskFolder) + [IO.Path]::DirectorySeparatorChar
    foreach ($item in $taskInventory.records) {
        $taskFile = [IO.Path]::GetFullPath((Join-Path $taskFolder $item.path))
        if (-not $taskFile.StartsWith($taskFolderResolved,[StringComparison]::OrdinalIgnoreCase)) { throw 'Inventory path escapes artifact folder.' }
        if ((Get-Item -LiteralPath $taskFile).Length -ne $item.bytes -or
            (Get-FileHash -LiteralPath $taskFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) { throw "Copied identity mismatch: $($item.path)" }
    }
    $taskCandidate = Join-Path $taskFolder 'candidate_A_PTS.zip'
    if ((Get-Item -LiteralPath $taskCandidate).Length -ne $taskRemoteReceipt.candidate_bytes -or
        (Get-FileHash -LiteralPath $taskCandidate -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskRemoteReceipt.candidate_sha256) {
        throw 'Final candidate size or independent SHA mismatch.'
    }
    $taskResult = @{stage='PASS_LOCAL_426_CANDIDATE_DELIVERED_NOT_UPLOADED';candidate=$taskCandidate;
        candidate_sha256=$taskRemoteReceipt.candidate_sha256;candidate_bytes=$taskRemoteReceipt.candidate_bytes;
        inventory_files=$taskInventory.records.Count;videos=426;selected_frames=$taskRemoteReceipt.selected_frames;
        uploaded=$false;transport='scp -J macmini';checked_utc=(Get-Date).ToUniversalTime().ToString('o')}
} catch {
    $taskResult = @{stage='STOP_FORMAT_DELIVERY';failure=$_.Exception.Message;candidate_not_accepted=$true;
        uploaded=$false;checked_utc=(Get-Date).ToUniversalTime().ToString('o')}
}
Write-TaskStatus $taskResult
$taskResult | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskCompletion -Encoding utf8
if ($taskResult.stage -ne 'PASS_LOCAL_426_CANDIDATE_DELIVERED_NOT_UPLOADED') { exit 1 }
