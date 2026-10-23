"""Bounded independent information experiment after the fixed joint4 STOP."""
import json
import os
from pathlib import Path
import subprocess
import traceback

from frozen_branch46 import RUN
from speech_task60 import OUT
from t_io import ROOT, WORK, check, identity, read, save

CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'


def execute(script, phase, seconds=None):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if script == 'speech_gpu60.py':
        command.append(phase)
    name = phase if seconds is not None else Path(script).stem
    job = 'T_whole_speech_visual_' + phase + '_20261022_v60'
    if seconds is not None:
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
        if apps.strip():
            raise RuntimeError('External GPU compute present; preserve all accepted inputs')
        save(OUT / (phase + '_resource_admission.json'), dict(apps=apps,
            GPU=subprocess.check_output(['nvidia-smi'], text=True), RAM=subprocess.check_output(['free', '-b'], text=True),
            disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True),
            basis='Original oneTIME inference, actual accepted prefixes7437..10401, prior20.7GB peak on48GB, no optimizer; short outputs estimate100MB'))
        command = [str(PY), '-B', str(WRAPPER), '--name', job, '--max-seconds', str(seconds),
            '--planned-output-bytes', '100000000', '--capacity-reason',
            'First aligned/shifted whole-source speech observation with same native visual inputs; all original50/365BASE and identical VERIFY tasks adopted',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (name + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if seconds is not None else '', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (name + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (name + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Actual new information phase failed: ' + name)
    if seconds is None:
        return 0.
    record = read(RUN / 'controller' / (job + '.resource.json'))
    rows = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if record['status'] != 'completed' or record['exit_code'] != 0 or [row for row in rows if row.get('name') == job] != [record]:
        raise ValueError('Unique natural information GPU terminal/ledger mismatch')
    return record['charged_seconds']


def main():
    OUT.mkdir()
    if read(ROOT / 'development_remaining55/completion.json')['state'] != 'STOP_FROZEN_JOINT4_DEVELOPMENT':
        raise ValueError('Prior scientific STOP not established')
    cpu = read(ROOT / 'speech_inputs59/completion.json')
    if cpu['new_inputs'] != 100 or cpu['state'] != 'FIRST_ALL100_AV_TEXT_PREFIXES_PASS_NO_MODEL_QUALITY':
        raise ValueError('Complete real new CPU input gate not passed')
    protocol = identity(CODE / 'speech_protocol60.json')
    names = ['speech_scope58.py', 'speech_text59.py', 'speech_inputs59.py', 'speech_task60.py', 'speech_gpu60.py',
        'speech_prepare60.py', 'speech_review60.py', 'speech_development60.py', 'development_call46.py',
        'development_data46.py', 'development_prepare55.py', 'development_verify46.py', 'frozen_branch46.py']
    save(OUT / 'registration.json', dict(protocol=protocol, complete_CPU=identity(ROOT / 'speech_inputs59/completion.json'),
        prior_STOP=identity(ROOT / 'development_remaining55/completion.json'), no_old_profile_gate_modified=True,
        GPU_development_aggregate_max=2400, new_training=0, no_automatic_confirmation_or_production=True))
    save(OUT / 'source_input_lock.json', dict(protocol=protocol,
        code={name: identity(CODE / name) for name in names},
        original_dependencies=read(ROOT / 'development51/source_input_lock.json')['original_dependencies'],
        actual_CPU=identity(ROOT / 'speech_inputs59/completion.json'), wrapper=identity(WRAPPER)))
    first = execute('speech_gpu60.py', 'coarse', 2400)
    execute('speech_prepare60.py', 'prepare')
    cpu = read(OUT / 'verify_CPU_completion.json')
    if cpu['actual_missing_VERIFY_calls']:
        remaining = int(2400 - first)
        if remaining <= 0:
            raise RuntimeError('Fixed new development aggregate budget exhausted before first VERIFY')
        second = execute('speech_gpu60.py', 'verify', remaining)
    else:
        second = 0.
        save(OUT / 'verify_GPU_completion.json', dict(outputs=cpu['adopted_VERIFY_outputs'],
            actual_calls=0, adopted_calls=len(cpu['adopted_VERIFY_outputs']), no_model_job_started=True))
    execute('speech_review60.py', 'review')
    save(OUT / 'completion.json', dict(state=read(OUT / 'review.json')['state'],
        review=identity(OUT / 'review.json'), independent_CPU=identity(OUT / 'independent_CPU_audit.json'),
        actual_GPU_seconds=first + second, all_goal_GPU_seconds=6404.41972579807 + first + second,
        new_training=0, new_packages=0,
        next='Only if fixed dev gatesPASS, freeze this information method before first original four-publisher confirmation and cost admission'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
