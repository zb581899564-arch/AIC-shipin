"""One descriptive audio/author-summary association audit on accepted caches.

No decoder, model, optimizer, threshold search, labels changed, or output masks.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import numpy as np

W = Path('/home/inspur/aic_video_work')
R = W/'bottleneck_24h_20261019_v1'


def read(path):
    return json.loads(Path(path).read_text())


def ref(path):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def bound(value):
    path = Path(value['path']).resolve(strict=True)
    assert path.is_relative_to(W) and path.is_file() and ref(path)['sha256'] == value['sha256']
    return path


def rater_auc(values, labels):
    """Rank association, ties half; original not-selected != ordinary negative."""
    assert values.ndim == 1 and labels.dtype == bool and labels.shape[0] == len(values)
    if len(values) == 0:
        return None, 0
    _, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    ranks = (np.cumsum(counts)-counts+(counts+1)/2)[inverse]
    results = []
    for chosen in labels.T:
        positive = int(chosen.sum()); other = len(chosen)-positive
        if positive and other:
            results.append(float((ranks[chosen].sum()-positive*(positive+1)/2)/(positive*other)))
    return (float(np.mean(results)) if results else None), len(results)


def in_coverage(points, intervals):
    starts = [start for start, _ in intervals]
    output = []
    for point in points:
        index = bisect_right(starts, point)-1
        output.append(index >= 0 and point < intervals[index][1])
    return np.asarray(output, bool)


def main():
    assert os.uname().nodename == 'inspur-NP5570M5'
    output = R/'audio_hypothesis_result_22.json'
    assert not output.exists(), 'Do not repeat a successful diagnostic'
    reg = read(R/'audio_hypothesis_registration_22.json')
    assert bound(reg['code_ref']) == Path(__file__).resolve()
    catalog = read(bound(reg['source_registration_ref']))
    adoption = read(bound(reg['accepted_audio_completion_ref']))
    assert adoption['status'] == 'PASS33_ALL_FIRST_AUDIO_NATIVE_INPUTS'
    accepted = {read(bound(value))['sid']: value for value in adoption['sources']}
    assert len(accepted) == len(catalog['sources']) == 33
    rows = []
    for source in catalog['sources']:
        sid = source['sid']; receipt = read(bound(accepted[sid]))
        manifest = read(bound(receipt['manifest_ref']))
        assert manifest['status'] == 'COMPLETE'
        with np.load(bound(manifest['features_ref']), allow_pickle=False) as data:
            raw, valid = data['raw'], data['valid']
        clock = read(bound(source['clock_ref']))
        points = list(map(F, clock['normalized_exact_pts']))
        with np.load(bound(source['data_ref']), allow_pickle=False) as data:
            labels = data['labels']
        assert labels.dtype == bool and labels.ndim == 2 and len(labels) == len(points)
        assert clock['source_sha256'] == manifest['media_ref']['sha256']
        assert F(clock['physical_end_exact']) == F(manifest['physical_video_end_exact'])
        intervals = [(F(a), F(b)) for a, b in manifest['observed_coverage_exact']]
        observed = in_coverage(points, intervals)
        indices = np.asarray([int(point*4) for point in points], np.int64)
        assert len(indices) and indices.max() < len(raw)
        features = []
        for column, name in enumerate(manifest['feature_names']):
            eligible = observed & valid[indices, column]
            auc, raters = rater_auc(raw[indices[eligible], column], labels[eligible])
            features.append(dict(name=name, native_frames_observed=int(eligible.sum()),
                valid_DSP_bins=int(valid[:, column].sum()), reviewer_mean_rank_AUC=auc,
                reviewers_with_both_selected_and_not_selected=raters,
                selected_definition='Original author reviewer summary selection; unselected is not ordinary'))
        rows.append(dict(sid=sid, group=source['group'], name=source['name'],
            accepted_audio_receipt_ref=accepted[sid], native_frames=len(points),
            observed_native_frames=int(observed.sum()), original_reviewers=labels.shape[1],
            no_audio=manifest['no_audio'], features=features,
            original_human_data_ref=source['data_ref'], clock_ref=source['clock_ref']))
    original = read(bound(reg['original_target_acceptance_ref']))
    targets = [json.loads(line) for line in bound(original['candidate_targets_ref']).read_text().splitlines() if line.strip()]
    windows = defaultdict(list)
    for target in targets:
        windows[target['uid']].append(target)
    empty = [target for target in targets if target['segments_count'] == 0]
    mixed_empty = sum(any(item['segments_count'] > 0 for item in windows[target['uid']]) for target in empty)
    label_semantics = dict(targets=len(targets), windows=len(windows),
        empty_reviewer_window_targets=len(empty),
        empty_targets_with_other_reviewer_selecting_same_window=mixed_empty,
        windows_all_reviewers_unselected=sum(all(item['segments_count'] == 0 for item in items) for items in windows.values()),
        adopted_original_native_roundtrip_acceptance=reg['original_target_acceptance_ref'],
        original_frame_mapping_QA_repeated=False, original_labels_changed=False,
        interpretation='Empty means one reviewer did not choose this excerpt for whole-source summary; not a no-highlight truth claim')
    groups = {}
    for group in ('train', 'check'):
        items = [row for row in rows if row['group'] == group]
        summary = []
        for column in range(3):
            values = [row['features'][column]['reviewer_mean_rank_AUC'] for row in items]
            actual = [value for value in values if value is not None]
            summary.append(dict(name=items[0]['features'][column]['name'],
                eligible_sources=len(actual), total_sources=len(items),
                source_equal_mean_AUC=float(np.mean(actual)) if actual else None,
                source_median_AUC=float(np.median(actual)) if actual else None,
                above_half=sum(value > .5 for value in actual), below_half=sum(value < .5 for value in actual),
                no_threshold_fit_or_feature_selection=True))
        groups[group] = summary
    result = dict(status='COMPLETE_AUDIO_CACHE_HUMAN_SUMMARY_ASSOCIATION_NO_NEW_MODEL_OR_SELECTION',
        utc=datetime.now(timezone.utc).isoformat(), registration_ref=ref(R/'audio_hypothesis_registration_22.json'),
        label_semantics=label_semantics, summary_by_original_group=groups, sources=rows,
        all_sources_historically_exposed=True, new_blind_test=False, inference_causality=False,
        no_statistical_independence_claim=True, spatial_or_official_joint_score=None,
        source_audio_semantics_not_available=True,
        invalid_change_features_not_filled_or_interpreted_as_silence=True,
        new_media_decode=0, new_model_calls=0, new_fit=0, output_masks_or_packages=0,
        formal_test_contents_or_labels_used=False, production_admitted=False,
        active_training_protocol_changed=False)
    with output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())
    print(json.dumps(dict(status=result['status'], label_semantics=label_semantics, summary=groups), ensure_ascii=False))


if __name__ == '__main__':
    main()
