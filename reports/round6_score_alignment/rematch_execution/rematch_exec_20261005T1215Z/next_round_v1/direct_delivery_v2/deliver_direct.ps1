param([string]$RunRoot='G:\ai\AIC视频\reports\round6_score_alignment\rematch_execution\rematch_exec_20261005T1215Z')
$ErrorActionPreference='Stop'
$taskDir=Join-Path $RunRoot 'next_round_v1/direct_delivery_v2'
$remoteDir='/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1'
if(Test-Path -LiteralPath (Join-Path $taskDir 'delivery_registration.json')){throw 'Never duplicate delivery waiter'}
[IO.File]::WriteAllText((Join-Path $taskDir 'delivery_registration.json'),(@{pid=$PID;utc=[DateTime]::UtcNow.ToString('o');mac_heartbeat_for_linux=$false;transfer_route='DIRECT_WINDOWS_LINUX_USER_RETIREMENT_OVERRIDE';uploaded=$false}|ConvertTo-Json))
$deadline=[DateTime]::UtcNow.AddDays(3)
$queryFailures=0
try{
  while([DateTime]::UtcNow -lt $deadline){
    $text=& ssh aic-inspur-home "if test -f ${remoteDir}/completion.json; then cat ${remoteDir}/completion.json; fi" 2>&1
    if($LASTEXITCODE -ne 0){$queryFailures++;if($queryFailures -ge 10){throw 'Remote state unavailable after bounded retries'};Start-Sleep -Seconds 60;continue}
    $queryFailures=0
    if("$text".Trim()){
      $completion=($text -join [Environment]::NewLine)|ConvertFrom-Json
      [IO.File]::WriteAllText((Join-Path $taskDir 'completion.json'),($completion|ConvertTo-Json -Depth 30))
      if($completion.stage -ne 'PASS_COMPLETE_426_Z8B_READY_FOR_DELIVERY'){throw "Remote STOP: $($completion.failure)"}
      $delivery=Join-Path $taskDir 'delivery_01'
      if(Test-Path -LiteralPath $delivery){throw 'Existing partial delivery preserved; no overwrite'}
      New-Item -ItemType Directory -Path $delivery|Out-Null
      foreach($name in @('candidate_Z_8B.zip','predictions.jsonl','provenance.jsonl','selected.jsonl','metadata.json','package.stage.json','independent_validation.json','spatial.stage.json')){
        & scp "aic-inspur-home:${remoteDir}/rematch_01/$name" (Join-Path $delivery $name)
        if($LASTEXITCODE -ne 0){throw "Direct alias transfer failed: $name"}
      }
      & python -B (Join-Path $taskDir 'verify_delivery.py') $delivery
      if($LASTEXITCODE -ne 0){throw 'Local SHA/size/CRC/independent loader failed'}
      [IO.File]::WriteAllText((Join-Path $taskDir 'delivery_completion.json'),(@{status='PASS_LOCAL_UPLOADABLE_Z8B_PACKAGE';utc=[DateTime]::UtcNow.ToString('o');candidate=(Join-Path $delivery 'candidate_Z_8B.zip');sha256=$completion.candidate_sha256;bytes=$completion.candidate_bytes;videos=426;uploaded=$false}|ConvertTo-Json))
      exit 0
    }
    Start-Sleep -Seconds 60
  }
  throw 'Delivery deadline reached'
}catch{
  [IO.File]::WriteAllText((Join-Path $taskDir 'delivery_stop.json'),(@{status='STOP_DELIVERY';utc=[DateTime]::UtcNow.ToString('o');reason=$_.Exception.Message;uploaded=$false}|ConvertTo-Json))
  throw
}
