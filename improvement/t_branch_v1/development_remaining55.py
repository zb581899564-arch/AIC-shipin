"""Adopt complete150greedy/365BASE and31 prefixes; only remaining dev work."""
import json
import os
from pathlib import Path
import subprocess
import traceback

import development51 as original
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'development_remaining55'
OLD = ROOT / 'development51'
OLD_JOB = 'T_joint4_dev_greedy_BASE_20261022_v51'
JOB = 'T_joint4_dev_only_VERIFY_remaining_20261022_v55'
CODE = Path(__file__).parent


def execute(stage, remaining=None):
    command = ([str(original.previous.PY), '-B', '-u', str(CODE / 'development_prepare55.py')]
        if stage == 'prepare' else [str(original.previous.PY), '-B', '-u', str(CODE / 'development_run55.py'), stage])
    if remaining is not None:
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
        if apps.strip():
            raise RuntimeError('External GPU compute exists; preserve accepted CPU inputs')
        save(OUT / 'resource_admission.json', dict(apps=apps,
            GPU=subprocess.check_output(['nvidia-smi'], text=True), RAM=subprocess.check_output(['free', '-b'], text=True),
            disk=subprocess.check_output(['df', '-B1', str(ROOT)], text=True),
            basis='Only unique originalTIME VERIFY tasks after first CPU acceptance;150greedy/365BASE adopted, no repeated source forward or training'))
        command = [str(original.previous.PY), '-B', str(original.previous.WRAPPER), '--name', JOB,
            '--max-seconds', str(remaining), '--planned-output-bytes', '100000000',
            '--capacity-reason', 'Only first distinct candidate-specific VERIFY; original fixed dev2400 minus actual1399.546, old completed outputs/CPU inputs adopted',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (stage + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if remaining is not None else '', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (stage + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (stage + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Actual remaining development stage failed: ' + stage)


def main():
    OUT.mkdir()
    if read(OLD / 'verify_prepare_terminal.json')['exit_code'] != 1:
        raise ValueError('Expected first independent CPU interface failure absent')
    log = (OLD / 'verify_prepare.log').read_text()
    if "KeyError: 'allowed'" not in log or (OLD / 'verify_GPU_completion.json').exists():
        raise ValueError('Not exact before-model VERIFY interface recovery')
    resource = read(original.previous.RUN / 'controller' / (OLD_JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [row for row in ledger if row.get('name') == OLD_JOB] != [resource]:
        raise ValueError('Actual complete150greedy/365BASE natural terminal differs')
    remaining = int(2400 - resource['charged_seconds'])
    if remaining <= 0:
        raise ValueError('Original fixed development budget exhausted')
    lock = read(OLD / 'source_input_lock.json')
    for ref in lock['code'].values():
        check(ref)
    for name in ['development_remaining55.py', 'development_run55.py', 'development_prepare55.py']:
        lock['code'][name] = identity(CODE / name)
    save(OUT / 'registration.json', dict(actual_failure=identity(ROOT / 'development_follow51/failure.json'),
        actual_trace=identity(OLD / 'verify_prepare.log'), actual_completed_GPU=identity(original.previous.RUN / 'controller' / (OLD_JOB + '.resource.json')),
        source_model_calls_adopted=150, BASE_batches_adopted=365, CPU_prefixes_adopted=31,
        prior_development_GPU_seconds=resource['charged_seconds'], original_development_limit=2400,
        remaining_GPU_seconds=remaining, recovery='Read actual allowed list from persisted score payload; old acceptance lacked duplicate field',
        no_scientific_gate_or_prompt_or_parameter_change=True, new_training=0))
    lock['original_execution_lock'] = identity(OLD / 'source_input_lock.json')
    lock['registration'] = identity(OUT / 'registration.json')
    save(OUT / 'source_input_lock.json', lock)
    for name in ['coarse_and_BASE_GPU_completion.json', 'coarse_CPU_completion.json']:
        save(OUT / name, dict(read(OLD / name), adopted_original_result=identity(OLD / name), new_model_calls=0))
    execute('prepare')
    save(OUT / 'verify_source_input_lock.json', dict(**lock,
        all_actual_VERIFY_CPU=identity(OUT / 'verify_CPU_completion.json'),
        prior_development_GPU_seconds=resource['charged_seconds'], remaining_GPU_seconds=remaining))
    execute('verify', remaining)
    final = read(original.previous.RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if final['status'] != 'completed' or final['exit_code'] != 0 or [row for row in ledger if row.get('name') == JOB] != [final]:
        raise ValueError('Unique remaining VERIFY natural resource/ledger mismatch')
    execute('review')
    prior_T1 = read(ROOT / 'joint_continue50/completion.json')['cumulative_T1_seconds']
    total = resource['charged_seconds'] + final['charged_seconds']
    save(OUT / 'completion.json', dict(state=read(OUT / 'review.json')['state'],
        review=identity(OUT / 'review.json'), independent_CPU=identity(OUT / 'independent_CPU_audit.json'),
        actual_GPU_seconds=total, T1_cumulative_GPU_seconds=prior_T1 + total,
        actual_failed51_CPU_preserved=True, new_packages=0,
        next='Only fixed full4publisher confirmation if unchanged development gates PASS and cost fits actual remainingT1'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
