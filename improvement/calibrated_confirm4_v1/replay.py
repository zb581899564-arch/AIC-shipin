"""First independent CPU output replay and exact protected-policy construction."""
from bisect import bisect_left
from fractions import Fraction as F
import json
import math
import numpy as np
from confirm_common import bound, read, ref, require, save
from prepare import _torch


def _tokens(run):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(run.model_config()['model_dir'], local_files_only=True)


def _raw(raw, tok):
    ids = raw['output_token_ids']; scores = raw['selected_scores']
    require(0 < len(ids) <= 256 and len(ids) == raw['output_tokens'] == len(scores) == raw['generated_score_count']
            and all(type(token) is int and token >= 0 for token in ids)
            and all(type(score) in (int, float) and math.isfinite(score) for score in scores), 'Independent untouched output-token/finite-score denominator')
    require(tok.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False) == raw['raw_output'], 'Independent generated-token decode')
    return ids


def b0_output_qa(run):
    torch = _torch(run); run.begin('b0_output_qa')
    lock = run.accepted('b0'); terminal = run.terminal('b0')
    produced, gpu = run.receipt('b0_prepare'), run.receipt('b0_gpu')
    require(gpu['actual_calls'] == len(gpu['outputs']) == lock['expected_calls'], 'Actual complete B0 calls')
    rt = run.runtime(); gm = run.module('constrained_json'); tok = _tokens(run)
    candidates = gm.ascii_token_candidates(tok)
    windows = []
    for input_ref, done_ref in zip(produced['inputs'], gpu['outputs']):
        proof = read(bound(input_ref)); meta = read(bound(proof['meta_ref'])); done = read(bound(done_ref))
        raw = read(bound(done['raw_ref'])); request = read(bound(done['request_ref']))
        require(done['input_ref'] == input_ref and done['case_id'] == proof['case_id']
                and request['input_signature'] == proof['input_evidence']['tensor_signature']
                and request['reference_labels_read'] is False and request['model_role'] == 'TIME_ENABLED', 'Actual B0 input/role/raw binding')
        ids = _raw(raw, tok); lo, hi = F(meta['window_start']), F(meta['window_end'])
        require(raw['input_tokens'] == proof['input_tokens'], 'B0 actual prompt length')
        grammar = gm.make_prefix_constraint(tok, raw['input_tokens'], hi-lo, candidate_token_ids=candidates,
                                           eos_token_ids=raw['eos'], allow_empty=True)
        grammar.assert_complete(ids)
        segments, errors, warnings = rt.parse_segments(raw['raw_output'], hi-lo, allow_empty=True)
        require(segments is not None and not errors and segments == done['segments'] and warnings == done['parse_warnings']
                and done['status'] == ('MODEL_OK' if segments else 'LEGAL_EMPTY'), 'Independent original B0 grammar/parser replay')
        points = list(map(F, meta['all_source_exact_pts'])); events, native = [], []
        for index, pair in enumerate(segments):
            a, b = [F(str(value)) for value in pair]
            require(0 <= a < b <= hi-lo, 'Exact original B0 interval domain')
            members = [i for i, point in enumerate(points) if lo+a <= point < lo+b]
            require(members and members == list(range(members[0], members[-1]+1)), 'Independent exact B0 native membership')
            native.append([members[0], members[-1]+1])
            events.append(dict(event_id='confirm.'+proof['case_id']+'.seg'+str(index), original_segment_index=index,
                               original_interval_exact=[str(lo+a), str(lo+b)]))
        windows.append(dict(sid=proof['sid'], case_id=proof['case_id'], input_ref=input_ref,
                            done_ref=done_ref, events=events, native_ranges=native))
    require(len(windows) == lock['expected_calls'] and not torch.cuda.is_initialized(), 'First complete CPU B0 output QA')
    run.finish('b0_output_qa', windows=windows, calls=len(windows), terminal_ref=terminal,
               source_lock_ref=ref(run.root/'locks/b0.json'), no_processor_or_model_calls=True)


