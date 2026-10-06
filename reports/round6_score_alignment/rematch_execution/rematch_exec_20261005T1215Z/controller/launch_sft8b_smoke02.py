"""One exclusive detached registered B GPU wrapper, after repaired A acceptance."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL, HERE = RUN/'controller', RUN/'temporal_sft8b_v1'
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok, message):
    if not ok:
        raise RuntimeError(message)

if __name__ == '__main__':
    admission_path = CTRL/'sft8b_smoke_02.admission.json'
    admission = json.loads(admission_path.read_text())
    config_path = HERE/'smoke_config_PREPARED_NOT_ADMITTED.json'
    config = json.loads(config_path.read_text())
    require(sha(admission_path) == '886a9181214d36e6e847e4b378de3ac7451a4b4f332ae910da1cd6ca940e9791', 'registered admission changed')
    require(sha(config_path) == admission['config_sha256'] and config['updates'] == 5 and
            config['grad_accum'] == 16 and config['max_wall_seconds'] == 1800, 'registered fixed smoke recipe changed')
    lock_path = HERE/'smoke_source_lock.json'
    require(sha(lock_path) == '806deb54de18835ee6841a1a921f015cd0d8b82ad65268e016af3144cb19ff93', 'B source lock changed')
    for name, digest in json.loads(lock_path.read_text())['files'].items():
        require(sha(HERE/name) == digest, 'B source/input changed: '+name)
    require(sha(CTRL/'gpu_run.py') == '0cddca5f85a2a885ee2ac50e9193819b58dead39b6b561a30cb1c97f192ca961', 'shared runner changed')
    for name in ['sft8b_smoke02.launch.json', 'rematch_sft8b_smoke_02.resource.json']:
        require(not (CTRL/name).exists(), 'existing registered job; no duplicate: '+name)
    with (CTRL/'sft8b_smoke02.launch_registration.json').open('x') as stream:
        json.dump({'admission_sha256': sha(admission_path), 'launcher_sha256': sha(__file__)}, stream)
    command = [sys.executable, '-B', '-u', str(CTRL/'gpu_run.py'), '--name', 'rematch_sft8b_smoke_02',
        '--max-seconds', '1800', '--planned-output-bytes', str(admission['planned_output_bytes']),
        '--capacity-reason', 'fixed_8B_interval_SFT_5_updates_80_effective_batches_actual_adapter_evidence_plan',
        '--queue-seconds', '1800', '--', sys.executable, '-B', '-u', str(HERE/'train_sft.py'),
        '--config', str(config_path), '--admission', str(admission_path)]
    with (CTRL/'sft8b_smoke02.background.log').open('xb') as log:
        child = subprocess.Popen(command, cwd=str(HERE), stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(stage='DETACHED_REGISTERED_SFT_GPU_WRAPPER_STARTED', pid=child.pid,
        started_utc=dt.datetime.now(dt.timezone.utc).isoformat(), admission_sha256=sha(admission_path),
        launcher_sha256=sha(__file__), fixed_updates=5, fixed_effective_batches=80,
        formal_c_bce_admitted=False, full_training_started=False, uploaded=False)
    with (CTRL/'sft8b_smoke02.launch.json').open('x') as stream:
        stream.write(json.dumps(receipt, indent=2)+'\n')
    time.sleep(.5)
    require(child.poll() is None or (CTRL/'rematch_sft8b_smoke_02.resource.json').exists(), 'wrapper exited before evidence')
    print(json.dumps(receipt), flush=True)
