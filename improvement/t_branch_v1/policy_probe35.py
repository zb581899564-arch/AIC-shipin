"""Unique backward-only engineering probe, strictly after the running original controls."""
import os
from pathlib import Path
import subprocess
import time
import traceback

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'policy_probe35'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_real_causal_actor_backward_probe_20261022_v35'


def wait_control():
    launch = read(ROOT / 'pilot_control30_launch.json')
    end = time.monotonic() + 5400
    while not (ROOT / 'pilot_control30/completion.json').exists():
        if (ROOT / 'pilot_control30/failure_controller.json').exists():
            raise RuntimeError('Actual prior-control failure; do not launch new probe or restart it')
        stat = Path('/proc') / str(launch['pid']) / 'stat'
        if not stat.exists() or stat.read_text().rsplit(')', 1)[1].split()[19] != launch['start_ticks']:
            raise RuntimeError('Prior-control handle missing without terminal; inspect, never relaunch')
        if time.monotonic() > end:
            raise TimeoutError('Registered wait exhausted, keep live prior control untouched')
        time.sleep(5)


def execute(name, GPU=False):
    command = [str(PY), '-B', '-u', str(CODE / name)]
    if GPU:
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
        if apps.strip():
            raise RuntimeError('Protect current external GPU compute; no probe launch')
        save(OUT / 'resource_admission.json', dict(apps=apps, GPU=subprocess.check_output(['nvidia-smi'], text=True),
            RAM=subprocess.check_output(['free', '-b'], text=True), disk=subprocess.check_output(['df', '-B1', str(ROOT)], text=True)))
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '600',
            '--planned-output-bytes', '8000000', '--capacity-reason',
            'First4 causal TF plus1 cloned-actor backward, zero optimizer; same accepted native64/cache, shared base/reference/actor total8.798B; checkpoint language and no external GPU',
            '--queue-seconds', '0', '--'] + command
    label = Path(name).stem
    with (OUT / (label + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if GPU else '', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (label + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (label + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Actual backward-only probe stage failed: ' + label)


def main():
    OUT.mkdir()
    if read(ROOT / 'causal_contract32/completion.json')['state'] != 'PASS_REAL4_CAUSAL_PREFIX_GRAMMAR_POLICY_CONTRACT':
        raise ValueError('Actual real-prefix causal contract missing')
    if read(ROOT / 'actor_contract33/completion.json')['state'] != 'PASS_INSTALLED_PEFT_CPU_ROLE_CONTRACT_AND_TIME_HEADER':
        raise ValueError('Actual installed PEFT role contract missing')
    save(OUT / 'registration.json', dict(purpose='Actual8B causal/role/gradient engineering, no optimizer or source-quality claim',
        inputs=identity(ROOT / 'causal_contract32/completion.json'), roles=identity(ROOT / 'actor_contract33/completion.json'),
        first_reference_TF=4, first_actor_gradient_forward=1, backwards=1, optimizer_updates=0,
        source_advantage=1.0, synthetic_advantage_not_actual_training_reward=True,
        conditional_temperature=1.0, KL_weight=0.02, original_actor_clone_exact=True,
        logits_slice='Last L of prefix plus self-generated suffix excluding last token, includingEOS target',
        TF_incremental_logit_drift_bound='4*actual_model_dtype_epsilon*(1+abs(cached_selected_logit))',
        exact_incremental_probability_or_quality_claim=False,
        GPU_max_seconds=600, no_new_generation_decode_processor_or_successful_TF_repeated=True,
        wait_for_actual_control30_terminal_before_GPU=True, wait_seconds_max=5400,
        no_training_production_package_or_official_submission=True))
    wait_control()
    names = ['policy_probe35.py', 'policy_probe34.py', 'policy_forward34.py', 'policy_replay36.py',
             'actor_roles33.py', 'policy_contract.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(code={name: identity(CODE / name) for name in names},
        registration=identity(OUT / 'registration.json'), wrapper=identity(WRAPPER),
        original_control=identity(ROOT / 'pilot_control30/completion.json')))
    execute('policy_probe34.py', True)
    execute('policy_replay36.py')
    import json
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [row for row in ledger if row.get('name') == JOB] != [resource]:
        raise ValueError('Natural unique backward probe GPU terminal differs')
    save(OUT / 'completion.json', dict(state='REAL8B_CAUSAL_BACKWARD_ENGINEERING_COMPLETE',
        audit=identity(OUT / 'independent_CPU_audit.json'), GPU_seconds=resource['charged_seconds'],
        new_TF=5, real_backward=1, optimizer_updates=0,
        no_training_or_quality_or_candidate_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(),
                preserve_all_raw_and_successes=True, no_automatic_retry=True))
        raise
