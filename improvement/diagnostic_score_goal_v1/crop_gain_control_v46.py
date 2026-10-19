"""One explicit CPU/pilot128/remaining2280; no automatic fit or production."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import WORK, RUN, read, save, ref, bound, require, utc


def run(root, phase):
    cpu_path = root/'crop_gain_CPU_registration_44.json'
    cpu = read(cpu_path)
    require(bound(cpu['CPU_controller']) == Path(__file__).resolve(), 'Exact gain parent code')
    if phase == 'cpu':
        regpath, reg = cpu_path, cpu
        commands = [('first_combinations', [sys.executable, '-B', '-u', str(bound(cpu['preparation_code'])),
                                          '--root', str(root)], True)]
    else:
        require(phase in ('pilot128', 'remaining2280') and bool(os.environ.get('CUDA_VISIBLE_DEVICES')),
                'Explicit GPU phase retains physical assignment')
        original_path = root/'crop_gain_GPU_registration_46.json'
        original = read(original_path)
        regpath = original_path if phase == 'pilot128' else root/'crop_gain_remaining_admission_46.json'
        reg = read(regpath)
        require(original['CPU_registration'] == ref(cpu_path), 'GPU binds first complete new CPU purpose')
        gate = read(bound(original['input_acceptance']))
        require(gate['status'] == 'PASS_ALL_GAIN44_2408_ADOPT2000_NEW408_COMBINATIONS_FIRST_CPU_QA',
                'Every actual new combination first-QAd before GPU')
        budget = 900 if phase == 'pilot128' else 1800
        remain = (dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))
                  - dt.datetime.now(dt.timezone.utc)).total_seconds()
        require(remain > budget+180, 'All work remains inside original Goal deadline')
        wrapper = RUN/'resource_unlimited_v1_20261007/gpu_run.py'
        commands = [('GPU', [sys.executable, '-B', str(wrapper), '--name', reg['GPU_job'],
            '--max-seconds', str(budget), '--planned-output-bytes', '1900000000', '--capacity-reason',
            'First read-only final500 CROP training-source scores for separately registered continuous IoU utility target. No optimizer or labels. New408 combinations first-QAd, original2000/native crop/source encoded pixels adopted. Live shared resources and measured crop peak inspected, no fixed free-resource thresholds.',
            '--queue-seconds', '60', '--', sys.executable, '-B', '-u', str(bound(original['GPU_code'])),
            '--root', str(root), '--phase', phase], False),
            ('first_output_QA', [sys.executable, '-B', '-u', str(bound(original['review_code'])),
                                 '--root', str(root), '--phase', phase], True)]
    save(root/('crop_gain_'+phase+'_claim_46.json'), dict(utc=utc(), registration=ref(regpath), phase=phase,
        no_automatic_fit=True, no_automatic_production=True, no_automatic_retry=True))
    stages = []
    try:
        for name, argv, cpu_child in commands:
            env = dict(os.environ, OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                       PYTHONDONTWRITEBYTECODE='1')
            if cpu_child:
                env['CUDA_VISIBLE_DEVICES'] = ''
            with (root/('crop_gain_'+phase+'_'+name+'_46.log')).open('xb') as log:
                child = subprocess.Popen(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                         stdout=log, stderr=subprocess.STDOUT)
                ticks = Path('/proc', str(child.pid), 'stat').read_text().split(') ', 1)[1].split()[19]
                entry = dict(stage=name, argv=argv, pid=child.pid, start_ticks=ticks, CPU_child=cpu_child)
                save(root/('crop_gain_'+phase+'_'+name+'_launch_46.json'), entry)
                stages.append(entry)
                exit_code = child.wait()
                require(exit_code == 0, 'Actual gain '+phase+'/'+name+' exit '+str(exit_code))
            if name == 'GPU':
                resource_path = RUN/'controller'/(reg['GPU_job']+'.resource.json')
                record = read(resource_path)
                ledger = [json.loads(s) for s in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                          if s.strip() and json.loads(s).get('name') == reg['GPU_job']]
                require(ledger == [record] and record['status'] == 'completed' and record['exit_code'] == 0,
                        'Unique natural shared GPU terminal required')
                save(root/('crop_gain_'+phase+'_resource_46.json'), dict(record=record, resource=ref(resource_path),
                                                                       unique_ledger_entries=1))
        save(root/('crop_gain_'+phase+'_terminal_46.json'), dict(utc=utc(), exit_code=0, stages=stages,
            status='GAIN_REGISTERED_PHASES_NATURAL_COMPLETE_EXIT0', automatic_next_phase=False,
            automatic_fit=False, automatic_confirm=False, automatic_production=False))
    except BaseException as error:
        save(root/('crop_gain_'+phase+'_failure_46.json'), dict(utc=utc(), error=repr(error),
            traceback=traceback.format_exc(), stages=stages, preserve_all_success=True, automatic_retry=False))
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--phase', choices=['cpu', 'pilot128', 'remaining2280'], required=True)
    a = p.parse_args()
    run(a.root, a.phase)
