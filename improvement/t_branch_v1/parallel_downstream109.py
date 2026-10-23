"""Complete fixed parallel105 source comparison; no automatic fresh confirmation."""
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import traceback

from frozen_branch46 import RUN
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'parallel_full109'
CODE = Path(__file__).parent
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER = RUN / 'resource_unlimited_v1_20261007/gpu_run.py'
JOB = 'T_parallel_queries_first_missing_VERIFY_full40_48_20261023_v109'


def run(script, phase, seconds=None, output_bytes=0):
    command = [str(PY), '-B', '-u', str(CODE / script)]
    if seconds is not None:
        command = [str(PY), '-B', str(WRAPPER), '--name', JOB, '--max-seconds', str(seconds),
            '--planned-output-bytes', str(output_bytes), '--capacity-reason',
            'Only first missing exact originalTIME VERIFY; all old successful55/78/93 tasks and365BASE/head/40.48route adopted. New text/raw/proofs only, no media/RGB/processor/ASR or completed parallel training repeated.',
            '--queue-seconds', '0', '--'] + command
    with (OUT / (phase + '.log')).open('x') as stream:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='0' if seconds is not None else '',
                     OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                     PYTHONDONTWRITEBYTECODE='1'))
        save(OUT / (phase + '_launch.json'), dict(pid=process.pid, command=command,
            start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]))
        status = process.wait()
    save(OUT / (phase + '_terminal.json'), dict(exit_code=status))
    if status:
        raise RuntimeError('First parallel downstream phase failed; preserve all successes: ' + phase)


def lock_inputs(cpu):
    protocol = read(CODE / 'parallel_protocol105.json')
    stopped = Path('/proc/1244689/stat').read_text().rsplit(')', 1)[1].split()
    if socket.gethostname() != 'inspur-NP5570M5' or stopped[0] != 'T' or stopped[19] != '491630308':
        raise ValueError('Actual host/CONTROL5 guard differs; do not signal')
    for key in ['protected_original', 'protected_best']:
        check(protocol[key])
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                                    '--format=csv,noheader'], text=True)
    if apps.strip():
        raise RuntimeError('External GPU compute exists; preserve accepted texts without collision')
    save(OUT / 'registration.json', dict(protocol=identity(CODE / 'parallel_protocol105.json'),
        complete_parallel_native=identity(ROOT / 'parallel_remaining108/completion.json'),
        complete_verify_inputs=identity(ROOT / 'parallel_verify_inputs109/completion.json'),
        actual_first_missing_calls=cpu['maximum_first_new_VERIFY_calls'],
        remaining_original_profile_seconds=cpu['remaining_fixed_profile_GPU_seconds'],
        measured_cost=cpu['cost_estimate'], actual_GPU_apps=apps,
        CPU=subprocess.check_output(['ps', '-eo', 'pid,ppid,pcpu,pmem,args', '--sort=-pcpu'], text=True).splitlines()[:12],
        RAM=subprocess.check_output(['free', '-b'], text=True),
        capacity=subprocess.check_output(['df', '-B1', str(ROOT), '/dev/shm'], text=True)))
    names = ['parallel_downstream109.py', 'parallel_verify_inputs109.py', 'parallel_verify_plan109.py',
        'parallel_verify109_gpu.py', 'parallel_full109_masks.py', 'parallel_full109_review.py',
        'parallel_metric_cache109.py', 'parallel_protocol105.json', 'verify_adoption92.py',
        'summary_full93_masks.py', 'stage_metric_cache96.py', 'event_full79.py', 'event_chain78.py',
        'development_verify46.py', 'development_review48.py', 'development_data46.py', 'frozen_branch46.py',
        'reference_gpu19.py', 'reference_data18.py', 'native_sets.py', 'preference_reward.py',
        't_io.py', 't_runtime39.py', 'joint_data44.py', 'prompt_contract13.py']
    save(OUT / 'source_input_lock.json', dict(code={name: identity(CODE / name) for name in names},
        actual_verify_CPU=identity(ROOT / 'parallel_verify_inputs109/completion.json'),
        actual_success_catalog=identity(ROOT / 'parallel_verify_catalog109/completion.json'),
        original_dependencies=read(ROOT / 'event_caption70/source_input_lock.json')['original_dependencies'],
        actual_current40_48_route=identity(ROOT / 'event_route77/CPU_completion.json'), wrapper=identity(WRAPPER)))


def main():
    OUT.mkdir()
    native = read(ROOT / 'parallel_remaining108/completion.json')
    if native['state'] != 'COMPLETE217_TRAINING_AND150_DEV_FIRST_CPU_PASS_NOT_QUALITY':
        raise ValueError('Complete native training/development and first independent CPU required')
    run('parallel_verify_inputs109.py', 'first_VERIFY_input_CPU')
    inputs_root = ROOT / 'parallel_verify_inputs109'
    if (inputs_root / 'cost_STOP.json').exists():
        save(OUT / 'completion.json', dict(state='STOP_FIXED_PARALLEL105_COMPLETE_VERIFY_COST',
            actual_cost_STOP=identity(inputs_root / 'cost_STOP.json'), new_VERIFY_calls=0, GPU_seconds=0.,
            all_goal_GPU_seconds=native['all_goal_GPU_seconds'], profile_GPU_seconds=native['profile_GPU_seconds'],
            no_complete_quality_or_confirmation_or_production_admission=True))
        return
    cpu = read(inputs_root / 'completion.json')
    if cpu['state'] != 'COMPLETE_PARALLEL_VERIFY_INPUTS_CPU_PASS':
        raise ValueError('All actual first/adopted exact VERIFY inputs must pass')
    lock_inputs(cpu)
    charged = 0.
    if cpu['maximum_first_new_VERIFY_calls']:
        run('parallel_verify109_gpu.py', 'GPU', cpu['remaining_fixed_profile_GPU_seconds'], cpu['proposed_specific_bytes'])
        resource = read(RUN / 'controller' / (JOB + '.resource.json'))
        ledger = [json.loads(line) for line in (WORK / 'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
                  if line.strip()]
        if (resource['status'] != 'completed' or resource['exit_code'] != 0
                or [row for row in ledger if row.get('name') == JOB] != [resource]):
            raise ValueError('Actual first missing parallel VERIFY natural terminal/unique ledger differs')
        charged = resource['charged_seconds']
    else:
        save(OUT / 'GPU_completion.json', dict(state='ALL_EXACT_PARALLEL_VERIFY_ADOPTED_NO_NEW_GPU',
            outputs=cpu['adopted_successful_outputs'], first_new_keys=[], first_new_calls=0))
    run('parallel_full109_review.py', 'first_full_source_CPU')
    review = read(OUT / 'review.json')
    save(OUT / 'completion.json', dict(state=review['state'], review=identity(OUT / 'review.json'),
        first_full_CPU=identity(OUT / 'independent_CPU_completion.json'),
        first_new_VERIFY_calls=cpu['maximum_first_new_VERIFY_calls'], GPU_seconds=charged,
        all_goal_GPU_seconds=native['all_goal_GPU_seconds'] + charged,
        profile_GPU_seconds=native['profile_GPU_seconds'] + charged,
        actual_complete_parameters=8869330010, exact_full40_48_comparison=True,
        no_automatic_confirmation_or_production=True, new_T_ZIPs=0,
        original40_47_and40_48_unchanged=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes_raw_fees=True))
        raise
