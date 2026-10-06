"""Windows relay: Linux read through configured Mac jump, only Mac workspace writes."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE=Path(__file__).resolve().parent
manifest_path=HERE/'assets_manifest.json';manifest=json.loads(manifest_path.read_text())
digest=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
remote_linux=manifest['linux_stage'];remote_mac=manifest['mac_project']
controller=HERE/'controller';controller.mkdir(exist_ok=True)
assert not (controller/'bridge_completion.json').exists()
with (controller/'bridge_sender.log').open('xb') as source_log,(controller/'bridge_receiver.log').open('xb') as target_log:
    source=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-J','macmini',
        'aic-inspur-home','/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python','-B',
        remote_linux+'/asset_sender.py','--manifest',remote_linux+'/assets_manifest.json','--expected-sha',digest],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=source_log)
    target=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','macmini',
        '/Users/choubk/codex-workspace/bin/run','/Users/choubk/codex-workspace/envs/ml/bin/python','-B',
        remote_mac+'/asset_receiver.py','--manifest',remote_mac+'/assets_manifest.json','--expected-sha',digest],
        stdin=source.stdout,stdout=target_log,stderr=subprocess.STDOUT)
    source.stdout.close()
    receipt=dict(status='BRIDGING_LINUX_NONTEST_ASSETS_VIA_MAC',started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                 windows_pid=__import__('os').getpid(),source_pid=source.pid,target_pid=target.pid,manifest_sha256=digest)
    (controller/'bridge_launch.json').write_text(json.dumps(receipt,indent=2)+'\n')
    target_rc=target.wait();source_rc=source.wait()
receipt.update(status='PASS_ASSET_BRIDGE_PROCESSES' if target_rc==source_rc==0 else 'STOP_ASSET_BRIDGE',
               source_exit=source_rc,target_exit=target_rc,finished_utc=dt.datetime.now(dt.timezone.utc).isoformat())
(controller/'bridge_completion.json').write_text(json.dumps(receipt,indent=2)+'\n')
