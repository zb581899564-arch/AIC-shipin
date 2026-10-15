"""CPU-only audit of the failed five-call v2 run, never an inference retry.

Deploy beside the frozen runtime on Linux, then run with the existing CPU Python
and -B. This creates cpu_partial_replay_v1.json once. It does not run preparation,
load model weights, decode source media, change v2, or manufacture completion.
"""
import argparse
import hashlib
import json
import math
import os
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_HERE = Path('/home/inspur/aic_video_work/temporal_refinement_pilot_20261011/dev_01')
LOCK_SHA256 = 'deebf054f43a54aa429016b68bd8878c5b3d01f997f006dda6d13aec493490fe'
CASES = tuple(f'T{i:02d}' for i in range(1, 7))
EXPECTED_CALLS = (('T01', 'baseline'), ('T01', 'refinement'),
                  ('T02', 'baseline'), ('T02', 'refinement'), ('T03', 'baseline'))
EXPECTED_ERROR = 'positive interval has no real native source frame'
READ_SHA256 = {}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def remember(path):
    path = Path(path).resolve()
    digest = sha(path)
    if str(path) in READ_SHA256:
        require(READ_SHA256[str(path)] == digest, 'input changed while auditing: '+str(path))
    READ_SHA256[str(path)] = digest
    return digest


def reject_constant(value):
    raise ValueError('nonfinite JSON constant: '+value)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key: '+key)
        result[key] = value
    return result


def parse_json(text):
    return json.loads(text, parse_constant=reject_constant, object_pairs_hook=unique_object)


def read_json(path):
    remember(path)
    return parse_json(Path(path).read_text(encoding='utf-8'))


def exact_pairs(values, duration):
    require(type(values) is list and len(values) <= 5, 'strict segment count/type differs')
    previous = Fraction(0)
    result = []
    for pair in values:
        require(type(pair) is list and len(pair) == 2, 'strict segment pair differs')
        require(all(type(v) in (float, int) and math.isfinite(v) for v in pair),
                'strict segment has nonfinite or nonnumeric value')
        start, stop = (Fraction(str(v)) for v in pair)
        require(previous <= start < stop <= duration, 'strict segment geometry differs')
        result.append([start, stop])
        previous = stop
    return result


def independent_observations(pairs, points, origin):
    """Count the entire source clock directly; do not reuse native_ranges/bisect."""
    observations = []
    for index, (start, stop) in enumerate(pairs, 1):
        start, stop = Fraction(str(start))+origin, Fraction(str(stop))+origin
        ordinals = [i for i, point in enumerate(points) if start <= point < stop]
        first = sum(point < start for point in points)
        exclusive_stop = sum(point < stop for point in points)
        require(ordinals == list(range(first, exclusive_stop)), 'independent clock count is inconsistent')
        observations.append(dict(segment_index=index, source_start_exact=str(start),
            source_end_exact=str(stop), native_count=len(ordinals), first_ordinal=first,
            exclusive_stop_ordinal=exclusive_stop,
            first_native_pts=str(points[ordinals[0]]) if ordinals else None,
            last_native_pts=str(points[ordinals[-1]]) if ordinals else None))
    return observations


def observed_ranges(observations):
    return [[r['first_ordinal'], r['exclusive_stop_ordinal']] for r in observations]


def independently_sample(points, start, stop):
    eligible = [i for i, point in enumerate(points) if start <= point < stop]
    require(bool(eligible), 'request has no actual native observations')
    if len(eligible) <= 64:
        return eligible
    return [eligible[i*(len(eligible)-1)//63] for i in range(64)]


def independently_intersect(values, candidates, offset):
    shifted = [[Fraction(str(a))+offset, Fraction(str(b))+offset] for a, b in values]
    source = [[Fraction(str(a)), Fraction(str(b))] for a, b in candidates]
    pieces = sorted([max(a, c), min(b, d)] for a, b in shifted for c, d in source
                    if max(a, c) < min(b, d))
    merged = []
    for start, stop in pieces:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], stop)
        else:
            merged.append([start, stop])
    require(len(merged) <= 5, 'independent final intersection exceeds five intervals')
    return shifted, merged


