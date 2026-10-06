"""Read-only compact snapshot; PIDs alone never imply successful training."""
import datetime as dt
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent; RUN=HERE.parent; ROOT=RUN.parents[2]
def read(path):
    return json.loads(path.read_text()) if path.exists() else None
progress=read(HERE/'train_01/progress.json')
resource=read(RUN/'controller/rematch_sft8b_full_01.resource.json')
active=read(ROOT/'improvement_round1/active_gpu_job.json')
owned=active if active and active.get('name')=='rematch_sft8b_full_01' else None
result=dict(checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),launch=read(HERE/'launch.json'),
    stage=progress['status'] if progress else ('WAITING_REGISTERED_GPU_WRAPPER' if owned else 'NO_TRAIN_PROGRESS_YET'),
    optimizer_steps=progress.get('optimizer_steps') if progress else None,
    effective_batches=progress.get('effective_batches') if progress else None,
    epoch_effective_counts=progress.get('epoch_effective_counts') if progress else None,
    parameter_inventory=progress.get('parameter_inventory') if progress else None,
    last_update=progress.get('updates',[])[-1] if progress and progress.get('updates') else None,
    failure=progress.get('failure') if progress else None,
    resource=resource,owned_active_gpu_job=owned,
    gpu_compute=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory',
                                         '--format=csv,noheader,nounits'],text=True).strip())
print(json.dumps(result,ensure_ascii=False,indent=2))
