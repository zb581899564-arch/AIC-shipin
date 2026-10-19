"""First independent formal output QA; no pixel/model/processor/label replay."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
from bisect import bisect_left
from collections import defaultdict
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import traceback

from summary_output import parse_summary
from summary_grammar6 import BoundedSegmentsGrammar

W = Path('/home/inspur/aic_video_work')
RUN = W / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ROLE = 'SUMMARY_FINAL'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def bound(reference):
    path = Path(reference['path']).resolve(strict=True)
    require(path.is_relative_to(W) and path.is_file() and sha(path) == reference['sha256'],
            'Changed/out-of-workspace bound output evidence')
    if 'bytes' in reference:
        require(path.stat().st_size == reference['bytes'], 'Bound byte count changed')
    return path


def identity(reference):
    return str(bound(reference)), reference['sha256']


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())


def native_ranges(text, start, end, points):
    require(BoundedSegmentsGrammar(end-start, max_segments=6, allow_empty=True).complete(text),
            'Actual unmodified raw is outside the registered output grammar')
    segments = parse_summary(text, end-start)
    ranges = []
    for left, right in segments:
        lo, hi = bisect_left(points, start+left), bisect_left(points, start+right)
        require(0 <= lo <= hi <= len(points)
                and all(start+left <= points[i] < start+right for i in range(lo, hi)),
                'Exact source-local output does not map to original native PTS')
        if lo:
            require(points[lo-1] < start+left, 'Native left boundary off by one')
        if hi < len(points):
            require(points[hi] >= start+right, 'Native right boundary off by one')
        ranges.append([lo, hi])
    return segments, ranges


def run(registration_path):
    require(os.uname().nodename == 'inspur-NP5570M5', 'Only the actual registered CPU host')
    path = Path(registration_path).resolve(strict=True); reg = read(path)
    require(reg['schema'] == 'SUMMARY_TWO_VIEW_FORMAL_426_V14' and reg['role'] == ROLE
            and reg['expected_sources'] == 426, 'Explicit formal schema/role')
    here = Path(__file__).resolve().parent
    for name, reference in reg['code'].items():
        require(Path(name).name == name and bound(reference) == here/name, 'Executed QA dependency changed')
    cfg = read(bound(reg['model_config_ref'])); weights = reg['final_adapter_ref']; bound(weights)
    admission = read(bound(reg['production_admission_ref']))
    frozen = read(bound(reg['final_freeze_ref']))
    require(admission['status'] == 'ADMIT_FIXED_SUMMARY_FINAL559_426'
            and admission['production_allowed'] is True and admission['main_review_completed'] is True
            and identity(admission['final_adapter_ref']) == identity(weights)
            and frozen['status'] == 'FINAL559_WEIGHTS_FROZEN_BEFORE_DEV_METRICS'
            and identity(frozen['final_adapter_ref']) == identity(weights), 'Exact externally admitted final559')
    terminal_path = RUN/'controller'/(reg['job_name']+'.resource.json')
    terminal = read(terminal_path)
    ledger = [json.loads(line) for line in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip() and json.loads(line).get('name') == reg['job_name']]
    require(terminal['status'] == 'completed' and type(terminal['exit_code']) is int
            and terminal['exit_code'] == 0 and ledger == [terminal], 'Unique natural completed/exit0 ledger')
    out = Path(reg['output_directory']).resolve(strict=True)
    require(out.is_relative_to(W), 'Explicit actual output root')
    complete = read(out/'completion.json')
    require(complete['status'] == 'PASS_ALL426_FORMAL_SUMMARY_GENERATIONS'
            and complete['model_role'] == ROLE and complete['sources'] == 426
            and complete['windows'] == reg['expected_windows']
            and complete['optimizer_updates'] == 0 and complete['labels_read'] is False
            and complete['old_TIME_unchanged'] is True and complete['all_parameter_flags_unchanged'] is True
            and identity(complete['model_weights_ref']) == identity(weights)
            and identity(complete['registration_ref']) == identity(ref(path)), 'Complete immutable formal execution evidence')
    inv = complete['inventory']
    require(inv['base'] == 8767123696 and inv['summary'] == 15335424
            and inv['resident_parameters'] == reg['actual_resident_parameters'] == 8782459120
            and inv['actual_pipeline_parameters'] == reg['actual_pipeline_parameters'] <= 9_000_000_000
            and inv['all_frozen'] is True and inv['active_adapter'] == 'summary' and inv['matrices'] == 288
            and complete['base_fingerprint']['sha256'] == cfg['expected_base_sha256'],
            'Actual base/summary/pipeline count, flags and base byte identity')
    accepted = read(bound(reg['first_input_acceptance_ref']))
    require(accepted['status'] == 'PASS_ALL426_FIRST_SUMMARY_FORMAL_TWO_VIEW_INPUTS'
            and accepted['sources'] == 426 and accepted['windows'] == reg['expected_windows'],
            'All426 first actual input acceptance required')
    require(identity(accepted['registration_ref']) == identity(reg['input_phase_registration_ref']),
            'First CPU acceptance and separately frozen GPU input registration must join exactly')
    prepared = read(bound(accepted['prepared_ref']))
    catalog = read(bound(prepared.get('source_catalog_ref', prepared.get('source_catalog'))))['sources']
    sources = {row['id']: row for row in catalog}
    require(len(sources) == 426 and set(sources) == {str(i) for i in range(426)}, 'All original formal source IDs')
    requests, members, clocks = {}, defaultdict(list), {}
    for reference in prepared['inputs']:
        request = read(bound(reference)); uid, sid = request['uid'], request['sid']
        require(uid not in requests and sid in sources and request['labels_read'] is False
                and request['first_new_pixel_text_native_QA'] is True
                and request['source_sha256'] == sources[sid]['source_sha256']
                and identity(request['source_clock_ref']) == identity(sources[sid]['clock']),
                'Original unique accepted source/clock request identity')
        # Prefix identity only: do not deserialize tensors or repeat pixel QA.
        bound(request['prefix_ref']); requests[uid] = (reference, request); members[sid].append(request)
    require(len(requests) == reg['expected_windows'] and set(members) == set(sources), 'All registered new windows')
    for sid, windows in members.items():
        clock = read(bound(sources[sid]['clock'])); points = list(map(F, clock['normalized_exact_pts']))
        end = F(clock['physical_end_exact'])
        require(points and points[0] == 0 and all(a < b for a, b in zip(points, points[1:]))
                and end > points[-1] and clock['source_sha256'] == sources[sid]['source_sha256'],
                'Complete native source clock and original byte identity')
        intervals = sorted((F(row['plan']['window_start_exact']), F(row['plan']['window_end_exact'])) for row in windows)
        require(intervals[0][0] == 0 and intervals[-1][1] == end
                and all(a < b for a, b in intervals)
                and all(a[1] == b[0] for a, b in zip(intervals, intervals[1:])),
                'Whole native source coverage without missing windows or implicit-as-empty gaps')
        clocks[sid] = (points, end)
    require(len(complete['outputs']) == reg['expected_windows']
            and len({identity(r) for r in complete['outputs']}) == reg['expected_windows'], 'Full unique output denominator')
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg['model_dir'], local_files_only=True)
    eos = tok.convert_tokens_to_ids('<|im_end|>'); require(eos == 151645, 'Pinned actual EOS')
    details, seen, output_by_source = [], set(), defaultdict(list)
    for reference in complete['outputs']:
        output = read(bound(reference)); uid, sid = output['uid'], output['sid']
        require(uid in requests and uid not in seen and sid == requests[uid][1]['sid']
                and output['model_role'] == ROLE and identity(output['model_weights_ref']) == identity(weights)
                and identity(output['request_ref']) == identity(requests[uid][0]), 'Exact output/source/model/request join')
        seen.add(uid); request = requests[uid][1]; output_by_source[sid].append(reference)
        ids = output['generated_ids']
        require(ids and len(ids) <= 512 and ids[-1] == eos and eos not in ids[:-1]
                and all(type(value) is int and value >= 0 for value in ids), 'Complete exact generated IDs/EOS')
        raw = read(bound(output['raw_token_ref']))
        require(all(raw[key] == output[key] for key in
                    ('uid', 'sid', 'request_ref', 'generated_ids', 'model_role', 'model_weights_ref')),
                'First raw token record differs from accepted output')
        require(raw['actual_prefix_signature'] == raw['expected_prefix_signature']
                == {'input_ids': request['input_signature']['input_ids']}, 'Actual generated prefix differs from first input')
        text = tok.decode(ids[:-1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        require(text == output['raw_text'], 'Unmodified decoded raw text identity')
        start, end = F(request['plan']['window_start_exact']), F(request['plan']['window_end_exact'])
        points, source_end = clocks[sid]; require(0 <= start < end <= source_end, 'Exact legal excerpt coordinates')
        segments, ranges = native_ranges(text, start, end, points)
        require([[str(a), str(b)] for a, b in segments] == output['parsed_exact_segments'], 'Exact Decimal parser identity')
        details.append(dict(uid=uid, sid=sid, native_ranges=ranges,
            selected_native_frames=sum(b-a for a, b in ranges), valid_empty_JSON=not segments,
            segments_without_native_frames=sum(a == b for a, b in ranges), output_ref=reference))
    require(seen == set(requests) and set(output_by_source) == set(sources), 'All registered outputs exactly once')
    require(len(complete['source_completion_refs']) == 426, 'Every source has durable output completion')
    completed_sources = set()
    for reference in complete['source_completion_refs']:
        source = read(bound(reference)); sid = source['sid']
        require(sid in sources and sid not in completed_sources
                and source['status'] == 'PASS_FORMAL_SOURCE_SUMMARY_GENERATIONS'
                and source['model_role'] == ROLE and identity(source['model_weights_ref']) == identity(weights)
                and source['source_sha256'] == sources[sid]['source_sha256']
                and source['outputs'] == output_by_source[sid] and source['windows'] == len(members[sid]),
                'Durable whole-source completion identity')
        completed_sources.add(sid)
    save(out/'first_independent_output_QA.json', dict(
        status='PASS_ALL426_FIRST_INDEPENDENT_SUMMARY_FORMAL_TOKEN_GRAMMAR_NATIVE_QA',
        model_role=ROLE, outputs=complete['outputs'], resource_ref=ref(terminal_path),
        completion_ref=ref(out/'completion.json'), unique_ledger_equal=True,
        sources=426, windows=reg['expected_windows'], invalid_outputs=0, details=details,
        no_model_replay=True, no_media_or_processor=True, no_pixel_input_QA_replay=True,
        reference_labels_read=False, source_empty_results_preserved_not_fallback=True))
    print(json.dumps(dict(status='PASS_ALL426_FIRST_INDEPENDENT_SUMMARY_FORMAL_TOKEN_GRAMMAR_NATIVE_QA',
                          sources=426, windows=reg['expected_windows'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--registration', required=True)
    args = parser.parse_args()
    try:
        run(args.registration)
    except BaseException as error:
        out = Path(read(Path(args.registration))['output_directory'])
        failure = out/'first_independent_output_QA_failure.json'
        if out.is_dir() and not failure.exists():
            save(failure, dict(error=repr(error), traceback=traceback.format_exc(),
                              no_automatic_retry=True, no_model_replay=True, preserve_all_successes=True))
        raise
