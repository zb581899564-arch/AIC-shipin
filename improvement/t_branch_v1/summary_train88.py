"""Unique fixed10-update training after complete217-event/data/cost admission."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'summary_train88'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_publisher_balanced_content_summary10_20261022_v88'
PARAMETERS = 15335424
PERMANENT_BYTES = PARAMETERS * 4 * 4 + 20000000


def await_actual_inputs():
    launch = read(ROOT / 'summary_chain85_launch.json'); deadline = time.monotonic() + 3300
    while True:
        complete, failure = ROOT / 'summary_caption85/completion.json', ROOT / 'summary_caption85/failure.json'
        if failure.exists() or (ROOT / 'summary_chain85_dependency_failure.json').exists():
            raise RuntimeError('Actual fit event/input phase failed; never re-launch successes here')
        if complete.exists():
            value = read(complete)
            if value['state'] != 'FIRST217_FIT_EVENTS_AND86_CONTENT_INPUTS_PASS_NOT_TRAINING_ADMISSION':
                raise ValueError('Actual complete first217 event/86-target input terminal differs')
            return value
        proc = Path('/proc') / str(launch['pid'])
        if not proc.exists():
            raise RuntimeError('Actual85 parent missing without terminal; inspect, never repeat')
        stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        if stat[19] != launch['start_ticks'] or stat[0] == 'Z' or time.monotonic() > deadline:
            raise RuntimeError('Upstream actual handle identity/wait bound differs')
        time.sleep(3)


def run(script, phase, GPU=False):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if GPU:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', '1000',
            '--planned-output-bytes', str(PERMANENT_BYTES), '--capacity-reason',
            'One fixed fresh-summary LoRA10 publisher updates/172 original content targets; exact gradients and recovery in declared tmpfs, durable first optimizer witness/final adapter/projections; no image decode, old training or inference replay',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (phase + '.log')).open('x') as log:
        child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if GPU else '',
                     OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=child.pid, command=command,
            start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = child.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('Actual content training phase failed; preserve every success: ' + phase)


def main():
    event = await_actual_inputs(); OUT.mkdir()
    protocol = read(CODE / 'summary_protocol85.json')
    if (event['profile_development_GPU_seconds'] + 1000 + 2100
            > protocol['profile_development_GPU_seconds_max_including_fit_and_all_failures']):
        raise ValueError('Actual profile fees cannot fund fixed training and first development')
    if event['all_goal_GPU_seconds'] + 1000 > protocol['Goal_all_GPU_seconds_max']:
        raise ValueError('Fixed all-Goal GPU budget cannot fund this training')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    data = read(check(event['actual_training_inputs']))
    if data['actual_review_count'] != 86 or data['sources'] != 9 or data['publisher_groups'] != 5:
        raise ValueError('Actual complete9-source/all86 review training input gate differs')
    layer_contract = read(ROOT / 'summary_target_contract88/completion.json')
    if (layer_contract['state'] != 'PASS_FIRST144_FULL_NAME_FRESH_ADAPTER_CPU_CONTRACT'
            or layer_contract['role_factory'] != identity(CODE / 'summary_actor88.py')):
        raise ValueError('Actual first full-name adapter CPU check is absent or belongs to different code')
    # Full micro-gradient snapshots permit exact remaining-only recovery. All
    # are new88 temporary artifacts, never a reason to repeat successful TFs.
    temporary = PARAMETERS * 4 * (172 + 10 + 31 + 5) + 631 * 151936 * 4
    if shutil.disk_usage('/dev/shm').free < temporary or shutil.disk_usage(ROOT).free < PERMANENT_BYTES:
        raise RuntimeError('Specific complete new training/recovery/final artifact capacity insufficient')
    control = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if control[0] != 'T' or control[19] != '491630308':
        raise ValueError('Protected CONTROL5 state differs; do not signal or restart it')
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External GPU compute appeared; preserve accepted data, no collision')
    names = ['summary_train88.py', 'summary_train88_gpu.py', 'summary_train88_cpu.py',
        'summary_step88.py', 'summary_recovery88.py', 'summary_actor88.py', 'summary_data88.py',
        'summary_teacher88_cpu.py', 'summary_protocol85.json', 'actor_roles33.py',
        'causal_policy32.py', 'joint_checkpoint44.py', 't_io.py', 't_runtime39.py']
    save(OUT / 'source_input_lock.json', dict(protocol=identity(CODE / 'summary_protocol85.json'),
        code={n: identity(CODE / n) for n in names}, actual_complete_event_gate=identity(ROOT / 'summary_caption85/completion.json'),
        actual_all_source_targets=event['actual_training_inputs'],
        initial_role_CPU=identity(ROOT / 'summary_contract85/completion.json'),
        exact_full_name_layer_CPU=identity(ROOT / 'summary_target_contract88/completion.json'),
        source_scope=identity(ROOT / 'summary_content81/completion.json'),
        wrapper=identity(WRAPPER), actual_GPU_apps=apps,
        transient_recovery_bytes_upper=temporary, permanent_output_bytes_upper=PERMANENT_BYTES,
        recovery_storage='/dev/shm/aic_T_summary_train88',
        exact_per_success_gradients_and_publisher_states=True,
        permanent_raw='All172 target/logp/weight/gradient proofs, first optimizer full witness, final FP32 adapter; temporary full TF logits retire after first CPU; recovery remains until explicit post-audit retirement',
        no_old_raw_cache_or_success_repeated=True,
        runtime_checks_before_actual_backward='Actual fresh144-layer/288tensor zeroB summary and total8869330010 parameters; teacher causal binding and first full-vocab CPU',
        current_live_CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:12]))
    run('summary_train88_gpu.py', 'GPU', GPU=True)
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    if resource['status'] != 'completed' or resource['exit_code'] != 0 or [r for r in ledger if r.get('name') == JOB] != [resource]:
        raise ValueError('Actual training natural GPU terminal/unique ledger differs')
    run('summary_train88_cpu.py', 'independent_CPU')
    review = read(OUT / 'independent_CPU_completion.json')
    save(OUT / 'completion.json', dict(state='FIXED10_CONTENT_TRAINING_AND_FIRST_INDEPENDENT_CPU_COMPLETE_NOT_TIME_QUALITY',
        actual_optimizer_updates=10, actual_target_forwards=172, final_adapter=review['final_actual_FP32_save_reload'],
        actual_full_pipeline_parameters=review['actual_complete_parameters'],
        training=identity(OUT / 'GPU_completion.json'), first_independent_CPU=identity(OUT / 'independent_CPU_completion.json'),
        GPU_seconds=resource['charged_seconds'], all_goal_GPU_seconds=event['all_goal_GPU_seconds'] + resource['charged_seconds'],
        profile_development_GPU_seconds=event['profile_development_GPU_seconds'] + resource['charged_seconds'],
        no_development_confirmation_or_production_admission=True, new_T_ZIP=0,
        next='Freeze native goal interface before first new selectors; trained and adopted BASE summary controls, fixed goal shift and actual full40.48 source comparison. No training-dose/prompt scan or automatic426.'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_every_success_and_fee=True))
        else:
            save(ROOT / 'summary_train88_dependency_failure.json', dict(traceback=traceback.format_exc(), no_upstream_restart=True))
        raise
