"""First independent TIME/BASE token, grammar and exact native-PTS QA.

CPU only. Legal empty answers remain successful evidence; missing or failed
generations are never converted to empty. No model, pixels or labels are read.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
from bisect import bisect_left
from collections import defaultdict
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
import traceback

W = Path('/home/inspur/aic_video_work')
RUN = W / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
SCHEMA = 'FIVE_SUMMARY_SPRINT_V41'
PARAMETERS = 8782459120
ROLES = ('TIME', 'BASE')
QA_STATUS = 'PASS_BOTH_ROLES_FIRST_INDEPENDENT_TOKEN_GRAMMAR_NATIVE_QA_41'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def bound(reference):
    path = Path(reference['path']).resolve(strict=True)
    require(path.is_relative_to(W) and path.is_file() and sha(path) == reference['sha256'],
            'Changed or out-of-workspace artifact: ' + str(path))
    if 'bytes' in reference:
        require(path.stat().st_size == reference['bytes'], 'Bound artifact byte size changed')
    return path


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def identity(reference):
    return str(bound(reference)), reference['sha256']


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())


def native_ranges(text, start, end, points, grammar_type, parser):
    require(grammar_type(end-start, max_segments=6, allow_empty=True).complete(text),
            'Unmodified output is outside the frozen grammar')
    segments = parser(text, end-start)
    ranges = []
    for left, right in segments:
        lo, hi = bisect_left(points, start+left), bisect_left(points, start+right)
        require(0 <= lo <= hi <= len(points)
                and all(start+left <= points[i] < start+right for i in range(lo, hi)),
                'Exact excerpt interval does not map to original native PTS')
        require(not lo or points[lo-1] < start+left, 'Off-by-one native left boundary')
        require(hi == len(points) or points[hi] >= start+right, 'Off-by-one native right boundary')
        ranges.append([lo, hi])
    return segments, ranges


def check_tokens(ids, tokenizer, eos, duration, grammar_type):
    require(isinstance(ids, list) and ids and len(ids) <= 512
            and all(type(value) is int and value >= 0 for value in ids)
            and ids[-1] == eos and eos not in ids[:-1], 'Actual complete token list with one final EOS required')
    grammar = grammar_type(duration, max_segments=6, allow_empty=True)
    text = ''
    for count in range(1, len(ids)):
        text = tokenizer.decode(ids[:count], skip_special_tokens=False,
                                clean_up_tokenization_spaces=False)
        require(grammar.valid_prefix(text), 'Actual token prefix violates the frozen grammar')
    require(grammar.complete(text), 'EOS preceded an incomplete grammar answer')
    return text


def run(registration_path):
    require(os.uname().nodename == 'inspur-NP5570M5', 'Only the registered Linux CPU host')
    path = Path(registration_path).resolve(strict=True); reg = read(path)
    require(path.is_relative_to(W) and reg['schema'] == SCHEMA
            and reg['expected_sources'] == 426 and reg['expected_windows'] == 522
            and reg['actual_resident_parameters'] == PARAMETERS
            and type(reg['actual_pipeline_parameters']) is int
            and PARAMETERS <= reg['actual_pipeline_parameters'] <= 9_000_000_000,
            'Fixed formal schema, denominator and complete parameter count')
    pipeline = reg['actual_pipeline_parameters']
    root = Path(reg['root']).resolve(strict=True)
    out = Path(reg['output_directory']).resolve(strict=True)
    require(root.is_relative_to(W) and out == root/'formal_outputs_41', 'Exact new formal output root')
    here = Path(__file__).resolve().parent
    for name in ('qa_outputs41.py', 'summary_output.py', 'summary_grammar6.py'):
        require(bound(reg['code'][name]) == here/name, 'Executed independent QA code binding: ' + name)
    sys.path.insert(0, str(here))
    from summary_output import parse_summary
    from summary_grammar6 import BoundedSegmentsGrammar
    for name in ('summary_output.py', 'summary_grammar6.py'):
        require(Path(sys.modules[name[:-3]].__file__).resolve() == bound(reg['code'][name]),
                'Imported grammar/parser path collision')
    cfg = read(bound(reg['model_config_ref'])); weights = reg['original_TIME_ref']; original = bound(weights)
    require(original == Path(cfg['b_adapter'])/'adapter_model.safetensors'
            and weights['sha256'] == cfg['b_adapter_sha256'], 'Exact original TIME, no failed trained adapter')
    admission = read(bound(reg['production_admission_ref']))
    require(admission['status'] == 'ADMIT_FROZEN_ORIGINAL_TIME_BASE_426_TWO_VIEW_41'
            and admission['production_allowed'] is True and admission['main_review_completed'] is True
            and identity(admission['original_TIME_ref']) == identity(weights)
            and admission['actual_pipeline_parameters'] == pipeline, 'Actual frozen original model admission')
    terminal_path = RUN/'controller'/(reg['job_name']+'.resource.json')
    terminal = read(terminal_path)
    ledger_path = W/'improvement_round1/gpu_ledger.jsonl'
    ledger = [json.loads(line) for line in ledger_path.read_text().splitlines()
              if line.strip() and json.loads(line).get('name') == reg['job_name']]
    require(terminal['name'] == reg['job_name'] and terminal['status'] == 'completed'
            and type(terminal['exit_code']) is int and terminal['exit_code'] == 0
            and ledger == [terminal], 'One natural completed/exit0 GPU resource and exactly equal unique ledger')
    accepted = read(bound(reg['first_input_acceptance_ref']))
    require(accepted['status'] == 'PASS_ALL426_FIRST_SUMMARY_FORMAL_TWO_VIEW_INPUTS_41'
            and accepted['sources'] == 426 and accepted['windows'] == 522
            and identity(accepted['registration_ref']) == identity(reg['input_phase_registration_ref']),
            'All first actual input acceptance and immutable input-phase registration join')
    prepared = read(bound(accepted['prepared_ref']))
    catalog_ref = prepared.get('source_catalog_ref', prepared.get('source_catalog'))
    catalog = read(bound(catalog_ref))['sources']
    sources = {row['id']: row for row in catalog}
    require(len(catalog) == len(sources) == 426 and set(sources) == {str(i) for i in range(426)},
            'Every formal source ID exactly once')
    requests, members, clocks = {}, defaultdict(list), {}
    for reference in prepared['inputs']:
        request = read(bound(reference)); uid, sid = request['uid'], request['sid']
        require(uid not in requests and sid in sources and request['labels_read'] is False
                and request['first_new_pixel_text_native_QA'] is True
                and request['source_sha256'] == sources[sid]['source_sha256']
                and identity(request['source_clock_ref']) == identity(sources[sid]['clock']),
                'Unique accepted source/request/native-clock identity')
        bound(request['prefix_ref'])  # Do not deserialize or replay pixel/input QA.
        requests[uid] = (reference, request); members[sid].append(request)
    require(len(requests) == 522 and set(members) == set(sources), 'All registered input windows, including empty outputs')
    for sid, windows in members.items():
        clock = read(bound(sources[sid]['clock'])); points = list(map(F, clock['normalized_exact_pts']))
        end = F(clock['physical_end_exact'])
        require(points and points[0] == 0 and all(a < b for a, b in zip(points, points[1:]))
                and end > points[-1] and clock['source_sha256'] == sources[sid]['source_sha256'],
                'Complete monotone original native source clock')
        intervals = sorted((F(row['plan']['window_start_exact']), F(row['plan']['window_end_exact'])) for row in windows)
        require(intervals[0][0] == 0 and intervals[-1][1] == end and all(a < b for a, b in intervals)
                and all(a[1] == b[0] for a, b in zip(intervals, intervals[1:])),
                'Whole-source coverage without ungenerated gaps treated as empty')
        clocks[sid] = (points, end)
    top = read(out/'completion.json')
    require(top['status'] == 'PASS_BOTH_ORIGINAL_TIME_BASE_FORMAL_GENERATIONS_41'
            and top['roles'] == list(ROLES) and top['sources'] == 426 and top['windows_per_role'] == 522
            and top['actual_resident_parameters'] == PARAMETERS and top['actual_pipeline_parameters'] == pipeline
            and top['optimizer_updates'] == 0 and top['labels_read'] is False
            and top['original_TIME_ref'] == weights
            and identity(top['registration_ref']) == identity(ref(path)), 'Both roles must actually finish before independent QA')
    exact_load = read(out/'exact_TIME_load_acceptance41.json')
    require(exact_load['status'] == 'PASS_ORIGINAL_TIME_EXACT_SAVED_FP32_BEFORE_ANY_FORWARD_41'
            and exact_load['original_TIME_ref'] == weights and exact_load['matrices'] == 288
            and exact_load['all288_bit_equal_saved'] is True and exact_load['model_forwards'] == 0,
            'Saved original FP32 TIME must be exactly loaded before the first actual forward')
    top_refs = top['role_completion_refs']
    require(len(top_refs) == 2, 'Exactly two actual role completions, no duplicate or ignored role')
    if isinstance(top_refs, list):
        top_refs = {read(bound(reference))['model_role']: reference for reference in top_refs}
    require(set(top_refs) == set(ROLES), 'Exactly TIME and BASE role completion refs')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(cfg['model_dir'], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids('<|im_end|>'); require(eos == 151645, 'Pinned actual EOS')
    role_reports = {}
    for role in ROLES:
        complete_path = bound(top_refs[role]); complete = read(complete_path)
        require(complete_path == out/role/'completion.json'
                and complete['status'] == 'PASS_ALL426_FORMAL_SUMMARY_GENERATIONS_41'
                and complete['model_role'] == role and complete['sources'] == 426 and complete['windows'] == 522
                and complete['optimizer_updates'] == 0 and complete['labels_read'] is False
                and complete['old_TIME_unchanged'] is True and complete['all_parameter_flags_unchanged'] is True
                and complete['original_TIME_exact_FP32_bits_unchanged'] is True
                and complete['adapter_disabled_actual_forward'] is (role == 'BASE')
                and complete['TIME_flags_restored'] is True
                and complete['forward_role_flag_checks'] > 0
                and complete['role_terminal'] == 'completed' and type(complete['role_exit_code']) is int
                and complete['role_exit_code'] == 0
                and identity(complete['registration_ref']) == identity(ref(path))
                and complete['model_weights_ref'] == weights
                and identity(complete['input_acceptance_ref']) == identity(reg['first_input_acceptance_ref'])
                and identity(complete['production_admission_ref']) == identity(reg['production_admission_ref']),
                'Exact naturally completed immutable role generation evidence')
        restoration = read(bound(complete['TIME_frozen_flag_restoration_ref']))
        require(restoration['status'] == 'PASS_ORIGINAL_TIME_ROLE_AND_FROZEN_FLAGS_RESTORED_41'
                and restoration['model_role'] == role and restoration['restored_trainable_parameters'] == 0
                and restoration['restored_disabled_layers'] == 0 and restoration['all144_TIME_layers_enabled'] is True
                and restoration['optimizer_updates'] == 0 and restoration['model_forwards_in_restoration'] == 0,
                'Actual post-role TIME enable flags and frozen trainability restored without a forward')
        inventory = complete['inventory']
        require(inventory['base'] == 8767123696 and inventory['TIME'] == 15335424
                and inventory['resident_parameters'] == PARAMETERS and inventory['actual_pipeline_parameters'] == pipeline
                and inventory['all_frozen'] is True and inventory['active_adapter'] == 'TIME'
                and inventory['matrices'] == 288 and inventory['language_targets'] == 144
                and complete['base_fingerprint']['sha256'] == cfg['expected_base_sha256'],
                'Actual shared BASE/TIME inventory, flags and BASE bytes')
        require(len(complete['outputs']) == 522 and len({identity(r) for r in complete['outputs']}) == 522,
                'Full unique role output denominator')
        details, seen, output_by_source, selected_by_source = [], set(), defaultdict(list), defaultdict(set)
        actual_forward_checks = 0
        for reference in complete['outputs']:
            output_path = bound(reference); output = read(output_path); uid, sid = output['uid'], output['sid']
            require(uid in requests and uid not in seen and sid == requests[uid][1]['sid']
                    and output_path == out/role/(uid+'.output.json')
                    and output['model_role'] == role and output['model_weights_ref'] == weights
                    and identity(output['request_ref']) == identity(requests[uid][0])
                    and output['adapter_disabled_actual_forward'] is (role == 'BASE')
                    and output['forward_role_flag_checks'] > 0, 'Exact role/request output and actual forward adapter state')
            actual_forward_checks += output['forward_role_flag_checks']
            request = requests[uid][1]; seen.add(uid); output_by_source[sid].append(reference)
            raw_path = bound(output['raw_token_ref']); raw = read(raw_path)
            require(raw_path == out/role/(uid+'.tokens.json') and all(raw[key] == output[key] for key in
                    ('uid', 'sid', 'request_ref', 'generated_ids', 'model_role', 'model_weights_ref')),
                    'Original raw token record differs from accepted output')
            require(raw['actual_prefix_signature'] == raw['expected_prefix_signature']
                    == {'input_ids': request['input_signature']['input_ids']}, 'Actual prefix differs from first input')
            start, end = F(request['plan']['window_start_exact']), F(request['plan']['window_end_exact'])
            points, source_end = clocks[sid]; require(0 <= start < end <= source_end, 'Exact excerpt domain')
            text = check_tokens(output['generated_ids'], tokenizer, eos, end-start, BoundedSegmentsGrammar)
            require(text == output['raw_text'], 'Raw decoded text was modified')
            segments, ranges = native_ranges(text, start, end, points, BoundedSegmentsGrammar, parse_summary)
            require([[str(a), str(b)] for a, b in segments] == output['parsed_exact_segments'], 'Exact Decimal parser identity')
            for a, b in ranges:
                selected_by_source[sid].update(range(a, b))
            details.append(dict(uid=uid, sid=sid, native_ranges=ranges, output_ref=reference,
                selected_native_frames=sum(b-a for a,b in ranges), valid_empty_JSON=not segments,
                segments_without_native_frames=sum(a == b for a,b in ranges),
                actual_token_prefixes_checked=len(output['generated_ids'])-1))
        require(seen == set(requests) and set(output_by_source) == set(sources), 'Every role window actually generated exactly once')
        require(actual_forward_checks == complete['forward_role_flag_checks'], 'Unique per-output and per-role actual-forward evidence sum')
        require(len(complete['source_completion_refs']) == 426, 'Durable completion for all 426 sources')
        completed = set()
        for reference in complete['source_completion_refs']:
            source = read(bound(reference)); sid = source['sid']
            require(sid in sources and sid not in completed
                    and source['status'] == 'PASS_FORMAL_SOURCE_SUMMARY_GENERATIONS_41'
                    and source['model_role'] == role and source['model_weights_ref'] == weights
                    and source['source_sha256'] == sources[sid]['source_sha256']
                    and identity(source['source_clock_ref']) == identity(sources[sid]['clock'])
                    and source['outputs'] == output_by_source[sid] and source['windows'] == len(members[sid]),
                    'Durable source completion identity')
            completed.add(sid)
        empty = sorted((sid for sid in sources if not selected_by_source[sid]), key=int)
        role_reports[role] = dict(completion_ref=top_refs[role], outputs=complete['outputs'], details=details,
            sources=426, windows=522, invalid_outputs=0, valid_empty_windows=sum(d['valid_empty_JSON'] for d in details),
            raw_selected_native_frames=sum(map(len, selected_by_source.values())), empty_source_ids=empty,
            all_sources_empty=len(empty) == 426, engineering_pass_not_quality_admission=True)
    require(sha(original) == weights['sha256'], 'Original TIME bytes changed during independent output QA')
    save(root/'first_independent_output_QA41.json', dict(status=QA_STATUS, schema=SCHEMA,
        registration_ref=ref(path), completion_ref=ref(out/'completion.json'), resource_ref=ref(terminal_path),
        unique_ledger_equal=True, job_name=reg['job_name'], sources=426, windows_per_role=522,
        total_outputs=1044, invalid_outputs=0, roles=role_reports,
        actual_resident_parameters=PARAMETERS, actual_pipeline_parameters=pipeline,
        source_native_counts={sid:len(value[0]) for sid,value in clocks.items()},
        source_clock_refs={sid:source['clock'] for sid,source in sources.items()},
        source_catalog_ref=catalog_ref, prepared_ref=accepted['prepared_ref'],
        source_empty_results_preserved_not_fallback=True, successful_empty_distinct_from_failure=True,
        requires_main_collapse_review=True, no_model_replay=True, no_media_or_processor=True,
        no_pixel_input_QA_replay=True, reference_labels_read=False))
    print(json.dumps(dict(status=QA_STATUS, sources=426, windows_per_role=522, total_outputs=1044)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--registration', required=True)
    argument = parser.parse_args().registration
    try:
        run(argument)
    except BaseException as error:
        root = Path(read(argument)['root']); failure = root/'first_independent_output_QA41_failure.json'
        if root.is_dir() and not failure.exists():
            save(failure, dict(error=repr(error), traceback=traceback.format_exc(), no_automatic_retry=True,
                              preserve_all_successes=True, no_model_replay=True, failure_to_empty=False))
        raise
