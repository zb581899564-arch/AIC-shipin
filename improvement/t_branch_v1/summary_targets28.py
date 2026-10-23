"""Original whole-video human summaries, all reviewers, no semantic negative labels."""
from fractions import Fraction
import math
import traceback

import numpy as np

from native_sets import NativeTimeline
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'summary_targets28'


def source_targets(row):
    source = row['source']
    clock = read(check(source['clock']))
    timeline = NativeTimeline.from_clock(clock)
    reviews = read(check(source['annotations']))
    if len(reviews) != source['independent_reviewers']:
        raise ValueError('Original all-reviewer denominator differs')
    ids = [str(review['annotator_id']) for review in reviews]
    if len(set(ids)) != len(ids):
        raise ValueError('Repeated original reviewer identity')
    masks, score_rows = [], []
    for review in reviews:
        spans, scores = [], []
        for segment in review['summary_timestamps']:
            score = segment['score']
            if not isinstance(score, (int, float)) or not math.isfinite(score) or score <= 0:
                raise ValueError('Unexpected summary relevance schema; do not silently drop rows')
            spans.append((Fraction(str(segment['start_time'])) / 1000,
                          Fraction(str(segment['end_time'])) / 1000))
            scores.append(score)
        mask = timeline.intervals(spans)
        # Independent native predicate, not another bisect implementation.
        predicate = np.array([any(lo <= point < hi for lo, hi in spans) for point in timeline.points], dtype=bool)
        if not np.array_equal(mask, predicate):
            raise ValueError('Independent original summary-to-native mapping differs')
        masks.append(mask)
        score_rows.append(scores)
    target = OUT / (source['sid'] + '.npz')
    with target.open('xb') as stream:
        np.savez_compressed(stream, summary_selected=np.stack(masks),
                            summary_task_domain=np.ones(clock['native_frames'], dtype=bool))
    save(OUT / (source['sid'] + '.json'), dict(source_id=source['sid'], role=source['role'],
        original_annotations=source['annotations'], original_clock=source['clock'],
        original_scores_preserved=score_rows, all_original_reviewers=ids,
        summary_task='TIMESTAMP_AWARE_WHOLE_VIDEO_SUMMARY_PREFERENCE',
        unselected_semantic_importance='UNKNOWN_NOT_EXPLICIT_ORDINARY',
        scores_not_reinterpreted_as_clip_ID_or_binary_strength=True,
        reference='Every originally selected summary interval, no relevance-threshold selection',
        reward='Whole-source P/R/F1 averaged across every original reviewer',
        ordinary_supervision_created=False, native_frames=clock['native_frames'],
        tensor=identity(target), independent_predicate_mapping_PASS=True,
        labels_never_in_inference=True))
    print('SUMMARY_TARGET28_ACCEPTED', source['sid'], len(ids), clock['native_frames'], flush=True)
    return identity(OUT / (source['sid'] + '.json'))


def main():
    OUT.mkdir()
    plan = read(ROOT / 'pilot_profile21/registration.json')
    save(OUT / 'registration.json', dict(frozen_cohort=identity(ROOT / 'pilot_profile21/registration.json'),
        fitted_sources=2, development_sources=2, new_confirmation_labels_read=False,
        no_NHL_from_unselected_summary_or_relevance_score=True,
        only_original_summary_task_domain=True, no_model_or_quality_metric=True))
    accepted = [source_targets(row) for row in plan['planned']]
    save(OUT / 'completion.json', dict(state='ALL_ORIGINAL_SUMMARY_PREFERENCE_TARGETS_ACCEPTED',
        accepted=accepted, all_raters=True, actual_native_predicate_versus_bisect=True,
        no_dense_semantic_ordinary_labels=True, no_new_confirmation_exposure=True,
        no_prediction_or_training_or_model_call=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
