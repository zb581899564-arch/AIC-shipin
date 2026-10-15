"""Exactly one admitted GPU job and first independent replay; no retries."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

BASE = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/local_boundary_v4/dev')
sys.path.insert(0, str(BASE.parent/'code'))
import lb_io as io
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'


def main():
    io.host(cpu=False)
    admission = io.read(BASE/'gpu_admission.json')
    accepted = io.read(BASE/'gpu_admission_independent_check_01.json')
    if accepted['gpu_admission_sha256'] != io.sha(BASE/'gpu_admission.json'):
        raise ValueError('Actual independent admission missing or changed')
    if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(admission['deadline']):
        raise ValueError('No new development experiment after the goal deadline')
    out = BASE/'chain_01'
    out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(),
        argv=sys.argv, admission_sha256=io.sha(BASE/'gpu_admission.json'),
        parent_actual_CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),
        actual_model_calls_budget=37, original_successful_stages_not_repeated=True))
    name = admission['gpu_job_name']
    steps = [('gpu', [PY, str(io.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
        '--name', name, '--max-seconds', '1500', '--planned-output-bytes', str(8 << 20),
        '--capacity-reason', '37 independently accepted native64 CPU inputs and3 typed structural original points; same fixed TIME B0 <=22.4GiB actual prior peak on Ada46068MiB, currently182MiB0% and120GB available RAM/145GB disk. No active Java or GPU observed; shared lock protects external jobs. Inputs already real and never re-encoded; first independent replay follows natural terminal.',
        '--queue-seconds', '900', '--', PY, '-u', str(BASE.parent/'code/infer_local_boundaries.py'), '--base', str(BASE)]),
        ('replay', [PY, '-u', str(BASE.parent/'code/replay_local_boundaries.py'), '--base', str(BASE)])]
    stage = None
    try:
        for stage, argv in steps:
            env = os.environ.copy()
            if stage == 'replay':
                env['CUDA_VISIBLE_DEVICES'] = ''
            env.update(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
            io.save(out/(stage+'_command.json'), dict(argv=argv, child_CUDA_VISIBLE_DEVICES=env.get('CUDA_VISIBLE_DEVICES'), utc=io.utc()))
            with (out/(stage+'.log')).open('x') as log:
                result = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT)
            io.save(out/(stage+'_exit.json'), dict(exit_code=result.returncode, utc=io.utc()))
            if result.returncode != 0:
                raise RuntimeError(stage+' failed; preserve successes; no automatic retry')
        io.save(out/'completion.json', dict(status='COMPLETE_REAL_DEV37_TIME_AND_FIRST_INDEPENDENT_CPU_REPLAY_NOT_QUALITY',
            actual_model_calls=37, nominal_endpoints=40, structural_skips=3, new_ZIPs=0, science_quality_claim=False,
            gpu_completion_sha256=io.sha(BASE/'gpu_01/completion.json'),
            independent_replay_completion_sha256=io.sha(BASE/'replay_01/completion.json'),
            export_sha256=io.sha(BASE/'boundary_prediction_export.json'), utc=io.utc()))
    except BaseException as error:
        io.save(out/'failure.json', dict(stage=stage, error=repr(error), traceback=traceback.format_exc(),
            preserve_success=True, successful_model_calls_must_not_repeat=True, utc=io.utc()))
        raise


if __name__ == '__main__':
    main()
