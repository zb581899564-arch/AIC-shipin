"""Unadmitted query-saliency index ranges using existing relative-PTS bounds."""
import hashlib
import json
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

WORK = Path('/home/inspur/aic_video_work')
ROOT = WORK / 'diagnostic_score_goal_20261018_v1'
DATA = ROOT / 'qvh_original_human_146'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
R7 = WORK / 'round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z'
INPUTS = {
    'human_train': (DATA / 'highlight_train_release.jsonl', 'fd28404187468f57cf99242be2963127dc9b4aef26c7de3cb9469569801f2625'),
    'data_license': (DATA / 'LICENSE', '9e502ba75fd0fd30cea5497b438a4bc12f07f02bc932a7a6041fd6a18b8f46a0'),
    'registry': (RUN / 'temporal_sft8b_v1/inputs_01/r7_train_registry.json', '71552f64ccdb125ca11a451baf5b8a22491d51d73db1a42e0ce1a545262d1cd4'),
    'old_train': (R7 / 'inputs/train_temporal.jsonl', 'ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf'),
}


def ceiling(value):
    return -((-value.numerator) // value.denominator)


def certified_range(start, end, fps_num, fps_den, residual, n_frames):
    """All retained i satisfy [i/fps-e,i/fps+e] contained in [start,end)."""
    if not (0 <= start < end and fps_num > 0 and fps_den > 0 and n_frames > 0
            and math.isfinite(residual) and residual >= 0):
        raise ValueError('invalid clock or interval')
    # Published ffprobe timestamps have finite decimal precision. This is an
    # arithmetic guard, not a policy/quality threshold or a measured new PTS.
    epsilon = Fraction(str(residual)) + Fraction(1, 1_000_000)
    fps = Fraction(fps_num, fps_den)
    lo = ceiling((Fraction(str(start)) + epsilon) * fps)
    hi = ceiling((Fraction(str(end)) - epsilon) * fps)
    if lo < 0 or hi > n_frames or lo >= hi:
        return None
    return lo, hi


def query_clip_records(parent, historical, row):
    if historical['sample_id'] != parent['parent_sample_id']:
        raise ValueError('parent mismatch')
    if historical['source_path'] != parent['source_path']:
        raise ValueError('source path mismatch')
    if historical['decoded_source_frames'] != parent['n_frames']:
        raise ValueError('frame count mismatch')
    if historical['pts_audit_status'] != 'PASS':
        raise ValueError('missing old relative-PTS audit')
    if row['vid'] != Path(parent['source_path']).stem:
        raise ValueError('author clip ID mismatch')
    results = []
    skipped = Counter()
    for clipid, scores in zip(row['relevant_clip_ids'], row['saliency_scores']):
        if type(clipid) is not int or len(scores) != 3 or any(type(x) is not int or not 0 <= x <= 4 for x in scores):
            raise ValueError('invalid original rating')
        a, b = 2 * clipid, 2 * (clipid + 1)
        # Never trim a source annotation or extend a registered old window.
        if a < 0 or b > row['duration']:
            skipped['clip_not_wholly_inside_author_duration'] += 1
            continue
        windows = [w['window_id'] for w in parent['registered_windows']
                   if w['clip_start_sec'] <= a < b <= w['clip_end_sec']]
        if not windows:
            skipped['clip_not_wholly_inside_existing_window'] += 1
            continue
        frame_range = certified_range(a, b, parent['fps_num'], parent['fps_den'],
                                      historical['pts_max_residual_sec'], parent['n_frames'])
        if frame_range is None:
            skipped['no_certified_native_indices'] += 1
            continue
        results.append({
            'source_sha256': parent['source_sha256'], 'parent_sample_id': parent['parent_sample_id'],
            'source_path': parent['source_path'], 'author_vid': row['vid'],
            'qid': row['qid'], 'query': row['query'], 'clip_id': clipid,
            'original_local_interval_seconds': [a, b], 'original_rater_scores': scores,
            'native_frame_range_half_open': list(frame_range),
            'old_relative_pts_max_residual_seconds': historical['pts_max_residual_sec'],
            'arithmetic_guard_seconds': 0.000001, 'existing_window_ids': sorted(windows),
            'annotation_scope': 'QUERY_CONDITIONAL_RELEVANT_CLIP_SALIENCY',
            'native_pts_absolute_values_present': False,
            'source_identity_scope': 'AUTHOR_VID_AND_CURRENT_FROZEN_SOURCE_SHA_JOIN_ONLY',
            'training_admitted': False,
        })
    return results, skipped


def main():
    out = DATA / 'query_saliency_bridge'
    out.mkdir(exist_ok=False)
    bound = {}
    hashes = {}
    for key, (path, expected) in INPUTS.items():
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected:
            raise ValueError('frozen metadata changed: ' + key)
        bound[key] = raw
        hashes[key] = digest
    parents = json.loads(bound['registry'])['records']
    old = {x['sample_id']: x for x in map(json.loads, bound['old_train'].decode().splitlines())}
    if len(parents) != 704 or len(old) != 704 or set(old) != {p['parent_sample_id'] for p in parents}:
        raise ValueError('wrong frozen training set')
    by_vid = {}
    for row in map(json.loads, bound['human_train'].decode().splitlines()):
        by_vid.setdefault(row['vid'], []).append(row)
    records, skipped, seen = [], Counter(), set()
    for parent in parents:
        for row in by_vid.get(Path(parent['source_path']).stem, []):
            candidates, counts = query_clip_records(parent, old[parent['parent_sample_id']], row)
            skipped.update(counts)
            for candidate in candidates:
                key = (candidate['source_sha256'], candidate['qid'], candidate['clip_id'])
                if key in seen:
                    raise ValueError('duplicate source/query/clip target')
                seen.add(key)
                records.append(candidate)
    grades = Counter(x for record in records for x in record['original_rater_scores'])
    per_query = {}
    for record in records:
        per_query.setdefault(record['qid'], set()).add(sum(record['original_rater_scores']))
    with (out / 'query_saliency_native_index_candidates.jsonl').open('x') as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n')
    result = {
        'status': 'COMPLETE_UNADMITTED_QUERY_SALIENCY_BOUND_MAPPING_CANDIDATES',
        'input_sha256': hashes, 'query_clip_records': len(records),
        'parents_with_candidates': len({x['parent_sample_id'] for x in records}),
        'queries_with_candidates': len(per_query),
        'queries_with_at_least_two_different_rater_sum_targets': sum(len(x) >= 2 for x in per_query.values()),
        'original_rating_histogram': dict(sorted(grades.items())), 'skipped_original_clips': dict(skipped),
        'overlap_duplicate_targets': 0, 'unknown_regions_converted_to_negative': 0,
        'annotation_task_or_scores_changed': False, 'labels_stretched_or_truncated': False,
        'proof_scope': 'Index ranges follow old measured relative-PTS error bounds, conditional on author vid identity; no exact absolute PTS or original-author media-byte identity is asserted.',
        'unconditional_highlight_truth': False, 'source_video_rights': 'UNKNOWN',
        'new_media_reads': 0, 'new_decode_or_processor_calls': 0,
        'new_model_calls': 0, 'new_training_updates': 0,
        'training_admitted': False, 'production_admitted': False,
    }
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