def check_lock():
    lock_path = HERE/'source_lock_v2.json'
    require(remember(lock_path) == LOCK_SHA256, 'original v2 source lock SHA differs')
    lock = read_json(lock_path)
    require(lock['scope'] == 'LIMITED_VISUAL_FACT_MECHANISM_DIAGNOSTIC_ONLY'
            and lock['max_model_calls'] == 12 and lock['quality_pass_allowed'] is False,
            'original v2 scope differs')
    files = lock['files']
    require(type(files) is dict and bool(files), 'missing frozen file manifest')
    for path, digest in files.items():
        require(remember(path) == digest, 'frozen v2 input SHA differs: '+path)
    required = ['runtime.py', 'infer_v2.py', 'contract_v2.py', 'cpu_probe_v2.py',
                'inputs.json', 'baseline_cpu_acceptance.json', 'mechanism_scope.json']
    require(all(str(HERE/name) in files for name in required), 'required v2 inputs are not frozen')
    return dict(source_lock_sha256=LOCK_SHA256, frozen_files=len(files), all_frozen_sha256_equal=True)


def check_attempts():
    path = HERE/'attempts.jsonl'
    remember(path)
    events = [parse_json(line) for line in path.read_text(encoding='utf-8').splitlines()]
    begun, accepted, pending = [], {}, None
    for event in events:
        if event['event'] == 'BEGIN_MODEL_CALL':
            require(pending is None, 'new call began before previous call was accepted')
            require(event['call_id'] == len(begun)+1, 'BEGIN IDs are not unique consecutive actual calls')
            raw_path = Path(event['raw_path'])
            identity = (raw_path.parent.name, raw_path.name.removesuffix('_raw.json'))
            require(len(begun) < len(EXPECTED_CALLS) and identity == EXPECTED_CALLS[len(begun)],
                    'actual call sequence differs from this failed run')
            require(raw_path == HERE/identity[0]/(identity[1]+'_raw.json'), 'raw path escapes fixed run')
            require(type(event.get('utc')) is str and bool(event['utc']), 'BEGIN has no actual timestamp')
            begun.append(event)
            pending = event
        elif event['event'] == 'ACCEPTED_MODEL_CALL':
            require(pending is not None and event['call_id'] == pending['call_id']
                    and event['raw_path'] == pending['raw_path'], 'ACCEPTED has no corresponding BEGIN')
            require(event['call_id'] not in accepted, 'duplicate ACCEPTED terminal')
            accepted[event['call_id']] = event
            pending = None
        else:
            raise ValueError('unknown actual call ledger event')
    failure = read_json(HERE/'failure.json')
    require(len(begun) == 5 and set(accepted) == {1, 2, 3, 4}
            and pending == begun[-1], 'actual five-BEGIN/four-ACCEPTED denominator differs')
    require(failure['status'] == 'STOP_NO_RETRY_NO_EMPTY_FALLBACK'
            and failure['error'] == 'ValueError: '+EXPECTED_ERROR,
            'original natural v2 failure differs')
    require(failure['actual_started_model_calls'] == len(begun) and failure['attempts'] == begun,
            'failure denominator does not equal durable BEGIN ledger')
    require('contract_v2.py' in failure['traceback'] and 'native_ranges' in failure['traceback']
            and EXPECTED_ERROR in failure['traceback'], 'failure does not identify native realizability')
    require(not (HERE/'inference_completion.json').exists(), 'failed original run unexpectedly has completion')
    return begun, accepted


def load_inputs():
    entries = read_json(HERE/'inputs.json')
    require([e['case_id'] for e in entries] == list(CASES), 'six-source input denominator differs')
    metas = {}
    for entry in entries:
        path = Path(entry['input_path'])
        require(path == HERE/entry['case_id']/'input.json', 'input path escapes fixed case')
        require(remember(path) == entry['input_sha256'], 'input metadata SHA differs')
        meta = read_json(path)
        require(meta['case_id'] == entry['case_id'], 'input metadata case differs')
        points = [Fraction(value) for value in meta['all_source_exact_pts']]
        require(len(points) == meta['source_total_frames'] and bool(points)
                and points[0] == 0 and all(a < b for a, b in zip(points, points[1:])),
                'full native source clock differs')
        start, stop = Fraction(meta['window_start']), Fraction(meta['window_end'])
        require(0 <= start < stop < points[-1] and stop-start == 30, 'fixed source domain differs')
        require(remember(meta['source_path']) == meta['source_sha256'], 'source media SHA differs')
        require(remember(meta['frame_array_path']) == meta['frame_array_sha256'], 'accepted RGB cache SHA differs')
        metas[meta['case_id']] = (meta, points)
    prior = read_json(HERE/'baseline_cpu_acceptance.json')
    require(prior['CPU_only'] is True and prior['CUDA_initialized'] is False
            and prior['new_model_calls'] == 0 and prior['new_optimizer_updates'] == 0,
            'inherited CPU input acceptance differs')
    proofs = {p['case_id']: p for p in prior['proofs']}
    require(len(prior['proofs']) == 6 and set(proofs) == set(CASES), 'inherited CPU denominator differs')
    return metas, proofs


