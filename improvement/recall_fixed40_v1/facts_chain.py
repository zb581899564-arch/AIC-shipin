"""Independent fixed40 execution chain; no summary metric, veto or production.

This code only runs when explicitly invoked against a complete frozen phase
registration. No stage is retried/resumed and no existing successful output is
overwritten. The final CPU export adopts already-completed first QA receipts.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

import facts_common as io


def ref(path):
    return dict(path=str(path), sha256=io.sha(path))


def child(root, state, script, args):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='')
    argv = [sys.executable, '-B', '-u', str(root/'code'/script), *args]
    name = script+'.'+(args[0] if args and not args[0].startswith('--') else 'main')+'.log'
    with (state/name).open('xb') as log:
        completed = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT)
    io.require(completed.returncode == 0, 'Actual CPU child failed; preserve all success without retry: '+script)


def snapshot(root):
    return dict(utc=io.utc(), host=__import__('socket').gethostname(), cpu_count=os.cpu_count(),
        load_average=list(os.getloadavg()), memory=Path('/proc/meminfo').read_text(), disk=list(shutil.disk_usage(root)),
        active_processes=subprocess.run(['ps', '-eo', 'pid,ppid,stat,pcpu,pmem,rss,comm', '--sort=-pcpu'],
            capture_output=True, text=True, check=True).stdout.splitlines()[:18],
        gpu=subprocess.run(['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,utilization.gpu',
                            '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True).stdout)


def verify_lock(root):
    cpu_path = root/'facts/VERIFY/cpu_01/completion.json'
    cpu = io.read(cpu_path)
    files = dict(io.read(root/'source_lock_facts_B0.json')['files'])
    def add(path, digest=None):
        path = io.checked(path, digest)
        actual = io.sha(path)
        io.require(str(path) not in files or files[str(path)] == actual, 'Previously frozen successful evidence changed')
        files[str(path)] = actual
    add(cpu_path); add(cpu['requests_path'], cpu['requests_sha256'])
    for prefix in ('b0_cpu_acceptance', 'b0_source_lock', 'b0_admission', 'b0_gpu_completion', 'b0_replay_completion'):
        add(cpu['bindings'][prefix+'_path'], cpu['bindings'][prefix+'_sha256'])
    for entry in cpu['entries']:
        add(entry['input_path'], entry['input_sha256']); add(entry['proof_path'], entry['proof_sha256'])
        proof, request = io.read(entry['proof_path']), io.read(entry['input_path'])
        for prefix in ('token_cache', 'original_vision_cache'):
            add(proof[prefix+'_path'], proof[prefix+'_sha256'])
        for original in request['original_evidence'].values():
            add(original['path'], original['sha256'])
    for path, digest in io.code_files().items():
        add(path, digest)
    io.save(root/'source_lock_facts_VERIFY.json', dict(schema='FIXED40_SOURCE_CODE_INPUT_LOCK_V1',
        group='facts', stage='VERIFY', files=files, registration_sha256=io.sha(root/'registration.json'), utc=io.utc()))
    return cpu_path


def admit(root, state, stage, reg):
    cpu_path = root/'cpu_acceptance_facts.json' if stage == 'B0' else verify_lock(root)
    cpu = io.read(cpu_path)
    count = len(cpu['entries'])
    io.require((stage == 'B0' and count == io.INPUT_COUNT) or
               (stage == 'VERIFY' and 0 < count <= io.VERIFY_MAX_CALLS), 'Exact complete actual fixed40 stage budget required')
    lock_path = root/('source_lock_facts_'+stage+'.json')
    io.validate_lock(lock_path, set(reg['required_files']) | {str(root/'registration.json'), str(cpu_path)})
    io.deadline(reg)
    job = io.JOB_NAMES[stage]
    ledger = io.rows(io.HOME_ROOT/'improvement_round1/gpu_ledger.jsonl')
    io.require(not (io.RUN/'controller'/(job+'.resource.json')).exists() and not any(row['name'] == job for row in ledger),
               'Unique job already has a successful or failed history; never repeat it')
    io.save(state/('resources_before_'+stage+'.json'), snapshot(root))
    gate = dict(status=io.ADMISSION_STATUS, group='facts', stage=stage, expected_input_count=count, gpu_job_name=job,
        deadline=reg['deadline'], cpu_acceptance_path=str(cpu_path), cpu_acceptance_sha256=io.sha(cpu_path),
        source_lock_path=str(lock_path), source_lock_sha256=io.sha(lock_path),
        registration_path=str(root/'registration.json'), registration_sha256=io.sha(root/'registration.json'),
        source_scope='EXTERNAL_NONTEST_ONLY', model_parameters=io.MODEL_PARAMETERS,
        optimizer_updates=0, reference_available_to_inference=False)
    io.save(root/('gpu_admission_facts_'+stage+'.json'), gate)
    return gate


def gpu(root, state, stage, gate):
    script = 'facts_infer.py' if stage == 'B0' else 'facts_verify.py'
    maximum = io.GPU_BUDGET[stage+'_max_seconds']
    # Only small per-call raw tokens/signatures/decision records are new at this
    # point; input tensors already exist. The shared wrapper owns live capacity.
    planned_output = max(1 << 20, gate['expected_input_count']*(256*128+64*1024))
    argv = [sys.executable, '-B', str(io.RUN/'resource_unlimited_v1_20261007/gpu_run.py'),
        '--name', gate['gpu_job_name'], '--max-seconds', str(maximum), '--planned-output-bytes', str(planned_output),
        '--capacity-reason', str(gate['expected_input_count'])+' new registered fixed40 overlap inputs; CPU inputs exist; only bounded raw/signature/decision output is added.',
        '--queue-seconds', '1800', '--', sys.executable, '-B', '-u', str(root/'code'/script),
        'infer', '--root', str(root), '--group', 'facts']
    io.save(state/('gpu_launch_'+stage+'.json'), dict(argv=argv, utc=io.utc(),
        admission_sha256=io.sha(root/('gpu_admission_facts_'+stage+'.json'))))
    with (state/('gpu_'+stage+'.log')).open('xb') as log:
        result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT)
    io.require(result.returncode == 0, 'Actual unique shared GPU wrapper failed; no automatic recovery')
    io.terminal(gate)


def verify_prior_first_qa(root, stage, count):
    """Read/bind completed actual QA; never re-encode or repeat a replay."""
    gate_path = root/('gpu_admission_facts_'+stage+'.json')
    gate = io.read(gate_path)
    terminal, terminal_sha = io.terminal(gate)
    gpu_root, qa_root = root/'facts'/stage/'gpu_01', root/'facts'/stage/'replay_01'
    completion, by_id = io.completed_job(gpu_root, gate, gate_path, count, stage)
    qa = io.read(qa_root/'completion.json')
    io.require(qa['status'] == 'PASS_ALL_FIXED40_'+stage+'_INDEPENDENT_REPLAYS_NOT_QUALITY' and
        qa['group'] == 'facts' and qa['calls'] == count and len(qa['proofs']) == count and
        qa['CPU_only'] is True and qa['CUDA_initialized'] is False and qa['new_model_calls'] == 0 and
        qa['gpu_completion_sha256'] == io.sha(gpu_root/'completion.json') and qa['resource_terminal_sha256'] == terminal_sha,
        'Actual complete first independent '+stage+' QA required')
    identities = []
    for entry in qa['proofs']:
        proof = io.read(io.checked(entry['proof_path'], entry['proof_sha256']))
        current = entry['case_id']
        io.require(current in by_id and proof['case_id'] == current and proof['CPU_only'] is True and
            proof['new_model_calls'] == 0 and proof['done_sha256'] == by_id[current]['done_sha256'] and
            io.sha(by_id[current]['done_path']) == by_id[current]['done_sha256'], 'Completed first QA/input-output identity changed')
        identities.append(current)
    io.require(len(set(identities)) == count and set(identities) == set(by_id), 'Complete unique first QA denominator changed')
    return ref(qa_root/'completion.json'), ref(io.RUN/'controller'/(gate['gpu_job_name']+'.resource.json'))


def actual_call_refs(root, stage):
    """Explicit raw/request/done/first-QA bindings for every actual call."""
    gpu_root, qa_root = root/'facts'/stage/'gpu_01', root/'facts'/stage/'replay_01'
    accepted = {row['case_id']: row for row in io.read(gpu_root/'completion.json')['entries']}
    replayed = {row['case_id']: row for row in io.read(qa_root/'completion.json')['proofs']}
    io.require(set(accepted) == set(replayed), 'Every actual call needs its already-completed first independent QA')
    result = {}
    for case, entry in accepted.items():
        folder = gpu_root/case
        done_path = io.checked(entry['done_path'], entry['done_sha256'])
        qa_path = io.checked(replayed[case]['proof_path'], replayed[case]['proof_sha256'])
        done, qa = io.read(done_path), io.read(qa_path)
        io.require(done_path == folder/'done.json' and done['case_id'] == qa['case_id'] == case and
            done['raw_path'] == str(folder/'raw.json') and qa['done_sha256'] == entry['done_sha256'],
            'Actual case/raw/done/first-QA paths or identity changed')
        raw_path = io.checked(folder/'raw.json', done['raw_sha256'])
        request_path = io.checked(folder/'request.json', done['request_sha256'])
        result[case] = dict(done_ref=ref(done_path), raw_ref=ref(raw_path), request_ref=ref(request_path),
                            first_independent_qa_ref=ref(qa_path), first_qa_ref=ref(qa_path), status=done['status'])
        if stage == 'B0':
            io.require(qa['segments'] == done['segments'] and qa['native_ranges'] == done['native_ranges'], 'Actual B0 first-QA segments changed')
            result[case].update(segments=done['segments'], native_ranges=done['native_ranges'])
        else:
            io.require(qa['decision_result'] == done['decision_result'], 'Actual VERIFY first-QA decision changed')
            result[case]['decision_result'] = done['decision_result']
            result[case]['original_native_range'] = qa['original_native_range']
    return result


def export_execution(root):
    """CPU-only collation of actual execution and previously completed first QA."""
    io.host(cpu=True)
    reg = io.registration(root)
    acceptance = io.read(root/'cpu_acceptance_facts.json')
    io.require(acceptance['source_count'] == io.SOURCE_COUNT and acceptance['expected_input_count'] == len(acceptance['entries']) == io.INPUT_COUNT,
               'Complete actual fixed40 accepted input denominator required')
    first_qa, terminal = verify_prior_first_qa(root, 'B0', io.INPUT_COUNT)
    qa_refs, terminal_refs = [first_qa], [terminal]
    verify_cpu = io.read(root/'facts/VERIFY/cpu_01/completion.json')
    export_path = root/'facts/VERIFY/verification_export.json'
    exported = io.read(export_path)
    count = len(verify_cpu['entries'])
    if count:
        io.require(0 < count <= io.VERIFY_MAX_CALLS and len(exported['events']) == count and
            exported['status'] == 'PASS_FIXED40_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY', 'Actual complete decision export required')
        first_qa, terminal = verify_prior_first_qa(root, 'VERIFY', count)
        io.require(exported['independent_replay_completion_sha256'] == first_qa['sha256'], 'Decision export/first QA changed')
        qa_refs.append(first_qa); terminal_refs.append(terminal)
    else:
        io.require(exported['status'] == 'PASS_FIXED40_VERIFY_ZERO_CANDIDATES_AFTER_COMPLETE_B0_QA' and exported['events'] == [] and
            exported['actual_VERIFY_model_calls'] == exported['actual_VERIFY_GPU_jobs'] == 0 and
            exported['B0_independent_replay_completion_sha256'] == qa_refs[0]['sha256'], 'Missing actual work cannot become zero decisions')
    metadata = {entry['case_id']: io.read(io.checked(entry['input_path'], entry['input_sha256'])) for entry in acceptance['entries']}
    B0_calls = actual_call_refs(root, 'B0')
    VERIFY_calls = actual_call_refs(root, 'VERIFY') if count else {}
    VERIFY_inputs = {entry['case_id']: entry for entry in verify_cpu['entries']}
    io.require(list(VERIFY_calls) == [event['decision_result']['request_id'] for event in exported['events']],
               'Complete VERIFY call/export order differs')
    by_source = {meta['source_name']: [] for meta in metadata.values()}
    by_case = {source['case_id']: [] for source in reg['sources']}
    io.require(len(metadata) == io.INPUT_COUNT and len(by_source) == io.SOURCE_COUNT, 'Actual fixed source/view denominator differs')
    all_events = set()
    for event in exported['events']:
        decision = event['decision_result']['decision']
        io.require(event['event_id'] not in all_events and event['original_case_id'] in metadata and
            event['source_name'] == metadata[event['original_case_id']]['source_name'] and
            decision in ('KEEP', 'UNKNOWN', 'DROP') and event['decision_result']['successful_model_call_required'] is True and
            event['eligible_for_new_addition'] == (decision == 'KEEP'), 'Actual explicit decision/source binding differs')
        all_events.add(event['event_id'])
        io.require(event['decision_result']['request_id'] in VERIFY_calls and
            VERIFY_calls[event['decision_result']['request_id']]['decision_result'] == event['decision_result'],
            'Exported semantic decision is not bound to its complete actual raw/first-QA call')
        if decision == 'KEEP':
            by_source[event['source_name']].append(event['event_id'])
            by_case[metadata[event['original_case_id']]['fixed_case_id']].append(event['event_id'])
    output = root/'execution_export_01'; output.mkdir(exist_ok=False)
    execution_path = output/'execution_receipt.json'
    io.save(execution_path, dict(status='PASS_FIXED40_ACTUAL_EXECUTION_NOT_FACT_QUALITY',
        registration_sha256=io.sha(root/'registration.json'), geometry_scope=reg['scope'],
        all_registered_views_completed=True, registered_view_count=io.INPUT_COUNT, completed_view_count=len(metadata),
        failed_views=0, source_count=io.SOURCE_COUNT, group='facts',
        registered_views=[dict(case_id=view['fixed_case_id'], view_id=view['case_id'],
            start_exact=view['window_start'], end_exact=view['window_end']) for view in reg['views']],
        registered_view_plan=reg['views'],
        actual_inputs=[dict(case_id=entry['case_id'], fixed_case_id=metadata[entry['case_id']]['fixed_case_id'],
            source_name=metadata[entry['case_id']]['source_name'],
            window_start=metadata[entry['case_id']]['window_start'], window_end=metadata[entry['case_id']]['window_end'],
            input_ref=dict(path=entry['input_path'], sha256=entry['input_sha256']),
            CPU_proof_ref=dict(path=entry['proof_path'], sha256=entry['proof_sha256']),
            **B0_calls[entry['case_id']])
            for entry in acceptance['entries']],
        verification_decisions=[dict(request_id=event['decision_result']['request_id'], event_id=event['event_id'],
            original_case_id=event['original_case_id'], original_segment_index=event['original_segment_index'],
            original_interval_exact=event['original_interval_exact'],
            input_ref=dict(path=VERIFY_inputs[event['decision_result']['request_id']]['input_path'],
                           sha256=VERIFY_inputs[event['decision_result']['request_id']]['input_sha256']),
            CPU_proof_ref=dict(path=VERIFY_inputs[event['decision_result']['request_id']]['proof_path'],
                               sha256=VERIFY_inputs[event['decision_result']['request_id']]['proof_sha256']),
            **VERIFY_calls[event['decision_result']['request_id']])
                                for event in exported['events']],
        keep_event_ids_by_source_name=by_source,
        keep_event_ids_by_case=by_case,
        resource_terminal_refs=terminal_refs, first_independent_stage_qa_refs=qa_refs,
        B0_actual_model_calls=io.INPUT_COUNT, VERIFY_actual_model_calls=count,
        model_parameters=io.MODEL_PARAMETERS, new_optimizer_updates=0,
        verification_export_ref=ref(export_path), source_scope='EXTERNAL_NONTEST_ONLY',
        new_baseline_model_calls=0, human_summary_evaluation_performed=False, fact_quality='NOT_EVALUATED', production_admitted=False))
    import torch
    io.require(not torch.cuda.is_initialized(), 'CPU first-QA manifest collation initialized CUDA')
    io.save(output/'first_independent_qa.json', dict(status='PASS_FIXED40_FIRST_QA_NOT_FACT_QUALITY',
        actual_execution_receipt_sha256=io.sha(execution_path), CPU_only=True, CUDA_initialized=False,
        complete_view_and_decision_denominators=True, adopted_completed_first_stage_qa_refs=qa_refs,
        repeated_first_input_or_output_replays=0, media_decodes=0, vision_processor_calls=0, new_model_calls=0,
        scientific_fact_gate='NOT_EVALUATED', production_admitted=False))


def main(root):
    io.host(cpu=False)
    root = io.root_path(root)
    reg = io.registration(root)
    io.deadline(reg)
    state = root/'facts/chain_01'; state.mkdir(parents=True, exist_ok=False)
    io.save(state/'started.json', dict(pid=os.getpid(), utc=io.utc(), group='facts', parent_CUDA=os.environ['CUDA_VISIBLE_DEVICES'],
        registration_sha256=io.sha(root/'registration.json'), controller_sha256=io.sha(__file__)))
    current = 'CPU_PREPARATION'
    try:
        child(root, state, 'facts_prepare.py', ['--root', str(root), '--group', 'facts'])
        current = 'INDEPENDENT_CPU_CACHE_ADMISSION'
        child(root, state, 'facts_admit.py', ['--root', str(root), '--group', 'facts'])
        current = 'B0'; gate = admit(root, state, 'B0', reg); gpu(root, state, 'B0', gate)
        current = 'B0_FIRST_INDEPENDENT_REPLAY'
        child(root, state, 'facts_infer.py', ['replay', '--root', str(root), '--group', 'facts'])
        current = 'VERIFY_PROMPT_ONLY_CPU_PREPARE'
        child(root, state, 'facts_verify.py', ['prepare', '--root', str(root), '--group', 'facts'])
        prepared = io.read(root/'facts/VERIFY/cpu_01/completion.json')
        if prepared['entries']:
            current = 'VERIFY'; gate = admit(root, state, 'VERIFY', reg); gpu(root, state, 'VERIFY', gate)
            current = 'VERIFY_FIRST_INDEPENDENT_REPLAY'
            child(root, state, 'facts_verify.py', ['replay', '--root', str(root), '--group', 'facts'])
        else:
            current = 'LEGAL_ZERO_VERIFY_CANDIDATES_AFTER_COMPLETE_B0_QA'
            child(root, state, 'facts_verify.py', ['zero_export', '--root', str(root), '--group', 'facts'])
        current = 'EXECUTION_FIRST_QA_MANIFEST_EXPORT'
        child(root, state, 'facts_chain.py', ['export', '--root', str(root), '--group', 'facts'])
        io.save(state/'completion.json', dict(status='PASS_FIXED40_EXECUTION_AND_FIRST_QA_PENDING_FACT_VETO', group='facts', utc=io.utc(),
            execution_receipt_ref=ref(root/'execution_export_01/execution_receipt.json'),
            first_independent_qa_ref=ref(root/'execution_export_01/first_independent_qa.json'),
            verification_export_ref=ref(root/'facts/VERIFY/verification_export.json'),
            model_parameters=io.MODEL_PARAMETERS, new_optimizer_updates=0, production_admitted=False,
            no_human_summary_metric_or_fact_quality_gate_was_run=True))
    except BaseException as error:
        io.save(state/'failure.json', dict(stage=current, error=repr(error), traceback=traceback.format_exc(), utc=io.utc(),
            preserve_all_success=True, do_not_repeat_successful_calls_or_first_QA=True, production_admitted=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('run', 'export'))
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--group', choices=('facts',), default='facts')
    args = parser.parse_args()
    if args.stage == 'export':
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        export_execution(io.root_path(args.root))
    else:
        main(args.root)
