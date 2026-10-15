"""One first fresh-confirmation chain; never resumes or starts production.

Media/native-clock acquisition is a separately completed prerequisite. CPU
children hide only their own CUDA. The parent retains its registered GPU index.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

import model_common as io
from prepare_fresh_inputs import (require_fresh_inputs, bound_reference_completion,
                                  confirm_media_files)


def first_launch(root, group):
    io.require(group == 'confirm', 'Only the first fresh confirmation can run')
    require_fresh_inputs(root, group)
    for pattern in ('chain_*', 'admission_*', 'input_admission_*', 'B0', 'VERIFY', 'comparison_*'):
        io.require(not any((root/group).glob(pattern)), 'Existing fresh stage must not be restarted: '+pattern)
    for name in ('cpu_acceptance_confirm.json', 'source_lock_confirm_B0.json', 'source_lock_confirm_VERIFY.json',
                 'gpu_admission_confirm_B0.json', 'gpu_admission_confirm_VERIFY.json'):
        io.require(not (root/name).exists(), 'Earlier fresh accepted/started work requires explicit recovery: '+name)
    ledger = io.HOME_ROOT/'improvement_round1/gpu_ledger.jsonl'
    names = set(io.JOBS.values())
    io.require(not any(row['name'] in names for row in io.rows(ledger)), 'Fresh job name already has a ledger entry')
    for name in names:
        io.require(not (io.RUN/'controller'/(name+'.resource.json')).exists(), 'Fresh job already has a resource terminal')
    active_path = io.HOME_ROOT/'improvement_round1/active_gpu_job.json'
    if active_path.exists():
        io.require(io.read(active_path).get('name') not in names, 'This fresh job is already active')


def snapshot(root):
    return dict(utc=io.utc(), host=__import__('socket').gethostname(), cpu_count=os.cpu_count(),
        load=list(os.getloadavg()), memory=Path('/proc/meminfo').read_text(), disk=list(shutil.disk_usage(root)),
        active_processes=subprocess.run(['ps', '-eo', 'pid,ppid,stat,pcpu,pmem,rss,comm', '--sort=-pcpu'],
            capture_output=True, text=True, check=True).stdout.splitlines()[:18],
        gpu=subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,utilization.gpu',
                            '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True).stdout)


def child(root, state, name, arguments):
    argv = [sys.executable, '-B', '-u', str(root/'code'/name), *arguments]
    # This environment belongs only to this CPU child, never to the parent.
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='')
    label = arguments[0] if arguments and not arguments[0].startswith('-') else 'run'
    with (state/(name+'.'+label+'.log')).open('xb') as log:
        result = subprocess.run(argv, env=environment, stdout=log, stderr=subprocess.STDOUT)
    io.require(result.returncode == 0, 'Actual CPU child failed; keep all successful work: '+name)


def verify_lock(root, group):
    cpu_path = root/group/'VERIFY/cpu_01/completion.json'
    cpu = io.read(cpu_path)
    files = dict(io.read(root/'source_lock_confirm_B0.json')['files'])

    def add(path, digest=None):
        path = io.checked(path, digest)
        actual = io.sha(path)
        io.require(str(path) not in files or files[str(path)] == actual, 'Previously frozen input or source changed')
        files[str(path)] = actual

    add(cpu_path)
    add(cpu['requests_path'], cpu['requests_sha256'])
    for prefix in ('b0_cpu_acceptance', 'b0_source_lock', 'b0_admission', 'b0_gpu_completion', 'b0_replay_completion'):
        add(cpu['bindings'][prefix+'_path'], cpu['bindings'][prefix+'_sha256'])
    for entry in cpu['entries']:
        add(entry['input_path'], entry['input_sha256'])
        add(entry['proof_path'], entry['proof_sha256'])
        proof, request = io.read(entry['proof_path']), io.read(entry['input_path'])
        for prefix in ('token_cache', 'original_vision_cache'):
            add(proof[prefix+'_path'], proof[prefix+'_sha256'])
        for ref in request['original_evidence'].values():
            add(ref['path'], ref['sha256'])
        done = io.read(request['original_evidence']['done']['path'])
        add(done['raw_path'], done['raw_sha256'])
        add(Path(request['original_evidence']['done']['path']).parent/'request.json', done['request_sha256'])
    add(root/group/'B0/gpu_01/model_identity.json')
    for name, digest in io.code_files().items():
        add(name, digest)
    io.save(root/'source_lock_confirm_VERIFY.json', dict(files=files, group=group, stage='VERIFY', utc=io.utc()))
    return cpu_path


def admit(root, state, group, stage):
    fresh = io.fresh_gate(root, group)
    media_files = confirm_media_files(root, group, fresh)
    cpu_path = root/'cpu_acceptance_confirm.json' if stage == 'B0' else verify_lock(root, group)
    cpu = io.read(cpu_path)
    count = len(cpu['entries'])
    maximum = fresh['gpu_budget']['per_group_max_'+stage+'_actual_calls']
    io.require(0 < count <= maximum, 'Actual complete stage input budget exceeded or empty')
    lock_path = root/('source_lock_confirm_'+stage+'.json')
    required = (set(io.code_files()) | io.runtime_dependencies() | io.processor_assets() | set(fresh['files']) |
                set(media_files) | {str(io.CONFIG), str(cpu_path), fresh['registration_path']})
    required.update(str(io.CV_CODE/name) for name in ('cv_contract.py', 'cv_grammar.py', 'cv_tokens.py'))
    io.validate_lock(lock_path, required)
    io.save(state/('resources_before_'+stage+'.json'), snapshot(root))
    io.require(not (io.RUN/'controller'/(io.JOBS[stage]+'.resource.json')).exists(), 'Job already has a terminal; no repeated success')
    pointer_path, completion_path = bound_reference_completion(root, group)
    gate = dict(status=io.ADMISSION_STATUS, group=group, stage=stage, expected_input_count=count,
        gpu_job_name=io.JOBS[stage], max_seconds=fresh['gpu_budget']['confirm_'+stage+'_max_seconds'],
        deadline=fresh['registration']['deadline'], cpu_acceptance_path=str(cpu_path), cpu_acceptance_sha256=io.sha(cpu_path),
        source_lock_path=str(lock_path), source_lock_sha256=io.sha(lock_path), source_scope='EXTERNAL_NONTEST_ONLY',
        model_parameters=io.MODEL_PARAMETERS, optimizer_updates=0, reference_available_to_inference=False,
        reference_pointer_sha256=io.sha(pointer_path), reference_completion_sha256=io.sha(completion_path),
        **{key: fresh[key] for key in ('protocol_sha256', 'authorization_sha256', 'selection_sha256',
                                      'result_sha256', 'registration_sha256')})
    io.save(root/('gpu_admission_confirm_'+stage+'.json'), gate)
    return gate


def gpu(root, state, group, stage, gate):
    io.deadline(gate)
    script = 'pilot_runtime.py' if stage == 'B0' else 'pilot_verify.py'
    argv = [sys.executable, '-B', str(io.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
        '--name', gate['gpu_job_name'], '--max-seconds', str(gate['max_seconds']),
        '--planned-output-bytes', str(32 << 20), '--capacity-reason',
        str(gate['expected_input_count'])+' actual fresh same-B inputs; complete CPU caches retained, raw output and independent QA only.',
        '--queue-seconds', '1800', '--', sys.executable, '-B', '-u', str(root/'code'/script),
        'infer', '--root', str(root), '--group', group]
    io.save(state/('gpu_launch_'+stage+'.json'), dict(argv=argv, utc=io.utc(),
        admission_sha256=io.sha(root/('gpu_admission_confirm_'+stage+'.json'))))
    with (state/('gpu_'+stage+'.log')).open('xb') as log:
        result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT)
    io.require(result.returncode == 0, 'Unique actual GPU wrapper failed; no automatic rerun')
    io.terminal(gate)


def stage_receipt(root, group, stage):
    gate_path = root/('gpu_admission_confirm_'+stage+'.json')
    gate = io.read(gate_path)
    resource, resource_sha = io.terminal(gate)
    gpu_dir, qa_dir = root/group/stage/'gpu_01', root/group/stage/'replay_01'
    io.completed_job(gpu_dir, gate, gate_path, gate['expected_input_count'], stage)
    qa_path = qa_dir/'completion.json'
    qa = io.read(qa_path)
    io.require(qa['status'] == 'PASS_ALL_RECALL_'+stage+'_INDEPENDENT_REPLAYS_NOT_QUALITY' and
        qa['calls'] == gate['expected_input_count'] and len(qa['proofs']) == gate['expected_input_count'] and
        len({row['case_id'] for row in qa['proofs']}) == gate['expected_input_count'] and
        qa['gpu_completion_sha256'] == io.sha(gpu_dir/'completion.json') and
        qa['resource_terminal_sha256'] == resource_sha and qa['CPU_only'] is True and qa['CUDA_initialized'] is False,
        'Entire first independent QA denominator and unique terminal must be retained')
    for row in qa['proofs']:
        io.checked(row['proof_path'], row['proof_sha256'])
    resource_path = io.RUN/'controller'/(gate['gpu_job_name']+'.resource.json')
    return dict(calls=gate['expected_input_count'], resource=resource,
        resource_ref=dict(path=str(resource_path), sha256=resource_sha),
        admission_ref=dict(path=str(gate_path), sha256=io.sha(gate_path)),
        gpu_completion_ref=dict(path=str(gpu_dir/'completion.json'), sha256=io.sha(gpu_dir/'completion.json')),
        first_QA_completion_ref=dict(path=str(qa_path), sha256=io.sha(qa_path)))


def evaluate(root, state):
    argv = [sys.executable, '-B', str(root/'code/evaluate_confirmation.py'), '--root', str(root)]
    with (state/'comparison.log').open('xb') as log:
        result = subprocess.run(argv, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''), stdout=log, stderr=subprocess.STDOUT)
    io.require(result.returncode in (0, 5), 'Fresh confirmation evaluation engineering failure')
    path = root/'confirm/comparison_01/result.json'
    comparison = io.read(path)
    expected = 'PASS_CONSENSUS_FRESH_CONFIRM_PENDING_FIXED40' if result.returncode == 0 else 'STOP_CONSENSUS_FRESH_CONFIRM_REJECTED'
    io.require(comparison['status'] == expected and len(comparison['cases']) == 4 and
        set(comparison['conditions']) == set(io.CONDITIONS) and
        all(type(value) is bool for value in comparison['conditions'].values()) and
        comparison['bindings']['protocol_sha256'] == io.PROTOCOL_SHA and
        comparison['bindings']['registration_sha256'] == io.sha(root/'fresh_confirm_registration.json') and
        comparison['bindings']['verification_export_sha256'] == io.sha(root/'confirm/VERIFY/verification_export.json') and
        comparison['bindings']['cpu_acceptance_sha256'] == io.sha(root/'cpu_acceptance_confirm.json') and
        comparison['bindings']['first_B0_QA_sha256'] == io.sha(root/'confirm/B0/replay_01/completion.json') and
        comparison['bindings']['reference_completion_sha256'] == io.read(root/'reference_completion_confirm.json')['sha256'] and
        ((result.returncode == 0) == all(value is True for value in comparison['conditions'].values())),
        'Actual fresh four-source result/exit status/input bindings disagree')
    return expected, path


def main(root, group):
    io.host(cpu=False)
    root = io.root_path(root)
    fresh = io.fresh_gate(root, group)
    io.require(Path(__file__).resolve().parent == root/'code', 'Only separately deployed fresh code may run')
    confirm_media_files(root, group, fresh)
    bound_reference_completion(root, group)
    first_launch(root, group)
    state = root/group/'chain_01'
    state.mkdir(exist_ok=False)
    io.save(state/'started.json', dict(pid=os.getpid(), utc=io.utc(), parent_CUDA=os.environ['CUDA_VISIBLE_DEVICES'],
        registration_sha256=fresh['registration_sha256'], protocol_sha256=fresh['protocol_sha256'],
        controller_sha256=io.sha(__file__), fresh_confirmation_only=True, production_admitted=False))
    current = 'CPU_PREPARATION'
    try:
        child(root, state, 'prepare_fresh_inputs.py', ['--root', str(root), '--group', group])
        current = 'INDEPENDENT_CPU_ADMISSION'
        child(root, state, 'admit_fresh_inputs.py', ['--root', str(root), '--group', group])
        current = 'B0'
        gate = admit(root, state, group, 'B0')
        gpu(root, state, group, 'B0', gate)
        current = 'B0_FIRST_QA'
        child(root, state, 'pilot_runtime.py', ['replay', '--root', str(root), '--group', group])
        B0 = stage_receipt(root, group, 'B0')
        current = 'VERIFY_PREPARATION'
        child(root, state, 'pilot_verify.py', ['prepare', '--root', str(root), '--group', group])
        cpu = io.read(root/group/'VERIFY/cpu_01/completion.json')
        if cpu['entries']:
            current = 'VERIFY'
            gate = admit(root, state, group, 'VERIFY')
            gpu(root, state, group, 'VERIFY', gate)
            current = 'VERIFY_FIRST_QA'
            child(root, state, 'pilot_verify.py', ['replay', '--root', str(root), '--group', group])
            VERIFY = stage_receipt(root, group, 'VERIFY')
        else:
            current = 'LEGAL_ZERO_VERIFY_EXPORT'
            child(root, state, 'pilot_verify.py', ['zero_export', '--root', str(root), '--group', group])
            VERIFY = dict(calls=0, GPU_started=False, first_QA_not_applicable=True)
        current = 'FRESH_CONFIRMATION_EVALUATION'
        io.require(io.sha(root/'fresh_confirm_registration.json') == fresh['registration_sha256'],
                   'The original fresh registration changed during execution')
        status, result_path = evaluate(root, state)
        io.require(VERIFY['calls'] != 0 or status == 'STOP_CONSENSUS_FRESH_CONFIRM_REJECTED',
                   'No real candidate additions must stop scientific confirmation')
        io.save(state/'completion.json', dict(status=status, group=group, utc=io.utc(), B0=B0, VERIFY=VERIFY,
            comparison_ref=dict(path=str(result_path), sha256=io.sha(result_path)),
            registration_sha256=fresh['registration_sha256'], production_admitted=False,
            no_fixed40_426_or_package_started=True, successful_calls_or_QA_repeated=False))
    except BaseException as error:
        io.save(state/'failure.json', dict(stage=current, error=repr(error), traceback=traceback.format_exc(), utc=io.utc(),
            preserve_all_success=True, do_not_repeat_successful_calls_or_QA=True, production_admitted=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--group', choices=('confirm',), required=True)
    args = parser.parse_args()
    main(args.root, args.group)
