from pathlib import Path
import json,os,signal,subprocess,datetime as dt
HERE=Path(__file__).resolve().parent
active=json.loads((HERE/'controller/active_training.json').read_text())
assert active['phase']=='probe' and active['source_lock_sha256']=='25f7b9df1a0a452c9187043bbc7d9fe2bf4658d232afcfb9f1d7dd4c8cb30fc5'
child=active['child_pid'];command=subprocess.check_output(['/bin/ps','-p',str(child),'-o','command='],text=True).strip()
assert str(HERE/'train_mac.py') in command and os.getpgid(child)==child
probe=json.loads((HERE/'probe_01/progress.json').read_text())
assert probe['optimizer_steps']>=1
receipt=dict(status='STOP_OWNED_V5_AFTER_REAL_UPDATE_FOR_CACHE_AND_RNG_REPAIR',checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 child_pid=child,runner_pid=active['runner_pid'],optimizer_steps=probe['optimizer_steps'],effective_batches=probe['effective_batches'],
 peak_mps_driver_mib=probe['peak_mps_driver_mib'],reason='variable-length allocator cache exceeds live recommended memory; equivalence tests altered initialization RNG; new v6 clears cache and restores registered seed')
with (HERE/'controller/owned_repair_stop.json').open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
os.killpg(child,signal.SIGTERM)
print(json.dumps(receipt))
