"""One CPU evaluation of frozen source-summary generations; no model or decode.

Manifest fields (all refs have path/sha256, optionally bytes):
  dev_prepared_ref, baseline_human_adoption_ref (the 33-source registration),
  role_output_refs, role_completion_refs, role_resource_refs,
  role_output_QA_refs (keys INIT_TIME/TRAINED), initial_TIME_ref,
  final_adapter_ref, frozen_selection_ref.
Each role completion must bind model_role and its exact 43 outputs. The manifest
is an explicit adoption of completed generations, never permission to retry them.
The eight historical VideoXum sources are exposed development, not a blind test.
"""
import argparse
from bisect import bisect_left
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import traceback

import numpy as np

from summary_output import parse_summary


ROOT = Path('/home/inspur/aic_video_work/bottleneck_24h_20261019_v1/summary_objective_v20')
WORK = Path('/home/inspur/aic_video_work')
ROLES = ('INIT_TIME', 'TRAINED')
SIDS = tuple('V%02d' % i for i in range(8))
WINDOWS = 43


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'Duplicate metadata JSON key: ' + key)
        value[key] = item
    return value


def _nonfinite(value):
    raise ValueError('Nonfinite metadata JSON constant: ' + value)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),
                      object_pairs_hook=_unique_object, parse_constant=_nonfinite)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)


def bound(reference):
    require(isinstance(reference, dict) and isinstance(reference.get('path'), str)
            and isinstance(reference.get('sha256'), str), 'Explicit path/SHA reference required')
    path = Path(reference['path']).resolve(strict=True)
    require(path.is_relative_to(WORK) and path.is_file(), 'Input outside registered workspace or not a file: ' + str(path))
    require(sha(path) == reference['sha256'], 'Input SHA changed: ' + str(path))
    if 'bytes' in reference:
        require(type(reference['bytes']) is int and reference['bytes'] == path.stat().st_size,
                'Input byte count changed: ' + str(path))
    return path


def reference_key(reference):
    """Equality of bound identity; optional descriptive fields do not matter."""
    return str(Path(reference['path']).resolve(strict=True)), reference['sha256']


def same_ref(left, right):
    return reference_key(left) == reference_key(right)


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def exact(value):
    # Exact strings/integers only; never admit JSON binary floats as native time.
    require(type(value) in (str, int), 'Exact rational native time required')
    return Fraction(value)


def native_interval_mask(points, intervals):
    """Half-open source intervals, one native ordinal mask, no interpolation."""
    mask = np.zeros(len(points), dtype=bool)
    for start, end in intervals:
        require(start < end, 'Nonempty interval required')
        mask[bisect_left(points, start):bisect_left(points, end)] = True
    return mask


def metric(mask, labels):
    """All raters equally; preserve source_clear's explicit zero denominators."""
    require(mask.dtype == labels.dtype == np.bool_ and mask.ndim == 1
            and labels.ndim == 2 and labels.shape[0] == len(mask) and labels.shape[1] > 0,
            'One native source mask and all original reviewer columns required')
    p = int(mask.sum())
    g = labels.sum(axis=0, dtype=np.int64)
    tp = labels[mask].sum(axis=0, dtype=np.int64)
    fp, fn = p - tp, g - tp
    precision = tp / max(1, p)
    recall = tp / np.maximum(1, g)
    f1 = 2 * tp / np.maximum(1, p + g)
    raters = [dict(reviewer=i, reference_selected=int(g[i]), true_positive=int(tp[i]),
                   false_positive=int(fp[i]), false_negative=int(fn[i]),
                   precision=float(precision[i]), recall=float(recall[i]), f1=float(f1[i]),
                   prediction_empty=(p == 0), reference_empty=bool(g[i] == 0),
                   both_empty=bool(p == 0 and g[i] == 0)) for i in range(len(g))]
    return dict(precision=float(precision.mean()), recall=float(recall.mean()), f1=float(f1.mean()),
                selected_native_frames=p, native_frames=len(mask), native_frame_coverage=p / len(mask),
                prediction_empty=(p == 0), empty_reference_reviewers=int((g == 0).sum()),
                empty_prediction_false_positives=0 if p == 0 else None,
                empty_prediction_false_negatives_by_reviewer=g.tolist() if p == 0 else None,
                reviewers=raters)


