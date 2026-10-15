"""Unique natural GPU completion followed by first independent CPU replay."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import coarse as c


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root', required=True)
    root = c.checked_base(p.parse_args().root)
    c.require(os.environ.get('CUDA_VISIBLE_DEVICES') not in ('', None), 'Actual parent CUDA index required')
    state = root/'chain_01'; state.mkdir(exist_ok=False)
    c.save(state/'started.json', dict(pid=os.getpid(), actual_CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES']))
    try:
        cpu_env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
        subprocess.run([sys.executable, '-u', str(root/'admit.py'), '--root', str(root)], env=cpu_env, check=True)
        admission = c.read(root/'gpu_admission.json')
        wrapper = c.RUN/'resource_unlimited_v1_20261007/gpu_run.py'
        command = [sys.executable, str(wrapper), '--name', admission['gpu_job_name'], '--max-seconds', '1200',
            '--planned-output-bytes', str(8 << 20), '--capacity-reason',
            '38 same-B original native64 accepted inputs; actual cached inputs retained, only raw/token/done outputs and first independent replay proofs added; actual resources recorded before launch.',
            '--queue-seconds', '900', '--', sys.executable, '-u', str(root/'coarse.py'), 'infer', '--root', str(root)]
        c.save(root/'training_gpu_launch.json', dict(name=admission['gpu_job_name'], argv=command, source_input_lock_sha256=admission['source_input_lock_sha256']))
        subprocess.run(command, env=dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'), check=True)
        subprocess.run([sys.executable, '-u', str(root/'coarse.py'), 'replay', '--root', str(root)], env=cpu_env, check=True)
        c.save(state/'completion.json', dict(status='COMPLETE_NEW38_CHARADES_ORIGINAL_B_AND_INDEPENDENT_CPU_REPLAY_NOT_QUALITY',
            actual_model_calls=38, actual_independent_CPU_replays=38, optimizer_updates=0,
            gpu_completion_sha256=c.sha(root/'gpu_01/completion.json'), replay_completion_sha256=c.sha(root/'replay_01/completion.json')))
        print('COMPLETE_38_CALLS_AND_REPLAYS_NOT_QUALITY', flush=True)
    except BaseException as error:
        c.save(state/'failure.json', dict(error=repr(error), preserve_all_success=True, do_not_repeat_successful_calls=True))
        raise
