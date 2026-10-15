"""Main-agent unique controller; separate from frozen three-file ablation code."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

C = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1')
R = C/'boundary_activation_ablation_v1'
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2); f.flush(); os.fsync(f.fileno())


if __name__ == '__main__':
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '0'
    state = R/'chain_01'; state.mkdir(exist_ok=False)
    save(state/'started.json', dict(pid=os.getpid(), controller_sha256=sha(Path(__file__)), utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    try:
        protocol = read(R/'protocol.json'); admission = read(R/'admission.json')
        assert admission['status'] == 'PASS_PAIRED_2CALL_ACTIVATION_INPUT_REUSE_NOT_GPU_PERMISSION_OR_QUALITY'
        save(R/'gpu_admission.json', dict(status='PASS_INDEPENDENT_BOUNDARY_ACTIVATION_GPU_ADMISSION',
            source_lock_sha256=sha(R/'source_lock.json'), input_admission_sha256=sha(R/'admission.json'),
            actual_model_call_budget=2, gpu_job_name=protocol['gpu_job_name'], actual_physical_parameters=8782459120,
            activated_base_parameters=8767123696, optimizer_updates=0, controller_sha256=sha(Path(__file__))))
        cmd = [sys.executable, str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
            '--name', protocol['gpu_job_name'], '--max-seconds', '900', '--planned-output-bytes', str(4 << 20),
            '--capacity-reason', 'New two boundary activation calls on reused successful exact inputs; measured TIME smoke peak21114MiB. Extra frozen-weight hashing budget, no new media or processor inputs. Queue behind current Charades38 job, no external task interruption.',
            '--queue-seconds', '900', '--', sys.executable, '-u', str(R/'run_ablation.py'), '--root', str(R), '--stage', 'infer']
        save(R/'gpu_launch.json', dict(argv=cmd, name=protocol['gpu_job_name'], controller_sha256=sha(Path(__file__))))
        subprocess.run(cmd, check=True)
        subprocess.run([sys.executable, '-u', str(R/'run_ablation.py'), '--root', str(R), '--stage', 'replay'],
            check=True, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'))
        save(state/'completion.json', dict(status='COMPLETE_NEW_TWO_ACTIVATION_CALLS_AND_OUTPUT_REPLAYS_NOT_QUALITY',
            model_calls=2, new_media_decodes=0, new_processor_encodes=0,
            gpu_completion_sha256=sha(R/'gpu_01/completion.json'), replay_completion_sha256=sha(R/'replay_01/completion.json'),
            comparisons_sha256=sha(R/'activation_behavior_export.json')))
    except BaseException as e:
        save(state/'failure.json', dict(error=repr(e), preserve_all_old_and_new_success=True, do_not_repeat_calls=True))
        raise
