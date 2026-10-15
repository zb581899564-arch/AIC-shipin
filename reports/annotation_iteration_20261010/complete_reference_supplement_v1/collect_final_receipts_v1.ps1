[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$destination='G:\ai\AIC视频\deliveries\SILVER24_SFT_20261011'
if (Test-Path -LiteralPath $destination) { throw 'Exclusive delivery destination already exists; preserve it.' }
New-Item -ItemType Directory -Path (Join-Path $destination 'evidence') | Out-Null
$query=@'
import pathlib,json,hashlib,datetime
r=pathlib.Path('/home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1')
h=pathlib.Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller')
names=['pipeline_01/completion.json','pipeline_01/train.terminal_binding.json','pipeline_01/evaluate.terminal_binding.json','pipeline_01/independent_quality.execution.json','train_01/training_receipt.json','evaluate_01/evaluation_receipt.json','evaluate_01/independent_quality_receipt.json','evaluate_01/scientific_gate.json']
paths=[r/n for n in names]+[h/('aic_complete_silver_native_v1_'+phase+'.resource.json') for phase in ['train','evaluate']]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((r/'pipeline_01/completion.json').read_text())
q=json.loads((r/'evaluate_01/independent_quality_receipt.json').read_text())
assert c['status']=='STOP_SCIENTIFIC_QUALITY_NO426_NO_RETUNING' and c['candidate_started'] is False
assert q['status']=='PASS_INDEPENDENT_CPU_FINAL_ONLY_EVALUATION_RECONSTRUCTION' and q['quality_gate_passed'] is False and q['model_calls_reconstructed']==24
ledger=pathlib.Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
rows=[json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
terminals=[]
for phase in ['train','evaluate']:
 p=h/('aic_complete_silver_native_v1_'+phase+'.resource.json');d=json.loads(p.read_text())
 found=[x for x in rows if x.get('name')==d['name']]
 assert len(found)==1 and found[0]==d
 assert d['stop_reason'] is None
 terminals.append({'phase':phase,'unique_terminal_equal':True,'status':d['status'],'exit_code':d['exit_code'],'charged_seconds':d['charged_seconds'],'started_utc':d['started_utc'],'finished_utc':d['finished_utc']})
adapter=r/'train_01/final_adapter/adapter_model.safetensors'
assert sha(adapter)==q['final_adapter_sha256']
assert not (r/'candidate_01').exists()
owned=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
  if str(r) in cmd and ('pipeline_controller.py' in cmd or 'inputs/runtime/' in cmd or 'gpu_run.py' in cmd):owned.append({'pid':int(p.name),'command':cmd})
 except OSError:pass
assert not owned
print(json.dumps({'status':'PASS_READ_ONLY_FINAL_RECONSTRUCTION_AND_UNIQUE_TERMINALS_SCIENTIFIC_STOP_PRESERVED','read_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':'inspur-NP5570M5','files':[{'remote_path':str(p),'local_name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths],'terminal_costs':terminals,'total_new_charged_seconds':sum(x['charged_seconds'] for x in terminals),'ledger_sha256':sha(ledger),'ledger_lines':len(rows),'owned_processes':owned,'candidate_started':False,'adapter':{'path':str(adapter),'bytes':adapter.stat().st_size,'sha256':sha(adapter)},'completion_timestamp_note':'completion.utc is the execute-report creation timestamp, not the finish timestamp; original bytes preserved. Phase terminal times and independent_quality.execution.json supply actual finish evidence.','completion_mtime_utc':datetime.datetime.fromtimestamp((r/'pipeline_01/completion.json').stat().st_mtime,datetime.timezone.utc).isoformat()},ensure_ascii=False))
'@
$raw=$query | ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 aic-inspur-home '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'
if ($LASTEXITCODE -ne 0) { throw 'Final read-only remote admission failed; preserve delivery directory.' }
$rawText=$raw -join "`n"
$manifest=$rawText | ConvertFrom-Json
$remoteSources=@($manifest.files | ForEach-Object { 'aic-inspur-home:'+$_.remote_path })
$arguments=@('-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15','-J','macmini')+$remoteSources+@((Join-Path $destination 'evidence'))
& scp @arguments
if ($LASTEXITCODE -ne 0) { throw 'Receipt download via macmini failed; no direct fallback or automatic retry.' }
foreach ($entry in $manifest.files) {
 $path=Join-Path (Join-Path $destination 'evidence') $entry.local_name
 if ((Get-Item -LiteralPath $path).Length -ne $entry.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw ('Receipt transfer integrity failed: '+$entry.local_name) }
}
[IO.File]::WriteAllText((Join-Path $destination 'remote_final_snapshot.json'),$rawText,[Text.UTF8Encoding]::new($false))
[pscustomobject]@{status='PASS_RECEIPTS_DOWNLOADED_VIA_MAC_JUMP_ALL_SHA_MATCH';destination=$destination;files=$manifest.files.Count;payload_bytes=($manifest.files | Measure-Object bytes -Sum).Sum;new_charged_seconds=$manifest.total_new_charged_seconds;scientific_quality_passed=$false;candidate_started=$false} | ConvertTo-Json -Compress
