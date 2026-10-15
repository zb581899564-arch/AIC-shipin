"""Independent CPU-only read of completed fixed40 execution and first QA.

This stage never decodes media, imports a processor/model, or repeats a replay.
It adopts byte-bound, completed first token/parser/native QA and independently
rebuilds every B0 candidate, every canonical VERIFY decision and native range.
Only explicit KEEP is K. Missing work is an exception, never an empty K.

K disjoint from all 222 original ORDINARY observations suffices for the
unchanged zero-addition gate for any unknown real baseline B. If K touches an
observation this implementation returns INCONCLUSIVE, without substituting D8
or inventing a real VERIFY baseline. The frozen merge is B union K; production
426 byte/frame/box preservation is a separate later mandatory actual QA.
"""
import argparse
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

import facts_common as io
import source_audit as sources_api


MERGE_SHA = '4b3e5b4ba95d9dff278e7dde6b9d4389a09ea538c10fbee05b427dd1f872d277'
PASS = 'PASS_KNOWN_ORDINARY_SUFFICIENT_CONDITION_NOT_QUALITY'
INCONCLUSIVE = 'INCONCLUSIVE_NEEDS_REAL_VERIFY_BASELINE'


def ref(path):
    return dict(path=str(path), sha256=io.sha(path))


def bound(value, expected=None):
    io.require(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'Explicit untouched JSON path/SHA reference required')
    path = io.checked(value['path'], value['sha256'])
    io.require(path.suffix == '.json' and (expected is None or path == Path(expected).resolve()), 'Wrong original JSON evidence path')
    return io.read(path)


def event_identity(case, index):
    return 'facts.B0.'+hashlib.sha256(case.encode()).hexdigest()[:24]+'.seg'+str(index)


def native_interval(points, interval):
    first, last = map(F, interval)
    io.require(0 <= first < last, 'Exact positive original candidate interval required')
    a, b = bisect_left(points, first), bisect_left(points, last)
    io.require(a < b and list(range(a, b)) == [i for i, point in enumerate(points) if first <= point < last],
               'Original candidate contains no real frame or native membership differs')
    return [a, b]


def native_segments(segments, meta, points):
    io.require(isinstance(segments, list), 'Complete actual B0 segment list required, including legal empty')
    start, end = F(meta['window_start']), F(meta['window_end'])
    intervals, ranges = [], []
    for segment in segments:
        io.require(isinstance(segment, (list, tuple)) and len(segment) == 2 and
                   all(type(value) in (int, float, str) for value in segment), 'Original accepted segment pair required')
        first, last = [F(str(value)) for value in segment]
        io.require(0 <= first < last <= end-start, 'B0 segment escaped its original full-source window')
        interval = [str(start+first), str(start+last)]
        intervals.append(interval)
        ranges.append(native_interval(points, interval))
    return intervals, ranges


