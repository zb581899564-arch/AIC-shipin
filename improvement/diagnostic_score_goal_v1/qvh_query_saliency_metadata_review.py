"""First saved-artifact review; never a current native-clock or model QA."""
import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work/diagnostic_score_goal_20261018_v1')
DATA = ROOT / 'qvh_original_human_146'
OUT = DATA / 'query_saliency_bridge'
REGISTRY = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1/inputs_01/r7_train_registry.json')
HUMAN = DATA / 'highlight_train_release.jsonl'
OLD = Path('/home/inspur/aic_video_work/round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z/inputs/train_temporal.jsonl')


def load_bound(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('artifact changed: ' + str(path))
    return data


def main():
    raw = load_bound(OUT / 'query_saliency_native_index_candidates.jsonl',
                     'ddb047a132c6585c9e17ae4c175c93107b504bf5cdb6dc3ddc35e4244e6579d6')
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    parents = json.loads(load_bound(REGISTRY, '71552f64ccdb125ca11a451baf5b8a22491d51d73db1a42e0ce1a545262d1cd4'))['records']
    by_parent = {x['parent_sample_id']: x for x in parents}
    old_rows = [json.loads(line) for line in load_bound(OLD, 'ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf').decode().splitlines()]
    old_by_parent = {x['sample_id']: x for x in old_rows}
    author = [json.loads(line) for line in load_bound(HUMAN, 'fd28404187468f57cf99242be2963127dc9b4aef26c7de3cb9469569801f2625').decode().splitlines()]
    by_qid = {x['qid']: x for x in author}
    limits = json.loads(load_bound(OUT / 'scope_limits.json', '7c51e10effcc2ab06bd5ce36e06cb384430b69a15dd182a029f1b0f212190da3'))
    assert limits['training_admitted'] is False
    assert limits['current_exact_native_PTS_mapping_pass'] is False
    keys, used_sources = set(), set()
    ratings = Counter()
    grades_per_query = defaultdict(set)
    for row in rows:
        parent = by_parent[row['parent_sample_id']]
        historical = old_by_parent[row['parent_sample_id']]
        assert row['old_relative_pts_max_residual_seconds'] == historical['pts_max_residual_sec']
        assert historical['pts_audit_status'] == 'PASS'
        original = by_qid[row['qid']]
        assert original['vid'] == Path(parent['source_path']).stem == row['author_vid']
        assert row['source_path'] == parent['source_path']
        assert row['source_sha256'] == parent['source_sha256']
        assert row['query'] == original['query']
        indexes = [i for i, x in enumerate(original['relevant_clip_ids']) if x == row['clip_id']]
        assert len(indexes) == 1
        assert row['original_rater_scores'] == original['saliency_scores'][indexes[0]]
        assert row['original_local_interval_seconds'] == [2 * row['clip_id'], 2 * (row['clip_id'] + 1)]
        a, b = map(Fraction, row['original_local_interval_seconds'])
        assert 0 <= a < b <= original['duration']
        expected_windows = sorted(w['window_id'] for w in parent['registered_windows']
                                  if Fraction(str(w['clip_start_sec'])) <= a < b <= Fraction(str(w['clip_end_sec'])))
        assert expected_windows and row['existing_window_ids'] == expected_windows
        lo, hi = row['native_frame_range_half_open']
        assert type(lo) is int and type(hi) is int and 0 <= lo < hi <= parent['n_frames']
        epsilon = Fraction(str(row['old_relative_pts_max_residual_seconds'])) + Fraction(1, 1_000_000)
        interval = Fraction(parent['fps_den'], parent['fps_num'])
        # Monotone endpoints prove containment for every retained integer i.
        assert lo * interval - epsilon >= a
        assert (hi - 1) * interval + epsilon < b
        assert row['training_admitted'] is False
        key = (row['source_sha256'], row['qid'], row['clip_id'])
        assert key not in keys
        keys.add(key)
        used_sources.add(parent['parent_sample_id'])
        ratings.update(row['original_rater_scores'])
        grades_per_query[row['qid']].add(sum(row['original_rater_scores']))
    source_stats = Counter()
    for pid in used_sources:
        parent = by_parent[pid]
        path = Path(parent['source_path'])
        if not path.is_file():
            source_stats['missing'] += 1
            continue
        current = path.stat()
        unchanged = current.st_size == parent['source_bytes'] and current.st_mtime_ns == parent['source_mtime_ns']
        source_stats['size_mtime_unchanged' if unchanged else 'size_or_mtime_changed'] += 1
    result = {
        'status': 'PASS_FIRST_QUERY_BRIDGE_SAVED_METADATA_REVIEW_ONLY',
        'reviewed_records': len(rows), 'source_parents': len(used_sources),
        'queries': len(grades_per_query),
        'queries_with_multiple_rater_sum_targets': sum(len(x) > 1 for x in grades_per_query.values()),
        'original_rating_histogram': dict(sorted(ratings.items())),
        'original_query_ratings_and_intervals_preserved': True,
        'conditional_range_containment_all_records': True,
        'overlap_duplicate_targets': 0, 'current_source_stat_check': dict(source_stats),
        'stat_is_not_new_source_SHA_or_PTS_proof': True,
        'scope_limits_sha256': '7c51e10effcc2ab06bd5ce36e06cb384430b69a15dd182a029f1b0f212190da3',
        'current_native_pts_QA': False, 'current_source_SHA_reread': False,
        'training_admitted': False, 'production_admitted': False,
        'new_media_reads': 0, 'new_model_calls': 0,
    }
    with (OUT / 'first_saved_metadata_review.json').open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
