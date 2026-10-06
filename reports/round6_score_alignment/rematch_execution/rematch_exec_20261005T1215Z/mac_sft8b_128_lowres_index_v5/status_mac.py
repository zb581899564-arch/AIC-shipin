"""Read compact live status, never promote a saved launch PID into run success."""
import json
import os
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent;CTRL=HERE/'controller'
def read(path):return json.loads(path.read_text()) if path.exists() else None
def alive(pid):
    if not pid:return False
    try:os.kill(pid,0)
    except ProcessLookupError:return False
    return str(HERE) in subprocess.check_output(['/bin/ps','-p',str(pid),'-o','command='],text=True)
launch=read(CTRL/'finish_mac_launch.json');latest=read(CTRL/'pipeline_latest.json')
asset_ctrl=Path('/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_20261006T054133Z')/'controller'
transfer=read(asset_ctrl/'asset_http_completion.json') or read(asset_ctrl/'asset_http_progress.json')
result=dict(controller_alive=alive((launch or {}).get('pid')),launch=launch,
    stage=(latest or {}).get('status'),optimizer_steps=(latest or {}).get('optimizer_steps'),
    effective_batches=(latest or {}).get('effective_batches'),failure=(latest or {}).get('failure'),
    transfer_status=(transfer or {}).get('status'),transfer_bytes=(transfer or {}).get('received_bytes'),
    transfer_total_bytes=(transfer or {}).get('total_bytes'),transfer_wall_seconds=(transfer or {}).get('wall_seconds'),
    completion=read(CTRL/'pipeline_completion.json'))
print(json.dumps(result,ensure_ascii=False,indent=2))
