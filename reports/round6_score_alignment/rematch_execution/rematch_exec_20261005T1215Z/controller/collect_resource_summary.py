"""Read current identity/resources/append-only ledger; do not alter old records."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess

ROOT=Path('/home/inspur/aic_video_work')
RUN=ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
if __name__=='__main__':
    ledger=ROOT/'improvement_round1/gpu_ledger.jsonl'
    rows=[json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    policy=ROOT/'resource_policy.json'
    active=ROOT/'improvement_round1/active_gpu_job.json'
    report={'checked_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'host':socket.gethostname(),
        'resource_policy':json.loads(policy.read_text()),'resource_policy_sha256':hashlib.sha256(policy.read_bytes()).hexdigest(),
        'ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest(),'ledger_records':len(rows),
        'initial_offset_seconds':7200,'total_charged_seconds_including_offset':7200+sum(r['charged_seconds'] for r in rows),
        'this_execution_charged_seconds':sum(r['charged_seconds'] for r in rows if r['name'].startswith('rematch_')),
        'this_execution_jobs':[r for r in rows if r['name'].startswith('rematch_')],
        'project_disk_bytes':int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0]),
        'free_disk_bytes':shutil.disk_usage(ROOT).free,
        'nvidia_gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip(),
        'compute_processes':subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader'],text=True).strip(),
        'active_owned_reservation':json.loads(active.read_text()) if active.exists() else None}
    target=RUN/'controller/resource_latest.json'
    temp=target.with_suffix('.json.tmp')
    temp.write_text(json.dumps(report,indent=2)+'\n')
    temp.replace(target)
    print(json.dumps({key:report[key] for key in ['host','ledger_records','total_charged_seconds_including_offset',
        'this_execution_charged_seconds','project_disk_bytes','free_disk_bytes','compute_processes']},indent=2))
