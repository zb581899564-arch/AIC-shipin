"""Reuse already-computed source/mask metrics; score only new stage masks."""
import hashlib

import numpy as np

from development_diagnosis57 import native_masks
from preference_reward import summary_agreement
from t_io import ROOT, check, identity, read

FIELDS = ('mean_f1', 'mean_precision', 'mean_recall')


def mask_key(mask):
    if mask.ndim != 1 or mask.dtype != bool:
        raise ValueError('Complete original native boolean mask required')
    return len(mask), hashlib.sha256(mask.tobytes()).hexdigest()


def add(cache, sid, mask, score, proof):
    key = (sid,) + mask_key(mask)
    values = {k: float(score[k]) for k in FIELDS}
    if key in cache and any(abs(values[k] - cache[key]['score'][k]) > 1e-12 for k in FIELDS):
        raise ValueError('Two accepted same-mask/all-reviewer metrics disagree')
    cache[key] = dict(score=values, adopted_metric=proof)


def accepted_metrics(sources):
    cache = {}
    old57 = ROOT / 'development_diagnosis57/completion.json'
    values = read(old57); coarse = read(ROOT / 'development51/coarse_GPU_completion.json')['outputs']
    binding = read(ROOT / 'development_remaining55/frozen_all_predictions_before_labels.json')
    for sid, source in sources.items():
        masks = native_masks(source, coarse, binding)
        for arm, stages in masks.items():
            for stage, mask in stages.items():
                add(cache, sid, mask, values['per_source'][sid]['scores'][arm][stage], identity(old57))
    old72 = ROOT / 'event_selection72/CPU_completion.json'; values = read(old72)
    for sid, ref in read(check(values['frozen_masks'])).items():
        with np.load(check(ref), allow_pickle=False) as data:
            for arm in data.files:
                add(cache, sid, data[arm], values['coarse_only_metrics'][sid][arm], identity(old72))
    for name in ['event_full78', 'summary_full93']:
        review = ROOT / name / 'review.json'; values = read(review)
        for sid, arms in read(ROOT / name / 'frozen_all_masks_before_labels.json').items():
            for arm, row in arms.items():
                with np.load(check(row['native']), allow_pickle=False) as data:
                    add(cache, sid, data['full40_48'], values['metrics'][sid][arm], identity(review))
    return cache


def metric(mask, source, cache, first):
    key = (source.sid,) + mask_key(mask)
    if key not in cache:
        score = summary_agreement(mask, source.reviews, len(source.reviews))
        cache[key] = dict(score={k: score[k] for k in FIELDS},
                          first_stage_metric=True, all_original_reviewers=len(source.reviews))
        first.append(dict(source=source.sid, native_mask_key=list(key[1:]), **cache[key]))
    return dict(cache[key], selected_native_frames=int(mask.sum()), source_native_frames=len(mask))
