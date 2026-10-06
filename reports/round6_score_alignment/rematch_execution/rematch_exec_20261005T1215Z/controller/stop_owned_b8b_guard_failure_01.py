import json,os,signal
from pathlib import Path
p=Path('/home/inspur/aic_video_work/improvement_round1/active_gpu_job.json')
a=json.loads(p.read_text());assert a['name']=='rematch_B8B_v2_rematch_temporal_01'
pid=a['child_pid'];cmd=Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\x00',b' ').decode()
assert '/b_sft8b_package_v2/runtime.py temporal rematch ' in cmd and os.getpgid(pid)==pid
os.killpg(pid,signal.SIGTERM)
print(json.dumps(dict(status='STOPPED_ONLY_REGISTERED_GUARD_FAILURE_CHILD_GROUP',job=a['name'],child_pid=pid,reason='train-only8192 guard rejects unchanged production processor inputs',external_processes_touched=False)))