def verify_output_qa(run):
    torch = _torch(run); run.begin('verify_output_qa')
    lock = run.accepted('verify'); terminal = run.terminal('verify')
    inputs, gpu = run.receipt('verify_prepare')['inputs'], run.receipt('verify_gpu')
    require(gpu['actual_calls'] == len(gpu['outputs']) == len(inputs) == lock['expected_calls'], 'Actual complete VERIFY calls')
    tok = _tokens(run); gm = run.module('cv_grammar'); cv = run.module('cv_contract')
    decisions = {}
    for input_ref, done_ref in zip(inputs, gpu['outputs']):
        row, done = read(bound(input_ref)), read(bound(done_ref))
        raw, request = read(bound(done['raw_ref'])), read(bound(done['request_ref']))
        require(done['input_ref'] == input_ref and request['input_signature'] == row['full_signature']
                and request['model_role'] == 'TIME_ENABLED' and request['reference_labels_read'] is False, 'Actual VERIFY input/role binding')
        ids = _raw(raw, tok)
        grammar = gm.VerifyConstraint(tok, raw['input_tokens'], row['request'], raw['eos'], candidates=())
        parsed = grammar.assert_complete(ids)
        require(parsed['decision'] == done['decision'] and raw['raw_output'] == json.dumps(parsed, separators=(',', ':')),
                'Independent canonical finite VERIFY grammar')
        cv.resolve(raw['raw_output'], row['request'], execution_status='MODEL_OK')
        event_id = row['request']['event_id']
        require(event_id == done['event_id'] and event_id not in decisions, 'Unique original event decision')
        decisions[event_id] = parsed['decision']
    expected = {event['event_id'] for window in run.receipt('b0_output_qa')['windows'] for event in window['events']}
    require(set(decisions) == expected and not torch.cuda.is_initialized(), 'All events assessed; failure cannot become UNKNOWN')
    run.finish('verify_output_qa', decisions=decisions, calls=len(decisions), terminal_ref=terminal,
               source_lock_ref=ref(run.root/'locks/verify.json'), no_processor_or_model_calls=True)


def context_output_qa(run):
    torch = _torch(run); run.begin('context_output_qa')
    lock = run.accepted('context'); terminal = run.terminal('context')
    produced, gpu = run.receipt('context_prepare'), run.receipt('context_gpu')
    require(gpu['actual_calls'] == produced['expected_calls'] == lock['expected_calls'], 'Actual context batch denominator')
    require([s['sid'] for s in gpu['sources']] == run.c['source_ids'], 'Actual BASE source order')
    queries = 0
    for source, output in zip(produced['sources'], gpu['sources']):
        languages, pairs = [], []
        require(len(source['cases']) == len(output['cases']), 'Actual BASE case count')
        for expected, case in zip(source['cases'], output['cases']):
            require(case['input_ref'] == expected and case['role'] == 'BASE_DISABLED', 'Actual BASE input/source/target binding')
            request = read(bound(case['request_ref']))
            require(request['input_ref'] == expected and request['model_role'] == 'BASE_DISABLED'
                    and request['actual_model_call_started'] is True and request['labels_read'] is False,
                    'Independent actual BASE call/role/label exclusion evidence')
            value = torch.load(bound(case['output_ref']), map_location='cpu', weights_only=True)
            k = expected['queries']
            require(value['language'].shape == (k, 4096) and value['yes_no'].shape == (k, 2)
                    and torch.isfinite(value['language']).all() and torch.isfinite(value['yes_no']).all(), 'Independent finite4096 BASE outputs')
            languages.append(value['language'].numpy()); pairs.append(value['yes_no'].numpy()); queries += k
        require(np.array_equal(np.concatenate(languages), np.load(bound(output['language_ref'])))
                and np.array_equal(np.concatenate(pairs), np.load(bound(output['yes_no_ref'])))
                and len(np.concatenate(languages)) == source['cells'], 'Independent full-source concatenation/order')
    require(queries == gpu['context_queries'] == produced['expected_queries'] and not torch.cuda.is_initialized(), 'First complete CPU BASE output QA')
    run.finish('context_output_qa', sources=gpu['sources'], calls=lock['expected_calls'], queries=queries, terminal_ref=terminal,
               source_lock_ref=ref(run.root/'locks/context.json'), no_processor_or_model_calls=True)


