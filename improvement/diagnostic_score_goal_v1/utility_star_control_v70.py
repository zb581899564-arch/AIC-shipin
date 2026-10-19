"""One explicitly registered star GPU phase then its independent CPU first QA.

No CPU preparation, automatic remaining, confirmation or production dispatch.
Only new69/70 paths are writable; successful old55 stages are adopted.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

_support = Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir():
    sys.path.insert(0, str(_support))
from pair_common import WORK, RUN, read, save, ref, bound, require, utc


def phase_contract(root, phase):
    require(phase in ('pilot4', 'remaining796'), 'Only explicit new4 or remaining796 phase')
    original_path = root/'utility_star_GPU_registration_69.json'; original = read(original_path)
    require(original['schema'] == 'UTILITY_CONNECTED_STAR_CONTINUATION_V69'
            and bound(original['controller_code']) == Path(__file__).resolve(), 'Exact registered70 parent')
    gate = read(bound(original['input_acceptance']))
    require(gate['status'] == 'PASS_UTILITY68_CONNECTED_STAR_ALL_INPUTS_FIRST_CPU_QA'
            and gate['prepared'] == original['prepared'] and gate['registration'] == original['CPU_registration'],
            'Actual68 input gate before any new GPU')
    registration_path = original_path
    if phase == 'remaining796':
        registration_path = root/'utility_star_remaining_admission_69.json'
    registration = read(registration_path)
    if phase == 'remaining796':
        prior = read(bound(registration['pilot_output_acceptance']))
        require(registration['schema'] == 'UTILITY_CONNECTED_STAR_REMAINING796_V69'
                and registration['original_GPU_registration'] == ref(original_path)
                and registration['expected_remaining_updates'] == 796
                and all(registration[k] == original[k] for k in ('GPU_code', 'math_code', 'prepared', 'input_acceptance'))
                and prior['status'] == 'PASS_STAR_GLOBAL504_FIRST_ENGINEERING_QA'
                and prior['registration'] == ref(original_path)
                and prior['engineering']['global_updates'] == 504
                and prior['engineering']['progress'] == registration['immutable_pilot_progress']
                and prior['pilot_completion'] == registration['pilot_completion'], 'Only accepted complete new504 may continue')
    budget = registration['max_seconds']
    require(type(budget) is int and budget > 0 and isinstance(registration['GPU_job'], str) and registration['GPU_job'],
            'Explicit per-phase time budget and unique GPU job')
    return original, registration, registration_path, budget


def run(root, phase):
    root = Path(root).resolve()
    require(root.is_relative_to(WORK) and bool(os.environ.get('CUDA_VISIBLE_DEVICES')),
            'Authorized Linux root; GPU parent retains physical CUDA index')
    original, reg, registration_path, budget = phase_contract(root, phase)
    remaining = (dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00'))-dt.datetime.now(dt.timezone.utc)).total_seconds()
    require(remaining > budget+120, 'Leave independent QA inside Goal deadline')
    wrapper = RUN/'resource_unlimited_v1_20261007/gpu_run.py'
    gpu = [sys.executable, '-B', str(wrapper), '--name', reg['GPU_job'], '--max-seconds', str(budget),
        '--planned-output-bytes', '1000000000', '--capacity-reason',
        'Registered complete500 Adam/RNG continuation on connected-star supervision. New first4 measures actual dual-order graph resources; remaining796 is separately admitted. Reuses accepted pixels, no old successful phase repeat; live shared GPU checks remain dynamic.',
        '--queue-seconds', '60', '--', sys.executable, '-B', '-u', str(bound(original['GPU_code'])),
        '--root', str(root), '--phase', phase]
    commands = [('GPU', gpu, False), ('first_output_QA', [sys.executable, '-B', '-u', str(bound(original['review_code'])),
        '--root', str(root), '--stage', 'pilot' if phase == 'pilot4' else 'final'], True)]
    save(root/('utility_star_'+phase+'_parent_claim_70.json'), dict(utc=utc(), pid=os.getpid(),
        registration=ref(registration_path), phase=phase, original55_remains_STOP=True))
    entries = []
    try:
        for name, argv, is_cpu in commands:
            env = dict(os.environ, OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
            if is_cpu:
                env['CUDA_VISIBLE_DEVICES'] = ''
            with (root/('utility_star_'+phase+'_'+name+'_70.log')).open('xb') as log:
                process = subprocess.Popen(argv, cwd=root, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
                ticks = Path('/proc', str(process.pid), 'stat').read_text().split(') ', 1)[1].split()[19]
                entry = dict(stage=name, argv=argv, pid=process.pid, start_ticks=ticks, CPU_child=is_cpu)
                save(root/('utility_star_'+phase+'_'+name+'_launch_70.json'), entry); entries.append(entry)
                code = process.wait()
                save(root/('utility_star_'+phase+'_'+name+'_exit_70.json'), dict(utc=utc(), actual_exit_code=code, entry=entry))
                require(code == 0, 'Actual star '+phase+'/'+name+' exit '+str(code))
            if name == 'GPU':
                resource = RUN/'controller'/(reg['GPU_job']+'.resource.json'); record = read(resource)
                ledger = [json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                          if line.strip() and json.loads(line).get('name') == reg['GPU_job']]
                require(ledger == [record] and record['status'] == 'completed' and record['exit_code'] == 0,
                        'Unique actual naturally completed shared GPU job/ledger')
                save(root/('utility_star_'+('pilot' if phase == 'pilot4' else 'remaining')+'_resource_receipt_70.json'),
                     dict(record=record, resource=ref(resource), unique_ledger_entries=1))
        save(root/('utility_star_'+phase+'_terminal_70.json'), dict(status='REGISTERED_STAR_PHASE_NATURAL_COMPLETE_EXIT0',
            utc=utc(), exit_code=0, entries=entries, automatic_remaining=False, confirm_started=False, production_started=False))
    except BaseException as error:
        save(root/('utility_star_'+phase+'_parent_failure_70.json'), dict(utc=utc(), error=repr(error),
            traceback=traceback.format_exc(), entries=entries, preserve_all_success=True, no_automatic_retry=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--phase', choices=('pilot4', 'remaining796'), required=True)
    args = parser.parse_args(); run(args.root, args.phase)
