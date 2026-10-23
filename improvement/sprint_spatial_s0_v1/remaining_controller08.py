"""Adopt80 CPU inputs and exact weight after a zero-forward import failure."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback
from control import ROOT, PY, WRAPPER, RESOURCE, LEDGER, read, write, reference, checked


def import_contract():
    code = "import runpy,sys,torch;runpy.run_path('" + str(ROOT / 'code_v8/score80.py') + "',run_name='s0_import_contract');import runtime,legacy_align;assert runtime.__file__=='" + str(ROOT / 'code_v7/runtime.py') + "';assert not torch.cuda.is_initialized();print(runtime.__file__,legacy_align.__file__)"
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='')
    env.pop('PYTHONPATH', None)
    done = subprocess.run([str(PY), '-B', '-c', code], env=env, capture_output=True, text=True)
    write(ROOT / 'clean_environment_import08.json', dict(exit_code=done.returncode, stdout=done.stdout, stderr=done.stderr,
        PYTHONPATH_removed=True, research_forward_calls=0))
    if done.returncode:
        raise ValueError('Clean child environment import contract fails before GPU')


def run_gpu(seconds):
    name = 's0_author_gaic80_remaining08_20261021_v1'
    if (RESOURCE / (name + '.resource.json')).exists():
        raise ValueError('Remaining unique job already exists')
    GPU = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.free,memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True).strip()
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True).strip()
    admission = dict(host=socket.gethostname(), GPU=GPU, outside_tasks=apps, disk_free=shutil.disk_usage(ROOT).free,
        registered_input_estimate=read(ROOT / 'resource_admission.json')['model_and_registered_activation_estimate_bytes'])
    write(ROOT / 'remaining_resource08.json', admission)
    if admission['host'] != 'inspur-NP5570M5' or int(GPU.split(',')[0]) * 1024**2 < admission['registered_input_estimate']:
        raise ValueError('Actual current capacity cannot hold this registered profile')
    command = [str(PY), '-B', str(WRAPPER), '--name', name, '--max-seconds', str(seconds),
        '--planned-output-bytes', '134217728', '--capacity-reason', json.dumps(admission), '--queue-seconds', '0', '--',
        str(PY), '-u', '-B', str(ROOT / 'code_v8/score80.py')]
    with (ROOT / 'remaining_GPU08.log').open('x') as log:
        child = subprocess.Popen(command, cwd=ROOT, env=dict(os.environ, CUDA_VISIBLE_DEVICES='0'),
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        write(ROOT / 'remaining_GPU08_launch.json', dict(pid=child.pid, argv=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        code = child.wait()
    write(ROOT / 'remaining_GPU08_terminal.json', dict(exit_code=code))
    record = read(RESOURCE / (name + '.resource.json'))
    ledger = [r for r in map(json.loads, LEDGER.read_text().splitlines()) if r.get('name') == name]
    if code or record['status'] != 'completed' or ledger != [record]:
        raise ValueError('Real remaining GPU failure/unique ledger mismatch')
    return record


def main():
    write(ROOT / 'remaining08_claim.json', dict(pid=os.getpid()))
    prior_name = 's0_author_gaic80_dev_20261021_v1'
    failed = read(RESOURCE / (prior_name + '.resource.json'))
    trace = (RESOURCE / (prior_name + '.log')).read_text()
    if failed['status'] != 'failed' or "ModuleNotFoundError: No module named 'runtime'" not in trace:
        raise ValueError('Only known zero-forward wrapper import failure can enter')
    if (ROOT / 'raw_journal.jsonl').exists() or (ROOT / 'scores').exists():
        raise ValueError('Unexpected successful model output; remaining protocol must be explicit')
    for entry in read(ROOT / 'source_lock.json')['code'].values():
        checked(entry)
    checked(read(ROOT / 'input_acceptance.json')['inputs'])
    checked(read(ROOT / 'learned_weight_acceptance.json')['weight'])
    seconds = int(read(ROOT / 'protocol.json')['GPU_max_seconds'] - failed['charged_seconds'])
    write(ROOT / 'remaining08_registration.json', dict(failed_GPU=reference(RESOURCE / (prior_name + '.resource.json')),
        raw_before=0, inputs_adopted=80, checkpoint_adopted=True, lost_or_repeated_model_calls=0,
        sole_fix='Explicit fixed module paths before imports; wrapper deliberately removes PYTHONPATH',
        remaining_GPU_max_seconds=seconds, original_candidate_grid_and_risk_gates_unchanged=True))
    write(ROOT / 'source_lock08.json', dict(original_lock=reference(ROOT / 'source_lock.json'),
        code={p.name: reference(p) for p in sorted((ROOT / 'code_v8').glob('*.py'))}))
    import_contract()
    record = run_gpu(seconds)
    with (ROOT / 'independent_review08.log').open('x') as output:
        done = subprocess.run([str(PY), '-u', '-B', str(ROOT / 'code_run/review.py')], cwd=ROOT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
    write(ROOT / 'independent_review08_terminal.json', dict(exit_code=done.returncode))
    if done.returncode:
        raise ValueError('Independent CPU review failed; no model repetition')
    for entry in read(ROOT / 'source_lock08.json')['code'].values():
        checked(entry)
    before = read(ROOT / 'source_lock.json')['baseline']
    checked(before)
    result = dict(status=read(ROOT / 'review.json')['status'], summary=read(ROOT / 'review.json')['summary'],
        GPU_charged_seconds=failed['charged_seconds'] + record['charged_seconds'],
        failed_import_seconds=failed['charged_seconds'], successful_GPU_seconds=record['charged_seconds'],
        wrapper_peak_MiB=record['sampled_peak_memory_mib'], model=read(ROOT / 'model_completion.json'),
        original_baseline_unchanged=True, new_ZIP=0, automatic_production=False,
        original_source_independence='UNKNOWN', old_failed_GPU_and_all_success_preserved=True)
    write(ROOT / 'completion.json', result)
    write(ROOT / 'short_result.json', result)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        write(ROOT / 'remaining08_failure.json', dict(status='ACTUAL_FAILURE_KEEP_SUCCESS', traceback=traceback.format_exc()))
        raise