def completed_stage(root, stage, count, registration_sha):
    gate_path = root/('gpu_admission_facts_'+stage+'.json')
    gate = io.read(gate_path)
    io.require(gate['status'] == io.ADMISSION_STATUS and gate['group'] == 'facts' and gate['stage'] == stage and
               gate['gpu_job_name'] == io.JOB_NAMES[stage] and gate['expected_input_count'] == count and
               gate['registration_sha256'] == registration_sha,
               'Wrong independent admitted actual '+stage+' execution')
    cpu_path = root/'cpu_acceptance_facts.json' if stage == 'B0' else root/'facts/VERIFY/cpu_01/completion.json'
    lock_path = root/('source_lock_facts_'+stage+'.json')
    io.require(gate['registration_path'] == str(root/'registration.json') and
               gate['cpu_acceptance_path'] == str(cpu_path) and gate['source_lock_path'] == str(lock_path) and
               gate['model_parameters'] == io.MODEL_PARAMETERS and gate['optimizer_updates'] == 0 and
               gate['source_scope'] == 'EXTERNAL_NONTEST_ONLY' and gate['reference_available_to_inference'] is False,
               'Actual admitted stage CPU/source/model/reference scope differs')
    io.checked(cpu_path, gate['cpu_acceptance_sha256'])
    lock = bound(dict(path=str(lock_path), sha256=gate['source_lock_sha256']))
    io.require(lock['files'].get(str(cpu_path)) == gate['cpu_acceptance_sha256'] and
               lock['files'].get(str(root/'registration.json')) == registration_sha,
               'Actual admitted stage is not byte-bound to its registered CPU inputs')
    _, terminal_sha = io.terminal(gate)
    gpu, qa_root = root/'facts'/stage/'gpu_01', root/'facts'/stage/'replay_01'
    _, accepted = io.completed_job(gpu, gate, gate_path, count, stage)
    qa_path = qa_root/'completion.json'
    qa = io.read(qa_path)
    io.require(qa['status'] == 'PASS_ALL_FIXED40_'+stage+'_INDEPENDENT_REPLAYS_NOT_QUALITY' and
               qa['group'] == 'facts' and qa['calls'] == len(qa['proofs']) == count and
               qa['CPU_only'] is True and qa['CUDA_initialized'] is False and qa['new_model_calls'] == 0 and
               qa['gpu_completion_sha256'] == io.sha(gpu/'completion.json') and qa['resource_terminal_sha256'] == terminal_sha,
               'Complete natural actual '+stage+' execution and first independent QA required')
    by_id = {entry['case_id']: entry for entry in qa['proofs']}
    io.require(len(by_id) == count and set(by_id) == set(accepted), 'Missing/duplicate first QA identity')
    for case, entry in by_id.items():
        proof = bound(dict(path=entry['proof_path'], sha256=entry['proof_sha256']), qa_root/(case+'.json'))
        io.require(proof['case_id'] == case and proof['CPU_only'] is True and proof['new_model_calls'] == 0 and
                   proof['done_sha256'] == accepted[case]['done_sha256'], 'First QA is not bound to the actual accepted answer')
    return accepted, by_id, ref(qa_path), ref(io.RUN/'controller'/(gate['gpu_job_name']+'.resource.json'))


