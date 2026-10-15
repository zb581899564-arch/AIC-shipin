"""New registration/lock namespace; legacy helpers only for frozen runtime/cache IO.

No old admission function is used. Prior successful raw and first QA are adopted
by exact path/hash, not recomputed. This module never downloads or decodes media.
"""
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import sys

import positive_contract as c

HOME = Path('/home/inspur/aic_video_work')
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
REG_STATUS = 'REGISTERED_POSITIVE_ADMISSION_V1'
CPU_STATUS = 'PASS_POSITIVE_PROMPT_TOKENS_PREPARED_NOT_GPU_ADMISSION'
QA_STATUS = 'PASS_FIRST_INDEPENDENT_POSITIVE_TOKEN_INPUT_QA_PRE_GPU'
ADMISSION_STATUS = 'PASS_INDEPENDENT_POSITIVE_GPU_ADMISSION_V1'
GPU_STATUS = 'PASS_ALL_POSITIVE_CALLS_NOT_QUALITY'
REPLAY_STATUS = 'PASS_ALL_POSITIVE_OUTPUT_QA_NOT_QUALITY'
EXPORT_STATUS = 'PASS_POSITIVE_EXECUTION_AND_OUTPUT_QA_NOT_QUALITY'
CONDITIONS = ('full_group', 'macro_F1_not_lower', 'macro_recall_gain',
    'every_source_loss_within_gate', 'macro_precision_not_lower',
    'all_rater_recall_retained', 'all_baseline_native_frames_retained', 'real_changed_sources')
require = c.require


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def append(path, value):
    with Path(path).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False)+'\n')
        stream.flush(); os.fsync(stream.fileno())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def host(cpu=False):
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux',
            'Real stages require the existing Linux host')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == ('' if cpu else '0'),
            'CPU children alone hide CUDA; GPU parent retains explicit CUDA0')


def root_path(path):
    path = Path(path).resolve()
    require(path.is_relative_to(HOME) and path != HOME, 'Independent Linux output root required')
    return path


def checked(path, digest=None):
    path = Path(path).resolve()
    require(path.is_relative_to(HOME) and path.is_file(), 'Missing/escaped frozen evidence: '+str(path))
    if digest is not None:
        require(re.fullmatch('[0-9a-f]{64}', digest) is not None and sha(path) == digest,
                'Frozen evidence changed: '+str(path))
    return path


