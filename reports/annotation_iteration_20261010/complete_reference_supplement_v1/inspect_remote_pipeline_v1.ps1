[CmdletBinding()]
param([switch]$Compact)
$ErrorActionPreference='Stop'
$code=@'
import json,pathlib,datetime,subprocess,hashlib
R=pathlib.Path("/home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1")
report={"utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
H=pathlib.Path("/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller")
report["training_step_files"]=[p.name for p in sorted((R/"train_01").glob("step_*.json"))]
report["native_input_files"]=len(list((R/"native_inputs_01").glob("*.input.json")))
report["evaluation_done"]=len(list((R/"evaluate_01").glob("*/*.done.json")))
for phase in ["train","evaluate","candidate"]:
 p=H/("aic_complete_silver_native_v1_"+phase+".log")
 if p.exists():report[phase+"_actual_child_log"]={"bytes":p.stat().st_size,"last_lines":p.read_text(errors="replace").splitlines()[-4:]}
 p=H/("aic_complete_silver_native_v1_"+phase+".resource.json")
 if p.exists():
  d=json.loads(p.read_text());report[phase+"_resource"]={k:d.get(k) for k in ["status","started_utc","finished_utc","charged_seconds","exit_code","stop_reason","child_pid","sampled_peak_memory_mib"]}
paths=["pipeline_01/completion.json","candidate_static_input_acceptance.json","native_inputs_01/receipt.json","train_01/training_receipt.json","evaluate_01/evaluation_receipt.json","evaluate_01/independent_quality_receipt.json","candidate_01/completion.json"]
for name in paths:
 p=R/name
 if p.exists():
  d=json.loads(p.read_text());report[name]={k:v for k,v in d.items() if k in ["status","utc","failure","failure_type","quality_gate_passed","optimizer_updates","updates","records","fresh_temporal_model_calls","candidate","zip_bytes","zip_sha256","final_adapter_sha256","model_calls_reconstructed","rows","steps","new_optimizer_updates"]}
  if "rows" in report[name]:report[name]["rows"]={"count":len(d["rows"])}
  if "updates" in report[name]:report[name]["updates"]={"count":len(d["updates"])}
  report[name]["sha256"]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ["deployment_metadata_v1/pipeline.nohup.log","pipeline_01/candidate_static_cpu.log","pipeline_01/native_cpu.log","pipeline_01/train.runner.log","pipeline_01/evaluate.runner.log","pipeline_01/candidate.runner.log"]:
 p=R/name
 if p.exists():report[name]={"bytes":p.stat().st_size,"last_lines":p.read_text(errors="replace").splitlines()[-5:]}
report["owned"]=[]
for p in pathlib.Path("/proc").iterdir():
 if not p.name.isdigit():continue
 try:
  raw=(p/"cmdline").read_bytes();cmd=raw.replace(b"\0",b" ").decode(errors="replace")
  if str(R) in cmd and ("pipeline_controller.py" in cmd or "inputs/runtime/" in cmd or "gpu_run.py" in cmd):
   stat=(p/"stat").read_text().split();report["owned"].append({"pid":int(p.name),"command":cmd,"state":stat[2],"ppid":int(stat[3]),"pgid":int(stat[4]),"CPU_ticks":int(stat[13])+int(stat[14]),"io":(p/"io").read_text(),"files":[str(x.readlink()) for x in (p/"fd").iterdir() if x.exists()][:10]})
 except (OSError,PermissionError):pass
report["gpu"]=subprocess.run(["nvidia-smi","--query-gpu=name,utilization.gpu,memory.used,memory.total","--format=csv,noheader"],text=True,capture_output=True).stdout.strip()
print(json.dumps(report,ensure_ascii=False))
'@
$lines=$code | & ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 aic-inspur-home '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'
if ($LASTEXITCODE -ne 0) { throw "Read-only pipeline snapshot exit $LASTEXITCODE" }
if (-not $Compact) { $lines; return }
$snap=($lines -join "`n") | ConvertFrom-Json
$short=[ordered]@{}
foreach ($p in $snap.PSObject.Properties) {
 if ($p.Name -eq 'owned') { $short['owned']=$p.Value | Select-Object pid,ppid,pgid,state,CPU_ticks; continue }
 if ($p.Name -like '*runner.log') { $short[$p.Name]=@{bytes=$p.Value.bytes}; continue }
 if ($p.Name -like '*log') { $short[$p.Name]=@{bytes=$p.Value.bytes;last_line=$p.Value.last_lines | Select-Object -Last 1}; continue }
 $short[$p.Name]=$p.Value
}
$short | ConvertTo-Json -Depth 10 -Compress