def matched_semantic(groups, scores, selected_count):
    """Choose exactly model K; score descending, original ordinal ascending."""
    require(groups.ndim == scores.ndim == 1 and len(groups) > 0
            and groups.dtype.kind in 'iu' and groups.min() >= 0
            and scores.dtype.kind in 'fiu' and groups.max() < len(scores)
            and np.isfinite(scores).all(), 'Finite semantic/native group domain')
    require(type(selected_count) is int and 0 <= selected_count <= len(groups), 'Actual model K in native domain')
    ordinal = np.arange(len(groups), dtype=np.int64)
    native_scores = np.asarray(scores[groups], dtype=np.float64)
    order = np.lexsort((ordinal, -native_scores))
    result = np.zeros(len(groups), dtype=bool)
    result[order[:selected_count]] = True
    require(int(result.sum()) == selected_count, 'Matched semantic exact actual native count')
    return result


def difference(actual, control):
    return dict(added_native_frames=int((actual & ~control).sum()),
                removed_native_frames=int((control & ~actual).sum()),
                common_native_frames=int((actual & control).sum()),
                identical=bool(np.array_equal(actual, control)))


def comparison(actual_metric, control_metric, actual, control):
    return dict(delta={key: actual_metric[key] - control_metric[key]
                       for key in ('precision', 'recall', 'f1', 'native_frame_coverage')},
                **difference(actual, control))


def verify_output_set(completion, role, output_refs):
    require(completion.get('model_role') == role, role + ' evidence role mismatch')
    require(isinstance(completion.get('outputs'), list) and len(completion['outputs']) == WINDOWS,
            role + ' evidence must bind all43 outputs')
    expected = [reference_key(item) for item in output_refs]
    completed = [reference_key(item) for item in completion['outputs']]
    require(len(set(completed)) == WINDOWS and set(completed) == set(expected),
            role + ' evidence output identities differ from manifest')
    for item in completion['outputs']:
        bound(item)


def verify_completion(reference, role, output_refs, weights_ref):
    completion = read(bound(reference))
    require(completion.get('status') == 'PASS_ALL43_MATCHED_SUMMARY_GENERATIONS',
            role + ' has no successful generation completion')
    verify_output_set(completion, role, output_refs)
    require(same_ref(completion['model_weights_ref'], weights_ref), role + ' completed model weights differ')
    for key in ('actual_calls', 'free_generation_calls', 'windows', 'outputs_count'):
        if key in completion:
            require(type(completion[key]) is int and completion[key] == WINDOWS,
                    role + ' completion count mismatch: ' + key)
    return completion


def verify_role_admission(manifest, role, output_refs):
    resource = read(bound(manifest['role_resource_refs'][role]))
    require(resource.get('status') == 'completed' and type(resource.get('exit_code')) is int
            and resource['exit_code'] == 0, role + ' wrapper did not naturally complete/exit0')
    qa = read(bound(manifest['role_output_QA_refs'][role]))
    require(qa.get('status') == 'PASS_ALL43_FIRST_INDEPENDENT_SUMMARY_TOKEN_GRAMMAR_NATIVE_QA',
            role + ' first independent output QA not accepted')
    verify_output_set(qa, role, output_refs)


def load_requests(manifest):
    prepared = read(bound(manifest['dev_prepared_ref']))
    require(prepared.get('exposed_development_not_blind') is True, 'Historical exposed development identity required')
    references = prepared['inputs']
    require(isinstance(references, list) and len(references) == WINDOWS, 'Exactly43 adopted matched dev inputs')
    requests = {}
    for reference in references:
        request = read(bound(reference))
        uid, sid = request['uid'], request['sid']
        require(isinstance(uid, str) and uid and uid not in requests and sid in SIDS,
                'Missing/duplicate dev uid or wrong source identity')
        require(request.get('first_new_pixel_text_native_QA') is True and request.get('labels_read') is False,
                uid + ' must be the accepted label-free new input')
        bound(request['source_clock_ref'])
        # No tensor deserialization, processor, or repeated pixel QA is performed.
        bound(request['prefix_ref'])
        start, end = (exact(request['plan'][key]) for key in ('window_start_exact', 'window_end_exact'))
        require(0 <= start < end, uid + ' invalid exact excerpt domain')
        requests[uid] = dict(request=request, request_ref=reference, start=start, end=end)
    require({item['request']['sid'] for item in requests.values()} == set(SIDS), 'Exactly original V00..V07 sources')
    return prepared, requests