def time_masks(clock, windows, decisions):
    """Exact original D8 padding and KEEP/UNKNOWN union, before semantic residual."""
    points = list(map(F, clock['normalized_exact_pts']))
    b0 = np.zeros(len(points), bool); verify = np.zeros(len(points), bool)
    expected = {event['event_id'] for window in windows for event in window['events']}
    require(set(decisions) == expected, 'Complete unique decision domain for this source')
    for window in windows:
        lo, hi = F(window['window_start']), F(window['window_end'])
        for event in window['events']:
            a, b = map(F, event['original_interval_exact'])
            require(0 <= lo <= a < b <= hi, 'Original event/window domain')
            first, last = max(lo, a-F(3, 4)), min(hi, b+F(1, 2)+(F(1, 4) if b-a >= 8 else F(0)))
            left, right = bisect_left(points, first), bisect_left(points, last)
            require(left < right, 'Actual padded event contains native frames')
            b0[left:right] = True
            decision = decisions[event['event_id']]
            require(decision in ('KEEP', 'UNKNOWN', 'DROP'), 'No failure-to-UNKNOWN fallback')
            if decision != 'DROP':
                verify[left:right] = True
    return b0, verify


def finalize(run):
    _torch(run); out = run.begin('finalize')
    contexts = run.receipt('context_output_qa')['sources']
    b0 = run.receipt('b0_output_qa'); decisions = run.receipt('verify_output_qa')['decisions']
    native = run.receipt('b0_prepare')['sources']; semantic = run.module('sr_common')
    require((semantic.OLD/'selected_head.pt').resolve() == bound(run.dependencies['semantic_head']).resolve(), 'Exact original frozen semantic head')
    exported = []
    for source, context in zip(native, contexts):
        require(source['sid'] == context['sid'], 'Final source/context order')
        clock = read(bound(source['clock_ref']))
        with np.load(bound(source['native_ref']), allow_pickle=False) as value:
            groups, samples = value['groups'], value['sample_ordinals']
        windows = []
        for window in b0['windows']:
            if window['sid'] == source['sid']:
                proof = read(bound(window['input_ref'])); meta = read(bound(proof['meta_ref']))
                windows.append(dict(window_start=meta['window_start'], window_end=meta['window_end'], events=window['events']))
        event_ids = {event['event_id'] for window in windows for event in window['events']}
        initial, verified = time_masks(clock, windows, {key: decisions[key] for key in event_ids})
        language = np.load(bound(context['language_ref']))
        require(language.shape == (len(samples), 4096) and len(groups) == len(initial), 'Complete original source language/native domain')
        hidden, score, baseline = semantic.semantic(language, verified, groups)
        require(np.array_equal(baseline, verified | (score[groups] > 1.)) and np.all(verified <= baseline), 'Exact40.47 complete temporal policy')
        path = out/(source['sid']+'.npz')
        with path.open('xb') as stream:
            np.savez(stream, baseline=baseline, B0_D8=initial, VERIFY=verified, groups=groups,
                     sample_ordinals=samples, semantic_score=score, semantic_hidden=hidden)
        exported.append(dict(sid=source['sid'], name=source['name'], clock_ref=source['clock_ref'], data_ref=ref(path),
            language_ref=context['language_ref'], yes_no_ref=context['yes_no_ref'], selected_frames=int(baseline.sum()),
            native_frames=len(baseline), cells=len(samples), labels_read=False))
    run.finish('finalize', sources=exported, original_model_parameters=8782459120, original_semantic_parameters=98329,
               quality_or_reference_evaluation_performed=False, formal426_accessed=False)
