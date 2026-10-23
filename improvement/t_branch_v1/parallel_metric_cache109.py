"""Adopt accepted native-mask scores; independently check only first missing arithmetic."""
import numpy as np

from event_full79 import independent_set_metrics
from stage_metric_cache96 import accepted_metrics, mask_key, metric
from t_io import ROOT, check, identity, read


def accepted(sources):
    cache = accepted_metrics(sources)
    independent = set()
    for stage in ['event_full78', 'summary_full93']:
        binding = read(ROOT / stage / 'frozen_all_masks_before_labels.json')
        for sid, arms in binding.items():
            for row in arms.values():
                with np.load(check(row['native']), allow_pickle=False) as data:
                    independent.add((sid,) + mask_key(data['full40_48']))
    old = read(ROOT / 'development_remaining55/frozen_all_predictions_before_labels.json')
    for sid, arms in old.items():
        for row in arms.values():
            with np.load(check(row['native']), allow_pickle=False) as data:
                independent.add((sid,) + mask_key(data['full40_47']))
    #96 saved first metrics already carry an exact native SHA; no mask or score rerun.
    prior = ROOT / 'summary_diagnosis96/completion.json'
    for row in read(prior)['first_new_stage_metrics']:
        key = (row['source'],) + tuple(row['native_mask_key'])
        if key not in cache:
            cache[key] = dict(score=row['score'], adopted_metric=identity(prior))
    return cache, independent


def score(mask, source, cache, independent_keys, first_scores, first_independent):
    result = metric(mask, source, cache, first_scores)
    key = (source.sid,) + mask_key(mask)
    if key not in independent_keys:
        other = independent_set_metrics(mask, source.reviews, len(source.reviews))
        if abs(other - result['score']['mean_f1']) > 1e-12:
            raise ValueError('First independent full-source/all-reviewer native F1 differs')
        independent_keys.add(key)
        first_independent.append(dict(source=source.sid, native_mask_key=list(key[1:]),
                                      all_original_reviewers=len(source.reviews), mean_f1=other))
    return result
