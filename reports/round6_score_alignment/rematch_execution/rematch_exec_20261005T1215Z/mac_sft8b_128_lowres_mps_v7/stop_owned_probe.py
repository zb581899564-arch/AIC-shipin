from pathlib import Path
import json,os,signal,subprocess,datetime as dt
HERE=Path(__file__).resolve().parent
active=json.loads((HERE/'controller/active_training.json').read_text())
assert active['phase']=='probe' and active['source_lock_sha256']=='fb72b24e524423fc9af585a404eb954c36bcf59eca4df3685ef5211e2c647936'
child=active['child_pid'];command=subprocess.check_output(['/bin/ps','-p',str(child),'-o','command='],text=True).strip()
assert str(HERE/'train_mac.py') in command and os.getpgid(child)==child
probe=json.loads((HERE/'probe_01/progress.json').read_text())
assert probe['optimizer_steps']>=1 and probe['peak_mps_driver_mib']*2**20>probe['mps_recommended_max_memory_bytes']
receipt=dict(status='STOP_OWNED_128_FRAME_PROBE_OUTSIDE_LIVE_RECOMMENDED_MEMORY',checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 child_pid=child,runner_pid=active['runner_pid'],optimizer_steps=probe['optimizer_steps'],effective_batches=probe['effective_batches'],
 peak_mps_driver_mib=probe['peak_mps_driver_mib'],recommended_max_memory_bytes=probe['mps_recommended_max_memory_bytes'],
 reason='user-authorized direction change to64 frames after128 working-set admission failed; preserve inputs/results and only stop registered child group')
with (HERE/'controller/owned_direction_stop.json').open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
os.killpg(child,signal.SIGTERM);print(json.dumps(receipt))
