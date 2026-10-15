"""One first-fresh control chain; explicit new recipe, three serial unique GPU jobs."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import traceback

import model_common as io
from fresh_registration import registration, media_files, input_QA


def ref(path):
    path = io.checked(path); return dict(path=str(path), sha256=io.sha(path))


def child(state, name, argv):
    io.save(state/(name+'_launch.json'), dict(argv=argv, utc=io.utc(), child_only_CUDA_hidden=True))
    with (state/(name+'.log')).open('xb') as log:
        result = subprocess.run(argv, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), stdout=log, stderr=subprocess.STDOUT)
    io.require(result.returncode == 0, 'Fresh CPU child failed; preserve successes, no automatic retry: '+name)


def admit(root, reg, stage):
    qa_path, qa = input_QA(root, stage)
    cpu_path = root/'cpu_acceptance_confirm.json' if stage == 'B0' else root/'confirm/VERIFY/cpu_01/completion.json'
    cpu = io.read(cpu_path); budget = reg['gpu_budget'][stage]
    io.require(qa['calls'] == len(cpu['entries']) <= budget['max_actual_calls'] and len(cpu['entries']) > 0,
               'Complete nonempty actual fresh-stage denominator within pre-registered budget required')
    lock_path = root/('source_lock_confirm_'+stage+'.json'); io.validate_lock(lock_path, set(io.code_files()) | {str(cpu_path), str(qa_path)})
    io.require(not (io.RUN/'controller'/(budget['gpu_job_name']+'.resource.json')).exists(), 'Unique job already has a terminal; never repeat success')
    gate = dict(status=io.ADMISSION_STATUS, group='confirm', stage=stage, expected_input_count=len(cpu['entries']),
        gpu_job_name=budget['gpu_job_name'], max_seconds=budget['max_seconds'], deadline=reg['deadline'],
        cpu_acceptance_path=str(cpu_path), cpu_acceptance_sha256=io.sha(cpu_path),
        source_lock_path=str(lock_path), source_lock_sha256=io.sha(lock_path),
        first_input_QA_sha256=io.sha(qa_path), fresh_registration_sha256=io.sha(root/'positive_fresh_registration.json'),
        model_parameters=io.MODEL_PARAMETERS, optimizer_updates=0, source_scope='EXTERNAL_NONTEST_ONLY',
        reference_available_to_inference=False, production_admitted=False)
    gate_path = root/('gpu_admission_confirm_'+stage+'.json'); io.save(gate_path, gate)
    return gate, gate_path


def gpu(state, root, gate, gate_path, script, extra=()):
    io.deadline(gate)
    from native_helpers import resource_snapshot
    observations = []
    for command in (['ps', '-eo', 'pid,ppid,stat,args'],
        ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader,nounits'],
        ['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader,nounits']):
        value = subprocess.run(command, capture_output=True, text=True)
        io.require(value.returncode == 0, 'Read-only live shared-resource observation failed')
        observations.append(dict(argv=command, stdout=value.stdout, stderr=value.stderr))
    io.save(state/(gate['stage']+'_resources_before_GPU.json'),
        dict(snapshot=resource_snapshot(root), observations=observations, fixed_utilization_threshold_applied=False))
    argv = [sys.executable, '-B', str(io.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
        '--name', gate['gpu_job_name'], '--max-seconds', str(gate['max_seconds']),
        '--planned-output-bytes', str(32 << 20), '--capacity-reason',
        str(gate['expected_input_count'])+' unique fresh actual pre-input-QA-admitted calls; retained caches/raw/first output QA.',
        '--queue-seconds', '1800', '--', sys.executable, '-B', '-u', str(script),
        'infer', '--root', str(root), '--group', 'confirm', *extra]
    name = gate['stage']; io.save(state/(name+'_GPU_launch.json'), dict(argv=argv, utc=io.utc(), admission_ref=ref(gate_path)))
    with (state/(name+'_GPU.log')).open('xb') as log:
        result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT)
    io.require(result.returncode == 0, 'Unique shared GPU wrapper failed; no rerun')
    return io.terminal(gate)


def positive_registration(root, positive_root, reg):
    """Expose completed fresh stage evidence to the unchanged positive adopter."""
    code = Path(reg['frozen_positive_code_dir']).resolve()
    io.require(code == positive_root/'confirm_code', 'Use frozen same-factor BASE-admission confirmation implementation')
    # Pure JSON metadata creation only; frozen positive code checks all refs.
    devreg = io.read(reg['positive_template_registration_ref']['path'])
    cohort = dict(prior_root=str(root), prior_group='confirm',
        source_names=[row['video_id'] for row in io.read(reg['reference_completion_ref']['path'])['accepted']],
        old_cpu_admission=ref(root/'cpu_acceptance_confirm.json'),
        old_b0=dict(admission=ref(root/'gpu_admission_confirm_B0.json'),
            gpu_completion=ref(root/'confirm/B0/gpu_01/completion.json'), replay_completion=ref(root/'confirm/B0/replay_01/completion.json')),
        old_verify=dict(admission=ref(root/'gpu_admission_confirm_VERIFY.json'),
            gpu_completion=ref(root/'confirm/VERIFY/gpu_01/completion.json'), replay_completion=ref(root/'confirm/VERIFY/replay_01/completion.json'),
            export=ref(root/'confirm/VERIFY/verification_export.json')),
        reference_completion=reg['reference_completion_ref'])
    budget = reg['gpu_budget']['POSITIVE']
    required = dict(reg['required_files']); required.update(devreg['required_files'])
    required[str(root/'positive_fresh_registration.json')] = io.sha(root/'positive_fresh_registration.json')
    value = dict(devreg, status='REGISTERED_ROLE_POSITIVE_CONFIRM_V1', activation_contract_ref=reg['activation_contract_ref'], role_runtime_ref=reg['role_runtime_ref'], stage_group='confirm', protocol_ref=reg['protocol_ref'],
        authorization_ref=reg['authorization_ref'], dev_selection_ref=reg['dev_selection_ref'],
        required_files=required, adopted_source_groups=dict(confirm=[cohort]),
        gpu_budget=dict(confirm=dict(budget, deadline=reg['deadline'])), production_admitted=False)
    path = positive_root/'registration_confirm.json'; io.save(path, value)
    return path, code


def main(root, positive_root):
    io.host(cpu=False); io.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '0', 'Parent must retain explicit CUDA0')
    root, positive_root = io.root_path(root), io.root_path(positive_root); reg = registration(root)
    io.require(root.parent == positive_root and root.name == 'fresh_01', 'Independent fresh source evidence root required')
    media_files(root, reg)
    state = root/'confirm/chain_01'; state.mkdir(parents=True, exist_ok=False)
    io.save(state/'started.json', dict(pid=os.getpid(), utc=io.utc(), registration_ref=ref(root/'positive_fresh_registration.json'),
        parent_CUDA=os.environ['CUDA_VISIBLE_DEVICES'], no_automatic_retry=True, production_admitted=False))
    code = Path(__file__).parent; stage = 'PREPARE_ALL_NATIVE_INPUTS'
    try:
        child(state, 'prepare_inputs', [sys.executable, '-B', '-u', str(code/'prepare_inputs.py'), '--root', str(root)])
        stage = 'FIRST_ALL_NATIVE_INPUT_QA_PRE_GPU'
        child(state, 'first_input_qa', [sys.executable, '-B', '-u', str(code/'first_input_qa.py'), '--root', str(root)])
        stage = 'B0'; gate, path = admit(root, reg, stage); gpu(state, root, gate, path, code/'pilot_runtime.py')
        stage = 'B0_OUTPUT_ONLY_QA'
        child(state, 'B0_replay', [sys.executable, '-B', '-u', str(code/'pilot_runtime.py'), 'replay', '--root', str(root), '--group', 'confirm'])
        stage = 'VERIFY_PROMPT_PREPARATION'
        child(state, 'VERIFY_prepare', [sys.executable, '-B', '-u', str(code/'pilot_verify.py'), 'prepare', '--root', str(root), '--group', 'confirm'])
        stage = 'VERIFY_FIRST_INPUT_QA_PRE_GPU'
        child(state, 'VERIFY_first_input_qa', [sys.executable, '-B', '-u', str(code/'verify_input_qa.py'), '--root', str(root)])
        count = io.read(root/'confirm/VERIFY/cpu_01/completion.json')['expected_input_count']
        if not count:
            io.save(state/'completion.json', dict(status='STOP_POSITIVE_FRESH_NO_B0_CANDIDATES_RECALL_GAIN_IMPOSSIBLE',
                actual_VERIFY_calls=0, actual_POSITIVE_calls=0, complete_B0_actual=True, engineering_failure=False,
                production_admitted=False, no_fixed40_426_or_package_started=True))
            return
        stage = 'VERIFY'; gate, path = admit(root, reg, stage); gpu(state, root, gate, path, code/'pilot_verify.py')
        stage = 'VERIFY_OUTPUT_ONLY_QA'
        child(state, 'VERIFY_replay', [sys.executable, '-B', '-u', str(code/'pilot_verify.py'), 'replay', '--root', str(root), '--group', 'confirm'])
        stage = 'REGISTER_FROZEN_POSITIVE_CONFIRM'
        positive_reg_path, positive_code = positive_registration(root, positive_root, reg)
        for action in ('prepare', 'input_qa', 'admit'):
            stage = 'POSITIVE_'+action.upper()
            child(state, stage, [sys.executable, '-B', '-u', str(positive_code/'positive_runtime.py'), action,
                '--root', str(positive_root), '--group', 'confirm'])
        gate_path = positive_root/'gpu_admission_confirm_POSITIVE.json'; gate = io.read(gate_path)
        if gate['expected_input_count'] == 0:
            io.save(state/'completion.json', dict(status='STOP_POSITIVE_FRESH_NO_NEW_OLD_KEEP_CANDIDATES_RECALL_GAIN_IMPOSSIBLE',
                actual_POSITIVE_calls=0, engineering_failure=False, production_admitted=False, no_fixed40_426_or_package_started=True))
            return
        stage = 'POSITIVE'; gate['stage'] = stage
        gpu(state, positive_root, gate, gate_path, positive_code/'positive_runtime.py')
        stage = 'POSITIVE_OUTPUT_ONLY_QA'
        child(state, stage, [sys.executable, '-B', '-u', str(positive_code/'positive_runtime.py'), 'replay',
            '--root', str(positive_root), '--group', 'confirm'])
        stage = 'FIRST_FRESH_EIGHT_GATE_EVALUATION'
        argv = [sys.executable, '-B', '-u', str(positive_code/'positive_evaluate.py'), '--root', str(positive_root), '--group', 'confirm']
        with (state/'comparison.log').open('xb') as log:
            result = subprocess.run(argv, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), stdout=log, stderr=subprocess.STDOUT)
        io.require(result.returncode in (0, 5), 'Engineering failure cannot become scientific EMPTY/UNKNOWN')
        path = positive_root/'confirm/comparison_01/result.json'; comparison = io.read(path)
        expected = 'PASS_ROLE_FRESH_CONFIRM_PENDING_FIXED40' if result.returncode == 0 else 'STOP_ROLE_FRESH_CONFIRM_REJECTED'
        io.require(comparison['status'] == expected and len(comparison['cases']) == 4 and len(comparison['conditions']) == 8 and
            all(type(v) is bool for v in comparison['conditions'].values()) and
            (result.returncode == 0) == all(comparison['conditions'].values()), 'First full fresh scientific gate/exit result differs')
        io.save(state/'completion.json', dict(status=expected, utc=io.utc(), comparison_ref=ref(path),
            positive_registration_ref=ref(positive_reg_path), production_admitted=False, no_fixed40_426_or_package_started=True))
    except BaseException as error:
        io.save(state/'failure.json', dict(stage=stage, error=repr(error), traceback=traceback.format_exc(),
            preserve_all_raw_and_success=True, no_automatic_resume=True, no_UNKNOWN_or_EMPTY_fallback=True, production_admitted=False))
        raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--positive-root',type=Path,required=True); args=parser.parse_args()
    main(args.root,args.positive_root)