def load_sources(manifest, requests):
    adoption = read(bound(manifest['baseline_human_adoption_ref']))
    sources = [source for source in adoption['sources'] if source['group'] == 'check']
    require(len(sources) == 8 and {source['sid'] for source in sources} == set(SIDS),
            'Bound original all8 check source registration required')
    result = {}
    for source in sources:
        sid = source['sid']
        require(sid not in result, 'Duplicate baseline/human source')
        clock = read(bound(source['clock_ref']))
        points = [exact(value) for value in clock['normalized_exact_pts']]
        end = exact(clock['physical_end_exact'])
        require(points and points[0] == 0 and all(a < b for a, b in zip(points, points[1:]))
                and points[-1] < end, sid + ' must have complete ordered zero-origin native PTS')
        require(clock.get('original_zero_origin_verified') is True,
                sid + ' native clock original zero origin unverified')
        members = [item for item in requests.values() if item['request']['sid'] == sid]
        for item in members:
            request = item['request']
            request_clock = read(bound(request['source_clock_ref']))
            # Adopted newer clock refs may add geometry. Native identity must be exact.
            require(request_clock['source_sha256'] == clock['source_sha256'] == request['source_sha256']
                    and request_clock['normalized_exact_pts'] == clock['normalized_exact_pts']
                    and exact(request_clock['physical_end_exact']) == end,
                    sid + ' request/reference source native identity mismatch')
            require(item['end'] <= end, sid + ' excerpt exceeds actual native source end')
            videos = request['plan']['videos']
            require(len(videos) == 2 and [video['role'] for video in videos] == ['Overview', 'Excerpt'],
                    sid + ' requires original dual-view request')
            for video in videos:
                require(video['owner']['source_id'] == sid
                        and video['owner']['source_sha256'] == clock['source_sha256'], sid + ' visual source ownership')
        coverage = native_interval_mask(points, [(item['start'], item['end']) for item in members])
        require(bool(coverage.all()), sid + ' original windows do not cover full native source; no implicit missing-as-empty')
        result[sid] = dict(source=source, clock=clock, points=points, end=end,
                           windows=len(members), window_coverage_native_frames=int(coverage.sum()))
    return result


def load_outputs(manifest, requests, sources):
    require(set(manifest['role_output_refs']) == set(ROLES)
            and set(manifest['role_completion_refs']) == set(ROLES)
            and set(manifest['role_resource_refs']) == set(ROLES)
            and set(manifest['role_output_QA_refs']) == set(ROLES), 'Exactly INIT_TIME and TRAINED roles')
    parsed, completions = {}, {}
    for role in ROLES:
        references = manifest['role_output_refs'][role]
        require(isinstance(references, list) and len(references) == WINDOWS, role + ' must contain43 real outputs')
        require(len({reference_key(item) for item in references}) == WINDOWS, role + ' duplicate output file')
        weights_ref = manifest['initial_TIME_ref' if role == 'INIT_TIME' else 'final_adapter_ref']
        completions[role] = verify_completion(manifest['role_completion_refs'][role], role, references, weights_ref)
        verify_role_admission(manifest, role, references)
        rows = {}
        for reference in references:
            output = read(bound(reference))
            uid, sid = output['uid'], output['sid']
            require(uid in requests and uid not in rows and output.get('model_role') == role,
                    role + ' wrong/duplicate uid or output role')
            item = requests[uid]
            require(sid == item['request']['sid'] and same_ref(output['request_ref'], item['request_ref']),
                    role + '/' + uid + ' is not the identical matched input')
            require(same_ref(output['model_weights_ref'], weights_ref),
                    role + '/' + uid + ' is not the fixed role model weights')
            bound(output['request_ref'])
            require(isinstance(output.get('raw_text'), str), role + '/' + uid + ' missing real raw text')
            for key in ('failure', 'error'):
                require(not output.get(key), role + '/' + uid + ' recorded model failure')
            require(isinstance(output.get('generated_ids'), list) and output['generated_ids']
                    and all(type(token) is int and token >= 0 for token in output['generated_ids']),
                    role + '/' + uid + ' invalid generated token record')
            try:
                local = parse_summary(output['raw_text'], item['end'] - item['start'])
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(role + '/' + uid + ' invalid raw summary: ' + str(exc)) from exc
            absolute = [(item['start'] + start, item['start'] + end) for start, end in local]
            require(all(0 <= start < end <= sources[sid]['end'] for start, end in absolute),
                    role + '/' + uid + ' invalid absolute source interval; no clipping')
            rows[uid] = dict(sid=sid, absolute=absolute, output_ref=reference,
                             empty=(len(local) == 0), intervals=len(local))
        require(set(rows) == set(requests), role + ' missing expected dev output')
        parsed[role] = rows
    require(not ({reference_key(item) for item in manifest['role_output_refs']['INIT_TIME']}
                 & {reference_key(item) for item in manifest['role_output_refs']['TRAINED']}),
            'Roles must have distinct real output records')
    return parsed, completions


