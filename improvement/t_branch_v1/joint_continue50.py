"""Explicit time-limit-only engineering continuation inside unchanged T1 total."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import traceback

import joint_controller44 as controller
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'joint_continue50'
OLD = ROOT / 'joint_remaining47'
JOB = 'T_joint4_only_missing_engineering_20261022_v50'
OLD_JOB = 'T_joint_source_counterfactual_remaining_20261022_v47'


def execute(script, seconds=None):
    command = [str(controller.PY), '-B', '-u', str(Path(__file__).parent / script)]
    if seconds is not None:
        command = [str(controller.PY), '-B', str(controller.WRAPPER), '--name', JOB,
            '--max-seconds', str(seconds), '--planned-output-bytes', '2000000000',
            '--capacity-reason', 'Only missing original4episode work; restore committed actor/Adam/RNG and durable gradients, retain all old bytes; remaining estimate2GB, no new data/model or successful operation replay',
            '--queue-seconds', '0', '--'] + command
    name = Path(script).stem
    with (OUT / (name + '.log')).open('x') as stream:
        child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if seconds is not None else '', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (name + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (name + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Actual remaining-only stage failed: ' + name)


def main():
    OUT.mkdir()
    if socket.gethostname() != 'inspur-NP5570M5':
        raise ValueError('Actual continuation host identity differs')
    resource = read(controller.RUN / 'controller' / (OLD_JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (controller.WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'failed' or [r for r in ledger if r.get('name') == OLD_JOB] != [resource]:
        raise ValueError('Actual unique failed stage47 not established; never relaunch a live task')
    if resource.get('stop_reason') != 'frozen single-job wall-time reached' or resource['charged_seconds'] < 2206 or not (OLD / 'failure.json').exists():
        raise ValueError('Not the actual registered2206s limit; inspect different failure instead')
    log = (controller.RUN / 'controller' / (OLD_JOB + '.log')).read_text()
    if 'Traceback (most recent call last)' in log:
        raise ValueError('Actual model/grammar error is not a time-only engineering recovery')
    protocol = identity(Path(__file__).parent / 'joint_policy_protocol44.json')
    if protocol['sha256'] != 'd9f01805183ab0a40028f0cc173053f6470083659cf0e17c14f848bfc7e849c7':
        raise ValueError('Original frozen scientific protocol changed')
    prefix = [identity(path) for path in sorted(OLD.glob('episode_*/completion.json'))]
    rows = [read(check(ref)) for ref in prefix]
    if not rows or len(rows) > 4 or [row['index'] for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError('No contiguous committed source state to resume')
    for row in rows:
        check(row['recovery_checkpoint'])
    pending = OLD / ('episode_%02d' % (len(rows) + 1))
    if len(rows) < 4 and (pending / 'clipped_gradient.npz').exists():
        raise ValueError('A pending old optimizer may already have run; adopt actual checkpoint before any update')
    if pending.exists():
        for backward in pending.glob('*_replay/backward.json'):
            case = read(backward)['case']
            if not (pending / (case + '_gradient_acceptance.json')).exists():
                raise ValueError('A completed backward lacks durable acceptance; audit orphan gradient before any replay')
    prior = 1496.405099238269 + resource['charged_seconds']
    seconds = 1200
    if prior + seconds + 2400 > 10800:
        raise ValueError('Original total T1 does not fund remaining work and frozen development')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('A GPU process is live; protect it, no continuation launch')
    if shutil.disk_usage(ROOT).free < 2000000000:
        raise RuntimeError('Insufficient actual capacity for remaining durable gradients/checkpoint')
    names = ['joint_continue50.py', 'joint_continue50_gpu.py', 'joint_continue50_audit.py',
        'joint_finish50.py', 'resume_episode50.py', 'resume_rollout50.py', 'resume_rng50.py', 'resume_state50.py']
    lock = read(OLD / 'source_input_lock.json')
    check(lock['wrapper'])
    for ref in lock['code'].values():
        check(ref)
    lock['code'].update({name: identity(Path(__file__).parent / name) for name in names})
    control = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if control[0] != 'T' or control[19] != '491630308':
        raise ValueError('Protected CONTROL5 state/identity differs')
    save(OUT / 'source_input_lock.json', lock)
    save(OUT / 'registration.json', dict(actual_prior_failure=identity(OLD / 'failure.json'),
        actual_old_resource=identity(controller.RUN / 'controller' / (OLD_JOB + '.resource.json')),
        original_train_phase_limit_failed=True, original_protocol_unchanged=protocol,
        measured_per_window_backward_seconds='15.0..16.4; original phase estimate insufficient',
        engineering_time_amendment='Only missing work inside original10800s T1 total; no dose/checkpoint/gate change, not a claimed within2400s pass',
        previous_T1_seconds=prior, new_engineering_seconds_max=seconds, total_T1_max=10800,
        original_four_episodes_only=True, original_optimizer_updates_max=4,
        completed_episodes_adopted=prefix, no_completed_model_TF_backward_or_update_repeated=True,
        new_development_or_confirmation_metrics_seen=False,
        authority='User standing autonomous implementation and original T1 total budget, no new data/model or quality-gate change',
        new_GPU_output_estimate_bytes=2000000000))
    save(OUT / 'resource_admission.json', dict(apps=apps,
        GPU=subprocess.check_output(['nvidia-smi'], text=True), RAM=subprocess.check_output(['free', '-b'], text=True),
        disk=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True),
        restore_committed_prefix_only=True, capacity_estimate_bytes=2000000000))
    execute('joint_continue50_gpu.py', seconds)
    execute('joint_continue50_audit.py')
    final = read(controller.RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (controller.WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if final['status'] != 'completed' or final['exit_code'] != 0 or [r for r in ledger if r.get('name') == JOB] != [final]:
        raise ValueError('Actual unique continuation terminal differs')
    result = read(OUT / 'gpu_completion.json')
    save(OUT / 'completion.json', dict(state=result['state'], actual_optimizer_updates=result['actual_optimizer_updates'],
        GPU_seconds=final['charged_seconds'], old47_seconds=resource['charged_seconds'],
        cumulative_T1_seconds=prior + final['charged_seconds'], original_phase_limit_failure_preserved=True,
        final_adapter=result['final_adapter'], CPU_audit=identity(OUT / 'independent_CPU_audit.json'),
        no_automatic_production_or_package=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
