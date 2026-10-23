"""First stage-wise diagnosis of a rejected105 profile, never candidate selection."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math
import traceback

import numpy as np

from development_data46 import development_sources
from parallel_metric_cache109 import accepted, score
from stage_metric_cache96 import add, mask_key
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'parallel_diagnosis113'
FULL = ROOT / 'parallel_full109'
STAGES = ('coarse', 'D8', 'VERIFY', 'full40_47', 'full40_48')


def accepted_full_metrics(sources):
    cache, independent = accepted(sources)
    review = read(FULL / 'review.json')
    bindings = read(FULL / 'frozen_all_masks_before_labels.json')
    for sid, arms in bindings.items():
        for arm, binding in arms.items():
            with np.load(check(binding['native']), allow_pickle=False) as data:
                mask = data['full40_48'].copy()
            add(cache, sid, mask, review['metrics'][sid][arm]['score'], identity(FULL / 'review.json'))
            independent.add((sid,) + mask_key(mask))
    return cache, independent, bindings


def source_masks(source, arm, outputs, binding):
    coarse = np.zeros(len(source.timeline.points), dtype=bool)
    for case in source.cases:
        actual = read(check(outputs[case.name]))
        coarse |= source.selection(case, actual)
    with np.load(check(binding['native']), allow_pickle=False) as data:
        return dict(coarse=coarse, **{stage: data[stage].copy() for stage in STAGES[1:]})


def main():
    OUT.mkdir()
    terminal = read(FULL / 'completion.json')
    if terminal['state'] != 'STOP_FIXED_PARALLEL105_DEVELOPMENT':
        raise ValueError('Only complete rejected105 profile is admitted for this diagnosis')
    save(OUT / 'registration.json', dict(completed_profile=identity(FULL / 'completion.json'),
        task='First stage decomposition of all four fixed arms; no new action or checkpoint choice',
        no_model_calls_or_training_or_confirmation=True, original_gates_and_STOP_unchanged=True,
        code=identity(ROOT / 'code/parallel_diagnosis113.py')))
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=True)
    arms = read(ROOT / 'code/parallel_protocol105.json')['development_matrix']
    first = read(ROOT / 'parallel_cost107/initial_controls_GPU.json')['outputs']
    final = read(ROOT / 'parallel_remaining108/development_GPU.json')['outputs']
    cache, independent, bindings = accepted_full_metrics(sources)
    primary, independent_first, metrics, changes = [], [], {}, {}
    for sid, source in sources.items():
        masks = {arm: source_masks(source, arm, first[sid] if index == 0 else final[arm][sid],
                                   bindings[sid][arm]) for index, arm in enumerate(arms)}
        metrics[sid] = {arm: {stage: score(mask, source, cache, independent, primary, independent_first)
                             for stage, mask in stages.items()} for arm, stages in masks.items()}
        changes[sid] = {stage: {arm: dict(
            added=int((masks[arms[1]][stage] & ~masks[arm][stage]).sum()),
            removed=int((masks[arm][stage] & ~masks[arms[1]][stage]).sum()),
            delta_F1=metrics[sid][arms[1]][stage]['score']['mean_f1']
                     - metrics[sid][arm][stage]['score']['mean_f1'])
            for arm in (arms[0], arms[2], arms[3])} for stage in STAGES}
    means = {arm: {stage: math.fsum(metrics[sid][arm][stage]['score']['mean_f1']
                                   for sid in sources) / len(sources) for stage in STAGES} for arm in arms}
    save(OUT / 'completion.json', dict(state='FIRST_STOP105_STAGEWISE_CPU_DIAGNOSIS_COMPLETE',
        metrics=metrics, means=means, changes=changes, first_native_metrics=primary,
        first_independent_all_reviewer_F1=independent_first,
        original_full_review=identity(FULL / 'review.json'),
        no_model_calls_or_old_metrics_replayed=True, confirmation_sources_read=0,
        original105_quality_STOP_unchanged=True, no_threshold_prompt_dose_or_production_admission=True,
        human_summary_omissions_semantically_UNKNOWN=True, official_joint_score='UNKNOWN'))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_successes=True))
        raise