def macro(rows, name):
    return dict(**{key: float(np.mean([row['metrics'][name][key] for row in rows]))
                   for key in ('precision', 'recall', 'f1', 'native_frame_coverage')},
                sources=len(rows), empty_prediction_sources=sum(row['metrics'][name]['prediction_empty'] for row in rows),
                selected_native_frames=sum(row['metrics'][name]['selected_native_frames'] for row in rows))


def evaluate(root, manifest_path):
    require(root == ROOT, 'Only the independently registered Linux root is admitted')
    manifest_path = Path(manifest_path).resolve(strict=True)
    require(manifest_path.is_relative_to(root) and manifest_path.is_file(), 'Generation manifest must be in the new root')
    output_dir = root / 'evaluation_10'
    output_dir.mkdir(exist_ok=False)
    manifest_ref = ref(manifest_path)
    try:
        manifest = read(manifest_path)
        # These immutable refs establish fixed final-epoch model/checkpoint selection.
        bound(manifest['initial_TIME_ref'])
        bound(manifest['final_adapter_ref'])
        bound(manifest['frozen_selection_ref'])
        prepared, requests = load_requests(manifest)
        sources = load_sources(manifest, requests)
        parsed, completions = load_outputs(manifest, requests, sources)
        # No baseline/label NPZ is opened before all86 raw outputs have passed.
        rows = []
        for sid in SIDS:
            adopted = sources[sid]
            source, points = adopted['source'], adopted['points']
            with np.load(bound(source['data_ref']), allow_pickle=False) as data:
                baseline, labels = data['baseline'], data['labels']
                groups, scores = data['groups'], data['semantic_score']
            require(baseline.dtype == labels.dtype == np.bool_ and baseline.shape == (len(points),)
                    and labels.ndim == 2 and labels.shape[0] == len(points) and labels.shape[1] > 0,
                    sid + ' full baseline/all-human native domain mismatch')
            require(groups.shape == (len(points),) and groups.dtype.kind in 'iu', sid + ' native semantic group shape')
            bins = np.asarray([int(point * 2) for point in points], dtype=np.int64)
            _, compressed = np.unique(bins, return_inverse=True)
            require(np.array_equal(groups, compressed), sid + ' original semantic/native2Hz group mapping changed')
            masks = dict(BASELINE_40_47=baseline)
            window_results = {}
            for role in ROLES:
                windows = [row for row in parsed[role].values() if row['sid'] == sid]
                intervals = [interval for row in windows for interval in row['absolute']]
                masks[role] = native_interval_mask(points, intervals)
                window_results[role] = dict(windows=len(windows), empty_windows=sum(row['empty'] for row in windows),
                                            nonempty_windows=sum(not row['empty'] for row in windows),
                                            generated_intervals=sum(row['intervals'] for row in windows))
            masks['MATCHED_SEMANTIC'] = matched_semantic(groups, scores, int(masks['TRAINED'].sum()))
            metrics = {name: metric(mask, labels) for name, mask in masks.items()}
            comparisons = {}
            for name, actual, control in (
                    ('TRAINED_vs_INIT_TIME', 'TRAINED', 'INIT_TIME'),
                    ('TRAINED_vs_BASELINE_40_47', 'TRAINED', 'BASELINE_40_47'),
                    ('INIT_TIME_vs_BASELINE_40_47', 'INIT_TIME', 'BASELINE_40_47'),
                    ('TRAINED_vs_MATCHED_SEMANTIC', 'TRAINED', 'MATCHED_SEMANTIC')):
                comparisons[name] = comparison(metrics[actual], metrics[control], masks[actual], masks[control])
            row = dict(sid=sid, name=source['name'], native_frames=len(points), reviewers=labels.shape[1],
                       source_clock_ref=source['clock_ref'], baseline_human_data_ref=source['data_ref'],
                       source_sha256=adopted['clock']['source_sha256'], physical_end_exact=str(adopted['end']),
                       original_window_count=adopted['windows'], window_results=window_results,
                       window_coverage_native_frames=adopted['window_coverage_native_frames'],
                       metrics=metrics, comparisons=comparisons, invalid_outputs=0,
                       native_masks_saved=False, spatial_contribution='UNKNOWN_NO_SPATIAL_LABELS')
            save(output_dir / (sid + '.json'), row)
            rows.append(row)
        names = ('BASELINE_40_47', 'INIT_TIME', 'TRAINED', 'MATCHED_SEMANTIC')
        macros = {name: macro(rows, name) for name in names}
        comparisons = {}
        for name, actual, control in (
                ('TRAINED_vs_INIT_TIME', 'TRAINED', 'INIT_TIME'),
                ('TRAINED_vs_BASELINE_40_47', 'TRAINED', 'BASELINE_40_47'),
                ('INIT_TIME_vs_BASELINE_40_47', 'INIT_TIME', 'BASELINE_40_47'),
                ('TRAINED_vs_MATCHED_SEMANTIC', 'TRAINED', 'MATCHED_SEMANTIC')):
            deltas = [row['comparisons'][name]['delta']['f1'] for row in rows]
            comparisons[name] = dict(
                macro_delta={key: macros[actual][key] - macros[control][key]
                             for key in ('precision', 'recall', 'f1', 'native_frame_coverage')},
                improved_sources=sum(value > 0 for value in deltas), decreased_sources=sum(value < 0 for value in deltas),
                identical_f1_sources=sum(value == 0 for value in deltas), worst_source_delta_f1=min(deltas),
                added_native_frames=sum(row['comparisons'][name]['added_native_frames'] for row in rows),
                removed_native_frames=sum(row['comparisons'][name]['removed_native_frames'] for row in rows))
        result = dict(schema='SOURCE_SUMMARY_MATCHED_DEV8_EVALUATION_V1',
                      status='COMPLETE_CPU_EVALUATION_NOT_SCIENTIFIC_PROMOTION',
                      utc=datetime.now(timezone.utc).isoformat(), generation_manifest_ref=manifest_ref,
                      dev_prepared_ref=manifest['dev_prepared_ref'],
                      baseline_human_adoption_ref=manifest['baseline_human_adoption_ref'],
                      role_completion_refs=manifest['role_completion_refs'],
                      role_resource_refs=manifest['role_resource_refs'], role_output_QA_refs=manifest['role_output_QA_refs'],
                      initial_TIME_ref=manifest['initial_TIME_ref'],
                      final_adapter_ref=manifest['final_adapter_ref'], frozen_selection_ref=manifest['frozen_selection_ref'],
                      exact_raw_parser_ref=ref(Path(__file__).with_name('summary_output.py')),
                      evaluation_code_ref=ref(Path(__file__)),
                      sources=rows, macro=macros, comparisons=comparisons,
                      raw_output_counts={role: len(parsed[role]) for role in ROLES}, invalid_output_count=0,
                      absent_or_failed_output_to_empty=False,
                      aggregation='Equal original raters within source, then equal8 source weights; one common native mask per source',
                      metric_zero_denominator='P/R/F1 zero when denominator zero, preserving source_clear metric; empty FP/FN explicit',
                      local_to_source='Exact Fraction window origin; native PTS half-open membership; overlapping windows union',
                      matched_semantic_policy='Original semantic_score[groups], score descending/ordinal ascending, exactly TRAINED actual K per source',
                      matched_semantic_labels_used_for_selection=False, parameter_or_threshold_scan=False,
                      reference_semantics='Original human whole-source summary choices, unselected is not ordinary/no-highlight',
                      historical_exposure=True, blind_test=False, official_joint_score=None,
                      spatial_contribution='UNKNOWN_NO_SPATIAL_LABELS', masks_or_submittable_oracle_saved=False,
                      new_model_calls=0, new_fit=0, new_media_decode=0, repeated_pixel_or_output_QA=False,
                      production_admitted=False, automatic_promotion=False)
        save(output_dir / 'result.json', result)
        print(json.dumps(dict(status=result['status'], macro=macros, comparisons=comparisons), allow_nan=False))
    except BaseException as exc:
        save(output_dir / 'failure.json', dict(status='STOP_EVALUATION_INVALID_OR_INCOMPLETE',
             utc=datetime.now(timezone.utc).isoformat(), generation_manifest_ref=manifest_ref,
             error=repr(exc), traceback=traceback.format_exc(), failed_output_to_empty=False,
             production_admitted=False, automatic_retry=False))
        raise


