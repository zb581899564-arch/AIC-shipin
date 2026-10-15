"""One fresh dev chain only; never acquires confirmation media or starts production."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

import positive_io as io
from positive_runtime import base, failure


def child(root, state, stage):
    argv = [sys.executable, '-B', '-u', str(Path(__file__).parent/'positive_runtime.py'),
            stage, '--root', str(root), '--group', 'dev']
    io.save(state/(stage+'_launch.json'), dict(argv=argv, utc=io.utc(), CPU_child_only_CUDA_hidden=True))
    with (state/(stage+'.log')).open('xb') as log:
        result = subprocess.run(argv, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), stdout=log, stderr=subprocess.STDOUT)
    io.require(result.returncode == 0, 'New CPU stage failed; preserve success and require explicit recovery: '+stage)


def resource_snapshot():
    commands = [
        ['hostname'], ['ps', '-eo', 'pid,ppid,stat,args'], ['free', '-b'], ['df', '-B1', str(io.HOME)],
        ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader,nounits'],
        ['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader,nounits']]
    results = []
    for argv in commands:
        result = subprocess.run(argv, capture_output=True, text=True)
        io.require(result.returncode == 0, 'Read-only real resource observation failed: '+str(argv))
        results.append(dict(argv=argv, stdout=result.stdout, stderr=result.stderr, exit_code=result.returncode))
    return dict(utc=io.utc(), observations=results, static_capacity_threshold_applied=False)


def main(root):
    io.host(cpu=False); reg, _, reg_path = io.registration(root, 'dev')
    io.require(Path(__file__).resolve().parent == root/'code', 'Only separately deployed new code may run')
    state = root/'dev/chain_01'; state.mkdir(parents=True, exist_ok=False)
    io.save(state/'started.json', dict(pid=os.getpid(), utc=io.utc(), registration_ref=io.ref(reg_path),
        controller_ref=io.ref(__file__), parent_CUDA=os.environ['CUDA_VISIBLE_DEVICES'],
        automatic_resume=False, production_admitted=False, confirmation_media_acquisition_authorized=False))
    stage = 'NEW_PROMPT_PREPARATION'
    try:
        child(root, state, 'prepare')
        stage = 'FIRST_NEW_INPUT_QA_PRE_GPU'; child(root, state, 'input_qa')
        stage = 'INDEPENDENT_NEW_GPU_ADMISSION'; child(root, state, 'admit')
        gate_path = root/'gpu_admission_dev_POSITIVE.json'; gate = io.read(gate_path)
        io.require(0 < gate['expected_input_count'] <= reg['gpu_budget']['dev']['max_actual_calls'],
                   'Zero-candidate development stops without GPU; nonempty complete denominator required here')
        io.save(state/'resources_before_GPU.json', resource_snapshot())
        io.legacy(reg).deadline(gate)
        stage = 'UNIQUE_NEW_POSITIVE_GPU'
        argv = [sys.executable, '-B', str(io.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
            '--name', gate['gpu_job_name'], '--max-seconds', str(gate['max_seconds']),
            '--planned-output-bytes', str(32 << 20), '--capacity-reason',
            str(gate['expected_input_count'])+' strict new positive-admission calls; retained vision caches, raw and first output QA only.',
            '--queue-seconds', '1800', '--', sys.executable, '-B', '-u',
            str(Path(__file__).parent/'positive_runtime.py'), 'infer', '--root', str(root), '--group', 'dev']
        io.save(state/'gpu_launch.json', dict(argv=argv, utc=io.utc(), admission_ref=io.ref(gate_path),
                                            parent_CUDA=os.environ['CUDA_VISIBLE_DEVICES']))
        with (state/'gpu.log').open('xb') as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT)
        io.require(result.returncode == 0, 'Unique shared GPU wrapper failed; no automatic rerun')
        resource, resource_sha = io.terminal(gate)
        stage = 'FIRST_OUTPUT_ONLY_QA'; child(root, state, 'replay')
        stage = 'FULL_EIGHT_GATE_DEV_COMPARISON'
        argv = [sys.executable, '-B', '-u', str(Path(__file__).parent/'positive_evaluate.py'),
                '--root', str(root), '--group', 'dev']
        with (state/'comparison.log').open('xb') as log:
            result = subprocess.run(argv, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), stdout=log, stderr=subprocess.STDOUT)
        io.require(result.returncode in (0, 5), 'Comparison engineering failure cannot become scientific UNKNOWN/EMPTY')
        result_path = root/'dev/comparison_01/result.json'; comparison = io.read(result_path)
        expected = 'PASS_POSITIVE_DEV_FROZEN_PENDING_FRESH_CONFIRMATION' if result.returncode == 0 else 'STOP_POSITIVE_DEV_REJECTED'
        io.require(comparison['status'] == expected and len(comparison['cases']) == 4 and
            tuple(comparison['conditions']) == io.CONDITIONS and
            all(type(v) is bool for v in comparison['conditions'].values()) and
            (result.returncode == 0) == all(comparison['conditions'].values()), 'Actual scientific exit/result/gates disagree')
        io.save(state/'completion.json', dict(status=expected, utc=io.utc(), comparison_ref=io.ref(result_path),
            actual_new_calls=gate['expected_input_count'], resource=resource,
            resource_terminal_sha256=resource_sha, production_admitted=False,
            no_confirm_media_fixed40_426_or_package_started=True, old_model_or_QA_repeated=False))
    except BaseException as error:
        failure(state, stage, error)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--group', choices=('dev',), default='dev')
    args = parser.parse_args()
    main(io.root_path(args.root))