def check_b0(root, registration, execution, sources, views, clocks):
    cpu_path = root/'cpu_acceptance_facts.json'
    cpu = io.read(cpu_path)
    io.require(cpu['status'] == io.CPU_STATUS and cpu['group'] == 'facts' and cpu['source_count'] == 9 and
               cpu['expected_input_count'] == len(cpu['entries']) == 17, 'All17 independently accepted actual B0 inputs required')
    entries = {entry['case_id']: entry for entry in cpu['entries']}
    io.require(len(entries) == 17 and list(entries) == [view['case_id'] for view in views], 'Registered actual CPU view order/denominator differs')
    accepted, qa_entries, qa_ref, terminal_ref = completed_stage(root, 'B0', 17, io.sha(root/'registration.json'))
    io.require(list(accepted) == list(entries), 'All17 ordered actual B0 calls are required')
    actual = execution['actual_inputs']
    io.require(isinstance(actual, list) and len(actual) == 17 and [row['case_id'] for row in actual] == list(entries),
               'Execution export omitted/duplicated a registered B0 view')
    by_case, candidates = {}, []
    by_source = {source['video_id']: source for source in sources}
    for row, view in zip(actual, views):
        case, entry = view['case_id'], entries[view['case_id']]
        io.require(row['input_ref'] == dict(path=entry['input_path'], sha256=entry['input_sha256']) and
                   row['CPU_proof_ref'] == dict(path=entry['proof_path'], sha256=entry['proof_sha256']), 'Actual input/primary CPU proof differs')
        meta, proof = bound(row['input_ref']), bound(row['CPU_proof_ref'])
        source, clock = by_source[view['source_name']], clocks[view['source_name']]
        io.validate_native(meta)
        io.require(meta['case_id'] == case and meta['fixed_case_id'] == source['case_id'] and
                   meta['source_name'] == source['video_id'] and meta['source_sha256'] == source['source_sha256'] and
                   meta['original_clock_sha256'] == source['clock_sha256'] and
                   meta['all_source_exact_pts'] == clock['original_exact_pts'] and
                   F(meta['physical_end_exact']) == F(clock['physical_end_exact']) and
                   all(meta[key] == view[key] for key in ('window_start', 'window_end', 'source_frame_ordinals', 'sample_exact_pts')) and
                   meta['reference_available_to_inference'] is False and meta['audio_observed'] is False and
                   meta['window_role'] == 'overlap' and meta['view_roles'] == ['overlap'], 'Actual B0 source/native64/reference isolation differs')
        io.require(proof['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' and proof['CPU_only'] is True and
                   proof['CUDA_initialized'] is False and proof['case_id'] == case and
                   proof['input_path'] == row['input_ref']['path'] and proof['input_sha256'] == row['input_ref']['sha256'],
                   'Actual primary CPU processor proof/input is missing')
        folder = root/'facts/B0/gpu_01'/case
        request, raw, done, qa = [bound(row[key], path) for key, path in (
            ('request_ref', folder/'request.json'), ('raw_ref', folder/'raw.json'), ('done_ref', folder/'done.json'),
            ('first_qa_ref', root/'facts/B0/replay_01'/(case+'.json')))]
        io.require(row['done_ref'] == dict(path=accepted[case]['done_path'], sha256=accepted[case]['done_sha256']) and
                   row['first_qa_ref'] == dict(path=qa_entries[case]['proof_path'], sha256=qa_entries[case]['proof_sha256']),
                   'Export must bind exactly the naturally accepted B0 answer and first QA')
        io.output_tokens(raw, done)
        io.require(request['case_id'] == done['case_id'] == qa['case_id'] == case and
                   request['input_path'] == row['input_ref']['path'] and request['input_sha256'] == row['input_ref']['sha256'] and
                   request['CPU_proof_sha256'] == row['CPU_proof_ref']['sha256'] and
                   request['encoded_tensor_sha256'] == proof['encoded_tensor_sha256'] and
                   hashlib.sha256(request['prompt'].encode()).hexdigest() == io.PROMPT_SHA and
                   request['reference_labels_read'] is False and request['audio_observed'] is False and
                   done['source_sha256'] == source['source_sha256'] and done['source_name'] == source['video_id'] and
                   done['raw_sha256'] == row['raw_ref']['sha256'] and done['request_sha256'] == row['request_ref']['sha256'] and
                   qa['raw_sha256'] == row['raw_ref']['sha256'] and qa['done_sha256'] == row['done_ref']['sha256'] and
                   raw['input_tokens'] == done['input_tokens'] == proof['input_tokens'] and
                   proof['input_evidence'] == request['input_evidence'] == raw['input_evidence'] == done['input_evidence'] == qa['input_evidence'] and
                   qa['status'] == 'PASS_INDEPENDENT_FIXED40_B0_TENSOR_TOKEN_GRAMMAR_PARSER_NATIVE_REPLAY',
                   'Actual untouched B0 raw/request/parser first-QA hash chain differs')
        segments = done['segments']
        points = list(map(F, clock['original_exact_pts']))
        intervals, native = native_segments(segments, meta, points)
        io.require(done['status'] == ('MODEL_OK' if segments else 'LEGAL_EMPTY') and not done['parse_errors'] and
                   done['source_start_exact'] == view['window_start'] and done['source_end_exact'] == view['window_end'] and
                   qa['segments'] == row['segments'] == segments and qa['native_ranges'] == row['native_ranges'] == done['native_ranges'] == native,
                   'Actual B0 segments/native membership differ from completed first parser QA')
        by_case[case] = dict(row=row, meta=meta, proof=proof, points=points, source=source)
        for index, (interval, membership) in enumerate(zip(intervals, native)):
            candidates.append(dict(event_id=event_identity(case, index), original_case_id=case,
                                   original_segment_index=index, original_interval_exact=interval,
                                   original_native_range=membership, source_name=source['video_id'], source_sha256=source['source_sha256']))
    return by_case, candidates, qa_ref, terminal_ref


def check_verify(root, execution, by_case, candidates, registration_sha):
    cpu_path = root/'facts/VERIFY/cpu_01/completion.json'
    cpu = io.read(cpu_path)
    io.require(cpu['status'] == 'PASS_ALL_FIXED40_VERIFY_TOKEN_INPUTS_NOT_GPU_ADMISSION' and cpu['group'] == 'facts' and
               cpu['expected_input_count'] == len(cpu['entries']) == len(candidates) and cpu['CPU_only'] is True and
               cpu['CUDA_initialized'] is False and cpu['new_model_calls'] == 0, 'All actual B0 segments need complete VERIFY token preparation')
    for prefix, path in (
        ('b0_cpu_acceptance', root/'cpu_acceptance_facts.json'),
        ('b0_source_lock', root/'source_lock_facts_B0.json'),
        ('b0_admission', root/'gpu_admission_facts_B0.json'),
        ('b0_gpu_completion', root/'facts/B0/gpu_01/completion.json'),
        ('b0_replay_completion', root/'facts/B0/replay_01/completion.json')):
        bound(dict(path=cpu['bindings'][prefix+'_path'], sha256=cpu['bindings'][prefix+'_sha256']), path)
    planned = bound(dict(path=cpu['requests_path'], sha256=cpu['requests_sha256']), root/'facts/VERIFY/cpu_01/requests.json')
    io.require(len(planned) == len(candidates) and [row['event_id'] for row in planned] == [row['event_id'] for row in candidates],
               'VERIFY requests omit/reorder/fabricate an actual B0 segment')
    exported = bound(execution['verification_export_ref'], root/'facts/VERIFY/verification_export.json')
    decisions = execution['verification_decisions']
    io.require(len(decisions) == len(exported['events']) == len(candidates), 'Complete KEEP/UNKNOWN/DROP denominator required')
    if not candidates:
        io.require(exported['status'] == 'PASS_FIXED40_VERIFY_ZERO_CANDIDATES_AFTER_COMPLETE_B0_QA' and
                   exported['events'] == [] and decisions == [] and cpu['entries'] == [] and
                   exported['actual_VERIFY_model_calls'] == exported['actual_VERIFY_GPU_jobs'] == 0 and
                   exported['actual_B0_model_calls'] == 17 and
                   exported['B0_gpu_completion_sha256'] == io.sha(root/'facts/B0/gpu_01/completion.json') and
                   exported['B0_independent_replay_completion_sha256'] == io.sha(root/'facts/B0/replay_01/completion.json') and
                   exported['zero_candidate_CPU_completion_sha256'] == io.sha(cpu_path),
                   'Missing/failed/unassessed work cannot be treated as legal zero candidates')
        return [], None, None
    io.require(len(candidates) <= io.VERIFY_MAX_CALLS and exported['status'] == 'PASS_FIXED40_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY' and
               exported['reference_labels_read'] is False and exported['new_additions_require_explicit_KEEP'] is True,
               'Actual complete explicit semantic decision export required')
    accepted, qa_entries, qa_ref, terminal_ref = completed_stage(root, 'VERIFY', len(candidates), registration_sha)
    io.require(exported['independent_replay_completion_sha256'] == qa_ref['sha256'] and
               list(accepted) == [row['request_id'] for row in planned] == [row['request_id'] for row in decisions] and
               [entry['case_id'] for entry in cpu['entries']] == list(accepted), 'All actual first VERIFY decision calls/QA must match the raw candidate order')
    kept = []
    for candidate, planned_req, entry, row, event in zip(candidates, planned, cpu['entries'], decisions, exported['events']):
        case = row['request_id']
        original = by_case[candidate['original_case_id']]
        io.require(all(row[key] == candidate[key] == planned_req[key] for key in
                       ('event_id', 'original_case_id', 'original_segment_index', 'original_interval_exact')) and
                   planned_req['source_name'] == candidate['source_name'] and planned_req['source_sha256'] == candidate['source_sha256'],
                   'Actual semantic decision changed its original B0 source/segment/endpoints')
        expected_evidence = dict(input=original['row']['input_ref'], proof=original['row']['CPU_proof_ref'],
                                 done=original['row']['done_ref'], replay=original['row']['first_qa_ref'])
        io.require(planned_req['original_evidence'] == expected_evidence and
                   row['input_ref'] == dict(path=entry['input_path'], sha256=entry['input_sha256']) and
                   row['CPU_proof_ref'] == dict(path=entry['proof_path'], sha256=entry['proof_sha256']),
                   'VERIFY request must bind the original successful B0 input/proof/raw-segment/first-QA chain')
        req, proof = bound(row['input_ref']), bound(row['CPU_proof_ref'])
        io.require(all(req[key] == value for key, value in planned_req.items()) and
                   proof['status'] == 'PASS_CPU_FIXED40_VERIFY_PROMPT_ONLY_UNCHANGED_VISION' and proof['CPU_only'] is True and
                   proof['CUDA_initialized'] is False and proof['input_sha256'] == row['input_ref']['sha256'] and
                   proof['vision_processor_calls'] == proof['media_decodes'] == proof['new_model_calls'] == 0,
                   'Actual VERIFY token input/unchanged original vision proof differs')
        folder = root/'facts/VERIFY/gpu_01'/case
        request, raw, done, qa = [bound(row[key], path) for key, path in (
            ('request_ref', folder/'request.json'), ('raw_ref', folder/'raw.json'), ('done_ref', folder/'done.json'),
            ('first_qa_ref', root/'facts/VERIFY/replay_01'/(case+'.json')))]
        io.require(row['done_ref'] == dict(path=accepted[case]['done_path'], sha256=accepted[case]['done_sha256']) and
                   row['first_qa_ref'] == dict(path=qa_entries[case]['proof_path'], sha256=qa_entries[case]['proof_sha256']),
                   'VERIFY export must adopt the exact naturally accepted answer/first QA')
        io.output_tokens(raw, done)
        io.require(request['input_path'] == row['input_ref']['path'] and request['input_sha256'] == row['input_ref']['sha256'] and
                   request['CPU_proof_sha256'] == row['CPU_proof_ref']['sha256'] and
                   request['reference_labels_read'] is False and request['audio_observed'] is False and
                   request['prompt'] == req['prompt'] == planned_req['prompt'] and
                   request['original_interval_exact'] == candidate['original_interval_exact'] and
                   request['original_case_id'] == candidate['original_case_id'] and request['original_segment_index'] == candidate['original_segment_index'] and
                   request['original_vision_cache_sha256'] == proof['original_vision_cache_sha256'] == original['proof']['encoded_tensor_sha256'] and
                   request['token_cache_sha256'] == proof['token_cache_sha256'] and
                   done['status'] == 'PASS_FIXED40_VERIFY_DECISION_NOT_QUALITY' and
                   done['raw_sha256'] == row['raw_ref']['sha256'] and done['request_sha256'] == row['request_ref']['sha256'] and
                   qa['status'] == 'PASS_INDEPENDENT_FIXED40_VERIFY_TOKEN_RAW_GRAMMAR_NATIVE_REPLAY' and
                   qa['raw_sha256'] == row['raw_ref']['sha256'] and qa['done_sha256'] == row['done_ref']['sha256'] and
                   qa['full_tensor_signature'] == proof['input_evidence']['tensor_signature'] and
                   qa['unchanged_vision_tensor_signature'] == proof['input_evidence']['unchanged_vision_tensor_signature'] and
                   raw['input_tokens'] == done['input_tokens'] == proof['input_tokens'] and
                   proof['input_evidence'] == req['input_evidence'] == request['input_evidence'] == raw['input_evidence'] == done['input_evidence'],
                   'Actual untouched VERIFY raw/request/vision/first-QA identity differs')
        first, last = map(F, candidate['original_interval_exact'])
        observed = sum(first <= F(point) < last for point in original['meta']['sample_exact_pts'])
        io.require(observed == req['candidate_visible_sample_count'], 'Actual candidate shown-sample denominator differs')
        legal = ('KEEP', 'UNKNOWN', 'DROP') if observed else ('UNKNOWN',)
        io.require(raw['raw_output'] in tuple('{"decision":"'+value+'"}' for value in legal), 'Noncanonical raw semantic decision or illegal unobserved KEEP')
        decision = json.loads(raw['raw_output'])['decision']
        result = dict(event_id=candidate['event_id'], request_id=case, original_case_id=candidate['original_case_id'],
            original_segment_index=candidate['original_segment_index'], source_sha256=candidate['source_sha256'],
            original_interval_exact=candidate['original_interval_exact'], decision=decision, candidate_kept=decision != 'DROP',
            retained_interval_exact=candidate['original_interval_exact'] if decision != 'DROP' else None,
            boundaries_changed=False, new_candidate_created=False,
            uncertainty_gate='NONE' if observed else 'NO_SHOWN_SAMPLE_IN_CANDIDATE', successful_model_call_required=True)
        membership = native_interval(original['points'], candidate['original_interval_exact'])
        io.require(done['decision_result'] == qa['decision_result'] == row['decision_result'] == event['decision_result'] == result and
                   qa['original_native_range'] == row['original_native_range'] == event['original_native_range'] == membership and
                   all(event[key] == candidate[key] for key in ('source_name', 'source_sha256', 'event_id', 'original_case_id', 'original_segment_index', 'original_interval_exact')) and
                   event['window_role'] == req['window_role'] == request['window_role'] == done['window_role'] == 'overlap' and
                   event['view_roles'] == req['view_roles'] == request['view_roles'] == done['view_roles'] == ['overlap'] and
                   event['eligible_for_new_addition'] == (decision == 'KEEP'), 'Independent actual KEEP/UNKNOWN/DROP/native result differs')
        if decision == 'KEEP':
            kept.append(dict(candidate, request_id=case))
    return kept, qa_ref, terminal_ref


def evaluate(root):
    io.host(cpu=True)
    root = io.root_path(root)
    registration = io.registration(root)
    sources, views = sources_api.validate_registered_sources(registration)
    reference = sources_api.load_reference(registration['reference_ref']['path'])
    protocol = bound(registration['main_protocol_ref'])
    io.require(protocol['baseline'] == 'TEMPORAL_VERIFY_USER40.46' and
               protocol['quality_gates']['fixed_40_KEEP_deletion'] == 0 and
               protocol['quality_gates']['fixed_40_ORDINARY_addition'] == 0 and
               protocol['quality_gates']['UNKNOWN_old_coverage_failed_unchanged'] is True, 'Original fixed scientific thresholds changed')
    merge_ref = registration['merge_implementation_ref']
    merge_path = io.checked(merge_ref['path'], merge_ref['sha256'])
    io.require(merge_ref['sha256'] == MERGE_SHA and merge_path.name == 'merge_keep.py' and
               registration['required_files'].get(str(merge_path)) == MERGE_SHA,
               'Exactly reviewed KEEP-only B-union-K merge implementation must be frozen before scientific fact admission')
    execution_path, first_qa_path = root/'execution_export_01/execution_receipt.json', root/'execution_export_01/first_independent_qa.json'
    execution, first_qa = io.read(execution_path), io.read(first_qa_path)
    registration_sha = io.sha(root/'registration.json')
    io.require(execution['status'] == 'PASS_FIXED40_ACTUAL_EXECUTION_NOT_FACT_QUALITY' and
               execution['registration_sha256'] == registration_sha and execution['geometry_scope'] == sources_api.SCOPE and
               execution['source_scope'] == 'EXTERNAL_NONTEST_ONLY' and execution['group'] == 'facts' and
               execution['all_registered_views_completed'] is True and execution['failed_views'] == 0 and
               execution['registered_view_count'] == execution['completed_view_count'] == execution['B0_actual_model_calls'] == 17 and
               execution['source_count'] == 9 and execution['registered_view_plan'] == views and
               execution['model_parameters'] == io.MODEL_PARAMETERS and execution['new_optimizer_updates'] == 0 and
               execution['new_baseline_model_calls'] == 0 and execution['production_admitted'] is False,
               'Complete actual all17-source-grid execution is missing; retained baseline alone never passes')
    io.require(first_qa['status'] == 'PASS_FIXED40_FIRST_QA_NOT_FACT_QUALITY' and first_qa['CPU_only'] is True and
               first_qa['CUDA_initialized'] is False and first_qa['actual_execution_receipt_sha256'] == io.sha(execution_path) and
               first_qa['complete_view_and_decision_denominators'] is True and first_qa['new_model_calls'] == 0 and
               first_qa['media_decodes'] == first_qa['vision_processor_calls'] == first_qa['repeated_first_input_or_output_replays'] == 0,
               'Completed actual first independent QA manifest is missing; no new replay is performed here')
    clocks = {source['video_id']: sources_api.load_source_clock(source) for source in sources}
    by_case, candidates, b0_qa_ref, b0_terminal_ref = check_b0(root, registration, execution, sources, views, clocks)
    io.require(execution['VERIFY_actual_model_calls'] == len(candidates), 'Incomplete actual candidate VERIFY denominator')
    kept, verify_qa_ref, verify_terminal_ref = check_verify(root, execution, by_case, candidates, registration_sha)
    qa_refs = [b0_qa_ref]+([verify_qa_ref] if verify_qa_ref is not None else [])
    terminal_refs = [b0_terminal_ref]+([verify_terminal_ref] if verify_terminal_ref is not None else [])
    io.require(execution['first_independent_stage_qa_refs'] == first_qa['adopted_completed_first_stage_qa_refs'] == qa_refs and
               execution['resource_terminal_refs'] == terminal_refs, 'Actual complete stage first-QA/natural-terminal binding changed')
    by_video = {source['video_id']: [] for source in sources}
    by_fixed_case = {source['case_id']: [] for source in sources}
    for candidate in kept:
        by_video[candidate['source_name']].append(candidate['event_id'])
        by_fixed_case[by_case[candidate['original_case_id']]['source']['case_id']].append(candidate['event_id'])
    io.require(execution['keep_event_ids_by_source_name'] == by_video and execution['keep_event_ids_by_case'] == by_fixed_case,
               'Export omitted/invented an explicit actual KEEP event')
    cases, touched_total = [], 0
    for row in sources_api.ordinary_rows(reference):
        ordinary = [point for point in row['points'] if point['label'] == 'ORDINARY']
        source_keeps = [candidate for candidate in kept if candidate['source_name'] == row['video_id']]
        touched = [point for point in ordinary if any(candidate['original_native_range'][0] <= point['ordinal'] <
                   candidate['original_native_range'][1] for candidate in source_keeps)]
        touched_total += len(touched)
        cases.append(dict(case_id=row['case_id'], video_id=row['video_id'], source_key=row['source_key'],
                          ordinary_observation_count=len(ordinary), actual_KEEP_events=len(source_keeps),
                          touched_ordinary=[dict(ordinal=point['ordinal'], exact_pts=point['exact_pts']) for point in touched]))
    sufficient = touched_total == 0
    return dict(schema='RECALL_FIXED40_KNOWN_FACT_VETO_V1', group='facts', status=PASS if sufficient else INCONCLUSIVE,
        conditions=dict(complete_actual17_B0_inputs_calls_and_first_QA=True,
                        complete_actual_VERIFY_decisions_and_first_QA=True,
                        actual_explicit_KEEP_disjoint_from_all222_ORDINARY=sufficient,
                        frozen_B_union_K_merge_structurally_preserves_any_baseline=True),
        bindings=dict(registration_sha256=registration_sha, reference_ref=registration['reference_ref'],
                      execution_receipt_ref=ref(execution_path), first_independent_qa_ref=ref(first_qa_path),
                      merge_implementation_ref=merge_ref),
        scope=sources_api.SCOPE, source_count=9, completed_B0_calls=17, completed_VERIFY_calls=len(candidates),
        actual_explicit_KEEP_events=len(kept), ordinary_observations_checked=222, touched_ordinary_observations=touched_total,
        ordinary_addition_proved_zero_for_any_real_baseline=sufficient,
        fixed40_KEEP_deletion_threshold=0, KEEP_deletion_proved_zero_for_any_baseline_under_frozen_merge=True,
        KEEP_deletion_proof_kind='GENERAL_B_SUBSET_B_UNION_K_UNDER_EXACT_FROZEN_MERGE',
        real_VERIFY_baseline_reconstructed=False, real_VERIFY_baseline_required_to_resolve_touched_points=not sufficient,
        baseline_assumed_from_D8=False, original_reference_level=sources_api.REFERENCE_LEVEL,
        original_reference_coverage_pass=False, original_reference_quality_pass=False,
        original_UNKNOWN_points=2675, old_failed_gates_changed=False, cases=cases,
        production_final_baseline_frame_box_ratio_byte_QA='REQUIRED_PENDING_ACTUAL_PRODUCTION',
        production_final_QA_already_performed=False, production_admitted=False, submission_package_created=False,
        proxy_pass_and_known_fact_sufficient_condition_do_not_establish_online_quality=True,
        CPU_only=True, new_model_calls=0, media_decodes=0, vision_processor_calls=0, repeated_first_QA_replays=0)


def main():
    parser = argparse.ArgumentParser(description='Read only completed actual fixed40 execution; never infer or replay')
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = evaluate(args.root)
    output = Path(args.output).resolve()
    io.require(output.is_relative_to(io.root_path(args.root)), 'Fact-veto result must remain in its new independent output root')
    io.save(output, result)
    print(json.dumps(dict(status=result['status'], touched_ordinary_observations=result['touched_ordinary_observations'],
                          actual_explicit_KEEP_events=result['actual_explicit_KEEP_events'], production_admitted=False)))


if __name__ == '__main__':
    main()