def self_check():
    """Pure synthetic contract checks only; no files, labels, models or old QA."""
    points = list(map(Fraction, ('0', '1/4', '1/2', '3/4', '1', '5/4')))
    intervals = [(Fraction(1, 4), Fraction(3, 4)), (Fraction(1, 2), Fraction(1))]
    mask = native_interval_mask(points, intervals)
    require(mask.tolist() == [False, True, True, True, False, False], 'Half-open overlapping native union')
    start = Fraction(1, 4)
    local = parse_summary('{"segments":[[0.25,0.75]]}', Fraction(1))
    absolute = [(start + a, start + b) for a, b in local]
    require(native_interval_mask(points, absolute).tolist() == [False, False, True, True, False, False],
            'Exact clip-local origin addition')
    groups = np.asarray([0, 0, 1, 1, 2, 2], dtype=np.int64)
    scores = np.asarray([.5, .5, .1])
    require(matched_semantic(groups, scores, 3).tolist() == [True, True, True, False, False, False],
            'Matched K and ordinal ties')
    require(not matched_semantic(groups, scores, 0).any() and matched_semantic(groups, scores, 6).all(), 'Legal empty/full K')
    labels = np.asarray([[True, False], [False, True], [False, False]], dtype=bool)
    empty = metric(np.zeros(3, dtype=bool), labels)
    require(empty['f1'] == 0 and empty['empty_prediction_false_negatives_by_reviewer'] == [1, 1]
            and all(row['false_positive'] == 0 for row in empty['reviewers']), 'Empty prediction remains explicit FN')
    common = metric(np.asarray([True, False, False]), labels)
    require(common['precision'] == .5 and common['recall'] == .5 and common['f1'] == .5,
            'Same prediction for contradictory raters')
    for text in ('{"segments":[],"segments":[]}', '{"segments":[[0,NaN]]}', '{"segments":[[0,1.1]]}'):
        try:
            parse_summary(text, Fraction(1))
        except (ValueError, TypeError):
            continue
        raise ValueError('Synthetic invalid output was not rejected')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--generation-manifest')
    parser.add_argument('--self-check-only', action='store_true')
    args = parser.parse_args()
    if args.self_check_only:
        require(args.generation_manifest is None, 'Synthetic check must not read generation manifest')
        self_check()
        print('PASS_SYNTHETIC_MASK_TIME_METRIC_AND_MATCHED_K_ONLY')
    else:
        require(args.generation_manifest is not None, '--generation-manifest is required')
        evaluate(Path(args.root).resolve(strict=True), args.generation_manifest)
