"""Use only remaining original600s budget after proved additional-adapter copy rounding."""
import os
from pathlib import Path
import subprocess
import traceback

from t_io import ROOT, WORK, identity, read, save

OUT = ROOT / 'policy_remaining42'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_actor_copy_remaining_backward_20261022_v42'


def execute(name, seconds=None):
    command = [str(PY), '-B', '-u', str(CODE / name)]
    if seconds is not None:
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
        if apps.strip():
            raise RuntimeError('External GPU compute exists, no remaining probe launch')
        save(OUT / 'resource_admission.json', dict(apps=apps, GPU=subprocess.check_output(['nvidia-smi'], text=True),
            RAM=subprocess.check_output(['free', '-b'], text=True), disk=subprocess.check_output(['df', '-B1', str(ROOT)], text=True)))
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', str(seconds),
            '--planned-output-bytes', '5000000', '--capacity-reason',
            'Adopt4 successful causal TFs; first exact actual-default copy and1 backward, no optimizer; original600s less75.274 prior, actual8.798B, checkpoint language',
            '--queue-seconds', '0', '--'] + command
    label = Path(name).stem
    with (OUT / (label + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if seconds is not None else '', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (label + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (label + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Actual remaining actor-copy stage failed: ' + label)


def main():
    OUT.mkdir()
    old = read(ROOT / 'policy_adopt40/completion.json')
    if read(ROOT / 'actor_contract41/completion.json')['state'] != 'PASS_MIXED_PRECISION_ACTUAL_DEFAULT_COPY':
        raise ValueError('Installed PEFT mixed-precision reproduction/fix missing')
    seconds = old['remaining_GPU_seconds_integer']
    if not 0 < seconds <= int(600 - old['prior_GPU_seconds']):
        raise ValueError('Remaining original protocol budget differs')
    save(OUT / 'registration.json', dict(actual_failure=identity(ROOT / 'policy_probe38/failure.json'),
        accepted_original_TFs=identity(ROOT / 'policy_adopt40/completion.json'),
        actual_installed_PEFT_fix=identity(ROOT / 'actor_contract41/completion.json'),
        original_GPU_limit_seconds=600, prior_charged_GPU_seconds=old['prior_GPU_seconds'],
        remaining_GPU_seconds=seconds, original_successful_TFs_adopted=4,
        new_reference_TFs=0, first_actor_forward=1, first_backward=1, optimizer_updates=0,
        no_new_scientific_recipe=True, original40_47_and_all_failures_preserved=True))
    names = ['policy_remaining42.py', 'policy_remaining42_gpu.py', 'policy_remaining42_review.py',
             'actor_copy41.py', 'actor_roles33.py', 'policy_probe34.py', 'policy_contract.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(code={name: identity(CODE / name) for name in names},
        registration=identity(OUT / 'registration.json'), wrapper=identity(WRAPPER)))
    execute('policy_remaining42_gpu.py', seconds)
    execute('policy_remaining42_review.py')
    import json
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [row for row in ledger if row.get('name') == JOB] != [resource]:
        raise ValueError('Unique natural remaining-probe completion differs')
    save(OUT / 'completion.json', dict(state='REAL8B_CAUSAL_BACKWARD_ENGINEERING_COMPLETE',
        independent_CPU=identity(OUT / 'independent_CPU_audit.json'),
        GPU_seconds=resource['charged_seconds'], prior_GPU_seconds=old['prior_GPU_seconds'],
        adopted_TFs=4, first_actor_forward=1, first_backward=1, optimizer_updates=0,
        no_quality_or_training_or_package_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True,
                no_automatic_retry=True))
        raise
