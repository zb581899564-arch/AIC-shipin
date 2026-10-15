"""Independent CPU tensor/token/native-boundary replay; never calls a model.

Re-encoding is the new request's independent proof, not another model attempt.
No old successful CPU input/replay stage is invoked or rewritten.
"""
import argparse
from bisect import bisect_left
from fractions import Fraction as F
import json
import math
import os
from pathlib import Path
import traceback

from lb_contract import MAX_OUTPUT_TOKENS, prompt, response_strings
from lb_grammar import BoundaryConstraint, candidates
import lb_io as io


def independent_endpoint(decision, meta, clock):
    """Separate implementation from infer's resolve_endpoint conversion."""
    points = [F(p) for p in meta['all_source_exact_pts']]
    raw_pts = [F(p) for p in clock['original_exact_pts']]
    origin = F(meta['original_clock_origin_exact'])
    if len(points) != len(raw_pts) or any(raw-origin != point for raw, point in zip(raw_pts, points)):
        raise ValueError('Independent normalized/native clock conversion differs')
    old = F(meta['original_endpoint_exact'])
    cut = bisect_left(points, old)
    durations = meta['native_duration_by_ordinal']
    physical_end = F(clock['physical_end_exact'])

    def contiguous(i):
        if i < 0 or str(i) not in durations or durations[str(i)] is None:
            return False
        d = F(durations[str(i)])
        next_raw = raw_pts[i+1] if i+1 < len(raw_pts) else physical_end+origin
        return d > 0 and raw_pts[i]+d == next_raw

    if meta['original_endpoint_kind'] == 'SOURCE_START':
        original_contiguous = old == 0 and points[0] == 0 and raw_pts[0] == origin
    elif meta['original_endpoint_kind'] == 'SOURCE_PHYSICAL_END':
        endpoint_evidence = clock.get('physical_endpoint_evidence', {})
        last_duration = clock.get('last_frame_duration_exact', endpoint_evidence.get('last_frame_duration_exact'))
        original_contiguous = (last_duration is not None and F(last_duration) > 0 and old == physical_end and
                               points[-1]+F(last_duration) == physical_end)
    else:
        original_contiguous = 0 < cut < len(points) and points[cut-1] < old <= points[cut] and contiguous(cut-1)
    if original_contiguous != meta['original_endpoint_continuity_verified']:
        raise ValueError('Independent original endpoint adjacency/positive-duration proof differs')
    for index, ordinal in enumerate(meta['source_frame_ordinals']):
        verified = contiguous(ordinal-1 if meta['side'] == 'start' else ordinal)
        if verified != meta['continuity_by_sample'][str(index)]:
            raise ValueError('Independent sample adjacency/positive-duration proof differs')
    if decision not in [json.loads(s) for s in response_strings(meta)]:
        raise ValueError('Independent finite decision parser rejected the actual raw')
    new, reason = old, decision['decision']
    if reason == 'REFINE':
        index = decision['sample_index']
        ordinal = meta['source_frame_ordinals'][index]
        if index in (0, 63):
            reason = 'UNKNOWN_EDGE_SAMPLE'
        else:
            shown = [F(p) for p in meta['sample_exact_pts']]
            context_start, context_end = F(meta['window_start']), F(meta['window_end'])
            new_cut = points[ordinal] if meta['side'] == 'start' else (
                points[ordinal+1] if ordinal+1 < len(points) else physical_end)
            visible = (context_start <= shown[index-1] < new_cut < shown[index+1] < context_end
                       if meta['side'] == 'start' else
                       context_start <= shown[index] < new_cut <= shown[index+1] < context_end)
            if visible != meta['selected_cut_has_two_sided_visible_samples'][str(index)]:
                raise ValueError('Independent selected native cut two-sided visible geometry differs')
            if not visible:
                reason = 'UNKNOWN_CHOSEN_CUT_VISIBLE_CONTEXT'
            elif not original_contiguous:
                reason = 'UNKNOWN_ORIGINAL_ENDPOINT_NATIVE_DOMAIN'
            elif not contiguous(ordinal-1 if meta['side'] == 'start' else ordinal):
                reason = 'UNKNOWN_SAMPLE_CONTINUITY'
            elif meta['side'] == 'start':
                new = points[ordinal]
            else:
                new = points[ordinal+1] if ordinal+1 < len(points) else physical_end
            if reason == 'REFINE' and (
                    (meta['original_endpoint_kind'] == 'SOURCE_START' and new <= old) or
                    (meta['original_endpoint_kind'] == 'SOURCE_PHYSICAL_END' and new >= old)):
                reason, new = 'UNKNOWN_SOURCE_BOUNDARY_OUTWARD_OR_UNCHANGED', old
        if reason == 'REFINE' and str(new) != meta['sample_boundary_exact'][index]:
            raise ValueError('Independent first-included/exclusive-end conversion differs')
    return dict(request_id=meta['request_id'], event_id=meta['event_id'], side=meta['side'],
        raw_decision=decision, applied_decision=reason, original_endpoint_exact=str(old),
        endpoint_exact=str(new), displacement_exact=str(new-old), changed=new != old)


