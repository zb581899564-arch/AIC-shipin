"""One exclusive training launch, natural resource terminal, first independent CPU audit."""
import json
import math
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'joint_train44'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_joint_source_counterfactual_sft4_20261022_v44'
PROTOCOL_SHA = 'd9f01805183ab0a40028f0cc173053f6470083659cf0e17c14f848bfc7e849c7'


def execute(script, seconds=None):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if seconds is not None:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', str(seconds),
            '--planned-output-bytes', '8000000000', '--capacity-reason',
            'Actual8.798B/backward24.95GB profile passed; 4complete sources47windows each twice, up to94 compressed cumulative61MB gradients plus4 recovery states and final; estimate8GB, existing11.85GB disk and109GB RAM; source caches adopted, no new decode',
            '--queue-seconds', '0', '--'] + command
    name = Path(script).stem
    with (OUT / (name + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if seconds is not None else '', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (name + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        code = child.wait()
    save(OUT / (name + '_terminal.json'), dict(exit_code=code))
    if code:
        raise RuntimeError('Actual stage failed, retain all partial successes: ' + name)


def main():
    OUT.mkdir()
    if socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('Actual host differs')
    protocol_ref = identity(CODE / 'joint_policy_protocol44.json')
    if protocol_ref['sha256'] != PROTOCOL_SHA:
        raise ValueError('Frozen protocol changed')
    protocol = read(check(protocol_ref))
    for item in protocol['method']['causal_dependencies']:
        if not (ROOT / item).is_file():
            raise ValueError('Actual accepted causal dependency missing: ' + item)
    execute('joint_preflight44.py')
    if read(ROOT / 'joint_preflight44/completion.json')['state'] != 'PASS_EXACT_FINAL_FP32_ACTOR_RELOAD':
        raise ValueError('Installed PEFT final roundtrip not accepted')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External GPU app active; no new training launch')
    names = ['joint_controller44.py', 'joint_preflight44.py', 'joint_train44.py', 'joint_audit45.py',
        'joint_data44.py', 'joint_rollout44.py', 'joint_replay44.py', 'joint_checkpoint44.py',
        'joint_reward43.py', 'causal_policy32.py', 'policy_contract.py', 'actor_copy41.py',
        'actor_roles33.py', 'coarse_call25.py', 't_runtime39.py', 'native_sets.py', 'preference_reward.py', 't_io.py']
    save(OUT / 'source_input_lock.json', dict(protocol=protocol_ref,
        code={name: identity(CODE / name) for name in names}, wrapper=identity(WRAPPER),
        all97_CPU=identity(ROOT / 'pilot_input_qa29/completion.json'),
        source_cohort=identity(ROOT / protocol['source_cohort']),
        all_review_targets=identity(ROOT / 'summary_targets28/completion.json'),
        original_controls=identity(ROOT / 'pilot_control30/gpu_completion.json')))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    prior_receipts = ['reference_review22/completion.json', 'pilot_cost25/completion.json',
        'pilot_review37/completion.json', 'policy_remaining42/completion.json']
    fees = [read(ROOT / name)['GPU_seconds'] for name in prior_receipts]
    failed = read(RUN / 'controller/T_real_causal_actor_backward_probe_20261022_v35.resource.json')
    fees.append(failed['charged_seconds'])
    prior = math.fsum(fees)
    if abs(prior - 1302.8305039964616) > 1e-8:
        raise ValueError('Actual prior fee receipts differ from frozen budget registration')
    if identity(WRAPPER)['sha256'] != '9997d41fbe2bb51726914b4698b874cf939c52aac02048fa9b3bb753c64c6cec':
        raise ValueError('Shared GPU wrapper changed')
    control = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if control[0] != 'T' or control[19] != '491630308':
        raise ValueError('Protected CONTROL5 identity/state differs')
    if shutil.disk_usage(ROOT).free < 8000000000:
        raise RuntimeError('Current disk cannot hold the actual registered snapshot/recovery estimate')
    save(OUT / 'resource_admission.json', dict(host=socket.gethostname(), apps=apps,
        GPU=subprocess.check_output(['nvidia-smi'], text=True), RAM=subprocess.check_output(['free', '-b'], text=True),
        disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True),
        expected_output_bytes=8000000000, existing_disk_free=shutil.disk_usage(ROOT).free,
        previous_T1_charged_seconds=prior, train_max_seconds=2400,
        T1_total_max_seconds=10800, dynamic_actual_profile_basis=True,
        immutable_prior_ledger_count=len(ledger), previous_receipts=prior_receipts,
        prior_fees=fees, CONTROL5_identity_state_preserved=True))
    if prior + protocol['budgets']['train_GPU_seconds_max'] > protocol['budgets']['T1_cumulative_GPU_seconds_max']:
        raise ValueError('No actual T1 budget for frozen training stage')
    execute('joint_train44.py', protocol['budgets']['train_GPU_seconds_max'])
    execute('joint_audit45.py')
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [row for row in ledger if row.get('name') == JOB] != [resource]:
        raise ValueError('Actual unique natural GPU terminal/ledger mismatch')
    result = read(OUT / 'gpu_completion.json')
    save(OUT / 'completion.json', dict(state=result['state'], actual_optimizer_updates=result['actual_optimizer_updates'],
        GPU_seconds=resource['charged_seconds'], cumulative_T1_seconds=prior + resource['charged_seconds'],
        final_adapter=result['final_adapter'], CPU_audit=identity(OUT / 'independent_CPU_audit.json'),
        next='Frozen development/free-greedy and actual40.47 chain only if mechanism passed',
        no_automatic_development_confirmation_production_or_package=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), no_automatic_retry=True,
                preserve_all_completed_rollouts_TFs_gradients_and_checkpoints=True))
        raise
