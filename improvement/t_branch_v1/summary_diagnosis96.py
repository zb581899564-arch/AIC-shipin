"""First saved-mask diagnosis after85 STOP; no new model or candidate selection."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import math
import traceback

import numpy as np

from development_data46 import development_sources
from stage_metric_cache96 import accepted_metrics, metric
from summary_context90 import ARMS
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'summary_diagnosis96'
CONTROL = 'original_native_no_memory'
STAGES = ('coarse', 'D8', 'VERIFY', 'full40_48')


def source_masks(sid, arm):
    native_arm = 'native_no_memory_control' if arm == CONTROL else arm
    native_root = ROOT / ('event_selection72' if arm == CONTROL else 'summary_selection91')
    frozen = read(native_root / 'frozen_coarse_masks_before_labels.json')
    with np.load(check(frozen[sid]), allow_pickle=False) as data:
        coarse = data[native_arm].copy()
    full_root = ROOT / ('event_full78' if arm == CONTROL else 'summary_full93')
    ref = read(full_root / 'frozen_all_masks_before_labels.json')[sid][native_arm]['native']
    with np.load(check(ref), allow_pickle=False) as data:
        return dict(coarse=coarse, **{key: data[key].copy() for key in STAGES[1:]})


def main():
    OUT.mkdir()
    complete = read(ROOT / 'summary_full93/completion.json')
    if complete['state'] != 'STOP_FIXED_CONTENT_SUMMARY85_DEVELOPMENT':
        raise ValueError('Only the completed rejected85 profile is this diagnostic scope')
    save(OUT / 'registration.json', dict(completed_profile=identity(ROOT / 'summary_full93/completion.json'),
        task='First new stage-mask metrics and cross-condition changes; accepted identical-mask metrics adopted',
        original_gates_unchanged=True, no_prompt_threshold_dose_or_candidate_selection=True,
        new_model_calls=0, no_original_confirmation_labels=True,
        code={name: identity(ROOT / 'code' / name) for name in
              ['summary_diagnosis96.py', 'stage_metric_cache96.py']}))
    sources = development_sources(None, None, read(ROOT / 'code/joint_policy_protocol44.json'),
                                  values=False, labels=True)
    cache = accepted_metrics(sources); first = []; scores, changes = {}, {}
    for sid, source in sources.items():
        masks = {arm: source_masks(sid, arm) for arm in (CONTROL,) + ARMS}
        scores[sid] = {arm: {stage: metric(mask, source, cache, first)
                            for stage, mask in stages.items()} for arm, stages in masks.items()}
        changes[sid] = {}
        for stage in STAGES:
            correct = masks[ARMS[1]][stage]
            changes[sid][stage] = {arm: dict(
                added=int((correct & ~masks[arm][stage]).sum()),
                removed=int((masks[arm][stage] & ~correct).sum()),
                delta_f1=scores[sid][ARMS[1]][stage]['score']['mean_f1']
                         - scores[sid][arm][stage]['score']['mean_f1'])
                for arm in (CONTROL, ARMS[0], ARMS[2])}
    macro = {arm: {stage: math.fsum(scores[sid][arm][stage]['score']['mean_f1']
                                  for sid in sources) / len(sources)
                   for stage in STAGES} for arm in (CONTROL,) + ARMS}
    save(OUT / 'completion.json', dict(state='FIRST_STOP85_STAGEWISE_CPU_DIAGNOSIS_COMPLETE',
        scores=scores, changes=changes, macro=macro, first_new_stage_metrics=first,
        fixed85_quality_STOP_unchanged=True, no_model_training_or_package_admission=True,
        labels_scope='Exposed human-summary preference, unselected semantics UNKNOWN',
        old_successful_model_token_QA_and_mask_metrics_not_repeated=True,
        new_model_calls=0, confirmation_sources_read=0, new_packages=0))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
