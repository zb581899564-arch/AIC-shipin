"""One explicitly admitted new-gain CPU or native19 GPU/first-QA phase."""
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
    cpu_path = root/'crop_gain_confirm_CPU_registration_49.json'
    cpu = read(cpu_path)
    require(bound(cpu['CPU_controller']) == Path(__file__).resolve(), 'Exact new confirm controller')
    if phase == 'cpu':
        regpath, reg = cpu_path, cpu
        commands = [('first_CPU_inputs', [sys.executable, '-B', '-u', str(bound(cpu['preparation_code'])),
                                        '--root', str(root)], True)]
    else:
        require(phase == 'readonly' and bool(os.environ.get('CUDA_VISIBLE_DEVICES')), 'Explicit assigned GPU phase')
        regpath = root/'crop_gain_confirm_GPU_registration_50.json'
        reg = read(regpath)
        require(reg['CPU_registration'] == ref(cpu_path), 'Exact new49 CPU registration binding')
        left = (dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))
                - dt.datetime.now(dt.timezone.utc)).total_seconds()
        require(left > 1080, 'Full bounded first readout and review inside Goal window')
        require(read(bound(reg['screen_result']))['confirm_admitted'] is True, 'Actual new47 screen qualification')
        gate = read(bound(reg['input_acceptance']))
        require(gate['sources'] == 19 and gate['first_independent_pixels_text_native_QA'] is True,
                'All real new native inputs before GPU')
        commands = [('GPU', [sys.executable, '-B', str(RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
            '--name', reg['GPU_job'], '--max-seconds', '900', '--planned-output-bytes', '220000000',
            '--capacity-reason', 'New gain-critic native19 independent scope; every first input QA passed. Immutable final500 CROP only, at most247 triplets, no optimizer or labels, adopt original19 BASE. Live shared resources and prior measured17.6GB inference inspected.',
            '--queue-seconds', '60', '--', sys.executable, '-B', '-u', str(bound(reg['GPU_code'])),
            '--root', str(root)], False),
            ('first_output_QA', [sys.executable, '-B', '-u', str(bound(reg['review_code'])),
                                 '--root', str(root)], True)]
    save(root/('crop_gain_confirm_'+phase+'_claim_50.json'), dict(utc=utc(), registration=ref(regpath),
        phase=phase, automatic_next_phase=False, automatic_production=False, automatic_retry=False))
    stages = []
    try:
        for name, argv, cpu_child in commands:
            env = dict(os.environ, OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                       PYTHONDONTWRITEBYTECODE='1')
            if cpu_child:
                env['CUDA_VISIBLE_DEVICES'] = ''
            with (root/('crop_gain_confirm_'+phase+'_'+name+'_50.log')).open('xb') as log:
                child = subprocess.Popen(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                         stdout=log, stderr=subprocess.STDOUT)
                ticks = Path('/proc', str(child.pid), 'stat').read_text().split(') ', 1)[1].split()[19]
                entry = dict(stage=name, argv=argv, pid=child.pid, start_ticks=ticks, CPU_child=cpu_child)
                save(root/('crop_gain_confirm_'+phase+'_'+name+'_launch_50.json'), entry)
                stages.append(entry)
                code = child.wait()
                require(code == 0, 'Actual gain confirm '+name+' exit '+str(code))
            if name == 'GPU':
                rp = RUN/'controller'/(reg['GPU_job']+'.resource.json')
                record = read(rp)
                ledger = [json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                          if line.strip() and json.loads(line).get('name') == reg['GPU_job']]
                require(ledger == [record] and record['status'] == 'completed' and record['exit_code'] == 0,
                        'Natural unique shared GPU terminal required')
                save(root/'crop_gain_confirm_resource_50.json', dict(record=record, resource=ref(rp), unique_ledger_entries=1))
        save(root/('crop_gain_confirm_'+phase+'_terminal_50.json'), dict(utc=utc(), exit_code=0,
            status='GAIN_CONFIRM_REGISTERED_PHASE_NATURAL_COMPLETE_EXIT0', stages=stages,
            automatic_comparison=False, automatic_production=False))
    except BaseException as error:
        save(root/('crop_gain_confirm_'+phase+'_failure_50.json'), dict(utc=utc(), error=repr(error),
            traceback=traceback.format_exc(), stages=stages, preserve_all_success=True, automatic_retry=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--phase', choices=['cpu', 'readonly'], required=True)
    args = parser.parse_args()
    run(args.root, args.phase)