def ref(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def checked_ref(value):
    require(isinstance(value, dict) and {'path', 'sha256'} <= set(value), 'Explicit frozen ref required')
    return checked(value['path'], value['sha256'])


def load_module(name, value):
    path = checked_ref(value)
    require(path.suffix == '.py', 'Explicit frozen Python implementation required')
    old = sys.modules.get(name)
    if old is not None:
        require(Path(old.__file__).resolve() == path, 'Runtime dependency namespace shadowed: '+name)
        return old
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def code_files():
    return {str(path.resolve()): sha(path) for path in Path(__file__).parent.glob('*.py')}


def registration(root, group):
    require(group in ('dev', 'confirm'), 'Explicit dev/confirm group required')
    path = root/('registration.json' if group == 'dev' else 'registration_confirm.json')
    reg = read(path)
    require(reg['status'] == REG_STATUS and reg['stage_group'] == group and
            reg['baseline_sha256'] == c.BASELINE_SHA256 and reg['model_parameters'] == c.MODEL_PARAMETERS,
            'Independent new recipe, protected 40.46 baseline and same model required')
    require(reg['source_scope'] == 'EXTERNAL_NONTEST_ONLY' and reg['reference_available_to_inference'] is False and
            reg['optimizer_updates'] == 0 and reg['production_admitted'] is False,
            'Non-test/no-reference/no-training/small-pilot scope required')
    for key in ('protocol_ref', 'authorization_ref', 'legacy_model_common_ref', 'legacy_token_module_ref', 'proxy_metrics_ref'):
        checked_ref(reg[key])
    require(Path(reg['protocol_ref']['path']).resolve().parent == root, 'Frozen independent protocol must be in new project root')
    protocol = read(reg['protocol_ref']['path'])
    require(protocol['candidate'] == 'OLD_EXPLICIT_KEEP_PLUS_POSITIVE_EVIDENCE_NEW_ADMISSION' and
            protocol['baseline_zip_sha256'] == c.BASELINE_SHA256, 'No consensus or old recipe substitution')
    gates = protocol['quality_gates']
    require(set(('macro_paired_all_rater_duration_F1_delta_min', 'macro_all_rater_recall_delta_min', 'per_source_F1_delta_min',
                'macro_all_rater_precision_delta_min', 'minimum_sources_with_real_new_native_frames')) <= set(gates) and
            c.exact(gates['macro_paired_all_rater_duration_F1_delta_min']) >= 0 and c.exact(gates['macro_all_rater_recall_delta_min']) >= c.exact('0.01') and
            c.exact(gates['per_source_F1_delta_min']) >= c.exact('-0.01') and
            c.exact(gates['macro_all_rater_precision_delta_min']) >= 0 and gates['minimum_sources_with_real_new_native_frames'] >= 2,
            'All eight fixed quality gates must remain at least as strict as registered')
    required = reg['required_files']
    require(isinstance(required, dict) and set(code_files()) <= set(required), 'Complete new code closure required')
    for filename, digest in required.items():
        checked(filename, digest)
    require(all(required.get(filename) == digest for filename, digest in code_files().items()), 'New code changed after registration')
    for key in ('legacy_model_common_ref', 'legacy_token_module_ref', 'proxy_metrics_ref'):
        require(required.get(str(Path(reg[key]['path']).resolve())) == reg[key]['sha256'], 'Frozen implementation missing from registered closure')
    runtime_io = legacy(reg)
    require(runtime_io.runtime_dependencies() | runtime_io.processor_assets() | {str(runtime_io.CONFIG)} <= set(required),
            'Actual runtime/processor/config dependency closure must be registered before any new CPU work')
    budget = reg['gpu_budget'][group]
    require(type(budget['max_actual_calls']) is int and 0 < budget['max_actual_calls'] <= 80 and
            type(budget['max_seconds']) is int and 0 < budget['max_seconds'] <= 2400 and
            re.fullmatch('[A-Za-z0-9_.-]{1,100}', budget['gpu_job_name']),
            'Bounded <=80 unique new calls/2400 seconds required')
    deadline = dt.datetime.fromisoformat(budget['deadline'].replace('Z', '+00:00'))
    require(deadline.tzinfo is not None, 'Explicit timezone-aware new deadline required')
    if group == 'dev':
        require(budget['max_actual_calls'] == protocol['development']['new_admission_call_count_from_output_only_inventory'] and
                budget['max_seconds'] <= protocol['development']['maximum_new_GPU_seconds'],
                'Exact dev call denominator and time budget must match active protocol')
    if group == 'confirm':
        # No automatic fresh acquisition exists. A separately registered first
        # confirmation may only adopt already independently admitted new input.
        selection = read(checked_ref(reg['dev_selection_ref']))
        require(selection['status'] == 'PASS_DEV_FROZEN_FOR_FIRST_CONFIRMATION' and
                selection['confirm_metrics_examined'] is False and
                selection['protocol_sha256'] == reg['protocol_ref']['sha256'],
                'First independent confirmation requires immutable passing dev selection')
    return reg, protocol, path


def legacy(reg):
    module = load_module('_positive_frozen_legacy_io', reg['legacy_model_common_ref'])
    require(module.MODEL_PARAMETERS == c.MODEL_PARAMETERS and module.PROMPT_SHA ==
            'dc0aa31d4a4df1894457a636ace17c55159122d62d7200fd2490ede06e19bce0',
            'Frozen original-B runtime identity differs')
    return module


def tokens_module(reg):
    # cv_tokens imports MAX_INPUT_TOKENS from cv_contract. Bind its exact sibling
    # as an isolated legacy namespace, never replacing positive_contract.
    path = checked_ref(reg['legacy_token_module_ref'])
    sibling = path.parent/'cv_contract.py'
    require(reg['required_files'].get(str(sibling)) == sha(sibling), 'Legacy token helper contract must be frozen')
    existing = sys.modules.get('cv_contract')
    require(existing is None or Path(existing.__file__).resolve() == sibling, 'Legacy token contract shadowed')
    if existing is None:
        load_module('cv_contract', ref(sibling))
    return load_module('_positive_frozen_legacy_tokens', reg['legacy_token_module_ref'])


def adopted(root, group, reg):
    """Bind complete old calls/QA, then mathematically select candidate denominator.

    Only completed files are read. No old processor, model, parser or output QA
    is re-run. Source references/labels are not read here.
    """
    oldio = legacy(reg)
    from positive_metrics import baseline_prediction, frames
    cohorts = reg['adopted_source_groups'][group]
    if isinstance(cohorts, dict):
        cohorts = [cohorts]
    inputs, events, candidates, audit, files, names = {}, [], [], [], {}, []

    def take(value, prior=None):
        path = checked_ref(value)
        require(prior is None or path.is_relative_to(prior), 'Adopted evidence escaped its declared prior root')
        files[str(path)] = value['sha256']
        return path

    for cohort in cohorts:
        prior = root_path(cohort['prior_root'])
        require(prior != root, 'Adoption must name distinct prior evidence root')
        old_group = cohort['prior_group']
        cohort_names = cohort['source_names']; names.extend(cohort_names)
        cpu_path = take(cohort['old_cpu_admission'], prior); cpu = read(cpu_path)
        require(cpu['group'] == old_group and cpu['status'] == 'PASS_ALL_RECALL_REAL_CPU_INPUTS_NOT_GPU_ADMISSION' and
                cpu['CPU_only'] is True and cpu['CUDA_initialized'] is False and cpu['new_model_calls'] == 0,
                'Complete original real CPU input acceptance required')
        stages = {}
        for stage, key in (('B0', 'old_b0'), ('VERIFY', 'old_verify')):
            adopted_stage = cohort[key]
            gate_path = take(adopted_stage['admission'], prior); gate = read(gate_path)
            complete_path = take(adopted_stage['gpu_completion'], prior)
            qa_path = take(adopted_stage['replay_completion'], prior)
            require(gate['group'] == old_group and gate['stage'] == stage and
                    gate['model_parameters'] == c.MODEL_PARAMETERS and gate['optimizer_updates'] == 0 and
                    gate['reference_available_to_inference'] is False, 'Adopted same-model group/stage differs')
            if stage == 'B0':
                require(gate['cpu_acceptance_path'] == str(cpu_path) and gate['cpu_acceptance_sha256'] == sha(cpu_path),
                        'Old B0 CPU acceptance binding differs')
            # Existing helper checks unique actual journal, model identity and
            # shared natural terminal. It never recomputes any successful QA.
            complete, by_id = oldio.completed_job(complete_path.parent, gate, gate_path,
                                                 gate['expected_input_count'], stage)
            resource, resource_sha = oldio.terminal(gate)
            qa = read(qa_path)
            require(qa['status'] == 'PASS_ALL_RECALL_'+stage+'_INDEPENDENT_REPLAYS_NOT_QUALITY' and
                    qa['group'] == old_group and qa['calls'] == complete['calls'] == len(qa['proofs']) and
                    qa['gpu_completion_sha256'] == sha(complete_path) and qa['resource_terminal_sha256'] == resource_sha and
                    qa['CPU_only'] is True and qa['CUDA_initialized'] is False and qa['new_model_calls'] == 0,
                    'Adopt complete successful first old QA without repetition')
            proof_by_id = {p['case_id']: p for p in qa['proofs']}
            require(len(proof_by_id) == len(qa['proofs']) and list(proof_by_id) == list(by_id),
                    'Complete unique old QA denominator differs')
            files[str(RUN/'controller'/(gate['gpu_job_name']+'.resource.json'))] = resource_sha
            for extra in ('attempts.jsonl', 'model_identity.json'):
                extra_path = complete_path.parent/extra; files[str(extra_path)] = sha(extra_path)
            stages[stage] = (by_id, proof_by_id)
        by_b0, qa_b0 = stages['B0']; by_verify, qa_verify = stages['VERIFY']
        require(list(by_b0) == [e['case_id'] for e in cpu['entries']], 'Entire old CPU/B0 denominator differs')
        local_inputs = {}
        for entry in cpu['entries']:
            meta_path = take(dict(path=entry['input_path'], sha256=entry['input_sha256']), prior)
            proof_path = take(dict(path=entry['proof_path'], sha256=entry['proof_sha256']), prior)
            meta, proof = read(meta_path), read(proof_path)
            case = entry['case_id']; require(case not in inputs and case == meta['case_id'] == proof['case_id'], 'Duplicate/crossed original input')
            require(meta['source_name'] in cohort_names and proof['CPU_only'] is True and
                    meta['reference_available_to_inference'] is False and meta['audio_observed'] is False,
                    'Original input is outside registered source/no-reference scope')
            oldio.validate_native(meta)
            done_ref, qa_ref = by_b0[case], qa_b0[case]
            done_path = take(dict(path=done_ref['done_path'], sha256=done_ref['done_sha256']), prior)
            qa_file = take(dict(path=qa_ref['proof_path'], sha256=qa_ref['proof_sha256']), prior)
            done, oldqa = read(done_path), read(qa_file)
            require(done['case_id'] == case and done['source_sha256'] == meta['source_sha256'] and
                    oldqa['done_sha256'] == done_ref['done_sha256'] and oldqa['segments'] == done['segments'] and
                    oldqa['native_ranges'] == done['native_ranges'], 'Immutable original B0/native first QA differs')
            # Old first QA may adopt a pre-GPU exceptional input proof. Its
            # completion proves that observation; do not call the processor.
            require(proof['input_evidence'] == done['input_evidence'], 'Old accepted input evidence differs from real B0')
            cache_ref = dict(path=proof['encoded_tensor_path'], sha256=proof['encoded_tensor_sha256'])
            take(cache_ref, prior)
            local_inputs[case] = dict(meta=meta, proof=proof, input_ref=ref(meta_path), proof_ref=ref(proof_path),
                                     done=done, done_ref=ref(done_path), old_input_QA_ref=ref(qa_file), cache_ref=cache_ref)
            inputs[case] = local_inputs[case]
        export_path = take(cohort['old_verify']['export'], prior); export = read(export_path)
        require(export['status'] == 'PASS_RECALL_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY' and
                export['group'] == old_group and len(export['events']) == len(by_verify) and
                export['independent_replay_completion_sha256'] == cohort['old_verify']['replay_completion']['sha256'] and
                export['reference_labels_read'] is False and export['model_parameters'] == c.MODEL_PARAMETERS,
                'Complete immutable old VERIFY export required')
        expected_segments = {(case, index) for case, value in local_inputs.items()
                             for index in range(len(value['done']['segments']))}
        actual_segments = set(); local_events = []
        for event in export['events']:
            pair = (event['original_case_id'], event['original_segment_index'])
            require(pair not in actual_segments and pair in expected_segments, 'Duplicate/foreign old candidate')
            actual_segments.add(pair)
            original = local_inputs[pair[0]]; meta = original['meta']; done = original['done']
            exact_interval = [str(c.exact(meta['window_start'])+c.exact(v)) for v in done['segments'][pair[1]]]
            decision = event['decision_result']; request_id = decision['request_id']
            require(event['original_interval_exact'] == decision['original_interval_exact'] == exact_interval and
                    event['source_name'] == meta['source_name'] and event['source_sha256'] == meta['source_sha256'] and
                    decision['successful_model_call_required'] is True and decision['decision'] in c.DECISIONS and
                    decision['boundaries_changed'] is False and request_id in by_verify and request_id in qa_verify,
                    'Old explicit decision/exact original candidate binding differs')
            old_done_ref, old_qa_ref = by_verify[request_id], qa_verify[request_id]
            old_done_path = take(dict(path=old_done_ref['done_path'], sha256=old_done_ref['done_sha256']), prior)
            old_qa_path = take(dict(path=old_qa_ref['proof_path'], sha256=old_qa_ref['proof_sha256']), prior)
            vd, vq = read(old_done_path), read(old_qa_path)
            require(vd['decision_result'] == vq['decision_result'] == decision and
                    vq['done_sha256'] == old_done_ref['done_sha256'], 'Old VERIFY raw/first QA decision differs')
            take(dict(path=vd['raw_path'], sha256=vd['raw_sha256']), prior)
            events.append(event); local_events.append(event)
            event['_adopted_verify_done_ref'] = ref(old_done_path)
            event['_adopted_verify_QA_ref'] = ref(old_qa_path)
        require(actual_segments == expected_segments, 'Old complete candidate denominator cannot be filtered by reference')
        # Freeze reference pointers only. Do not open the actual reference file
        # or labels in any inference preparation/admission process.
        take(cohort['reference_completion'], prior)
        meta_map = {case: item['meta'] for case, item in local_inputs.items()}
        for source in cohort_names:
            source_events = [e for e in local_events if e['source_name'] == source]
            baseline = baseline_prediction(source_events, meta_map)
            source_metas = [m for m in meta_map.values() if m['source_name'] == source]
            require(source_metas and len({m['source_sha256'] for m in source_metas}) == 1, 'Full unique source identity required')
            pts = list(map(c.exact, source_metas[0]['all_source_exact_pts'])); protected = frames(baseline, pts)
            for event in source_events:
                meta = meta_map[event['original_case_id']]; roles = meta.get('view_roles', [meta['window_role']])
                eligible = 'overlap' in roles and event['decision_result']['decision'] == 'KEEP'
                native = frames([event['original_interval_exact']], pts)
                effect = len(native-protected)
                reason = 'NEW_STRICT_POSITIVE_VERIFY_REQUIRED' if eligible and effect else (
                    'PURE_NATIVE_BASELINE_SUBSET_NO_EFFECT' if eligible else 'NOT_OLD_SHORT_EXPLICIT_KEEP')
                audit.append(dict(old_event_id=event['event_id'], original_case_id=event['original_case_id'],
                    original_interval_exact=event['original_interval_exact'], old_decision=event['decision_result']['decision'],
                    source_name=source, native_frames_outside_baseline=effect, disposition=reason))
                if eligible and effect:
                    req = c.request(event, meta, sorted(native-protected))
                    req.update(group=group, prompt=c.prompt(req), view_roles=roles,
                        original_vision_cache_path=original_cache(meta, local_inputs)['path'],
                        original_vision_cache_sha256=original_cache(meta, local_inputs)['sha256'],
                        original_input_evidence=local_inputs[meta['case_id']]['proof']['input_evidence'],
                        original_evidence=dict(input=local_inputs[meta['case_id']]['input_ref'],
                            proof=local_inputs[meta['case_id']]['proof_ref'], done=local_inputs[meta['case_id']]['done_ref'],
                            old_input_QA=local_inputs[meta['case_id']]['old_input_QA_ref'],
                            old_VERIFY_done=event['_adopted_verify_done_ref'], old_VERIFY_QA=event['_adopted_verify_QA_ref']),
                        new_native_frames_before_admission=effect)
                    candidates.append(req)
    require(len(names) == len(set(names)) == 4 and len({r['request_id'] for r in candidates}) == len(candidates),
            'Exactly four distinct complete sources and unique new request namespace required')
    require(len(candidates) <= reg['gpu_budget'][group]['max_actual_calls'], 'Complete actual candidate denominator exceeds budget')
    if group == 'dev':
        protocol = read(reg['protocol_ref']['path'])
        require(len(candidates) == protocol['development']['new_admission_call_count_from_output_only_inventory'],
                'Full actual development denominator differs from pre-execution output-only registration')
    # Internal adoption refs do not modify any original JSON or export.
    events = [{k: v for k, v in e.items() if not k.startswith('_adopted_')} for e in events]
    return dict(inputs=inputs, events=events, requests=candidates, denominator_audit=audit,
                adopted_files=files, source_names=names)


def original_cache(meta, inputs):
    return inputs[meta['case_id']]['cache_ref']


def validate_lock(path, required=()):
    files = read(path)['files']
    require(isinstance(files, dict) and set(map(str, required)) <= set(files), 'Complete explicit source/input/code lock required')
    for filename, digest in files.items():
        checked(filename, digest)
    return files


def terminal(gate):
    path = RUN/'controller'/(gate['gpu_job_name']+'.resource.json')
    resource = read(path)
    matches = [r for r in rows(HOME/'improvement_round1/gpu_ledger.jsonl') if r['name'] == gate['gpu_job_name']]
    require(matches == [resource] and resource['status'] == 'completed' and resource['exit_code'] == 0,
            'Unique natural completed/exit0 shared GPU terminal required')
    return resource, sha(path)