def check_model_receipt():
    receipt = read_json(HERE/'model_identity.json')
    identity = receipt['identity']
    require(identity['base']['sha256'] == '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
            and identity['base']['parameters'] == 8767123696 and identity['logical_parameters'] == 8782459120
            and identity['adapter']['sha256'] == '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'
            and identity['adapter']['tensors'] == 288 and identity['adapter']['actual_saved_values_equal'] is True
            and identity['adapter']['adapter_enabled'] is True and receipt['selected_time_adapter_enabled'] is True
            and receipt['same_model_for_both_arms'] is True and receipt['new_optimizer_updates'] == 0,
            'archived original B model identity receipt differs')
    return dict(archived_model_identity_sha256=READ_SHA256[str(HERE/'model_identity.json')],
                original_B_identity_receipt_equal=True, live_weights_reloaded=False)


def replay_call(processor, runtime, torch, np, begun, accepted, metas, prior, replayed):
    from constrained_json import make_prefix_constraint
    from contract_v2 import native_ranges
    raw_path = Path(begun['raw_path'])
    case, stage = raw_path.parent.name, raw_path.name.removesuffix('_raw.json')
    meta, points = metas[case]
    q = read_json(HERE/case/(stage+'_request.json'))
    raw = read_json(raw_path)
    origin, end = Fraction(q['source_start']), Fraction(q['source_end'])
    duration = end-origin
    lo, hi = Fraction(meta['window_start']), Fraction(meta['window_end'])
    require(lo <= origin < end <= hi, 'actual request exceeds original source window')
    require(q['ordinals'] == independently_sample(points, origin, end), 'request sampling is not exact native floor64')
    require(q['exact_pts'] == [meta['all_source_exact_pts'][i] for i in q['ordinals']],
            'request ordinal/PTS membership differs')
    cache = Path(q['cached_array'])
    if stage == 'baseline':
        require(origin == lo and end == hi and q['text'] == runtime.EMPTY_PROMPT,
                'actual baseline request is not original B prompt/domain')
        require(cache == Path(meta['frame_array_path']) and q['ordinals'] == meta['source_frame_ordinals']
                and q['exact_pts'] == meta['sample_exact_pts'], 'baseline native cache selection differs')
        require(remember(cache) == meta['frame_array_sha256'], 'baseline cache differs')
    else:
        base = replayed[(case, 'baseline')]['segments']
        expected_origin = max(lo, lo+Fraction(str(base[0][0]))-3)
        expected_end = min(hi, lo+Fraction(str(base[-1][1]))+3)
        require((origin, end) == (expected_origin, expected_end), 'registered candidate context differs')
        proposed = [[float(Fraction(str(a))-(origin-lo)), float(Fraction(str(b))-(origin-lo))] for a, b in base]
        exact_pairs(proposed, duration)
        require(q['candidate_context_local'] == proposed, 'actual candidate hint differs')
        base_obs = independent_observations(base, points, lo)
        hint_obs = independent_observations(proposed, points, origin)
        require(observed_ranges(base_obs) == observed_ranges(hint_obs), 'hint changes original native membership')
        text = runtime.REFINEMENT_PROMPT.format(candidates=json.dumps(proposed, separators=(',', ':')),
                                              duration=float(duration))
        require(q['text'] == text, 'actual refinement prompt differs')
        reused = q['ordinals'] == meta['source_frame_ordinals']
        require(q['new_sampling_not_repeated_original_decode'] is (not reused), 'cache reuse declaration differs')
        require(cache == (Path(meta['frame_array_path']) if reused else HERE/case/'context_frames.npz'),
                'context cache path differs')
        require(remember(cache) == q['array_sha256'], 'context cache SHA differs')
    with np.load(cache, allow_pickle=False) as archive:
        require(archive.files == ['rgb'], 'RGB cache member differs')
        arr = archive['rgb']
    require(arr.dtype == np.uint8 and arr.shape == (len(q['ordinals']), meta['height'], meta['width'], 3),
            'cached native RGB geometry/dtype differs')
    if stage == 'baseline':
        require([hashlib.sha256(a.tobytes()).hexdigest() for a in arr] == meta['pixel_sha256'],
                'baseline accepted pixel SHA differs')
    encoded, detail = runtime.encode(processor, meta, (arr, q['ordinals'], q['exact_pts']), origin, q['text'])
    require(not torch.cuda.is_initialized(), 'CPU processor replay initialized CUDA')
    require(all(v.device.type == 'cpu' for v in encoded.values() if torch.is_tensor(v)), 'CPU replay has non-CPU tensor')
    require(detail == raw['input_evidence'], 'actual raw CPU processor signature differs from independent replay')
    if stage == 'baseline':
        require(detail == prior[case]['input_evidence'], 'inherited accepted baseline input differs')
    transfer_path = Path(str(raw_path)+'.gpu_input.json')
    transfer = read_json(transfer_path)
    require(transfer['status'] == 'PASS_ACTUAL_CPU_GPU_TENSOR_EQUALITY'
            and transfer['tensor_signature'] == detail['tensor_signature'],
            'archived actual GPU input equality does not equal independent CPU replay')
    token_ids, scores = raw['output_token_ids'], raw['selected_token_scores']
    require(type(token_ids) is list and 0 < len(token_ids) <= 256
            and all(type(token) is int and token >= 0 for token in token_ids), 'actual output token IDs differ')
    require(type(scores) is list and len(scores) == len(token_ids)
            and all(type(score) in (float, int) and math.isfinite(score) for score in scores),
            'actual token/score denominator or finite check failed')
    require(raw['input_tokens'] == int(encoded['input_ids'].shape[1]) <= 16384
            and raw['output_tokens'] == len(token_ids) and raw['actual_model_call'] is True,
            'actual token receipt/input prefix differs')
    require(type(raw['generation_seconds']) in (float, int) and math.isfinite(raw['generation_seconds'])
            and raw['generation_seconds'] >= 0, 'actual generation timing is invalid')
    decoded = processor.tokenizer.decode(token_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    require(decoded == raw['raw_output'], 'actual generated token IDs/raw text differ')
    grammar = make_prefix_constraint(processor.tokenizer, raw['input_tokens'], duration, allow_empty=True)
    grammar.assert_complete(token_ids)
    raw_object = parse_json(raw['raw_output'])
    require(type(raw_object) is dict and set(raw_object) == {'segments'}, 'strict raw JSON object differs')
    pairs = exact_pairs(raw_object['segments'], duration)
    segments, errors, warnings = runtime.parse_segments(raw['raw_output'], duration, allow_empty=True)
    require(segments is not None and not errors, 'original strict parser replay failed')
    require([[Fraction(str(a)), Fraction(str(b))] for a, b in segments] == pairs,
            'original parser changed raw segment values')
    observations = independent_observations(pairs, points, origin)
    zero = [row['segment_index'] for row in observations if row['native_count'] == 0]
    call_id = begun['call_id']
    if call_id in accepted:
        require(not zero and native_ranges(segments, meta['all_source_exact_pts'], origin) == observed_ranges(observations),
                'accepted native realizability differs from independent full-clock count')
        require(accepted[call_id]['raw_sha256'] == READ_SHA256[str(raw_path)]
                and accepted[call_id]['native_ranges'] == observed_ranges(observations),
                'actual ACCEPTED raw SHA/native ranges differ')
        native_status = 'PASS_NATIVE_REALIZABILITY'
        frozen_contract_rejection = None
    else:
        require((case, stage) == ('T03', 'baseline') and zero == [3, 4], 'unexpected failed native intervals')
        require(meta['fps_num'] == 12 and meta['fps_den'] == 1 and (lo, hi) == (28, 58)
                and all(point == Fraction(i, 12) for i, point in enumerate(points)), 'failed source actual 12fps clock differs')
        require(raw_object['segments'] == [[0, 0.0333], [0.0667, 0.1333], [0.1667, 0.2333],
                                           [0.2667, 0.3333], [0.3667, 0.4333]], 'actual failed raw intervals differ')
        require([row['native_count'] for row in observations] == [1, 1, 0, 0, 1], 'expected failed native counts differ')
        try:
            native_ranges(segments, meta['all_source_exact_pts'], origin)
        except ValueError as exc:
            require(str(exc) == EXPECTED_ERROR, 'frozen native contract raised a different failure')
            frozen_contract_rejection = str(exc)
        else:
            raise ValueError('frozen native contract unexpectedly accepted the failed raw')
        native_status = 'EXPECTED_NATIVE_REALIZABILITY_FAILURE_REPRODUCED'
    del encoded, arr
    proof = dict(call_id=call_id, case_id=case, stage=stage, raw_path=str(raw_path),
        raw_sha256=READ_SHA256[str(raw_path)], request_sha256=READ_SHA256[str(HERE/case/(stage+'_request.json'))],
        gpu_input_receipt_sha256=READ_SHA256[str(transfer_path)], input_tensors_exact=True,
        archived_actual_gpu_tensor_equality_verified=True, GPU_reexecuted=False,
        token_score_count=len(token_ids), strict_json_grammar_parser_pass=True,
        parse_warnings=warnings, parsed_segments=segments, native_status=native_status,
        independent_full_source_fraction_observations=observations, zero_native_segment_indices=zero,
        frozen_contract_expected_rejection=frozen_contract_rejection,
        actual_accepted_model_call=(call_id in accepted))
    replayed[(case, stage)] = dict(segments=segments, request=q, proof=proof)
    return proof


def verify_prediction(case, metas, replayed):
    from contract_v2 import project_context
    meta, points = metas[case]
    baseline = replayed[(case, 'baseline')]
    refinement = replayed[(case, 'refinement')]
    q = refinement['request']
    lo, hi, origin = Fraction(meta['window_start']), Fraction(meta['window_end']), Fraction(q['source_start'])
    prediction = read_json(HERE/case/'prediction.json')
    require(prediction['case_id'] == case and prediction['source_sha256'] == meta['source_sha256']
            and prediction['candidate_only'] is True and prediction['baseline_segments'] == baseline['segments'],
            'original successful baseline prediction differs')
    shifted, exact = independently_intersect(refinement['segments'], baseline['segments'], origin-lo)
    independent_result = [[float(a), float(b)] for a, b in exact]
    exact_pairs(independent_result, hi-lo)
    independent_ranges = observed_ranges(independent_observations(exact, points, lo))
    require(independent_ranges == observed_ranges(independent_observations(independent_result, points, lo)),
            'independent final float projection changes actual native membership')
    require(all(any(Fraction(str(c)) <= a < b <= Fraction(str(d)) for c, d in baseline['segments'])
                for a, b in exact), 'independent final selection exceeds original candidates')
    projected, projection = project_context(refinement['segments'], baseline['segments'], origin-lo,
                                            hi-lo, meta['all_source_exact_pts'], lo)
    require(projected == independent_result == prediction['refined_segments']
            and projection == prediction['exact_projection']
            and projection['exact_shifted'] == [[str(a), str(b)] for a, b in shifted]
            and projection['exact_final'] == [[str(a), str(b)] for a, b in exact]
            and projection['native_ranges'] == independent_ranges, 'final candidate intersection replay differs')
    for stage, data in [('baseline', baseline), ('refinement', refinement)]:
        call = prediction[stage+'_call']
        proof = data['proof']
        require(call['raw_path'] == proof['raw_path'] and call['raw_sha256'] == proof['raw_sha256']
                and call['parse_warnings'] == proof['parse_warnings']
                and call['native_ranges'] == observed_ranges(proof['independent_full_source_fraction_observations']),
                'successful prediction call provenance differs')
    require(prediction['context_source_start'] == q['source_start'] and prediction['context_source_end'] == q['source_end']
            and prediction['context_frames'] == len(q['ordinals']) and prediction['baseline_frames'] == 64
            and prediction['original_frames_reused'] == (q['ordinals'] == meta['source_frame_ordinals'])
            and prediction['proposed_before_candidate_intersection'] == [[float(a), float(b)] for a, b in shifted],
            'successful prediction context/offset provenance differs')
    return dict(case_id=case, status='PARTIAL_CASE_COMPLETE_NOT_QUALITY',
        prediction_sha256=READ_SHA256[str(HERE/case/'prediction.json')],
        final_intersection_independently_rederived=True, frozen_project_context_equal=True,
        baseline_segments=baseline['segments'], refined_segments=independent_result,
        actual_model_calls=2)


def require_absent(case, stages, prediction=True):
    for stage in stages:
        for suffix in ('_request.json', '_raw.json', '_raw.json.gpu_input.json'):
            require(not (HERE/case/(stage+suffix)).exists(), 'unrun stage has unexpected inference artifact')
    if prediction:
        require(not (HERE/case/'prediction.json').exists(), 'unrun/failed case has unexpected prediction')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE/'cpu_partial_replay_v1.json')
    args = parser.parse_args()
    require(HERE == EXPECTED_HERE, 'partial replay must be deployed beside this exact frozen Linux run')
    output = args.output.resolve()
    require(output.parent == HERE and output.name == 'cpu_partial_replay_v1.json' and not output.exists(),
            'partial CPU output is fixed and create-only')
    frozen = check_lock()
    begun, accepted = check_attempts()
    metas, prior = load_inputs()
    model_receipt = check_model_receipt()
    if 'torch' in sys.modules:
        require(not sys.modules['torch'].cuda.is_initialized(), 'CUDA was already initialized')
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    import torch
    import numpy as np
    require(not torch.cuda.is_initialized(), 'CPU audit must not initialize CUDA')
    import runtime
    require(runtime.HERE == HERE, 'imported frozen runtime belongs to another run')
    from transformers import AutoProcessor
    config = read_json(runtime.RUN/'b_score_aligned_package_v4/config.json')
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True,
                                             min_pixels=131072, max_pixels=131072)
    replayed = {}
    proofs = [replay_call(processor, runtime, torch, np, item, accepted, metas, prior, replayed) for item in begun]
    cases = [verify_prediction(case, metas, replayed) for case in ('T01', 'T02')]
    require_absent('T03', ('refinement',))
    cases.append(dict(case_id='T03', status='FAILED_BASELINE_NATIVE_REALIZABILITY_NO_PREDICTION',
                      actual_model_calls=1, zero_native_segment_indices=[3, 4]))
    for case in ('T04', 'T05', 'T06'):
        require_absent(case, ('baseline', 'refinement'))
        cases.append(dict(case_id=case, status='UNRUN_NOT_EMPTY_PREDICTION', actual_model_calls=0,
                          baseline_segments=None, refined_segments=None))
    require(len(proofs) == len(begun) == 5
            and sum(p['actual_accepted_model_call'] for p in proofs) == len(accepted) == 4,
            'independent partial replay denominator differs')
    require(not torch.cuda.is_initialized(), 'CPU audit unexpectedly initialized CUDA')
    require(not (HERE/'inference_completion.json').exists(), 'original failure was replaced by completion')
    for path, digest in READ_SHA256.items():
        require(sha(path) == digest, 'input changed during partial CPU replay: '+path)
    result = dict(status='PASS_PARTIAL_CPU_REPLAY_EXPECTED_V2_FAILURE_NOT_QUALITY',
        source_run_status='FAILED_NO_RETRY_NO_EMPTY_FALLBACK', scope='LIMITED_VISUAL_FACT_MECHANISM_DIAGNOSTIC_ONLY',
        CPU_only=True, CUDA_initialized=False, new_model_calls=0, new_optimizer_updates=0,
        new_426_inference=0, quality_pass_allowed=False, inference_completion_created=False,
        actual_started_model_calls=len(begun), actual_accepted_model_calls=len(accepted),
        actual_native_passes=4, actual_expected_native_failures=1, actual_unrun_cases=3,
        frozen_input_acceptance=frozen, archived_model_receipt_acceptance=model_receipt,
        proofs=proofs, cases=cases, audited_input_sha256=READ_SHA256,
        replay_source_sha256=sha(__file__), reference_labels_read=False,
        limitations=['Only the five actual calls are replayed; this is not a completed six-case inference.',
                     'GPU equality is checked against archived actual transfer receipts; GPU/model are not rerun.',
                     'Exact native counts audit the frozen full-source PTS; source media is not decoded again.',
                     'Expected failure reproduction is engineering evidence, not quality or official score evidence.'])
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(dict(status=result['status'], actual_started_model_calls=5,
        actual_accepted_model_calls=4, native_passes=4, expected_native_failures=1,
        unrun_cases=3, output=str(output), output_sha256=sha(output)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