def independent_event(event, endpoints):
    start_result, end_result = endpoints[event['event_id']+'.start'], endpoints[event['event_id']+'.end']
    if (start_result['event_id'] != event['event_id'] or start_result['side'] != 'start' or
            end_result['event_id'] != event['event_id'] or end_result['side'] != 'end'):
        raise ValueError('Independent original event/endpoint pair identity differs')
    old = tuple(map(F, event['original_interval_exact']))
    a, b = F(start_result['endpoint_exact']), F(end_result['endpoint_exact'])
    crossed = a >= b
    if crossed:
        a, b = old
    return dict(event_id=event['event_id'], original_case_id=event['original_case_id'],
        original_segment_index=event['original_segment_index'],
        original_interval_exact=list(map(str, old)), refined_interval_exact=[str(a), str(b)],
        changed=(a, b) != old, pair_conflict_preserved_original=crossed,
        endpoint_results=[start_result, end_result], new_event_created=False, original_event_removed=False)


def main(base):
    io.host(cpu=True)
    base = io.base_path(base)
    admission, cpu, rows = io.admitted_inputs(base)
    resource, resource_sha = io.terminal_resource(admission['gpu_job_name'])
    gpu = base/'gpu_01'
    complete = io.read(gpu/'completion.json')
    if (complete['status'] != 'PASS_ALL_LOCAL_BOUNDARY_CALLS_NOT_QUALITY' or
            complete['actual_model_calls'] != len(rows) or complete['requests'] != len(rows) or
            complete['gpu_admission_sha256'] != io.sha(base/'gpu_admission.json') or
            complete['attempts_sha256'] != io.sha(gpu/'attempts.jsonl') or
            complete['model_identity_sha256'] != io.sha(gpu/'model_identity.json')):
        raise ValueError('Actual complete unique model execution is not accepted')
    journal = [json.loads(s) for s in (gpu/'attempts.jsonl').read_text().splitlines() if s.strip()]
    if len(journal) != 2*len(rows):
        raise ValueError('Actual model attempt/accepted denominator is incomplete')
    for i, (entry, _, _) in enumerate(rows, 1):
        started, accepted = journal[2*(i-1):2*i]
        if (started['event'] != 'BEGIN_MODEL_CALL' or accepted['event'] != 'ACCEPTED_MODEL_CALL' or
                started['call_id'] != i or accepted['call_id'] != i or
                started['request_id'] != entry['request_id'] or accepted['request_id'] != entry['request_id']):
            raise ValueError('Actual unique request order differs from registration')
    done_by_id = {entry['request_id']: entry for entry in complete['entries']}
    if len(done_by_id) != len(rows):
        raise ValueError('Successful actual request IDs missing/duplicated')
    out = base/'replay_01'
    out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json', dict(pid=os.getpid(), utc=io.utc(), CPU_only=True,
        resource_terminal_sha256=resource_sha, gpu_completion_sha256=io.sha(gpu/'completion.json'),
        new_model_calls=0, new_optimizer_updates=0))
    current, proofs, endpoints = None, [], {}
    try:
        runtime, processor, runtime_identity = io.cpu_runtime()
        if runtime_identity != cpu['bindings']['original_b_processor_runtime']:
            raise ValueError('Independent original CPU processor/runtime identity changed')
        config = io.read(io.RUN/'b_score_aligned_package_v4/config.json')
        generation = io.read(Path(config['model_dir'])/'generation_config.json')
        eos = generation['eos_token_id']
        eos = [eos] if isinstance(eos, int) else list(eos)
        strings = tuple(sorted({s for _, _, meta in rows for s in response_strings(meta)}))
        allowed_tokens = candidates(processor.tokenizer, strings)
        for entry, proof, meta in rows:
            current = entry['request_id']
            accepted = done_by_id[current]
            done_path = io.checked_ref(dict(path=accepted['done_path'], sha256=accepted['done_sha256']), roots=(gpu,))
            if done_path != gpu/current/'done.json':
                raise ValueError('Accepted actual done path is not this unique request')
            done = io.read(done_path)
            raw_path, request_path = gpu/current/'raw.json', gpu/current/'request.json'
            raw, request = io.read(raw_path), io.read(request_path)
            if (done['raw_sha256'] != io.sha(raw_path) or done['request_sha256'] != io.sha(request_path) or
                    request['CPU_proof_sha256'] != entry['proof_sha256'] or
                    request['input_sha256'] != proof['input_sha256'] or
                    request['encoded_tensor_sha256'] != proof['encoded_tensor_sha256'] or
                    request['encoded_tensor_format'] != io.TENSOR_CACHE_FORMAT or
                    proof['encoded_tensor_format'] != io.TENSOR_CACHE_FORMAT or
                    request['prompt'] != meta['prompt'] or meta['prompt'] != prompt(meta) or
                    request['reference_labels_read'] is not False or raw['actual_model_call'] is not True or
                    request['finite_response_strings'] != list(response_strings(meta))):
                raise ValueError('Actual untouched raw/request/CPU input binding differs')
            frames = runtime.baseline_frames(meta)
            encoded, evidence = runtime.encode(processor, meta, frames, F(meta['window_start']), meta['prompt'])
            if not evidence == proof['input_evidence'] == request['input_evidence'] == raw['input_evidence'] == done['input_evidence']:
                raise ValueError('Independent actual RGB/processor/tensor signature differs')
            cache_path = io.checked_ref(dict(path=proof['encoded_tensor_path'],
                sha256=proof['encoded_tensor_sha256']), roots=(base,))
            cached = io.load_tensor_cache(cache_path)
            if runtime.tensor_signature(cached) != evidence['tensor_signature']:
                raise ValueError('Independent lossless gzip cache tensor signature differs')
            transfer = io.read(gpu/current/'gpu_input.json')
            if (transfer['status'] != 'PASS_ACCEPTED_CPU_GPU_TENSOR_EQUALITY' or
                    transfer['tensor_signature'] != evidence['tensor_signature'] or
                    transfer['encoded_tensor_sha256'] != proof['encoded_tensor_sha256'] or
                    transfer['encoded_tensor_format'] != io.TENSOR_CACHE_FORMAT):
                raise ValueError('Accepted actual CPU/GPU tensor transfer changed')
            ids, scores = raw['output_token_ids'], raw['selected_token_scores']
            if (not 0 < len(ids) <= MAX_OUTPUT_TOKENS or any(type(t) is not int or t < 0 for t in ids) or
                    len(ids) != len(scores) or len(ids) != raw['generated_score_count'] or
                    len(ids) != raw['output_tokens'] or len(ids) != done['output_tokens'] or
                    any(type(s) not in (float, int) or not math.isfinite(s) for s in scores) or
                    int(encoded['input_ids'].shape[1]) != raw['input_tokens'] or
                    raw['input_tokens'] != proof['input_tokens'] or raw['eos_token_ids'] != eos):
                raise ValueError('Independent input/output-token/finite-score identity differs')
            decoded = processor.tokenizer.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
            if decoded != raw['raw_output']:
                raise ValueError('Actual token IDs do not decode to the untouched raw')
            grammar = BoundaryConstraint(processor.tokenizer, raw['input_tokens'], meta, eos, allowed_tokens)
            decision = grammar.assert_complete(ids)
            if decision != done['decision'] or json.dumps(decision, separators=(',', ':')) != decoded:
                raise ValueError('Independent finite native decision parser differs')
            clock = io.extract_clock(io.read(io.checked_ref(meta['original_evidence']['clock'])),
                                     meta['clock_object_keys'])
            endpoint = independent_endpoint(decision, meta, clock)
            if endpoint != done['endpoint_result']:
                raise ValueError('Independent native endpoint/UNKNOWN retention conversion differs')
            endpoints[current] = endpoint
            proof_path = out/(current+'.json')
            io.save(proof_path, dict(status='PASS_INDEPENDENT_CPU_BOUNDARY_TENSOR_TOKEN_NATIVE_REPLAY',
                request_id=current, event_id=meta['event_id'], side=meta['side'], CPU_only=True,
                done_sha256=io.sha(done_path), raw_sha256=io.sha(raw_path), input_evidence=evidence,
                endpoint_result=endpoint, new_model_calls=0, new_optimizer_updates=0))
            proofs.append(dict(request_id=current, proof_path=str(proof_path), proof_sha256=io.sha(proof_path)))
            print(json.dumps(dict(completed_replays=len(proofs), total_requests=len(rows))), flush=True)
            del encoded, cached, frames
        events = io.read(base/'plan_01/events.json')
        exported = [independent_event(event, endpoints) for event in events]
        import torch
        if torch.cuda.is_initialized():
            raise ValueError('Independent replay initialized CUDA')
        io.save(out/'completion.json', dict(status='PASS_ALL_NEW_LOCAL_BOUNDARY_INDEPENDENT_REPLAYS_NOT_QUALITY',
            requests=len(proofs), events=len(events), proofs=proofs, CPU_only=True, CUDA_initialized=False,
            gpu_completion_sha256=io.sha(gpu/'completion.json'), resource_terminal_sha256=resource_sha,
            new_model_calls=0, new_optimizer_updates=0))
        io.save(base/'boundary_prediction_export.json', dict(status='PASS_LOCAL_BOUNDARY_EXECUTION_REPLAY_NOT_QUALITY',
            events=exported, independent_replay_completion_sha256=io.sha(out/'completion.json'),
            original_b_model_parameters=io.MODEL_PARAMETERS, reference_labels_read=False,
            new_model_calls=0, new_optimizer_updates=0,
            retained_events=len(events), newly_created_events=0, removed_events=0))
    except BaseException as error:
        io.save(out/'failure.json', dict(status='FAILED_NEW_REPLAY_KEEP_RAW_AND_SUCCESSFUL_PROOFS',
            request_id=current, successful_proofs=proofs, error=repr(error),
            traceback=traceback.format_exc(), new_model_calls=0, new_optimizer_updates=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True)
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    main(args.base)
