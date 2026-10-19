"""Explicit conditional confirm CPU or GPU stage; never production or retry."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import WORK, RUN, read, save, ref, bound, require, utc


def run(root, phase):
    cpu_path = root/'crop_confirm_CPU_registration_36.json'
    cpu = read(cpu_path)
    require(bound(cpu['CPU_controller']) == Path(__file__).resolve(), 'Exact separately frozen controller')
    native = read(bound(cpu['native_screen_result']))
    require(native['status'] == 'PASS_NATIVE_CROP_SCREEN_ONLY' and native['confirm_admitted'] is True,
            'Native screen has not qualified confirmation')
    if phase == 'cpu':
        regpath, reg = cpu_path, cpu
        commands = [('first_inputs', [sys.executable, '-B', '-u', str(bound(cpu['preparation_code'])),
                                      '--root', str(root)], True)]
    else:
        require(phase == 'gpu' and bool(os.environ.get('CUDA_VISIBLE_DEVICES')), 'Explicit GPU phase/assignment')
        regpath = root/'crop_confirm_GPU_registration_37.json'
        reg = read(regpath)
        require(reg['CPU_registration'] == ref(cpu_path), 'New GPU must bind completed CPU registration')
        gate = read(bound(reg['input_acceptance']))
        require(gate['status'] == 'PASS_ALL_NATIVE_CONFIRM19_NEW_CROP_TRIPLETS_FIRST_CPU_QA_V36',
                'All first actual confirm inputs must pass before GPU')
        import datetime as dt
        remain = (dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))
                  - dt.datetime.now(dt.timezone.utc)).total_seconds()
        require(remain > 1380, 'Reserve all confirm, independent QA and delivery inside Goal deadline')
        wrapper = RUN/'resource_unlimited_v1_20261007/gpu_run.py'
        commands = [('GPU', [sys.executable, '-B', str(wrapper), '--name', reg['GPU_job'],
            '--max-seconds', '1200', '--planned-output-bytes', '600000000', '--capacity-reason',
            'Native screen qualified fixed CROP final500. Remaining19 accepted sources only, all new triplet input QA complete. Live shared resources and measured crop grids/peak checked; no training or fixed free-resource thresholds.',
            '--queue-seconds', '60', '--', sys.executable, '-B', '-u', str(bound(reg['GPU_code'])),
            '--root', str(root)], False),
            ('first_output_QA_comparison', [sys.executable, '-B', '-u', str(bound(reg['review_code'])),
                                           '--root', str(root)], True)]
    save(root/('crop_confirm_'+phase+'_claim_37.json'), dict(utc=utc(), registration=ref(regpath), phase=phase,
        no_automatic_production=True, no_automatic_retry=True))
    entries = []
    try:
        for name, argv, cpu_child in commands:
            env = dict(os.environ, OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                       PYTHONDONTWRITEBYTECODE='1')
            if cpu_child:
                env['CUDA_VISIBLE_DEVICES'] = ''
            with (root/('crop_confirm_'+phase+'_'+name+'_37.log')).open('xb') as log:
                child = subprocess.Popen(argv, cwd=root, env=env, stdin=subprocess.DEVNULL,
                                         stdout=log, stderr=subprocess.STDOUT)
                ticks = Path('/proc', str(child.pid), 'stat').read_text().split(') ', 1)[1].split()[19]
                entry = dict(stage=name, argv=argv, pid=child.pid, start_ticks=ticks, CPU_child=cpu_child)
                save(root/('crop_confirm_'+phase+'_'+name+'_launch_37.json'), entry)
                entries.append(entry)
                exit_code = child.wait()
                require(exit_code == 0, 'Actual conditional confirm '+name+' exit '+str(exit_code))
            if name == 'GPU':
                import json
                resource_path = RUN/'controller'/(reg['GPU_job']+'.resource.json')
                record = read(resource_path)
                ledger = [json.loads(s) for s in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                          if s.strip() and json.loads(s).get('name') == reg['GPU_job']]
                require(ledger == [record] and record['status'] == 'completed' and record['exit_code'] == 0,
                        'Unique natural GPU completed/exit0 terminal required')
                save(root/'crop_confirm_resource_37.json', dict(record=record, resource=ref(resource_path),
                                                               unique_ledger_entries=1))
        save(root/('crop_confirm_'+phase+'_terminal_37.json'), dict(utc=utc(), exit_code=0, entries=entries,
            status='CONDITIONAL_CONFIRM_STAGES_NATURAL_EXIT0', automatic_next_stage=False,
            automatic_production=False, automatic_package=False))
    except BaseException as error:
        save(root/('crop_confirm_'+phase+'_failure_37.json'), dict(utc=utc(), error=repr(error),
            traceback=traceback.format_exc(), entries=entries, preserve_all_success=True, automatic_retry=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--phase', choices=['cpu', 'gpu'], required=True)
    args = parser.parse_args()
    run(args.root, args.phase)
